## PKU自动选课程序日志条目完整列表

### 1. 程序启动和配置相关日志

#### 信息级别 (INFO)
- **"刷课开始"** - 程序启动时发送的微信推送消息
- **"======== Loop %d ========"** - 每次选课循环开始时显示循环次数
- **"> User Agent"** - 显示User-Agent池信息
- **"pool_size: %d"** - 显示可用的User-Agent数量
- **"> Config"** - 显示配置信息标题
- **"is_dual_degree: %s"** - 是否双学位
- **"identity: %s"** - 身份标识
- **"refresh_interval: %s"** - 刷新间隔
- **"refresh_random_deviation: %s"** - 刷新随机偏差
- **"supply_cancel_page: %s"** - 补退选页面
- **"iaaa_client_timeout: %s"** - IAAA客户端超时时间
- **"elective_client_timeout: %s"** - 选课客户端超时时间
- **"login_loop_interval: %s"** - 登录循环间隔
- **"elective_client_pool_size: %s"** - 选课客户端池大小
- **"elective_client_max_life: %s"** - 选课客户端最大生命周期
- **"is_print_mutex_rules: %s"** - 是否打印互斥规则

#### 调试级别 (DEBUG)
- **"> %s  %s"** - 显示HTTP请求方法和URL
- **"> Headers:"** - 显示请求头信息
- **"%s: %s"** - 显示具体的请求头键值对
- **"> Body:"** - 显示请求体内容
- **"> Response Headers:"** - 显示响应头信息
- **"Dump request %s to %s"** - 显示请求转储到文件的信息

### 2. 任务管理相关日志

#### 信息级别 (INFO)
- **"> Current tasks"** - 显示当前任务列表
- **"%02d. %s"** - 显示任务编号和课程信息
- **"> Ignored tasks"** - 显示被忽略的任务列表
- **"%02d. %s  %s"** - 显示被忽略任务的编号、课程和原因
- **"> Mutex rules"** - 显示互斥规则
- **"%02d. %s --x-- %s"** - 显示互斥的课程对
- **"%d mutex rules"** - 显示互斥规则总数
- **"> Delay rules"** - 显示延迟规则
- **"%02d. %s --- %d"** - 显示延迟规则的课程和阈值
- **"No tasks"** - 没有任务可执行
- **"Quit elective loop"** - 退出选课循环

### 3. 登录和认证相关日志

#### 信息级别 (INFO)
- **"Try to login IAAA (client: %s)"** - 尝试登录IAAA系统
- **"User-Agent: %s"** - 显示使用的User-Agent
- **"client: %s needs Login"** - 客户端需要重新登录
- **"client: %s expired"** - 客户端已过期
- **"client: %s needs relogin"** - 客户端需要重新登录
- **"IAAA login loop sleep %s s"** - IAAA登录循环等待时间
- **"Quit IAAA loop"** - 退出IAAA登录循环

#### 警告级别 (WARNING)
- **"ServerError/StatusCodeError encountered"** - 遇到服务器错误或状态码错误
- **"OperationFailedError encountered"** - 遇到操作失败错误
- **"RequestException encountered"** - 遇到请求异常
- **"IAAAException encountered"** - 遇到IAAA异常
- **"ElectiveException encountered"** - 遇到选课异常
- **"JSONDecodeError encountered"** - 遇到JSON解码错误
- **"Logout error"** - 登出时出现错误

#### 错误级别 (ERROR)
- **"Unable to get errcode/errmsg from response JSON"** - 无法从响应JSON获取错误码/错误消息

#### 严重错误级别 (CRITICAL)
- **"RuntimeError with Course(...)"** - 运行时错误，包含课程详细信息
- **"Dump response from 'get_SupplyCancel / get_supplement' to %s"** - 转储响应到文件

### 4. 选课操作相关日志

#### 信息级别 (INFO)
- **"Get SupplyCancel page %s"** - 获取补退选页面
- **"Page dump to %s"** - 页面转储到文件
- **"Get Supplement page %s"** - 获取补充页面
- **"Get available courses"** - 获取可用课程
- **"%s is elected, ignored"** - 课程已被选中，忽略
- **"%s is simultaneously ignored by mutex rules"** - 课程因互斥规则被同时忽略
- **"%s is AVAILABLE now !"** - 课程现在可用
- **"No course available"** - 没有可用课程
- **"%s --x-- %s"** - 课程因互斥规则被提前忽略
- **"Try to elect %s"** - 尝试选课
- **"Fetch a captcha"** - 获取验证码
- **"Recognition result: %s"** - 验证码识别结果
- **"Validation passed"** - 验证通过
- **"Validation failed"** - 验证失败
- **"Auto error caching skipped for good"** - 自动错误缓存跳过
- **"Try again"** - 重试
- **"%s is ELECTED !"** - 选课成功
- **"Logout"** - 登出

#### 警告级别 (WARNING)
- **"Unknown validation result: %s"** - 未知的验证结果
- **"ElectionRepeatedError encountered"** - 遇到重复选课错误
- **"TimeConflictError encountered"** - 遇到时间冲突错误
- **"ExamTimeConflictError encountered"** - 遇到考试时间冲突错误
- **"ElectionPermissionError encountered"** - 遇到选课权限错误
- **"CreditsLimitedError encountered"** - 遇到学分限制错误
- **"MutexCourseError encountered"** - 遇到互斥课程错误
- **"MultiEnglishCourseError encountered"** - 遇到多英语课程错误
- **"MultiPECourseError encountered"** - 遇到多体育课程错误
- **"ElectionFailedError encountered"** - 遇到选课失败错误
- **"Abnormal status of %s, a bug of 'elective.pku.edu.cn' found"** - 发现选课网异常状态
- **"IndexError encountered"** - 遇到索引错误

#### 严重错误级别 (CRITICAL)
- **"Unexcepted behaviour"** - 意外行为

### 5. 异常处理相关日志

#### 错误级别 (ERROR)
- **各种异常的具体错误信息** - 包括所有在`exceptions.py`中定义的异常类型

#### 异常级别 (EXCEPTION)
- **异常堆栈跟踪信息** - 当使用`exception()`方法记录日志时

### 6. 微信推送相关日志

根据`const.py`中的定义，程序会在以下情况发送微信推送：

- **"出现未知异常，程序中止"** - 程序遇到未知异常时
- **"选课成功，课程为："** - 选课成功时
- **"有名额，验证码识别失败，正在重试"** - 验证码识别失败时
- **"出现重复选课，请调整config文件"** - 重复选课时
- **"时间冲突，课程为"** - 时间冲突时
- **"考试时间冲突，课程为"** - 考试时间冲突时

### 7. 日志文件分类

程序将日志分别存储在不同的文件中：
- **控制台日志** - 实时显示在控制台
- **错误日志** - 存储在`log/error/`目录下
- **请求日志** - 存储在`log/request/`目录下  
- **网页日志** - 存储在`log/web/`目录下

### 8. 日志级别说明

- **DEBUG** - 详细的调试信息，包括HTTP请求/响应的详细信息
- **INFO** - 一般信息，程序运行状态、选课进度等
- **WARNING** - 警告信息，遇到可恢复的错误或异常情况
- **ERROR** - 错误信息，遇到需要处理的错误
- **EXCEPTION** - 异常信息，包含完整的异常堆栈跟踪
- **CRITICAL** - 严重错误，程序可能无法继续运行
- **FATAL** - 致命错误，程序必须终止

