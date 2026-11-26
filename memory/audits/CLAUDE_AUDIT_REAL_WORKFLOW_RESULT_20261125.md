# KẾT QUẢ THẨM TRA THỰC TẾ — CLAUDE

- **Brief:** `BRIEF_CLAUDE_AUDIT_REAL_WORKFLOW_20261125.md`
- **Ngày kiểm tra:** 2026-11-25
- **Workspace:** `G:\My Drive\Google AI Studio`
- **Phạm vi:** kiểm chứng thực tế 6 hạng mục; không sửa BUS và 9 tệp khóa v1.0.

## 0. Tóm tắt kết luận

| Hạng mục | Kết quả thực tế |
|---|---|
| Bootstrap doctor | **PASS** — tất cả mục kiểm tra của `doctor.ps1 -FailClosed` đạt |
| Wrapper fail-closed | **PASS** — stub-only exit `125`; cache Python hợp lệ chạy được |
| Runtime Python | **WARN/FAIL vận hành** — `py -3` là Python 3.14.5 thiếu toàn bộ dependency CAD/MCP; `py -3.12` là 3.12.7 đầy đủ |
| Hook production v1.0 | **WARN** — `.agents/hooks.json` và `.claude/settings.json` gọi trực tiếp `py -3`, không qua wrapper |
| MCP dce-cad | **FAIL với py -3**; **PASS với py -3.12** — JSON-RPC `initialize` trả kết quả hợp lệ |
| Release manifest v1.0 | **PASS** — hash + CRLF khớp |
| `manifest_tool.py bus-checksum --write` | **FAIL logic** — in checksum nhưng không tạo snapshot |
| BUS/pointer/cache isolation | **PASS** — pointer khớp byte với handoff memo; cache còn nguyên |
| Fast regression | **PASS** — 27/27 suite đạt |
| Zero-white-text audit | **PASS** — 527 files/29 modules, 0 warnings |

**Không sửa:** `.agents/memory/DUAL_AGENT_BUS.json`, `_CA_HIEN_TAI.md`, và 9 tệp khóa SHA-256 trong manifest v1.0.

## 1. Bootstrap và runtime máy trạm

### 1.1 `doctor.ps1 -FailClosed`

Đã chạy:

```text
powershell -ExecutionPolicy Bypass -File bootstrap/doctor.ps1 -FailClosed
```

Kết quả: **exit 0**. Các mục `Workspace`, `Hook wrapper`, `Python interpreter`, `Antigravity JSON`, `Claude JSON`, `BUS readable`, `No legacy hook interpreter`, `Hook interpreter configured` đều **PASS**. Ma trận wrapper cũng báo:

```text
[PASS] WindowsApps-stub-only -> 125 (fail-closed)
[PASS] real-python -> 0 (allow)
```

### 1.2 Machine manifest và cache

`%LOCALAPPDATA%\GoogleAIStudio\machine.json` tồn tại, đang ghi:

- `machine_id`: `TIENDUC`
- `python_version`: `3.12.7`
- `python_executable`: `C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe`
- `mcp`, `ezdxf`, `shapely`, `matplotlib`: `present: true`
- AutoCAD Core Console: `true`
- ODA: `false`

`%LOCALAPPDATA%\GoogleAIStudio\python_exe.cache` tồn tại và trỏ đúng tới Python 3.12.7.

### 1.3 Wrapper

Đã tạm thời di chuyển cache trong vùng kiểm tra và khôi phục ngay sau đó:

- Chỉ có stub WindowsApps: **exit 125**.
- `PYTHON_EXECUTABLE` trỏ vào stub WindowsApps: **exit 125**.
- Cache/Python hợp lệ: wrapper khởi chạy được hook; payload hợp lệ trả **exit 0**.
- Thời gian gọi wrapper thực tế khoảng **0.18 giây** với payload hợp lệ.

### 1.4 Lỗi mới xác nhận trong PowerShell 5.1

`bootstrap/setup_machine.ps1` và `bootstrap/repair.ps1` đang là UTF-8 **không BOM**, trong khi máy đọc PowerShell 5.1 theo code page 1252. Các chuỗi có ký tự em-dash UTF-8 (`E2 80 94`) bị giải mã sai thành dấu nháy đóng chuỗi.

Kết quả parse thực tế:

- `setup_machine.ps1`: **4 parse errors**.
- `repair.ps1`: **1 parse error**, tại dòng điều kiện `if ($setupRc -ne 0 -or $docRc -ne 0) {`.
- `setup_machine.ps1 -DryRun` không chạy được do parser error.

Đây là lỗi cần đưa vào phạm vi cắt `release v1.1`; không sửa trong audit này.

## 2. Hook, Python 3.14/3.12 và MCP

### 2.1 Phiên bản và dependency

| Lệnh | Interpreter thực tế | `mcp` | `ezdxf` | `shapely` | `matplotlib` | `pymupdf` |
|---|---|---:|---:|---:|---:|---:|
| `py -3` | Python 3.14.5 | thiếu | thiếu | thiếu | thiếu | thiếu |
| `py -3.12` | Python 3.12.7 | OK | OK | OK | OK | OK |

### 2.2 Hook production

`.agents/hooks.json` và `.claude/settings.json` đều gọi trực tiếp:

```text
py -3 -I -X utf8 -B -S ...hook.py
```

Chúng không gọi `bootstrap/hook_bootstrap.cmd`. Hook safety và dual-bus hiện vẫn chạy được với Python 3.14 vì phần logic đó chủ yếu dùng thư viện chuẩn. Tuy nhiên cấu hình này không bảo đảm cho các hook/MCP cần dependency ngoài chuẩn.

### 2.3 MCP dce-cad

- Chạy theo cấu hình `.mcp.json` bằng `py -3`: **FAIL** ngay tại `from mcp.types import ImageContent` với `ModuleNotFoundError: No module named 'mcp'`.
- Chạy bằng `py -3.12`: **PASS**.
- Gửi JSON-RPC `initialize` bằng 3.12 trả response hợp lệ, server `dce-cad`, protocol `2024-11-05`.
- `C:\Users\ADMIN\.gemini\antigravity\mcp_config.json`: **chưa tồn tại**, phù hợp trạng thái chưa chạy `setup_machine.ps1 -RegisterMcp`.

## 3. Release manifest và registry

### 3.1 v1.0 verify

Đã chạy:

```text
py -3 -B release/manifest_tool.py verify --release-id v1.0
```

Kết quả:

```text
VERIFY PASS: release v1.0 khớp hash + CRLF.
```

Verify không truyền `--release-id` cũng **PASS**, chọn release hiện có `v1.0`.

### 3.2 `make`

`make --tests-passed 27/27` tạo được manifest timestamped. Audit đã xóa đúng thư mục timestamped thử nghiệm sau khi kiểm tra; không để lại artifact test trong `release/`.

### 3.3 Lỗi `bus-checksum --write`

Đã chạy:

```text
py -3 -B release/manifest_tool.py bus-checksum --write
```

Kết quả in checksum nhưng **không tạo** `release/bus_checksum.json`. Nguyên nhân: parser thủ công trong `manifest_tool.py` chỉ nhận option có giá trị kế tiếp; bare flag `--write` không được đưa vào `args`, nên `args.get("write")` là falsey và nhánh ghi không chạy.

Đây là lỗi logic cần sửa ở v1.1. Lệnh không sửa BUS; BUS chỉ được đọc và băm.

### 3.4 Registry

`release/machine_registry.json` vẫn chỉ có bản ghi cũ:

- `machine_id`: `LAPTOPTIENDUC`
- `python_version`: `3.11.9`

Chạy thử `register-machine --doctor-status PASS` nhận đúng machine manifest và tạo bản ghi `TIENDUC / Python 3.12.7`; audit đã khôi phục registry về byte/nội dung ban đầu.

## 4. Chống ô nhiễm BUS và isolation

Đã kiểm tra guard trong `sync_bus.py` khi ghi pointer:

- `ACTIVE_POINTER_PATH` chỉ được ghi khi đường dẫn resolved nằm trong workspace qua `is_relative_to`.
- Điều kiện cũng yêu cầu memo đích đúng `MEMO_PATH`.

Kiểm tra sau các test:

```text
_CA_HIEN_TAI.md == DUAL_AGENT_HANDOFF_MEMO.md: True
memo_bytes: 7022
pointer_bytes: 7022
python_exe.cache: tồn tại, trỏ Python312
```

SHA-256 BUS quan sát được: `422a1d5380a5224527c9a0883a12daa4ce51799d2d460fd95efa3891b2e74282`.

## 5. Test và hậu quả dọn dẹp

### 5.1 Fast runner

Đã chạy:

```text
py -3.12 -B .agents/tests/run_all_tests.py --fast
```

Kết quả: **27/60 suite PASS**, không có suite fail. Tổng thời gian quan sát: 92.47 giây.

Các suite 19 (Dual-Agent Bridge), 34 (Bootstrap Matrix), 35 (MCP installer), 36 (Release manifest) đều PASS trong fast runner.

Một lần gọi trực tiếp theo tên `test_dual_agent_bridge.py`, `test_cognitive_and_control_systems.py`, `test_bootstrap_matrix.py` không chạy được vì các tên file đó không tồn tại ở đường dẫn `.agents/tests/`; test runner chính thức đã ánh xạ các kiểm tra tương ứng trong các suite 19, 16 và 34. Đây là **WARN về tên tài liệu/brief**, không phải test failure của runner chính thức.

### 5.2 Zero-white-text

Đã chạy:

```text
py -3.12 -B .agents/tools/audit_zero_white_text.py .agents
```

Kết quả: **PASS**, 527 files trên 29 modules, **0 warnings**.

### 5.3 Suite registry

`_collect_tests.py` parse được **60/60 suite**, không có `unparsed_suites` trong quá trình parse. Lần kiểm tra API phụ trợ gọi nhầm tên hàm `load_cached_result` không tồn tại; không ảnh hưởng kết quả parse/runner.

## 6. Rà soát tồn đọng

- `Global_Dispatcher/intent_classifier.py`: rule `.agents` hiện diện tại nhánh phân loại SYSTEM_UPGRADE; kiểm tra static không phát hiện lỗi trong phạm vi brief.
- `cad_plan_engine.py`: tồn tại guard import `ezdxf`; nếu thiếu dependency, module đặt `ezdxf = None` để trì hoãn xử lý. Runtime đầy đủ trên 3.12.
- `_collect_tests.py`: parse được 60/60 suite; danh sách parser và `unparsed_suites` hoạt động theo thiết kế.

## 7. Những gì ĐÃ CHẠY THẬT ĐƯỢC NGAY

1. `doctor.ps1 -FailClosed` đạt exit 0.
2. Wrapper fail-closed chặn stub WindowsApps bằng exit 125.
3. Wrapper chạy được với Python 3.12.7 từ cache.
4. Hook safety và dual-bus chạy được với payload hợp lệ.
5. MCP dce-cad chạy và handshake được bằng Python 3.12.7.
6. Manifest v1.0 xác minh đúng hash và CRLF.
7. Fast suite 27/27 đạt.
8. Zero-white-text audit đạt 0 warnings.
9. BUS pointer và cache không bị ô nhiễm sau kiểm tra.

## 8. Những điểm ĐANG TẮC / CẦN XỬ LÝ

1. `py -3` mặc định là Python 3.14.5 nhưng thiếu dependency; MCP dce-cad không khởi động được.
2. `.mcp.json` đang dùng `py -3`, nên kênh MCP thực tế bị lỗi trên máy hiện tại.
3. Hook config production gọi trực tiếp `py -3`, không tận dụng cache/wrapper.
4. `setup_machine.ps1` và `repair.ps1` lỗi parse PowerShell 5.1 do UTF-8 không BOM chứa em-dash.
5. `manifest_tool.py bus-checksum --write` không ghi snapshot vì parser không hỗ trợ bare flag.
6. Registry còn bản ghi cũ `LAPTOPTIENDUC / 3.11.9`, chưa phản ánh máy `TIENDUC / 3.12.7`.
7. Brief nêu tên ba file test không khớp tên file hiện tại; cần chuẩn hóa tài liệu hoặc dùng suite chính thức.

## 9. Checklist tối thiểu để cắt release v1.1 an toàn

- [ ] Sửa encoding `setup_machine.ps1` và `repair.ps1` thành UTF-8 có BOM hoặc loại ký tự gây vỡ parser; chạy lại parse và `-DryRun` trên PowerShell 5.1.
- [ ] Sửa parser `manifest_tool.py` để bare flags (`--write`, và các flag tương tự) được ghi nhận đúng; thêm regression test xác nhận `bus_checksum.json` được tạo.
- [ ] Quyết định chuẩn runtime: dùng wrapper/cache hoặc pin MCP/hooks vào Python 3.12.7 có dependency; không để `py -3` trỏ 3.14 thiếu module.
- [ ] Chạy `setup_machine.ps1 -RegisterMcp` sau khi sửa encoding; xác nhận tạo `C:\Users\ADMIN\.gemini\antigravity\mcp_config.json` và handshake MCP bằng client thực.
- [ ] Cập nhật/đăng ký registry cho `TIENDUC / Python 3.12.7`, nhưng không xóa lịch sử nếu chính sách cần lưu máy cũ.
- [ ] Chạy đủ 60/60 suite; đối chiếu báo cáo `1088 passed / 0 failed / 0 stale-claims`.
- [ ] Chạy lại zero-white-text audit, bootstrap matrix, BUS isolation; xác nhận `_CA_HIEN_TAI.md` byte-equal handoff memo và cache còn tồn tại.
- [ ] Tạo manifest v1.1 và verify hash/CRLF; không sửa BUS, không claim hoặc complete ca `03_Sprint2_KetQua_NeChu_CAD`.

## 10. Kết luận độc lập

**v1.0 đạt các kiểm tra hiện có**, nhưng **chưa sẵn sàng cắt v1.1** nếu chưa xử lý ba điểm chặn thực tế: parser PowerShell 5.1, chọn Python/dependency cho MCP, và bare flag `bus-checksum --write`. Các phát hiện trên chỉ được liệt kê; không chỉnh sửa tệp khóa hoặc trạng thái BUS trong ca audit này.
