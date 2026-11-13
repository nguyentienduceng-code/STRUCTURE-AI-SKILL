import hashlib
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent
AGENTS = OUT.parents[2]
ROOT = AGENTS.parent
sys.path.insert(0, str(AGENTS/'tools'))
import sync_bus

def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))

full, fast = read('full/timings.json'), read('fast/timings.json')
structure, probes = read('structure_evidence.json'), read('bus_registry_evidence.json')
assert full['all_passed'] and full['selected_suites'] == 27
assert fast['all_passed'] and probes['ownership_probe']['ownership_preserved']
assert not probes['registry']['issues'] and not probes['registry']['warnings']
assert not structure['syntax_errors']
assert not [p for p in structure['windows_path_literals'] if 'Google AI Studio' in p['value']]
assert sync_bus.WORKSPACE_ROOT == ROOT
assert (AGENTS/'tools/sync_bus.py').read_bytes() == (AGENTS/'skills/SKILL_DUAL_AGENT_BRIDGE/scripts/sync_bus.py').read_bytes()
archives = []
for path in sorted((AGENTS/'_references_archived').glob('*.zip')):
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None
        members = [{'path': entry.filename, 'bytes': entry.file_size,
                    'sha256': hashlib.sha256(archive.read(entry)).hexdigest()}
                   for entry in archive.infolist() if not entry.is_dir()]
    archives.append({'archive': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'files': members})
assert len(archives) == 7
(AGENTS/'_references_archived/verified_manifest.json').write_text(json.dumps({
    'scope': 'Verified current archive contents; no claim of completeness against the pre-archive repositories.',
    'archives': archives}, indent=2), encoding='utf-8')
summary = {'timestamp': datetime.now().astimezone().isoformat(), 'status': 'COMPLETED',
           'fixed_findings': ['F01', 'F02', 'F03', 'F04', 'F05'],
           'full_passed': 27, 'full_seconds': full['wall_seconds'], 'fast_passed': 17,
           'fast_seconds': fast['wall_seconds'], 'verified_archives': 7, 'recovered_rvt_entries': 663,
           'registry_issues': 0, 'registry_warnings': 0,
           'limitation': 'All bytes and local entries present in the damaged ZIP were recovered. Completeness before the original archive was created is unknown.'}
report = f'''# Khắc phục F01–F05 — CODEX

Ngày: {summary['timestamp']}

Đã sửa năm lỗi trong biên bản STRUCTURE_CODEX_20261113. Full PASS 27/27
({full['wall_seconds']:.2f}s), fast PASS 17/17 ({fast['wall_seconds']:.2f}s).

| Lỗi | Cách sửa | Kiểm chứng |
|---|---|---|
| F01 — ZIP hỏng | Dựng lại bảng chỉ mục rvt-mcp.zip từ 663 local entries | Toàn bộ byte đầu vào được xử lý; CRC và SHA-256 từng entry khớp; 7/7 ZIP hiện đọc được |
| F02 — nhận đè ca | Kiểm holder bên trong FileLock trước claim/complete/review | Tác tử khác bị từ chối, cùng holder được nhận lại; hai subprocess tranh ca chỉ một bên thắng |
| F03 — root/memory | Dò project root chứa .agents, dùng get_bus_paths cho quét memory, sinh đường dẫn memo động | Cả hai entry points cho cùng root và .agents/memory/DUAL_AGENT_BUS.json; test cwd lồng nhau, bên ngoài và layout legacy |
| F04 — đường dẫn ổ G cố định | CAD yêu cầu input/output rõ ràng, template theo __file__; demo MS Project yêu cầu output rõ ràng | Không còn 8 literal workspace trong ba entrypoints; CLI thiếu output thoát 2 và không tạo file |
| F05 — registry CAD | Thêm path tương đối, validator và discovery cùng dùng path, khai báo module nội bộ | Registry 0 lỗi/0 cảnh báo; đường dẫn discovery tồn tại |

## ZIP có cần thiết không?

Các ZIP là mã nguồn tham khảo lưu trữ, không cần cho hoạt động hiện tại của tools
production hoặc bộ 27 suites. Không cần giải nén để chạy hệ thống. Giữ lại giúp
tra cứu/tích hợp Revit sau này và bảo toàn lịch sử; chúng không phải bản cài Revit
đã được kích hoạt. Lượt sửa này không cài đặt hay chạy code trong các ZIP.

Bản rvt-mcp bị thiếu central directory/EOCD. Tất cả 663 local entries còn trong
1.877.086 byte đều giải nén và kiểm CRC được. Đã tái tạo ZIP, đọc lại từng entry
và kiểm SHA-256. Bản gốc được giữ tại `rvt-mcp.original.damaged`, không bị xóa.
SHA-256 bản phục hồi: `26729ac2b5d28bd374f30ec8dbc551f5f2df0476c03e6c29c82a177f9a21aa81`.

Manifest `../../.. /_references_archived/rvt-mcp.manifest.json` (bỏ khoảng trắng
trong đường dẫn mô tả) ghi từng entry và checksum. Manifest chuẩn tại
`.agents/_references_archived/verified_manifest.json` ghi cả 7 ZIP hiện tại.
Tổng kiểm kê hiện tại là 2.969 file; không đủ bằng chứng để xác nhận con số 3.739
của lần nén trước. Không đánh đồng khôi phục mọi entry còn hiện diện với khôi
phục đầy đủ repository trước khi nén. README lưu trữ đã ghi rõ giới hạn này.

## Kiểm thử và phạm vi

- Suite 19 tăng từ 3 lên 7 tests, bổ sung kiểm quyền sở hữu, race hai tiến trình,
  workspace mới và đường dẫn legacy; vẫn nằm trong bộ 27 suites.
- `full/` lưu log từng suite và timings.json. `fast/` lưu lần xác nhận fast.
- `structure_evidence.json`: 14 skills, 222 nguồn Python không lỗi cú pháp,
  archive CRC, root resolver và rà literal đường dẫn.
- `bus_registry_evidence.json`: tái hiện lại lỗi cũ đã sửa trên bus tạm.
- `entrypoints.json`: CLI từ cwd ngoài dự án, không ghi vào dự án mẫu.

Smoke CLI phát hiện thêm import không dùng `import_from_msproject_xml` trỏ tới
hàm không tồn tại. Đã bỏ import này. Full được chạy trước sửa import nhỏ cuối
cùng; CLI smoke và fast được chạy lại sau đó. Không chạy pipeline MS Project
có tạo MPP qua COM vì yêu cầu kiểm thử hiện tại không cần mở ứng dụng GUI.
Các API XML/export đang dùng được giữ nguyên; không tuyên bố bổ sung chức năng
import XML vốn chưa được engine triển khai.

Bus/memo được cập nhật nguyên tử cho trạng thái COMPLETED và trỏ báo cáo này.
Những giới hạn hiệu năng từ ca tối ưu trước không nằm trong năm lỗi của lượt
sửa này và không được ngầm đánh dấu là đã giải quyết.
'''
report = report.replace('`../../.. /_references_archived/rvt-mcp.manifest.json` (bỏ khoảng trắng\ntrong đường dẫn mô tả)', '`.agents/_references_archived/rvt-mcp.manifest.json`')
(OUT/'REPORT.md').write_text(report, encoding='utf-8')
(OUT/'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
changed = ['tools/sync_bus.py', 'skills/SKILL_DUAL_AGENT_BRIDGE/scripts/sync_bus.py',
    'skills/SKILL_DUAL_AGENT_BRIDGE/SKILL.md', 'skills/SKILL_DUAL_AGENT_BRIDGE/templates/DUAL_AGENT_HANDOFF_MEMO_TEMPLATE.md',
    'skills/SKILL_DUAL_AGENT_BRIDGE/tests/test_dual_agent_bridge.py', 'tests/run_all_tests.py',
    'skills/Technical_Illustrator/cad_integration/cad_plan_engine.py',
    'skills/Technical_Illustrator/cad_integration/dce_dxf_generator.py',
    'skills/Project_Manager/scripts/msproject_bridge.py', 'skills/Technical_Illustrator/scripts/registry.json',
    'skills/Design_Evaluation/scripts/validate_registry.py', 'skills/Design_Evaluation/modules/script_discovery.py',
    '_references_archived/rvt-mcp.zip', '_references_archived/rvt-mcp.manifest.json',
    '_references_archived/verified_manifest.json', '_references_archived/README.md']
with sync_bus.FileLock(sync_bus.LOCK_PATH):
    data = json.loads(sync_bus.BUS_PATH.read_text(encoding='utf-8'))
    assert data['current_holder'] == 'CODEX'
    data.update(last_updated_by='CODEX', timestamp=summary['timestamp'], handoff_status='COMPLETED',
                current_holder='IDLE', Verification_Status='FIXES_VERIFIED_PASS', repair_verification=summary,
                summary=f"Fixed F01-F05. Recovered 663 rvt-mcp ZIP entries; 7/7 archives CRC verified. Ownership race/holder guards pass. Root/memory paths corrected. Fixed absolute CLI defaults and CAD registry. Full 27/27 PASS ({full['wall_seconds']:.2f}s), fast 17/17 PASS ({fast['wall_seconds']:.2f}s). Historical pre-archive completeness is unknown; original damaged ZIP preserved.",
                artifacts_modified=['.agents/'+name for name in changed]+[
                    '.agents/memory/audits/STRUCTURE_REPAIR_CODEX_20261113/REPORT.md',
                    '.agents/memory/audits/STRUCTURE_REPAIR_CODEX_20261113/summary.json',
                    '.agents/memory/DUAL_AGENT_BUS.json', '.agents/memory/DUAL_AGENT_HANDOFF_MEMO.md'])
    data['next_action_for_partner'].update(target_agent='GEMINI',
        task_description='F01-F05 repaired and verified. Optional independent review of repair report; archive manifest certifies present contents only, not historical repository completeness.',
        target_files=[], command='Read .agents/memory/audits/STRUCTURE_REPAIR_CODEX_20261113/REPORT.md')
    valid, reason = sync_bus.validate_bus_payload(data)
    assert valid, reason
    sync_bus._atomic_write_json(sync_bus.BUS_PATH, data)
    sync_bus.generate_handoff_memo(data, sync_bus.MEMO_PATH)
print(json.dumps(summary, ensure_ascii=False, indent=2))
