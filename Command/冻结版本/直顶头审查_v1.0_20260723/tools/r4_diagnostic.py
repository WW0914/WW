# -*- coding: utf-8 -*-
import json
import math
import sys

import NXOpen
import NXOpen.UF


def angle_to_z(normal_z):
    return math.degrees(math.asin(max(-1.0, min(1.0, abs(normal_z)))))


def normalize_xy(x, y):
    length = math.hypot(x, y)
    if length <= 1.0e-12:
        return 0.0, 0.0
    return x / length, y / length


def main():
    part_path = sys.argv[1]
    result_path = sys.argv[2]
    session = NXOpen.Session.GetSession()
    ufs = NXOpen.UF.UFSession.GetUFSession()
    base_part, status = session.Parts.OpenActiveDisplay(
        part_path, NXOpen.DisplayPartOption.AllowAdditional)
    try:
        part = session.Parts.Work
        output = {"part": part_path, "bodies": []}
        for body in list(part.Bodies):
            faces = list(body.GetFaces())
            data = [(face, ufs.Modeling.AskFaceData(face.Tag)) for face in faces]
            planar = []
            all_boxes = [item[1][3] for item in data]
            center_x = (min(box[0] for box in all_boxes) + max(box[3] for box in all_boxes)) * 0.5
            center_y = (min(box[1] for box in all_boxes) + max(box[4] for box in all_boxes)) * 0.5

            for face, face_data in data:
                face_type, point, direction, box, radius, rad_data, normal_dir = face_data
                angle = angle_to_z(direction[2])
                if face_type == 22 and angle <= 30.0:
                    horizontal_x, horizontal_y = normalize_xy(direction[0], direction[1])
                    face_center_x = (box[0] + box[3]) * 0.5
                    face_center_y = (box[1] + box[4]) * 0.5
                    outward_x, outward_y = normalize_xy(face_center_x - center_x, face_center_y - center_y)
                    outward_alignment = horizontal_x * outward_x + horizontal_y * outward_y
                    oriented_normal_z = direction[2] if outward_alignment >= 0.0 else -direction[2]
                    # 对隐式平面 n·p=d，沿 +Z 时横向外移符号由 -n_z / |n_xy| 决定。
                    draft_expansion = -oriented_normal_z / max(math.hypot(direction[0], direction[1]), 1.0e-12)
                    planar.append({
                        "face_tag": int(face.Tag),
                        "angle_deg": angle,
                        "direction": [direction[0], direction[1], direction[2]],
                        "normal_dir": int(normal_dir),
                        "outward_alignment": outward_alignment,
                        "oriented_normal_z": oriented_normal_z,
                        "draft_expansion_per_z": draft_expansion,
                        "expands_outward_toward_positive_z": draft_expansion > 1.0e-8,
                    })
            output["bodies"].append({
                "body_tag": int(body.Tag),
                "side_face_count": len(planar),
                "side_faces": planar,
                "r4_passed": len(planar) == 4 and all(item["expands_outward_toward_positive_z"] for item in planar),
            })
        with open(result_path, "w", encoding="utf-8") as stream:
            json.dump(output, stream, ensure_ascii=False, indent=2)
    finally:
        status.Dispose()


if __name__ == "__main__":
    main()