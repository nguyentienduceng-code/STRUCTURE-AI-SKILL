# Virtual Drive Guard — MCP CAD

Triển khai ngày 2026-11-14 tại lớp adapter; engine CAD giữ nguyên.

## Vùng I/O

- Preview PNG, cache matplotlib và temporary files của thư viện nằm dưới
  `%TEMP%/dce-cad` sau khi kiểm tra ổ đĩa. Mặc định trên máy này là
  `C:/Users/ADMIN/AppData/Local/Temp/dce-cad`.
- `DCE_CAD_SCRATCH_ROOT` cho phép chọn thư mục khác. Giá trị không an toàn
  tự chuyển về local Temp. Không tìm được thư mục an toàn thì từ chối ghi.
- Chỉ chấp nhận đường dẫn tuyệt đối trên C:/D:, loại fixed và NTFS/ReFS.
  Chặn UNC, device path, ADS, traversal, reparse point/junction, thư mục có tên
  OneDrive/Google Drive/Dropbox và các root OneDrive khai báo trong môi trường.
- Không chỉ dựa vào `GetDriveTypeW`: Google Drive G: trên máy này cũng trả
  `DRIVE_FIXED`. Kiểm tra lại đường dẫn sau resolve trước khi ghi.
- Khởi tạo guard trước khi import ezdxf/matplotlib. Chuyển TEMP/TMP/TMPDIR và
  MPLCONFIGDIR sang local; tắt Python bytecode cache bằng `-B` và runtime flag.
- Phiên `edit_entity` trên Drive được ánh xạ ổn định bằng SHA-256 sang
  `sessions/`. Caller có thể dùng tên cũ hoặc `session_dir` thực tế trả về.
  HEAD, candidate, revision DXF, SVG và khóa phiên đều nằm local.
- DXF nguồn chỉ đọc. `render_cad_plan` và `resolve_cad_collisions` tạo DXF UUID
  local; đường dẫn yêu cầu chỉ là gợi ý. Caller đọc `output_dxf` thực tế.
  Xuất bản bản sao sản phẩm sang thư mục bàn giao là bước riêng được User cho phép.
  `pdf_path` của generator là PDF đầu vào, không phải nơi xuất file.

## Vòng đời preview

1. Gọi `render_preview(dxf_path, ...)`. Mỗi lần có UUID riêng.
2. Đọc `preview_id` và `output_png` từ kết quả. `out_png` chỉ giữ vai trò gợi ý
   tương thích; không ghi file tại đường dẫn đó, kể cả khi nó nằm trên ổ local.
3. Ưu tiên gọi `consume_preview(preview_id)`. MCP trả `ImageContent` chứa PNG
   base64 đã nạp đầy đủ vào bộ nhớ và đóng file, sau đó xóa PNG local.
   Vision kiểm tra ảnh trong response mà không cần giữ file trên đĩa.
4. Nếu client đọc trực tiếp `output_png`, gọi `release_preview(preview_id)`
   sau khi kiểm tra hoặc hủy. Python caller dùng `preview_for_vision(...)`
   làm context manager để dọn trong `finally`, kể cả khi Vision báo lỗi.
5. CLI hỗ trợ `--release <preview_id>` sau khi đọc ảnh.

Token đã consume không đọc lại được. Preview hoàn thành bị bỏ quên có TTL
24 giờ, được quét khi cấp preview mới. Preview đang render không bị quét.
Phiên sửa CAD và lịch sử revision không bị TTL xóa.

Lỗi render được dọn ngay; figure matplotlib được đóng trong `finally`.
Các lượt render dùng chung khóa do pyplot có trạng thái toàn tiến trình.
Dọn dẹp chỉ unlink hai file đã biết (`preview.png`, `.ready`), rồi rmdir
thư mục UUID rỗng; không xóa đệ quy theo đường dẫn caller gửi vào.
Khóa local được thử lại ba lần. Nếu vẫn lỗi, trả `CLEANUP_PENDING` thay vì
báo thành công; gọi lại `release_preview` sau khi ứng dụng giữ file nhả khóa.

## Kiểm chứng

```powershell
python -B 'G:/My Drive/Google AI Studio/.agents/tests/run_all_tests.py' --fast
python -B 'G:/My Drive/Google AI Studio/.agents/tests/run_all_tests.py' --suite 18 --suite 28
```

Suite 28 kiểm tra guard, render thật toàn layout/crop, lỗi render, giải phóng
figure, cleanup/TTL, junction, UNC/traversal, biến môi trường trỏ Drive,
allocation đồng thời, phiên sửa và revision lock, kết nối MCP stdio thật.

## Giới hạn của kết luận

Guard loại bỏ việc ghi scratch MCP CAD lên Google Drive trong các luồng trên.
Đây không phải sandbox cấp hệ điều hành; không chống tiến trình có quyền trên
máy cố tình thay mount/junction giữa lúc kiểm tra và ghi. NTFS/fixed không xác
nhận phần cứng là SSD. Thư mục local do người vận hành cấu hình phải nằm ngoài
các thư mục tự đồng bộ tùy chỉnh không khai báo với guard.

Không cam kết mọi `WinError 32` của Windows biến mất: ứng dụng khác vẫn có thể
giữ file local; DXF đầu vào/đầu ra lâu dài trên Drive vẫn chịu cơ chế của Drive.
Không có sự kiện MCP tự báo “Vision đã suy luận xong”; `consume_preview` giải
phóng file sau khi chuyển ảnh vào response. Client đọc file trực tiếp phải
release hoặc dùng context manager. TTL là quét khi có yêu cầu mới, không phải
dịch vụ nền, và không tự dọn thư mục render dang dở do tiến trình bị kill.
