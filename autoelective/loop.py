"""
@Author : xiaoce2025
@File   : loop.py
@Date   : 2025-08-30
"""

import os
import time
import random
from queue import Queue
from collections import deque
from itertools import combinations
from requests.compat import json
from requests.exceptions import RequestException
import numpy as np
from . import __version__, __date__
from .environ import Environ
from .config import AutoElectiveConfig
from .logger import ConsoleLogger, FileLogger
from .course import Course
from .captcha import TTShituRecognizer, Captcha
from .parser import get_tables, get_courses, get_courses_with_detail, get_sida
from .hook import _dump_request
from .iaaa import IAAAClient
from .elective import ElectiveClient
from .const import (
    CAPTCHA_CACHE_DIR,
    USER_AGENT_LIST,
    WEB_LOG_DIR,
    WECHAT_MSG,
    WECHAT_PREFIX,
)
from .exceptions import *
from ._internal import mkdir
from .notification.manager import send_notify

environ = Environ()
config = AutoElectiveConfig()
cout = ConsoleLogger("loop")
ferr = FileLogger("loop.error")  # loop 的子日志，同步输出到 console

username = config.iaaa_id
password = config.iaaa_password
is_dual_degree = config.is_dual_degree
identity = config.identity
refresh_interval = config.refresh_interval
refresh_random_deviation = config.refresh_random_deviation
supply_cancel_page = config.supply_cancel_page
iaaa_client_timeout = config.iaaa_client_timeout
elective_client_timeout = config.elective_client_timeout
login_loop_interval = config.login_loop_interval
elective_client_pool_size = config.elective_client_pool_size
elective_client_max_life = config.elective_client_max_life
is_print_mutex_rules = config.is_print_mutex_rules

config.check_identify(identity)
config.check_supply_cancel_page(supply_cancel_page)

_USER_WEB_LOG_DIR = os.path.join(WEB_LOG_DIR, config.get_user_subpath())
mkdir(_USER_WEB_LOG_DIR)

recognizer = TTShituRecognizer()
RECOGNIZER_MAX_ATTEMPT = 15

electivePool = Queue(maxsize=elective_client_pool_size)
reloginPool = Queue(maxsize=elective_client_pool_size)

goals = environ.goals  # let N = len(goals);
ignored = environ.ignored
mutexes = np.zeros(0, dtype=np.uint8)  # uint8 [N][N];
delays = np.zeros(0, dtype=np.int32)  # int [N];

killedElective = ElectiveClient(-1)
NO_DELAY = -1


# ────────────────────────── 配置刷新 ──────────────────────────

def refreshsettings():
    """从 config 重新读取所有运行时参数，并重建对象池和识别器。"""
    global username, password, is_dual_degree, identity, refresh_interval
    global refresh_random_deviation, supply_cancel_page, iaaa_client_timeout
    global elective_client_timeout, login_loop_interval, elective_client_pool_size
    global elective_client_max_life, is_print_mutex_rules
    global electivePool, reloginPool, goals, ignored, mutexes, delays
    global recognizer

    username = config.iaaa_id
    password = config.iaaa_password
    is_dual_degree = config.is_dual_degree
    identity = config.identity
    refresh_interval = config.refresh_interval
    refresh_random_deviation = config.refresh_random_deviation
    supply_cancel_page = config.supply_cancel_page
    iaaa_client_timeout = config.iaaa_client_timeout
    elective_client_timeout = config.elective_client_timeout
    login_loop_interval = config.login_loop_interval
    elective_client_pool_size = config.elective_client_pool_size
    elective_client_max_life = config.elective_client_max_life
    is_print_mutex_rules = config.is_print_mutex_rules

    recognizer = TTShituRecognizer()

    electivePool = Queue(maxsize=elective_client_pool_size)
    reloginPool = Queue(maxsize=elective_client_pool_size)

    goals = environ.goals  # let N = len(goals);
    ignored = environ.ignored
    mutexes = np.zeros(0, dtype=np.uint8)  # uint8 [N][N];
    delays = np.zeros(0, dtype=np.int32)  # int [N];


# ────────────────────────── 内部异常 ──────────────────────────

class _ElectiveNeedsLogin(Exception):
    pass


class _ElectiveExpired(Exception):
    pass


# ────────────────────────── 辅助函数 ──────────────────────────

def _get_refresh_interval():
    if refresh_random_deviation <= 0:
        return refresh_interval
    delta = (random.random() * 2 - 1) * refresh_random_deviation * refresh_interval
    return refresh_interval + delta


def _ignore_course(course, reason):
    ignored[course.to_simplified()] = reason


def _add_error(e):
    clz = e.__class__
    name = clz.__name__
    key = "[%s] %s" % (e.code, name) if hasattr(clz, "code") else name
    environ.errors[key] += 1


def _format_timestamp(timestamp):
    if timestamp == -1:
        return str(timestamp)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))


def _dump_respose_content(content, filename):
    path = os.path.join(_USER_WEB_LOG_DIR, filename)
    with open(path, "wb") as fp:
        fp.write(content)


def _log_common_exception(e, label):
    """通用非致命异常：记录日志 + 统计错误计数。"""
    ferr.error(e)
    cout.warning("%s encountered" % label)
    _add_error(e)


# ────────────────────────── 选课页面操作 ──────────────────────────

def _fetch_elective_page(elective):
    """获取补退选页面，返回 (page_response, elected_courses, plans)。"""
    if supply_cancel_page == 1:
        cout.info("Get SupplyCancel page %s" % supply_cancel_page)
        r = elective.get_SupplyCancel(username)
        tables = get_tables(r._tree)
        try:
            elected = get_courses(tables[1])
            plans = get_courses_with_detail(tables[0])
        except IndexError:
            filename = "elective.get_SupplyCancel_%d.html" % int(time.time() * 1000)
            _dump_respose_content(r.content, filename)
            cout.info("Page dump to %s" % filename)
            raise UnexceptedHTMLFormat
        return r, elected, plans

    # 非第一页：需要先访问主页面防止空表格
    retry = 3
    while True:
        if retry == 0:
            raise OperationFailedError(
                msg="unable to get normal Supplement page %s" % supply_cancel_page
            )

        cout.info("Get Supplement page %s" % supply_cancel_page)
        r = elective.get_supplement(username, page=supply_cancel_page)
        tables = get_tables(r._tree)
        try:
            elected = get_courses(tables[1])
            plans = get_courses_with_detail(tables[0])
        except IndexError:
            cout.warning("IndexError encountered")
            cout.info("Get SupplyCancel first to prevent empty table returned")
            _ = elective.get_SupplyCancel(username)
        else:
            return r, elected, plans
        finally:
            retry -= 1


def _check_available_courses(goals, elected, plans):
    """检查哪些目标课程当前可选，返回 deque[(ix, course)]。"""
    cout.info("Get available courses")

    tasks = []  # [(ix, course)]
    for ix, c in enumerate(goals):
        if c in ignored:
            continue
        elif c in elected:
            cout.info("%s is elected, ignored" % c)
            _ignore_course(c, "Elected")
            for (mix,) in np.argwhere(mutexes[ix, :] == 1):
                mc = goals[mix]
                if mc in ignored:
                    continue
                cout.info("%s is simultaneously ignored by mutex rules" % mc)
                _ignore_course(mc, "Mutex rules")
        else:
            for c0 in plans:  # c0 has detail
                if c0 == c:
                    if c0.is_available():
                        delay = delays[ix]
                        if delay != NO_DELAY and c0.remaining_quota > delay:
                            cout.info(
                                "%s hasn't reached the delay threshold %d, skip"
                                % (c0, delay)
                            )
                        else:
                            tasks.append((ix, c0))
                            cout.info("%s is AVAILABLE now !" % c0)
                    break
            else:
                raise UserInputException(
                    "%s is not in your course plan, please check your config." % c
                )

    return deque([(ix, c) for ix, c in tasks if c not in ignored])


def _validate_captcha(elective):
    """获取并验证验证码，返回 True 表示通过，False 表示跳过本课程。"""
    captcha_fail_count = 0
    max_captcha_fails = 5

    while True:
        cout.info("Fetch a captcha")
        r = elective.get_DrawServlet()

        captcha = recognizer.recognize(r.content)
        cout.info("Recognition result: %s" % captcha.code)

        r = elective.get_Validate(username, captcha.code)
        try:
            res = r.json()["valid"]
        except Exception as e:
            ferr.error(e)
            raise OperationFailedError(msg="Unable to validate captcha")

        if res == "2":
            cout.info("Validation passed")
            return True
        elif res == "0":
            captcha_fail_count += 1
            cout.info("Validation failed (attempt %d/%d)" % (captcha_fail_count, max_captcha_fails))
            cout.info("Auto error caching skipped for good")

            if captcha_fail_count >= max_captcha_fails:
                cout.warning("Captcha validation failed %d times, skipping this course" % max_captcha_fails)
                return False
            else:
                cout.info("Try again")
        else:
            cout.warning("Unknown validation result: %s" % res)


def _handle_election_error(e, course, page_r):
    """处理选课提交后的异常，返回动态已选课程列表（可能为 None）。"""
    if isinstance(e, ElectionRepeatedError):
        ferr.error(e)
        cout.warning("ElectionRepeatedError encountered")
        send_notify(msg=WECHAT_MSG[3], prefix=WECHAT_PREFIX[3])
        _ignore_course(course, "Repeated")
        _add_error(e)

    elif isinstance(e, TimeConflictError):
        ferr.error(e)
        cout.warning("TimeConflictError encountered")
        send_notify(msg=WECHAT_MSG[4] + str(course), prefix=WECHAT_PREFIX[3])
        _ignore_course(course, "Time conflict")
        _add_error(e)

    elif isinstance(e, ExamTimeConflictError):
        ferr.error(e)
        cout.warning("ExamTimeConflictError encountered")
        send_notify(msg=WECHAT_MSG[5] + str(course), prefix=WECHAT_PREFIX[3])
        _ignore_course(course, "Exam time conflict")
        _add_error(e)

    elif isinstance(e, ElectionPermissionError):
        ferr.error(e)
        cout.warning("ElectionPermissionError encountered")
        _ignore_course(course, "Permission required")
        _add_error(e)

    elif isinstance(e, CreditsLimitedError):
        ferr.error(e)
        cout.warning("CreditsLimitedError encountered")
        _ignore_course(course, "Credits limited")
        _add_error(e)

    elif isinstance(e, MutexCourseError):
        ferr.error(e)
        cout.warning("MutexCourseError encountered")
        _ignore_course(course, "Mutual exclusive")
        _add_error(e)

    elif isinstance(e, MultiEnglishCourseError):
        ferr.error(e)
        cout.warning("MultiEnglishCourseError encountered")
        _ignore_course(course, "Multi English course")
        _add_error(e)

    elif isinstance(e, MultiPECourseError):
        ferr.error(e)
        cout.warning("MultiPECourseError encountered")
        _ignore_course(course, "Multi PE course")
        _add_error(e)

    elif isinstance(e, ElectionFailedError):
        ferr.error(e)
        cout.warning("ElectionFailedError encountered")
        _add_error(e)

    elif isinstance(e, QuotaLimitedError):
        ferr.error(e)
        if course.used_quota == 0:
            cout.warning(
                "Abnormal status of %s, a bug of 'elective.pku.edu.cn' found" % course
            )
        else:
            ferr.critical("Unexcepted behaviour")
            _add_error(e)

    elif isinstance(e, ElectionSuccess):
        cout.info("%s is ELECTED !" % course)
        send_notify(msg=WECHAT_MSG[1] + str(course), prefix=WECHAT_PREFIX[1])
        # 动态更新 elected，同一回合内低优先级课程可被 mutex 规则提前忽略
        r = e.response
        tables = get_tables(r._tree)
        return get_courses(tables[1])

    elif isinstance(e, RuntimeError):
        ferr.critical(e)
        ferr.critical(
            "RuntimeError with Course(name=%r, class_no=%d, school=%r, status=%s, href=%r)"
            % (course.name, course.class_no, course.school, course.status, course.href)
        )
        file = _dump_request(page_r)
        ferr.critical("Dump response from 'get_SupplyCancel / get_supplement' to %s" % file)
        raise e

    else:
        raise e

    return None


# ────────────────────────── IAAA 登录循环 ──────────────────────────

# IAAA 循环中可统一处理的非致命异常
_IAAA_NON_FATAL_EXCEPTIONS = (
    ServerError, StatusCodeError, OperationFailedError,
    RequestException, IAAAException, ElectiveException, json.JSONDecodeError,
)

def run_iaaa_loop():
    elective = None

    while True:
        if elective is None:
            elective = reloginPool.get()
            if elective is killedElective:
                cout.info("Quit IAAA loop")
                return

        environ.iaaa_loop += 1
        user_agent = random.choice(USER_AGENT_LIST)

        cout.info("Try to login IAAA (client: %s)" % elective.id)
        cout.info("User-Agent: %s" % user_agent)

        try:
            iaaa = IAAAClient(timeout=iaaa_client_timeout)  # not reusable
            iaaa.set_user_agent(user_agent)

            # request elective's home page to get cookies
            r = iaaa.oauth_home()

            r = iaaa.oauth_login(username, password)

            try:
                token = r.json()["token"]
            except Exception as e:
                ferr.error(e)
                raise OperationFailedError(
                    msg="Unable to parse IAAA token. response body: %s" % r.content
                )

            elective.clear_cookies()
            elective.set_user_agent(user_agent)

            r = elective.sso_login(token)

            if is_dual_degree:
                sida = get_sida(r)
                sttp = identity
                referer = r.url
                r = elective.sso_login_dual_degree(sida, sttp, referer)

            if elective_client_max_life == -1:
                elective.set_expired_time(-1)
            else:
                elective.set_expired_time(int(time.time()) + elective_client_max_life)
            cout.info(
                "Login success (client: %s, expired_time: %s)"
                % (elective.id, _format_timestamp(elective.expired_time))
            )
            cout.info("")

            electivePool.put_nowait(elective)
            elective = None

        except _IAAA_NON_FATAL_EXCEPTIONS as e:
            _log_common_exception(e, type(e).__name__)

        except IAAAIncorrectPasswordError as e:
            cout.error(e)
            _add_error(e)
            raise e

        except IAAAForbiddenError as e:
            ferr.error(e)
            _add_error(e)
            raise e

        except CaughtCheatingError as e:
            ferr.critical(e)
            _add_error(e)
            raise e

        except KeyboardInterrupt as e:
            raise e

        except Exception as e:
            ferr.exception(e)
            _add_error(e)
            raise e

        finally:
            t = login_loop_interval
            cout.info("")
            cout.info("IAAA login loop sleep %s s" % t)
            cout.info("")
            time.sleep(t)


# ────────────────────────── 选课循环 ──────────────────────────

# 选课循环中需要重新登录的会话/认证异常
_RELOGIN_EXCEPTIONS = (
    SessionExpiredError, InvalidTokenError, NoAuthInfoError, SharedSessionError,
)

def _print_loop_header():
    """打印当前循环的状态信息。"""
    line = "-" * 30

    current = [c for c in goals if c not in ignored]
    if len(current) > 0:
        cout.info("> Current tasks")
        cout.info(line)
        for ix, course in enumerate(current):
            cout.info("%02d. %s" % (ix + 1, course))
        cout.info(line)
        cout.info("")

    if len(ignored) > 0:
        cout.info("> Ignored tasks")
        cout.info(line)
        for ix, (course, reason) in enumerate(ignored.items()):
            cout.info("%02d. %s  %s" % (ix + 1, course, reason))
        cout.info(line)
        cout.info("")

    if np.any(mutexes):
        cout.info("> Mutex rules")
        cout.info(line)
        ixs = [(ix1, ix2) for ix1, ix2 in np.argwhere(mutexes == 1) if ix1 < ix2]
        if is_print_mutex_rules:
            for ix, (ix1, ix2) in enumerate(ixs):
                cout.info("%02d. %s --x-- %s" % (ix + 1, goals[ix1], goals[ix2]))
        else:
            cout.info("%d mutex rules" % len(ixs))
        cout.info(line)
        cout.info("")

    if np.any(delays != NO_DELAY):
        cout.info("> Delay rules")
        cout.info(line)
        ds = [
            (cix, threshold)
            for cix, threshold in enumerate(delays)
            if threshold != NO_DELAY
        ]
        for ix, (cix, threshold) in enumerate(ds):
            cout.info("%02d. %s --- %d" % (ix + 1, goals[cix], threshold))
        cout.info(line)
        cout.info("")

    return current


def run_elective_loop():
    elective = None
    noWait = False

    ## load courses

    cs = config.courses  # OrderedDict
    N = len(cs)
    cid_cix = {}  # { cid: cix }

    for ix, (cid, c) in enumerate(cs.items()):
        goals.append(c)
        cid_cix[cid] = ix

    ## load mutex

    ms = config.mutexes
    mutexes.resize((N, N), refcheck=False)

    for mid, m in ms.items():
        ixs = []
        for cid in m.cids:
            if cid not in cs:
                raise UserInputException(
                    "In 'mutex:%s', course %r is not defined" % (mid, cid)
                )
            ix = cid_cix[cid]
            ixs.append(ix)
        for ix1, ix2 in combinations(ixs, 2):
            mutexes[ix1, ix2] = mutexes[ix2, ix1] = 1

    ## load delay

    ds = config.delays
    delays.resize(N, refcheck=False)
    delays.fill(NO_DELAY)

    for did, d in ds.items():
        cid = d.cid
        if cid not in cs:
            raise UserInputException(
                "In 'delay:%s', course %r is not defined" % (did, cid)
            )
        ix = cid_cix[cid]
        delays[ix] = d.threshold

    ## setup elective pool

    for ix in range(1, elective_client_pool_size + 1):
        client = ElectiveClient(id=ix, timeout=elective_client_timeout)
        client.set_user_agent(random.choice(USER_AGENT_LIST))
        electivePool.put_nowait(client)

    cout.info("欢迎使用严小希选课小助手！")
    cout.info("让时光的帷幕，牵动往昔的涟漪，自此汇入晨光！")
    cout.info("")

    send_notify(msg=WECHAT_MSG["s"], prefix=WECHAT_PREFIX[3])

    line = "-" * 30

    cout.info("> User Agent")
    cout.info(line)
    cout.info("pool_size: %d" % len(USER_AGENT_LIST))
    cout.info(line)
    cout.info("")
    cout.info("> Config")
    cout.info(line)
    cout.info("is_dual_degree: %s" % is_dual_degree)
    cout.info("identity: %s" % identity)
    cout.info("refresh_interval: %s" % refresh_interval)
    cout.info("refresh_random_deviation: %s" % refresh_random_deviation)
    cout.info("supply_cancel_page: %s" % supply_cancel_page)
    cout.info("iaaa_client_timeout: %s" % iaaa_client_timeout)
    cout.info("elective_client_timeout: %s" % elective_client_timeout)
    cout.info("login_loop_interval: %s" % login_loop_interval)
    cout.info("elective_client_pool_size: %s" % elective_client_pool_size)
    cout.info("elective_client_max_life: %s" % elective_client_max_life)
    cout.info("is_print_mutex_rules: %s" % is_print_mutex_rules)
    cout.info(line)
    cout.info("")

    while True:
        noWait = False

        if elective is None:
            elective = electivePool.get()

        environ.elective_loop += 1

        cout.info("")
        cout.info("======== Loop %d ========" % environ.elective_loop)
        cout.info("")

        ## print current plans / ignored / mutex / delay

        current = _print_loop_header()

        if len(current) == 0:
            cout.info("No tasks")
            cout.info("Quit elective loop")
            reloginPool.put_nowait(killedElective)  # kill signal
            return

        ## print client info

        cout.info(
            "> Current client: %s (qsize: %s)" % (elective.id, electivePool.qsize() + 1)
        )
        cout.info(
            "> Client expired time: %s" % _format_timestamp(elective.expired_time)
        )
        cout.info("User-Agent: %s" % elective.user_agent)
        cout.info("")

        try:
            if not elective.has_logined:
                raise _ElectiveNeedsLogin  # quit this loop

            if elective.is_expired:
                try:
                    cout.info("Logout")
                    r = elective.logout()
                except Exception as e:
                    cout.warning("Logout error")
                    cout.exception(e)
                raise _ElectiveExpired  # quit this loop

            ## check supply/cancel page

            page_r, elected, plans = _fetch_elective_page(elective)

            ## check available courses

            tasks = _check_available_courses(goals, elected, plans)

            ## elect available courses

            if len(tasks) == 0:
                cout.info("No course available")
                continue

            elected_dynamic = []  # cache elected courses dynamically

            while len(tasks) > 0:
                ix, course = tasks.popleft()

                # dynamically filter course by mutex rules
                is_mutex = False
                for (mix,) in np.argwhere(mutexes[ix, :] == 1):
                    mc = goals[mix]
                    if mc in elected_dynamic:
                        is_mutex = True
                        cout.info("%s --x-- %s" % (course, mc))
                        cout.info("%s is ignored by mutex rules in advance" % course)
                        _ignore_course(course, "Mutex rules")
                        break

                if is_mutex:
                    continue

                cout.info("Try to elect %s" % course)

                ## validate captcha first

                if not _validate_captcha(elective):
                    cout.info("Skipping course %s due to captcha validation failures" % course)
                    continue

                ## try to elect

                try:
                    r = elective.get_ElectSupplement(course.href)

                except (
                    ElectionRepeatedError, TimeConflictError, ExamTimeConflictError,
                    ElectionPermissionError, CreditsLimitedError, MutexCourseError,
                    MultiEnglishCourseError, MultiPECourseError, ElectionFailedError,
                    QuotaLimitedError,
                ) as e:
                    _handle_election_error(e, course, page_r)

                except ElectionSuccess as e:
                    # 不从此处加入 ignored，而是在下回合根据教学网返回的实际选课结果来决定是否忽略
                    result_elected = _handle_election_error(e, course, page_r)
                    if result_elected is not None:
                        # use clear() + extend() instead of op `=` to ensure `id(elected_dynamic)` doesn't change
                        elected_dynamic.clear()
                        elected_dynamic.extend(result_elected)

                except RuntimeError as e:
                    _handle_election_error(e, course, page_r)  # 内部会 raise

                except Exception as e:
                    raise e  # don't increase error count here

        except UserInputException as e:
            cout.error(e)
            _add_error(e)
            raise e

        except _IAAA_NON_FATAL_EXCEPTIONS as e:
            _log_common_exception(e, type(e).__name__)

        except UnexceptedHTMLFormat as e:
            _log_common_exception(e, "UnexceptedHTMLFormat")

        except _ElectiveNeedsLogin:
            cout.info("client: %s needs Login" % elective.id)
            reloginPool.put_nowait(elective)
            elective = None
            noWait = True

        except _ElectiveExpired:
            cout.info("client: %s expired" % elective.id)
            reloginPool.put_nowait(elective)
            elective = None
            noWait = True

        except _RELOGIN_EXCEPTIONS as e:
            _log_common_exception(e, type(e).__name__)
            cout.info("client: %s needs relogin" % elective.id)
            reloginPool.put_nowait(elective)
            elective = None
            noWait = True

        except CaughtCheatingError as e:
            ferr.critical(e)
            _add_error(e)
            raise e

        except SystemException as e:
            _log_common_exception(e, "SystemException")

        except TipsException as e:
            _log_common_exception(e, "TipsException")

        except OperationTimeoutError as e:
            _log_common_exception(e, "OperationTimeoutError")

        except json.JSONDecodeError as e:
            _log_common_exception(e, "JSONDecodeError")

        except KeyboardInterrupt as e:
            raise e

        except Exception as e:
            ferr.exception(e)
            _add_error(e)
            raise e

        finally:
            if elective is not None:  # change elective client
                electivePool.put_nowait(elective)
                elective = None

            if noWait:
                cout.info("")
                cout.info("======== END Loop %d ========" % environ.elective_loop)
                cout.info("")
            else:
                t = _get_refresh_interval()
                cout.info("")
                cout.info("======== END Loop %d ========" % environ.elective_loop)
                cout.info("Main loop sleep %s s" % t)
                cout.info("")
                time.sleep(t)
