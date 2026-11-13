---
name: SKILL_DUAL_AGENT_BRIDGE
version: 3.1.0
last_updated: 2026-11-07
description: "Giao thức và quy trình chuẩn điều phối làm việc song song hoặc luân phiên giữa Gemini (Antigravity) và Claude (Claude Code / Desktop). Đảm bảo tính nguyên tử của dữ liệu, loại bỏ xung đột file trên Google Drive, khóa phần vùng an toàn và kiểm toán chéo định lượng."
triggers:
  - "Khi người dùng yêu cầu bàn giao công việc giữa Gemini và Claude"
  - "Khi cần phối hợp 2 AI cùng làm việc đồng thời trên một dự án"
  - "Khi cần thẩm tra chéo độc lập (Red-Team Audit, Verification) giữa 2 Agent"
  - "Khi đồng bộ trạng thái qua .agents/memory/DUAL_AGENT_BUS.json hoặc DUAL_AGENT_HANDOFF_MEMO.md"
---

# 🛰️ SKILL_DUAL_AGENT_BRIDGE: CẦU NỐI ĐIỀU PHỐI ĐA TÁC TỬ (GEMINI ⚔️ CLAUDE)

> **Cơ sở vận hành:** Hệ thống Bus nguyên tử `.agents/memory/DUAL_AGENT_BUS.json` & Biên bản ca trực `.agents/memory/DUAL_AGENT_HANDOFF_MEMO.md`.  
> **Nguyên tắc cốt lõi:** Tuyệt đối không để 2 AI giẫm chân lên nhau (Zero-Collision), không thất thoát ngữ cảnh (Zero-Context-Leak), và nghiệm thu bằng số liệu cứng (Deterministic Criteria).

---

## 1. BA KỊCH BẢN PHỐI HỢP ĐỒNG THỜI (OPERATIONAL MODES)

Hệ thống hỗ trợ 3 chế độ cộng tác linh hoạt tùy theo tính chất công việc:

### 1.1 Kịch bản A: Luân phiên ca trực (Relay / Sequential Handoff)
- **Áp dụng:** Khi một tác tử hoàn thành một giai đoạn (Sprint/Phase) và cần bàn giao toàn bộ cho tác tử kia tiếp quản.
- **Quy trình:**
  1. **Agent hoàn thành:** Chạy lệnh `--auto` hoặc ghi nhận tệp đã sửa, chuyển trạng thái bus sang `PENDING`, chỉ định rõ `target_agent: "CLAUDE"` (hoặc `GEMINI`).
  2. **Agent tiếp nhận:** Kiểm tra bus (`--read`), kích hoạt nhận ca (`--claim`), trạng thái chuyển sang `IN_PROGRESS` và `current_holder: "<AGENT_NAME>"`.
  3. **Thực thi:** Làm theo danh sách `target_files` và hoàn thành từng mục trong `acceptance_criteria`.
  4. **Nghiệm thu:** Chạy `--complete` để đóng ca hoặc `--need-review` để mời đối tác kiểm tra chéo.

### 1.2 Kịch bản B: Làm việc song song có phân vùng (Partitioned Parallel Co-Working)
- **Áp dụng:** Khi cả Gemini và Claude cùng mở và làm việc trong cùng một phiên làm việc (ví dụ: Gemini phụ trách Backend/Calculators, Claude phụ trách Frontend/Docs).
- **Quy tắc bất khả xâm phạm:**
  - **Phân tách tập tệp (Disjoint Sets):** `target_files` của Gemini và `target_files` của Claude **TUYỆT ĐỐI KHÔNG GIAO NHAU**.
  - **Khóa cục bộ (Local File Lock):** Khóa `FileLock` đặt tại `%LOCALAPPDATA%/GoogleAIStudio/locks/` để đảm bảo khi một bên ghi dữ liệu thì bên kia không thể tranh chấp.
  - **Đồng bộ Bus:** Mỗi bên chỉ cập nhật phân đoạn phụ trách của mình vào bus.

### 1.3 Kịch bản C: Thẩm tra đối kháng & Độc lập (Red-Team Adversarial Audit)
- **Áp dụng:** Thẩm định thiết kế kết cấu, kiểm toán thuật toán tài chính (như Crypto-Gold Quant) hoặc review code an toàn trước khi commit.
- **Quy trình:**
  - **Agent 1 (Maker):** Triển khai tính năng, tạo file và ghi nhận log tính toán.
  - **Agent 2 (Breaker / Auditor):** Đóng vai trò phản biện, cố tình thử nghiệm các trường hợp biên (Edge cases), kiểm tra chuẩn TCVN/Eurocode/TypeScript types.
  - **Consensus Matrix:** Chỉ khi Agent 2 xác nhận `APPROVE` và không còn `divergenceFlags`, mã nguồn hoặc tài liệu mới được chốt phê duyệt chính thức.

---

## 2. QUY CHUẨN DỮ LIỆU BUS NGUYÊN TỬ (JSON SCHEMA v3.0)

File `.agents/memory/DUAL_AGENT_BUS.json` bắt buộc tuân thủ cấu trúc sau:

```json
{
  "project_context": {
    "project_code": "00_MANAGEMENT_QLTK",
    "project_purpose": "Mô tả ngắn gọn mục tiêu của dự án",
    "role_distribution": "Phân vai linh hoạt: Ai làm thiết kế, ai làm thẩm tra",
    "action_type": "DYNAMIC | RELAY | PARALLEL | AUDIT"
  },
  "last_updated_by": "GEMINI | CLAUDE",
  "timestamp": "ISO-8601 with timezone (e.g. 2026-11-07T09:30:00+07:00)",
  "handoff_status": "PENDING | IN_PROGRESS | COMPLETED | NEED_REVIEW",
  "current_holder": "GEMINI | CLAUDE | IDLE",
  "summary": "Tóm tắt súc tích các công việc đã làm trong lượt này",
  "artifacts_modified": [
    ".agents/tools/sync_bus.py",
    ".agents/memory/DUAL_AGENT_BUS.json"
  ],
  "next_action_for_partner": {
    "target_agent": "CLAUDE | GEMINI",
    "task_description": "Chỉ thị hành động cụ thể, không dùng ngôn ngữ mơ hồ",
    "target_files": [
      "src/components/MyComponent.tsx",
      "docs/SPEC.md"
    ],
    "acceptance_criteria": [
      "Tiêu chí định lượng 1 (ví dụ: Test suite PASS 100%)",
      "Tiêu chí định lượng 2 (ví dụ: Không còn lỗi TypeScript)"
    ],
    "command": "Câu lệnh hoặc hướng dẫn ngắn để đối tác bắt đầu ngay"
  },
  "Verification_Status": "CONFIRMED_AND_HANDED_OFF | UNVERIFIED"
}
```

---

## 3. NGUYÊN TẮC KỸ THUẬT CỨNG (HARD RULES)

1. **Chuẩn hóa Đường dẫn Tương đối POSIX (POSIX Relative Paths):**
   - 100% tệp trong `artifacts_modified` và `target_files` bắt buộc dùng định dạng `path/to/file.ext` (dấu `/`, bắt đầu từ thư mục gốc).
   - **CẤM:** Dùng đường dẫn tuyệt đối chứa ổ đĩa (`G:\...`, `D:\...`) hoặc dấu gạch chéo ngược `\` (tránh lỗi JSON escape và tiết kiệm context).

2. **Cơ chế Khóa Nguyên tử Không phụ thuộc Cloud (Local AppData Lock):**
   - Tệp khóa `dual_agent_bus.lock` được đặt ở `%LOCALAPPDATA%`, tuyệt đối không đặt trên ổ Google Drive để tránh deadlock do độ trễ đồng bộ mạng.

3. **Ghi tệp an toàn (Atomic Write with Fsync):**
   - Mọi thao tác ghi bus đều ghi qua tệp tạm ẩn `.{stem}.tmp.{pid}`, gọi `os.fsync()`, rồi mới đổi tên `os.replace()`.

4. **Xử lý Xung đột Google Drive (Drive Conflict Hygiene):**
   - Trước khi nhận ca hoặc khi kết thúc ca, tự động quét các file có đuôi `(1)`, `(2)`. So sánh mtime và hash để bảo tồn bản sửa đổi mới nhất, không xóa nhầm dữ liệu.

---

## 4. HỆ THỐNG LỆNH CLI ĐIỀU PHỐI (`sync_bus.py`)

Công cụ điều phối đặt tại `.agents/tools/sync_bus.py`:

```bash
# 1. Đọc trạng thái hiện tại của Bus:
python .agents/tools/sync_bus.py --read

# 2. Agent nhận ca (Khóa bus, ngăn Agent kia ghi đè):
python .agents/tools/sync_bus.py --claim --agent CLAUDE

# 3. Hoàn tất ca làm việc và mở khóa:
python .agents/tools/sync_bus.py --complete --agent CLAUDE --summary "Đã hoàn tất tính toán dầm D1"

# 4. Yêu cầu Agent đối tác kiểm tra / thẩm tra chéo:
python .agents/tools/sync_bus.py --need-review --agent CLAUDE

# 5. Tự động bàn giao ca có tiêu chí nghiệm thu:
python .agents/tools/sync_bus.py --auto --sender GEMINI --target CLAUDE \
    --project 00_MANAGEMENT_QLTK --purpose "Đồng bộ giao thức Bus v3.1" \
    --task "Kiểm tra chéo và chạy kiểm thử tự động" \
    --criteria "100% test Suite PASS;Không còn file xung đột Drive" --confirm

# 6. Quét và dọn dẹp file xung đột Google Drive an toàn:
python .agents/tools/sync_bus.py --scan-conflicts
python .agents/tools/sync_bus.py --clean-conflicts --confirm
```

---

## 5. MẪU LỆNH CHUYỂN TIẾP NHANH (PROMPT TEMPLATES)

### Khi Gemini bàn giao sang Claude:
> *"Claude ơi, tôi đã hoàn tất công việc ở phần của mình. Trạng thái bus đã cập nhật tại `.agents/memory/DUAL_AGENT_BUS.json`. Bạn hãy chạy `python .agents/tools/sync_bus.py --claim --agent CLAUDE` để nhận ca và đối soát các tiêu chí nghiệm thu trong `.agents/memory/DUAL_AGENT_HANDOFF_MEMO.md` nhé."*

### Khi Claude bàn giao sang Gemini:
> *"Gemini ơi, tôi đã thực hiện xong các hạng mục được giao và xác nhận tiêu chí nghiệm thu. Tôi đã chuyển trạng thái sang `COMPLETED`. Bạn hãy kiểm tra lại bus qua `python .agents/tools/sync_bus.py --read` để tiếp tục tiến trình nhé."*

