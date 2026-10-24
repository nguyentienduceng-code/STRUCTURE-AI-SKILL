"""
MODULE 13: assess_excavation_geometry.py
SKILL_GEOTECH v2.4.0 -- Urban Excavation Upgrade
Phan tich hinh hoc mat bang ho dao, xac dinh canh nguy hiem nhat.
Usage:
  python assess_excavation_geometry.py --L 14.5 --W 7.1 --sides "dat_tu_nhien,vach_betong,dat_tu_nhien,dat_tu_nhien" --strut_x 5.5 --strut_y 4.5
"""
import sys, json, math, argparse

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

SIDE_TYPE = {
    "dat_tu_nhien": {"label": "Dat tu nhien", "risk": 3, "note": "Ap luc dat day vao cu, dam bo chiu uon toan bo"},
    "vach_betong":  {"label": "Vach ham be tong hien huu", "risk": 0, "note": "Vach be tong la tuong chan cung, dam bo khong chiu ap luc dat"},
    "coc_hien_huu": {"label": "Co coc/dai mong hien huu can ke", "risk": 2, "note": "Khong ep cu duoc, can bien phap chong tuong khac"},
    "cu_nhung_day": {"label": "Cu nhung day du chieu dai", "risk": 1, "note": "Cu dam bao on dinh, kiem tra dam bo"},
}

def assess_geometry(L, W, sides, strut_x=None, strut_y=None, corner_brace_inner=2.0):
    """
    sides: list 4 phan tu theo thu tu [canh_dai_1, canh_ngan_1, canh_dai_2, canh_ngan_2]
    """
    logs = []
    results = []
    side_labels = [f"Canh dai (L={L}m) - phia duoi", f"Canh ngan (W={W}m) - phia trai", f"Canh dai (L={L}m) - phia tren", f"Canh ngan (W={W}m) - phia phai"]
    side_dims   = [L, W, L, W]

    logs.append({"step": "Thong so ho dao", "L_m": L, "W_m": W, "ratio_L_W": round(L/W, 2)})

    for i, (side_code, dim, side_label) in enumerate(zip(sides, side_dims, side_labels)):
        if side_code not in SIDE_TYPE:
            side_code = "dat_tu_nhien"
        stype = SIDE_TYPE[side_code]
        risk = stype["risk"]

        # Tinh nhip tu do dam bo
        if side_code == "vach_betong":
            L_clear = 0
            span_note = "Vach be tong do, khong co nhip tu do"
        else:
            if strut_x and dim == L:
                # Canh dai: nhip giua = L - 2*strut_x (hoac dat cuoi L neu khong co strut)
                L_clear = max(0, L - 2*strut_x)
                span_note = f"Nhip tu do giua = {L:.1f} - 2x{strut_x:.1f} = {L_clear:.1f}m"
            elif strut_y and dim == W:
                L_clear = max(0, W - strut_y - corner_brace_inner)
                span_note = f"Nhip tu do = {W:.1f} - {strut_y:.1f} - {corner_brace_inner:.1f} = {L_clear:.1f}m"
            else:
                L_clear = dim
                span_note = "Chua co thanh chong, nhip tu do = chieu dai canh"

        results.append({
            "canh": side_label,
            "loai": stype["label"],
            "muc_rui_ro": risk,
            "L_clear_m": round(L_clear, 2),
            "ghi_chu": stype["note"],
            "span_note": span_note
        })
        logs.append({"step": f"Phan tich {side_label}", "loai": stype["label"], "L_clear": L_clear, "risk_level": risk})

    # Xac dinh canh nguy hiem nhat
    dat_sides = [r for r in results if r["muc_rui_ro"] > 0]
    if dat_sides:
        critical = max(dat_sides, key=lambda x: x["L_clear_m"])
        critical_note = f"CANH NGUY HIEM NHAT: {critical['canh']} -- Nhip tu do L_clear = {critical['L_clear_m']}m"
    else:
        critical_note = "Tat ca cac canh deu co cau kien chong do hoac vach hien huu. An toan."

    # Kiem tra corner brace
    corner_brace_note = ""
    if strut_x and strut_y:
        brace_length = math.sqrt(strut_x**2 + strut_y**2)
        brace_angle = math.degrees(math.atan(strut_y / strut_x))
        corner_brace_note = f"Thanh chong goc: chieu dai = sqrt({strut_x}^2 + {strut_y}^2) = {brace_length:.2f}m, goc = {brace_angle:.1f} do"
        logs.append({"step": "Kich thuoc thanh chong goc", "brace_length_m": round(brace_length,2), "angle_deg": round(brace_angle,1)})

    return {
        "Standard_Method": "CIRIA C760 / BS EN 1997-1 Eurocode 7",
        "Ho_dao": {"L_m": L, "W_m": W, "Ratio": round(L/W,2)},
        "Phan_tich_tung_canh": results,
        "Critical_Assessment": critical_note,
        "Corner_Brace_Geometry": corner_brace_note,
        "Calculation_Logs": logs
    }

def main():
    p = argparse.ArgumentParser(description="MODULE 13: Excavation Geometry Assessment")
    p.add_argument("--L", type=float, required=True, help="Chieu dai ho dao (m)")
    p.add_argument("--W", type=float, required=True, help="Chieu rong ho dao (m)")
    p.add_argument("--sides", required=True, help="4 canh cach boi dau phay: dat_tu_nhien|vach_betong|coc_hien_huu|cu_nhung_day")
    p.add_argument("--strut_x", type=float, default=None, help="Khoang cach diem ty thanh chong goc tren canh dai (m)")
    p.add_argument("--strut_y", type=float, default=None, help="Khoang cach diem ty thanh chong goc tren canh ngan (m)")
    p.add_argument("--corner_inner", type=float, default=2.0, help="Nhip chong goc trong (m), mac dinh 2.0")
    args = p.parse_args()
    sides = args.sides.split(",")
    result = assess_geometry(args.L, args.W, sides, args.strut_x, args.strut_y, args.corner_inner)
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
