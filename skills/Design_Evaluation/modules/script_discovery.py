import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import json
import os

class ScriptDiscovery:
    def __init__(self, registry_path=None):
        if registry_path is None:
            # __file__ = <skills>/Design_Evaluation/modules/script_discovery.py
            # -> di len 2 cap de ve thu muc <skills>, roi sang Technical_Illustrator
            current_dir = os.path.dirname(os.path.abspath(__file__))          # .../modules
            skill_dir = os.path.dirname(current_dir)                          # .../Design_Evaluation
            skills_root = os.path.dirname(skill_dir)                          # .../skills
            registry_path = os.path.join(skills_root, "Technical_Illustrator",
                                         "scripts", "registry.json")

        if not os.path.isfile(registry_path):
            raise FileNotFoundError(
                f"Khong tim thay registry cua Technical_Illustrator tai: {registry_path}\n"
                f"Kiem tra lai cau truc thu muc .agents/skills/."
            )

        with open(registry_path, encoding='utf-8') as f:
            self.registry = json.load(f)
        self.registry_path = registry_path

    def find_script(self, keywords, input_data=None):
        """Tìm script phù hợp dựa trên keywords và input data"""
        if isinstance(keywords, str):
            keywords = [k.strip().lower() for k in keywords.split(',')]
        else:
            keywords = [k.lower() for k in keywords]
            
        candidates = []

        for script in self.registry.get("scripts", []):
            score = 0

            # Match tags
            for tag in script.get("tags", []):
                tag_lower = tag.lower()
                if any(kw in tag_lower for kw in keywords):
                    score += 2

            # Match description
            desc_lower = script.get("description", "").lower()
            if any(kw in desc_lower for kw in keywords):
                score += 1

            # Check input compatibility
            if input_data:
                required_inputs = set(script.get("input_schema", {}).keys())
                provided_inputs = set(input_data.keys())
                if required_inputs.issubset(provided_inputs):
                    score += 3

            if score > 0:
                candidates.append((script["name"], score, script["description"]))

        # Trả về top 3 candidates
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:3]

if __name__ == "__main__":
    # Test
    discovery = ScriptDiscovery()
    import sys
    args = sys.argv[1:]
    if args:
        print(f"🔍 Đang tìm script cho từ khóa: {args}")
        results = discovery.find_script(args)
        for name, score, desc in results:
            print(f"⭐ Score {score}: {name} - {desc}")
    else:
        print("Vui lòng truyền từ khóa. VD: python script_discovery.py dầm thép")
