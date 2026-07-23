# -*- coding: utf-8 -*-
"""在 NX2306 会话中执行已批准的直顶头自动修复计划。"""

import datetime
import json
import math
import os
import sys


PROTOCOL_VERSION = "1.0"
R4_ACTION_ID = "AUTO_REPAIR_R4_POSITIVE_SIGNED_DRAFT"
R1_ACTION_ID = "AUTO_REPAIR_R1_DRAFT_TO_MINIMUM"
R3_ACTION_ID = "AUTO_REPAIR_R3_BOTTOM_ROTATE_TO_Z90"
R4_ANGLE_TOLERANCE = 1.0e-6
NX_DISTANCE_TOLERANCE_MM = 0.001


def _now_iso():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().isoformat()


def _write_json(path, value):
    directory = os.path.dirname(os.path.abspath(path))
    if directory:
        os.makedirs(directory, exist_ok=True)
    temporary_path = path + ".tmp"
    with open(temporary_path, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    os.replace(temporary_path, path)


class NXRepairExecutor(object):
    """执行计划中明确允许自动执行的 R1、R3、R4 修复项。"""

    def __init__(self, session=None):
        try:
            import NXOpen
            import NXOpen.UF
        except ImportError as error:
            raise RuntimeError("必须在 NX2306 的 NX Python 环境中运行修复执行器。") from error
        self.NXOpen = NXOpen
        self.session = session or NXOpen.Session.GetSession()
        self.ufs = NXOpen.UF.UFSession.GetUFSession()

    def _object_by_tag(self, tag):
        manager = getattr(self.NXOpen, "TaggedObjectManager", None)
        if manager is None or not hasattr(manager, "GetTaggedObject"):
            raise RuntimeError("当前 NX Python 环境没有 TaggedObjectManager。")
        obj = manager.GetTaggedObject(int(tag))
        if obj is None:
            raise RuntimeError("无法根据 Tag {0} 找到 NX 对象。".format(tag))
        return obj

    def _body_by_selection_index(self, selection_index, fallback_tag=None):
        bodies = list(self.session.Parts.Work.Bodies)
        if selection_index is not None:
            index = int(selection_index)
            if 0 <= index < len(bodies):
                return bodies[index]
        if fallback_tag is not None:
            for body in bodies:
                if int(body.Tag) == int(fallback_tag):
                    return body
        raise RuntimeError("当前工作部件中找不到计划指定的目标实体。")

    def _find_face(self, body, face_tag):
        for face in body.GetFaces():
            if int(face.Tag) == int(face_tag):
                return face
        raise RuntimeError(
            "实体 Tag {0} 中找不到错误面 Tag {1}。".format(body.Tag, face_tag))

    def _face_data(self, face):
        return self.ufs.Modeling.AskFaceData(face.Tag)

    def _find_stationary_face(self, body, target_face):
        candidates = []
        for face in body.GetFaces():
            if face == target_face:
                continue
            data = self._face_data(face)
            direction = data[2]
            face_box = data[3]
            if abs(float(direction[2])) < 0.9:
                continue
            candidates.append((float(face_box[2]), face))
        if not candidates:
            raise RuntimeError(
                "实体 Tag {0} 没有可作为 R4 固定参考的 Z 向端面。".format(body.Tag))
        candidates.sort(key=lambda item: item[0])
        return candidates[0][1]

    def _create_face_collector(self, part, face_or_faces):
        faces = face_or_faces if isinstance(face_or_faces, (list, tuple)) else [face_or_faces]
        collector = part.ScCollectors.CreateCollector()
        rule = part.ScRuleFactory.CreateRuleFaceDumb(faces)
        collector.ReplaceRules([rule], False)
        return collector

    def _create_z_direction(self, part):
        origin = self.NXOpen.Point3d(0.0, 0.0, 0.0)
        vector = self.NXOpen.Vector3d(0.0, 0.0, 1.0)
        update_option = self.NXOpen.SmartObject.UpdateOption.WithinModeling
        return part.Directions.CreateDirection(origin, vector, update_option)

    def _create_draft(self, body, faces, stationary_face, target_angle):
        part = self.session.Parts.Work
        if part is None:
            raise RuntimeError("NX 当前没有工作部件。")

        if target_angle >= -R4_ANGLE_TOLERANCE:
            raise RuntimeError("目标拔模角必须为明确负数。")

        target_collector = self._create_face_collector(part, faces)
        stationary_collector = self._create_face_collector(part, stationary_face)
        direction = self._create_z_direction(part)
        builder = None
        try:
            builder = part.Features.CreateDraftBuilder(None)
            builder.Direction = direction
            builder.AngleTolerance = R4_ANGLE_TOLERANCE
            builder.DistanceTolerance = NX_DISTANCE_TOLERANCE_MM
            builder.StationaryReference.ReplaceRules(
                stationary_collector.GetRules(), False)
            angle_set = part.CreateExpressionCollectorSet(
                target_collector,
                "{0:.12f}".format(target_angle),
                "Degrees",
                0)
            builder.FaceSetAngleExpressionList.Append(angle_set)
            feature = builder.CommitFeature()
            if feature is None:
                raise RuntimeError("NX DraftBuilder 未返回修复特征。")
            return feature, target_angle
        finally:
            if builder is not None:
                builder.Destroy()

    def _create_bottom_rotation(self, face, measured_normal):
        part = self.session.Parts.Work
        nx = float(measured_normal[0])
        ny = float(measured_normal[1])
        nz = float(measured_normal[2])
        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        if length <= 1.0e-12:
            raise RuntimeError("R3 底面法向量无效，拒绝自动修复。")
        nx /= length
        ny /= length
        nz /= length
        target_z = -1.0 if nz < 0.0 else 1.0
        target = (0.0, 0.0, target_z)
        dot = max(-1.0, min(1.0, nx * target[0] + ny * target[1] + nz * target[2]))
        correction = math.acos(dot)
        if correction <= math.radians(0.1):
            raise RuntimeError("R3 底面已经在允许公差内，无需旋转。")

        axis_x = ny * target[2] - nz * target[1]
        axis_y = nz * target[0] - nx * target[2]
        axis_z = nx * target[1] - ny * target[0]
        axis_length = math.sqrt(axis_x * axis_x + axis_y * axis_y + axis_z * axis_z)
        if axis_length <= 1.0e-12:
            raise RuntimeError("R3 无法确定底面旋转轴。")
        axis = self.NXOpen.Vector3d(
            axis_x / axis_length,
            axis_y / axis_length,
            axis_z / axis_length)
        point_data = self._face_data(face)[1]
        pivot = self.NXOpen.Point3d(
            float(point_data[0]), float(point_data[1]), float(point_data[2]))
        update_option = self.NXOpen.SmartObject.UpdateOption.WithinModeling
        axis_object = part.Axes.CreateAxis(pivot, axis, update_option)
        builder = None
        try:
            builder = part.Features.CreateAdmMoveFaceBuilder(None)
            if builder is None:
                raise RuntimeError("NX AdmMoveFaceBuilder 返回空构建器。")
            builder.FaceToMove.SelectEntities([face])
            builder.Motion.Option = self.NXOpen.GeometricUtilities.ModlMotionOptions.Angle
            builder.Motion.AngularAxis = axis_object
            builder.Motion.Angle.RightHandSide = "{0:.12f}".format(
                math.degrees(correction))
            feature = builder.CommitFeature()
            if feature is None:
                raise RuntimeError("NX AdmMoveFaceBuilder 未返回修复特征。")
            return feature, math.degrees(correction), axis_object
        finally:
            if builder is not None:
                builder.Destroy()

    def _review_body(self, body):
        module_directory = os.path.dirname(os.path.abspath(__file__))
        if module_directory not in sys.path:
            sys.path.insert(0, module_directory)
        from ZD_StraightLifterReview import StraightLifterReviewer

        reviewer = StraightLifterReviewer()
        return reviewer.review_body(body, 0.0, interactive=False)

    def _verify_body(self, body, run_id, part_path):
        from ZD_ReviewResultAdapter import adapt_legacy_result

        legacy_body = self._review_body(body)
        legacy_result = {
            "part_path": part_path,
            "nx_version": self.session.GetEnvironmentVariableValue(
                "NX_FULL_VERSION"),
            "radius_limit_mm": 0.0,
            "bodies": [legacy_body],
        }
        return adapt_legacy_result(
            legacy_result, run_id, workflow_mode="verify_only")

    @staticmethod
    def _r4_failures(review):
        return [
            issue for issue in review.get("data", {}).get("issues", [])
            if issue.get("rule_id") == "R4"
        ]

    @staticmethod
    def _rule_failures(review, rule_id):
        return [
            issue for issue in review.get("data", {}).get("issues", [])
            if issue.get("rule_id") == rule_id
        ]

    @staticmethod
    def _new_after_review(repair_plan):
        return {
            "protocol_version": PROTOCOL_VERSION,
            "document_type": "review_after",
            "run_id": repair_plan.get("run_id"),
            "created_at": _now_iso(),
            "producer": {
                "name": "ZD_AutoRepairWorkflow",
                "component": "repair_verifier",
                "component_version": "1.0.0",
            },
            "status": "not_available",
            "context": repair_plan.get("context", {}),
            "data": {"body_results": [], "issues": []},
            "errors": [],
        }

    @staticmethod
    def _append_after_review(after_review_document, body_review):
        after_review_document["data"]["body_results"].extend(
            body_review.get("data", {}).get("body_results", []))
        after_review_document["data"]["issues"].extend(
            body_review.get("data", {}).get("issues", []))

    def _write_after_review(self, execution_path, after_review_document):
        after_path = os.path.join(
            os.path.dirname(os.path.abspath(execution_path)), "review-after.json")
        _write_json(after_path, after_review_document)
        return after_path

    def _save_part(self, part):
        """将当前已复审通过的模型保存回已明确指定的 PRT。"""
        save_components = self.NXOpen.BasePart.SaveComponents.TrueValue
        keep_open = self.NXOpen.BasePart.CloseAfterSave.FalseValue
        save_status = part.Save(save_components, keep_open)
        if save_status is not None and hasattr(save_status, "Dispose"):
            save_status.Dispose()

    def execute(self, repair_plan, execution_path, save_part=False):
        run_id = repair_plan.get("run_id") or _now_iso()
        part_path = repair_plan.get("context", {}).get("part_path")
        execution = {
            "protocol_version": PROTOCOL_VERSION,
            "document_type": "repair_execution",
            "run_id": run_id,
            "created_at": _now_iso(),
            "producer": {
                "name": "ZD_AutoRepairWorkflow",
                "component": "nx_repair_executor",
                "component_version": "1.0.0",
            },
            "status": "running",
            "part_path": part_path,
            "items": [],
            "rollback": {
                "available": False,
                "used": False,
                "mark_id": None,
            },
            "save": {
                "requested": bool(save_part),
                "saved": False,
                "path": part_path,
            },
            "errors": [],
        }
        after_review_document = self._new_after_review(repair_plan)
        active_mark = None
        active_body = None
        try:
            part = self.session.Parts.Work
            if part is None:
                raise RuntimeError("请先在 NX 中打开目标 PRT。")
            action_priority = {R3_ACTION_ID: 0, R1_ACTION_ID: 1, R4_ACTION_ID: 2}
            plan_items = sorted(
                repair_plan.get("data", {}).get("plan_items", []),
                key=lambda item: action_priority.get(item.get("action_id"), 99))
            for item in plan_items:
                if not item.get("execution_required"):
                    continue
                if item.get("action_id") not in (R1_ACTION_ID, R3_ACTION_ID, R4_ACTION_ID):
                    raise RuntimeError(
                        "计划包含未实现的自动修复动作：{0}".format(
                            item.get("action_id")))
                body = self._body_by_selection_index(
                    item.get("target_body_selection_index"),
                    fallback_tag=item.get("target_body_tag"))
                active_body = body
                if not isinstance(body, self.NXOpen.Body):
                    raise RuntimeError("目标 Tag 不是 NX 实体。")
                issue_id = item.get("issue_id")
                review_before = self._verify_body(
                    body, run_id + "-before-" + str(issue_id), part_path)
                action_id = item.get("action_id")
                rule_id = {
                    R1_ACTION_ID: "R1",
                    R3_ACTION_ID: "R3",
                    R4_ACTION_ID: "R4",
                }[action_id]
                rule_issues = self._rule_failures(review_before, rule_id)
                if not rule_issues:
                    raise RuntimeError(
                        "{0} 原问题在执行前已经不存在，拒绝重复修改。".format(rule_id))
                current_face_tags = [
                    tag
                    for rule_issue in rule_issues
                    for tag in rule_issue.get("face_tags", [])
                ]
                if not current_face_tags:
                    raise RuntimeError("当前复审没有返回可执行的错误面 Tag。")
                faces = [self._find_face(body, tag) for tag in current_face_tags]

                mark = self.session.SetUndoMark(
                    self.NXOpen.Session.MarkVisibility.Visible,
                    "ZD {0} 自动修复 {1}".format(rule_id, issue_id))
                active_mark = mark
                execution["rollback"]["available"] = True
                execution["rollback"]["mark_id"] = str(mark)
                stationary_face = None
                target_angle = None
                correction_angle = None
                axis_object = None
                if action_id == R3_ACTION_ID:
                    measured_normal = self._face_data(faces[0])[2]
                    feature, correction_angle, axis_object = self._create_bottom_rotation(
                        faces[0], measured_normal)
                elif action_id == R1_ACTION_ID:
                    stationary_face = self._find_stationary_face(body, faces[0])
                    target_angle = -3.0
                    feature, target_angle = self._create_draft(
                        body, faces, stationary_face, target_angle)
                else:
                    face = faces[0]
                    measured_angle = rule_issues[0].get("measured", {}).get("value")
                    if measured_angle is None or float(measured_angle) <= R4_ANGLE_TOLERANCE:
                        raise RuntimeError("R4 缺少明确的正拔模角证据，拒绝自动修复。")
                    stationary_face = self._find_stationary_face(body, face)
                    target_angle = -abs(float(measured_angle))
                    feature, target_angle = self._create_draft(
                        body, [face], stationary_face, target_angle)
                after_review = self._verify_body(
                    body, run_id + "-after-" + str(issue_id), part_path)
                self._append_after_review(after_review_document, after_review)
                remaining = self._rule_failures(after_review, rule_id)
                item_result = {
                    "plan_id": item.get("plan_id"),
                    "issue_id": issue_id,
                    "action_id": item.get("action_id"),
                    "status": "pass" if not remaining else "verify_failed",
                    "target_body_tag": str(body.Tag),
                    "target_face_tags": [str(face.Tag) for face in faces],
                    "stationary_face_tag": str(stationary_face.Tag) if stationary_face is not None else None,
                    "target_angle_deg": target_angle,
                    "correction_angle_deg": correction_angle,
                    "axis_tag": str(axis_object.Tag) if axis_object is not None else None,
                    "feature_tag": str(feature.Tag),
                    "remaining_rule_issues": remaining,
                }
                execution["items"].append(item_result)
                if remaining:
                    self.session.UndoToMark(mark, None)
                    execution["rollback"]["used"] = True
                    active_mark = None
                    item_result["status"] = "rolled_back_after_verify_failure"
                    raise RuntimeError(
                        "{0} 修复后复审仍失败，已自动回滚：{1}".format(rule_id, issue_id))

            if save_part:
                self._save_part(part)
                execution["save"]["saved"] = True
            execution["status"] = "success"
        except Exception as error:
            if active_mark is not None and not execution["rollback"]["used"]:
                try:
                    self.session.UndoToMark(active_mark, None)
                    execution["rollback"]["used"] = True
                    execution["rollback"]["reason"] = "NX API 异常或执行异常"
                except Exception as rollback_error:
                    execution["rollback"]["error"] = str(rollback_error)
            if active_body is not None and not after_review_document["data"]["body_results"]:
                try:
                    rollback_review = self._verify_body(
                        active_body, run_id + "-rollback", part_path)
                    self._append_after_review(after_review_document, rollback_review)
                except Exception as verify_error:
                    after_review_document["errors"].append({
                        "code": "ROLLBACK_VERIFY_FAILED",
                        "message": str(verify_error),
                    })
            execution["status"] = "failed" if not execution["rollback"]["used"] else "rolled_back"
            execution["errors"].append({
                "code": "NX_REPAIR_EXECUTION_FAILED",
                "message": str(error),
            })
        if execution["status"] == "success":
            after_review_document["status"] = (
                "pass" if not after_review_document["data"]["issues"]
                else "partial_success")
        elif after_review_document["data"]["body_results"]:
            after_review_document["status"] = "partial_success"
        after_path = self._write_after_review(execution_path, after_review_document)
        execution["review_after_path"] = after_path
        _write_json(execution_path, execution)
        return execution, after_review_document


def execute_repair_plan(repair_plan_path, execution_path, session=None, save_part=False):
    with open(repair_plan_path, "r", encoding="utf-8-sig") as stream:
        repair_plan = json.load(stream)
    executor = NXRepairExecutor(session=session)
    return executor.execute(repair_plan, execution_path, save_part=save_part)


def main():
    if len(sys.argv) != 3:
        raise SystemExit("用法：ZD_NXRepairExecutor.py repair-plan.json repair-execution.json")
    execution, _ = execute_repair_plan(sys.argv[1], sys.argv[2])
    print(json.dumps(execution, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
