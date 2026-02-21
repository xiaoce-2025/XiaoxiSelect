# 严小希选课小助手
## 更新日志
本项目基于[PKUElective2024Spring](https://github.com/zhuozhiyongde/PKUElective2024Spring)。

本项目创造了图形化界面，并完善了相关选课功能
```Java
{
    "version": "2025-Autumn-1.1.4",
    "changelog": "1.修复了特定情况下会产生的异常高频的验证码识别请求",
    "release_date": "2025-09-07",
    "type": "CriticalBugFix",
    "min_required_version": "1.1.4"
},
{
    "version": "2025-Autumn-1.1.5",
    "changelog": "1.添加了严小希的语音提醒功能",
    "release_date": "2025-10-02",
    "type": "Feature",
    "min_required_version": "1.1.4"
},
{
    "version": "2026-Spring-1.2.1",
    "changelog": "1.重构界面UI和配置逻辑，大幅提高用户体验\n2.添加了更新系统",
    "release_date": "2025-01-06",
    "type": "Feature",
    "min_required_version": "1.1.4"
}
```

## 注意事项

-   作者可能无视 issue 和 PR，如果您有更好的改进想法，请最好 clone 一份后自行改动
-   请不要在公开场合传播此项目，以免造成不必要的麻烦
-   刷课有风险 USE AT YOUR OWN RISK!
-   **暂时不能给你明确的答复，这个需要你自己衡量！**
-   

## 附录
2025年秋季学期，选课网对验证码系统进行了更新

现有验证码识别系统无法识别部分验证码，且在识别后会反复进行尝试，容易造成短时间内高频次访问

故而为选课网的验证码识别添加限速系统。
