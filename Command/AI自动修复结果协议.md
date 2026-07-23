# 直顶头审查插件 — AI 自动修复结果协议

> 文档定位：本文件是审查 DLL、NX Python、AI 修复规划器、NX 修复执行器和复审器之间的数据合同。
>
> 所有组件必须按本协议读写结果，不能各自发明字段。识别失败、修复失败和回滚必须如实记录，不能返回固定成功。

---

## 一、协议元信息

| 项目 | 内容 |
|---|---|
| 协议名称 | ZD AI Auto Repair Result Protocol |
| 协议版本 | `1.0` |
| 适用插件 | `ZD_StraightLifterReview` |
| 基线版本 | `直顶头审查_v1.0_20260723` |
| 文件编码 | UTF-8 |
| 数据格式 | JSON |
| 日期时间 | ISO 8601，包含时区 |
| 长度单位 | `mm` |
| 角度单位 | `degree` |
| Tag 表示 | JSON 字符串 |

NX Tag 统一写为字符串，避免不同语言、平台或 JSON 解析器对整数范围处理不一致。无 Tag 时使用 `null`，不能用 `0` 冒充有效对象。

---

## 二、协议文件

| 文件 | 生成阶段 | 必须生成 | 说明 |
|---|---|---:|---|
| `review-before.json` | 修复前审查 | 是 | 只读审查结果和问题清单 |
| `repair-plan.json` | 修复规划 | 是 | 问题分级、修复动作和确认要求 |
| `repair-execution.json` | 修复执行 | 有执行时必须 | 实际 NX 操作和返回结果 |
| `review-after.json` | 修复后复审 | 有执行时必须 | 修复后完整复审结果 |
| `model-state.json` | 修改前后 | 有执行时必须 | 模型和目标对象的关键状态 |
| `workflow-report.md` | 批次结束 | 是 | 面向用户的汇总报告 |
| `error.log` | 任意异常 | 有异常时必须 | 原始错误和调用阶段 |

未进入修复执行时，不能伪造空的成功执行记录；应在 `repair-plan.json` 中明确写明 `execution_required: false` 或等待确认。

---

## 三、通用顶层结构

所有 JSON 文件共享以下顶层字段：

| 字段 | 类型 | 必须 | 说明 |
|---|---|---:|---|
| `protocol_version` | string | 是 | 固定为 `1.0` |
| `document_type` | enum | 是 | 当前文件类型 |
| `run_id` | string | 是 | 单次运行唯一编号 |
| `created_at` | string | 是 | ISO 8601 时间 |
| `producer` | object | 是 | 生成组件和版本 |
| `status` | enum | 是 | 当前文档状态 |
| `summary` | string | 是 | 中文简要结论 |
| `context` | object | 是 | NX 会话、Part、WCS 和输入上下文 |
| `data` | object | 是 | 当前文件的业务数据 |
| `errors` | array | 是 | 错误数组，无错误时为空数组 |

### 3.1 `document_type` 枚举

- `review_before`
- `repair_plan`
- `repair_execution`
- `review_after`
- `model_state`

### 3.2 通用 `status` 枚举

- `success`：当前阶段成功完成。
- `partial_success`：部分对象完成，部分对象失败或待确认。
- `waiting_human_confirmation`：需要人工确认后才能继续。
- `no_issue`：审查完成且没有发现问题。
- `error`：阶段执行失败。
- `cancelled`：用户取消。
- `rolled_back`：已经执行回滚。

---

## 四、生产者信息 `producer`

```json
{
  "name": "ZD_StraightLifterReview",
  "component": "nx_python",
  "component_version": "1.0.0",
  "source_baseline": "直顶头审查_v1.0_20260723"
}
```

`component` 可取：

- `nx_dll`
- `nx_python`
- `repair_planner`
- `nx_repair_executor`
- `repair_verifier`
- `workflow_controller`

---

## 五、上下文结构 `context`

| 字段 | 类型 | 必须 | 说明 |
|---|---|---:|---|
| `nx_version` | string | 是 | 例如 `NX2306` |
| `part_path` | string/null | 是 | 当前 Part 规范化绝对路径 |
| `part_name` | string | 是 | Part 名称 |
| `part_modified_before_run` | boolean | 是 | 运行前是否已有未保存修改 |
| `workflow_mode` | enum | 是 | 配置定义的运行模式 |
| `wcs_z_axis` | number[3] | 是 | 实际使用的 Z 轴单位向量 |
| `numeric_tolerance` | object | 是 | 浮点比较容差 |
| `selected_body_tags` | string[] | 是 | 用户选择的实体 Tag，保持选择顺序 |
| `user_inputs` | object | 是 | 本次 UI 输入 |

`user_inputs` 初始结构：

```json
{
  "min_radius": {
    "value": 0.0,
    "unit": "mm",
    "source": "block_ui_radius_dim0"
  }
}
```

---

## 六、实体结果结构 `body_results`

`review-before.json` 和 `review-after.json` 的 `data.body_results` 为数组，每个元素对应一个实体：

| 字段 | 类型 | 必须 | 说明 |
|---|---|---:|---|
| `body_tag` | string | 是 | 实体 Tag |
| `body_name` | string/null | 是 | 实体名称 |
| `selection_index` | integer | 是 | 用户选择顺序，从 0 开始 |
| `review_status` | enum | 是 | 实体总体审查状态 |
| `bounding_box` | object | 是 | 实体包围盒 |
| `rule_results` | array | 是 | R1/R2/R3/R4/R9 结果 |
| `issue_ids` | string[] | 是 | 该实体关联的问题编号 |
| `display_actions` | array | 是 | 标红、定位等显示动作 |

`review_status` 枚举：

- `pass`
- `fail`
- `unrecognized`
- `error`
- `not_checked`

包围盒格式：

```json
{
  "min": [0.0, 0.0, 0.0],
  "max": [10.0, 10.0, 30.0],
  "unit": "mm"
}
```

---

## 七、统一规则结果 `rule_result`

每条规则使用同一基础结构：

| 字段 | 类型 | 必须 | 说明 |
|---|---|---:|---|
| `rule_id` | enum | 是 | `R1`、`R2`、`R3`、`R4`、`R9` |
| `rule_name` | string | 是 | 中文名称 |
| `enabled` | boolean | 是 | 本次是否启用 |
| `status` | enum | 是 | 规则结果 |
| `standard` | object | 是 | 标准和单位 |
| `measurements` | array | 是 | 实测数据 |
| `failed_object_tags` | string[] | 是 | 失败对象 Tag |
| `reason_code` | string/null | 是 | 机器可读原因码 |
| `reason` | string | 是 | 中文原因 |
| `evidence` | object | 是 | 判定依据 |

规则 `status` 枚举：

- `pass`
- `fail`
- `disabled`
- `unrecognized`
- `error`

识别失败必须使用 `unrecognized`，不得写成 `pass`。

---

## 八、各规则测量字段

### 8.1 R1 主侧面最小倾角

`measurements` 每个元素：

```json
{
  "face_tag": "37140",
  "angle_to_z": 2.5,
  "unit": "degree",
  "threshold": 3.0,
  "comparison": "gte",
  "status": "fail"
}
```

R1 原因码：

- `R1_ANGLE_BELOW_MINIMUM`
- `R1_SIDE_FACE_COUNT_INVALID`
- `R1_SIDE_FACE_UNRECOGNIZED`
- `R1_MEASUREMENT_ERROR`

### 8.2 R2 Z 向高度

```json
{
  "body_tag": "37136",
  "z_min": 0.0,
  "z_max": 28.0,
  "height": 28.0,
  "required_height_increase": 2.0,
  "unit": "mm",
  "threshold": 30.0,
  "comparison": "gte",
  "status": "fail"
}
```

R2 原因码：

- `R2_HEIGHT_BELOW_MINIMUM`
- `R2_BOUNDING_BOX_ERROR`

R2 失败的用户提示模板：`直顶高度不够，无法正常放下直顶杆；当前高度 {height} mm，建议至少增加 {required_height_increase} mm。`

`required_height_increase` 的计算方式固定为 `max(0, threshold - height)`。该字段表示最小补高量，不代表已确定具体拉伸方向或修复特征。

### 8.3 R3 底面方向

```json
{
  "face_tag": "37145",
  "plane_to_z_angle": 89.7,
  "target_angle": 90.0,
  "deviation": 0.3,
  "tolerance": 0.1,
  "unit": "degree",
  "status": "fail"
}
```

R3 原因码：

- `R3_BOTTOM_ANGLE_OUT_OF_TOLERANCE`
- `R3_BOTTOM_FACE_UNRECOGNIZED`
- `R3_MULTIPLE_BOTTOM_CANDIDATES`
- `R3_MEASUREMENT_ERROR`

R3 的 `evidence` 必须记录底面候选过滤依据，证明侧面没有被误选为底面。

### 8.4 R4 有符号拔模方向

```json
{
  "face_tag": "37140",
  "raw_normal": [0.0, 0.052336, 0.99863],
  "outward_normal": [0.0, 0.052336, 0.99863],
  "signed_draft_angle": 3.0,
  "maximum_allowed": 0.0,
  "unit": "degree",
  "status": "fail"
}
```

R4 的 `evidence` 必须包含：

- 实体中心。
- 面采样点。
- 原始法向。
- 校正后的向外法向。
- 实际 Z 轴。
- 有符号拔模角计算结果。

R4 原因码：

- `R4_POSITIVE_SIGNED_DRAFT`
- `R4_OUTWARD_NORMAL_UNRESOLVED`
- `R4_FACE_UNRECOGNIZED`
- `R4_MEASUREMENT_ERROR`

R4 自动修复权限：

- 当实体中心校正后的有符号拔模角明确大于 `0°`，且目标实体 Tag、错误面 Tag 和方向证据完整时，`repairability` 必须为 `auto_repair_allowed`。
- 此时 `requires_human_confirmation` 必须为 `false`，修复计划的 `approval_status` 为 `not_required`，并进入 `ready_to_repair` 队列。
- R4 不弹人工确认窗口；执行器仍必须创建 Undo Mark、记录实际目标、执行后完整复审，失败时回滚。
- 无法确定实体中心校正方向或面 Tag 时，输出 `unrecognized`，不得伪装为可执行 R4 修复。

### 8.5 R9 最小圆角

```json
{
  "face_tag": "37150",
  "surface_type": "cylindrical",
  "radius": 1.5,
  "minimum_radius": 2.0,
  "suggested_radius_increase": 0.5,
  "unit": "mm",
  "status": "fail"
}
```

R9 原因码：

- `R9_RADIUS_BELOW_MINIMUM`
- `R9_DISABLED_BY_ZERO_INPUT`
- `R9_NON_ANALYTIC_SURFACE`
- `R9_RADIUS_MEASUREMENT_ERROR`

R9 失败时必须生成交互请求：

```json
{
  "interaction_type": "radius_adjustment_confirmation",
  "message": "检测到圆角小于设定值。当前圆角：1.5 mm，目标圆角：2.0 mm，是否需要调整圆角？",
  "options": ["yes", "no"],
  "default_option": "no",
  "response": null
}
```

- 用户选择 `yes`：将响应写为 `yes`，生成或批准对应圆角修复计划；仍需满足 Undo Mark、目标 Tag、修复动作注册和复审要求。
- 用户选择 `no`：将响应写为 `no`，保留 R9 问题和红色提示，不修改模型。
- 用户关闭窗口：按 `no` 处理，并记录 `dismissed`，不能默认执行修复。

---

## 九、统一问题对象 `issue`

`review-before.json` 的 `data.issues` 必须包含所有失败和无法可靠识别项：

| 字段 | 类型 | 必须 | 说明 |
|---|---|---:|---|
| `issue_id` | string | 是 | 批次内唯一问题编号 |
| `rule_id` | enum | 是 | 关联规则 |
| `body_tag` | string | 是 | 目标实体 |
| `face_tags` | string[] | 是 | 相关面，无明确面时为空数组 |
| `issue_type` | enum | 是 | `rule_failure`、`unrecognized`、`runtime_error` |
| `severity` | enum | 是 | `warning`、`error`、`critical` |
| `reason_code` | string | 是 | 机器可读原因码 |
| `reason` | string | 是 | 中文说明 |
| `measured` | object | 是 | 实测值摘要 |
| `required` | object | 是 | 标准值摘要 |
| `location` | object | 是 | 定位数据 |
| `repairability` | enum | 是 | 自动修复分类 |
| `risk_level` | enum | 是 | 风险等级 |
| `requires_human_confirmation` | boolean | 是 | 是否需要人工确认 |
| `suggested_delta` | object/null | 是 | 建议调整量；R2 为补高量，R9 为圆角增加量 |
| `interaction_request` | object/null | 是 | 需要用户选择时的交互请求，R9 失败时必须提供 |

`repairability` 枚举：

- `auto_repair_allowed`
- `human_confirm`
- `manual_only`
- `not_repairable`

`risk_level` 枚举：

- `low`
- `medium`
- `high`
- `prohibited`

问题编号建议格式：

```text
<RULE>-<BODY_TAG>-<三位序号>
```

例如：`R4-37136-001`。

---

## 十、修复计划 `repair_plan`

`repair-plan.json` 的 `data.plan_items` 每项结构：

| 字段 | 类型 | 必须 | 说明 |
|---|---|---:|---|
| `plan_id` | string | 是 | 修复计划编号 |
| `issue_id` | string | 是 | 对应问题编号 |
| `action_id` | string/null | 是 | 已注册修复动作名称 |
| `action_version` | string/null | 是 | 动作版本 |
| `target_body_tag` | string | 是 | 目标实体 |
| `target_face_tags` | string[] | 是 | 目标面 |
| `parameters` | object | 是 | 修复参数、单位和来源 |
| `preconditions` | array | 是 | 执行前提 |
| `expected_result` | object | 是 | 预期审查结果 |
| `affected_objects` | array | 是 | 预计影响对象 |
| `risk_level` | enum | 是 | 风险 |
| `approval_status` | enum | 是 | 审批状态 |
| `execution_required` | boolean | 是 | 是否需要执行修改 |

`approval_status` 枚举：

- `not_required`
- `waiting_human_confirmation`
- `approved`
- `rejected`
- `prohibited`

没有注册修复动作时，`action_id` 必须为 `null`，并将 `execution_required` 设为 `false`。不得用不存在的动作名称伪装可修复。

---

## 十一、修复执行记录 `repair_execution`

每个 `execution_item` 必须记录计划与实际操作的差异：

| 字段 | 类型 | 必须 | 说明 |
|---|---|---:|---|
| `execution_id` | string | 是 | 执行编号 |
| `plan_id` | string | 是 | 对应计划 |
| `started_at` | string | 是 | 开始时间 |
| `finished_at` | string/null | 是 | 结束时间 |
| `status` | enum | 是 | 执行状态 |
| `undo_mark_id` | string/null | 是 | NX Undo Mark 标识 |
| `actual_action` | string | 是 | 实际调用动作 |
| `actual_targets` | object | 是 | 实际修改对象 |
| `actual_parameters` | object | 是 | 实际使用参数 |
| `nx_result` | object | 是 | NX API 返回摘要 |
| `created_tags` | string[] | 是 | 新建对象 Tag |
| `modified_tags` | string[] | 是 | 修改对象 Tag |
| `deleted_tags` | string[] | 是 | 删除对象 Tag；默认应为空 |
| `rollback` | object | 是 | 回滚状态 |

执行 `status` 枚举：

- `not_started`
- `running`
- `success`
- `failed`
- `cancelled`
- `rolled_back`

`rollback` 结构：

```json
{
  "available": true,
  "required": false,
  "used": false,
  "status": "not_used",
  "reason": ""
}
```

---

## 十二、修复后复审 `review_after`

复审结果必须重新执行完整 R1、R2、R3、R4、R9，不仅检查被修复的一条规则。

`data.verification` 至少包含：

| 字段 | 类型 | 必须 | 说明 |
|---|---|---:|---|
| `verified_issue_ids` | string[] | 是 | 已复审问题 |
| `resolved_issue_ids` | string[] | 是 | 已解决问题 |
| `remaining_issue_ids` | string[] | 是 | 仍存在问题 |
| `new_issue_ids` | string[] | 是 | 修复后新增问题 |
| `model_valid` | boolean | 是 | 模型是否仍有效 |
| `unselected_bodies_unchanged` | boolean | 是 | 未选实体是否未被影响 |
| `verification_status` | enum | 是 | 总体验证状态 |

`verification_status` 枚举：

- `repair_success`
- `partial_success`
- `repair_failed`
- `new_issue_detected`
- `model_invalid`
- `verification_error`

只有 `repair_success` 且 `new_issue_ids` 为空时，工作流才可以报告自动修复成功。

---

## 十三、错误对象 `error`

```json
{
  "error_id": "ERR-20260723-001",
  "stage": "repair_execution",
  "code": "NX_API_ERROR",
  "message": "NX API 返回错误",
  "details": "原始异常文本",
  "body_tag": "37136",
  "face_tags": ["37140"],
  "recoverable": true,
  "rollback_required": true,
  "timestamp": "2026-07-23T10:00:00+08:00"
}
```

`stage` 可取：

- `config_loading`
- `input_collection`
- `review_before`
- `repair_planning`
- `repair_execution`
- `review_after`
- `rollback`
- `result_writing`

原始异常可以写入 `details`，但 `message` 必须提供可理解的中文摘要。

---

## 十四、完整 `review-before.json` 示例

```json
{
  "protocol_version": "1.0",
  "document_type": "review_before",
  "run_id": "20260723-100000-001",
  "created_at": "2026-07-23T10:00:00+08:00",
  "producer": {
    "name": "ZD_StraightLifterReview",
    "component": "nx_python",
    "component_version": "1.0.0",
    "source_baseline": "直顶头审查_v1.0_20260723"
  },
  "status": "partial_success",
  "summary": "完成1个实体审查，发现1个R2问题。",
  "context": {
    "nx_version": "NX2306",
    "part_path": "C:\\example\\sample.prt",
    "part_name": "sample.prt",
    "part_modified_before_run": false,
    "workflow_mode": "plan_only",
    "wcs_z_axis": [0.0, 0.0, 1.0],
    "numeric_tolerance": {"linear": 0.000001, "angular": 0.000001},
    "selected_body_tags": ["37136"],
    "user_inputs": {
      "min_radius": {"value": 0.0, "unit": "mm", "source": "block_ui_radius_dim0"}
    }
  },
  "data": {
    "body_results": [
      {
        "body_tag": "37136",
        "body_name": null,
        "selection_index": 0,
        "review_status": "fail",
        "bounding_box": {"min": [0.0, 0.0, 0.0], "max": [10.0, 10.0, 28.0], "unit": "mm"},
        "rule_results": [],
        "issue_ids": ["R2-37136-001"],
        "display_actions": ["focus_body", "show_height_error_dialog"]
      }
    ],
    "issues": [
      {
        "issue_id": "R2-37136-001",
        "rule_id": "R2",
        "body_tag": "37136",
        "face_tags": [],
        "issue_type": "rule_failure",
        "severity": "error",
        "reason_code": "R2_HEIGHT_BELOW_MINIMUM",
        "reason": "直顶高度不够，无法正常放下直顶杆；当前高度28.0 mm，建议至少增加2.0 mm。",
        "measured": {"value": 28.0, "unit": "mm"},
        "required": {"comparison": "gte", "value": 30.0, "unit": "mm"},
        "suggested_delta": {"value": 2.0, "unit": "mm", "meaning": "required_height_increase"},
        "interaction_request": null,
        "location": {"body_center": [5.0, 5.0, 14.0], "unit": "mm"},
        "repairability": "human_confirm",
        "risk_level": "medium",
        "requires_human_confirmation": true
      }
    ]
  },
  "errors": []
}
```

示例只用于说明字段，不代表真实模型结论。

---

## 十五、文件写入规则

1. 文件统一使用 UTF-8。
2. JSON 不允许注释、尾逗号或 `NaN/Infinity`。
3. 写入正式文件前先写同目录临时文件。
4. 完整序列化和校验通过后，再原子替换正式文件。
5. 结果写入失败时不得继续执行模型修改。
6. 同一 `run_id` 下所有文件必须引用同一 Part 和选择实体列表。
7. `review-before.json` 写入成功后才能生成修复计划。
8. `repair-plan.json` 写入成功后才能执行修复。
9. 执行过模型修改就必须生成 `repair-execution.json` 和 `review-after.json`。
10. 回滚后仍保留原执行记录，并把最终状态写为 `rolled_back`。

---

## 十六、协议校验要求

后续应建立 JSON Schema，至少校验：

- 所有必填字段存在。
- 枚举值合法。
- Tag 为字符串或 `null`。
- 三维向量长度为 3。
- 数值和单位同时存在。
- 失败规则有 `reason_code` 和 `reason`。
- 修复计划引用的 `issue_id` 存在。
- 执行记录引用的 `plan_id` 存在。
- 复审结果能对应原问题编号。
- 报告修复成功时不存在新增问题。
- 回滚状态与执行状态不矛盾。

协议不兼容时，工作流停止在只读阶段，并返回 `PROTOCOL_VERSION_UNSUPPORTED`。

---

## 十七、DLL 与 Python 一致性

DLL 与 Python 必须对同一模型输出语义一致的：

- 规则状态。
- 实测值和单位。
- 错误实体与面 Tag。
- 原因码。
- R4 有符号拔模证据。
- R9 启用/关闭状态。
- 多实体选择顺序。

允许存在生成组件名称和时间差异，不允许存在规则结论差异。数值差异必须在统一容差内。

---

## 十八、协议完成标准

- 人可以根据 JSON 找到具体实体、面、规则和实测值。
- AI 可以只读取 JSON 生成修复计划，不必猜测日志文本。
- NX 执行器可以根据计划定位明确目标。
- 修复前、执行、修复后结果可以通过 `run_id`、`issue_id`、`plan_id` 串联。
- 识别失败不会被当作通过。
- 修复失败和回滚能够完整追踪。
- DLL 与 Python 能使用同一份字段和枚举定义。
