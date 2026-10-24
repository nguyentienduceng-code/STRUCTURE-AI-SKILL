"""
dce_rules_registry.py — DCE Pro Engineering Rules Registry
===========================================================
Sprint 3 · Phase 3 · Nhiệm vụ 1

Mục đích:
    Gom toàn bộ 1.239 file cấu hình và cơ sở tri thức kỹ thuật của DCE Pro
    từ các thư mục C:\\Dce Pro\\System\\, SystemSteel\\, SystemRvt\\,
    AddinSteelCad\\SystemSteel\\ cùng với PowerShell Reflection từ assembly
    DbimSteelAutocad.dll và Form 2.dxf thành một nguồn chân lý (Single Source of Truth):
    `.agents/_SHARED/data/dce_engineering_rules.json`.

Cấu trúc Registry:
    1. rc_detailing_rules      : Quy tắc cấu tạo BTCT (bảo vệ, nối thép 40d, so le, khoảng cách, coupler...)
    2. viewport_packing_rules  : Quy tắc đóng gói khung tên, tỷ lệ, chia khung model, padding...
    3. steel_sections_catalog  : Danh mục thép hình I, U, V, Pipe, Box, Plate kèm Im0, Um0...
    4. steel_bolt_rules        : Quy cách bu lông M12..M36 (B, C, F, G, P), đệm W1..W8, ron G1..G8, BLNG, BLNW
    5. steel_layers_and_blocks : 46 DCE Layers, 18 DimStyles, 110 Block Names, 52 KHSteel, 16 TagBlocks
    6. revit_family_mappings   : Ánh xạ Revit Families, Type tags, Tag symbols, tham số cấu kiện

Sử dụng:
    python dce_rules_registry.py [--rebuild] [--output path/to/json]
"""

import sys
import os
import json
import subprocess
import glob
import argparse
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

# ─────────────────────────────────────────────────────────────────────────────
# 0. Đường dẫn mặc định
# ─────────────────────────────────────────────────────────────────────────────

DCE_ROOT = Path(r"C:\Dce Pro")
DEFAULT_OUTPUT_JSON = Path(__file__).resolve().parent.parent / "_SHARED" / "data" / "dce_engineering_rules.json"
FORM2_DXF = DCE_ROOT / "Cad" / "Form 2.dxf"
STEEL_DLL = DCE_ROOT / "AddinSteelCad" / "DbimSteelAutocad.dll"

SYSTEM_DIRS = [
    DCE_ROOT / "System",
    DCE_ROOT / "SystemSteel",
    DCE_ROOT / "SystemRvt",
    DCE_ROOT / "AddinSteelCad" / "SystemSteel",
]


# ─────────────────────────────────────────────────────────────────────────────
# 1. Trình đọc và phân loại các file TXT của DCE
# ─────────────────────────────────────────────────────────────────────────────

def read_all_txt_configs(system_dirs: list) -> dict:
    """Đọc toàn bộ file txt cấu hình từ các thư mục DCE."""
    import re
    configs = {}
    for folder in system_dirs:
        folder_path = Path(folder)
        if not folder_path.exists():
            continue
        for txt_file in folder_path.glob("*.txt"):
            try:
                # Đọc với utf-8, fallback cp1258 / latin1
                try:
                    content = txt_file.read_text(encoding="utf-8").strip()
                except UnicodeDecodeError:
                    content = txt_file.read_text(encoding="cp1258", errors="ignore").strip()

                is_md5 = bool(re.fullmatch(r"[0-9a-fA-F]{32}", content))
                # Không ghi đè giá trị số hợp lệ đã có bằng chuỗi MD5 hex 32 ký tự
                if is_md5 and txt_file.name in configs and isinstance(configs[txt_file.name], (int, float)):
                    continue

                # Chuyển đổi kiểu dữ liệu nếu có thể (int, float, bool)
                val = content
                if content.lower() == "true":
                    val = True
                elif content.lower() == "false":
                    val = False
                elif content.lower() == "yes":
                    val = True
                elif content.lower() == "no":
                    val = False
                elif not is_md5:
                    try:
                        if "." in content:
                            val = float(content)
                        else:
                            val = int(content)
                    except ValueError:
                        val = content

                # Nếu khóa đã có số hợp lệ, không ghi đè bằng chuỗi không phải số
                if txt_file.name in configs and isinstance(configs[txt_file.name], (int, float)) and not isinstance(val, (int, float)):
                    continue

                configs[txt_file.name] = val
            except Exception as e:
                configs[txt_file.name] = f"<read_error: {e}>"
    return configs


# ─────────────────────────────────────────────────────────────────────────────
# 2. PowerShell Reflection trích xuất Type Metadata từ DbimSteelAutocad.dll
# ─────────────────────────────────────────────────────────────────────────────

def extract_dll_metadata(dll_path: Path) -> dict:
    """Trích xuất static fields và constants từ DbimSteelAutocad.dll qua PowerShell Reflection."""
    if not dll_path.exists():
        return {}

    ps_code = f"""
$DllPath = "{dll_path}"
$bytes = [System.IO.File]::ReadAllBytes($DllPath)
$asm = [System.Reflection.Assembly]::Load($bytes)

$types = @()
try {{
    $types = $asm.GetTypes()
}} catch [System.Reflection.ReflectionTypeLoadException] {{
    $types = $_.Exception.Types | Where-Object {{ $_ -ne $null }}
}}

$targetNames = @(
    "DbimSteelAutocad.DceSteelLayer",
    "DbimSteelAutocad.DceLayerName",
    "DbimSteelAutocad.DceBlockName",
    "DbimSteelAutocad.Z_DataSteel",
    "DbimSteelAutocad.KHSteel",
    "DbimSteelAutocad.TagBlock",
    "DbimSteelAutocad.TemplateCode"
)

$result = @{{}}

foreach ($t in $types) {{
    if ($targetNames -contains $t.FullName -or ($targetNames | Where-Object {{ $t.Name -eq ($_ -split '\\.')[-1] }})) {{
        $typeData = @{{
            "FullName" = $t.FullName
            "Fields" = @{{}}
            "Constants" = @{{}}
        }}
        $flags = [System.Reflection.BindingFlags]"Public,NonPublic,Static,Instance,FlattenHierarchy"
        try {{
            $fields = $t.GetFields($flags)
            foreach ($f in $fields) {{
                try {{
                    if ($f.IsLiteral) {{
                        $typeData["Constants"][$f.Name] = "$($f.GetRawConstantValue())"
                    }} elseif ($f.IsStatic) {{
                        $v = $f.GetValue($null)
                        $typeData["Fields"][$f.Name] = "$v"
                    }}
                }} catch {{}}
            }}
        }} catch {{}}
        $result[$t.FullName] = $typeData
    }}
}}

$json = $result | ConvertTo-Json -Depth 5
[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Output $json
"""
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_code],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=30
        )
        if proc.returncode == 0 and proc.stdout.strip():
            raw = proc.stdout.strip()
            # Bỏ BOM nếu có
            if raw.startswith("\ufeff"):
                raw = raw[1:]
            return json.loads(raw)
    except Exception as e:
        sys.stderr.write(f"[WARN] PowerShell reflection failed: {e}\n")
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# 3. Trích xuất Layers, Dimstyles, Blocks từ Form 2.dxf
# ─────────────────────────────────────────────────────────────────────────────

def extract_dxf_assets(dxf_path: Path) -> dict:
    """Trích xuất layers, dimstyles và blocks từ template Form 2.dxf qua ezdxf."""
    if not dxf_path.exists():
        return {"layers": [], "dimstyles": [], "blocks": {}}
    
    try:
        import ezdxf
        doc = ezdxf.readfile(str(dxf_path))
        layers = []
        for lay in doc.layers:
            layers.append({
                "name": lay.dxf.name,
                "color": lay.color,
                "linetype": lay.dxf.linetype,
            })
            
        dimstyles = [ds.dxf.name for ds in doc.dimstyles]
        
        blocks = {}
        for blk in doc.blocks:
            attdefs = [e.dxf.tag for e in blk if e.dxftype() == "ATTDEF"]
            blocks[blk.name] = {
                "name": blk.name,
                "attdefs": attdefs,
                "is_rebar_shape": blk.name.startswith("TK") and blk.name != "TKTitle",
                "is_title": blk.name == "TKTitle",
            }
            
        return {
            "layers": layers,
            "dimstyles": dimstyles,
            "blocks": blocks,
            "tk_block_count": len([b for b in blocks if b.startswith("TK")]),
        }
    except Exception as e:
        sys.stderr.write(f"[WARN] ezdxf extraction failed: {e}\n")
        return {"layers": [], "dimstyles": [], "blocks": {}, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# 4. Biên dịch toàn bộ thành dce_engineering_rules.json
# ─────────────────────────────────────────────────────────────────────────────

def build_dce_registry(output_file: Path = DEFAULT_OUTPUT_JSON) -> dict:
    """Tập hợp 1.239 file, Reflection DLL, và Assets DXF thành Registry chuẩn."""
    print("[1/4] Đang nạp toàn bộ file cấu hình TXT từ System/, SystemSteel/, SystemRvt/...")
    all_txt = read_all_txt_configs(SYSTEM_DIRS)
    print(f"      Đã nạp thành công {len(all_txt)} khóa cấu hình.")

    print("[2/4] Đang chạy Reflection trên DbimSteelAutocad.dll...")
    dll_meta = extract_dll_metadata(STEEL_DLL)
    print(f"      Đã trích xuất {len(dll_meta)} types từ assembly.")

    print("[3/4] Đang phân tích mẫu bản vẽ Form 2.dxf...")
    dxf_meta = extract_dxf_assets(FORM2_DXF)
    print(f"      Tìm thấy {len(dxf_meta.get('layers', []))} Layers, {len(dxf_meta.get('dimstyles', []))} DimStyles, {len(dxf_meta.get('blocks', {}))} Blocks.")

    # 4.1 Gom rc_detailing_rules
    rc_rules = {
        "standard_lap_multiplier": 40,  # QTKT_Noi1 = 40d
        "min_lap_stagger_offset": 10,   # 10d
        "standard_stock_length_mm": 11700,
        "min_reuse_offcut_length_mm": 500,
        "default_cover_beam": all_txt.get("BtbvDaiTren.txt", all_txt.get("CoverBeam.txt", 25)),
        "default_cover_col": all_txt.get("LopBTBVVeCot.txt", all_txt.get("CoverCol.txt", 30)),
        "default_cover_slab": all_txt.get("CoverSlab.txt", 15),
        "default_cover_wall": all_txt.get("LopBTBVVeVach.txt", all_txt.get("CoverWall.txt", 30)),
        "default_cover_footing": all_txt.get("LopBTBVVe.txt", all_txt.get("CoverFooting.txt", 50)),
        "cat_sole_cung_mot_lop": all_txt.get("CatSoLeCung1Lop.txt", True),
        "diem_noi_dau_cach_san_ve_cot": all_txt.get("DiemNoiDauCachSanVeCot.txt", 100),
        "dk_noi_nhan_co_chai": all_txt.get("DKNoiNhanCoChai.txt", 18),
        "column_noi_coupler": all_txt.get("ColumnNoiCoupler.txt", False),
        "pa_cat_thep_trong_mot_vung_noi": all_txt.get("PACatThepTrong1VungNoi.txt", "PA1"),
        "shop_toi_uu_to_hop_thep": all_txt.get("ShopToiUuToHopThep.txt", True),
        "bo_dim_dinh_vi_vung_noi": all_txt.get("BoDimDinhViVungNoiThepDam.txt", False),
        "dce_kh_dai": all_txt.get("KHDaiBang10.txt", "%%c"),
    }
    # Bổ sung các rule liên quan đến dầm, cột, vách, sàn từ txt
    for k, v in all_txt.items():
        if any(w in k for w in ["Noi", "Thep", "BaoVe", "Cover", "KhoangCach", "ToiUu", "Neo", "Moc"]):
            if k not in rc_rules:
                rc_rules[k.replace(".txt", "")] = v

    # 4.2 Gom viewport_packing_rules
    vp_rules = {
        "standard_sheet_height": all_txt.get("ViewPortCaoKhungTen.txt", 297),
        "standard_sheet_width": all_txt.get("ViewPortRongKhungTen.txt", 368),
        "standard_scale": all_txt.get("TyleTaoViewPort.txt", 20),
        "padding_x": all_txt.get("ViewPortAutoPadXx.txt", 5),
        "click_origin": all_txt.get("ViewPortAutoClickToaDoChinh.txt", "0,0,0"),
        "chieu_cao_khung_ten_ve_cot": all_txt.get("ChieuCaoKhungTenVeCot.txt", 4000),
        "chieu_cao_khung_ten_ve_vach": all_txt.get("ChieuCaoKhungTenVeVach.txt", 4000),
        "chia_khung_model_cat_dung_truc": all_txt.get("ChiaKhungModelCatDungTruc.txt", False),
        "viewport_command": all_txt.get("TaoViewport.txt", "taomv"),
        "viewport_sap_xep_toi_uu": all_txt.get("ViewPortSapXepToiUu.txt", False),
    }
    for k, v in all_txt.items():
        if any(w in k for w in ["ViewPort", "Khung", "TyLe", "BanVe", "KhoGiay"]):
            if k not in vp_rules:
                vp_rules[k.replace(".txt", "")] = v

    # 4.3 Gom steel_sections_catalog (I, U, V, Pipe, Box, Plate kèm Im0, Um0)
    steel_catalog = {
        "prefixes": {
            "I": all_txt.get("AutoCad_I.txt", "I-"),
            "U": all_txt.get("AutoCad_U.txt", "U-"),
            "V": all_txt.get("AutoCad_V.txt", "V-"),
            "Pipe": all_txt.get("AutoCad_Pipe.txt", "PIPE-"),
            "Box": all_txt.get("AutoCad_Box.txt", "BOX-"),
            "Plate": all_txt.get("AutoCad_Plate.txt", "PL-"),
        },
        "sections_I": {},
        "sections_U": {},
        "sections_V": {},
        "sections_P": {},
        "unit_weights_I_kg_m": {},
        "unit_weights_U_kg_m": {},
        "kh_steel_symbols": dll_meta.get("DbimSteelAutocad.KHSteel", {}).get("Fields", {}),
    }

    # Trích xuất I sections (ISect_1..19.txt -> "150 75 5 7", Im0, I_KH)
    for i in range(1, 25):
        key_i = f"ISect_{i}.txt"
        if key_i in all_txt:
            raw = str(all_txt[key_i]).strip()
            parts = raw.split()
            if len(parts) >= 4:
                h_mm, b_mm, tw_mm, tf_mm = (float(p) for p in parts[:4])
                desig = str(all_txt.get(f"I_KH{i}.txt", f"I{int(h_mm)}"))
                wt = float(all_txt.get(f"Im0_{i}.txt", 0.0))
                steel_catalog["sections_I"][f"I_{i}"] = {
                    "designation": desig,
                    "h_mm": h_mm,
                    "b_mm": b_mm,
                    "tw_mm": tw_mm,
                    "tf_mm": tf_mm,
                    "weight_kg_m": wt,
                }
                steel_catalog["unit_weights_I_kg_m"][f"I_{i}"] = wt

    # Trích xuất U sections (USect_1..12.txt -> "75 40 5 7", Um0, U_KH)
    for i in range(1, 20):
        key_u = f"USect_{i}.txt"
        if key_u in all_txt:
            raw = str(all_txt[key_u]).strip()
            parts = raw.split()
            if len(parts) >= 4:
                h_mm, b_mm, tw_mm, tf_mm = (float(p) for p in parts[:4])
                desig = str(all_txt.get(f"U_KH{i}.txt", f"U{int(h_mm)}"))
                wt = float(all_txt.get(f"Um0_{i}.txt", 0.0))
                steel_catalog["sections_U"][f"U_{i}"] = {
                    "designation": desig,
                    "h_mm": h_mm,
                    "b_mm": b_mm,
                    "tw_mm": tw_mm,
                    "tf_mm": tf_mm,
                    "weight_kg_m": wt,
                }
                steel_catalog["unit_weights_U_kg_m"][f"U_{i}"] = wt

    # Trích xuất V sections (VSect_1..13.txt -> "25 3", V_KH)
    for i in range(1, 20):
        key_v = f"VSect_{i}.txt"
        if key_v in all_txt:
            raw = str(all_txt[key_v]).strip()
            parts = raw.split()
            if len(parts) >= 2:
                b_mm, t_mm = (float(p) for p in parts[:2])
                desig = str(all_txt.get(f"V_KH{i}.txt", f"L{int(b_mm)}x{int(t_mm)}"))
                wt = round(((2 * b_mm - t_mm) * t_mm * 7850e-6), 2)
                steel_catalog["sections_V"][f"V_{i}"] = {
                    "designation": desig,
                    "b_mm": b_mm,
                    "t_mm": t_mm,
                    "weight_kg_m": wt,
                }

    # Trích xuất Pipe sections (PSect_1..11.txt -> "22 2", P_KH)
    for i in range(1, 20):
        key_p = f"PSect_{i}.txt"
        if key_p in all_txt:
            raw = str(all_txt[key_p]).strip()
            parts = raw.split()
            if len(parts) >= 2:
                d_mm, t_mm = (float(p) for p in parts[:2])
                desig = str(all_txt.get(f"P_KH{i}.txt", f"D{int(d_mm)}x{int(t_mm)}"))
                wt = round((3.141592653589793 * (d_mm - t_mm) * t_mm * 7850e-6), 2)
                steel_catalog["sections_P"][f"P_{i}"] = {
                    "designation": desig,
                    "d_mm": d_mm,
                    "t_mm": t_mm,
                    "weight_kg_m": wt,
                }

    # 4.4 Gom steel_bolt_rules (M12..M36, BLNG1..BLNG8, BLNW1..BLNW8, W1..W8, G1..G8)
    bolt_rules = {
        "bolts": {},
        "blng_edge_pitch": {},
        "blnw_plate_width": {},
        "washers_W": {},
        "gaskets_G": {},
    }
    for size in ["M12", "M16", "M20", "M24", "M27", "M30", "M33", "M36"]:
        spec = {}
        for suffix in ["B", "C", "F", "G", "P"]:
            k = f"{size}{suffix}.txt"
            if k in all_txt:
                spec[suffix] = all_txt[k]
        if spec:
            bolt_rules["bolts"][size] = spec

    for i in range(1, 9):
        k_g = f"BLNG{i}.txt"
        if k_g in all_txt:
            bolt_rules["blng_edge_pitch"][f"BLNG{i}"] = all_txt[k_g]
        k_w = f"BLNW{i}.txt"
        if k_w in all_txt:
            bolt_rules["blnw_plate_width"][f"BLNW{i}"] = all_txt[k_w]
        k_w_plain = f"W{i}.txt"
        if k_w_plain in all_txt:
            bolt_rules["washers_W"][f"W{i}"] = all_txt[k_w_plain]
        k_g_plain = f"G{i}.txt"
        if k_g_plain in all_txt:
            bolt_rules["gaskets_G"][f"G{i}"] = all_txt[k_g_plain]

    # 4.5 Gom steel_layers_and_blocks
    layers_blocks = {
        "dce_layers_46": dxf_meta.get("layers", []),
        "dce_dimstyles_18": dxf_meta.get("dimstyles", []),
        "dce_blocks_form2": dxf_meta.get("blocks", {}),
        "dce_layer_names_reflected": dll_meta.get("DbimSteelAutocad.DceLayerName", {}).get("Fields", {}),
        "dce_block_names_reflected": dll_meta.get("DbimSteelAutocad.DceBlockName", {}).get("Fields", {}),
        "dce_tag_blocks_reflected": dll_meta.get("DbimSteelAutocad.TagBlock", {}).get("Fields", {}),
    }

    # 4.6 Gom revit_family_mappings
    revit_mappings = {}
    for k, v in all_txt.items():
        if "Rvt" in k or "Family" in k or "Tag" in k:
            revit_mappings[k.replace(".txt", "")] = v

    full_registry = {
        "metadata": {
            "title": "DCE Pro Reverse-Engineered Engineering Rules Registry",
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "source": "C:\\Dce Pro (1,239 txt configs + DbimSteelAutocad.dll + Form 2.dxf)",
            "standard_compliance": "TCVN 5574:2018, TCVN 5575:2024",
            "total_txt_configs": len(all_txt),
            "total_dxf_layers": len(dxf_meta.get("layers", [])),
            "total_dxf_blocks": len(dxf_meta.get("blocks", {})),
        },
        "rc_detailing_rules": rc_rules,
        "viewport_packing_rules": vp_rules,
        "steel_sections_catalog": steel_catalog,
        "steel_bolt_rules": bolt_rules,
        "steel_layers_and_blocks": layers_blocks,
        "revit_family_mappings": revit_mappings,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(full_registry, f, ensure_ascii=False, indent=2)

    print(f"[4/4] Xuất thành công Registry ra file: {output_file}")
    print(f"      Kích thước: {output_file.stat().st_size / 1024:.2f} KB")
    return full_registry


# ─────────────────────────────────────────────────────────────────────────────
# 5. Class DceRulesRegistry để truy xuất trong code Python
# ─────────────────────────────────────────────────────────────────────────────

class DceRulesRegistry:
    """Interface tra cứu các quy tắc thiết kế DCE Pro."""

    _instance = None

    def __init__(self, json_path: Path = DEFAULT_OUTPUT_JSON):
        self.json_path = Path(json_path)
        self.data = {}
        self.load()

    def load(self, force_rebuild: bool = False):
        if not self.json_path.exists() or force_rebuild:
            if DCE_ROOT.exists():
                self.data = build_dce_registry(self.json_path)
            else:
                raise FileNotFoundError(f"Registry JSON not found at {self.json_path} and C:\\Dce Pro is absent.")
        else:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

    @classmethod
    def get_instance(cls, json_path: Path = DEFAULT_OUTPUT_JSON):
        if cls._instance is None:
            cls._instance = DceRulesRegistry(json_path)
        return cls._instance

    def get_rc_rule(self, key: str, default=None):
        return self.data.get("rc_detailing_rules", {}).get(key, default)

    def get_viewport_param(self, key: str, default=None):
        return self.data.get("viewport_packing_rules", {}).get(key, default)

    def get_bolt_spec(self, bolt_size: str) -> dict:
        """Lấy thông số chi tiết bu lông (e.g. 'M20') kèm B, C, F, G, P."""
        bolts = self.data.get("steel_bolt_rules", {}).get("bolts", {})
        return bolts.get(bolt_size.upper(), {})

    def get_bolt_edge_pitch(self, index: int) -> float:
        """Lấy khoảng cách bu lông BLNG1..BLNG8."""
        blng = self.data.get("steel_bolt_rules", {}).get("blng_edge_pitch", {})
        return float(blng.get(f"BLNG{index}", 0))

    def get_bolt_plate_width(self, index: int) -> float:
        """Lấy bề rộng bản mã bu lông BLNW1..BLNW8."""
        blnw = self.data.get("steel_bolt_rules", {}).get("blnw_plate_width", {})
        return float(blnw.get(f"BLNW{index}", 0))

    def get_steel_weight(self, section_type: str, index: int) -> float:
        """Lấy khối lượng thép hình đơn vị (kg/m) từ Im0 hoặc Um0."""
        catalog = self.data.get("steel_sections_catalog", {})
        if section_type.upper() == "I":
            weights = catalog.get("unit_weights_I_kg_m", {})
            return float(weights.get(f"I_{index}", 0))
        elif section_type.upper() == "U":
            weights = catalog.get("unit_weights_U_kg_m", {})
            return float(weights.get(f"U_{index}", 0))
        return 0.0

    def get_steel_section(self, section_type: str, index: int) -> dict:
        """Lấy thông số hình học chi tiết thép hình (designation, h_mm, b_mm, tw_mm, tf_mm, weight_kg_m)."""
        catalog = self.data.get("steel_sections_catalog", {})
        st = section_type.upper()
        if st == "I":
            return catalog.get("sections_I", {}).get(f"I_{index}", {})
        elif st == "U":
            return catalog.get("sections_U", {}).get(f"U_{index}", {})
        elif st == "V":
            return catalog.get("sections_V", {}).get(f"V_{index}", {})
        elif st == "P":
            return catalog.get("sections_P", {}).get(f"P_{index}", {})
        return {}

    def get_dce_layers(self) -> list:
        return self.data.get("steel_layers_and_blocks", {}).get("dce_layers_46", [])

    def get_dce_dimstyles(self) -> list:
        return self.data.get("steel_layers_and_blocks", {}).get("dce_dimstyles_18", [])

    def get_dce_blocks(self) -> dict:
        return self.data.get("steel_layers_and_blocks", {}).get("dce_blocks_form2", {})

    def get_revit_mapping(self, key: str, default=None):
        return self.data.get("revit_family_mappings", {}).get(key, default)


# ─────────────────────────────────────────────────────────────────────────────
# 6. CLI Entrypoint
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DCE Pro Rules Registry Builder")
    parser.add_argument("--rebuild", action="store_true", help="Buộc trích xuất lại từ C:\\Dce Pro")
    parser.add_argument("--output", type=str, default=str(DEFAULT_OUTPUT_JSON), help="Đường dẫn file JSON đầu ra")
    args = parser.parse_args()

    out_p = Path(args.output)
    if args.rebuild or not out_p.exists():
        build_dce_registry(out_p)
    else:
        reg = DceRulesRegistry(out_p)
        print(f"Registry đã có sẵn tại {out_p} ({out_p.stat().st_size / 1024:.2f} KB)")
        print(f"  - RC Detailing Rules : {len(reg.data.get('rc_detailing_rules', {}))} mục")
        print(f"  - Viewport Rules     : {len(reg.data.get('viewport_packing_rules', {}))} mục")
        print(f"  - Steel Bolts        : {len(reg.data.get('steel_bolt_rules', {}).get('bolts', {}))} cỡ bu lông")
        print(f"  - Form 2 Layers      : {len(reg.get_dce_layers())} layers")
        print(f"  - Form 2 Blocks      : {len(reg.get_dce_blocks())} blocks")
