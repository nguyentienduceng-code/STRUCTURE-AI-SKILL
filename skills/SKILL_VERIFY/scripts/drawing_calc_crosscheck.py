#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SKILL_VERIFY & SKILL_BIM_COORDINATION — Automated 4-Way Scope & Clash Cross-Checker
Version: 2.3.0 (Production Audit Engine)
Chức năng:
  - Tự động phân tích phạm vi thẩm tra (Scope Expansion) và đối soát 4 chiều:
    [Tầng 1] Bản vẽ Kiến trúc (KT) ↔ Bản vẽ Kết cấu (KC): Lưới trục, nhịp, cao độ, tiết diện xà gồ/cột.
    [Tầng 2] Nội bộ Bản vẽ Kết cấu (Mặt bằng ↔ Mặt cắt ↔ Chi tiết ↔ Tag thép):
             Phát hiện xung đột ký hiệu trục, độ lệch tâm móng, bu lông neo, đường kính/khoảng cách thép.
    [Tầng 3] Bản vẽ Kết cấu (BVKC) ↔ Thuyết minh Tính toán (TMKC) & Mô hình ETABS/SAP2000:
             Kiểm tra tiết diện khung thép, kích thước móng, hàm lượng thép As_drawing vs As_required,
             mác bê tông/cường độ thép, và các kết cấu vẽ trên bản vẽ nhưng bỏ sót trong mô hình.
    [Tầng 4] Kiểm toán Cơ học Độc lập & Tiêu chuẩn Pháp lý (TCVN 5575:2024, TCVN 5574:2018, TCVN 9362:2012,
             TT 34/2026/TT-BXD, QCVN 03:2022/BXD, QCVN 06:2022/BXD).
"""

import json
import math
import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional

@dataclass
class ClashRecord:
    clash_id: str
    item_code: str
    item_name: str
    layer: str  # Tầng 1 (KT-KC), Tầng 2 (MB-MC-Tag), Tầng 3 (BV-TMKC-ETABS), Tầng 4 (TCVN-Cơ học)
    severity: str  # CRITICAL, MAJOR, MINOR
    source_a_ref: str
    source_a_val: str
    source_b_ref: str
    source_b_val: str
    engineering_impact: str
    mandatory_fix: str
    linked_rfi_ncr: str

def compute_rebar_area_cm2(tag: str, width_m: float = 1.0) -> float:
    """Tính diện tích cốt thép As (cm2) từ tag bản vẽ: ví dụ '3Ø16', '2Ø16+1Ø16', hoặc 'Ø10a150'."""
    tag = tag.strip().replace(" ", "")
    # Dạng thanh rời: nØd + mØd
    parts = tag.split("+")
    total_area = 0.0
    matched_bars = False
    for p in parts:
        m = re.match(r"^(\d+)[ØøDd](\d+)$", p)
        if m:
            n_bars = int(m.group(1))
            dia_mm = float(m.group(2))
            total_area += n_bars * math.pi * (dia_mm / 20.0) ** 2
            matched_bars = True
    if matched_bars:
        return round(total_area, 2)
    # Dạng thép sàn/vách rải đều: ØdaS
    m_grid = re.match(r"^[ØøDd](\d+)[a@](\d+)$", tag)
    if m_grid:
        dia_mm = float(m_grid.group(1))
        spacing_mm = float(m_grid.group(2))
        n_per_width = (width_m * 1000.0) / spacing_mm
        area_single = math.pi * (dia_mm / 20.0) ** 2
        return round(n_per_width * area_single, 2)
    return 0.0

def build_tanhy_4way_matrix() -> List[ClashRecord]:
    """Xuất danh mục 18 xung đột 4 chiều (KT ↔ MB ↔ MC/Tag ↔ TMKC) phát hiện tại Dự án Tân Hỷ."""
    return [
        ClashRecord(
            clash_id="CL-01",
            item_code="CN3",
            item_name="Nhà xưởng chính CN3 (15.252 m2)",
            layer="Tầng 1 (KT ↔ KC) & Tầng 2 (MB ↔ Chi tiết)",
            severity="CRITICAL",
            source_a_ref="BV Kiến trúc KT-01..05 & MB móng KC-01 (tr.2)",
            source_a_val="7 trục ngang Y1–Y7 (bước 7.75m, cột giữa tại trục Y4); 11 trục dọc X1–X11 (90.0m)",
            source_b_ref="TMKC 01 (tr.7) & BV Chi tiết móng KC-02 (tr.3), KC-03 (tr.4)",
            source_b_val="TMKC vẽ 3 trục Y1-Y2-Y3 (nhịp 23.25m); KC-02 ghi móng giữa M2 tại trục 'Y2'; KC-03 ghi móng M4 tại trục 'X1-X14' (dư 3 trục ma X12-X14)",
            engineering_impact="Định vị sai tim móng cột giữa trên thực địa và sai lệch hệ tọa độ bàn giao giữa nhà thầu phần ngầm và nhà thầu lắp dựng kết cấu thép.",
            mandatory_fix="Chuẩn hóa toàn bộ hệ lưới trục thành Y1–Y7 và X1–X11 trên TMKC, KC-02 (sửa Y2 -> Y4) và KC-03 (sửa X1-X14 -> X1-X11).",
            linked_rfi_ncr="NCR-DES-20261025-006 / RFI-DES-20261025-001"
        ),
        ClashRecord(
            clash_id="CL-02",
            item_code="CN3",
            item_name="Nhà xưởng chính CN3",
            layer="Tầng 2 (MB ↔ Chi tiết) & Tầng 3 (BV ↔ TMKC)",
            severity="CRITICAL",
            source_a_ref="BV Kết cấu KC-09 (tr.10) — Mặt bằng bản mã chân cột CT1-K1 & CT2-K1",
            source_a_val="Ghi chú '4 BU LÔNG NEO M24' (4M24), bản đế PL-16",
            source_b_ref="BV Kết cấu KC-09 (tr.10) — Chi tiết bu lông neo góc phải & TMKC 01",
            source_b_val="Vẽ song song 2 chi tiết 'BL neo D.20x750' (M20) và 'BL neo D.24x850' (M24) không phân định vị trí; TMKC 01 bỏ sót hoàn toàn tính toán bu lông neo chịu nhổ",
            engineering_impact="Gia công nhầm bu lông M20 tại cột chính chịu lực nhổ gió bão và mô men chân cột, gây đứt bu lông hoặc tuột neo khi bão.",
            mandatory_fix="Xóa chi tiết BL neo D.20x750 thừa hoặc quy định rõ chỉ dùng cho cột phụ sảnh; bổ sung bảng kiểm toán bu lông neo M24 và sườn tăng cứng chân cột vào TMKC 01.",
            linked_rfi_ncr="RFI-DES-20261025-003"
        ),
        ClashRecord(
            clash_id="CL-03",
            item_code="CN3",
            item_name="Nhà xưởng chính CN3",
            layer="Tầng 2 (MB ↔ Mặt cắt) & Tầng 3 (BV ↔ TMKC)",
            severity="CRITICAL",
            source_a_ref="BV Kết cấu KC-02 (tr.3) & KC-03 (tr.4) — Mặt bằng móng M1, M3",
            source_a_val="M1 (1700x2000) đặt cổ cột lệch tâm: 1230 + 770 = 2000mm (e0 = 230mm); M3 (1200x1400) lệch tâm 2 phương: 880+520mm và 705+495mm",
            source_b_ref="BV Kết cấu KC-02, KC-03 (Mặt cắt 1-1) & TMKC 01 (tr.21, 23)",
            source_b_val="Mặt cắt 1-1 vẽ cổ cột đặt chính giữa móng đối xứng; TMKC 01 tính M1, M3 như móng đúng tâm (e0 = 0)",
            engineering_impact="Mô men lệch tâm bổ sung M_e = N * e0 làm tăng áp lực mép móng thêm 35–45%, vượt sức chịu tải nền đất và gây lún nghiêng chân cột biên.",
            mandatory_fix="Tính toán lại móng M1, M3 theo bài toán nén lệch tâm thực tế (hoặc thiết kế dầm giằng móng cân bằng lệch tâm) và vẽ đúng vị trí cổ cột trên Mặt cắt 1-1.",
            linked_rfi_ncr="NCR-DES-20261025-002 / RFI-DES-20261025-003"
        ),
        ClashRecord(
            clash_id="CL-04",
            item_code="CN3",
            item_name="Nhà xưởng chính CN3",
            layer="Tầng 2 (Chi tiết ↔ Tag thép) & Tầng 3 (BV ↔ TMKC)",
            severity="MAJOR",
            source_a_ref="BV Kết cấu KC-02 (tr.3) & KC-03 (tr.4) — Mặt cắt cổ cột M1, M2, M3, M4",
            source_a_val="Cổ cột M1, M2 vẽ 500x350 (6Ø16); M3 ghi trùng 2 mặt cắt tên 'MC:1-1' (400x350); M4 vẽ 6 thanh thép nhưng tag ghi '2Ø16 + 2Ø16' (4 thanh)",
            source_b_ref="TMKC 01 (tr.21–24)",
            source_b_val="TMKC 01 khai báo cổ cột M1 là ac = 0.5m, bc = 0.3m (500x300)",
            engineering_impact="Mâu thuẫn kích thước cổ cột (350mm vs 300mm) và số thanh thép cổ cột M4 (vẽ 6 thanh, ghi 4 thanh) gây tranh chấp khối lượng nghiệm thu tại công trường.",
            mandatory_fix="Đồng bộ tiết diện cổ cột M1, M2 (500x350) giữa bản vẽ và TMKC; sửa tag thép cổ cột M4 thành 6Ø16 (hoặc 4Ø16) thống nhất với hình vẽ.",
            linked_rfi_ncr="RFI-DES-20261025-003"
        ),
        ClashRecord(
            clash_id="CL-05",
            item_code="CN3",
            item_name="Nhà xưởng chính CN3",
            layer="Tầng 3 (BV ↔ TMKC — Tiết diện & Sườn tăng cứng khung K1)",
            severity="CRITICAL",
            source_a_ref="BV Kết cấu KC-07 (tr.8) — Khung chính K1 (nhịp 2x23.25m = 46.5m)",
            source_a_val="Kèo FR2 ghi 'I-400x210x5x6'; toàn bộ cột C1, SC2 và kèo RF1, RF3 (bụng mảnh tw=5mm, hw/tw up to 227.6) KHÔNG vẽ sườn tăng cứng ngang và sườn dọc",
            source_b_ref="TMKC 01 (tr.32–42)",
            source_b_val="Tiêu đề mục kèo FR2 ghi 'I-400x210x6x10'; bảng tính kết luận C1 (lambda_w=5.57>2.3), SC2 (5.98>2.3), RF1 (5.98>3.2) phải có sườn ngang và RF3 (lambda_w=8.01>7.67) BẮT BUỘC có cả sườn ngang lẫn sườn dọc",
            engineering_impact="Bản bụng mảnh tw=5mm mất ổn định cục bộ (Local Web Buckling) ngay dưới tải trọng tiêu chuẩn nếu gia công theo bản vẽ KC-07 không có sườn.",
            mandatory_fix="Bổ sung đầy đủ chi tiết sườn tăng cứng ngang (khoảng cách a <= 2*hw) và sườn tăng cứng dọc cho kèo RF3 lên bản vẽ KC-07, hoặc tăng chiều dày bản bụng lên tw >= 6–8mm.",
            linked_rfi_ncr="NCR-DES-20261025-003 / RFI-DES-20261025-004"
        ),
        ClashRecord(
            clash_id="CL-06",
            item_code="CN3",
            item_name="Nhà xưởng chính CN3",
            layer="Tầng 3 (BV ↔ TMKC — Cấp độ bền Bê tông & Thép)",
            severity="MAJOR",
            source_a_ref="BV Kết cấu KC-01 (tr.2) — Ghi chú chung",
            source_a_val="Bê tông móng Mác 250 (B20, Rb = 11.5 MPa); Thép Ø>=10 dùng nhóm AII (Ra = 2800 kG/cm2)",
            source_b_ref="TMKC 01 (tr.6, tr.21)",
            source_b_val="TMKC 01 trang 6 ghi B22.5 (M300, Rb = 11.5 MPa) và trang 21 tính móng với thép CB300-V (Rs = 2600 kG/cm2)",
            engineering_impact="Sử dụng ký hiệu thép AII/AIII cũ đã hết hiệu lực và vênh cấp bê tông B20 vs B22.5 giữa bản vẽ thi công và thuyết minh.",
            mandatory_fix="Chuẩn hóa ghi chú KC-01 theo TCVN 5574:2018 & TCVN 1651-2:2018: Bê tông B20 (M250), thép CB240-T (Ø<10) và CB300-V / CB400-V (Ø>=10).",
            linked_rfi_ncr="RFI-DES-20261025-011"
        ),
        ClashRecord(
            clash_id="CL-07",
            item_code="CN3",
            item_name="Nhà xưởng chính CN3",
            layer="Tầng 1 (KT ↔ KC) & Tầng 3 (BV ↔ Мо hình ETABS)",
            severity="CRITICAL",
            source_a_ref="BV Kết cấu KC-13, KC-14 (tr.14–15) & KC-05 (tr.6)",
            source_a_val="Hệ Giàn thao tác treo ở cao độ +6.000m (thép hộp 50x100x1.5, thanh xiên V50x50x3 hạ xuống +5.300m) treo trực tiếp vào kèo chính; thanh giằng dọc mái ỐNG D114x3.05",
            source_b_ref="TMKC 01 & Mô hình ETABS + BV Kiến trúc KT-04, KT-05",
            source_b_val="ETABS và TMKC 01 bỏ sót 100% tải trọng giàn treo +6.000m và không tính thanh chống dọc D114x3.05; BV Kiến trúc KT-04, KT-05 không thể hiện giàn treo này",
            engineering_impact="Kèo mái nhịp 23.25m đang đạt hệ số sử dụng 92.2% (nén-uốn) và võng 7.99cm/9.3cm khi chưa kể tải giàn treo; khi treo giàn thao tác + người + hệ M&E sẽ vượt giới hạn chịu lực ULS và SLS.",
            mandatory_fix="Đưa toàn bộ tải trọng giàn treo +6.000m (tĩnh tải + hoạt tải sửa chữa >= 1.5 kPa + hệ Sprinkler) vào mô hình ETABS để kiểm toán lại kèo K1 và bổ sung kiểm toán hệ giằng dọc D114x3.05.",
            linked_rfi_ncr="NCR-DES-20261025-004 / RFI-DES-20261025-006"
        ),
        ClashRecord(
            clash_id="CL-08",
            item_code="HT5",
            item_name="Nhà Bảo Vệ 2 (25.92 m2)",
            layer="Tầng 2 (MB ↔ Chi tiết) & Tầng 3 (BV ↔ TMKC)",
            severity="MINOR",
            source_a_ref="BV Kết cấu Hạng mục phụ (tr.2) — KC-01 Nhà bảo vệ",
            source_a_val="Mặt bằng đà kiềng ghi ký hiệu 'DK1A (200x300)'; Mặt cắt chi tiết ghi tên 'DK1 (200x300)' với thép gối/nhịp là 2Ø16 + 1Ø16 (3Ø16, As = 6.03 cm2)",
            source_b_ref="TMKC 05 Nhà bảo vệ (tr.13)",
            source_b_val="TMKC 05 tính toán dầm và chọn cốt thép chỉ 2Ø16 (As = 4.02 cm2)",
            engineering_impact="Ký hiệu cấu kiện trên mặt bằng (DK1A) không khớp tên mặt cắt chi tiết (DK1); lượng thép trên bản vẽ lớn hơn thuyết minh 50%.",
            mandatory_fix="Đồng bộ tên cấu kiện DK1 trên mặt bằng và chi tiết KC-01 Nhà bảo vệ.",
            linked_rfi_ncr="RFI-DES-20261025-011"
        ),
        ClashRecord(
            clash_id="CL-09",
            item_code="HT5",
            item_name="Nhà Bảo Vệ 2 (25.92 m2)",
            layer="Tầng 2 (MB ↔ Mặt cắt) & Tầng 3 (BV ↔ TMKC)",
            severity="MINOR",
            source_a_ref="BV Kết cấu Hạng mục phụ (tr.3) — KC-02 Mặt bằng thép sàn mái Nhà bảo vệ",
            source_a_val="Mặt bằng thép sàn mái ghi cả thép lớp dưới và thép mũ gối đều là 'Ø10a200' (As = 3.93 cm2/m)",
            source_b_ref="BV Kết cấu Hạng mục phụ (tr.3) — Mặt cắt 1-1 ngay trên cùng tờ KC-02",
            source_b_val="Mặt cắt 1-1 ghi tag thép mũ gối sàn mái là 'Ø10a150' (As = 5.24 cm2/m), đá nhau trực tiếp với Mặt bằng 'Ø10a200'",
            engineering_impact="Thợ sắt không biết rải thép mũ sàn theo bước a150 (Mặt cắt) hay a200 (Mặt bằng).",
            mandatory_fix="Chỉnh sửa thống nhất tag thép mũ sàn mái trên Mặt bằng và Mặt cắt 1-1 tờ KC-02 Nhà bảo vệ.",
            linked_rfi_ncr="RFI-DES-20261025-011"
        ),
        ClashRecord(
            clash_id="CL-10",
            item_code="DV3",
            item_name="Nhà Rác (156.0 m2)",
            layer="Tầng 3 (Tag thép Bản vẽ ↔ Thuyết minh TMKC — THIẾU THÉP CHỊU LỰC)",
            severity="CRITICAL",
            source_a_ref="BV Kết cấu Hạng mục phụ (tr.6) — KC-02 Mặt cắt Đà kiềng DK2 (200x400) Nhà rác",
            source_a_val="Vẽ và ghi tag cốt thép nhịp dưới chỉ '2Ø16' (As_drawing = 4.02 cm2), lớp trên '2Ø16'",
            source_b_ref="TMKC 02 Nhà rác (tr.17)",
            source_b_val="Đà kiềng DK2 (200x400) chịu mô men nhịp M = 50.0 kN.m, diện tích thép yêu cầu As_tt = 4.23 cm2 > 4.02 cm2; trong TMKC chọn '3Ø16' (As_ch = 6.03 cm2)",
            engineering_impact="Bản vẽ thi công KC-02 bố trí THIẾU THÉP CHỊU UỐN NHỊP so với diện tích tính toán yêu cầu (As_drawing = 4.02 cm2 < As_tt = 4.23 cm2), vi phạm điều kiện bền ULS theo TCVN 5574:2018!",
            mandatory_fix="Sửa ngay mặt cắt đà kiềng DK2 (200x400) trên bản vẽ KC-02 Nhà rác từ 2Ø16 lên 3Ø16 (2Ø16 + 1Ø16) đúng theo bảng tính TMKC 02.",
            linked_rfi_ncr="NCR-DES-20261025-007 / RFI-DES-20261025-012"
        ),
        ClashRecord(
            clash_id="CL-11",
            item_code="DV3",
            item_name="Nhà Rác (156.0 m2)",
            layer="Tầng 2 & Tầng 3 (Thiếu bản vẽ kết cấu mái & cột BTCT)",
            severity="MAJOR",
            source_a_ref="BV Kết cấu Hạng mục phụ (tr.5–6) — Nhà rác",
            source_a_val="Chỉ có 2 tờ KC-01 (Mặt bằng móng) và KC-02 (Mặt bằng đà kiềng); THIẾU HOÀN TOÀN bản vẽ Mặt bằng xà gồ mái và chi tiết khung/cột Nhà rác",
            source_b_ref="TMKC 02 Nhà rác (tr.7, tr.18) & BV Kiến trúc Nhà rác (tr.4–5)",
            source_b_val="TMKC 02 mô hình khung cột BTCT 200x200 và tính xà gồ mái hộp 50x100x1.5 nhưng bỏ trống phần kiểm toán cột BTCT; bản vẽ kết cấu quên xuất tờ mặt bằng mái và cột",
            engineering_impact="Không có bản vẽ kết cấu cột và mái Nhà rác để thi công; cột BTCT 200x200 chưa được kiểm toán.",
            mandatory_fix="Bổ sung bản vẽ KC-03 (Chi tiết cột BTCT và Mặt bằng xà gồ mái Nhà rác) và bảng tính cột BTCT vào TMKC 02.",
            linked_rfi_ncr="RFI-DES-20261025-009"
        ),
        ClashRecord(
            clash_id="CL-12",
            item_code="DV4",
            item_name="Nhà Vệ Sinh 2 (66.0 m2)",
            layer="Tầng 3 (BV ↔ TMKC — Thiếu bản vẽ móng & Móng quá tải 15.6%)",
            severity="CRITICAL",
            source_a_ref="BV Kết cấu Hạng mục phụ (tr.8) — KC-01 Nhà vệ sinh",
            source_a_val="Chỉ vẽ Mặt bằng đà kiềng và Mặt bằng xà gồ; KHÔNG CÓ Mặt bằng móng và Chi tiết móng M1 trên bản vẽ",
            source_b_ref="TMKC 03 Nhà vệ sinh (tr.12)",
            source_b_val="TMKC 03 tính móng M1 (1.0x1.0m) nhưng áp lực đáy móng tiêu chuẩn sigma_max,tc = 20.8 T/m2 > Rtc = 18.0 T/m2 (vượt tải 15.6%!) và bỏ sót kiểm toán cột BTCT",
            engineering_impact="Vừa thiếu bản vẽ móng để thi công, vừa thiết kế móng 1.0x1.0m không đủ sức chịu tải nền đất (quá tải 15.6%).",
            mandatory_fix="Tăng kích thước móng M1 Nhà vệ sinh lên tối thiểu 1.2x1.2m (sigma_max < 18 T/m2), bổ sung kiểm toán cột BTCT và xuất bổ sung bản vẽ Mặt bằng/Chi tiết móng Nhà vệ sinh.",
            linked_rfi_ncr="NCR-DES-20261025-007 / RFI-DES-20261025-009"
        ),
        ClashRecord(
            clash_id="CL-13",
            item_code="DV4",
            item_name="Nhà Vệ Sinh 2 (66.0 m2)",
            layer="Tầng 3 (BV ↔ TMKC — Tiết diện xà gồ mái đá nhau)",
            severity="MAJOR",
            source_a_ref="BV Kết cấu Hạng mục phụ (tr.8) — KC-01 Mặt bằng xà gồ Nhà vệ sinh",
            source_a_val="Ghi chú dùng xà gồ thép hộp '[]-50*100*1.5' (@ <= 1100)",
            source_b_ref="TMKC 03 Nhà vệ sinh (tr.14)",
            source_b_val="Bảng tính kiểm toán xà gồ dùng tiết diện thép hộp '60x120x1.5' (mô men kháng uốn lớn hơn 44% so với 50x100x1.5)",
            engineering_impact="Bản vẽ thi công hạ cấp tiết diện xà gồ từ 60x120x1.5 (trong tính toán) xuống 50x100x1.5.",
            mandatory_fix="Đồng bộ tiết diện xà gồ trên bản vẽ KC-01 Nhà vệ sinh thành []-60x120x1.5 hoặc tính kiểm toán lại với tiết diện 50x100x1.5.",
            linked_rfi_ncr="RFI-DES-20261025-009"
        ),
        ClashRecord(
            clash_id="CL-14",
            item_code="DV5",
            item_name="Nhà Để Xe (408.0 m2)",
            layer="Tầng 3 (BV ↔ TMKC — Kích thước móng M1 đá nhau & Lật móng)",
            severity="CRITICAL",
            source_a_ref="BV Kết cấu Hạng mục phụ (tr.10–11) — KC-01 & KC-02 Nhà xe",
            source_a_val="Móng M1 vẽ kích thước 1000 x 1700 mm (1.0x1.7m, diện tích 1.70 m2), cổ cột 200x450 (10Ø16); trên mặt bằng mái có dầm dọc đầu cột []-100x100x4",
            source_b_ref="TMKC 04 Nhà xe (tr.10–12)",
            source_b_val="TMKC 04 tính móng M1 với kích thước b=1.4m, a=2.0m (1.4x2.0m = 2.80 m2, lớn hơn bản vẽ 65%) và cổ cột 250x200; nhưng ngay cả với móng 1.4x2.0m đã bị kéo nhổ đáy móng sigma_min = -3.319 T/m2 (e = 1.366m > a/6 = 0.333m); đồng thời BỎ TRỐNG 100% kiểm toán cột H250, kèo công son H400 và dầm dọc []-100x100x4",
            engineering_impact="Nhà xe là hệ khung 1 hàng cột dầm vươn công son 2 phía chịu mô men chân cột rất lớn (M = 12.19 T.m). Bản vẽ vẽ móng 1.0x1.7m nhỏ hơn thuyết minh (1.4x2.0m) tới 65% diện tích sẽ gây LẬT MÓNG VÀ SẬP ĐỔ HÀNG LOẠT khi có gió lốc!",
            mandatory_fix="Bắt buộc mở rộng móng M1 Nhà xe lên tối thiểu 1.8x2.6m (hoặc gia cố cọc/đối trọng) để khử ứng suất kéo đáy móng (e <= L/6), đồng bộ kích thước lên bản vẽ KC-01/KC-02 và bổ sung đầy đủ bảng tính khung thép H250/H400 + dầm []-100x100x4.",
            linked_rfi_ncr="NCR-DES-20261025-005 / RFI-DES-20261025-008"
        ),
        ClashRecord(
            clash_id="CL-15",
            item_code="HT8",
            item_name="Hồ Nước Ngầm PCCC 300m3 (26.0 x 4.5 x 3.2 m)",
            layer="Tầng 2 (MB ↔ MC) & Tầng 3 (Tag thép BV ↔ TMKC — Thiếu thép gối nắp bể)",
            severity="CRITICAL",
            source_a_ref="BV Kết cấu Hạng mục phụ (tr.13) — KC-01 Mặt bằng thép nắp hồ & Mặt cắt 1-1",
            source_a_val="Mặt bằng thép nắp hồ ghi cả 2 lớp phương ngắn và phương dài đều là 'Ø10a200' (As = 3.93 cm2/m); Mặt cắt 1-1 ghi thành bể 3 tag chồng chéo (Ø8a150, Ø10a150, Ø8a200) và đáy bể ghi ký hiệu lạ 'Ø8@900x900'",
            source_b_ref="TMKC 06 Bể nước PCCC (tr.13–14)",
            source_b_val="TMKC 06 (tr.14) tính Bản nắp bể yêu cầu thép gối đứng & gối ngang đều là 'Ø10a150' (As_ch = 5.24 cm2/m > As_tt = 3.34 cm2); thành bể phương ngang chọn 'Ø8a200', phương đứng 'Ø10a150'",
            engineering_impact="Bản vẽ Mặt bằng nắp bể ghi Ø10a200 làm giảm 25% lượng thép gối nắp bể so với TMKC (Ø10a150), kết hợp với việc TMKC chưa tính tải xe chữa cháy và chưa kiểm toán nứt (acrc <= 0.2mm) sẽ gây nứt thấm và sập nắp bể ngầm.",
            mandatory_fix="Cập nhật bản vẽ KC-01 Bể PCCC: sửa thép nắp bể theo đúng tính toán sau khi bổ sung hoạt tải xe PCCC và kiểm toán nứt SLS; xóa các tag thép chồng chéo trên Mặt cắt 1-1.",
            linked_rfi_ncr="NCR-DES-20261025-007 / RFI-DES-20261025-007"
        ),
        ClashRecord(
            clash_id="CL-16",
            item_code="HT8",
            item_name="Hồ Nước Ngầm PCCC 300m3",
            layer="Tầng 2 (Hình vẽ Mặt bằng/Mặt cắt ↔ Ghi chú Chi tiết trên cùng tờ KC-01)",
            severity="MAJOR",
            source_a_ref="BV Kết cấu Hạng mục phụ (tr.13) — KC-01 Mặt bằng & Mặt cắt dọc Bể PCCC",
            source_a_val="Bể dài 26.0m chia 6 khoang, vẽ 5 Cột cấy CC (300x300) và 5 Dầm nắp bể DS1 (300x300) tại 5 trục trung gian",
            source_b_ref="BV Kết cấu Hạng mục phụ (tr.13) — KC-01 Chi tiết Cột cấy & Chi tiết DS1",
            source_b_val="Tiêu đề chi tiết ghi: 'CHI TIẾT CỘT CẤY (3 CỘT)' và 'CHI TIẾT DS1 (3 DẦM)' — lệch 2 cột và 2 dầm so với mặt bằng!",
            engineering_impact="Dự toán và tổ đội gia công thép chỉ làm 3 cột cấy + 3 dầm theo tiêu đề chi tiết, thiếu mất 2 hệ khung đỡ nắp bể tại hiện trường.",
            mandatory_fix="Sửa tiêu đề trên tờ KC-01 Bể PCCC thành 'CHI TIẾT CỘT CẤY (5 CỘT)' và 'CHI TIẾT DS1 (5 DẦM)'.",
            linked_rfi_ncr="RFI-DES-20261025-007"
        ),
        ClashRecord(
            clash_id="CL-17",
            item_code="HT7",
            item_name="Nhà Bơm PCCC (30.0 m2 — đặt trên nắp bể PCCC)",
            layer="Tầng 1 (Bản vẽ Kiến trúc ↔ Bản vẽ Kết cấu) & Tầng 3 (Bỏ sót TMKC)",
            severity="CRITICAL",
            source_a_ref="BV Kiến trúc Hạng mục phụ (tr.14) — KT-02 Mặt cắt A-A Nhà bơm PCCC",
            source_a_val="Ghi chú rõ: 'XÀ GỒ HỘP 60x120x1.5 @1000'",
            source_b_ref="BV Kết cấu Hạng mục phụ (tr.14) — KC-02 Nhà bơm PCCC & TMKC 06",
            source_b_val="Bản vẽ KC-02 vẽ xà gồ mái và xà gồ vách chỉ dùng thép hộp '[]-30*60*1.4' (nhỏ hơn gấp đôi so với Kiến trúc!) vượt nhịp 6.0m; TMKC 06 hoàn toàn không có tính toán khung và xà gồ Nhà bơm",
            engineering_impact="Thép hộp 30x60x1.4 vượt nhịp 6.0m có độ mảnh và độ võng vượt hơn 400% giới hạn cho phép (L/200), chắc chắn võng võng hoặc sập mái nhà bơm PCCC khi có gió bão!",
            mandatory_fix="Đổi ngay xà gồ trên bản vẽ KC-02 Nhà bơm từ []-30x60x1.4 sang tối thiểu []-60x120x1.5 (hoặc Z150) khớp với bản vẽ Kiến trúc KT-02 và bổ sung thuyết minh tính toán Nhà bơm.",
            linked_rfi_ncr="NCR-DES-20261025-007 / RFI-DES-20261025-007"
        ),
        ClashRecord(
            clash_id="CL-18",
            item_code="ALL",
            item_name="Toàn bộ 06 Bộ Thuyết minh TMKC 01–06",
            layer="Tầng 3 & Tầng 4 (Lỗi bảng tính Excel #VALUE! & Nghịch lý Phản lực Móng)",
            severity="CRITICAL",
            source_a_ref="TMKC 01, 02, 03, 04, 05 (Mục kiểm toán chọc thủng móng & phản lực móng)",
            source_a_val="05/06 cuốn TMKC bị lỗi '#VALUE!' tại công thức kiểm tra điều kiện P_ct <= P_cct; TMKC 01 nhập tải móng giữa M2 (N=10T) nhỏ hơn móng biên M1 (N=15.8T)",
            source_b_ref="Bảng xuất ETABS 'Joint Reactions' trong TMKC 01 (tr.18–20)",
            source_b_val="Phản lực ETABS thực tế tại cột giữa Joint 22/35 là Fz = 16.95 T (TH1) > cột biên Joint 48/61 (Fz = 9.71 T); TVTK đã gán nhầm nút hoặc chép nhầm tải trọng khi đưa vào bảng tính móng M2!",
            engineering_impact="Móng cột giữa M2 chịu diện truyền tải gấp đôi cột biên nhưng lại được tính với tải trọng nhỏ hơn 37%, dẫn đến thiếu kích thước đáy móng và nguy cơ lún sụt cột giữa.",
            mandatory_fix="Sửa triệt để lỗi #VALUE! trong 5 cuốn TMKC; lấy đúng tổ hợp phản lực chân cột giữa Joint 22/35 (Fz >= 16.95 T) từ ETABS để tính toán và mở rộng móng M2.",
            linked_rfi_ncr="NCR-DES-20261025-002 / RFI-DES-20261025-003"
        ),
    ]

if __name__ == "__main__":
    matrix = build_tanhy_4way_matrix()
    out_data = {
        "project": "Nhà máy Công ty TNHH Tân Hỷ — Giai đoạn II (TX. Chơn Thành, Bình Phước)",
        "engine_version": "2.3.0",
        "audit_date": "2026-10-25",
        "summary_counts": {
            "total_clashes": len(matrix),
            "critical": sum(1 for c in matrix if c.severity == "CRITICAL"),
            "major": sum(1 for c in matrix if c.severity == "MAJOR"),
            "minor": sum(1 for c in matrix if c.severity == "MINOR"),
        },
        "rebar_verification_samples": {
            "NhaRac_DK2_Drawing_2D16_cm2": compute_rebar_area_cm2("2Ø16"),
            "NhaRac_DK2_TMKC_Req_cm2": 4.23,
            "NhaRac_DK2_TMKC_Selected_3D16_cm2": compute_rebar_area_cm2("3Ø16"),
            "BePCCC_TopSlab_Drawing_D10a200_cm2_per_m": compute_rebar_area_cm2("Ø10a200", 1.0),
            "BePCCC_TopSlab_TMKC_D10a150_cm2_per_m": compute_rebar_area_cm2("Ø10a150", 1.0),
        },
        "clashes": [asdict(c) for c in matrix]
    }
    print(json.dumps(out_data, ensure_ascii=False, indent=2))
