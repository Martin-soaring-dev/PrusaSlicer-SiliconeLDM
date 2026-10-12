# 气动硅胶 G-code 代码审计（2026-10-12）

状态：仓库静态审查记录；不是构建、设备协议或实机验收报告。
分支：`docs/requirements-baseline`
用户已确认：手动调压、打印期间基本恒压；单组分硅胶；当前首要目标是生成适用 G-code。
重要边界：本文不假定具体打印机、控制器、固件或硬件命令协议。

## 1. 用户已确认的需求事实

- 目标是为特定硅胶／液态材料打印机定制 PrusaSlicer。
- 采用气动挤出，而非常规 FDM 丝材送料。
- 气压由人工调节，打印期间基本恒定。
- 材料为单组分。
- 当前第一优先级是生成设备可接受、行为正确的 G-code。
- 目前没有提供设备型号、固件、控制器、参考 G-code 或协议说明。

由此，当前不应把多组分混料、颜色预测、逐层配比或空间渐变作为 P0 需求。

## 2. 仓库代码中可以直接确认的事实

### 2.1 已有硅胶模式配置

文件：[src/libslic3r/PrintConfig.hpp](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/master/src/libslic3r/PrintConfig.hpp#L1056)

已定义以下配置项：

- `silicone_mode`
- `silicone_flow_rate`（注释单位 mm³/s）
- `silicone_pressure_on_delay`、`silicone_pressure_off_delay`（ms）
- `silicone_vacuum_retract_time`（ms）
- `silicone_min_speed`、`silicone_max_speed`（mm/s）
- `silicone_speed_ramp_length`（mm）
- `silicone_min_speed_ratio`

这些选项的存在是代码事实；不表示它们均适合当前设备或已被完整使用。

### 2.2 配置默认值及协议假设

文件：[src/libslic3r/PrintConfig.cpp](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/master/src/libslic3r/PrintConfig.cpp#L3948)

当前默认值包括：

- 硅胶模式默认关闭。
- 流量默认值为 7.44 mm³/s。
- Pressure ON delay 默认 150 ms。
- Pressure OFF delay 默认 400 ms。
- Vacuum retract time 默认 0 ms（关闭该项）。
- 最低速度默认 2 mm/s，最高速度默认 30 mm/s。
- Speed ramp length 默认 2 mm，起始比例默认 0.3。

同一配置说明文字把压力控制描述为通过 `M106/M107`，并把回抽描述为真空阀定时。这是当前代码中的设计假设，不是已确认的目标设备协议。特别是流量默认值没有被证明来自你的材料、气压、料筒和喷嘴校准，不能直接当作可靠工艺参数。

### 2.3 已有按流量反算路径速度的模型

文件：[src/libslic3r/Flow.cpp](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/master/src/libslic3r/Flow.cpp#L233)

函数 `Flow::speed_for_silicone` 采用：

`speed = flow_rate / (width × height)`

并把结果限制在最低／最高速度范围内。G-code 生成代码在硅胶模式下会根据该结果改写移动速度（见 [GCode.cpp](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/master/src/libslic3r/GCode.cpp#L3571)）。

这说明仓库已有“给定目标体积流量，反算路径速度”的实现方向。但它依赖流量值可信、线宽和层高合理、速度上下限可实现等条件。速度触及限值时，实际体积流量将不再严格等于配置流量；需用静态测试和校准测试验证其影响。

### 2.4 G-code 生成已有硅胶专用分支

文件：[src/libslic3r/GCode.cpp](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/master/src/libslic3r/GCode.cpp)

静态代码可确认：

- 启用 `silicone_mode` 时，会将该模式设置到 G-code writer。
- 路径移动使用硅胶专用的挤出输出分支；代码注释明确写着“不使用 E 轴，速度控制线宽”。
- 圆弧挤出在硅胶模式下走线性路径回退。
- 回抽分支改为调用硅胶专用的 `retract_silicone`，而非常规 FDM 回抽。
- 开始出料前会调用硅胶专用的 `unretract_silicone`。
- 在硅胶模式下跳过常规 PressureEqualizer，代码注释说明该模式没有 E 轴供其补偿。

这些只能证明存在代码分支和调用点；仍需检查完整输出文本，确认具体命令、顺序、等待指令、移动和起停行为是否符合目标机器。

## 3. 对当前设备条件的判断

### 适用方向

手动恒压、单组分设备不需要为 P0 建立多通道混料模型。优先路径是：

1. 确认运动命令与坐标、单位和移动速度的约定。
2. 确认材料由什么方式启动／停止：手动、独立开关、控制器输出、阀门或其他机制。
3. 确认是否存在可由 G-code 控制的阀／输出，以及其真实命令。
4. 用固定的线宽、层高和路径速度生成一份最小 G-code。
5. 静态检查输出，再按安全流程验证设备执行和沉积结果。

### 需要重点核查的现有假设

- **压力 ON/OFF：** 配置文字默认用 `M106/M107` 控制压力。手动恒压并不能单独证明机器支持、需要或不需要这些命令；必须确认出料是否由可控阀门启停。
- **真空回抽：** 当前设备是否有真空回抽阀、是否可控、是否需要，均未知。默认值为 0 不等于代码不会输出其他起停命令。
- **流量值：** `silicone_flow_rate` 是切片输入参数。必须定义其如何通过称重、体积或固定路径测试得到，不能只依赖默认值。
- **速度坡道：** 配置结构包含 ramp 参数；尚未在本次审查中证明它们的使用位置、覆盖所有路径类型或具有测试。
- **起停时序：** 已有延迟参数，但尚未验证其插入输出的具体位置、单位转换、等待指令及旅行移动的顺序。
- **G-code flavor：** 目标固件未知，因此不能确认所选 flavor、通用风扇命令、等待命令或其他输出对设备有效。
- **几何与边界：** 需要检查窄线、宽线、薄层、短路径、首层、桥接、圆弧回退、旅行移动和路径交汇等情况下的行为。

## 4. 需求状态表

| 项目 | 状态 | 证据／缺口 |
|---|---|---|
| 单组分气动挤出 | 用户已确认 | 当前不要求混料 |
| 手动调压、基本恒压 | 用户已确认 | 实际流量是否稳定仍需测量 |
| 专用硅胶模式 | 代码已存在 | 默认关闭；需要确认配置入口和输出链路 |
| 不依赖 E 轴的路径输出 | 代码中有专用分支 | 必须检查完整生成文件，不能仅凭注释验收 |
| 按流量与线宽／层高计算速度 | 代码已存在 | 流量标定、速度限值影响待验证 |
| M106/M107 控制压力 | 代码说明中的假设 | 目标设备是否支持、是否需要均待确认 |
| 真空回抽 | 代码存在参数与调用分支 | 硬件是否具备此能力待确认 |
| 起停延迟 | 代码存在参数与调用分支 | 输出顺序和时序待测试 |
| 设备可执行 G-code | 未验收 | 缺设备协议和参考输出 |
| 编译与自动化测试 | 本次未验证 | 需运行构建和相关测试 |
| 实机沉积结果 | 未验证 | 需设备、材料和测试方法 |

## 5. 当前代码缺口与验证任务

### P0 — 定义输出契约（阻塞项）

向设备资料或已有成功打印文件确认：

- 打印机、控制器和固件名称／版本。
- G-code flavor 或具体命令解释器。
- XYZ 运动、单位、进给速度和坐标原点约定。
- 出料如何启动／停止；是否有 G-code 控制的阀／数字输出；如有，使用哪些命令及参数。
- 是否存在真空回抽硬件及对应控制方式。
- 机器如何处理延时／等待命令。

在此之前，不要将 `M106/M107`、任何阀门命令、风扇输出或压力设定命令视为可用协议。

### P0 — 建立可复现的最小输出测试

创建一个仅含少量直线、旅行移动和一次出料起停的简单模型，并固定设备配置。自动检查：

- 是否意外出现 E 轴增量、E 轴重置或常规 FDM 回抽。
- 每段出料路径是否按预期输出移动速度。
- 出料开始／结束命令和等待的顺序是否符合已确认协议。
- 首层、普通层、路径结束和程序结束处的行为。
- 配置关闭和开启硅胶模式时的输出差异。

具体期望命令应在拿到协议后再写入测试，不能预先臆造。

### P1 — 验证速度／流量模型

- 验证流量为零、线宽或层高异常、速度限值反算等边界。
- 确认 `speed_for_silicone` 的调用覆盖哪些路径类型。
- 检查 `silicone_speed_ramp_length` 和 `silicone_min_speed_ratio` 是否被使用、在哪些路径生效，以及短路径时的边界行为。
- 制定固定路径测试，记录材料、气压设置、料筒、喷嘴、路径尺寸、打印速度与实际沉积量。
- 在实测前不预设准确度指标。

### P1 — 构建与回归

- 构建项目并运行相关 libslic3r／G-code 测试。
- 新增硅胶模式输出的自动化回归测试。
- 检查关闭硅胶模式时常规 FDM 输出未被意外改变。
- 检查 3MF 保存／重开是否保留相关设备设置（前提是这些参数确实被纳入项目配置持久化）。

本次仅做远程源码静态审查，未运行构建、测试或实机验证，因此不能报告通过。

## 6. 下一步需要的最小设备信息

请优先提供以下任一项，最好是前两项：

1. 打印机／控制器／固件名称，或控制软件名称。
2. 一份已经成功打印的 G-code（可删掉私人路径、文件名等内容）。
3. 出料是人工开关、脚踏、独立阀，还是控制板输出；如有输出控制，请提供设备手册中的命令说明。
4. 若没有可用 G-code，描述开始／停止出料的实际操作步骤。

在取得这些资料前，正确工作是继续核查现有代码、建立输出测试框架，而不是猜测硬件协议。

## 7. 本次审查来源

- [PrintConfig.hpp：硅胶配置字段](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/master/src/libslic3r/PrintConfig.hpp#L1056)
- [PrintConfig.cpp：硅胶参数及其说明／默认值](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/master/src/libslic3r/PrintConfig.cpp#L3948)
- [Flow.cpp：流量到移动速度的计算](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/master/src/libslic3r/Flow.cpp#L233)
- [GCode.cpp：硅胶模式的路径速度分支](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/master/src/libslic3r/GCode.cpp#L3571)
- [GCode.cpp：硅胶模式的起停／回抽分支](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/master/src/libslic3r/GCode.cpp#L3913)
- [需求基线文档](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/docs/requirements-baseline/docs/requirements/SiliconeLDM-Requirements-Baseline.md)
- [气动硅胶挤出需求补充](https://github.com/Martin-soaring-dev/PrusaSlicer-SiliconeLDM/blob/docs/requirements-baseline/docs/requirements/Pneumatic-Silicone-Extrusion.md)
