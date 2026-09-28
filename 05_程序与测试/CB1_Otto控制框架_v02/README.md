# CB1_Otto控制框架_v02

milk组桌面双足对战机器人的正式控制软件框架（纯软件阶段，**未连接、未驱动实机**）。
v01（`CB1_Otto单步实验_v01`）保留原样，仅作真机实验记录与硬件探针。

本版为**验收整改版**（2026-09-22 深夜第二轮，另含复核收尾轮）：显式使能、
五阶段重排、MicroPython 兼容与时间异常防护、执行器能力配置化、输入新鲜度诚实化、
板端可执行操作流程（run/pause/enable/resume/recover/release）。
整改明细见 `验收整改汇报_v02.md`。

## 一条命令演示

```bash
python run_demo.py
```

回放一段 16 秒的脚本化遥控操作（显式使能 → 左脚第一步 → 右脚交替 → 步态进行中
请求被丢弃 → 双摇杆冲突拒绝 → 同侧拒绝 → K4 中途急停 → 失联 FAULT → 故障中推进
被拒 → 显式恢复），生成 `output/demo_log.csv` + 关节曲线 SVG + 阶段时间线 SVG。

**这是软件回放，不是物理仿真**；步态序列是设计假设，未证明能平衡或前进。
演示运行在 `sim_config.py` 的**虚拟四位置舵机**档案上，绝不掩盖真实配置的缺件。

## 自动化测试

```bash
python -m unittest discover -s tests -v    # 84 项
```

结果存档 `output/测试结果_2026-09-22.txt`。cb1_pwm 驱动用桩 machine 模块在 PC 上
测通道策略；**真实 PWM 行为板端未验证**。

## 显式使能（默认不动作）与完整操作流程

有效遥控帧**永远不会**自动使能任何东西。使能是明确的人工动作，且**入口自己现场重读遥控**（不信任循环暂停前保存的旧输入）。

**推荐流程（连续循环 + Ctrl-C 暂停）**：

```python
import main_v02
main_v02.run()                    # 1+2. 初始化遥控链路并持续读取；Ctrl-C 暂停（力矩保持）
# <Ctrl-C>                        #     暂停：进行中的步态被取消（STOPPED，姿态保持）；
#                                 #     暂停期间 K4/失联检测不运行，输出不被遥控保护
main_v02.SESSION.enable()         # 3. 显式使能：此刻重读遥控；无有效帧或 K4 按住 → 拒绝
main_v02.resume()                 # 4. 继续运行；两杆回中被观察到后才接受迈步
# <Ctrl-C>
main_v02.SESSION.recover()        # 5. 停止/失联后显式恢复：同样现场重读 + K4 门禁 + 回中
main_v02.SESSION.release()        # 6. 退出：关闭 PWM（舵机电源不会被软件切断）
```

**分步调试流程（不进循环，REPL 里一拍一拍看）**：

```python
import main_v02
s = main_v02.start(link=main_v02.RcLink())  # link 必须用关键字传入
s.poll()                                # 持续读取：每次调用 = 读一帧 + 控制器走一拍
s.enable()                              # 显式使能（门禁同上）
s.enable_debug()                        # 调试使能：允许缺件，但每个动作都标记"输出不完整"
s.recover()                             # STOPPED/FAULT 后显式恢复
s.release()                             # 关闭 PWM（停止脉冲；非切断电源）
```

门禁规则：
- 无有效帧或 K4（停止键）按住时拒绝使能；K4 只停止，永不使能/攻击。
- 使能和恢复后触发器**未武装**：必须先观察到两杆回中，才可能产生迈步请求。
  使能瞬间摇杆已推着 → 不会即走。
- 停止、失联、重连都不自动续走；恢复后同样要重新回中。
- **新鲜度限制（不伪造）**：rc_slave_data() 无序号/收包时间戳，任何一次读都可能是
  固件缓存的旧帧。enable/recover 只保证"此刻读过遥控"，无法保证帧是刚生成的。

## 台架操作脚本（bench_v02.py，阶段A交付）

`import bench_v02` 不产生 PWM、不连遥控、不动关节。五类入口按需调用，详见
`台架验证计划_v02.md`：

```python
bench_v02.diag()                       # 只读诊断：关节能力表 + 行走门禁
bench_v02.monitor()                    # 无PWM遥控监测（杆量/K4，Ctrl-C结束）
bench_v02.joint('right_hip', 5, confirmed=True)   # 托住单关节，±10°上限
bench_v02.demo3()                      # 缺件三关节演示（持续标记不完整输出）
bench_v02.gait()                       # 完整四关节单步（严格使能，缺件拒绝）
bench_v02.remote_gait()                # 双杆完整流程（= main_v02.run()）
```

通道一律按关节名→`config.JOINTS` 的 port/gpio 选择；移动类入口要求
`confirmed=True`、拒绝 sim 驱动、结束回零位并关闭 PWM（不切断舵机电源）。

## 架构（依赖单向，上层永不直接碰舵机）

```
rc 10值帧 ─input_adapter─▶ UnifiedInput(±1) ─command_mapper─▶ 事件
─controller(状态机+门禁)─▶ gait_planner(五阶段) ─trajectory(时间驱动)
─▶ joint_model(能力报告+限位拒绝) ─▶ drivers(sim | cb1_pwm配置驱动通道)
timeutil：板端 ticks_ms/ticks_diff，PC 端同语义 30 位回绕时钟
```

五阶段（以左脚为例，S=step_sign，A=ankle_sign）：

| 阶段 | 髋 | 踝 | 物理意图 |
|---|---|---|---|
| prepare | 各自保持当前值 | →0 | 干净的起始接触 |
| weight_shift | 保持 | 双踝 →A·lean | 重心移到支撑脚 |
| unload_swing | **→S·hip（主摆动在这里）** | 摆动踝→A·(lean+lift) | 卸载并完成摆动 |
| land | **保持 S·hip（不再摆）** | →0 | 脚落下触地 |
| stabilize | 保持 | 保持 | 留住下一步所需姿态 |

髋部插值从**真实的当前命令姿态**开始，左右髋各自独立（中途急停冻结的不对称
姿态也能正确续接）。同侧重复步仍显式拒绝。**该序列未证明能平衡或行走。**

## 关键语义

| 要求 | 实现 |
|---|---|
| 默认不动作 | 无自动使能；使能/恢复后须回中 |
| 缺硬件不被隐藏 | 使能行走需 4×(enabled+position+calibrated)，否则拒绝并列出原因 |
| 三关节调试 | `enable_debug()` 独立入口，日志持续标记"输出不完整" |
| 禁用通道无输出 | 驱动按配置决定通道，禁用/连续旋转通道**永不创建 PWM** |
| 时间异常 | dt<0 记 0；单拍 >STALL_MS(500ms) 走行中→FAULT 拒绝跳阶段；新步不继承等待时间 |
| 计时回绕 | 板端 ticks_diff，PC 端同语义回绕时钟，跨界测试通过 |
| 新鲜度诚实 | 官方帧无序号/收包时间 → 不伪造新鲜度，None帧=断链，文档记录局限 |
| 超限拒绝不钳位 | `LimitViolation` 整组拒绝 |
| 停止≠松开 | `stop()` 冻结姿态；`release_output()` 才关闭 PWM 并清空动作残留（不切断舵机电源） |

## 下一步（真机接入）

见 [参数说明与硬件接入清单.md](参数说明与硬件接入清单.md)。切 `DRIVER='cb1_pwm'`
前先读安全清单。左踝换 180° PG001 只需改 `config.py` 的 JOINTS 条目，无需动驱动。
