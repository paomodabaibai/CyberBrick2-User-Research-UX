---
name: cba-api-doc
description: CyberBrick MicroPython API 参考文档。当用户要求编写、修改、调试或理解 CyberBrick MicroPython 代码时使用此 skill。包含所有硬件模块（Motor、Servo、IMU、Joystick、PixelMatrix 等）的类、方法、常量和示例代码。**目录按 mpy 版本号分组**（`cba-api-doc/<XX.XX.XX.XX>/<lang>/<file>.md`，例 `00.00.10.00`）：每次读 API 文档前必须先确定目标 mpy 版本号（优先取 `wiring.json.project.mpy_version`，缺失时再从板端 `bbl_product.get_mpy_version()` 兜底），再挑出"版本号 ≤ 目标且最接近"的那一版来加载。
---

# CyberBrick MicroPython API 参考文档

本 skill 提供 CyberBrick 平台所有硬件模块的 MicroPython API 文档。

文档按 **mpy 版本号** 分目录组织。每个版本目录名是 4 段点分十进制版本号（`XX.XX.XX.XX`，例 `00.00.10.00`），代表"该文档对应的那一版固件的 mpy 版本号"。**文档版本应当 ≤ 板端实际 mpy 版本**——比板端还新的文档里可能含有该固件还没有的 API（按它写出来的代码会在板端 `AttributeError` / `ImportError`）。所以选版本的硬规则是：先确定目标版本号，再挑"版本号 ≤ 目标、且最接近"的那一份文档。**禁止默认直接读"最新版本"**——必须先按下面的「版本选择」流程拿到目标版本号再选 doc。

## 目录结构

```
cba-api-doc/
├── SKILL.md                ← 本文件（索引 + 版本选择规则）
├── 00.00.00.01/            ← 开发/调试预留版本（内容不固定，目录结构和文件清单可能整体替换；专属"精确匹配 + 不回退"规则见 Step 3）
│   └── …（使用前先 list_files_local 探查）
├── <XX.XX.XX.XX>/          ← 一份按 mpy 版本号命名的正式 doc 目录
│   ├── en/  (英文 .md 集合)
│   └── zh/  (中文 .md 集合)
├── <XX.XX.XX.XX>/          ← 另一份正式 doc 目录
│   └── …
└── …（版本目录会随项目演进新增）
```

> **版本目录、以及每份目录下的 .md 清单都不是固定的**：可能新增版本目录；同一硬件的 .md 也可能在不同版本之间被新增、删除、合并、拆分或改名（典型例子：红外接口在旧版可能是单一 `Ir.md`，新版会拆成 `IrTx.md` / `IrRx.md` / `IrMessage.md`；模块文件名也可能换命名风格，例如 `dual_joystick.md` 改名为 `JoystickDual.md`，对应类名也跟着改）。**新加的版本目录可以直接复制进 `cba-api-doc/` 即可，无需回头改本 SKILL.md**——所有版本目录与文件清单都靠 `list_files_local` 实时发现。
> 需要拿到最新真实清单时：先 `list_files_local({ path: "<skill_base_path>" })` 看实际有哪些版本子目录，再 `list_files_local({ path: "<skill_base_path><version>/<lang>/" })` 看每个版本里实际有哪些 .md。`read_skill({ name: "cba-api-doc" })` 返回的 `<skill_base_path>` 即本 skill 的虚拟根路径。**禁止**凭模型记忆或本文里举过的清单 / 命名硬编码。

## 使用规则

### 1. 语言选择

- 用户消息包含中文 → 读取 `<version>/zh/` 目录
- 用户消息为英文或其它语言 → 读取 `<version>/en/` 目录

同一会话内沿用首轮选定的语言；用户明确说"切换为英文 / 中文文档"时再切。

### 2. 版本选择（核心规则：先确定目标 mpy 版本号，再选 doc 版本）

**任何要读 cba-api-doc 下任何 .md 之前**，必须先确定本会话的目标 doc 版本。**绝不允许**凭"目录里最新就是最新"直接读最新版——文档版本可能领先固件 N 版，按一份比板端还新的文档写出来的代码会在板端报错（`AttributeError` / `ImportError` / `TypeError: extra positional argument` 等），因为新 API 在旧固件里根本不存在。

#### Step 1：取目标 mpy 版本号

按下面顺序，命中第一条就用它：

**1.1 先读目标 codebase 的 wiring.json**

先确定本轮目标 codebase 路径 `<CODE>`：如果本轮来自 `sync_files_to_board` / pre-sync 版本守卫，沿用同一个 `src`；如果用户指定某块板，使用该板绑定的 codebase 路径。然后调 `read_file_local({ path: "<CODE>/wiring.json" })`，解析 JSON 看 `project.mpy_version` 字段：

- 字段存在且非空白字符串（形如 `"00.00.10.00"`）→ 直接用作**目标版本号**，跳到 Step 2。
- 字段缺失 / `null` / 空字符串 → 进入 1.2 从板端兜底。

**1.2 从板端读 mpy 版本号**

**让板端把版本号直接格式化成字符串打印回来，绝不要自己在脑内做十进制→十六进制→拆字节的心算**（手算进制极易出错，会选到错误的 doc 版本）。板端把那个 32-bit 整数按「大端 4 字节拆开、每字节十进制（0-99 补 2 位、100-255 保持 3 位）、用 `.` 连接」拼好再 print，你直接拿这行字符串用即可：

调 `esp32-s3-mpy-run-repl({ code: "import bbl_product\nv = bbl_product.get_mpy_version()\nprint('.'.join('%02d' % b if b < 100 else '%d' % b for b in v.to_bytes(4, 'big')))", timeoutSeconds: 5 })`：

- 成功，板端回打一个 `XX.XX.XX.XX` 形式的版本字符串（例 `00.00.10.08` / `99.00.00.01` / `255.255.255.255`）→ 直接把这行 stdout 去掉首尾空白后当**目标版本号**，跳到 Step 2，同时记住后面 Step 5 要把它写回 wiring.json。
  - 大端拆分示例（供理解，**不需要你算**，板端已算好）：整数 `2568` = `0x00000A08` → `00.00.10.08`；`0x63000001` → `99.00.00.01`。
- 设备未连接（工具返回 `device_not_connected` 等）→ 进入 1.3。
- 连了板但 `bbl_product` 报错（`ImportError` / `AttributeError`）/ stdout 不是 `XX.XX.XX.XX` 形式 → 进入 1.4。

> **省一次板端往返**：如果本轮还需要读板端实时接线（`cyberbrick.Port.list()`），把它和版本号合并到**同一次** `esp32-s3-mpy-run-repl` 里一起打印，不要拆成两次串口调用。例：`import bbl_product, cyberbrick, ujson as j\nv = bbl_product.get_mpy_version()\nprint('.'.join('%02d' % b if b < 100 else '%d' % b for b in v.to_bytes(4, 'big')))\nprint(j.dumps(cyberbrick.Port.list()))`——按行拆分 stdout 分别解析即可（第一行是版本字符串，第二行是接线 JSON）。

**1.3 串口未连接的固定动作**

**绝对禁止**默认读任何版本的 doc。必须停下来让用户在「连板子」与「自己指定版本号」之间二选一：

- 调 `list_files_local({ path: "<skill_base_path>" })` 列出当前所有可选版本子目录名（如 `00.00.01.00` / `00.00.10.00`）。
- 调 `highlight_element({ elements: ["connect_esp32"] })` 把顶栏「连接 ESP32」按钮闪一下。
- 文本里向用户说明：「我无法识别板端 mpy 版本来挑选匹配的 API 文档：板端尚未连接，且 `<CODE>/wiring.json` 里也没填 `project.mpy_version`。请二选一：① 在编辑器顶栏连上 CB2 后回复『已连接，继续』；② 直接告诉我用哪一版文档（可选版本：上面列出的子目录名）。」
- 调 `suggest_replies` 推一组气泡：`["已连接，继续", "用 <version-1>", "用 <version-2>", ...]`（每个可用版本都生成一个 `"用 <version>"` 气泡，**绝不**默认替用户选一个）。
- **停止本轮**，等用户回复：
  - 用户回 `"已连接，继续"` → 从 Step 1 重头走（这次 1.2 应能成功）。
  - 用户回 `"用 <version>"`（或文本里明确表达"就用 X.X.X.X 版"）→ 把该版本号作为目标版本号，跳到 Step 2，并**在 Step 5 把这个版本号写回 `<CODE>/wiring.json`**（用户主动选中等于明确授权）。
- **绝不允许**跳过版本选择直接默认读最新 / 最早 / 任何一版往下做。

**1.4 板端连了但拿不到 mpy 版本的固定动作**

板端连了但 `bbl_product` 报错（`ImportError` / `AttributeError`）/ stdout 不是 `XX.XX.XX.XX` 形式的版本字符串 → 同样**绝对禁止**默认读任何版本的 doc。处理方式同 1.3，区别仅在气泡里少一个「已连接，继续」（已经连了）：

- 调 `list_files_local({ path: "<skill_base_path>" })` 列出当前所有可选版本子目录名。
- 文本里说明：「板端已连接但**无法识别 mpy 版本**（可能未装 `bbl_product` 模块或固件过旧）。请告诉我用哪一版文档（可选版本：上面列出的子目录名）。」
- 调 `suggest_replies({ suggestions: ["用 <version-1>", "用 <version-2>", ...] })` 推气泡。
- **停止本轮**，等用户回复 `"用 <version>"` → 把该版本号作为目标版本号，跳到 Step 2，并**在 Step 5 把这个版本号写回 `<CODE>/wiring.json`**。
- **绝不允许**自己挑「最早版本」或「最新版本」当兜底。

#### Step 2：列出所有可用版本目录

调 `list_files_local({ path: "<skill_base_path>" })` 拿到全部版本子目录名（不要凭记忆，目录会随项目演进新增）。

#### Step 3：挑出目标版本对应的 doc 目录

**特殊规则：`00.00.00.01` 精确匹配（优先于下面的通用规则）**

若目标版本号恰好为 `00.00.00.01`：

- 检查 Step 2 列出的版本子目录清单中是否包含 `00.00.00.01/`。
- **存在** → 直接选用 `00.00.00.01`。加载时**不要假设**内部目录结构（可能有 `zh/`、`en/`、或两者都有、或直接把 .md 放根下）——先用 `list_files_local({ path: "<skill_base_path>00.00.00.01/" })` 探查实际内容，再根据语言偏好和实际存在的子目录 / 文件来读取所有 .md。跳到 Step 4。
- **不存在** → **禁止回退到其他版本**。必须停下来：
  - 文本告知用户：「目标版本 `00.00.00.01` 的 API 文档目录不存在，无法加载匹配的文档。请告诉我如何处理。」
  - 调 `suggest_replies({ suggestions: ["用其他版本", "继续，不加载文档"] })` 推气泡让用户决定。
  - **停止本轮**，等用户回复后再继续。
  - **绝不允许**在目标为 `00.00.00.01` 时回退选用其他版本的文档。

**通用规则（目标版本号非 `00.00.00.01` 时）**

按"4 段整数序"挑出**版本号 ≤ 目标、且最接近**的那个目录：

- 比较规则：把 `XX.XX.XX.XX` 拆成 4 段，每段 `parseInt`，从左到右逐段比较；**不**能直接用字符串字典序（字符串序里 `"00.00.10.00"` < `"00.00.2.00"`，但实际 `10 > 2`）。
- 若所有版本号都 > 目标（即仅在板端 / wiring 写了一个比所有 doc 还旧的版本时出现）→ 退一步取**版本号最小**的目录，并在文本里告诉用户「所有 doc 版本都比目标 `<target>` 新，可能含有该固件尚未实现的 API，写出来的代码请仔细核对」。

举例（假设目录里有 `00.00.00.01` / `00.00.01.00` / `00.00.10.00`）：

- 目标 `00.00.00.01` → 精确匹配规则命中，直接选 `00.00.00.01`（不走通用规则）
- 目标 `00.00.10.08` → 选 `00.00.10.00`（≤ 10.08 且最近）
- 目标 `00.00.10.00`（恰好相等）→ 选 `00.00.10.00`
- 目标 `00.00.05.00` → 选 `00.00.01.00`（≤ 05.00 且最近；注意 `00.00.00.01` 也 ≤ 目标，但 `00.00.01.00` 更接近）
- 目标 `00.00.00.50` → 选 `00.00.00.01`（≤ 00.50 且最近）

#### Step 4：加载选中版本的文档

按下面"加载方式"用 `read_file_local` 并行读完该目录下所有 .md。

#### Step 5：把版本号写回目标 codebase 的 wiring.json（仅在版本号来自板端 / 用户主动指定时）

**仅当** Step 1.1 读到的 `project.mpy_version` 是空 **且** 目标版本号是这两种来源之一 才做：

- Step 1.2 成功从板端拿到的整数转换后的字符串；
- 用户在 1.3 / 1.4 的气泡里主动选了 `"用 <version>"`（或文本里明确指定了某个 4 段版本号）。

写法：

- 再次 `read_file_local({ path: "<CODE>/wiring.json" })` 拿到最新 JSON 文本（避免与 Step 1.1 之间用户改了别的字段）。
- 解析 JSON → 在 `project` 对象上设 `mpy_version = "<目标版本号>"`（若 `project` 字段本身不存在则新建一个空对象再设）。
- 用 `JSON.stringify(json, null, 2) + "\n"` 序列化 → `write_file_local({ path: "<CODE>/wiring.json", content: <序列化结果> })` 整文件写回。
- **保持其它字段一字不动**——`board_config` / `connections` / `summary` 等结构性字段绝对不能误改，否则会破坏 wiring 工具组的不变量。
- 若 Step 1.1 时就有值（用户已自己填好） → **不**做这一步。

#### Step 6：简短告知用户 + 会话内缓存

- 文本简短报告：「已按目标版本 `<target>` 选用 `<chosen-dir>` 版文档」；
  若做了 Step 5 → 追加「并将版本号写回 `wiring.json.project.mpy_version`」。
- 本会话已经确认过目标版本与 doc 版本之后，后续读 / 写代码继续沿用同一份 doc 版本，**不必每次重跑 Step 1-5**。仅在以下情况重新走一遍：
  - 用户告诉你刷了新固件 / 改了 wiring.json 的 mpy_version
  - 串口断开 / 重连过
  - 同一会话里跑代码时撞到 API 不匹配错误（`AttributeError` / `ImportError` 等）
  - 用户主动要求「切换 / 重选 doc 版本」
  - `sync_files_to_board` 工具返回 `mpy_version_mismatch` 且用户选择「修改代码以匹配板端版本」（详见 `sync_files_to_board` 工具描述）

读取方式（确定 `<version>` 后）：

- `read_file_local({ path: "<skill_base_path><version>/<lang>/<file>" })`

### 3. 加载方式（并行读全部）

确定了 `<version>` 和 `<lang>` 之后：

1. **先**调 `list_files_local({ path: "<skill_base_path><version>/<lang>/" })` 拿到该版本目录下的真实 .md 清单。**禁止**凭模型记忆或本文里出现过的任意文件名 / 清单硬编码——不同版本之间文件可能新增（出现新硬件）、删除、合并、拆分、改名（包括 snake_case ↔ PascalCase 等命名风格变化）。
2. **在单次响应中并行调用** `read_file_local` 把上一步拿到的所有 .md 都读进来。20 出头个文件全部并行只是一次往返。

> **说明性的模块覆盖范围（仅供你理解 API 大致包含哪些类，不是任何具体版本的权威清单）**：顶层模块（如 `cyberbrick`）与端口（`Port`）、电机/舵机/推杆类（`Motor` / `Servo` / `Pushrod`）、传感器类（`IMU` / `DTOF` / `Hall` / `LimitSwitch` / `RotaryEncoder`）、输入类（单/双摇杆、`Knob` / `Slider` / `Button`）、红外类（旧版可能合并为 `Ir`，新版可能拆成 `IrTx` / `IrRx` / `IrMessage`）、显示发光类（`PixelLamp` / `PixelMatrix`）、音频（`Mp3Player`）、无线（`Wireless`）、电源（`PWRManager`）。**新版本可能新增此列表里没有的模块**——具体某版本到底有哪些 .md、叫什么名，一律以 Step 1 的 `list_files_local` 结果为准。

### 4. 使用 API 文档

加载完成后，写代码时严格遵循文档中的：

- 正确的 import 路径和类名
- 方法签名（参数名、类型、默认值）
- 常量名称和值
- 文档中给出的示例模式

**不要**凭模型记忆补全 API、不要拼参数；找不到的方法宁可承认"当前文档里没有这个方法、可能是固件版本不支持"也不要编造。

### 4.1 按文档写的代码在板端报"API 不匹配"错误时的处置

如果按当前选用的 doc 写出的代码在板端运行时报 API 不匹配错误（典型表现：`AttributeError: 'X' has no attribute 'Y'` / `ImportError: cannot import name 'Z'` / `TypeError: extra positional arguments` / `TypeError: missing required argument` / `TypeError: unexpected keyword argument` 等），按下面顺序处置，**不要**自己猜 API 名或参数补丁：

**Step A：先按 §2 Step 6 的触发条件重选一次 doc 版本。**

会话中途固件可能被刷过、`wiring.json.mpy_version` 可能被改过、板子可能被换过——这些都意味着原先缓存的 doc 版本已经不再匹配。完整重跑一遍 §2 Step 1–5（取目标版本 → 列可用版本 → 挑 ≤ 目标且最接近 → 加载新版 doc），看是否切到另一份 doc 后就能消除该错误。

**Step B：如果 Step A 命中的 doc 已经是「版本号 ≤ 目标且最接近」的那一份，仍然报同一个错。**

也就是说，这台板子本来就匹配这一份 doc，没有"更接近"的备选可换。此时**几乎肯定**是：**固件代码里改了这个接口（改名 / 改签名 / 删除参数 / 增加必填参数等），但 API 文档没有同步更新**。这种情况下：

- **不要**凭模型记忆补全 / 猜 API 名 / 猜参数列表；
- **不要**自动找看起来"差不多"的方法 / 参数名替代——一旦猜错，板端要么继续报错、要么静默跑出更隐蔽的错误（错电平 / 错通道 / 错单位）；
- **不要**回退到更早的 doc 版本去"找一个能调通的写法"——更早的 doc 写法对当前固件同样不对，只是错误形式可能不同。

正确动作是**停下来**告知用户：

- 文本里说清三件事：① 已经按目标版本 `<target>` 选用了当前 ≤ 它的最新文档 `<chosen-dir>`；② 按这份文档写的 `<symbol>`（含类名 + 方法名 + 你实际传入的参数）在板端报 `<错误原文摘要>`；③ 怀疑**固件在 `<chosen-dir>` 之后又改了这个接口，但 API 文档没有同步更新**。
- 让用户在两条路里挑一条：① 联系维护方核对 / 补发新一版 doc（写明发现的不一致点，方便对方定位）；② 直接告诉你正确的 API 名 / 参数，你按用户口述去写并在代码里加一行注释标明"按用户口述、非文档"。
- 调 `suggest_replies({ suggestions: ["先按我说的 API 写", "等更新后的文档"] })` 推气泡。
- **停止本轮**，等用户回复后再继续——绝不在没有权威信息（新 doc 或用户口述）的前提下硬猜。

## CB2：当前设备前置

用户问当前接线，或要求"用当前 / 现在 / 已接好的设备"写硬件程序时，先读板端实况，禁止猜：

1. 调 `esp32-s3-mpy-run-repl({ code: "import cyberbrick as c,ujson as j;print(j.dumps(c.Port.list()))", timeoutSeconds: 5 })`
2. 与 `wiring.json` 对比；不一致时说明差异，是否更新 wiring 必须问用户
3. 写全新硬件程序前，设备方案必须来自板端实况或用户确认；没有就先问，不写代码

