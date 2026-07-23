# -*- coding: utf-8 -*-
"""直顶头审查后的自动修复工作流入口。

工作流支持两种模式：plan_only 只生成审查结果和修复计划，
auto_repair_safe 在 NX2306 会话中执行已经验收的 R1、R3、R4 修复动作，
然后复审当前内存模型并输出完整运行报告。
"""

import argparse
import datetime
import json
import os
import uuid

from ZD_RepairPlanner import create_repair_plan
from ZD_ReviewResultAdapter import adapt_legacy_result


def _run_id():
    timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return timestamp + "-" + uuid.uuid4().hex[:6]


def _write_json(path, value):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    temporary_path = path + ".tmp"
    with open(temporary_path, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temporary_path, path)


def _write_report(path, review_before, repair_plan, execution=None, review_after=None):
    issues = review_before.get("data", {}).get("issues", [])
    workflow_mode = review_before.get("context", {}).get("workflow_mode")
    is_execution = execution is not None
    lines = [
        "# 直顶头 AI 自动修复工作流报告" if is_execution else "# 直顶头 AI 自动修复计划报告",
        "",
        "- 运行编号：`{0}`".format(review_before.get("run_id")),
        "- 当前模式：`{0}`".format(workflow_mode),
        "- 结论：{0}".format(review_before.get("summary")),
        "- 修复执行：R1、R3、R4 无需人工确认；实际 NX 几何执行由执行器负责",
        "",
        "## 问题清单",
    ]
    if not issues:
        lines.append("- 未发现问题。")
    else:
        for issue in issues:
            lines.append(
                "- `{0}` / `{1}` / 实体 `{2}` / 面 `{3}`：{4}".format(
                    issue.get("issue_id"),
                    issue.get("rule_id"),
                    issue.get("body_tag"),
                    ",".join(issue.get("face_tags", [])) or "无",
                    issue.get("reason"),
                ))
            if issue.get("suggested_delta"):
                delta = issue["suggested_delta"]
                lines.append("  - 建议调整量：{0} {1}".format(delta.get("value"), delta.get("unit")))
            if issue.get("interaction_request"):
                lines.append("  - 需要用户确认：是否需要调整圆角")
    lines.extend([
        "",
        "## 安全状态",
        "- 本次仅生成审查和修复计划，未调用 NX 几何修改 API。" if not is_execution
        else "- 本次已调用 NX 几何修改 API，并使用 NX Undo Mark 保护修复过程。",
        "- 未保存或覆盖原始 PRT；修复结果仅保留在当前 NX 会话中。" if not is_execution or not execution.get("save", {}).get("saved")
        else "- 已将修复后且复审通过的模型保存回指定 PRT：`{0}`。".format(
            execution.get("save", {}).get("path")),
        "- 计划项数量：{0}；需要执行的计划项：{1}。".format(
            len(repair_plan.get("data", {}).get("plan_items", [])),
            sum(1 for item in repair_plan.get("data", {}).get("plan_items", [])
                if item.get("execution_required"))),
        "- 计划模式不会修改模型；自动修复模式会在执行后生成 repair-execution.json 和 review-after.json。",
        "",
        "## 计划数量",
        "- 计划状态：`{0}`".format(repair_plan.get("status")),
    ])
    if execution is not None:
        lines.extend([
            "",
            "## 执行结果",
            "- 执行状态：`{0}`".format(execution.get("status")),
            "- 实际执行项：{0}。".format(len(execution.get("items", []))),
            "- 是否回滚：`{0}`。".format(execution.get("rollback", {}).get("used")),
            "- 是否保存：`{0}`。".format(execution.get("save", {}).get("saved", False)),
            "- 复审文件：`{0}`。".format(execution.get("review_after_path", "未生成")),
        ])
        for item in execution.get("items", []):
            lines.append(
                "- 修复动作：`{0}`；实体 Tag：`{1}`；目标面 Tag：`{2}`；"
                "Draft 特征 Tag：`{3}`；目标角度：`{4}°`.".format(
                    item.get("action_id"),
                    item.get("target_body_tag"),
                    ",".join(item.get("target_face_tags", [])) or "无",
                    item.get("feature_tag", "未返回"),
                    item.get("target_angle_deg", "未返回"),
                ))
        if review_after is not None:
            after_issues = review_after.get("data", {}).get("issues", [])
            after_status = "pass" if not after_issues else "fail"
            lines.extend([
                "",
                "## 修复后复审",
                "- 复审状态：`{0}`。".format(after_status),
                "- 剩余问题数量：{0}。".format(len(after_issues)),
                "- 复审结论：{0}".format(review_after.get("summary")),
            ])
    with open(path, "w", encoding="utf-8", newline="\n") as stream:
        stream.write("\n".join(lines) + "\n")


def run_workflow(legacy_result_path, output_root, run_id=None, workflow_mode="plan_only", radius_decisions=None):
    if run_id is None:
        run_id = _run_id()
    with open(legacy_result_path, "r", encoding="utf-8-sig") as stream:
        legacy_result = json.load(stream)

    review_before = adapt_legacy_result(legacy_result, run_id, workflow_mode)
    repair_plan = create_repair_plan(review_before, radius_decisions=radius_decisions)
    run_directory = os.path.join(output_root, run_id)
    _write_json(os.path.join(run_directory, "review-before.json"), review_before)
    _write_json(os.path.join(run_directory, "repair-plan.json"), repair_plan)
    _write_report(os.path.join(run_directory, "workflow-report.md"), review_before, repair_plan)
    return run_directory, review_before, repair_plan


def _import_nx_reviewer():
    try:
        import NXOpen
        import NXOpen.UF
    except ImportError as error:
        raise RuntimeError("NX 实时工作流必须在 NX2306 的 NX Python 环境中运行。") from error

    from ZD_StraightLifterReview import StraightLifterReviewer
    return NXOpen, StraightLifterReviewer


def _review_open_nx_part(part_path, radius_limit, body_tags=None):
    """打开当前 PRT，只读审查指定实体；不执行任何几何修改。"""
    NXOpen, reviewer_type = _import_nx_reviewer()
    session = NXOpen.Session.GetSession()
    reviewer = reviewer_type()
    part_load_status = None
    try:
        base_part, part_load_status = session.Parts.OpenActiveDisplay(
            os.path.abspath(part_path), NXOpen.DisplayPartOption.AllowAdditional)
        if base_part is None or session.Parts.Work is None:
            raise RuntimeError("目标 PRT 未能成为 NX 工作部件。")
        work_part = session.Parts.Work
        selected_tags = {int(tag) for tag in body_tags} if body_tags else None
        bodies = [
            body for body in work_part.Bodies
            if selected_tags is None or int(body.Tag) in selected_tags
        ]
        if not bodies:
            raise RuntimeError("目标 PRT 中没有找到待审查实体。")
        legacy_result = {
            "part_path": os.path.abspath(part_path),
            "radius_limit_mm": float(radius_limit),
            "nx_version": session.GetEnvironmentVariableValue("NX_FULL_VERSION"),
            "opened": True,
            "body_count": len(bodies),
            "bodies": [
                reviewer.review_body(body, float(radius_limit), interactive=False)
                for body in bodies
            ],
            "error": None,
        }
        return session, legacy_result
    finally:
        if part_load_status is not None:
            part_load_status.Dispose()


def _review_current_nx_part(session, part_path, radius_limit, body_tags=None):
    """复审 NX 当前工作部件，确保读取的是修复后的内存模型。"""
    _, reviewer_type = _import_nx_reviewer()
    reviewer = reviewer_type()
    work_part = session.Parts.Work
    if work_part is None:
        raise RuntimeError("NX 当前没有可复审的工作部件。")
    selected_tags = {int(tag) for tag in body_tags} if body_tags else None
    bodies = [
        body for body in work_part.Bodies
        if selected_tags is None or int(body.Tag) in selected_tags
    ]
    if not bodies:
        raise RuntimeError("修复后没有找到待复审实体。")
    return {
        "part_path": os.path.abspath(part_path),
        "radius_limit_mm": float(radius_limit),
        "nx_version": session.GetEnvironmentVariableValue("NX_FULL_VERSION"),
        "opened": True,
        "body_count": len(bodies),
        "bodies": [
            reviewer.review_body(body, float(radius_limit), interactive=False)
            for body in bodies
        ],
        "error": None,
    }


def _write_after_review(run_directory, review_after):
    _write_json(os.path.join(run_directory, "review-after.json"), review_after)


def run_nx_auto_repair_workflow(
        part_path,
        output_root,
        radius_limit=0.0,
        run_id=None,
        workflow_mode="auto_repair_safe",
        body_tags=None,
        radius_decisions=None,
        save_part=False):
    """执行审查后自动修复闭环。

    工作流只允许执行修复计划明确标记为 execution_required 的动作。
    当前实际 NX 修复器实现 R1、R3、R4；R2/R9 会保留为计划或人工处理项。
    """
    if workflow_mode not in ("plan_only", "auto_repair_safe"):
        raise ValueError("NX 自动工作流只支持 plan_only 或 auto_repair_safe。")
    if run_id is None:
        run_id = _run_id()

    session, legacy_before = _review_open_nx_part(
        part_path, radius_limit, body_tags)
    review_before = adapt_legacy_result(
        legacy_before, run_id, workflow_mode=workflow_mode,
        radius_limit=radius_limit)
    repair_plan = create_repair_plan(
        review_before, radius_decisions=radius_decisions)
    run_directory = os.path.join(output_root, run_id)
    _write_json(os.path.join(run_directory, "review-before.json"), review_before)
    _write_json(os.path.join(run_directory, "repair-plan.json"), repair_plan)

    execution = None
    review_after = None
    if workflow_mode == "auto_repair_safe" and repair_plan.get("data", {}).get("execution_required"):
        execution_path = os.path.join(run_directory, "repair-execution.json")
        execution, _ = execute_nx_repair_plan(
            os.path.join(run_directory, "repair-plan.json"), execution_path,
            session=session,
            save_part=save_part)
        legacy_after = _review_current_nx_part(
            session, part_path, radius_limit, body_tags)
        review_after = adapt_legacy_result(
            legacy_after, run_id + "-after", workflow_mode="verify_only",
            radius_limit=radius_limit, document_type="review_after")
        _write_after_review(run_directory, review_after)

    report_path = os.path.join(run_directory, "workflow-report.md")
    _write_report(
        report_path,
        review_before,
        repair_plan,
        execution=execution,
        review_after=review_after,
    )
    return {
        "run_directory": run_directory,
        "review_before": review_before,
        "repair_plan": repair_plan,
        "repair_execution": execution,
        "review_after": review_after,
    }


def execute_nx_repair_plan(
        repair_plan_path,
        execution_path,
        session=None,
        save_part=False):
    """在 NX Python 环境中执行 R1、R3、R4 计划；普通 Python 环境只生成明确错误。"""
    from ZD_NXRepairExecutor import execute_repair_plan
    return execute_repair_plan(
        repair_plan_path,
        execution_path,
        session=session,
        save_part=save_part)


def main():
    parser = argparse.ArgumentParser(description="生成直顶头只读自动修复工作流 JSON")
    parser.add_argument("legacy_result_path", nargs="?", default=None)
    parser.add_argument("output_root", nargs="?", default=None)
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--radius-decision", action="append", default=[], help="格式：issue_id=yes/no")
    parser.add_argument("--execute-nx", action="store_true", help="在 NX Python 环境中执行 R1、R3、R4 自动修复")
    parser.add_argument("--nx-part", default=None, help="在 NX 中打开并审查的 PRT 路径")
    parser.add_argument("--output-root", dest="output_root_option", default=None, help="工作流输出根目录")
    parser.add_argument(
        "--workflow-mode",
        choices=("plan_only", "auto_repair_safe"),
        default="plan_only",
        help="NX 实时工作流模式")
    parser.add_argument("--radius-limit", type=float, default=0.0, help="R9 最小圆角半径，0 表示关闭")
    parser.add_argument("--body-tag", action="append", default=[], help="限定审查实体 Tag，可重复指定")
    parser.add_argument(
        "--save-part",
        action="store_true",
        help="修复后复审通过时，将模型保存回指定 PRT；默认不保存")
    args = parser.parse_args()
    radius_decisions = {}
    for item in args.radius_decision:
        if "=" not in item:
            raise ValueError("--radius-decision 格式必须为 issue_id=yes/no")
        issue_id, decision = item.split("=", 1)
        radius_decisions[issue_id] = decision
    if args.nx_part:
        if not args.output_root_option:
            parser.error("NX 模式必须提供 --output-root")
        result = run_nx_auto_repair_workflow(
            args.nx_part,
            args.output_root_option,
            radius_limit=args.radius_limit,
            run_id=args.run_id,
            workflow_mode=args.workflow_mode,
            body_tags=args.body_tag or None,
            radius_decisions=radius_decisions,
            save_part=args.save_part,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not args.legacy_result_path or not args.output_root:
        parser.error("旧 JSON 模式需要 legacy_result_path 和 output_root；NX 模式请使用 --nx-part")
    run_directory, review_before, repair_plan = run_workflow(
        args.legacy_result_path, args.output_root, args.run_id,
        radius_decisions=radius_decisions)
    execution = None
    if args.execute_nx:
        execution_path = os.path.join(run_directory, "repair-execution.json")
        execution, _ = execute_nx_repair_plan(
            os.path.join(run_directory, "repair-plan.json"), execution_path)
    print(json.dumps({
        "run_directory": run_directory,
        "review_before": review_before,
        "repair_plan": repair_plan,
        "repair_execution": execution,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
