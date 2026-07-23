# 直顶头审查插件 — AI 自动修复配置规范

> 文档定位：定义直顶头 AI 自动修复工作流的默认配置、可修改项、安全边界和配置加载规则。
>
> 当前文件是配置规范，不是可执行程序。本次仅新增文档，不修改现有 DLL、Python、DLX、PRT 或冻结版本。

---

## 一、元信息

| 项目 | 内容 |
|---|---|
| 配置对象 | `ZD_AutoRepairWorkflow` |
| 审查插件 | `ZD_StraightLifterReview` |
| 审查基线 | `直顶头审查_v1.0_20260723` |
| 工作目录 | `C:\Users\10482\Desktop\ZD` |
| 配置规范版本 | v1.0 |
| 日期 | 2026-07-23 |
| 默认运行模式 | 只读审查与修复规划 |
| 默认保存策略 | 不覆盖原始 PRT |
| 默认触发策略 | 仅用户明确触发 |

---

## 二、配置原则

1. 审查规则和自动修复配置分开管理。
2. R1、R2、R3、R4 的已确认标准不得由 AI 在运行中自行修改。
3. R9 最小圆角允许从 Block UI 获取用户输入，输入 `0 mm` 时关闭 R9。
4. 默认先审查、再生成计划，不直接修改模型。
5. 自动修改必须有明确目标 Tag、Undo Mark 和修复后复审。
6. 配置缺失、损坏或版本不兼容时，工作流降级为只读模式。
7. 任意配置都不能授权程序修改 NX 安装目录。
8. 未收到用户明确触发时，不自动读取、审查或修改 PRT。
9. 不自动提交 Git，不创建 Git 分支或提交记录。
10. 冻结目录始终只读，后续版本不能覆盖旧冻结版本。

---

## 三、配置优先级

配置值按以下优先级生效，前者覆盖后者：

```text
本次 Block UI 用户输入
    ↓
本次工作流调用参数
    ↓
项目机器配置文件
    ↓
本规范定义的默认值
```

以下项目不允许被普通运行参数覆盖：

- 冻结版本路径。
- 禁止覆盖原始 PRT。
- 修改前必须建立回滚点。
- 修改后必须复审。
- 禁止修改 NX 安装目录。
- 禁止将识别失败记为通过。

---

## 四、工作流运行模式

| 模式值 | 中文名称 | 是否修改模型 | 用途 |
|---|---|---:|---|
| `review_only` | 只读审查 | 否 | 执行审查并生成结构化问题清单 |
| `plan_only` | 只生成修复计划 | 否 | 审查后生成 A/B/C 分类和修复建议 |
| `confirm_before_repair` | 确认后修复 | 是 | 对允许修复的问题先展示计划，确认后执行 |
| `auto_repair_safe` | 低风险自动修复 | 是 | 只执行已验收的 A 类修复动作 |
| `verify_only` | 只复审 | 否 | 对已经修改的模型重新执行审查 |
| `rollback_only` | 只回滚 | 是 | 使用当前批次保存的 Undo Mark 或备份恢复 |

默认值：

```text
workflow_mode = plan_only
```

R4 已按既定规则取消人工确认。只有在错误面 Tag、实体 Tag、实体中心校正后的正有符号拔模角和 NX Undo Mark 均满足时，执行器才会直接执行；任一证据缺失则失败关闭并回滚。

R4 已通过 NX2306 专用样件验收，可以启用 `auto_repair_safe` 执行 R4 反向 Draft 修复。
R1、R2、R3、R9 尚未分别完成专用样件验收，仍禁止自动几何修改；这些规则只能生成计划、定位结果或人工确认项。

---

## 五、规则配置

### 5.1 已确认默认值

| 配置项 | 默认值 | 单位 | 是否允许用户修改 | 说明 |
|---|---:|---|---|---|
| `rules.r1.enabled` | `true` | - | 否 | 启用主侧面最小倾角审查 |
| `rules.r1.min_side_angle` | `3.0` | degree | 否 | 小于 `3°` 判错并标红 |
| `rules.r2.enabled` | `true` | - | 否 | 启用 Z 向高度审查 |
| `rules.r2.min_height` | `30.0` | mm | 否 | 低于 `30 mm` 判错 |
| `rules.r3.enabled` | `true` | - | 否 | 启用底面方向审查 |
| `rules.r3.target_plane_to_z` | `90.0` | degree | 否 | 底面与 Z 轴目标角度 |
| `rules.r3.angle_tolerance` | `0.1` | degree | 否 | R3 角度公差 |
| `rules.r4.enabled` | `true` | - | 否 | 启用有符号拔模方向审查 |
| `rules.r4.max_signed_draft` | `0.0` | degree | 否 | 相对 `+Z` 的有符号拔模角大于 `0°` 判错 |
| `rules.r9.enabled` | `false` | - | 是 | 最小圆角输入大于 `0 mm` 时自动启用 |
| `rules.r9.min_radius` | `0.0` | mm | 是 | 来自 `radius_dim0`；为 `0` 时关闭 R9 |

### 5.2 方向定义

- 默认顶出方向使用当前 WCS 正 Z 轴。
- 每次运行必须把实际使用的 Z 轴向量写入结果。
- 如果 WCS 不可用或向量长度异常，停止审查并返回配置/输入错误。
- R4 必须先根据实体中心校正面法向的内外方向，再计算有符号拔模角。
- AI 不得在运行中根据“多数面方向”重新定义 R4 标准。

### 5.3 阈值边界

- R1：`angle < 3.0°` 为失败，等于 `3.0°` 通过。
- R2：`height < 30.0 mm` 为失败，等于 `30.0 mm` 通过。
- R3：与目标值偏差 `> 0.1°` 为失败，等于公差边界通过。
- R4：有符号拔模角 `> 0.0°` 为失败，等于 `0.0°` 通过。
- R9：`min_radius <= 0.0 mm` 时关闭；启用后，实测半径小于输入值为失败。

浮点比较必须使用实现层统一的小数容差，DLL 与 Python 采用同一数值。实现层容差必须写入运行结果的 `numeric_tolerance` 字段。

R2 失败时必须计算：

```text
required_height_increase = max(0, min_height - measured_height)
```

该数值只表示达到 `30 mm` 标准所需的最小高度差，不代表已经确定从顶面、底面或哪个历史特征执行补偿。

---

## 六、选择与批处理配置

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `selection.allow_multiple_bodies` | `true` | 允许一次选择多个实体 |
| `selection.require_solid_body` | `true` | 只接受可审查的实体 |
| `selection.auto_select_single_body` | `false` | 不自动选择零件中的唯一实体 |
| `batch.continue_after_body_error` | `true` | 单个实体审查失败后继续处理其他实体 |
| `batch.repair_one_issue_at_a_time` | `true` | 每次只执行一个可追踪修复动作 |
| `batch.stop_on_model_invalid` | `true` | 模型失效时停止整个修复批次 |
| `batch.rollback_scope` | `single_issue` | 默认只回滚当前问题；模型失效时整批回滚 |

处理顺序：

1. 按用户选择顺序建立实体队列。
2. 每个实体按 R1、R2、R3、R4、R9 顺序审查。
3. 报告按实体 Tag 分组。
4. 高度错误按实体顺序逐个定位和弹窗。
5. 修复队列按风险等级、实体顺序、规则顺序排列。

---

## 七、显示与定位配置

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `display.error_color` | `red` | 错误面显示为红色 |
| `display.keep_error_color_after_ok` | `true` | 用户点击确定后继续保留红色 |
| `display.clear_previous_on_new_run` | `true` | 新一轮审查前清除上一轮审查显示 |
| `display.restore_original_on_clear` | `true` | 清除高亮时恢复原显示属性 |
| `view.animate_navigation` | `true` | 定位时使用移动过程而非瞬移 |
| `view.target_scale` | `fit_body` | 最终视图适应当前错误实体 |
| `view.focus_height_errors_sequentially` | `true` | 多个高度错误逐个定位 |

显示属性恢复必须保存原始颜色、半透明和显示状态。不得用统一默认颜色覆盖用户原本设置。

---

## 八、弹窗与交互配置

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `ui.show_height_error_dialog` | `true` | R2 失败时弹出专用窗口 |
| `ui.height_error_message` | `直顶高度不够，无法正常放下直顶杆；建议至少增加 {required_height_increase} mm` | 固定模板，运行时替换补高量 |
| `ui.show_height_increase_value` | `true` | 在 R2 窗口中显示建议增加高度 |
| `ui.ask_radius_adjustment` | `true` | R9 失败时询问用户是否需要调整圆角 |
| `ui.radius_adjustment_message` | `检测到圆角小于设定值。当前圆角：{measured_radius} mm，目标圆角：{minimum_radius} mm，是否需要调整圆角？` | R9 确认窗口模板 |
| `ui.radius_adjustment_yes_action` | `create_repair_plan` | 用户选择“是”时生成/批准圆角调整计划，不绕过安全门禁 |
| `ui.radius_adjustment_no_action` | `keep_issue_only` | 用户选择“否”时保留问题和红色，不修改模型 |
| `ui.show_success_dialog` | `false` | 成功路径不弹普通信息框 |
| `ui.confirm_b_class_repairs` | `true` | B 类修复必须确认 |
| `ui.confirm_before_save` | `true` | 保存修复后 PRT 前确认 |
| `ui.close_keeps_highlight` | `true` | 关闭结果窗口后保留错误面红色 |

所有窗口文本使用 UTF-8 源文件和 `/utf-8` C++ 编译选项，防止中文乱码。

---

## 九、修复权限配置

### 9.1 风险等级

| 等级 | 默认权限 | 说明 |
|---|---|---|
| A 类 | `allow_after_validation` | 只有已经通过专用样件和 NX 人工验收的动作可以执行 |
| B 类 | `require_confirmation` | 只生成方案；必须人工确认参数和方向 |
| C 类 | `deny` | 不自动修改，只定位和输出人工建议 |

### 9.2 初始规则权限

| 规则 | 初始分类 | 默认动作 |
|---|---|---|
| R1 | B 类 | 输出建议拔模角、基准要求和目标面，不直接改模 |
| R2 | B 类 | 输出 `30 mm - 实测高度` 的补高量并定位实体，不决定从顶部或底部补偿 |
| R3 | B 类 | 输出底面方向修复建议，不自动重建实体 |
| R4 | A 类 | 按实体中心校正外法向，直接对正有符号拔模面执行反向修复；不弹人工确认窗口 |
| R9 解析圆角 | B 类 | 输出当前半径、目标半径和差值，并询问用户是否需要调整；用户确认后生成修复计划，专用样件通过后可升级 A 类 |
| R9 非解析曲面 | C 类 | 只报告，不自动修改 |

任何规则从 B 类升级为 A 类，必须记录：

- 修复动作名称。
- 支持的几何前提。
- 测试模型编号。
- 自动测试结果。
- NX 人工验收结果。
- 回滚测试结果。
- 升级版本号。

---

## 十、回滚与保存配置

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `rollback.create_undo_mark` | `true` | 每次修改前创建 NX Undo Mark |
| `rollback.capture_model_state` | `true` | 保存修改前关键几何状态 |
| `rollback.auto_on_api_error` | `true` | NX API 错误自动回滚 |
| `rollback.auto_on_verify_fail` | `true` | 修复后复审失败默认回滚 |
| `rollback.auto_on_new_issue` | `true` | 产生新错误时默认回滚 |
| `save.overwrite_original_part` | `false` | 禁止覆盖原始 PRT |
| `save.create_backup_before_write` | `true` | 保存修复模型前创建备份 |
| `save.output_suffix` | `_AI修复` | 修复后模型默认文件名后缀 |
| `save.require_user_confirmation` | `true` | 保存前必须确认 |

默认保存示例：

```text
原模型：正确的直顶头.prt
输出模型：正确的直顶头_AI修复.prt
```

实际实现时不得仅按文件名判断是否为同一模型，必须比较规范化绝对路径。

---

## 十一、日志与结果配置

| 配置项 | 默认值 | 说明 |
|---|---|---|
| `output.root` | `C:\Users\10482\Desktop\ZD\data\workflow_runs` | 单次运行输出根目录 |
| `output.encoding` | `utf-8` | JSON、Markdown 和日志编码 |
| `output.pretty_json` | `true` | JSON 使用缩进，便于人工查看 |
| `output.write_before_review` | `true` | 保存修复前审查结果 |
| `output.write_repair_plan` | `true` | 保存修复计划 |
| `output.write_execution_log` | `true` | 保存真实执行记录 |
| `output.write_after_review` | `true` | 保存修复后复审结果 |
| `output.write_markdown_report` | `true` | 生成人类可读报告 |
| `output.atomic_write` | `true` | 先写临时文件，再原子替换正式结果 |

单次运行目录：

```text
data\workflow_runs\<run_id>\
├── review-before.json
├── repair-plan.json
├── repair-execution.json
├── review-after.json
├── model-state.json
├── workflow-report.md
└── error.log
```

---

## 十二、超时与错误处理配置

| 配置项 | 默认值 | 说明 |
|---|---:|---|
| `timeout.review_seconds` | `120` | 单个实体审查超时 |
| `timeout.repair_seconds` | `180` | 单个修复动作超时 |
| `timeout.verify_seconds` | `120` | 单个实体复审超时 |
| `retry.nx_read_count` | `1` | NX 只读 API 临时失败重试次数 |
| `retry.geometry_modify_count` | `0` | 几何修改失败不自动重试 |
| `errors.continue_after_unrecognized_body` | `true` | 单体无法识别时继续其他实体 |
| `errors.fail_closed` | `true` | 不确定时按不可自动修复处理 |

几何修改失败不能自动重复执行，防止同一修改被应用两次。

---

## 十三、未来机器配置文件

后续实现阶段建议生成：

```text
C:\Users\10482\Desktop\ZD\tools\zd_auto_repair_config.json
```

建议初始内容：

```json
{
  "config_version": "1.0",
  "workflow_mode": "plan_only",
  "rules": {
    "r1": {"enabled": true, "min_side_angle": 3.0},
    "r2": {"enabled": true, "min_height": 30.0},
    "r3": {"enabled": true, "target_plane_to_z": 90.0, "angle_tolerance": 0.1},
    "r4": {"enabled": true, "max_signed_draft": 0.0},
    "r9": {"enabled": false, "min_radius": 0.0}
  },
  "selection": {"allow_multiple_bodies": true, "auto_select_single_body": false},
  "rollback": {"create_undo_mark": true, "auto_on_verify_fail": true},
  "save": {"overwrite_original_part": false, "create_backup_before_write": true},
  "output": {"root": "C:\\Users\\10482\\Desktop\\ZD\\data\\workflow_runs", "encoding": "utf-8"}
}
```

机器配置文件不在本次任务中生成。实现时必须对其执行 schema 校验，不能直接信任任意字段。

---

## 十四、配置验收标准

- 缺少配置文件时可使用安全默认值进入 `plan_only`。
- 非法枚举、负数超时、无效路径和未知规则字段会被明确拒绝。
- R9 输入 `0 mm` 时实际关闭。
- Block UI 输入可以覆盖本次 R9 值，但不能修改 R1-R4 固定标准。
- DLL 与 Python 读取到的有效配置一致。
- 配置错误不会导致模型修改。
- 任意修复模式都不能绕过 Undo Mark、复审和回滚要求。
- 保存操作不会覆盖原始 PRT。
- 日志和 JSON 中文内容无乱码。

---

## 十五、实施结论

本配置规范完成后，下一阶段程序应先实现配置读取和校验，再实现只读工作流。第一版运行模式固定为 `plan_only`，待某个单规则修复动作完成专用模型、回滚和 NX 人工验收后，再单独开放该动作的执行权限。
