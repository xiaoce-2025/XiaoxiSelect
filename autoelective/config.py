"""
@Author : xiaoce2025
@File   : config.py
@Date   : 2025-08-29
"""

# 主要修改内容：重构config类，并添加相应的reload方法

import os
import re
from configparser import RawConfigParser, DuplicateSectionError
from collections import OrderedDict
from .environ import Environ
from .course import Course
from .rule import Mutex, Delay
from .utils import Singleton
from .const import DEFAULT_CONFIG_INI
from .exceptions import UserInputException

_reNamespacedSection = re.compile(r'^\s*(?P<ns>[^:]+?)\s*:\s*(?P<id>[^,]+?)\s*$')
_reCommaSep = re.compile(r'\s*,\s*')

environ = Environ()


class BaseConfig(object):

    def __init__(self, config_file=None):
        if self.__class__ is __class__:
            raise NotImplementedError
        self._config_file = config_file
        self._parse_config()
    
    def _parse_config(self):
        """解析配置文件"""
        file = os.path.normpath(os.path.abspath(self._config_file))
        if not os.path.exists(file):
            raise FileNotFoundError("Config file was not found: %s" % file)
        self._config = RawConfigParser()
        self._config.read(file, encoding="utf-8-sig")

    def get(self, section, key):
        return self._config.get(section, key)

    def getint(self, section, key):
        return self._config.getint(section, key)

    def getfloat(self, section, key):
        return self._config.getfloat(section, key)

    def getboolean(self, section, key):
        return self._config.getboolean(section, key)

    def getdict(self, section, options):
        assert isinstance(options, (list, tuple, set))
        d = dict(self._config.items(section))
        if not all(k in d for k in options):
            raise UserInputException("Incomplete course in section %r, %s must all exist." % (section, options))
        return d

    def getlist(self, section, option, *args, **kwargs):
        v = self.get(section, option, *args, **kwargs)
        return _reCommaSep.split(v)

    def ns_sections(self, ns):
        ns = ns.strip()
        ns_sects = OrderedDict()  # { id: str(section) }
        for s in self._config.sections():
            mat = _reNamespacedSection.match(s)
            if mat is None:
                continue
            if mat.group('ns') != ns:
                continue
            id_ = mat.group('id')
            if id_ in ns_sects:
                raise DuplicateSectionError("%s:%s" % (ns, id_))
            ns_sects[id_] = s
        return [(id_, s) for id_, s in ns_sects.items()]  # [ (id, str(section)) ]


class AutoElectiveConfig(BaseConfig, metaclass=Singleton):

    def __init__(self):
        config_file = environ.config_ini or DEFAULT_CONFIG_INI
        super().__init__(config_file)
        self._init_properties()
    
    def reload(self):
        """重新加载配置文件"""
        # 重新解析配置文件
        self._parse_config()
        # 重新初始化属性
        self._init_properties()
    
    def _init_properties(self):
        """初始化所有配置属性"""
        # [user] 部分
        self._iaaa_id = self.get("user", "student_id")
        self._iaaa_password = self.get("user", "password")
        self._is_dual_degree = self.getboolean("user", "dual_degree")
        self._identity = self.get("user", "identity").lower()
        
        # [client] 部分
        self._supply_cancel_page = self.getint("client", "supply_cancel_page")
        self._refresh_interval = self.getfloat("client", "refresh_interval")
        self._refresh_random_deviation = self.getfloat("client", "random_deviation")
        self._iaaa_client_timeout = self.getfloat("client", "iaaa_client_timeout")
        self._elective_client_timeout = self.getfloat("client", "elective_client_timeout")
        self._elective_client_pool_size = self.getint("client", "elective_client_pool_size")
        self._elective_client_max_life = self.getint("client", "elective_client_max_life")
        self._login_loop_interval = self.getfloat("client", "login_loop_interval")
        self._is_print_mutex_rules = self.getboolean("client", "print_mutex_rules")
        self._is_debug_print_request = self.getboolean("client", "debug_print_request")
        self._is_debug_dump_request = self.getboolean("client", "debug_dump_request")
        
        # [monitor] 部分
        self._monitor_host = self.get("monitor", "host")
        self._monitor_port = self.getint("monitor", "port")
        
        # [notification] 部分（已弃用，为保证原有代码流畅运行，此处赋常值）
        self._disable_push = True
        self._wechat_token = ""
        self._verbosity = 1
        self._minimum_interval = 1.0
        
        # [course] 部分 - 动态属性
        self._courses = self._load_courses()
        
        # [mutex] 部分 - 动态属性
        self._mutexes = self._load_mutexes()
        
        # [delay] 部分 - 动态属性
        self._delays = self._load_delays()
    
    ## 动态属性加载方法
    
    def _load_courses(self):
        cs = OrderedDict()  # { id: Course }
        rcs = {}
        for id_, s in self.ns_sections('course'):
            d = self.getdict(s, ('name', 'class', 'school'))
            d.update(class_no=d.pop('class'))
            c = Course(**d)
            cs[id_] = c
            rid = rcs.get(c)
            if rid is not None:
                raise UserInputException("Duplicated courses in sections 'course:%s' and 'course:%s'" % (rid, id_))
            rcs[c] = id_
        return cs
    
    def _load_mutexes(self):
        ms = OrderedDict()  # { id: Mutex }
        for id_, s in self.ns_sections('mutex'):
            lst = self.getlist(s, 'courses')
            ms[id_] = Mutex(lst)
        return ms
    
    def _load_delays(self):
        ds = OrderedDict()  # { id: Delay }
        cid_id = {}  # { cid: id }
        for id_, s in self.ns_sections('delay'):
            cid = self.get(s, 'course')
            threshold = self.getint(s, 'threshold')
            if not threshold > 0:
                raise UserInputException("Invalid threshold %d in 'delay:%s', threshold > 0 must be satisfied" % (threshold, id_))
            id0 = cid_id.get(cid)
            if id0 is not None:
                raise UserInputException("Duplicated delays of 'course:%s' in 'delay:%s' and 'delay:%s'" % (cid, id0, id_))
            cid_id[cid] = id_
            ds[id_] = Delay(cid, threshold)
        return ds

    ## Property Getters

    @property
    def iaaa_id(self):
        return self._iaaa_id

    @property
    def iaaa_password(self):
        return self._iaaa_password

    @property
    def is_dual_degree(self):
        return self._is_dual_degree

    @property
    def identity(self):
        return self._identity

    @property
    def supply_cancel_page(self):
        return self._supply_cancel_page

    @property
    def refresh_interval(self):
        return self._refresh_interval

    @property
    def refresh_random_deviation(self):
        return self._refresh_random_deviation

    @property
    def iaaa_client_timeout(self):
        return self._iaaa_client_timeout

    @property
    def elective_client_timeout(self):
        return self._elective_client_timeout

    @property
    def elective_client_pool_size(self):
        return self._elective_client_pool_size

    @property
    def elective_client_max_life(self):
        return self._elective_client_max_life

    @property
    def login_loop_interval(self):
        return self._login_loop_interval

    @property
    def is_print_mutex_rules(self):
        return self._is_print_mutex_rules

    @property
    def is_debug_print_request(self):
        return self._is_debug_print_request

    @property
    def is_debug_dump_request(self):
        return self._is_debug_dump_request

    @property
    def monitor_host(self):
        return self._monitor_host

    @property
    def monitor_port(self):
        return self._monitor_port

    @property
    def disable_push(self):
        return self._disable_push

    @property
    def wechat_token(self):
        return self._wechat_token

    @property
    def verbosity(self):
        return self._verbosity

    @property
    def minimum_interval(self):
        return self._minimum_interval

    @property
    def courses(self):
        return self._courses

    @property
    def mutexes(self):
        return self._mutexes

    @property
    def delays(self):
        return self._delays

    ## Method

    def check_identify(self, identity):
        limited = ("bzx", "bfx")
        if identity not in limited:
            raise ValueError("unsupported identity %s for elective, identity must be in %s" % (identity, limited))

    def check_supply_cancel_page(self, page):
        if page <= 0:
            raise ValueError("supply_cancel_page must be positive number, not %s" % page)

    def get_user_subpath(self):
        if self.is_dual_degree:
            identity = self.identity
            self.check_identify(identity)
            if identity == "bfx":
                return "%s_%s" % (self.iaaa_id, identity)
        return self.iaaa_id