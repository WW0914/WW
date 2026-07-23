# -*- coding: utf-8 -*-
"""根据统一问题对象生成只读修复计划。"""


def create_repair_plan(review_before, radius_decisions=None):
    """生成计划，不执行任何 NX 几何修改。"""
    radius_decisions = radius_decisions or {}
    plan_items = []
    issues = review_before.get("data", {}).get("issues", [])
    body_selection_indexes = {
        str(body.get("body_tag")): body.get("selection_index")
        for body in review_before.get("data", {}).get("body_results", [])
    }
    grouped_r1 = {}
    for issue in issues:
        if issue.get("rule_id") == "R1":
            key = str(issue.get("body_tag"))
            grouped_r1.setdefault(key, []).append(issue)

    processed_r1_bodies = set()
    for issue in issues:
        rule_id = issue.get("rule_id")
        body_key = str(issue.get("body_tag"))
        if rule_id == "R1":
            if body_key in processed_r1_bodies:
                continue
            processed_r1_bodies.add(body_key)
            grouped_issues = grouped_r1[body_key]
            target_face_tags = [
                tag
                for grouped_issue in grouped_issues
                for tag in grouped_issue.get("face_tags", [])
            ]
            plan_items.append({
                "plan_id": "PLAN-R1-{0}".format(body_key),
                "issue_id": "R1-{0}-GROUP".format(body_key),
                "action_id": "AUTO_REPAIR_R1_DRAFT_TO_MINIMUM",
                "action_version": "planned-1",
                "target_body_tag": issue.get("body_tag"),
                "target_body_selection_index": body_selection_indexes.get(body_key),
                "target_face_tags": target_face_tags,
                "parameters": {
                    "target_angle_deg": -3.0,
                    "required_minimum_angle_deg": 3.0,
                },
                "preconditions": [
                    "必须明确目标实体和四个侧面 Tag",
                    "必须建立 NX Undo Mark 或备份",
                    "必须在执行后复审 R1，且不得产生新的 R2/R3/R4 问题",
                ],
                "expected_result": {"rule_id": "R1", "status": "pass"},
                "affected_objects": target_face_tags,
                "risk_level": "medium",
                "approval_status": "not_required",
                "execution_required": True,
                "repairability": "auto_repair_allowed",
                "description": "四个主侧面统一修正为 -3° 有符号拔模角，满足侧面与 Z 轴不小于 3°。",
            })
        elif rule_id == "R3":
            plan_items.append({
                "plan_id": "PLAN-" + issue["issue_id"],
                "issue_id": issue["issue_id"],
                "action_id": "AUTO_REPAIR_R3_BOTTOM_ROTATE_TO_Z90",
                "action_version": "planned-1",
                "target_body_tag": issue.get("body_tag"),
                "target_body_selection_index": body_selection_indexes.get(body_key),
                "target_face_tags": issue.get("face_tags", []),
                "parameters": {
                    "target_angle_to_z_deg": 90.0,
                    "tolerance_deg": 0.1,
                },
                "preconditions": [
                    "必须明确目标实体和底面 Tag",
                    "必须建立 NX Undo Mark 或备份",
                    "必须在执行后复审 R3，且不得产生新的 R2/R4 问题",
                ],
                "expected_result": {"rule_id": "R3", "status": "pass"},
                "affected_objects": issue.get("face_tags", []),
                "risk_level": "high",
                "approval_status": "not_required",
                "execution_required": True,
                "repairability": "auto_repair_allowed",
                "description": "将底面绕其倾斜方向旋转到与 Z 轴 90°，公差为 ±0.1°。",
            })
        elif rule_id == "R4":
            action_id = "AUTO_REPAIR_R4_POSITIVE_SIGNED_DRAFT"
            action_version = "planned-1"
            interaction_request = issue.get("interaction_request")
            approval_status = "not_required"
            execution_required = True
            repairability = "auto_repair_allowed"
            description = "R4 已明确无需人工确认；在满足 Undo、目标 Tag 和复审门禁后，可按自动修复执行。"
        elif rule_id == "R9" and issue.get("interaction_request"):
            decision = radius_decisions.get(issue["issue_id"], "no")
            interaction_request = dict(issue.get("interaction_request") or {})
            interaction_request["response"] = decision
            if decision == "yes":
                action_id = "ADJUST_ANALYTIC_RADIUS"
                action_version = "planned-1"
                approval_status = "approved"
                execution_required = True
                repairability = "human_confirm"
                description = "用户确认需要调整圆角；已生成圆角调整计划，执行前仍需 Undo、目标 Tag 和复审门禁。"
            else:
                action_id = None
                action_version = None
                approval_status = "rejected" if decision == "no" else "waiting_human_confirmation"
                execution_required = False
                repairability = "human_confirm"
                description = "用户未确认调整圆角；保留问题和红色提示，不修改模型。"
        elif rule_id == "R2":
            action_id = None
            action_version = None
            interaction_request = issue.get("interaction_request")
            approval_status = "waiting_human_confirmation"
            execution_required = False
            repairability = "human_confirm"
            description = "已计算建议补高量，但未决定从顶面、底面或历史特征补偿。"
        else:
            action_id = None
            action_version = None
            interaction_request = issue.get("interaction_request")
            approval_status = "waiting_human_confirmation"
            execution_required = False
            repairability = "human_confirm"
            description = "当前只生成修复建议，不执行几何修改。"

        if rule_id in ("R1", "R3"):
            continue

        plan_items.append({
            "plan_id": "PLAN-" + issue["issue_id"],
            "issue_id": issue["issue_id"],
            "action_id": action_id,
            "action_version": action_version,
            "target_body_tag": issue.get("body_tag"),
            "target_body_selection_index": body_selection_indexes.get(body_key),
            "target_face_tags": issue.get("face_tags", []),
            "parameters": {
                "suggested_delta": issue.get("suggested_delta"),
                "interaction_request": interaction_request,
            },
            "preconditions": [
                "必须明确目标实体和面 Tag",
                "必须建立 NX Undo Mark 或备份",
                "必须在执行后完整复审",
            ],
            "expected_result": {"rule_id": rule_id, "status": "pass"},
            "affected_objects": [],
            "risk_level": issue.get("risk_level"),
            "approval_status": approval_status,
            "execution_required": execution_required,
            "repairability": repairability,
            "description": description,
        })

    has_waiting_confirmation = any(
        item.get("approval_status") == "waiting_human_confirmation"
        for item in plan_items
    )
    has_executable_item = any(item.get("execution_required") for item in plan_items)
    if not plan_items:
        plan_status = "no_issue"
    elif has_waiting_confirmation:
        plan_status = "waiting_human_confirmation"
    elif has_executable_item:
        plan_status = "ready_to_repair"
    else:
        plan_status = "plan_only"

    return {
        "protocol_version": "1.0",
        "document_type": "repair_plan",
        "run_id": review_before.get("run_id"),
        "created_at": review_before.get("created_at"),
        "producer": {
            "name": "ZD_AutoRepairWorkflow",
            "component": "repair_planner",
            "component_version": "1.0.0",
            "source_baseline": review_before.get("producer", {}).get("source_baseline"),
        },
        "status": plan_status,
        "summary": "已生成修复计划；R1、R3、R4 自动修复项无需人工确认，但仍需由 NX 执行器执行并在执行后复审。",
        "context": review_before.get("context", {}),
        "data": {
            "plan_items": plan_items,
            "execution_required": any(item.get("execution_required") for item in plan_items),
        },
        "errors": [],
    }
