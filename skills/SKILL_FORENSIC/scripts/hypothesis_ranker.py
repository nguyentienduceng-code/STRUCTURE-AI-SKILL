#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKILL_FORENSIC Bước 5: Hypothesis Ranker
Xếp hạng các giả thuyết nguyên nhân theo xác suất dựa trên:
- Bằng chứng thu thập được
- Tính nhất quán với các triệu chứng quan sát được
- Mâu thuẫn với giả thuyết khác

Input: Danh sách hypotheses (mỗi hypothesis có evidence + contradictions)
Output: Ranking với probability scores
"""

import sys
import json
import argparse
from datetime import datetime


# Thư viện failure mode (tham chiếu failure_modes_database.json nếu có)
FAILURE_MODE_LIBRARY = {
    "flexural_crack": {
        "label": "Phá hoại uốn",
        "signature_crack": "vuông góc trục, giữa nhịp, mở rộng từ dưới lên",
        "main_causes": ["quá tải uốn", "thiếu cốt thép kéo", "bê tông mác thấp"]
    },
    "shear_crack": {
        "label": "Phá hoại cắt",
        "signature_crack": "chéo 45° gần gối, dài",
        "main_causes": ["quá tải cắt", "thiếu cốt đai", "bê tông cường độ thấp"]
    },
    "punching": {
        "label": "Phá hoại đục thủng",
        "signature_crack": "hình nón 45° quanh cột, xuyên qua bản",
        "main_causes": ["tải tập trung lớn", "bản mỏng", "thiếu cốt thép đặc biệt"]
    },
    "settlement": {
        "label": "Lún lệch",
        "signature_crack": "chéo 45° trên tường, vết nứt cửa sổ",
        "main_causes": ["nền đất yếu", "móng không đủ sâu", "mực nước ngầm thay đổi"]
    },
    "corrosion": {
        "label": "Ăn mòn cốt thép",
        "signature_crack": "bong tróc bê tông, vết rỉ",
        "main_causes": ["chloride xâm nhập", "carbonation", "cover không đủ"]
    }
}


def score_hypothesis(hypothesis, observed_symptoms, mode_library=None):
    """
    Tính điểm xác suất cho 1 giả thuyết.

    Args:
        hypothesis: {
            "cause": "Quá tải do chất hàng vượt thiết kế",
            "evidence": ["Back-calculation cho q = 28.5 kN/m", ...],
            "contradictions": ["..."]
        }
        observed_symptoms: {
            "crack_type": "flexural_crack",
            "crack_location": "midspan",
            "crack_width_mm": 2.0,
            ...
        }
    """
    if mode_library is None:
        mode_library = FAILURE_MODE_LIBRARY

    score = 50  # Base score
    matched_evidence = 0

    # Trừ điểm cho mỗi mâu thuẫn
    for contra in hypothesis.get("contradictions", []):
        if contra and len(contra) > 5:  # Mâu thuẫn có nội dung
            score -= 15

    # Cộng điểm cho mỗi bằng chứng có dấu hiệu đo lường cụ thể
    for ev in hypothesis.get("evidence", []):
        ev_lower = ev.lower() if isinstance(ev, str) else ""
        if any(kw in ev_lower for kw in ["mm", "kpa", "kn/m", "kn.m", "mpa", "%", "fck", "fy"]):
            # Có số liệu đo → bằng chứng mạnh
            score += 12
            matched_evidence += 1
        elif "nhân chứng" in ev_lower or "nhật ký" in ev_lower or "bản vẽ" in ev_lower:
            # Có nguồn tài liệu
            score += 8
            matched_evidence += 1
        else:
            score += 4

    # Match crack type với failure mode
    crack_type = observed_symptoms.get("crack_type", "")
    if crack_type and mode_library.get(crack_type):
        # Kiểm tra cause có liên quan đến main_causes của mode
        cause = hypothesis.get("cause", "").lower()
        for mc in mode_library[crack_type].get("main_causes", []):
            if mc.lower() in cause or any(kw in cause for kw in mc.lower().split()):
                score += 10
                break

    # Giới hạn 5-99%
    probability = max(5, min(99, score))

    return {
        "cause": hypothesis.get("cause"),
        "probability_pct": probability,
        "matched_evidence_count": matched_evidence,
        "evidence_count": len(hypothesis.get("evidence", [])),
        "contradiction_count": len(hypothesis.get("contradictions", [])),
        "rank_label": "MAIN" if probability >= 70 else "CONTRIBUTING" if probability >= 40 else "EXCLUDED"
    }


def rank_hypotheses(hypotheses, observed_symptoms):
    """
    Xếp hạng toàn bộ giả thuyết.
    """
    if not hypotheses:
        return {
            "Status": "NO_HYPOTHESES",
            "Recommendation": "Phải có tối thiểu 3 giả thuyết (theo Rule 2 của SKILL_FORENSIC)"
        }

    if len(hypotheses) < 3:
        return {
            "Status": "TOO_FEW_HYPOTHESES",
            "Count": len(hypotheses),
            "Recommendation": f"Chỉ có {len(hypotheses)} giả thuyết. Bổ sung thêm (yêu cầu tối thiểu 3)"
        }

    ranked = []
    for hyp in hypotheses:
        scored = score_hypothesis(hyp, observed_symptoms)
        ranked.append(scored)

    # Sort by probability DESC
    ranked.sort(key=lambda x: x["probability_pct"], reverse=True)

    # Add rank number
    for idx, item in enumerate(ranked, start=1):
        item["rank"] = idx

    # Identify most likely scenario
    main = [h for h in ranked if h["rank_label"] == "MAIN"]
    contributing = [h for h in ranked if h["rank_label"] == "CONTRIBUTING"]

    if main:
        scenario = f"Nguyên nhân chính: {main[0]['cause']} (xác suất {main[0]['probability_pct']}%)"
        if contributing:
            scenario += f". Có thể kết hợp với: {', '.join(h['cause'] for h in contributing[:2])}"
    else:
        scenario = "Không có giả thuyết nào đạt >70%. Cần thu thập thêm bằng chứng."

    return {
        "Ranking_ID": f"HR-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "Generated_At": datetime.now().isoformat(),
        "Observed_Symptoms": observed_symptoms,
        "Total_Hypotheses": len(hypotheses),
        "Ranked_Hypotheses": ranked,
        "Most_Likely_Scenario": scenario,
        "Main_Cause": main[0] if main else None,
        "Contributing_Causes": contributing,
        "Disclaimer": (
            "Xếp hạng dựa trên bằng chứng hiện có. Xác suất có thể thay đổi khi có thêm dữ liệu. "
            "Cần Hội đồng Giám định độc lập xác nhận nguyên nhân cuối cùng."
        )
    }


def main():
    parser = argparse.ArgumentParser(description="Hypothesis Ranker")
    parser.add_argument("--hypotheses", required=True, help="JSON file chứa list of hypotheses")
    parser.add_argument("--symptoms", help="JSON file chứa observed symptoms (optional)")
    parser.add_argument("--output", help="File JSON output")

    args = parser.parse_args()

    with open(args.hypotheses, 'r', encoding='utf-8') as f:
        hypotheses = json.load(f)

    symptoms = {}
    if args.symptoms:
        with open(args.symptoms, 'r', encoding='utf-8') as f:
            symptoms = json.load(f)

    result = rank_hypotheses(hypotheses, symptoms)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
