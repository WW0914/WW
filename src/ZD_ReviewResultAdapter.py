# -*- coding: utf-8 -*-
"""将直顶头审查插件旧版 JSON 转换为自动修复协议对象。"""

import datetime
import os


PROTOCOL_VERSION = "1.0"
PLUGIN_BASELINE = "直顶头审查_v1.0_20260723"
MIN_HEIGHT = 30.0
ANGULAR_TOLERANCE = 1.0e-6


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()


def _tag(value):
    return None if value is None else str(value)


def _status(passed):
    return "pass" if passed else "fail"


def _body_center(body):
    box = body.get("bounding_box") or {}
    minimum = box.get("min")
    maximum = box.get("max")
    if not minimum or not maximum:
        return None
    return [
        (minimum[0] + maximum[0]) * 0.5,
        (minimum[1] + maximum[1]) * 0.5,
        (minimum[2] + maximum[2]) * 0.5,
    ]


def _issue_id(rule_id, body_tag, index):
    return "{0}-{1}-{2:03d}".format(rule_id, body_tag, index)


def adapt_legacy_result(
        legacy_result,
        run_id,
        workflow_mode="plan_only",
        radius_limit=None,
        document_type="review_before"):
    """将现有审查 JSON 转成审查前或修复后复审协议。"""
    if radius_limit is None:
        radius_limit = float(legacy_result.get("radius_limit_mm", 0.0) or 0.0)

    body_results = []
    issues = []
    selected_tags = []
    issue_sequence = 1

    for selection_index, legacy_body in enumerate(legacy_result.get("bodies", [])):
        body_tag = _tag(legacy_body.get("body_tag"))
        if body_tag is not None:
            selected_tags.append(body_tag)

        height = float(legacy_body.get("height_mm", 0.0) or 0.0)
        height_passed = bool(legacy_body.get("height_passed", height >= MIN_HEIGHT))
        required_height_increase = max(0.0, MIN_HEIGHT - height)
        body_box = {
            "min": None,
            "max": None,
            "height": height,
            "unit": "mm",
            "source": "legacy_height_only",
        }
        rule_results = []
        display_actions = []
        body_issue_ids = []

        if not height_passed:
            issue_id = _issue_id("R2", body_tag, issue_sequence)
            issue_sequence += 1
            body_issue_ids.append(issue_id)
            display_actions.extend(["focus_body", "show_height_error_dialog"])
            issues.append({
                "issue_id": issue_id,
                "rule_id": "R2",
                "body_tag": body_tag,
                "face_tags": [],
                "issue_type": "rule_failure",
                "severity": "error",
                "reason_code": "R2_HEIGHT_BELOW_MINIMUM",
                "reason": (
                    "直顶高度不够，无法正常放下直顶杆；当前高度{0:.3f} mm，"
                    "建议至少增加{1:.3f} mm。"
                ).format(height, required_height_increase),
                "measured": {"value": height, "unit": "mm"},
                "required": {"comparison": "gte", "value": MIN_HEIGHT, "unit": "mm"},
                "suggested_delta": {
                    "value": required_height_increase,
                    "unit": "mm",
                    "meaning": "required_height_increase",
                },
                "interaction_request": None,
                "location": {"body_center": _body_center(body_box), "unit": "mm", "source": "legacy_result"},
                "repairability": "human_confirm",
                "risk_level": "medium",
                "requires_human_confirmation": True,
            })

        rule_results.append({
            "rule_id": "R2",
            "rule_name": "Z向最小高度",
            "enabled": True,
            "status": _status(height_passed),
            "standard": {"comparison": "gte", "value": MIN_HEIGHT, "unit": "mm"},
            "measurements": [{
                "height": height,
                "required_height_increase": required_height_increase,
                "unit": "mm",
                "status": _status(height_passed),
            }],
            "failed_object_tags": [body_tag] if not height_passed else [],
            "reason_code": None if height_passed else "R2_HEIGHT_BELOW_MINIMUM",
            "reason": "通过" if height_passed else "高度不足，需要增加{0:.3f} mm。".format(required_height_increase),
            "evidence": {"height_mm": height, "threshold_mm": MIN_HEIGHT},
        })

        for side_face in legacy_body.get("side_faces", []):
            face_tag = _tag(side_face.get("face_tag"))
            angle = float(side_face.get("angle_to_z_deg", 0.0) or 0.0)
            passed = bool(side_face.get("passed", angle + ANGULAR_TOLERANCE >= 3.0))
            if not passed:
                issue_id = _issue_id("R1", body_tag, issue_sequence)
                issue_sequence += 1
                body_issue_ids.append(issue_id)
                display_actions.append("highlight_face:{0}".format(face_tag))
                issues.append({
                    "issue_id": issue_id,
                    "rule_id": "R1",
                    "body_tag": body_tag,
                    "face_tags": [face_tag],
                    "issue_type": "rule_failure",
                    "severity": "error",
                    "reason_code": "R1_ANGLE_BELOW_MINIMUM",
                    "reason": "侧面相对Z轴角度小于3°。",
                    "measured": {"value": angle, "unit": "degree"},
                    "required": {"comparison": "gte", "value": 3.0, "unit": "degree"},
                    "suggested_delta": None,
                    "interaction_request": None,
                    "location": {"face_tag": face_tag},
                    "repairability": "human_confirm",
                    "risk_level": "medium",
                    "requires_human_confirmation": True,
                })

        side_faces = legacy_body.get("side_faces", [])
        rule_results.append({
            "rule_id": "R1",
            "rule_name": "主侧面最小倾角",
            "enabled": True,
            "status": "pass" if all(item.get("passed", False) for item in side_faces) and len(side_faces) == 4 else "fail",
            "standard": {"comparison": "gte", "value": 3.0, "unit": "degree"},
            "measurements": [{
                "face_tag": _tag(item.get("face_tag")),
                "angle_to_z": float(item.get("angle_to_z_deg", 0.0) or 0.0),
                "unit": "degree",
                "status": _status(bool(item.get("passed", False))),
            } for item in side_faces],
            "failed_object_tags": [_tag(item.get("face_tag")) for item in side_faces if not item.get("passed", False)],
            "reason_code": None,
            "reason": "通过" if all(item.get("passed", False) for item in side_faces) and len(side_faces) == 4 else "存在角度不足或侧面数量异常。",
            "evidence": {"side_face_count": len(side_faces)},
        })

        bottom = legacy_body.get("bottom_face")
        bottom_passed = bool(legacy_body.get("bottom_passed", True))
        if bottom and not bottom_passed:
            face_tag = _tag(bottom.get("face_tag"))
            issue_id = _issue_id("R3", body_tag, issue_sequence)
            issue_sequence += 1
            body_issue_ids.append(issue_id)
            display_actions.append("highlight_face:{0}".format(face_tag))
            angle = float(bottom.get("angle_to_z_deg", 0.0) or 0.0)
            issues.append({
                "issue_id": issue_id,
                "rule_id": "R3",
                "body_tag": body_tag,
                "face_tags": [face_tag],
                "issue_type": "rule_failure",
                "severity": "error",
                "reason_code": "R3_BOTTOM_ANGLE_OUT_OF_TOLERANCE",
                "reason": "底面与Z轴角度超出90°±0.1°。",
                "measured": {"value": angle, "unit": "degree"},
                "required": {"value": 90.0, "tolerance": 0.1, "unit": "degree"},
                "suggested_delta": None,
                "interaction_request": None,
                "location": {"face_tag": face_tag},
                "repairability": "human_confirm",
                "risk_level": "high",
                "requires_human_confirmation": True,
            })
        rule_results.append({
            "rule_id": "R3",
            "rule_name": "底面与Z轴角度",
            "enabled": True,
            "status": _status(bottom_passed),
            "standard": {"value": 90.0, "tolerance": 0.1, "unit": "degree"},
            "measurements": [bottom] if bottom else [],
            "failed_object_tags": [_tag(bottom.get("face_tag"))] if bottom and not bottom_passed else [],
            "reason_code": None if bottom_passed else "R3_BOTTOM_ANGLE_OUT_OF_TOLERANCE",
            "reason": "通过" if bottom_passed else "底面角度超差。",
            "evidence": {"candidate_face_tag": _tag(bottom.get("face_tag")) if bottom else None},
        })

        r4_failed_face_tags = [_tag(tag) for tag in legacy_body.get("r4_failed_face_tags", [])]
        for failed_face_tag in r4_failed_face_tags:
            issue_id = _issue_id("R4", body_tag, issue_sequence)
            issue_sequence += 1
            body_issue_ids.append(issue_id)
            display_actions.append("highlight_face:{0}".format(failed_face_tag))
            matched_side = None
            for side_face in legacy_body.get("side_faces", []):
                if _tag(side_face.get("face_tag")) == failed_face_tag:
                    matched_side = side_face
                    break

            signed_draft = None
            if matched_side is not None and matched_side.get("outward_normal_z") is not None:
                signed_draft = float(matched_side.get("angle_to_z_deg", 0.0) or 0.0)
                if float(matched_side.get("outward_normal_z")) < 0.0:
                    signed_draft = -signed_draft

            issues.append({
                "issue_id": issue_id,
                "rule_id": "R4",
                "body_tag": body_tag,
                "face_tags": [failed_face_tag],
                "issue_type": "rule_failure",
                "severity": "error",
                "reason_code": "R4_POSITIVE_SIGNED_DRAFT",
                "reason": "侧面相对 +Z 的有符号拔模角为正数。",
                "measured": {"value": signed_draft, "unit": "degree"},
                "required": {"comparison": "lte", "value": 0.0, "unit": "degree"},
                "suggested_delta": None,
                "interaction_request": None,
                "location": {"face_tag": failed_face_tag},
                "repairability": "auto_repair_allowed",
                "risk_level": "high",
                "requires_human_confirmation": False,
            })

        rule_results.append({
            "rule_id": "R4",
            "rule_name": "有符号拔模方向",
            "enabled": True,
            "status": _status(bool(legacy_body.get("r4_passed", not r4_failed_face_tags))),
            "standard": {"comparison": "lte", "value": 0.0, "unit": "degree"},
            "measurements": [{
                "face_tag": _tag(item.get("face_tag")),
                "angle_to_z": float(item.get("angle_to_z_deg", 0.0) or 0.0),
                "outward_normal_z": item.get("outward_normal_z"),
                "unit": "degree",
                "status": "fail" if _tag(item.get("face_tag")) in r4_failed_face_tags else "pass",
            } for item in legacy_body.get("side_faces", [])],
            "failed_object_tags": r4_failed_face_tags,
            "reason_code": None if not r4_failed_face_tags else "R4_POSITIVE_SIGNED_DRAFT",
            "reason": "通过" if not r4_failed_face_tags else "存在有符号拔模角为正数的侧面。",
            "evidence": {"r4_failed_face_tags": r4_failed_face_tags},
        })

        for radius_failure in legacy_body.get("radius_failures", []):
            face_tag = _tag(radius_failure.get("face_tag"))
            radius = float(radius_failure.get("radius_mm", 0.0) or 0.0)
            suggested_increase = max(0.0, radius_limit - radius)
            issue_id = _issue_id("R9", body_tag, issue_sequence)
            issue_sequence += 1
            body_issue_ids.append(issue_id)
            display_actions.append("highlight_face:{0}".format(face_tag))
            issues.append({
                "issue_id": issue_id,
                "rule_id": "R9",
                "body_tag": body_tag,
                "face_tags": [face_tag],
                "issue_type": "rule_failure",
                "severity": "warning",
                "reason_code": "R9_RADIUS_BELOW_MINIMUM",
                "reason": "检测到圆角小于设定值。",
                "measured": {"value": radius, "unit": "mm"},
                "required": {"value": radius_limit, "unit": "mm"},
                "suggested_delta": {
                    "value": suggested_increase,
                    "unit": "mm",
                    "meaning": "suggested_radius_increase",
                },
                "interaction_request": {
                    "interaction_type": "radius_adjustment_confirmation",
                    "message": "检测到圆角小于设定值。当前圆角：{0:.3f} mm，目标圆角：{1:.3f} mm，是否需要调整圆角？".format(radius, radius_limit),
                    "options": ["yes", "no"],
                    "default_option": "no",
                    "response": None,
                },
                "location": {"face_tag": face_tag},
                "repairability": "human_confirm",
                "risk_level": "medium",
                "requires_human_confirmation": True,
            })

        radius_failures = legacy_body.get("radius_failures", [])
        rule_results.append({
            "rule_id": "R9",
            "rule_name": "最小圆角",
            "enabled": radius_limit > 0.0,
            "status": "disabled" if radius_limit <= 0.0 else ("fail" if radius_failures else "pass"),
            "standard": {"value": radius_limit, "unit": "mm"},
            "measurements": radius_failures,
            "failed_object_tags": [_tag(item.get("face_tag")) for item in radius_failures],
            "reason_code": "R9_DISABLED_BY_ZERO_INPUT" if radius_limit <= 0.0 else ("R9_RADIUS_BELOW_MINIMUM" if radius_failures else None),
            "reason": "输入为0 mm，已关闭" if radius_limit <= 0.0 else ("存在圆角不足" if radius_failures else "通过"),
            "evidence": {"radius_limit_mm": radius_limit},
        })

        body_results.append({
            "body_tag": body_tag,
            "body_name": None,
            "selection_index": selection_index,
            "review_status": "fail" if body_issue_ids else "pass",
            "bounding_box": body_box,
            "rule_results": rule_results,
            "issue_ids": body_issue_ids,
            "display_actions": display_actions,
        })

    overall_status = "no_issue" if not issues else "partial_success"
    return {
        "protocol_version": PROTOCOL_VERSION,
        "document_type": document_type,
        "run_id": run_id,
        "created_at": _now_iso(),
        "producer": {
            "name": "ZD_AutoRepairWorkflow",
            "component": "review_result_adapter",
            "component_version": "1.0.0",
            "source_baseline": PLUGIN_BASELINE,
        },
        "status": overall_status,
        "summary": (
            "修复后复审完成，发现{0}个问题。" if document_type == "review_after"
            else "只读转换完成，发现{0}个问题。"
        ).format(len(issues)),
        "context": {
            "nx_version": legacy_result.get("nx_version"),
            "part_path": legacy_result.get("part_path"),
            "part_name": os.path.basename(legacy_result.get("part_path", "")),
            "part_modified_before_run": None,
            "workflow_mode": workflow_mode,
            "wcs_z_axis": [0.0, 0.0, 1.0],
            "numeric_tolerance": {"linear": 1.0e-6, "angular": ANGULAR_TOLERANCE},
            "selected_body_tags": selected_tags,
            "user_inputs": {
                "min_radius": {"value": radius_limit, "unit": "mm", "source": "legacy_result"},
            },
        },
        "data": {"body_results": body_results, "issues": issues},
        "errors": [],
    }
