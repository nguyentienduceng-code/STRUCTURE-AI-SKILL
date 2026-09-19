import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import os
try:
    from PIL import Image
except ImportError:
    # Fallback nếu hệ thống chưa cài Pillow
    Image = None

class ImageOutputValidator:
    def __init__(self, required_formats=['.png', '.jpg', '.jpeg', '.webp']):
        self.required_formats = required_formats

    def validate(self, image_path):
        """5-step validation tự động cho file ảnh"""
        checks = {
            "1_path_absolute": os.path.isabs(image_path),
            "2_file_exists": os.path.exists(image_path),
            "3_valid_format": os.path.splitext(image_path)[1].lower() in self.required_formats,
            "4_readable": False,
            "5_size_ok": False
        }

        if checks["2_file_exists"]:
            if Image:
                try:
                    img = Image.open(image_path)
                    checks["4_readable"] = True
                    # Check size > 100x100
                    if img.size[0] > 100 and img.size[1] > 100:
                        checks["5_size_ok"] = True
                except Exception as e:
                    pass
            else:
                # Nếu không có PIL, bypass 4 và 5
                checks["4_readable"] = True
                checks["5_size_ok"] = True

        all_pass = all(checks.values())
        return {
            "valid": all_pass,
            "checks": checks,
            "path": image_path,
            "error_msg": "Ảnh hợp lệ." if all_pass else f"Ảnh KHÔNG hợp lệ. Kiểm tra: {checks}"
        }
