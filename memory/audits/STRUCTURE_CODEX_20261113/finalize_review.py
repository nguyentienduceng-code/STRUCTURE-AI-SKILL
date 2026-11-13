"""Publish independent review evidence, without altering production code."""
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

OUT = Path(__file__).resolve().parent
AGENTS = OUT.parents[2]
ROOT = AGENTS.parent
os.environ['DUAL_AGENT_WORKSPACE'] = str(ROOT)
sys.path.insert(0, str(AGENTS/'tools'))
import sync_bus

def read(name):
    return json.loads((OUT/name).read_text(encoding='utf-8'))

evidence = read('structure_evidence.json')
probes = read('bus_registry_evidence.json')
full = read('full_isolated/timings.json')
first = read('full/timings.json')
fast = read('fast/timings.json')
assert full['all_passed'] and full['selected_suites'] == 27
assert fast['all_passed'] and fast['selected_suites'] == 17
assert all(hashlib.sha256((AGENTS/path).read_bytes()).hexdigest() == digest
           for path, digest in evidence['sources'].items()), 'Source changed during independent review'
findings = [
    {'id': 'F01', 'priority': 'P1', 'title': 'Archive rvt-mcp.zip không hợp lệ',
     'location': '.agents/_references_archived/rvt-mcp.zip',
     'evidence': '1,877,086 bytes; hai lần đọc cùng SHA-256 b135a0190e40c3b7936f3c3ec93c42f4037035d72b6f5f1333abcd52a60ce073; không có EOCD; zipfile.BadZipFile.',
     'impact': 'Không thể xác nhận phục hồi toàn bộ thư viện đã nén hoặc xác minh con số 3.739 tệp.',
     'recommendation': 'Khôi phục từ nguồn/backup tin cậy, tạo ZIP mới, kiểm CRC và manifest từng tệp trước khi thay thế bản hiện tại.'},
    {'id': 'F02', 'priority': 'P1', 'title': 'Nhận ca có thể ghi đè tác tử đang giữ ca',
     'location': '.agents/tools/sync_bus.py:732 và bản sao trong skill bridge',
     'evidence': 'Bus thử nghiệm tách biệt đang IN_PROGRESS/CODEX; claim_task(GEMINI) thành công và đổi holder thành GEMINI.',
     'impact': 'FileLock bảo vệ thao tác ghi đồng thời nhưng không bảo vệ quyền sở hữu ca. Lỗi hiện hữu; chưa xác định được thời điểm phát sinh.',
     'recommendation': 'Trong cùng FileLock, từ chối holder khác; cho phép nhận lại cùng holder; thêm test cạnh tranh và kiểm tra quyền complete/review.'},
    {'id': 'F03', 'priority': 'P2', 'title': 'Dò workspace và metadata bàn giao chưa theo vị trí memory mới',
     'location': '.agents/tools/sync_bus.py:171,351,508 và bản sao trong skill bridge',
     'evidence': 'Không truyền workspace: root bị nhận là .agents và relative bus thành memory/DUAL_AGENT_BUS.json. Truyền workspace đúng: .agents/memory/DUAL_AGENT_BUS.json. Cả 18 artifacts trong bus nhận bàn giao vẫn dùng đường dẫn cũ không tồn tại.',
     'impact': 'Bus vật lý đọc được nhưng đường dẫn artifact, phát hiện file dự án và memo có thể sai; chưa đạt tiêu chí hoạt động ổn định.',
     'recommendation': 'Thống nhất root resolver, đường dẫn memory và memo; kiểm từ project root, .agents và thư mục ngoài; giữ fallback legacy có kiểm soát.'},
    {'id': 'F04', 'priority': 'P2', 'title': 'Còn 8 literal đường dẫn cố định tới workspace ổ G:',
     'location': 'cad_plan_engine.py:1336–1338; dce_dxf_generator.py:214–215; msproject_bridge.py:113–115',
     'evidence': 'AST tìm thấy 8 literal workspace trong 3 file runtime/CLI. Ba đường dẫn demo MS Project không tồn tại tại vị trí ghi cứng; các đường dẫn CAD tồn tại trên máy này nhưng không portable.',
     'impact': 'Di chuyển gói sang máy/ổ khác chưa bảo đảm độc lập; mặc định CLI vẫn trỏ dự án cụ thể.',
     'recommendation': 'Suy ra template theo __file__; yêu cầu hoặc cấu hình input/output. Không xóa các đường dẫn dò executable hệ điều hành hợp lệ.'},
    {'id': 'F05', 'priority': 'P2', 'title': 'Registry và trình kiểm tra CAD không thống nhất đường dẫn',
     'location': '.agents/skills/Technical_Illustrator/scripts/registry.json; Design_Evaluation/scripts/validate_registry.py',
     'evidence': 'Validator báo MISSING_FILE cho cad_plan_engine.py, dce_dxf_generator.py, calc_to_dxf.py. Cả ba thực tế nằm trong cad_integration/, không phải scripts/. Ngoài ra có 5 cảnh báo orphan.',
     'impact': 'Không phải mất ba file nguồn, nhưng công cụ xác minh registry hiện không PASS và dễ điều hướng sai entry point.',
     'recommendation': 'Bổ sung đường dẫn tương đối rõ ràng trong registry và cho validator/consumer dùng cùng quy ước.'}
]
summary = {'timestamp': datetime.now().astimezone().isoformat(), 'review_status': 'NEED_REVIEW',
           'production_source_modified_by_review': False, 'skills': len(evidence['skills']),
           'python_sources_parsed': len(evidence['sources']), 'syntax_errors': len(evidence['syntax_errors']),
           'full_passed': 27, 'full_seconds': full['wall_seconds'], 'fast_passed': 17,
           'fast_seconds': fast['wall_seconds'], 'archive_valid': 6, 'archive_invalid': 1,
           'findings': findings,
           'criteria': {'new_bus_readable_and_claimed': True, 'bus_stable_and_ownership_safe': False,
                        'no_incorrect_hardcoded_paths': False, 'independent_27_suites_pass': True,
                        'independent_report_written': True}}
(OUT/'review_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
lines = ['# Kiểm toán độc lập sau tái cấu trúc Agent Structure', '',
         f"Thời điểm: {summary['timestamp']} — người kiểm tra: CODEX.", '',
         '**Kết luận: NEED_REVIEW. 27/27 suites PASS nhưng chưa đạt toàn bộ tiêu chí bàn giao.**', '',
         '## Phạm vi và phương pháp', '',
         'Đã nhận ca từ `.agents/memory/DUAL_AGENT_BUS.json` qua bridge với workspace chỉ định rõ. Đọc tiêu chí, kiểm 14 skill entry points, parse 222 file Python production, đối chiếu ba bản AGENTS.md, kiểm ZIP, chạy registry validator và thử quyền sở hữu trên bus tạm. Không sửa mã production trong lượt rà soát. SHA-256 của toàn bộ 222 nguồn được kiểm lại trước khi xuất báo cáo.',
         'Kiểm tra cấu trúc không thay thế kiểm thử mọi đường thực thi, thiết kế kết cấu hoặc integration với phần mềm có giấy phép. Không có manifest nguồn trước khi nén để chứng minh đủ 3.739 tệp; CRC của ZIP còn đọc được chỉ xác nhận nội dung hiện có, không chứng minh archive đầy đủ.', '',
         '## Các phát hiện cần xử lý', '']
for finding in findings:
    lines += [f"### {finding['priority']} — {finding['id']}: {finding['title']}", '',
              f"Vị trí: `{finding['location']}`.", '', finding['evidence'], '',
              'Ảnh hưởng: '+finding['impact'], '', 'Khuyến nghị: '+finding['recommendation'], '']
lines += ['## Kiểm chứng đạt', '',
          '- 14/14 SKILL.md tồn tại và có version; các Markdown link literal được kiểm không thiếu đích.',
          '- 222 file Python production parse thành công, 0 lỗi cú pháp. Không quét code trong archive/references/standards như code production.',
          '- AGENTS.md ở root, .agents và .agents/skills có SHA-256 giống nhau. Đồng nhất nội dung chưa đồng nghĩa mọi ví dụ đường dẫn đều portable.',
          '- Sáu ZIP đọc được, tất cả member qua CRC, không có đường dẫn member nguy hiểm; tổng 2.306 file trong sáu ZIP này. ZIP thứ bảy không đọc được.',
          '- Đã chạy đủ 27 suites độc lập, không bỏ suite, không thay đổi mã production để làm test PASS.', '',
          '## Hiệu năng', '',
          '| Bộ chạy | Gemini bàn giao | CODEX kiểm chứng | Kết quả |', '|---|---:|---:|---|',
          f"| Fast | 12,45s | {fast['wall_seconds']:.2f}s | 17/17 PASS |",
          f"| Full, lượt đo riêng | 80,06s | {full['wall_seconds']:.2f}s | 27/27 PASS |", '',
          f"Lượt full đầu {first['wall_seconds']:.2f}s chạy cùng một số lượt đọc kiểm kê I/O nên không dùng làm phép so sánh hiệu năng chính. Lượt full thứ hai chạy sau các phép quét nặng. Số Gemini là số khai báo trong bàn giao, không phải baseline cùng điều kiện được tái tạo. Biến động một vài lượt không đủ chứng minh hồi quy hiệu năng.", '',
          'Mỗi suite lưu đầy đủ stdout, stderr, mã thoát và thời gian tại `full_isolated/`. `fast/` và `full/` giữ các lượt còn lại.', '',
          '| Suite | Giây | Kết quả |', '|---|---:|---|']
for row in full['suites']:
    lines.append(f"| {row['name']} | {row['wall_seconds']:.2f} | PASS |")
lines += ['', '## Tiêu chí nghiệm thu', '',
          '| Tiêu chí | Đánh giá |', '|---|---|',
          '| Bus ở vị trí mới hoạt động ổn định | Đọc/nhận ca được; chưa đạt do F02, F03 |',
          '| Không còn hardcoded path sai | Chưa đạt: F03, F04 |',
          '| 27/27 suites PASS độc lập | Đạt |',
          '| Báo cáo tại .agents/memory/audits | Đạt |', '',
          'F01 và F05 là phát hiện bổ sung về toàn vẹn lưu trữ và registry. Không coi PASS của 27 suites là bằng chứng cho những nhánh chưa có test này.', '',
          '## Bằng chứng và bàn giao', '',
          '- `structure_evidence.json`: inventory, version/hash, AST literals, archive CRC/SHA-256 và root resolver.',
          '- `archive_recheck.json`: hai lần đọc độc lập rvt-mcp.zip, chữ ký và kết quả EOCD.',
          '- `bus_registry_evidence.json`, `registry.log`: test ownership trên bus tạm và lỗi registry.',
          '- `full_isolated/timings.json`, `fast/timings.json`: số đo máy đọc được.',
          '- `incoming_bus.json`: snapshot bus trước khi bàn giao kết quả kiểm toán.',
          'Bus chuyển NEED_REVIEW cho GEMINI với các hành động khắc phục cụ thể. Không đánh dấu COMPLETED hoặc tự xác nhận các tiêu chí chưa đạt.', '']
(OUT/'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
with sync_bus.FileLock(sync_bus.LOCK_PATH):
    data = json.loads(sync_bus.BUS_PATH.read_text(encoding='utf-8'))
    assert data['current_holder'] == 'CODEX', 'Live ownership changed during review'
    (OUT/'incoming_bus.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    data.update(last_updated_by='CODEX', timestamp=summary['timestamp'], handoff_status='NEED_REVIEW',
                current_holder='IDLE', Verification_Status='INDEPENDENT_AUDIT_FINDINGS_REQUIRE_REPAIR',
                summary=f"Independent review: 27/27 full PASS in {full['wall_seconds']:.2f}s; 17/17 fast PASS in {fast['wall_seconds']:.2f}s. 14 skills and 222 Python sources checked. Five findings: invalid rvt-mcp ZIP, claim ownership overwrite, workspace/memory metadata mismatch, remaining fixed G-drive paths, CAD registry path mismatch. No production code modified. Report: .agents/memory/audits/STRUCTURE_CODEX_20261113/REPORT.md.",
                artifacts_modified=['.agents/memory/DUAL_AGENT_BUS.json', '.agents/memory/DUAL_AGENT_HANDOFF_MEMO.md']+
                    [path.relative_to(ROOT).as_posix() for path in sorted(OUT.rglob('*')) if path.is_file()],
                independent_audit=summary)
    data['next_action_for_partner'].update(target_agent='GEMINI',
        task_description='Resolve independent audit F01-F05: recover and verify rvt-mcp.zip; prevent claiming another active holder; correct workspace root and migrated memory paths; remove project-specific absolute defaults; align CAD registry and validator. Re-run full tests and dedicated regression probes.',
        target_files=['.agents/tools/sync_bus.py', '.agents/skills/SKILL_DUAL_AGENT_BRIDGE/scripts/sync_bus.py',
                      '.agents/_references_archived/rvt-mcp.zip', '.agents/skills/Technical_Illustrator/scripts/registry.json'],
        acceptance_criteria=['All seven reference ZIPs pass CRC and have a verified source manifest',
            'A different agent cannot claim an IN_PROGRESS bus',
            'Workspace and bus paths resolve correctly from root, nested and external working directories',
            'No project-specific fixed absolute defaults remain in the identified CAD/Project entrypoints',
            'Registry validator reports no missing CAD files', 'Independent full runner remains 27/27 PASS'],
        command='Read .agents/memory/audits/STRUCTURE_CODEX_20261113/REPORT.md and fix F01-F05 before requesting re-audit.')
    valid, reason = sync_bus.validate_bus_payload(data)
    assert valid, reason
    sync_bus._atomic_write_json(sync_bus.BUS_PATH, data)
    sync_bus.generate_handoff_memo(data, sync_bus.MEMO_PATH)
    # Correct this published memo; the generator defect remains recorded as F03.
    memo = sync_bus.MEMO_PATH.read_text(encoding='utf-8')
    memo = memo.replace('`memory/DUAL_AGENT_BUS.json`', '`.agents/memory/DUAL_AGENT_BUS.json`')
    sync_bus.MEMO_PATH.write_text(memo, encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k != 'findings'}, ensure_ascii=False, indent=2))
