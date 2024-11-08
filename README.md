# Nonebot 2 的权限管理系统

## Rule 编写

规则文件一般放置于 ./data/pam/ 文件夹下面（仿造[文件夹例子](examples.data/pam)）

格式是 plugin_name.yaml，或者 plugin_name/xxx.yaml

plugin_name 是具体限制的插件名字，特别的，\_\_all\_\_ 表示在全局启用（即，每一个指令都会检测）

## Yaml 规范

```yaml
pam:
  - rule: user.id != '1919810'
    reason: 你是？
```

这个是判断发送消息的 id 是不是 1919810，如果不是，就发送“你是？”并终止指令 pam 的匹配。特别的，这里指约束指令的首个元素，即，cmd = ('pam', 'reload', ) 也会被这个匹配到。

```yaml
pam:
  - rule: len(plugin.command) > 1 and plugin.command[1] == 'help'
    ratelimit: limit.bucket(f'{plugin.command}', 60, 3)
    reason: "{user.name}，你怎么一直要查看帮助呢？"
```

要匹配 cmd = ('pam', 'help', )，或者类似的，则可以对 plugin.command 约束。具体的规则请查看[规范](#规则支持)。

并且，reason 是 f-string，也就是说，你可以在里面使用 {} 包裹一些变量，函数等，进行更加丰富的提示返回。这三个字段所运行的上下文都是一致的。不过可能缺失部分内建函数/类。

ratelimit 则是令牌桶管理，具体可以查看[限速配置](#限速配置)。

## 规则支持

### Top Level

变量：

- bot
- event
- limit
- group
- plugin
- state
- user
- bucket

模块/类：

- int
- str
- re

部分字段算是语法糖，例如，group.name 在 Python 中需要 await 的。

### bot

对 Bot 的包装，和 Nonebot2 的没啥区别。

### event

对 Evnet 的包装，和 Nonebot2 的没啥区别。

### state

对 T_State 的包装，大概的区别就是可以 state._prefix 这么用。

### bucket

快捷访问 key 为 f"{user.id}_{plugin.name}_{plugin.command}" 的 limit.

### group

群组信息，Onebot V11 适配器专属（其他适配器 pr wellcome）

- id: 群号，int
- name: 群名字，str

### user

- id: 用户标识码，str

Onebot V11 专属：

- name: 名字，群昵称优先，str

### plugin

- name: 插件名字，str
- command: 当前执行的命令，tuple[str] | None

### limit

限流，具体请查看[限速配置](#限速配置)。

## 限速配置

具体的实现是令牌桶。

```yaml
py:
  - ratelimit: limit.bucket(f"{user.id}_{plugin.name}_{plugin.command}")
    reason: 还有 {limit.status(f"{user.id}_{plugin.name}_{plugin.command}"):.2f} 秒哦。
```

等价于

```yaml
py:
  - ratelimit: bucket.bucket()
    reason: 还有 {bucket.status():.2f} 秒哦。
```

### limit.bucket(key, rate: float, max: int) -> bool

- key: 限定是什么桶，注意，key = 1 和 key = '1' 是两个桶。
- rate: 速率限制，也就是经过多少秒添加一个令牌，默认 60.
- max: 令牌桶最大容量，默认 3.

返回值为 True 意味着当前处于速率限制。

### limit.status(key) -> float

- key: 桶的key

返回值为还有多久的时间（单位 s）

## TODO LIST

### Main

1. 添加 Web UI
2. 自动提取指令

### Checker

1. 完善 alias 的识别

### Server

1. 完善 Reload API
2. 新增 Delete API
3. 新增 Change API
