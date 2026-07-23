# 直顶头审查 DLL 与 Python 同步规则

## 目标

`src\ZD_StraightLifterReview.cpp/.hpp` 编译为 NX DLL；`src\ZD_StraightLifterReview.py` 是同一套审查逻辑的 NX Python 实现。后续功能调整必须同时修改两端，并同步复制运行文件到 `tools\`。

## 必须同步的项目

| 项目 | DLL | Python |
|---|---|---|
| R1 侧面最小角度 | `minSideAngle` | `MIN_SIDE_ANGLE` |
| R2 最小高度 | `minHeight` | `MIN_HEIGHT` |
| R3 底面公差与候选规则 | `angleTolerance` 与底面识别 | `BOTTOM_ANGLE_TOLERANCE` 与底面识别 |
| R9 最小圆角 | `radius_dim0` 输入 | `RADIUS_LIMIT` 或后续 Python UI 输入 |
| 多实体审查顺序 | `GetSelectedBodies` / `apply_cb` | `select_bodies` / `run` |
| 高度错误定位与窗口 | `FlyToObjects` / `NXMessageBox` | `fly_to_body` / `NXMessageBox` |
| 错误面临时标红与清理 | `HighlightFace` / `ClearReviewDisplay` | `highlight_face` / `clear_review_display` |
| 报告内容 | `WriteReport` | `write_report` |

## 修改流程

1. 先修改 `src` 中 DLL 和 Python 的同一条规则。
2. 编译 DLL，输出覆盖 `tools\ZD_StraightLifterReview.dll`。
3. 将 `.cpp`、`.hpp`、`.py` 同步复制到 `tools\`。
4. 用 NX 分别测试 DLL 与 Python，确认审查结果、标红对象、定位顺序和窗口文本一致。
5. 不生成版本号后缀 DLL，不提交 Git。

## 当前 Python 运行方式

在 NX 中选择 `文件 -> 执行 -> NX Open`，运行：

`C:\Users\10482\Desktop\ZD\tools\ZD_StraightLifterReview.py`

Python 版会连续选择多个实体；完成选择后点击取消，随后开始批量审查。当前 Python 的 R9 输入与 DLL 默认值一致，为 `0 mm`（关闭 R9）。