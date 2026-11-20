"""Prepare an immutable work ticket and verify the same ticket after export."""
import argparse
import json
import sys
from pathlib import Path
import os
import tempfile

from agent_selection import AGENT_CHOICES
from sync_bus_2d_patch import SyncBus2DAdapter, approve_drafts


def main():
    if sys.stdout.encoding != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    prepare = actions.add_parser("prepare")
    prepare.add_argument("--prompt", required=True)
    prepare.add_argument("--workspace", type=Path, default=Path.cwd())
    prepare.add_argument("--ticket", type=Path, required=True)
    prepare.add_argument("--agent-selection", choices=AGENT_CHOICES)
    prepare.add_argument("--expected-file", action="append", default=[])
    prepare.add_argument("--project-identity", help="Mã hoặc tên chính thức xuất hiện trong từng sản phẩm")
    prepare.add_argument("--independent-review", action="store_true")
    default = actions.add_parser("set-default")
    default.add_argument("--workspace", type=Path, default=Path.cwd())
    default.add_argument("--project-dir", required=True, type=Path)
    default.add_argument("--agent-selection", required=True, choices=AGENT_CHOICES)
    approve = actions.add_parser("approve")
    approve.add_argument("--ticket", required=True, type=Path)
    approve.add_argument("--response", required=True)
    approve.add_argument("--draft", required=True, action="append", type=Path)
    approve.add_argument("--approval-record", required=True, type=Path)
    check = actions.add_parser("check")
    check.add_argument("--approval-record", type=Path)
    check.add_argument("--ticket", required=True, type=Path)
    check.add_argument("--report", required=True, type=Path)
    check.add_argument("--actor", choices=("CLAUDE", "GEMINI"), required=True)
    check.add_argument("--review-record", type=Path, help="Xác nhận từ người kiểm tra và mã băm từng tệp")
    args = parser.parse_args()
    try:
        if args.action == "set-default":
            from project_target_resolver import ProjectTargetResolver
            folder = args.project_dir.resolve(strict=True)
            resolver = ProjectTargetResolver(workspace_root=args.workspace.resolve(strict=True))
            known = {path.resolve() for _, path in resolver.discover_projects()}
            if folder not in known:
                parser.error("Chọn đúng thư mục dự án tại một trong hai thư mục dự án gốc.")
            dest = folder / ".agent-selection"
            with tempfile.NamedTemporaryFile(dir=folder, delete=False) as f:
                tmp = Path(f.name)
                f.write((args.agent_selection + "\n").encode("utf-8"))
            try:
                os.replace(tmp, dest)
            finally:
                tmp.unlink(missing_ok=True)
            print(f"{folder.name}: {args.agent_selection}")
            return 0
        if args.action == "prepare":
            workspace = args.workspace.resolve(strict=True)
            adapter = SyncBus2DAdapter(workspace_root=workspace)
            payload = adapter.prepare_handover_payload(
                args.prompt, args.ticket.stem, args.prompt, agent_selection=args.agent_selection,
                expected_files=args.expected_file, project_identity=args.project_identity,
                independent_review_required=args.independent_review, include_solo=True,
            )
            payload["workspace"] = str(workspace)
            if payload["status"] == "QUEUED":
                with args.ticket.open("x", encoding="utf-8") as stream:
                    json.dump(payload, stream, ensure_ascii=False, indent=2)
        else:
            payload = json.loads(args.ticket.read_text(encoding="utf-8-sig"))
            payload = payload.get("work_ticket", payload)
            if args.action == "approve":
                approval = approve_drafts(payload, args.response, args.draft)
                with args.approval_record.open("x", encoding="utf-8") as stream:
                    json.dump(approval, stream, ensure_ascii=False, indent=2)
                print(args.approval_record)
                return 0
            approval = json.loads(args.approval_record.read_text(encoding="utf-8-sig")) if args.approval_record else None
            review = json.loads(args.review_record.read_text(encoding="utf-8-sig")) if args.review_record else {}
            adapter = SyncBus2DAdapter(workspace_root=payload["workspace"])
            payload = adapter.complete_handover_with_gate(
                payload, args.report.read_text(encoding="utf-8-sig"), agent_name=args.actor,
                reviewed_by=review.get("reviewer"), reviewed_hashes=review.get("evidence_hashes"), approval=approval,
            )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if payload["status"] in ("QUEUED", "COMPLETED") else 2
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(2, str(exc) + "\n")


if __name__ == "__main__":
    sys.exit(main())
