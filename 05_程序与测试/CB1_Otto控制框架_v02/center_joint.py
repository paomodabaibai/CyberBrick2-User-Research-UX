"""center_joint.py - 单关节 90° 机械对中命令（Otto V9 腿部重新对中计划，阶段二现场用）。

IMPORT-SAFE: importing this module creates NO PWM object and never moves
anything - every action is behind an explicit function.

板上 REPL 用法：
    import center_joint
    center_joint.list()                       # 只读：四关节 端口/GPIO/类型
    center_joint.send('left_hip', confirmed=True)        # 90°中位并保持
    center_joint.send('right_hip', confirmed=True, seconds=5)  # 保持5秒后自动关
    center_joint.off()                        # 立即关闭输出（PWM off）

规则（由代码强制）：
- 通道按关节名 -> config.JOINTS 的 port/gpio 查找，绝不按数组索引猜舵机。
- 一次只给一路发脉冲：走 driver.write_one()，其他通道不创建 PWM。
- 拒绝 disabled 通道与 actuator='continuous' 关节：S2 现为 360° 连续舵机，
  发"90°定位"命令会被拒绝（等换装 180° PG001 并改 config 后自动放行）。
- 90° = 电气中位（PULSE_AT_0_US 与 PULSE_AT_180_US 的线性中点），故意不套
  center/trim——对中必须显示原始电气中位，trim 是装好舵盘之后的微调。
- 首次中位命令可能让舵机突然转动（软件不知道断电前输出轴的位置）：send()
  必须带 confirmed=True，且只在"托住机器人/已拆开该路舵盘机械连接"时使用。
- 明确的关闭输出操作：off() 或 send(..., seconds=N) 自动关闭。关 PWM 不等于
  切断舵机电源，物理开关负责。
"""
import time

import config
import joint_model
import timeutil
from drivers import create_driver

_driver = None
_driver_cfg = None
_active = None   # joint currently pulsed; a switch or off() clears it


def _get_driver(cfg=None):
    global _driver, _driver_cfg
    cfg = cfg or config
    if _driver is None or _driver_cfg is not cfg:
        _driver = create_driver(joint_model.JointModel(cfg), cfg)
        _driver_cfg = cfg
    return _driver


def list(cfg=None):
    """Read-only: print the four joints with port/gpio/type. No PWM."""
    cfg = cfg or config
    jm = joint_model.JointModel(cfg)
    print('%-11s %-4s %-5s %-8s %-11s %-6s'
          % ('joint', 'port', 'gpio', 'enabled', 'actuator', 'calibrated'))
    for name in cfg.JOINT_ORDER:
        j = cfg.JOINTS[name]
        print('%-11s %-4s %-5d %-8s %-11s %-6s'
              % (name, j['port'], j['gpio'], j['enabled'], j['actuator'],
                 j['calibrated']))
    blockers = jm.walk_blockers()
    if blockers:
        print('walking NOT ready: %s' % '; '.join(blockers))
    return None


def send(name, angle=90.0, seconds=None, cfg=None, confirmed=False,
         allow_sim=False):
    """Pulse ONE named channel at an absolute angle (default 90 = center).

    One channel at a time is ENFORCED: switching to a different joint first
    releases the previous channel's PWM (no two joints ever pulse together
    even if off() was forgotten). seconds=N waits N seconds and then turns
    the output off - the off() runs even if the wait is interrupted by
    Ctrl-C or any exception.
    """
    cfg = cfg or config
    if name not in cfg.JOINT_ORDER:
        raise ValueError('unknown joint %r; choose from %s'
                         % (name, cfg.JOINT_ORDER))
    if not confirmed:
        raise RuntimeError('centering refused: pass confirmed=True only with '
                           'the robot SUPPORTED / that horn disconnected - '
                           'the servo may JUMP to center unexpectedly')
    j = cfg.JOINTS[name]
    if not j.get('enabled', True):
        raise RuntimeError('centering refused: %s (%s/GPIO%d) is disabled in '
                           'config' % (name, j['port'], j['gpio']))
    if j.get('actuator') != 'position':
        raise RuntimeError('centering refused: %s (%s/GPIO%d) is a %r '
                           'actuator - a continuous servo must never receive '
                           'a 90-degree position command'
                           % (name, j['port'], j['gpio'], j['actuator']))
    if cfg.DRIVER == 'sim' and not allow_sim:
        raise RuntimeError('centering refused: DRIVER=%r is the PC-only '
                           'simulation driver - no servo would move. Use '
                           'allow_sim=True only for a software rehearsal.'
                           % cfg.DRIVER)
    global _active
    if _driver is not None and _active is not None and _active != name:
        off()   # one-channel guarantee: close the previous joint first
    drv = _get_driver(cfg)
    print('center %s (%s/GPIO%d) -> %.1f deg%s; PWM off %s'
          % (name, j['port'], j['gpio'], angle,
             ', hold %ds' % seconds if seconds else ' until off()',
             'in %ds' % seconds if seconds else 'on off()'))
    drv.write_one(name, angle)
    _active = name
    if seconds is not None:
        try:
            _sleep(seconds)
        finally:
            off()   # guaranteed even on KeyboardInterrupt/exceptions
    return drv


def off():
    """Close PWM output (stop pulses; servo POWER stays on)."""
    global _driver, _active
    if _driver is not None:
        _driver.release()
        print('center: PWM off (servo power stays on)')
    _active = None


def _sleep(seconds):
    if hasattr(time, 'sleep_ms'):
        time.sleep_ms(int(seconds * 1000))
    else:
        time.sleep(seconds)
