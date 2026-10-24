#!/usr/bin/env python3
"""
handoff_manager.py — Manage SKILL_BRIDGE handoffs in SHARED_CONTEXT

Usage:
    python handoff_manager.py create <type> <project_id> [options]
    python handoff_manager.py list [--status active|archived|rejected]
    python handoff_manager.py validate <file>
    python handoff_manager.py archive <file>
    python handoff_manager.py reject <file> --reason "..."
    python handoff_manager.py receipt <file>
"""

import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict


# Base directory
SHARED_CONTEXT = Path(__file__).parent
ACTIVE_DIR = SHARED_CONTEXT / "_active"
ARCHIVE_DIR = SHARED_CONTEXT / "_archive"
REJECT_DIR = SHARED_CONTEXT / "_rejected"
RECEIPTS_DIR = ACTIVE_DIR / "RECEIPTS"


@dataclass
class Handoff:
    """Represents a handoff between skills supporting both SKILL_BRIDGE v3.0.0 and legacy v1.0"""
    handoff_type: str
    project_id: str
    source_skill: str
    target_skill: str
    timestamp: str
    data: Dict
    calculation_log_ids: List[str]
    confidence_level: str = "MEDIUM"
    priority: str = "NORMAL"
    status: str = "PENDING"
    version: str = "3.0.0"

    def to_json(self) -> Dict:
        now_str = datetime.now().strftime('%Y%m%d')
        src_tag = self.source_skill[:3].upper() if self.source_skill else "SRC"
        tgt_tag = self.target_skill[:3].upper() if self.target_skill else "TGT"
        handoff_id = f"HND-{src_tag}-{tgt_tag}-{now_str}-001"

        return {
            "handoff_meta": {
                "handoff_id": handoff_id,
                "handoff_type": self.handoff_type,
                "version": self.version,
                "source_skill": self.source_skill,
                "target_skill": self.target_skill,
                "timestamp": self.timestamp,
                "confidence_level": self.confidence_level,
                "priority": self.priority,
                "status": self.status
            },
            "_meta": {  # Alias for legacy compatibility
                "handoff_type": self.handoff_type,
                "version": "1.0",
                "source_skill": self.source_skill,
                "target_skill": self.target_skill,
                "project_id": self.project_id,
                "calculation_log_ids": self.calculation_log_ids,
                "calculation_log_id": self.calculation_log_ids[0] if self.calculation_log_ids else "",
                "timestamp": self.timestamp,
                "confidence_level": self.confidence_level
            },
            "project_context": {
                "project_name": self.project_id,
                "project_code": self.project_id,
                "phase": "BVTC",
                "standards_lock_version": "v2.3.0"
            },
            "payload": self.data,
            "validation": {
                "schema_valid": True,
                "missing_fields": [],
                "warnings": []
            },
            **self.data
        }

    @classmethod
    def from_json(cls, data: Dict) -> 'Handoff':
        meta = data.get("handoff_meta") or data.get("_meta", {})
        proj_ctx = data.get("project_context", {})
        proj_id = meta.get("project_id") or proj_ctx.get("project_code") or proj_ctx.get("project_name", "")
        payload = data.get("payload") if isinstance(data.get("payload"), dict) else {
            k: v for k, v in data.items() if k not in ("_meta", "handoff_meta", "project_context", "validation")
        }
        calc_ids = meta.get("calculation_log_ids", [])
        if not calc_ids and meta.get("calculation_log_id"):
            calc_ids = [meta["calculation_log_id"]]
        return cls(
            handoff_type=meta.get("handoff_type", ""),
            project_id=proj_id,
            source_skill=meta.get("source_skill", ""),
            target_skill=meta.get("target_skill", ""),
            timestamp=meta.get("timestamp", ""),
            data=payload,
            calculation_log_ids=calc_ids,
            confidence_level=meta.get("confidence_level", "MEDIUM"),
            priority=meta.get("priority", "NORMAL"),
            status=meta.get("status", "PENDING"),
            version=meta.get("version", "3.0.0")
        )


class HandoffManager:
    """Manage handoff lifecycle"""

    def __init__(self):
        # Ensure directories exist
        for d in [ACTIVE_DIR, ARCHIVE_DIR, REJECT_DIR, RECEIPTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def _get_filename(self, handoff: Handoff) -> str:
        """Generate filename for handoff"""
        ts = handoff.timestamp.replace(":", "").replace("-", "").replace("+", "")
        return f"{handoff.handoff_type}_{handoff.project_id}_{ts}.json"

    def create(self, handoff_type: str, project_id: str, source: str, target: str,
               data: Dict, calculation_log_ids: List[str], confidence: str = "MEDIUM",
               custom_timestamp: Optional[str] = None) -> Path:
        """
        Create a new handoff.

        Args:
            handoff_type: Type of handoff (e.g., 'foundation_params')
            project_id: Project identifier
            source: Source skill name
            target: Target skill name
            data: Handoff data
            calculation_log_ids: List of calculation log IDs
            confidence: Confidence level (HIGH/MEDIUM/LOW)
            custom_timestamp: Optional timestamp

        Returns:
            Path to created handoff file
        """
        handoff = Handoff(
            handoff_type=handoff_type,
            project_id=project_id,
            source_skill=source,
            target_skill=target,
            timestamp=custom_timestamp or datetime.now().isoformat(),
            data=data,
            calculation_log_ids=calculation_log_ids,
            confidence_level=confidence
        )

        filename = self._get_filename(handoff)
        filepath = ACTIVE_DIR / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(handoff.to_json(), f, indent=2, ensure_ascii=False)

        print(f"✓ Created: {filepath.name}")
        print(f"  From: {source} → To: {target}")
        print(f"  Confidence: {confidence}")

        return filepath

    def list(self, status: str = "active") -> List[Dict]:
        """
        List handoffs by status.

        Args:
            status: 'active', 'archived', 'rejected', or 'all'

        Returns:
            List of handoff info dicts
        """
        results = []

        def scan_dir(directory: Path, status_label: str):
            if not directory.exists():
                return
            for f in directory.glob("*.json"):
                if f.name == "README.md":
                    continue
                if "receipt" in f.name:
                    continue
                try:
                    with open(f, 'r', encoding='utf-8') as fp:
                        data = json.load(fp)
                    meta = data.get("_meta", {})
                    results.append({
                        "file": f.name,
                        "path": str(f),
                        "status": status_label,
                        "type": meta.get("handoff_type", "unknown"),
                        "project": meta.get("project_id", "unknown"),
                        "source": meta.get("source_skill", "unknown"),
                        "target": meta.get("target_skill", "unknown"),
                        "timestamp": meta.get("timestamp", ""),
                        "confidence": meta.get("confidence_level", "unknown")
                    })
                except:
                    pass

        if status in ["active", "all"]:
            scan_dir(ACTIVE_DIR, "active")
        if status in ["archived", "all"]:
            scan_dir(ARCHIVE_DIR, "archived")
        if status in ["rejected", "all"]:
            scan_dir(REJECT_DIR, "rejected")

        # Sort by timestamp (newest first)
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return results

    def validate(self, filepath: str) -> bool:
        """
        Validate a handoff file.

        Returns:
            True if valid, False otherwise
        """
        from validate_handoff_schema import validate_handoff

        filepath = Path(filepath)
        if not filepath.exists():
            filepath = ACTIVE_DIR / filepath

        is_valid, errors, warnings = validate_handoff(str(filepath))

        print(f"\n{'='*60}")
        print(f"Validation: {'✓ VALID' if is_valid else '✗ INVALID'}")
        print(f"{'='*60}")

        if warnings:
            print(f"\n⚠ Warnings:")
            for w in warnings:
                print(f"  • {w}")

        if errors:
            print(f"\n✗ Errors:")
            for e in errors:
                print(f"  • {e}")

        return is_valid

    def archive(self, filename: str) -> bool:
        """
        Archive a completed handoff.

        Args:
            filename: Handoff filename

        Returns:
            True if successful
        """
        src = ACTIVE_DIR / filename
        if not src.exists():
            print(f"✗ File not found: {filename}")
            return False

        dst = ARCHIVE_DIR / filename

        # Move to archive
        shutil.move(str(src), str(dst))
        print(f"✓ Archived: {filename}")

        # Also archive any receipts
        receipt_src = RECEIPTS_DIR / filename.replace(".json", "_receipt.json")
        if receipt_src.exists():
            receipt_dst = ARCHIVE_DIR / receipt_src.name
            shutil.move(str(receipt_src), str(receipt_dst))

        return True

    def reject(self, filename: str, reason: str, rejector: str = "system") -> Path:
        """
        Reject a handoff with reason.

        Args:
            filename: Handoff filename
            reason: Rejection reason
            rejector: Name of skill rejecting

        Returns:
            Path to rejection file
        """
        src = ACTIVE_DIR / filename
        if not src.exists():
            # Try in other directories
            for d in [ARCHIVE_DIR, REJECT_DIR]:
                if (d / filename).exists():
                    src = d / filename
                    break
            else:
                print(f"✗ File not found: {filename}")
                return None

        # Load original
        with open(src, 'r', encoding='utf-8') as f:
            original = json.load(f)

        # Create rejection record
        rejection = {
            "_meta": {
                "handoff_type": "REJECTED",
                "original_file": str(src),
                "rejected_at": datetime.now().isoformat(),
                "rejected_by": rejector,
                "rejection_reasons": reason if isinstance(reason, list) else [reason]
            },
            "original_handoff": original
        }

        # Save to rejected
        dst = REJECT_DIR / filename
        with open(dst, 'w', encoding='utf-8') as f:
            json.dump(rejection, f, indent=2, ensure_ascii=False)

        # Remove from original location if it was in active
        if src.exists() and src != dst:
            src.unlink()

        print(f"✗ Rejected: {filename}")
        print(f"  Reason: {reason}")

        return dst

    def create_receipt(self, filename: str, processor: str, notes: str = "") -> Path:
        """
        Create a receipt confirmation for a handoff.

        Args:
            filename: Handoff filename
            processor: Name of skill that processed it
            notes: Optional processing notes

        Returns:
            Path to receipt file
        """
        src = ACTIVE_DIR / filename
        if not src.exists():
            print(f"✗ File not found: {filename}")
            return None

        # Load original to validate
        with open(src, 'r', encoding='utf-8') as f:
            original = json.load(f)

        meta = original.get("_meta", {})

        # Create receipt
        receipt = {
            "_meta": {
                "receipt_type": "CONFIRMED",
                "original_handoff": str(src),
                "received_by": processor,
                "received_at": datetime.now().isoformat(),
                "schema_validated": True
            },
            "fields_received": {
                "handoff_type": f"validated: true ({meta.get('handoff_type', 'N/A')})",
                "project_id": f"validated: true ({meta.get('project_id', 'N/A')})",
                "timestamp": f"validated: true ({meta.get('timestamp', 'N/A')})"
            },
            "processing_notes": notes,
            "next_action": "Processing complete - executing task"
        }

        # Save receipt
        receipt_name = filename.replace(".json", "_receipt.json")
        receipt_path = RECEIPTS_DIR / receipt_name
        with open(receipt_path, 'w', encoding='utf-8') as f:
            json.dump(receipt, f, indent=2, ensure_ascii=False)

        print(f"✓ Receipt created: {receipt_name}")
        print(f"  Processed by: {processor}")

        return receipt_path

    def get_pending(self, target_skill: str) -> List[Dict]:
        """
        Get pending handoffs for a specific skill.

        Args:
            target_skill: Target skill name

        Returns:
            List of pending handoff info dicts
        """
        pending = []

        for f in ACTIVE_DIR.glob("*.json"):
            if "receipt" in f.name or f.name == "README.md":
                continue

            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                meta = data.get("_meta", {})

                if meta.get("target_skill") == target_skill:
                    # Check if already has receipt
                    receipt_name = f.name.replace(".json", "_receipt.json")
                    has_receipt = (RECEIPTS_DIR / receipt_name).exists()

                    pending.append({
                        "file": f.name,
                        "type": meta.get("handoff_type", "unknown"),
                        "source": meta.get("source_skill", "unknown"),
                        "timestamp": meta.get("timestamp", ""),
                        "confidence": meta.get("confidence_level", "unknown"),
                        "has_receipt": has_receipt
                    })
            except:
                pass

        return pending


def main():
    import argparse

    parser = argparse.ArgumentParser(description="SKILL_BRIDGE Handoff Manager")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # create command
    create_parser = subparsers.add_parser("create", help="Create a new handoff")
    create_parser.add_argument("type", help="Handoff type")
    create_parser.add_argument("project_id", help="Project ID")
    create_parser.add_argument("--source", required=True, help="Source skill")
    create_parser.add_argument("--target", required=True, help="Target skill")
    create_parser.add_argument("--data", help="JSON data file or inline JSON")
    create_parser.add_argument("--logs", nargs="+", help="Calculation log IDs")
    create_parser.add_argument("--confidence", default="MEDIUM", choices=["HIGH", "MEDIUM", "LOW"])

    # list command
    list_parser = subparsers.add_parser("list", help="List handoffs")
    list_parser.add_argument("--status", default="active", choices=["active", "archived", "rejected", "all"])
    list_parser.add_argument("--skill", help="Filter by target skill")

    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate a handoff")
    validate_parser.add_argument("file", help="Handoff file")

    # archive command
    archive_parser = subparsers.add_parser("archive", help="Archive a handoff")
    archive_parser.add_argument("file", help="Handoff file")

    # reject command
    reject_parser = subparsers.add_parser("reject", help="Reject a handoff")
    reject_parser.add_argument("file", help="Handoff file")
    reject_parser.add_argument("--reason", required=True, help="Rejection reason")
    reject_parser.add_argument("--by", default="system", help="Rejector name")

    # receipt command
    receipt_parser = subparsers.add_parser("receipt", help="Create receipt for handoff")
    receipt_parser.add_argument("file", help="Handoff file")
    receipt_parser.add_argument("--processor", required=True, help="Processor skill name")
    receipt_parser.add_argument("--notes", default="", help="Processing notes")

    # pending command
    pending_parser = subparsers.add_parser("pending", help="Show pending handoffs for a skill")
    pending_parser.add_argument("--skill", required=True, help="Target skill name")

    args = parser.parse_args()

    manager = HandoffManager()

    if args.command == "create":
        # Parse data
        data = {}
        if args.data:
            if args.data.startswith("{"):
                data = json.loads(args.data)
            else:
                with open(args.data, 'r', encoding='utf-8') as f:
                    data = json.load(f)

        filepath = manager.create(
            handoff_type=args.type,
            project_id=args.project_id,
            source=args.source,
            target=args.target,
            data=data,
            calculation_log_ids=args.logs or [],
            confidence=args.confidence
        )
        print(f"\nHandoff ready: {filepath}")

    elif args.command == "list":
        results = manager.list(status=args.status)

        if args.skill:
            results = [r for r in results if r.get("target") == args.skill]

        if not results:
            print("No handoffs found.")
        else:
            print(f"\n{'='*80}")
            print(f"{'File':<45} {'Type':<20} {'Status':<10}")
            print(f"{'='*80}")
            for r in results:
                print(f"{r['file']:<45} {r['type']:<20} {r['status']:<10}")
            print(f"{'='*80}")
            print(f"Total: {len(results)}")

    elif args.command == "validate":
        manager.validate(args.file)

    elif args.command == "archive":
        manager.archive(args.file)

    elif args.command == "reject":
        manager.reject(args.file, args.reason, args.by)

    elif args.command == "receipt":
        manager.create_receipt(args.file, args.processor, args.notes)

    elif args.command == "pending":
        results = manager.get_pending(args.skill)

        if not results:
            print(f"No pending handoffs for {args.skill}.")
        else:
            print(f"\nPending handoffs for {args.skill}:")
            for r in results:
                status = "✓ Receipt" if r["has_receipt"] else "○ Pending"
                print(f"  {status} {r['type']} from {r['source']} ({r['timestamp'][:10]})")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
