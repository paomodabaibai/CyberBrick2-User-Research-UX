---
symbol: "cyberbrick.Wireless"
name: "Wireless"
lang: "zh"
kind: "class"
aliases: ["无线", "无线通信"]
keywords: ["分组通信", "标签订阅", "标签发布", "接收回调"]
category: "communication"
related: []
methods: ["get_status", "deinit", "reset_status", "publish_tag", "subscribe_tag", "read_tag", "get_pending_tag", "set_group", "register_rx_callback"]
constants: ["STATUS_UNPAIRED", "STATUS_NETWORKING_UNPAIRED", "STATUS_INITIATING", "STATUS_TRANSMIT_BANNED", "STATUS_PAIRED", "STATUS_NETWORKING_PAIRED", "STATUS_WAIT_USER"]
common_tasks: ["获取当前无线连接状态", "释放资源，注销回调函数", "重置无线状态", "发送带标签的数据", "订阅指定标签，接收该标签的数据", "读取指定 tag 的最新数据", "查询指定 tag 是否有待读取的数据", "设置通信分组"]
---

# cyberbrick.Wireless

brief: 无线通信模块（DCN 协议），支持分组、标签订阅与发布

## import
```python
import cyberbrick
wireless = cyberbrick.Wireless(group=b'demo')
```

constructor_example: wireless = cyberbrick.Wireless(group=b'demo')

## constructor
signature: Wireless(group=None)
example: wireless = cyberbrick.Wireless(group=b'demo')
parameters:
- group (bytes, optional): 分组名称，用于初始化通信分组

## constants
- STATUS_UNPAIRED (int) = 0: 未配对状态
- STATUS_NETWORKING_UNPAIRED (int) = 1: 组网中（未配对）状态
- STATUS_INITIATING (int) = 2: 初始化中状态
- STATUS_TRANSMIT_BANNED (int) = 3: 禁止发送状态
- STATUS_PAIRED (int) = 4: 已配对状态
- STATUS_NETWORKING_PAIRED (int) = 5: 组网中（已配对）状态
- STATUS_WAIT_USER (int) = 6: 等待用户操作状态

## methods

## method: get_status
signature: get_status() -> int
brief: 获取当前无线连接状态
aliases: []
keywords: []
returns: 状态常量值 (STATUS_UNPAIRED, STATUS_PAIRED 等)
raises:
- RuntimeError: DCN 未初始化或已关闭时抛出

## method: deinit
signature: deinit() -> None
brief: 释放资源，注销回调函数
aliases: []
keywords: []

## method: reset_status
signature: reset_status() -> None
brief: 重置无线状态
aliases: []
keywords: []
raises:
- RuntimeError: DCN 未初始化或已关闭时抛出

## method: publish_tag
signature: publish_tag(tag, data) -> None
brief: 发送带标签的数据
aliases: []
keywords: []
parameters:
- tag (bytes): 标签名（bytes 类型，最大 4 字节）
- data (bytes): 要发送的数据
raises:
- RuntimeError: DCN 未初始化或已关闭时抛出
example:
```python
import cyberbrick

wireless = cyberbrick.Wireless(group=b"room-01")
wireless.publish_tag(b"tmp", b"26.5")
```

## method: subscribe_tag
signature: subscribe_tag(tag) -> None
brief: 订阅指定标签，接收该标签的数据
aliases: []
keywords: []
parameters:
- tag (bytes): 标签名（bytes 类型，最大 4 字节）
raises:
- ValueError: 标签数量已满或标签已注册时抛出
- RuntimeError: DCN 未初始化或已关闭时抛出
example:
```python
import cyberbrick

wireless = cyberbrick.Wireless(group=b"room-01")
wireless.subscribe_tag(b"tmp")
```

## method: read_tag
signature: read_tag(tag) -> tuple
brief: 读取指定 tag 的最新数据
aliases: []
keywords: []
parameters:
- tag (bytes): 标签名（bytes 类型，最大 4 字节）
returns: (data, sender_mac) 元组；无数据时两个元素均为 None
raises:
- ValueError: 标签未注册时抛出
- RuntimeError: DCN 未初始化或已关闭时抛出
example:
```python
import cyberbrick

wireless = cyberbrick.Wireless(group=b"room-01")
wireless.subscribe_tag(b"tmp")

if wireless.get_pending_tag(b"tmp"):
    data, sender = wireless.read_tag(b"tmp")
    print(data, sender)
```

## method: get_pending_tag
signature: get_pending_tag(tag) -> bool
brief: 查询指定 tag 是否有待读取的数据
aliases: []
keywords: []
parameters:
- tag (bytes): 标签名（bytes 类型，最大 4 字节）
returns: True 表示有新数据，False 表示无
raises:
- ValueError: 标签未注册时抛出
- RuntimeError: DCN 未初始化或已关闭时抛出

## method: set_group
signature: set_group(group) -> None
brief: 设置通信分组
aliases: []
keywords: []
parameters:
- group (bytes): 分组名称（bytes 类型，最大 128 字节）
raises:
- RuntimeError: DCN 未初始化或已关闭时抛出
example:
```python
import cyberbrick

wireless = cyberbrick.Wireless()
wireless.set_group(b"room-01")
```

## method: register_rx_callback
signature: register_rx_callback(callback) -> None
brief: 注册数据接收回调函数
aliases: []
keywords: []
parameters:
- callback (callable): 回调函数，收到数据时被调用
raises:
- TypeError: 参数不可调用时抛出
- RuntimeError: DCN 未初始化或已关闭时抛出
example:
```python
import cyberbrick

wireless = cyberbrick.Wireless(group=b"room-01")
wireless.subscribe_tag(b"tmp")

def on_packet(dev):
    if dev.get_pending_tag(b"tmp"):
        data, sender = dev.read_tag(b"tmp")
        print('rx:', data, sender)

wireless.register_rx_callback(on_packet)
```

## example
```python
import cyberbrick

w = cyberbrick.Wireless(group=b"demo")
w.subscribe_tag(b"tmp")
w.publish_tag(b"tmp", b"25.3")
data, mac = w.read_tag(b"tmp")
print(data, mac)
w.deinit()
```
