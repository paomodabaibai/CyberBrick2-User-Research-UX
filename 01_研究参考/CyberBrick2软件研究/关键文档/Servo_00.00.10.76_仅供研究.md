---
symbol: "cyberbrick.Servo"
name: "Servo"
lang: "zh"
kind: "class"
aliases: ["舵机"]
keywords: ["角度控制", "连续旋转", "速度控制", "零点校准"]
category: "motion"
related: ["Port"]
methods: ["change_mode", "reset", "angle", "angle_speed", "angle_limit", "get_angle_feedback", "set_zero_position", "get_zero_position_offset", "set_continuous_speed", "deinit"]
constants: ["MODE_IDLE", "MODE_ANGLE", "MODE_CONTINUOUS", "ANGLE_LIMIT_MAX", "ANGLE_LIMIT_MIN"]
common_tasks: ["切换或获取舵机工作模式", "恢复出厂默认参数", "设置或获取目标角度，自动切换到角度模式", "设置或获取角度模式运行速度", "设置或获取角度限位值", "获取舵机当前实际角度（反馈值）", "设置当前位置为零位（物理角度需在 165°±10° 内）", "获取零位偏移量"]
---

# cyberbrick.Servo

brief: 标准舵机模块，支持角度模式和旋转模式

## import
```python
import cyberbrick
servo = cyberbrick.Servo(port='A1')
```

constructor_example: servo = cyberbrick.Servo(port='A1')

## constructor
signature: Servo(port)
example: servo = cyberbrick.Servo(port='A1')
parameters:
- port (int or str): 端口ID (0-11) 或端口名称 (A1-A6 或 B1-B6)

## constants
- MODE_IDLE (int) = 0: IDLE模式，舵机不出力（上电默认）
- MODE_ANGLE (int) = 1: 角度模式，闭环控制舵臂角度
- MODE_CONTINUOUS (int) = 2: 旋转模式，360°连续旋转
- ANGLE_LIMIT_MAX (int) = 150: 软件坐标系最大角度
- ANGLE_LIMIT_MIN (int) = -150: 软件坐标系最小角度

## methods

## method: change_mode
signature: change_mode(mode=None) -> int
brief: 切换或获取舵机工作模式
aliases: []
keywords: []
parameters:
- mode (int, optional): 工作模式: MODE_IDLE(0), MODE_ANGLE(1), MODE_CONTINUOUS(2)
returns: 当前工作模式
example:
```python
import cyberbrick

servo = cyberbrick.Servo('A1')
servo.change_mode(servo.MODE_ANGLE)
print(servo.change_mode())
servo.change_mode(servo.MODE_IDLE)
```

## method: reset
signature: reset() -> None
brief: 恢复出厂默认参数
aliases: []
keywords: []

## method: angle
signature: angle(angle=None) -> float
brief: 设置或获取目标角度，自动切换到角度模式
aliases: []
keywords: []
parameters:
- angle (float, optional): 目标角度（度），范围由 angle_limit 限制，默认 [-150, 150]
returns: 当前目标角度（度）
example:
```python
import cyberbrick

servo = cyberbrick.Servo('A1')
servo.angle_limit(-90, 90)
servo.angle(30)
print(servo.angle())
```

## method: angle_speed
signature: angle_speed(speed=None) -> int
brief: 设置或获取角度模式运行速度
aliases: []
keywords: []
parameters:
- speed (int, optional): 速度百分比，范围 1-100
returns: 当前速度百分比

## method: angle_limit
signature: angle_limit(min=None, max=None) -> tuple
brief: 设置或获取角度限位值
aliases: []
keywords: []
parameters:
- min (float, optional): 最小角度，范围 [-150, 150]，必须小于 max
- max (float, optional): 最大角度，范围 [-150, 150]
returns: (min, max) 角度限位元组
example:
```python
import cyberbrick

servo = cyberbrick.Servo('A1')
servo.angle_limit(-90, 90)
print(servo.angle_limit())
servo.angle(45)
```

## method: get_angle_feedback
signature: get_angle_feedback() -> float
brief: 获取舵机当前实际角度（反馈值）
aliases: []
keywords: []
returns: 当前角度（度，软件坐标系 [-150, 150]）

## method: set_zero_position
signature: set_zero_position() -> float
brief: 设置当前位置为零位（物理角度需在 165°±10° 内）
aliases: []
keywords: []
returns: 零位偏移值（度）
example:
```python
import cyberbrick

servo = cyberbrick.Servo('A1')

# 调用前请先将舵臂调整到接近中位
offset = servo.set_zero_position()
print(offset)
```

## method: get_zero_position_offset
signature: get_zero_position_offset() -> float
brief: 获取零位偏移量
aliases: []
keywords: []
returns: 零位偏移（度）

## method: set_continuous_speed
signature: set_continuous_speed(speed=None) -> int
brief: 设置或获取旋转模式速度，自动切换到旋转模式
aliases: []
keywords: []
parameters:
- speed (int, optional): 速度百分比 [-100, 100]，正值顺时针，负值逆时针，0停止
returns: 当前旋转速度
example:
```python
import cyberbrick

servo = cyberbrick.Servo('A1')
servo.set_continuous_speed(60)
print(servo.set_continuous_speed())
servo.set_continuous_speed(0)
```

## method: deinit
signature: deinit() -> None
brief: 释放资源
aliases: []
keywords: []

## example
```python
import cyberbrick

servo = cyberbrick.Servo('A1')

# 角度模式
servo.change_mode(servo.MODE_ANGLE)
servo.angle_speed(50)
servo.angle(0)
print(servo.get_angle_feedback())

# 旋转模式
servo.set_continuous_speed(50)
servo.set_continuous_speed(0)

servo.deinit()
```
