# 插件准入审查报告

插件名称：ZD

审查时间：2026-07-23T14:10:14

审查结论：不通过

审查范围：C:\Users\10482\Desktop\ZD

## Git 信息

- GitLab URL：
- 分支：
- Commit：
- 本地是否有未提交修改：否
- 规则配置：`C:\Users\10482\.codex\skills\skill-main\nx-plugin-review\references\rules.json`

## 类别审查重点

- 识别类别：未识别，按通用规则审查。

## 1. 准入结论

结论：**不通过**。

- 重大问题结论：不通过
- P0：7
- P1：0
- P2：0
- 总问题数：7
- 审查模式：重大问题模式
- 非阻塞延后项：34
- AI 优先修复项：40
- AI 待闭环项：34
- 人工待填项：1
- 人工填写表项：1
- 闭环完成：否
- 规范偏差但可兼容：0
- 疑似误报/需人工确认：0
- 主体非 DLX 对话框命中：0
- 提示/错误弹窗观察命中：12
- DLX 标题燕秀相关命中：0
- 源码临时编译：failed

> 重大问题模式先拦严重功能和交付风险；AI 可修复项必须先由 AI 小范围修复并复审，只有需要人工输入或 NX 实操确认的项目才进入填写表。主体界面对话框审查项不参与准入结论、计数或退出码；DLX 标题含燕秀相关内容按 P0 处理。

## 1.1 UFUN 使用审查

- 结论：发现 UFUN 函数调用，按当前规则记为 P0 阻塞项，需要迁移为 NXOpen 或人工明确豁免。
- 命中函数调用数：2
- 命中文件数：1
- 扫描范围：src, tests

| 序号 | 类别 | 文件 | 行 | UFUN 函数 | 代码 |
| --- | --- | --- | ---: | --- | --- |
| 1 | 几何查询 | `src/ZD_StraightLifterReview.cpp` | 366 | `UF_MODL_ask_bounding_box` | `if (UF_MODL_ask_bounding_box(body->Tag(), bodyBox) != 0)` |
| 2 | 几何查询 | `src/ZD_StraightLifterReview.cpp` | 425 | `UF_MODL_ask_face_data` | `if (UF_MODL_ask_face_data(face->Tag(), &type, point, direction, faceBox, &radius, &radiusData, &normalDirection) != 0)` |

## 1.2 源码临时编译审查

- 结论：failed
- 工程：`src/ZD_StraightLifterReview.vcxproj`
- 配置：Release|x64
- MSBuild：``
- 返回码：
- 新增临时产物：0
- 已删除临时产物：0
- 已删除空目录：0
- 临时输出目录已删除：是

- 原因：未找到 MSBuild.exe，无法进行源码临时编译。

## 1.3 主体界面对话框审查

- 结论：未发现插件主体使用非 DLX 对话框；发现 DLX/Block Styler 主界面证据。
- 主体非 DLX 命中：0
- DLX/Block Styler 主界面证据：1
- 提示/错误弹窗：12
- 辅助文件/目录选择对话框：0
- 观察命中文件数：2
- 扫描范围：src

| 序号 | 分组 | 类型 | 文件 | 行 | API/标记 | 代码 |
| --- | --- | --- | --- | ---: | --- | --- |
| 1 | DLX 主界面 | DLX/Block Styler 主界面 | `src/ZD_StraightLifterReview.cpp` | 69 | `CreateDialog(` | `theDialog = ZD_StraightLifterReview::theUI->CreateDialog(theDlxFileName);` |
| 2 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.cpp` | 129 | `NXMessageBox` | `ZD_StraightLifterReview::theUI->NXMessageBox()->Show("Block Styler", NXOpen::NXMessageBox::DialogTypeError, ex.what());` |
| 3 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.cpp` | 174 | `NXMessageBox` | `ZD_StraightLifterReview::theUI->NXMessageBox()->Show("Block Styler", NXOpen::NXMessageBox::DialogTypeError, ex.what());` |
| 4 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.cpp` | 190 | `NXMessageBox` | `ZD_StraightLifterReview::theUI->NXMessageBox()->Show("Block Styler", NXOpen::NXMessageBox::DialogTypeError, ex.what());` |
| 5 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.cpp` | 214 | `NXMessageBox` | `ZD_StraightLifterReview::theUI->NXMessageBox()->Show("Block Styler", NXOpen::NXMessageBox::DialogTypeError, ex.what());` |
| 6 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.cpp` | 231 | `NXMessageBox` | `ZD_StraightLifterReview::theUI->NXMessageBox()->Show("Block Styler", NXOpen::NXMessageBox::DialogTypeError, ex.what());` |
| 7 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.cpp` | 246 | `NXMessageBox` | `ZD_StraightLifterReview::theUI->NXMessageBox()->Show("直顶头审查", NXOpen::NXMessageBox::DialogTypeWarning, "请至少选择一个直顶头实体后再执行审查。");` |
| 8 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.cpp` | 258 | `NXMessageBox` | `ZD_StraightLifterReview::theUI->NXMessageBox()->Show("Block Styler", NXOpen::NXMessageBox::DialogTypeError, ex.what());` |
| 9 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.cpp` | 408 | `NXMessageBox` | `ZD_StraightLifterReview::theUI->NXMessageBox()->Show(` |
| 10 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.cpp` | 410 | `NXMessageBox` | `NXOpen::NXMessageBox::DialogTypeWarning,` |
| 11 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.cpp` | 566 | `NXMessageBox` | `ZD_StraightLifterReview::theUI->NXMessageBox()->Show("Block Styler", NXOpen::NXMessageBox::DialogTypeError, ex.what());` |
| 12 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.cpp` | 587 | `NXMessageBox` | `ZD_StraightLifterReview::theUI->NXMessageBox()->Show("Block Styler", NXOpen::NXMessageBox::DialogTypeError, ex.what());` |
| 13 | 提示/错误弹窗 | 提示/错误弹窗 | `src/ZD_StraightLifterReview.hpp` | 30 | `NXMessageBox` | `#include <NXOpen/NXMessageBox.hxx>` |

## 1.4 DLX 标题燕秀内容审查

- 结论：未发现 DLX 窗口标题包含燕秀相关内容。
- 已检查 DLX 数：0
- 已解析标题数：0
- 扫描范围：active dlx titles in src/application/staging and release zip application/startup entries

## 1.5 人工阻塞项填写表

本表只列出 AI 不能可靠代填、需要用户提供事实或 NX 实操确认的项目。AI 可修复项不进入此表，必须先由 AI 按 `ai_repair_issues` 小范围修复并复审。

| 序号 | 分组 | 建议处理人 | 优先级 | 类型 | 路径 | 问题/需要填写的内容 | 用户填写/处理结果 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 重大待人工确认 | 用户填写 | P0 | 使用说明文档 | `docs/04-usage/video` | 缺少操作视频目录 docs/04-usage/video |  |

## 2. 阻塞问题 P0

### 1. [P0] 测试数模：缺少测试数模：测试文档和 tests/data 说明中均未发现数模引用，tests/data 下也没有数模文件

- 路径：`tests/data`
- 证据：检查 docs/03-testing/testing.md；若信息缺失，已回退检查 tests/data 下的说明文档。
- 影响：缺少可复核的输入/输出数模或数模关系不清，会导致 NX 测试无法复现，功能正确性无法闭环。
- 整改建议：以 docs/03-testing/testing.md 为主登记输入数模、输出/标准结果数模；信息不足时补 tests/data 下的数据索引或说明文档。
- 是否阻塞准入：是

### 2. [P0] 使用说明文档：缺少操作视频目录 docs/04-usage/video

- 路径：`docs/04-usage/video`
- 证据：docs/04-usage/video
- 影响：需求、设计、测试或使用过程缺少审查依据，影响准入判断和后续维护。
- 整改建议：按对应模板补齐缺失章节，避免使用“待补充”替代验收信息。
- 是否阻塞准入：是

### 3. [P0] 编码规范：仓库文本文件存在非 UTF-8 编码，编码格式不统一

- 路径：`Command/冻结版本/直顶头审查_v1.0_20260723/src/ZD_StraightLifterReview.cpp`
- 证据：Command/冻结版本/直顶头审查_v1.0_20260723/src/ZD_StraightLifterReview.cpp, Command/冻结版本/直顶头审查_v1.0_20260723/src/ZD_StraightLifterReview.hpp, Command/冻结版本/直顶头审查_v1.0_20260723/tools/ZD_StraightLifterReview.cpp, Command/冻结版本/直顶头审查_v1.0_20260723/tools/ZD_StraightLifterReview.hpp, src/ZD_StraightLifterReview.cpp 等 8 个
- 影响：不同审查脚本、编译环境或编辑器可能误判中文字符串，甚至触发字符串常量跨行等假阳性/构建风险。
- 整改建议：将源码、工程、脚本和文档等文本文件统一转换为 UTF-8，并在 C/C++ 工程中显式加入 /utf-8 编译选项。
- 是否阻塞准入：是

### 4. [P0] 源码风险：DLX 路径硬编码为开发机绝对路径

- 路径：`src/ZD_StraightLifterReview.cpp`
- 证据：line 68: theDlxFileName = "C:\\Users\\10482\\Desktop\\ZD\\tools\\ZD_StraightLifterReview.dlx";
- 影响：发布环境或其他开发机上可能无法加载 Block UI 界面，插件启动即失败。
- 整改建议：改为随 DLL 所在目录、NX 自定义目录或相对部署路径定位 DLX。
- 是否阻塞准入：是

### 5. [P0] 构建环境：工程/编译配置中存在 Windows 绝对路径

- 路径：`src/ZD_StraightLifterReview.vcxproj`
- 证据：line 10: <PropertyGroup Condition="'$(Configuration)\|$(Platform)'=='Release\|x64'"><OutDir>C:\Users\10482\Desktop\ZD\tools\</OutDir><IntDir>$(ProjectDir)obj\Release\</IntDir><TargetName>ZD_StraightLifterReview</TargetName></PropertyGroup>
- 影响：构建或运行依赖个人电脑路径，迁移到其他机器后可能失败。
- 整改建议：使用环境变量、工程宏、相对路径或部署目录推导路径。
- 是否阻塞准入：是

### 6. [P0] UFUN 使用审查：源码中存在 UFUN 函数调用

- 路径：`src/ZD_StraightLifterReview.cpp`
- 证据：UFUN function calls: 2; files: 1; first hit: src/ZD_StraightLifterReview.cpp:366 UF_MODL_ask_bounding_box -> if (UF_MODL_ask_bounding_box(body->Tag(), bodyBox) != 0)
- 影响：正式插件仍依赖 UFUN API，不符合纯 NXOpen 迁移约束，后续编译、部署和维护风险较高。
- 整改建议：将命中的 UF_* 调用替换为 NXOpen API；若确需保留，应先由人工确认并从 P0 清单中单独豁免。
- 是否阻塞准入：是

### 7. [P0] 源码临时编译：源码临时编译未通过

- 路径：`src/ZD_StraightLifterReview.vcxproj`
- 证据：未找到 MSBuild.exe，无法进行源码临时编译。
- 影响：源码无法通过一次可复建编译，发布 DLL 与源码一致性、后续维护和 NX 人工验证都无法可靠确认。
- 整改建议：修复 Release\|x64 工程配置或源码编译错误后，重新运行 `scan_plugin.py --temp-build`。
- 是否阻塞准入：是

## 3. 重要问题 P1

未发现。

## 4. 一般问题 P2

未发现。

## 5. 规范偏差但可兼容

未发现。

## 6. 疑似误报/需人工确认项

未发现。

## 7. 整改清单

1. [P0] 测试数模：以 docs/03-testing/testing.md 为主登记输入数模、输出/标准结果数模；信息不足时补 tests/data 下的数据索引或说明文档。
2. [P0] 使用说明文档：按对应模板补齐缺失章节，避免使用“待补充”替代验收信息。
3. [P0] 编码规范：将源码、工程、脚本和文档等文本文件统一转换为 UTF-8，并在 C/C++ 工程中显式加入 /utf-8 编译选项。
4. [P0] 源码风险：改为随 DLL 所在目录、NX 自定义目录或相对部署路径定位 DLX。
5. [P0] 构建环境：使用环境变量、工程宏、相对路径或部署目录推导路径。
6. [P0] UFUN 使用审查：将命中的 UF_* 调用替换为 NXOpen API；若确需保留，应先由人工确认并从 P0 清单中单独豁免。
7. [P0] 源码临时编译：修复 Release|x64 工程配置或源码编译错误后，重新运行 `scan_plugin.py --temp-build`。

## 7.1 AI 优先修复队列

### 1. [P0] 测试数模：缺少测试数模：测试文档和 tests/data 说明中均未发现数模引用，tests/data 下也没有数模文件

- 路径：`tests/data`
- 证据：检查 docs/03-testing/testing.md；若信息缺失，已回退检查 tests/data 下的说明文档。
- 影响：缺少可复核的输入/输出数模或数模关系不清，会导致 NX 测试无法复现，功能正确性无法闭环。
- 整改建议：以 docs/03-testing/testing.md 为主登记输入数模、输出/标准结果数模；信息不足时补 tests/data 下的数据索引或说明文档。
- 是否阻塞准入：是

### 2. [P0] 编码规范：仓库文本文件存在非 UTF-8 编码，编码格式不统一

- 路径：`Command/冻结版本/直顶头审查_v1.0_20260723/src/ZD_StraightLifterReview.cpp`
- 证据：Command/冻结版本/直顶头审查_v1.0_20260723/src/ZD_StraightLifterReview.cpp, Command/冻结版本/直顶头审查_v1.0_20260723/src/ZD_StraightLifterReview.hpp, Command/冻结版本/直顶头审查_v1.0_20260723/tools/ZD_StraightLifterReview.cpp, Command/冻结版本/直顶头审查_v1.0_20260723/tools/ZD_StraightLifterReview.hpp, src/ZD_StraightLifterReview.cpp 等 8 个
- 影响：不同审查脚本、编译环境或编辑器可能误判中文字符串，甚至触发字符串常量跨行等假阳性/构建风险。
- 整改建议：将源码、工程、脚本和文档等文本文件统一转换为 UTF-8，并在 C/C++ 工程中显式加入 /utf-8 编译选项。
- 是否阻塞准入：是

### 3. [P0] 源码风险：DLX 路径硬编码为开发机绝对路径

- 路径：`src/ZD_StraightLifterReview.cpp`
- 证据：line 68: theDlxFileName = "C:\\Users\\10482\\Desktop\\ZD\\tools\\ZD_StraightLifterReview.dlx";
- 影响：发布环境或其他开发机上可能无法加载 Block UI 界面，插件启动即失败。
- 整改建议：改为随 DLL 所在目录、NX 自定义目录或相对部署路径定位 DLX。
- 是否阻塞准入：是

### 4. [P0] 构建环境：工程/编译配置中存在 Windows 绝对路径

- 路径：`src/ZD_StraightLifterReview.vcxproj`
- 证据：line 10: <PropertyGroup Condition="'$(Configuration)\|$(Platform)'=='Release\|x64'"><OutDir>C:\Users\10482\Desktop\ZD\tools\</OutDir><IntDir>$(ProjectDir)obj\Release\</IntDir><TargetName>ZD_StraightLifterReview</TargetName></PropertyGroup>
- 影响：构建或运行依赖个人电脑路径，迁移到其他机器后可能失败。
- 整改建议：使用环境变量、工程宏、相对路径或部署目录推导路径。
- 是否阻塞准入：是

### 5. [P0] UFUN 使用审查：源码中存在 UFUN 函数调用

- 路径：`src/ZD_StraightLifterReview.cpp`
- 证据：UFUN function calls: 2; files: 1; first hit: src/ZD_StraightLifterReview.cpp:366 UF_MODL_ask_bounding_box -> if (UF_MODL_ask_bounding_box(body->Tag(), bodyBox) != 0)
- 影响：正式插件仍依赖 UFUN API，不符合纯 NXOpen 迁移约束，后续编译、部署和维护风险较高。
- 整改建议：将命中的 UF_* 调用替换为 NXOpen API；若确需保留，应先由人工确认并从 P0 清单中单独豁免。
- 是否阻塞准入：是

### 6. [P0] 源码临时编译：源码临时编译未通过

- 路径：`src/ZD_StraightLifterReview.vcxproj`
- 证据：未找到 MSBuild.exe，无法进行源码临时编译。
- 影响：源码无法通过一次可复建编译，发布 DLL 与源码一致性、后续维护和 NX 人工验证都无法可靠确认。
- 整改建议：修复 Release\|x64 工程配置或源码编译错误后，重新运行 `scan_plugin.py --temp-build`。
- 是否阻塞准入：是

### 7. [P0] 目录结构：测试目录缺失

- 路径：`tests`
- 证据：tests
- 影响：可能影响插件库准入、发布可追溯性或后续维护。
- 整改建议：按插件库规范补齐或调整后重新审查。
- 是否阻塞准入：否

### 8. [P0] 目录结构：文档目录缺失

- 路径：`docs`
- 证据：docs
- 影响：可能影响插件库准入、发布可追溯性或后续维护。
- 整改建议：按插件库规范补齐或调整后重新审查。
- 是否阻塞准入：否

### 9. [P0] 目录结构：MCP 目录缺失

- 路径：`mcp`
- 证据：mcp
- 影响：可能影响插件库准入、发布可追溯性或后续维护。
- 整改建议：按插件库规范补齐或调整后重新审查。
- 是否阻塞准入：否

### 10. [P0] 目录结构：发布目录缺失

- 路径：`release`
- 证据：release
- 影响：可能影响插件库准入、发布可追溯性或后续维护。
- 整改建议：按插件库规范补齐或调整后重新审查。
- 是否阻塞准入：否

### 11. [P1] 目录结构：staging 目录缺失

- 路径：`staging`
- 证据：staging
- 影响：可能影响插件库准入、发布可追溯性或后续维护。
- 整改建议：按插件库规范补齐或调整后重新审查。
- 是否阻塞准入：否

### 12. [P1] 目录结构：附件目录缺失

- 路径：`attachments`
- 证据：attachments
- 影响：可能影响插件库准入、发布可追溯性或后续维护。
- 整改建议：按插件库规范补齐或调整后重新审查。
- 是否阻塞准入：否

### 13. [P1] 根文档：根目录缺少 README.md

- 路径：`README.md`
- 证据：README.md
- 影响：需求、设计、测试或使用过程缺少审查依据，影响准入判断和后续维护。
- 整改建议：按对应模板补齐缺失章节，避免使用“待补充”替代验收信息。
- 是否阻塞准入：否

### 14. [P1] 根文档：根目录缺少 CHANGELOG.md

- 路径：`CHANGELOG.md`
- 证据：CHANGELOG.md
- 影响：需求、设计、测试或使用过程缺少审查依据，影响准入判断和后续维护。
- 整改建议：按对应模板补齐缺失章节，避免使用“待补充”替代验收信息。
- 是否阻塞准入：否

### 15. [P2] 模板结构：缺少模板根标准文件：.editorconfig

- 路径：`.editorconfig`
- 证据：.editorconfig
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 16. [P2] 模板结构：缺少模板根标准文件：.gitignore

- 路径：`.gitignore`
- 证据：.gitignore
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 17. [P2] 目录说明：缺少模板目录 README：docs/README.md

- 路径：`docs/README.md`
- 证据：docs/README.md
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 18. [P2] 目录说明：缺少模板目录 README：docs/01-requirements/normalization/README.md

- 路径：`docs/01-requirements/normalization/README.md`
- 证据：docs/01-requirements/normalization/README.md
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 19. [P2] 目录说明：缺少模板目录 README：mcp/README.md

- 路径：`mcp/README.md`
- 证据：mcp/README.md
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 20. [P2] 目录说明：缺少模板目录 README：release/README.md

- 路径：`release/README.md`
- 证据：release/README.md
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 21. [P2] 目录说明：缺少模板目录 README：release/packages/v1.0.0/README.md

- 路径：`release/packages/v1.0.0/README.md`
- 证据：release/packages/v1.0.0/README.md
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 22. [P2] 目录说明：缺少模板目录 README：src/README.md

- 路径：`src/README.md`
- 证据：src/README.md
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 23. [P2] 目录说明：缺少模板目录 README：staging/README.md

- 路径：`staging/README.md`
- 证据：staging/README.md
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 24. [P2] 目录说明：缺少模板目录 README：staging/package-root/Bitmap/README.md

- 路径：`staging/package-root/Bitmap/README.md`
- 证据：staging/package-root/Bitmap/README.md
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 25. [P2] 目录说明：缺少模板目录 README：staging/package-root/config/README.md

- 路径：`staging/package-root/config/README.md`
- 证据：staging/package-root/config/README.md
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 26. [P2] 目录说明：缺少模板目录 README：staging/package-root/data/README.md

- 路径：`staging/package-root/data/README.md`
- 证据：staging/package-root/data/README.md
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 27. [P2] 目录说明：缺少模板目录 README：staging/package-root/startup/README.md

- 路径：`staging/package-root/startup/README.md`
- 证据：staging/package-root/startup/README.md
- 影响：仓库看似可运行，但不符合模板事实源和目录说明约定，后续发布/复审容易漏项。
- 整改建议：参考 workspace/模板 补齐对应 README、章节标题或根标准文件，保持内容贴合当前插件，不做大范围重写。
- 是否阻塞准入：否

### 28. [P0] 文档规范：需求文档缺失

- 路径：`docs/01-requirements/requirement.md`
- 证据：docs/01-requirements/requirement.md
- 影响：需求、设计、测试或使用过程缺少审查依据，影响准入判断和后续维护。
- 整改建议：按对应模板补齐缺失章节，避免使用“待补充”替代验收信息。
- 是否阻塞准入：否

### 29. [P0] 文档规范：方案设计文档缺失

- 路径：`docs/02-design/design.md`
- 证据：docs/02-design/design.md
- 影响：需求、设计、测试或使用过程缺少审查依据，影响准入判断和后续维护。
- 整改建议：按对应模板补齐缺失章节，避免使用“待补充”替代验收信息。
- 是否阻塞准入：否

### 30. [P0] 文档规范：测试文档缺失

- 路径：`docs/03-testing/testing.md`
- 证据：docs/03-testing/testing.md
- 影响：需求、设计、测试或使用过程缺少审查依据，影响准入判断和后续维护。
- 整改建议：按对应模板补齐缺失章节，避免使用“待补充”替代验收信息。
- 是否阻塞准入：否

### 31. [P0] 文档规范：使用说明文档缺失

- 路径：`docs/04-usage/usage.md`
- 证据：docs/04-usage/usage.md
- 影响：需求、设计、测试或使用过程缺少审查依据，影响准入判断和后续维护。
- 整改建议：按对应模板补齐缺失章节，避免使用“待补充”替代验收信息。
- 是否阻塞准入：否

### 32. [P0] 发布规范：缺少 release/packages 发布包目录

- 路径：`release/packages`
- 证据：release/packages
- 影响：发布包位置或命名不符合准入规范，影响交付、下载和版本追溯。
- 整改建议：将正式 ZIP 放到规范位置，确认包名和包内根目录结构符合发布规范。
- 是否阻塞准入：否

### 33. [P1] 发布规范：缺少 staging/package-root，无法确认发布包来源

- 路径：`staging/package-root`
- 证据：staging/package-root
- 影响：发布包位置或命名不符合准入规范，影响交付、下载和版本追溯。
- 整改建议：将正式 ZIP 放到规范位置，确认包名和包内根目录结构符合发布规范。
- 是否阻塞准入：否

### 34. [P0] 发布规范：缺少 release/notes/RELEASE-NOTES.md

- 路径：`release/notes/RELEASE-NOTES.md`
- 证据：release/notes/RELEASE-NOTES.md
- 影响：发布记录不完整或不可追溯，影响版本验收、升级和回滚。
- 整改建议：按模板补齐真实发布信息、变更摘要、包内容、升级说明和回滚说明。
- 是否阻塞准入：否

### 35. [P1] MCP 转换：缺少 mcp 目录，无法确认 MCP 转换交付物

- 路径：`mcp`
- 证据：mcp
- 影响：AIAMD 无法按规范发现和调用该插件能力。
- 整改建议：先用 `prepare_mcp_conversion.py` 生成转换填写表和最小脚手架，再补真实 NXOpen 逻辑并运行 `check_mcp_tools.py` 复审。
- 是否阻塞准入：否

### 36. [P2] 仓库卫生：存在 __pycache__ 目录 1 个

- 路径：`src/__pycache__`
- 证据：src/__pycache__
- 影响：可能影响插件库准入、发布可追溯性或后续维护。
- 整改建议：按插件库规范补齐或调整后重新审查。
- 是否阻塞准入：否

### 37. [P2] 仓库卫生：存在 .pyc 缓存文件 3 个

- 路径：`.`
- 证据：.
- 影响：可能影响插件库准入、发布可追溯性或后续维护。
- 整改建议：按插件库规范补齐或调整后重新审查。
- 是否阻塞准入：否

### 38. [P2] 仓库卫生：源码树内存在构建中间产物 12 个

- 路径：`src/obj/Release/vc143.pdb`
- 证据：src/obj/Release/vc143.pdb
- 影响：构建缓存或审查临时文件混入仓库，会干扰结构审查和发布清单。
- 整改建议：补 .gitignore 后清理或归档对应产物；如确需保留测试 DLL，应在测试文档中说明用途。
- 是否阻塞准入：否

### 39. [P1] 构建环境：Release|x64 AdditionalIncludeDirectories 缺少 NX SDK 路径

- 路径：`src/ZD_StraightLifterReview.vcxproj`
- 证据：line 12: <ClCompile><WarningLevel>Level3</WarningLevel><Optimization>Disabled</Optimization><PreprocessorDefinitions>_WINDOWS;_USRDLL;UNICODE;_UNICODE;%(PreprocessorDefinitions)</PreprocessorDefinitions><AdditionalIncludeDirectories>D:\Program Files\Siemens\NX2306\UGOPEN;%(AdditionalIncludeDirectories)</AdditionalIncludeDirectories><LanguageStandard>stdcpp17</LanguageStandard></ClCompile> \| Release\|x64 AdditionalIncludeDirectories 缺少 NX SDK include 路径
- 影响：Release\|x64 编译配置无法找到 NXOpen/UGOPEN 头文件，VS/MSBuild 编译会失败。
- 整改建议：在 Release\|x64 的 ClCompile 配置中补充：<AdditionalIncludeDirectories>$(UGII_BASE_DIR)\ugopen;%(AdditionalIncludeDirectories)</AdditionalIncludeDirectories>；若仓库采用 NxRoot 规范，也可使用 $(NxRoot)\UGOPEN。
- 是否阻塞准入：否

### 40. [P2] 源码风险：源码注释或生成头部存在 Windows 绝对路径，需确认是否为残留

- 路径：`src/ZD_StraightLifterReview.hpp`
- 证据：line 6: //       Filename:  C:\Users\10482\Desktop\ZD\tools\ZD_StraightLifterReview.hpp
- 影响：构建或运行依赖个人电脑路径，迁移到其他机器后可能失败。
- 整改建议：使用环境变量、工程宏、相对路径或部署目录推导路径。
- 是否阻塞准入：否

## 8. 复审命令

```powershell
python "C:\Users\10482\.codex\skills\skill-main\nx-plugin-review\scripts\scan_plugin.py" "C:\Users\10482\Desktop\ZD" --major-only --fail-on-p1 --fail-on-ai-followups --markdown "C:\Users\10482\Desktop\ZD\review-report.md" --json "C:\Users\10482\Desktop\ZD\review-result.json" --blocking-input-table "C:\Users\10482\Desktop\ZD\review-blocking-input-table.md" --human-input-table "C:\Users\10482\Desktop\ZD\review-human-input-table.md"
```

## 9. 人工待填信息表（非阻塞）

# 人工待填信息表

这些项目需要人工输入或人工实操确认。AI 可修复的延后项不应留在这里，应继续闭环修改。

| 序号 | 类型 | 路径 | 需要人工确认或补充的内容 | 人工填写/处理结果 |
| --- | --- | --- | --- | --- |
| 1 | 使用说明文档 | `docs/04-usage/video` | 缺少操作视频目录 docs/04-usage/video |  |
