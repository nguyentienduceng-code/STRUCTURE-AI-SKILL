#!/usr/bin/env python3
"""
Intent Classifier — Phân tích prompt người dùng và xác định Skill phù hợp nhất.

Usage:
    python intent_classifier.py --prompt "Tính cốt thép dầm B1 theo TCVN 5574"
    python intent_classifier.py --prompt "Review bản vẽ kết cấu tầng 5" --top 3
    python intent_classifier.py --prompt "Tính dầm rồi lập tờ trình" --verbose
    python intent_classifier.py --test  # Chạy 15 test cases

Output JSON:
    {
        "primary_skill": "Structural_Design_Engineer",
        "confidence": 0.95,
        "reasoning": "...",
        "all_matches": [...],
        "is_pipeline": false,
        "pipeline": null
    }
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import re
import os
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional


# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR = Path(__file__).parent
KEYWORD_DB_PATH = SCRIPT_DIR / "keyword_database.json"

# Scoring weights
PRIMARY_KEYWORD_WEIGHT = 10.0
SECONDARY_KEYWORD_WEIGHT = 5.0
REGEX_PATTERN_WEIGHT = 8.0
ANTI_KEYWORD_PENALTY = -15.0
SATURATION_SCORE = 15.0  # Ngưỡng bão hòa điểm số để chuẩn hóa confidence

# Thresholds
HIGH_CONFIDENCE = 0.85
MEDIUM_CONFIDENCE = 0.60
AMBIGUOUS_THRESHOLD = 0.15  # Nếu top-1 vs top-2 chênh < threshold → ambiguous
PIPELINE_DETECTION_THRESHOLD = 0.50  # Cả 2 skills đều > threshold → có thể là pipeline


# ============================================================================
# ============================================================================
# ENTITY EXTRACTOR (P1: SLOT FILLING)
# ============================================================================

class EntityExtractor:
    """Trích xuất thực thể kỹ thuật (kích thước, vật liệu, tải trọng, giả định) từ văn bản tự nhiên."""

    @staticmethod
    def extract(prompt: str, primary_skill: str = "") -> dict:
        prompt_lower = prompt.lower()
        geo = {}
        mat = {}
        loads = {}
        assumptions = []

        # 1. Hình học (Geometry)
        profile_match = re.search(r'\b([HIhi][1-9]\d{1,3})\s*[xX*×]\s*([1-9]\d{1,3})\b', prompt)
        if profile_match:
            prof_name = profile_match.group(1).upper()
            flange = int(profile_match.group(2))
            geo["profile"] = f"{prof_name}x{flange}"
            geo["h"] = int(prof_name[1:])
            geo["b"] = flange
        else:
            sec_match = re.search(r'\b([1-9]\d{1,3})\s*[xX*×]\s*([1-9]\d{1,3})\b', prompt)
            if sec_match:
                geo["b"] = int(sec_match.group(1))
                geo["h"] = int(sec_match.group(2))

        # Nhịp L
        span_match = re.search(r'(?:nhịp|span|l\s*=\s*)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:m\b|mét|m\s)', prompt_lower)
        if span_match:
            geo["L"] = float(span_match.group(1))

        # Chiều dày bản/sàn
        thick_match = re.search(r'(?:dày|chiều dày|bản dày)\s*([0-9]+(?:\.[0-9]+)?)\s*(mm|cm)?', prompt_lower)
        if thick_match:
            val = float(thick_match.group(1))
            unit = thick_match.group(2)
            if unit == 'cm':
                val = val * 10
            geo["thickness"] = val

        # Chiều sâu
        depth_match = re.search(r'(?:sâu|chiều sâu|hố đào sâu|chôn sâu)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:m|mét)?', prompt_lower)
        if depth_match:
            geo["depth"] = float(depth_match.group(1))

        # 2. Vật liệu (Materials)
        conc_match = re.search(r'\b(b15|b20|b22\.5|b25|b30|b35|b40|b45|b50|b60)\b', prompt_lower)
        if conc_match:
            mat["concrete"] = conc_match.group(1).upper()
        else:
            mark_match = re.search(r'(?:mác|m)\s*(200|250|300|350|400)\b', prompt_lower)
            if mark_match:
                m_num = mark_match.group(1)
                mark_map = {'200': 'B15', '250': 'B20', '300': 'B22.5', '350': 'B25', '400': 'B30'}
                mat["concrete"] = mark_map.get(m_num, 'B25')
                assumptions.append(f"Quy đổi mác M{m_num} → cấp bền {mat['concrete']} (TCVN 5574:2018)")

        rebar_match = re.search(r'\b(cb240-t|cb300-v|cb400-v|cb500-v|cb240|cb300|cb400|cb500)\b', prompt_lower)
        if rebar_match:
            r_val = rebar_match.group(1).upper()
            if '-' not in r_val:
                r_val += '-V' if r_val != 'CB240' else '-T'
            mat["rebar"] = r_val

        steel_match = re.search(r'\b(ss400|q235|q345|q355|sm490|a36|a572)\b', prompt_lower)
        if steel_match:
            mat["steel_grade"] = steel_match.group(1).upper()

        # 3. Nội lực & Tải trọng (Loads)
        m_match = re.search(r'(?:momen|mô men|m\s*=|m_ed\s*=|chịu momen\s*|chịu mô men\s*)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:knm|kn\.m|t\.m)?', prompt_lower)
        if m_match:
            loads["M"] = float(m_match.group(1))

        v_match = re.search(r'(?:lực cắt|cắt|v\s*=|v_ed\s*=|q\s*=|chịu cắt\s*)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:kn|tấn)?', prompt_lower)
        if v_match:
            loads["V"] = float(v_match.group(1))

        n_match = re.search(r'(?:lực dọc|nén|kéo|n\s*=|n_ed\s*=|chịu nén\s*)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:kn|tấn)?', prompt_lower)
        if n_match:
            loads["N"] = float(n_match.group(1))

        q_match = re.search(r'(?:tải rải đều|tải trọng|q\s*=)\s*([0-9]+(?:\.[0-9]+)?)\s*(?:kn/m2|kn/m²|dan/m2)?', prompt_lower)
        if q_match:
            loads["q"] = float(q_match.group(1))

        # 4. Standard Engineering Assumptions
        if "dầm" in prompt_lower or primary_skill == "Structural_Design_Engineer":
            if not mat.get("concrete"):
                assumptions.append("Cấp bền bê tông B25 (ASSUMED)")
            if not mat.get("rebar") and not mat.get("steel_grade"):
                assumptions.append("Cốt thép dọc CB400-V (ASSUMED)")
            if geo.get("b") and geo.get("h"):
                assumptions.append("Lớp bảo vệ cốt thép a = 35mm (ASSUMED)")
        elif "cột" in prompt_lower:
            if not mat.get("concrete"):
                assumptions.append("Cấp bền bê tông B25 (ASSUMED)")
            if not mat.get("rebar"):
                assumptions.append("Cốt thép dọc CB400-V (ASSUMED)")
            if geo.get("b") and geo.get("h"):
                assumptions.append("Lớp bảo vệ cốt thép a = 40mm (ASSUMED)")
        elif "sàn" in prompt_lower or primary_skill == "SKILL_TEMPWORKS":
            if not mat.get("concrete"):
                assumptions.append("Cấp bền bê tông B25 (ASSUMED)")
            if geo.get("thickness"):
                assumptions.append("Lớp bảo vệ cốt thép a = 20mm (ASSUMED)")

        return {
            "geometry": geo,
            "materials": mat,
            "loads": loads,
            "assumptions": assumptions
        }


# ============================================================================
# CORE CLASSIFIER
# ============================================================================

class IntentClassifier:
    """Phân loại intent từ prompt người dùng → Skill phù hợp."""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(KEYWORD_DB_PATH)
        self.db = self._load_database()
        self.skills = self.db["skills"]
        self.tie_breakers = self.db.get("tie_breakers", {}).get("rules", [])
        self.pipeline_templates = self.db.get("pipeline_templates", {})

    def _load_database(self) -> dict:
        """Load keyword database từ JSON."""
        with open(self.db_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def classify(self, prompt: str, top_n: int = 3, verbose: bool = False) -> dict:
        """
        Phân loại prompt → skill(s).

        Returns:
            {
                "primary_skill": str,
                "primary_skill_id": str,
                "confidence": float,
                "confidence_level": "HIGH" | "MEDIUM" | "LOW",
                "reasoning": str,
                "all_matches": [...],
                "is_pipeline": bool,
                "pipeline": {...} | null,
                "matched_keywords": [...],
                "suggestions": str
            }
        """
        prompt_lower = prompt.lower().strip()

        # Step 1: Score mỗi skill
        scores = {}
        match_details = {}
        for skill_name, skill_data in self.skills.items():
            score, details = self._score_skill(prompt_lower, skill_name, skill_data)
            scores[skill_name] = score
            match_details[skill_name] = details

        # Step 2: Normalize scores với SATURATION_SCORE
        max_score = max(scores.values()) if scores else 0
        norm_denom = max(max_score, SATURATION_SCORE)
        if norm_denom == 0:
            norm_denom = 1.0
        normalized = {k: min(1.0, v / norm_denom) for k, v in scores.items()}

        # Step 3: Sort by score descending
        ranked = sorted(normalized.items(), key=lambda x: x[1], reverse=True)

        # Step 4: Check for pipeline (multi-intent)
        pipeline_result = self._detect_pipeline(prompt_lower, ranked, match_details)
        if pipeline_result and pipeline_result.get("skills"):
            lead_skill = pipeline_result["skills"][0]
            # Ensure lead skill of pipeline is ranked #1
            ranked = [(lead_skill, 1.0)] + [(k, v) for k, v in ranked if k != lead_skill]

        # Step 5: Apply tie-breakers
        # TB-05: Technical_Illustrator is never primary when calculation context exists
        has_calc_intent = bool(re.search(r'\b(tính|thiết kế|thẩm tra|kiểm tra|review|đánh giá)\b', prompt_lower))
        if has_calc_intent and ranked and ranked[0][0] == "Technical_Illustrator":
            calc_skills = ["Structural_Design_Engineer", "Design_Evaluation", "SKILL_GEOTECH"]
            for calc_skill in calc_skills:
                matches = match_details.get(calc_skill, {}).get("matched", [])
                if any("[PRIMARY]" in m or "[REGEX]" in m for m in matches):
                    ranked = [(calc_skill, 1.0)] + [(k, v) for k, v in ranked if k != calc_skill]
                    if not pipeline_result:
                        pipeline_result = {
                            "template": "auto_detected",
                            "skills": [calc_skill, "Technical_Illustrator"],
                            "description": f"Auto-detected pipeline: {calc_skill} → Technical_Illustrator",
                            "trigger": "TI calculation context override (TB-05)"
                        }
                    break

        if not pipeline_result and len(ranked) >= 2 and (ranked[0][1] - ranked[1][1]) < AMBIGUOUS_THRESHOLD:
            winner = self._apply_tie_breakers(prompt_lower, ranked, match_details)
            if winner:
                # Re-rank with winner on top
                ranked = [(winner, 1.0)] + [(k, v) for k, v in ranked if k != winner]

        # Step 6: Build result
        primary = ranked[0] if ranked else (None, 0.0)
        confidence = primary[1]
        confidence_level = (
            "HIGH" if confidence >= HIGH_CONFIDENCE
            else "MEDIUM" if confidence >= MEDIUM_CONFIDENCE
            else "LOW"
        )

        # Build all_matches (top N)
        all_matches = []
        for skill_name, score in ranked[:top_n]:
            skill_data = self.skills.get(skill_name, {})
            all_matches.append({
                "skill": skill_name,
                "skill_id": skill_data.get("skill_id", ""),
                "display_name": skill_data.get("display_name", skill_name),
                "confidence": round(score, 3),
                "entry_points": skill_data.get("entry_points", []),
                "matched_keywords": match_details.get(skill_name, {}).get("matched", []),
                "is_placeholder": skill_data.get("is_placeholder", False)
            })

        # Build reasoning
        reasoning = self._build_reasoning(primary[0], confidence, match_details, pipeline_result)

        # Build suggestions
        suggestions = self._build_suggestions(primary[0], confidence_level, pipeline_result)

        # Step 7: Entity extraction (P1: Slot Filling)
        extracted_entities = EntityExtractor.extract(prompt, primary_skill=primary[0] or "")

        result = {
            "prompt": prompt,
            "primary_skill": primary[0],
            "primary_skill_id": self.skills.get(primary[0], {}).get("skill_id", ""),
            "confidence": round(confidence, 3),
            "confidence_level": confidence_level,
            "reasoning": reasoning,
            "all_matches": all_matches,
            "is_pipeline": pipeline_result is not None,
            "pipeline": pipeline_result,
            "extracted_entities": extracted_entities,
            "suggestions": suggestions
        }

        if verbose:
            result["debug"] = {
                "raw_scores": {k: round(v, 2) for k, v in scores.items()},
                "normalized_scores": {k: round(v, 3) for k, v in normalized.items()},
                "match_details": {k: v for k, v in match_details.items() if v.get("matched")}
            }

        return result

    def _score_skill(self, prompt: str, skill_name: str, skill_data: dict) -> Tuple[float, dict]:
        """Tính điểm cho 1 skill dựa trên prompt."""
        score = 0.0
        details = {"matched": [], "anti_matched": [], "regex_matched": []}

        # Check primary keywords
        for kw in skill_data.get("primary_keywords", []):
            if kw.lower() in prompt:
                score += PRIMARY_KEYWORD_WEIGHT
                details["matched"].append(f"[PRIMARY] {kw}")

        # Check secondary keywords
        for kw in skill_data.get("secondary_keywords", []):
            if kw.lower() in prompt:
                score += SECONDARY_KEYWORD_WEIGHT
                details["matched"].append(f"[SECONDARY] {kw}")

        # Check regex patterns
        for pattern in skill_data.get("regex_patterns", []):
            try:
                if re.search(pattern, prompt, re.IGNORECASE):
                    score += REGEX_PATTERN_WEIGHT
                    details["regex_matched"].append(pattern)
                    details["matched"].append(f"[REGEX] {pattern}")
            except re.error:
                pass  # Skip invalid regex

        # Apply anti-keyword penalty only if not in a multi-step sequence
        has_transition = bool(re.search(r'\b(rồi|sau đó|tiếp theo|xong|xong rồi|sau đấy)\b', prompt))
        if not has_transition:
            for kw in skill_data.get("anti_keywords", []):
                if kw.lower() in prompt:
                    score += ANTI_KEYWORD_PENALTY
                    details["anti_matched"].append(kw)

        return max(score, 0.0), details

    def _detect_pipeline(self, prompt: str, ranked: list, match_details: dict) -> Optional[dict]:
        """Phát hiện multi-intent → pipeline."""

        # Check pipeline templates first
        for template_name, template in self.pipeline_templates.items():
            for trigger in template.get("trigger_keywords", []):
                matched = False
                if trigger.lower() in prompt:
                    matched = True
                elif any(c in trigger for c in '.*+?[]()'):
                    try:
                        if re.search(trigger, prompt, re.IGNORECASE):
                            matched = True
                    except re.error:
                        pass

                if matched:
                    return {
                        "template": template_name,
                        "skills": template["skills"],
                        "description": template["description"],
                        "trigger": trigger
                    }

        # Check if 2+ skills have high scores
        if len(ranked) >= 2:
            top1_name, top1_score = ranked[0]
            top2_name, top2_score = ranked[1]

            if top1_score >= PIPELINE_DETECTION_THRESHOLD and top2_score >= PIPELINE_DETECTION_THRESHOLD:
                # Both are significant — check if they're complementary
                top1_matches = len(match_details.get(top1_name, {}).get("matched", []))
                top2_matches = len(match_details.get(top2_name, {}).get("matched", []))

                if top1_matches >= 2 and top2_matches >= 2:
                    # Determine order
                    order = self._determine_pipeline_order(top1_name, top2_name)
                    return {
                        "template": "auto_detected",
                        "skills": order,
                        "description": f"Auto-detected pipeline: {' → '.join(order)}",
                        "trigger": "multi-intent detection"
                    }

        return None

    def _determine_pipeline_order(self, skill_a: str, skill_b: str) -> list:
        """Xác định thứ tự pipeline."""
        # Design rules: SDE → DE, GEO → SDE, * → VERIFY, * → Cost
        order_priority = {
            "SKILL_GEOTECH": 1,
            "Structural_Design_Engineer": 2,
            "Design_Evaluation": 3,
            "SKILL_PHULUC": 4,
            "SKILL_VERIFY": 5,
            "Cost_Estimator": 6,
            "Technical_Illustrator": 7,
            "SKILL_RFI": 8,
            "SKILL_FORENSIC": 2  # Same level as SDE
        }

        prio_a = order_priority.get(skill_a, 99)
        prio_b = order_priority.get(skill_b, 99)

        if prio_a <= prio_b:
            return [skill_a, skill_b]
        else:
            return [skill_b, skill_a]

    def _apply_tie_breakers(self, prompt: str, ranked: list, match_details: dict) -> Optional[str]:
        """Áp dụng tie-breaker rules khi 2 skills gần bằng điểm."""
        top1_name = ranked[0][0]
        top2_name = ranked[1][0]

        # TB-04: GEOTECH always wins
        if "SKILL_GEOTECH" in (top1_name, top2_name):
            geo_details = match_details.get("SKILL_GEOTECH", {})
            if len(geo_details.get("matched", [])) >= 1:
                return "SKILL_GEOTECH"

        # TB-06: TEMPWORKS always wins for formwork/shoring
        if "SKILL_TEMPWORKS" in (top1_name, top2_name):
            tw_details = match_details.get("SKILL_TEMPWORKS", {})
            if len(tw_details.get("matched", [])) >= 1:
                return "SKILL_TEMPWORKS"

        # TB-01, TB-02 & TB-03: SDE vs DE
        sde_details = match_details.get("Structural_Design_Engineer", {})
        de_details = match_details.get("Design_Evaluation", {})
        sde_has_primary = any("[PRIMARY]" in m for m in sde_details.get("matched", []))
        de_has_primary = any("[PRIMARY]" in m for m in de_details.get("matched", []))

        # TB-03: Cả SDE và DE đều có primary keywords (vd: "tính lại dầm rồi lập tờ trình")
        # Theo AGENTS.md §0.2 Tie-breaker (3): Structural_Design_Engineer tính toán trước
        if sde_has_primary and de_has_primary:
            return "Structural_Design_Engineer"
        if sde_has_primary and not de_has_primary:
            return "Structural_Design_Engineer"
        if de_has_primary and not sde_has_primary:
            return "Design_Evaluation"

        # TB-05: TI is never primary when calculation context exists
        if "Technical_Illustrator" in (top1_name, top2_name):
            other = top2_name if top1_name == "Technical_Illustrator" else top1_name
            if other in ("Structural_Design_Engineer", "Design_Evaluation", "SKILL_GEOTECH"):
                return other

        return None

    def _build_reasoning(self, primary: str, confidence: float,
                         match_details: dict, pipeline: Optional[dict]) -> str:
        """Xây dựng giải thích cho kết quả."""
        if not primary:
            return "Không tìm thấy skill phù hợp. Vui lòng mô tả chi tiết hơn."

        details = match_details.get(primary, {})
        matched = details.get("matched", [])

        parts = [f"Chọn **{primary}**"]

        if matched:
            kw_list = [m.split("] ")[1] for m in matched[:5] if "] " in m]
            parts.append(f"vì khớp với: {', '.join(kw_list)}")

        if confidence >= HIGH_CONFIDENCE:
            parts.append("(Độ tin cậy CAO)")
        elif confidence >= MEDIUM_CONFIDENCE:
            parts.append("(Độ tin cậy TRUNG BÌNH — có thể cần xác nhận)")
        else:
            parts.append("(Độ tin cậy THẤP — nên hỏi lại User)")

        if pipeline:
            parts.append(f"\n→ Pipeline phát hiện: {' → '.join(pipeline['skills'])}")

        return " ".join(parts)

    def _build_suggestions(self, primary: str, confidence_level: str,
                           pipeline: Optional[dict]) -> str:
        """Đề xuất hành động tiếp theo."""
        if confidence_level == "LOW":
            return "HỎI User: 'Anh/chị muốn tôi [tính toán thiết kế] hay [review thẩm tra] kết cấu này?'"
        elif confidence_level == "MEDIUM":
            return f"XÁC NHẬN: 'Tôi sẽ dùng {primary} để xử lý yêu cầu này. Anh/chị đồng ý không?'"
        elif pipeline:
            skills = " → ".join(pipeline["skills"])
            return f"CHẠY PIPELINE: {skills}"
        else:
            return f"TIẾN HÀNH: Đọc SKILL.md của {primary} và thực thi."


# ============================================================================
# TEST CASES
# ============================================================================

TEST_CASES = [
    # Format: (prompt, expected_skill, expected_is_pipeline)
    ("Tính cốt thép dầm B1 theo TCVN 5574", "Structural_Design_Engineer", False),
    ("Review bản vẽ kết cấu tầng 5", "Design_Evaluation", False),
    ("Vẽ mặt cắt dầm H400x200", "Technical_Illustrator", False),
    ("So sánh chi phí BTCT vs thép cho nhà xưởng", "Cost_Estimator", False),
    ("Điều tra nguyên nhân nứt dầm tầng 3", "SKILL_FORENSIC", False),
    ("Cross-check kết quả với ETABS", "SKILL_VERIFY", False),
    ("Tạo RFI cho nhà thầu về thiếu bản vẽ", "SKILL_RFI", False),
    ("Phân tích SPT và tính thông số Plaxis", "SKILL_GEOTECH", False),
    ("Lập phụ lục tính toán chi tiết cho thẩm tra", "SKILL_PHULUC", False),
    ("Tính dầm thép rồi lập tờ trình trình duyệt", "Structural_Design_Engineer", True),
    ("Thuyết minh tính toán liên kết bu lông", "Structural_Design_Engineer", False),
    ("Thẩm tra hồ sơ thiết kế giai đoạn BVTC", "Design_Evaluation", False),
    ("Tính cốt thép dầm rồi vẽ mặt cắt", "Structural_Design_Engineer", True),
    ("Bóc tách khối lượng và xuất dự toán", "Design_Evaluation", False),
    ("Tính toán tường vây EA EI cho hố đào sâu", "SKILL_GEOTECH", False),
    ("Thiết kế cốp pha sàn dày 200mm nhịp 5m", "SKILL_TEMPWORKS", False),
    ("Tính sàn rồi tính cốp pha", "Structural_Design_Engineer", True),
]


def run_tests(classifier: IntentClassifier) -> dict:
    """Chạy test cases và báo cáo kết quả."""
    results = {"passed": 0, "failed": 0, "total": len(TEST_CASES), "details": []}

    for i, (prompt, expected_skill, expected_pipeline) in enumerate(TEST_CASES, 1):
        result = classifier.classify(prompt)
        skill_match = result["primary_skill"] == expected_skill
        pipeline_match = result["is_pipeline"] == expected_pipeline

        passed = skill_match  # Pipeline is bonus check
        status = "✅ PASS" if passed else "❌ FAIL"

        detail = {
            "test_id": i,
            "prompt": prompt,
            "expected": expected_skill,
            "got": result["primary_skill"],
            "confidence": result["confidence"],
            "skill_match": skill_match,
            "pipeline_match": pipeline_match,
            "status": "PASS" if passed else "FAIL"
        }
        results["details"].append(detail)

        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1

        print(f"  {status}  [{i:02d}] {prompt[:50]:50s} → {result['primary_skill']:35s} (conf={result['confidence']:.2f})"
              + (f"  [EXPECTED: {expected_skill}]" if not passed else ""))

    results["pass_rate"] = round(results["passed"] / results["total"] * 100, 1)
    return results


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Intent Classifier — Phân tích prompt → Skill phù hợp",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python intent_classifier.py --prompt "Tính cốt thép dầm B1"
  python intent_classifier.py --prompt "Review bản vẽ tầng 5" --top 3 --verbose
  python intent_classifier.py --test
        """
    )
    parser.add_argument("--prompt", type=str, help="Prompt cần phân loại")
    parser.add_argument("--top", type=int, default=3, help="Số lượng kết quả trả về (default: 3)")
    parser.add_argument("--verbose", action="store_true", help="Hiển thị debug info")
    parser.add_argument("--test", action="store_true", help="Chạy 15 test cases")
    parser.add_argument("--db", type=str, default=None, help="Đường dẫn keyword_database.json (mặc định: cùng thư mục)")

    args = parser.parse_args()

    # Init classifier
    classifier = IntentClassifier(db_path=args.db)

    if args.test:
        print("=" * 100)
        print("  INTENT CLASSIFIER — TEST SUITE")
        print("=" * 100)
        results = run_tests(classifier)
        print("-" * 100)
        print(f"  RESULT: {results['passed']}/{results['total']} passed ({results['pass_rate']}%%)")
        print("=" * 100)

        # Output JSON
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    if not args.prompt:
        parser.print_help()
        sys.exit(1)

    result = classifier.classify(args.prompt, top_n=args.top, verbose=args.verbose)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
