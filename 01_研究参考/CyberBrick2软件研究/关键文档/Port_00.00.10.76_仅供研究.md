---
symbol: "cyberbrick.Port"
name: "Port"
lang: "zh"
kind: "module"
aliases: ["端口"]
keywords: ["模块查找", "引脚映射", "原始模式", "端口信息"]
category: "system"
related: []
methods: ["find_module", "find_modules", "set_port_raw", "get_port_pin", "list", "info"]
constants: []
common_tasks: ["查找指定类型的单个模块", "查找指定类型的所有模块", "将端口设置为原始模式", "获取指定端口的引脚信息", "获取所有端口的详细信息列表", "打印所有端口的摘要信息到控制台"]
---

# cyberbrick.Port

brief: 端口管理模块，提供端口查询和配置功能

## import
```python
import cyberbrick
port = cyberbrick.Port
```

constructor_example: port = cyberbrick.Port

notes:
- 设置原始模式后，该端口上的模块将无法正常工作

## methods

## method: find_module
signature: find_module(module_name) -> int | None
brief: 查找指定类型的单个模块
aliases: []
keywords: []
parameters:
- module_name (str): 模块名称或类型 (如 "Button", "Servo", "any")
returns: 端口ID，未找到或找到多个时返回 None

## method: find_modules
signature: find_modules(module_name) -> list | None
brief: 查找指定类型的所有模块
aliases: []
keywords: []
parameters:
- module_name (str): 模块名称或类型 (如 "Button", "any")
returns: 端口ID列表，未找到时返回 None

## method: set_port_raw
signature: set_port_raw(port_id_or_name)
brief: 将端口设置为原始模式
aliases: []
keywords: []
parameters:
- port_id_or_name (int | str): 端口ID (0-11) 或端口名称 (A1-A6, B1-B6)

## method: get_port_pin
signature: get_port_pin(port_id_or_name) -> tuple
brief: 获取指定端口的引脚信息
aliases: []
keywords: []
parameters:
- port_id_or_name (int | str): 端口ID (0-11) 或端口名称 (A1-A6, B1-B6)
returns: 引脚元组 (dw0, dw1)

## method: list
signature: list() -> list
brief: 获取所有端口的详细信息列表
aliases: []
keywords: []
returns: 端口信息字典列表，每个字典包含 port_id, port_name, pins, module_type, module_name 等字段

## method: info
signature: info()
brief: 打印所有端口的摘要信息到控制台
aliases: []
keywords: []

## example
```python
import cyberbrick

port = cyberbrick.Port
port.info()
port_id = port.find_module("Button")
pins = port.get_port_pin("A1")
```
