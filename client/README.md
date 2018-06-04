# ArgusScan v0.1 分布式被动SQL注入检测系统 - 客户端

## 使用方法

1. 在使用前，请先安装`python 2.7`及`相关依赖库`。
    > 在`命令提示符`中，执行`pip install -r requirements.txt`安装`依赖库`。

2. 配置`setting.ini`，设置`主服务器`的`地址`、`端口`，及目标站点的`Domain`。
    > `Domain`的设置，可以使用`白名单`或`黑名单`模式。
    
    > 注意：使用`白名单`或`黑名单`时，请用`#`注释掉另一个名单，否则会产生冲突。

3. 运行`client.py`。
    > 可以通过`-c`参数，指定配置文件，如：`client.py -c C:\tmp\config.ini`。
