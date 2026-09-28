# 桌面双足机器人对战：图文与文件索引

整理日期：2026-09-14。目标：10–20 厘米高、短腿、少零件、CyberBrick 遥控、可更换轻量攻击模块。

这里收集的是参考资料和原始文件，尚未制作或验证 CyberBrick 适配程序。图片通过原作者网页链接展示，需要联网；没有把图片另行下载打包。

## 先回答可行性

**Otto 有官方开源代码。** [OttoDIYLib](https://github.com/OttoDIY/OttoDIYLib) 提供前进、后退、转弯与校准示例，代码采用 GPL-3.0。已下载 `OttoDIYLib-main.zip`，并检查压缩包完整性。

**基础行走可以复用，接 CyberBrick 要做移植。** Otto 的 Arduino C++ 库不能直接当作 CyberBrick 的 MicroPython 程序上传。可以保留四个舵机的周期、幅度、相位和校准逻辑，换成 CyberBrick 的舵机输出与遥控输入。原库步态循环会持续执行一段时间；用于实时遥控时应改成分时更新，让停止、转弯和攻击指令仍能及时被处理。原库 `home()` 还会释放舵机保持力，对战时的站立状态需要另行设计。

以上是依据源码作出的工程判断，不是实机测试结论。装上电池与攻击模块后，重心、脚底摩擦、舵机负载和转向效果都需要重新校准。

## 1. Otto DIY：推荐的基础底盘

- [当前打印模型页面](https://www.printables.com/model/31955-otto-diy-build-your-own-robot)
- [作者制作说明](https://hackaday.io/project/11776-otto-diy)
- [官方基础动作代码](https://github.com/OttoDIY/OttoDIYLib/blob/main/src/Otto.cpp)
- [舵机与行走校准示例](https://github.com/OttoDIY/OttoDIYLib/blob/main/examples/Otto_CalibrationWalk/Otto_CalibrationWalk.ino)
- [作者介绍视频](https://www.youtube.com/watch?v=VD6sgTo6NOY)
- [装配视频入口](https://www.youtube.com/watch?v=34v7R0FrSNE)

原版采用 4 个微型舵机、6 个主要打印件。适合保留短腿与脚，重新设计上身。视频入口来自项目 README，本次没有逐段审看视频。

![Otto 官方套件参考图](https://user-images.strikinglycdn.com/res/hrscywv4p/image/upload/c_limit,fl_lossy,h_9000,w_1200,f_auto,q_auto/838564/OttoDIY_officialtobotbuilderkit_lzdp7r.jpg)

图片来源：[Otto 项目历史资料仓库](https://github.com/Open-Hardware-Leaders/OttoDIY)。

### 已下载的旧版 V9 文件

`Otto-V9/3Dprint/` 中有腿、身体、脚、头四种 STL；`Otto-V9/CAD/OttoDIY_v09.step` 是可供修改的 CAD 文件。它们来自 Open-Hardware-Leaders 保存的历史仓库，**不是当前 Printables 版本，也不是已经适配 CyberBrick 的版本**。打印份数、左右件处理与安装应按该版本装配说明核对，不要混用不同代零件。

`Otto-V9/README.md` 保留了原仓库说明和许可表述；软件、模型与媒体的许可不应混为一谈。

## 2. CUBY：最相关的 CyberBrick 机械与遥控参考

[CUBY — CyberBrick Robot Buddy，作者 Viltsu](https://makerworld.com/en/models/2452243-cuby-cyberbrick-robot-buddy)

![CUBY 外观](https://makerworld.bblmw.com/makerworld/model/US44ddfbe406aacf/design/4ba7d19ba0535f36.png?x-oss-process=image/resize,w_1000/format,webp)

页面提供打印配置、可编辑 STEP 的入口、装配 PDF 和遥控 JSON。现有 JSON 可控制腿部与灯光，但作者仍征集完整的遥控行走步态。因此它能减少机械安装与遥控配置的探索，不能据此认定已经能稳定遥控行走或对战。

![CUBY 遥控布局参考](https://makerworld.bblmw.com/makerworld/model/DSM00000002452243/design/5b4d3350b71a99d9.png?x-oss-process=image/format,webp)

页面为 MakerWorld Exclusive License，不能按无限制开源模型理解；再发布改件需按页面许可处理。这里保存来源入口，没有重新分发它的模型。

## 3. Otto Humanoid：参考肩部、手臂和上身空间

[Otto DIY Humanoid 打印模型](https://www.printables.com/model/132407-otto-diy-humanoid-robot)

作者页面介绍使用 6 个微型舵机，沿用 Otto 腿脚并扩展上身。适合参考手臂如何安装；原版手臂不是已经验证过的冲击机构。六舵机也超过 XA004 的四路舵机接口，不能直接按同一接线照装。

本次找到了作者模型页及描述，但页面完整加载受限，未下载并检查附件内容。

## 4. Boxing Santa：双足加出拳的机构案例

[作者的完整制作教程](https://www.instructables.com/3D-Printed-Boxing-Santa-Biped-Robot-With-LOLIN-D32/)

[作者的打印文件页面](https://www.myminifactory.com/object/3d-print-boxing-santa-biped-robot-85558)

![Boxing Santa 双足拳击机器人](https://content.instructables.com/FV3/5A0Z/JPGSGNIV/FV35A0ZJPGSGNIV.jpg?frame=true&width=785&height=1024&fit=bounds)

作者 Sebastian Coddington 使用 3 个舵机完成行走，整机包括双臂共 5 个 SG90。教程有装配、接线、程序与手机 BLE 控制步骤；[动作视频入口](https://www.youtube.com/watch?v=DwLPysVhIJE)来自教程。本次未逐段审看视频。

模型页列出 28 个打印零件，所以不属于你们最想要的少零件底盘。它更适合参考出拳布局和动作。不是 CyberBrick 即插即用方案，文件使用条件以作者页面为准。

## 5. Zowi：可修改 CAD 与短腿结构参考

[Zowi 原始设计仓库](https://github.com/JavierIH/zowi)

已保存 `Zowi/parts/stl/` 中的 body、chassis、footL、footR、leg 五种 STL，以及 `Zowi/parts/freecad/zowi.fcstd`。原版使用 4 个 Futaba 3003 或兼容舵机，比微型 Otto 的选型大，不能默认与 CyberBrick 9g 舵机安装尺寸一致。

原仓库 README 标注 CC-BY-SA 4.0，已保留。下载时未找到独立 LICENSE 文件，许可依据请看 README 与源仓库。

同一仓库还有 [Zowarrior 改型](https://github.com/JavierIH/zowi/tree/master/mods/Zowarrior)，含肩、手臂和拳头的 STL，可参考战斗角色外观；文件名存在不等于已经验证了抗冲击性能。

## 6. CyberBrick 控制参考

- [官方硬件与接口说明](https://wiki.bambulab.com/en/makerworld/cyberbrick/component-list)
- [官方 MicroPython 文档](https://makerworld.com/en/cyberbrick/api-doc/)
- [官方遥控控制程序](https://github.com/CyberBrick-Official/CyberBrick_Controller_Core/blob/master/src/app_rc/app/control.py)
- [官方标准遥控器模型](https://makerworld.com/en/models/1395991)

按公开的 XA004 接收扩展板资料：4 路舵机、2 路直流电机。四个腿部舵机占满舵机接口后，可以研究用电机接口驱动攻击机构；仍需检查电压、总电流和实际套件版本。代码应走 CyberBrick 支持的应用开发方式，而不是把 Arduino 固件直接刷进去。

建议的控制分工：遥控器发送前进、后退、左转、右转、攻击意图；机器人本地程序协调四个关节。操作者不需要分别操作四个关节。第一版采用站稳后攻击，一人一遥控器一机器人；两台同时工作的配对隔离、掉线行为要通过同场测试确认。

## 推荐先看什么

1. 想保留 Otto 外观：先看 Otto CAD 和代码；用 CUBY 参考 CyberBrick 安装与遥控。
2. 想减少主板与电池仓改图：先评估 CUBY，再移植并校准 Otto 式步态；不能假定几何尺寸相同。
3. 想理解拳头机构：看 Boxing Santa；想参考肩臂空间：看 Otto Humanoid。

建议验证顺序：四舵机校准 → 空载前后走与转弯 → 遥控停止/转向 → 加等重假负载 → 接轻攻击模块 → 两台同场对战。现阶段应把“可行”与“已完成实测”分开。

## 文件完整性与来源

`sources.json` 记录已下载文件的来源、大小、SHA-256 和失败项。共保存 9 个 STL、1 个 STEP、1 个 FreeCAD 文件、1 份官方代码 ZIP，以及原仓库 README。未对网格进行打印修复，未验证打印装配与实机运行。
