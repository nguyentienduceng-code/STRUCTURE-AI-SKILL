import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import re

class AudienceDetector:
    def __init__(self):
        self.keywords = {
            "Chủ đầu tư (Investor)": ["chủ đầu tư", "ban lãnh đạo", "chi phí", "tiến độ", "rủi ro tài chính", "ngắn gọn", "tổng quan"],
            "Tư vấn thiết kế (Consultant)": ["tư vấn", "thiết kế", "công thức", "điều khoản", "số liệu", "calculation", "chi tiết"],
            "Nhà thầu thi công (Contractor)": ["nhà thầu", "biện pháp thi công", "constructability", "ncr", "rfi", "thực tế"],
            "Cơ quan thẩm tra (Authority)": ["thẩm tra", "nhà nước", "compliance", "điều", "tcvn", "pháp lý", "nghiệm thu"]
        }

    def detect(self, user_query, context=""):
        """Phát hiện đối tượng đọc từ query và context"""
        combined_text = (user_query + " " + context).lower()

        scores = {}
        for audience, keywords in self.keywords.items():
            scores[audience] = sum(1 for kw in keywords if kw in combined_text)

        if max(scores.values()) > 0:
            detected = max(scores, key=scores.get)
            confidence = scores[detected] / sum(scores.values())
        else:
            detected = "Tư vấn thiết kế (Consultant)" # Default fallback
            confidence = 0.5

        return {
            "audience": detected,
            "confidence": f"{confidence:.1%}",
            "scores": scores
        }

if __name__ == "__main__":
    import sys
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "làm báo cáo tóm tắt cho chủ đầu tư xem về chi phí"
    detector = AudienceDetector()
    result = detector.detect(query)
    print(f"🔍 Input: '{query}'")
    print(f"🎯 Đối tượng phát hiện: {result['audience']} (Độ tin cậy: {result['confidence']})")
