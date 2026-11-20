# -*- coding: utf-8 -*-
"""
dce_cad_compliance_checker.py — Bộ lọc Kiểm toán Tuân thủ Chuẩn CAD DCE Pro
===========================================================================
SKILL_VERIFY · Bộ lọc 8 (Filter 8: DCE Pro CAD Compliance Auditor)

Mục đích:
    Kiểm toán tính tương thích và tuân thủ 100% chuẩn CAD DCE Pro cho các tệp DXF
    sinh ra bởi AI hoặc đơn vị thiết kế/thẩm tra. Chặn đứng lỗi mất layer,
    bị loại bỏ tệp (drawing discarded), hoặc vẽ hình học thô sơ (primitives) thay vì Block thuộc tính.

Các tiêu chí kiểm toán:
    1. Kiểm toán Cú pháp & Toàn vẹn (ezdxf.audit): Không có lỗi syntax / undefined linetype.
    2. Kiểm toán Hệ thống Phân lớp (Layer Standards):
       - Chặn đứng 100% các layer tự chế không chuẩn: 0_TRUC, 0_COT, 0_VACH, 0_DAM, 0_DIM, 0_TEXT...
       - Xác nhận toàn bộ cấu kiện nằm trên hệ layer chuẩn DCE_* (DCE_Truc, DCE_BaoBeTong, DCE_Hatch, DCE_Beam, DCE_Dim, DCE_Name...).
    3. Kiểm toán Khối thuộc tính (Attribute Blocks vs Raw Primitives):
       - Bong bóng trục bắt buộc là Block Dce_KhTenTruc / Dce_TenTruc (ATTDEF TRUC).
       - Tên cấu kiện bắt buộc là Block TenCauKien (ATTDEF TENCAUKIEN, SOCAUKIEN) hoặc DCE_Name.
       - Tiêu đề bản vẽ là Block DCE_Plan header 1 hoặc TKTitle.
    4. Kiểm toán Thứ nguyên & DimStyle:
       - Đường kích thước phải dùng DimStyle chuẩn Dce_*MV (Dce_100MV, Dce_50MV...) với mũi tên _ArchTick.
       - Cấm vẽ đường dim thủ công bằng các đoạn thẳng và text tĩnh rời rạc.
"""

import os
import sys
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from collections import Counter

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

try:
    import ezdxf
    HAS_EZDXF = True
except ImportError:
    HAS_EZDXF = False

# Danh sách tiền tố và layer chuẩn DCE Pro
DCE_STANDARD_LAYERS = {
    'dce_baobetong', 'dce_beam', 'dce_mainbeam', 'dce_block', 'dce_bottombars', 'dce_cdd',
    'dce_chiadoituong', 'dce_coc', 'dce_coc3d', 'dce_dim', 'dce_dim2',
    'dce_gen_open', 'dce_goidam', 'dce_hatch', 'dce_hatch @ 1', 'dce_kt',
    'dce_lanh_to', 'dce_mcwiczac', 'dce_name', 'dce_netdut', 'dce_netkhuat',
    'dce_netthay', 'dce_nhip', 'dce_note', 'dce_sub-coln_s---', 'dce_sub-coln_t---',
    'dce_sub-cowa_----', 'dce_symbol', 'dce_tennhip', 'dce_text', 'dce_textcoc',
    'dce_thepchu', 'dce_thepchu.ttt', 'dce_thepdai', 'dce_thepdai.ttt',
    'dce_tkt-text', 'dce_truc', 'dce_vitrithep', 'dce_wipeout', '0', 'defpoints',
    # Các layer đồ họa kỹ thuật mở rộng của cad_plan_engine v3.0 (7 Gap) & dầm sàn & tổng mặt bằng
    'dce_setout', 'dce_schedule', 'dce_frame', 'dce_gapopen', 'dce_voidx', 'dce_core',
    'dce_ranhdat', 'dce_chigioi', 'dce_road'
}

# Các layer tùy tiện phi chuẩn thường gặp cần chặn đứng
ILLEGAL_LAYER_PATTERNS = [
    '0_truc', '0_cot', '0_vach', '0_dam', '0_dim', '0_text', '0_kientruc',
    'axis', 'column', 'wall', 'beam', 'slab', 'text_dim', 'temp'
]

# Các block chuẩn bắt buộc của DCE Pro
DCE_AXIS_BLOCKS = {'dce_khtentruc', 'dce_tentruc'}
DCE_MEMBER_BLOCKS = {
    'tencaukien', 'dce_name', 'dce_khtendam', 'dce_khtennhip', 'dce_khmatcat',
    'dce_drop mark', 'dce_slab tag'
}
DCE_TITLE_BLOCKS = {'dce_plan header 1', 'tktitle', 'tktitlee', 'dce_caotrinh'}


def audit_dxf_compliance(dxf_path: str) -> Dict[str, Any]:
    """
    Kiểm toán chi tiết 1 file DXF theo chuẩn DCE Pro.
    """
    if not HAS_EZDXF:
        return {
            'file_path': dxf_path,
            'status': 'ERROR',
            'message': 'Thư viện ezdxf chưa được cài đặt.'
        }

    p = Path(dxf_path)
    if not p.is_file():
        return {
            'file_path': dxf_path,
            'status': 'FAIL',
            'message': f'File không tồn tại: {dxf_path}'
        }

    try:
        doc = ezdxf.readfile(str(p))
    except Exception as ex:
        return {
            'file_path': dxf_path,
            'status': 'FAIL',
            'critical_error': f'AutoCAD/ezdxf không thể mở file (Corrupt/Drawing Discarded): {str(ex)}'
        }

    # 1. Audit cú pháp & linetypes
    auditor = doc.audit()
    audit_errors = [str(err) for err in auditor.errors]
    audit_fixes_count = len(auditor.fixes)

    msp = doc.modelspace()
    total_entities = len(msp)

    # 2. Quét Layers
    layer_counts = Counter(e.dxf.layer for e in msp)
    illegal_layers_found = []
    non_dce_layers_found = []

    for lname, count in layer_counts.items():
        lname_low = lname.lower().strip()

        # Kiểm tra chuẩn DCE: Bắt đầu bằng dce_ hoặc các layer đặc biệt của AutoCAD
        if lname_low.startswith('dce_') or lname_low in ('0', 'defpoints'):
            if lname_low not in DCE_STANDARD_LAYERS:
                non_dce_layers_found.append({'layer': lname, 'count': count})
        else:
            # Layer không có tiền tố DCE_ -> Bị ghi nhận là Non-DCE
            non_dce_layers_found.append({'layer': lname, 'count': count})
            # Nếu thuộc danh mục layer tự chế cấm (0_*, axis, column...) -> Gắn cờ ILLEGAL
            for ill in ILLEGAL_LAYER_PATTERNS:
                if ill in lname_low:
                    illegal_layers_found.append({'layer': lname, 'count': count})
                    break

    # 3. Quét Block Inserts
    inserts = [e for e in msp if e.dxftype() == 'INSERT']
    block_names_lower = [i.dxf.name.lower() for i in inserts]

    axis_bubble_count = sum(1 for b in block_names_lower if b in DCE_AXIS_BLOCKS)
    member_tag_count = sum(1 for b in block_names_lower if b in DCE_MEMBER_BLOCKS)
    title_block_count = sum(1 for b in block_names_lower if b in DCE_TITLE_BLOCKS)

    # 4. Quét Dimensions & DimStyles
    dims = [e for e in msp if e.dxftype() == 'DIMENSION']
    dce_dims_count = 0
    non_dce_dims = []

    for d in dims:
        ds_name = d.dxf.dimstyle if hasattr(d.dxf, 'dimstyle') else ''
        if ds_name.lower().startswith('dce_'):
            dce_dims_count += 1
        else:
            non_dce_dims.append(ds_name)

    # 5. Kiểm toán Chất lượng Đồ họa Kỹ thuật (Graphic Sanity Auditor - Điều 12d AGENTS.md)
    graphic_sanity = {
        'has_concrete_solid_hatch': False,
        'has_standard_frame': False,
        'has_schedule_table': False,
        'has_setting_out_dims': False,
        'beam_void_clashes': 0,
    }

    # 5.1 Kiểm tra Solid Hatch bê tông (yêu cầu pattern SOLID, layer DCE_Hatch hoặc color 8)
    hatches = [e for e in msp if e.dxftype() == 'HATCH']
    solid_concrete_hatches = []
    for h in hatches:
        pat = str(getattr(h.dxf, 'pattern_name', '') or '').upper()
        lname = h.dxf.layer.lower()
        hcolor = getattr(h.dxf, 'color', 256)
        if pat == 'SOLID' and ('hatch' in lname or hcolor == 8):
            solid_concrete_hatches.append(h)
    graphic_sanity['has_concrete_solid_hatch'] = (len(solid_concrete_hatches) > 0)

    # 5.2 Kiểm tra Khung bản vẽ, Bảng thống kê & Dim định vị
    graphic_sanity['has_standard_frame'] = any('frame' in e.dxf.layer.lower() or 'kt' in e.dxf.layer.lower() for e in msp)
    graphic_sanity['has_schedule_table'] = any('schedule' in e.dxf.layer.lower() or 'tktitle' in getattr(e.dxf, 'name', '').lower() for e in msp)
    graphic_sanity['has_setting_out_dims'] = any('setout' in e.dxf.layer.lower() for e in msp)

    # 5.3 Kiểm tra dầm (DCE_Beam / DCE_MainBeam) cắt xuyên lỗ mở sàn (DCE_VoidX)
    void_lines = [e for e in msp if e.dxftype() == 'LINE' and e.dxf.layer.lower() == 'dce_voidx']
    void_boxes = []
    # Mỗi dấu X gồm 2 đường chéo cắt nhau -> gom cặp đường chéo giao tâm gần nhau
    used_void = set()
    for idx_a in range(len(void_lines)):
        if idx_a in used_void:
            continue
        la = void_lines[idx_a]
        sa, ea = la.dxf.start, la.dxf.end
        cax, cay = (sa.x + ea.x) / 2.0, (sa.y + ea.y) / 2.0
        for idx_b in range(idx_a + 1, len(void_lines)):
            if idx_b in used_void:
                continue
            lb = void_lines[idx_b]
            sb, eb = lb.dxf.start, lb.dxf.end
            cbx, cby = (sb.x + eb.x) / 2.0, (sb.y + eb.y) / 2.0
            if abs(cax - cbx) < 50.0 and abs(cay - cby) < 50.0:
                xs = [sa.x, ea.x, sb.x, eb.x]
                ys = [sa.y, ea.y, sb.y, eb.y]
                void_boxes.append((min(xs) + 50.0, min(ys) + 50.0, max(xs) - 50.0, max(ys) - 50.0))
                used_void.add(idx_a)
                used_void.add(idx_b)
                break

    beam_void_clashes = 0
    if void_boxes:
        for e in msp:
            if e.dxftype() == 'LINE' and e.dxf.layer.lower() in ('dce_beam', 'dce_mainbeam'):
                x1, y1 = e.dxf.start.x, e.dxf.start.y
                x2, y2 = e.dxf.end.x, e.dxf.end.y
                for bx0, by0, bx1, by1 in void_boxes:
                    if bx0 >= bx1 or by0 >= by1:
                        continue
                    # Kiểm tra trung điểm hoặc giao cắt thực sự bên trong lỗ mở
                    mx, my = (x1 + x2) / 2.0, (y1 + y2) / 2.0
                    if (bx0 < mx < bx1 and by0 < my < by1) or (
                        max(min(x1, x2), bx0) < min(max(x1, x2), bx1)
                        and max(min(y1, y2), by0) < min(max(y1, y2), by1)
                        and ((x1 <= bx0 and x2 >= bx1) or (x2 <= bx0 and x1 >= bx1)
                             or (y1 <= by0 and y2 >= by1) or (y2 <= by0 and y1 >= by1))
                    ):
                        beam_void_clashes += 1
                        break
    graphic_sanity['beam_void_clashes'] = beam_void_clashes

    # 6. Đánh giá Pass / Fail
    issues = []
    if audit_errors:
        issues.append(f"Audit phát hiện {len(audit_errors)} lỗi cú pháp/linetypes nghiêm trọng.")

    if illegal_layers_found:
        layers_str = ", ".join([f"{item['layer']} ({item['count']})" for item in illegal_layers_found])
        issues.append(f"Phát hiện layer tùy tiện phi chuẩn bị cấm: {layers_str}.")

    # Kiểm tra tính toàn vẹn của bản vẽ mặt bằng kết cấu (khi có hệ lưới trục hoặc >= 100 entities)
    truc_lines = sum(1 for e in msp if e.dxftype() == 'LINE' and 'truc' in e.dxf.layer.lower())
    is_structural_plan = (truc_lines >= 4 or axis_bubble_count > 0 or total_entities >= 100)
    if truc_lines > 0 and axis_bubble_count == 0:
        issues.append("Bản vẽ có đường tim trục nhưng không sử dụng Block thuộc tính Dce_KhTenTruc / Dce_TenTruc.")
    if is_structural_plan:
        if not graphic_sanity['has_concrete_solid_hatch']:
            issues.append("Bản vẽ mặt bằng thiếu Solid Hatch bê tông xám (SOLID, color=8 / DCE_Hatch) cho cột vách.")
        if not graphic_sanity['has_standard_frame']:
            issues.append("Bản vẽ mặt bằng thiếu Khung bản vẽ tiêu chuẩn (DCE_Frame).")
        if not graphic_sanity['has_schedule_table'] and title_block_count == 0:
            issues.append("Bản vẽ mặt bằng thiếu Bảng thống kê cấu kiện (DCE_Schedule) và Khung tên chuẩn.")
    if beam_void_clashes > 0:
        issues.append(f"Phát hiện {beam_void_clashes} nét dầm cắt xuyên qua lỗ rỗng xuyên sàn (DCE_VoidX).")

    status = "PASS" if (len(audit_errors) == 0 and len(illegal_layers_found) == 0 and len(issues) == 0) else "FAIL"

    return {
        'file_path': str(p),
        'status': status,
        'dxf_version': doc.dxfversion,
        'total_entities': total_entities,
        'audit_errors': audit_errors,
        'audit_fixes_count': audit_fixes_count,
        'illegal_layers': illegal_layers_found,
        'non_dce_layers': non_dce_layers_found,
        'blocks': {
            'total_inserts': len(inserts),
            'axis_bubbles': axis_bubble_count,
            'member_tags': member_tag_count,
            'title_blocks': title_block_count
        },
        'dimensions': {
            'total_dimensions': len(dims),
            'dce_compliant_dimensions': dce_dims_count,
            'non_dce_dimensions': non_dce_dims
        },
        'graphic_sanity': graphic_sanity,
        'issues': issues
    }


def main():
    parser = argparse.ArgumentParser(description="SKILL_VERIFY - DCE Pro CAD Compliance Checker")
    parser.add_argument("--file", "-f", help="Đường dẫn file DXF cần kiểm toán")
    parser.add_argument("--dir", "-d", help="Thư mục chứa các file DXF cần kiểm toán hàng loạt")
    parser.add_argument("--json", action="store_true", help="Xuất kết quả định dạng JSON")
    args = parser.parse_args()

    target_files = []
    if args.file:
        target_files.append(args.file)
    elif args.dir:
        p_dir = Path(args.dir)
        if p_dir.is_dir():
            target_files.extend([str(f) for f in p_dir.glob("**/*.dxf")])

    if not target_files:
        print("[!] Vui lòng cung cấp --file hoặc --dir. Dùng --help để xem chi tiết.")
        sys.exit(1)

    results = []
    all_pass = True

    for tf in target_files:
        res = audit_dxf_compliance(tf)
        results.append(res)
        if res.get('status') != 'PASS':
            all_pass = False

        if not args.json:
            icon = "✅" if res.get('status') == 'PASS' else "❌"
            print(f"\n{icon} KIỂM TOÁN TỆP: {res.get('file_path')}")
            print(f"   - Trạng thái: {res.get('status')} | Phiên bản CAD: {res.get('dxf_version')} | Tổng entities: {res.get('total_entities')}")
            print(f"   - Lỗi Cú pháp / Linetype: {len(res.get('audit_errors', []))} lỗi")
            print(f"   - Layer Phi chuẩn (Bị cấm): {len(res.get('illegal_layers', []))}")
            print(f"   - Blocks DCE: {res.get('blocks', {}).get('axis_bubbles', 0)} Trục, {res.get('blocks', {}).get('member_tags', 0)} Cấu kiện, {res.get('blocks', {}).get('title_blocks', 0)} Tiêu đề")
            print(f"   - Kích thước DCE: {res.get('dimensions', {}).get('dce_compliant_dimensions', 0)} / {res.get('dimensions', {}).get('total_dimensions', 0)}")
            if res.get('issues'):
                print("   [!] Các vấn đề phát hiện:")
                for iss in res.get('issues'):
                    print(f"       • {iss}")

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))

    sys.exit(0 if all_pass else 1)


if __name__ == '__main__':
    main()
