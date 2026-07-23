# -*- coding: utf-8 -*-
"""直顶头审查 NX Python 版本。

此文件与 ZD_StraightLifterReview.dll 保持规则同步。
在 NX 中通过“文件 -> 执行 -> NX Open”运行本文件。
选择实体时可连续选择多个直顶头，按取消结束选择并开始审查。
"""

import json
import math
import os
import sys

import NXOpen
import NXOpen.UF


MIN_SIDE_ANGLE = 3.0
MIN_HEIGHT = 30.0
BOTTOM_ANGLE_TOLERANCE = 0.1
RADIUS_LIMIT = 0.0
RED_COLOR = 186
PLANAR_FACE_TYPE = 22
CYLINDRICAL_FACE_TYPE = 16


class StraightLifterReviewer(object):
    """与 DLL 审查规则一致的 Python 审查器。"""

    def __init__(self):
        self.session = NXOpen.Session.GetSession()
        self.ui = NXOpen.UI.GetUI()
        self.ufs = NXOpen.UF.UFSession.GetUFSession()
        self.highlighted_faces = []
        self.highlighted_bodies = []

    @staticmethod
    def angle_to_z_degrees(normal_z):
        """返回平面相对 Z 轴的夹角：侧面接近 0 度，端面接近 90 度。"""
        clamped = max(-1.0, min(1.0, abs(normal_z)))
        return math.degrees(math.asin(clamped))

    def select_bodies(self):
        """连续选择多个实体；用户按取消结束选择。"""
        bodies = []
        selected_tags = set()
        selection_manager = self.ui.SelectionManager
        mask = [NXOpen.Selection.MaskTriple(NXOpen.UF.UFConstants.UF_solid_type, 0, 0)]

        while True:
            response, selected_object, _ = selection_manager.SelectTaggedObject(
                "选择直顶头实体；继续选择，完成后点击取消",
                "直顶头审查",
                NXOpen.SelectionSelectionScope.WorkPart,
                NXOpen.SelectionSelectionAction.ClearAndEnableSpecific,
                False,
                False,
                mask)

            if response not in (
                    NXOpen.SelectionResponse.Ok,
                    NXOpen.SelectionResponse.ObjectSelected,
                    NXOpen.SelectionResponse.ObjectSelectedByName):
                break

            if isinstance(selected_object, NXOpen.Body) and selected_object.Tag not in selected_tags:
                bodies.append(selected_object)
                selected_tags.add(selected_object.Tag)

        return bodies

    def highlight_face(self, face):
        """临时将错误面标红，并保存原始颜色。"""
        for saved_face, _ in self.highlighted_faces:
            if saved_face == face:
                return

        self.highlighted_faces.append((face, face.Color))
        face.SetColor(RED_COLOR)
        face.RedisplayObject()

    def clear_review_display(self):
        """恢复本次审查改变的面颜色和实体高亮。"""
        for face, original_color in self.highlighted_faces:
            face.SetColor(original_color)
            face.RedisplayObject()
        self.highlighted_faces = []

        for body in self.highlighted_bodies:
            body.Unhighlight()
        self.highlighted_bodies = []

    def commit_review_display(self):
        """保留错误面红色，只清除实体的临时高亮。"""
        self.highlighted_faces = []
        for body in self.highlighted_bodies:
            body.Unhighlight()
        self.highlighted_bodies = []

    def fly_to_body(self, body):
        """将当前高度错误直顶头放大到 NX 实体适应视图大小。"""
        work_part = self.session.Parts.Work
        if work_part is None:
            return

        work_view = work_part.ModelingViews.WorkView
        work_view.FitToObjects([body])
        work_view.UpdateDisplay()

    def write_report(self, lines):
        """输出单个实体的审查报告。"""
        listing_window = self.session.ListingWindow
        listing_window.Open()
        listing_window.WriteLine("========== 直顶头审查 ==========")
        for line in lines:
            listing_window.WriteLine(line)
        listing_window.WriteLine("================================")

    def review_body(self, body, radius_limit, interactive=True):
        """执行 R1、R2、R3、R9。"""
        faces = list(body.GetFaces())
        face_data = [self.ufs.Modeling.AskFaceData(face.Tag) for face in faces]
        if not face_data:
            raise RuntimeError("实体 Tag {0} 没有可用于审查的面。".format(body.Tag))

        z_min = min(data[3][2] for data in face_data)
        z_max = max(data[3][5] for data in face_data)
        height = z_max - z_min
        side_faces = []
        side_directions = []
        failed_faces = []
        bottom_face = None
        bottom_normal_z = 0.0
        bottom_z = float("inf")
        report = ["审查实体 Tag {0}".format(body.Tag)]
        result = {
            "body_tag": int(body.Tag),
            "height_mm": height,
            "height_passed": height >= MIN_HEIGHT,
            "side_faces": [],
            "side_face_count": 0,
            "side_face_count_passed": False,
            "r4_passed": False,
            "r4_failed_face_tags": [],
            "bottom_face": None,
            "bottom_passed": False,
            "radius_limit_mm": radius_limit,
            "radius_failures": [],
            "failed_face_tags": [],
        }

        report.append(
            "[R2] Z 向高度={0:.3f} mm，标准 >= {1:.3f} mm：{2}".format(
                height, MIN_HEIGHT, "通过。" if height >= MIN_HEIGHT else "失败。"))
        if height < MIN_HEIGHT and interactive:
            body.Highlight()
            self.highlighted_bodies.append(body)
            self.fly_to_body(body)
            self.ui.NXMessageBox.Show(
                "直顶头审查",
                NXOpen.NXMessageBox.DialogType.Warning,
                "直顶高度不够，无法正常放下直顶杆。\n"
                "当前直顶头 Tag：{0}\n"
                "关闭本窗口后将继续检查下一个实体。".format(body.Tag))

        for face, data in zip(faces, face_data):
            face_type, _, direction, face_box, radius, _, _ = data

            if face_type == PLANAR_FACE_TYPE:
                angle = self.angle_to_z_degrees(direction[2])
                if angle >= 60.0 and face_box[2] < bottom_z:
                    bottom_z = face_box[2]
                    bottom_face = face
                    bottom_normal_z = direction[2]

                if angle <= 30.0:
                    side_faces.append((face, angle))
                    face_center_x = (face_box[0] + face_box[3]) * 0.5
                    face_center_y = (face_box[1] + face_box[4]) * 0.5
                    body_center_x = (
                        min(item[3][0] for item in face_data)
                        + max(item[3][3] for item in face_data)) * 0.5
                    body_center_y = (
                        min(item[3][1] for item in face_data)
                        + max(item[3][4] for item in face_data)) * 0.5
                    horizontal_length = math.hypot(direction[0], direction[1])
                    outward_length = math.hypot(
                        face_center_x - body_center_x,
                        face_center_y - body_center_y)
                    outward_alignment = 0.0
                    if horizontal_length > 1.0e-12 and outward_length > 1.0e-12:
                        outward_alignment = (
                            direction[0] * (face_center_x - body_center_x)
                            + direction[1] * (face_center_y - body_center_y)
                        ) / (horizontal_length * outward_length)
                    oriented_normal_z = (
                        direction[2] if outward_alignment >= 0.0 else -direction[2])
                    side_directions.append((face, oriented_normal_z))
                    result["side_faces"].append({
                        "face_tag": int(face.Tag),
                        "angle_to_z_deg": angle,
                        "passed": angle + 1.0e-6 >= MIN_SIDE_ANGLE,
                        "outward_normal_z": oriented_normal_z,
                    })
                    if angle + 1.0e-6 < MIN_SIDE_ANGLE:
                        failed_faces.append(face)

            if radius_limit > 0.0 and face_type == CYLINDRICAL_FACE_TYPE and radius + 1.0e-6 < radius_limit:
                failed_faces.append(face)
                result["radius_failures"].append({
                    "face_tag": int(face.Tag),
                    "radius_mm": radius,
                })
                report.append(
                    "[R9] 圆角面 Tag {0} 半径={1:.3f} mm，小于输入标准 {2:.3f} mm：失败，已标红。".format(
                        face.Tag, radius, radius_limit))

        result["side_face_count"] = len(side_faces)
        result["side_face_count_passed"] = len(side_faces) == 4
        if len(side_faces) != 4:
            report.append("[R1] 主侧面识别失败：候选面数量={0}，预期为 4。".format(len(side_faces)))
        else:
            for face, angle in side_faces:
                report.append(
                    "[R1] 侧面 Tag {0} 与 Z 轴夹角={1:.3f}°，标准 >= {2:.3f}°：{3}".format(
                        face.Tag, angle, MIN_SIDE_ANGLE,
                        "通过。" if angle + 1.0e-6 >= MIN_SIDE_ANGLE else "失败，已标红。"))

        if len(side_directions) != 4:
            report.append("[R4] 主侧面识别失败，无法检查拔模角正负方向。")
        else:
            r4_failed_faces = []
            for face, normal_z in side_directions:
                signed_draft_angle = math.degrees(math.asin(
                    max(-1.0, min(1.0, normal_z))))
                if signed_draft_angle > 1.0e-6:
                    r4_failed_faces.append(face)
                    failed_faces.append(face)
                    report.append(
                        "[R4] 侧面 Tag {0} 相对 +Z 的拔模角={1:.3f}°，为正数：失败，已标红。".format(
                            face.Tag, signed_draft_angle))
                else:
                    report.append(
                        "[R4] 侧面 Tag {0} 相对 +Z 的拔模角={1:.3f}°，不是正数：通过。".format(
                            face.Tag, signed_draft_angle))
            result["r4_failed_face_tags"] = [
                int(face.Tag) for face in r4_failed_faces]
            result["r4_passed"] = not r4_failed_faces

        if bottom_face is not None:
            normal_angle = 90.0 - self.angle_to_z_degrees(bottom_normal_z)
            is_failed = normal_angle > BOTTOM_ANGLE_TOLERANCE
            result["bottom_face"] = {
                "face_tag": int(bottom_face.Tag),
                "angle_to_z_deg": 90.0 - normal_angle,
            }
            result["bottom_passed"] = not is_failed
            report.append(
                "[R3] 底面 Tag {0} 与 Z 轴夹角={1:.3f}°，标准 90.000°±{2:.3f}°：{3}".format(
                    bottom_face.Tag,
                    90.0 - normal_angle,
                    BOTTOM_ANGLE_TOLERANCE,
                    "失败，已标红。" if is_failed else "通过。"))
            if is_failed:
                failed_faces.append(bottom_face)
        else:
            report.append("[R3] 未识别到底面，无法检查底面垂直度。")

        if radius_limit <= 0.0:
            report.append("[R9] 半径输入为 0 mm，已跳过圆角审查。")

        unique_failed_faces = []
        failed_tags = set()
        for face in failed_faces:
            if face.Tag not in failed_tags:
                unique_failed_faces.append(face)
                failed_tags.add(face.Tag)
                if interactive:
                    self.highlight_face(face)

        result["failed_face_tags"] = [int(face.Tag) for face in unique_failed_faces]
        result["passed"] = (
            result["height_passed"]
            and result["side_face_count_passed"]
            and all(item["passed"] for item in result["side_faces"])
            and result["r4_passed"]
            and result["bottom_passed"]
            and not result["radius_failures"])
        report.append("审查完成：标红错误面 {0} 个。".format(len(unique_failed_faces)))
        if interactive:
            self.write_report(report)
        result["report"] = report
        return result

    def run(self):
        """运行批量审查，完成后保留错误面红色。"""
        completed = False
        try:
            self.clear_review_display()
            bodies = self.select_bodies()
            if not bodies:
                self.ui.NXMessageBox.Show(
                    "直顶头审查",
                    NXOpen.NXMessageBox.DialogType.Warning,
                    "请至少选择一个直顶头实体后再执行审查。")
                return
            for body in bodies:
                self.review_body(body, RADIUS_LIMIT)
            completed = True
        finally:
            if completed:
                self.commit_review_display()
            else:
                self.clear_review_display()

    def run_batch(self, part_path, result_path, radius_limit=0.0):
        """自动打开 PRT，审查其中所有实体并写出 JSON 结果。"""
        output = {
            "part_path": os.path.abspath(part_path),
            "radius_limit_mm": radius_limit,
            "nx_version": self.session.GetEnvironmentVariableValue("NX_FULL_VERSION"),
            "opened": False,
            "body_count": 0,
            "passed": False,
            "bodies": [],
            "error": None,
        }

        part_load_status = None
        try:
            base_part, part_load_status = self.session.Parts.OpenActiveDisplay(
                output["part_path"], NXOpen.DisplayPartOption.AllowAdditional)
            output["opened"] = base_part is not None
            work_part = self.session.Parts.Work
            if work_part is None:
                raise RuntimeError("PRT 已打开，但 NX 没有可用的工作部件。")

            bodies = list(work_part.Bodies)
            output["body_count"] = len(bodies)
            output["bodies"] = [
                self.review_body(body, radius_limit, interactive=False)
                for body in bodies
            ]
            output["passed"] = bool(bodies) and all(
                item["passed"] for item in output["bodies"])
        except Exception as ex:
            output["error"] = str(ex)
        finally:
            if part_load_status is not None:
                part_load_status.Dispose()
            result_directory = os.path.dirname(os.path.abspath(result_path))
            if result_directory and not os.path.isdir(result_directory):
                os.makedirs(result_directory)
            with open(result_path, "w", encoding="utf-8") as result_file:
                json.dump(output, result_file, ensure_ascii=False, indent=2)

        if output["error"]:
            raise RuntimeError(output["error"])
        return output


def main():
    reviewer = StraightLifterReviewer()
    if len(sys.argv) >= 3:
        radius_limit = float(sys.argv[3]) if len(sys.argv) >= 4 else RADIUS_LIMIT
        reviewer.run_batch(sys.argv[1], sys.argv[2], radius_limit)
    else:
        reviewer.run()


if __name__ == "__main__":
    main()
