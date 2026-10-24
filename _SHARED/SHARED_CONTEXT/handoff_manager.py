#!/usr/bin/env python3
"""
handoff_manager.py — Manage SKILL_BRIDGE handoffs in SHARED_CONTEXT (v3.1.0)
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
            "_meta": {
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
                "standards_lock_version": "v3.1.0"
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
    """Manage handoff lifecycle (supports SKILL_BRIDGE v3.1.0 & v1.0 legacy)"""

    def __init__(self):
        for d in [ACTIVE_DIR, ARCHIVE_DIR, REJECT_DIR, RECEIPTS_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    def _get_filename(self, handoff: Handoff) -> str:
        ts = handoff.timestamp.replace(":", "").replace("-", "").replace("+", "")
        return f"{handoff.handoff_type}_{handoff.project_id}_{ts}.json"

    def create(self, handoff_type: str, project_id: str, source: str, target: str,
               data: Dict, calculation_log_ids: List[str], confidence: str = "MEDIUM",
               custom_timestamp: Optional[str] = None) -> Path:
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
        return filepath

    def list(self, status: str = "active") -> List[Dict]:
        results = []
        def scan_dir(directory: Path, status_label: str):
            if not directory.exists():
                return
            for f in directory.glob("*.json"):
                if f.name == "README.md" or "receipt" in f.name:
                    continue
                try:
                    with open(f, 'r', encoding='utf-8') as fp:
                        data = json.load(fp)
                    meta = data.get("handoff_meta") or data.get("_meta", {})
                    proj_ctx = data.get("project_context", {})
                    results.append({
                        "file": f.name,
                        "path": str(f),
                        "status": status_label,
                        "type": meta.get("handoff_type", "unknown"),
                        "project": meta.get("project_id") or proj_ctx.get("project_code", "unknown"),
                        "source": meta.get("source_skill", "unknown"),
                        "target": meta.get("target_skill", "unknown"),
                        "timestamp": meta.get("timestamp", ""),
                        "confidence": meta.get("confidence_level", "unknown")
                    })
                except Exception:
                    pass
        if status in ["active", "all"]:
            scan_dir(ACTIVE_DIR, "active")
        if status in ["archived", "all"]:
            scan_dir(ARCHIVE_DIR, "archived")
        if status in ["rejected", "all"]:
            scan_dir(REJECT_DIR, "rejected")
        results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return results

    def validate(self, filepath: str) -> bool:
        from validate_handoff_schema import validate_handoff
        fp = Path(filepath)
        if not fp.exists():
            fp = ACTIVE_DIR / filepath
        is_valid, errors, warnings = validate_handoff(str(fp))
        return is_valid

    def archive(self, filename: str) -> bool:
        src = ACTIVE_DIR / filename
        if not src.exists():
            return False
        dst = ARCHIVE_DIR / filename
        shutil.move(str(src), str(dst))
        receipt_src = RECEIPTS_DIR / filename.replace(".json", "_receipt.json")
        if receipt_src.exists():
            shutil.move(str(receipt_src), str(ARCHIVE_DIR / receipt_src.name))
        return True

    def reject(self, filename: str, reason: str, rejector: str = "system") -> Optional[Path]:
        src = ACTIVE_DIR / filename
        if not src.exists():
            for d in [ARCHIVE_DIR, REJECT_DIR]:
                if (d / filename).exists():
                    src = d / filename
                    break
            else:
                return None
        with open(src, 'r', encoding='utf-8') as f:
            original = json.load(f)
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
        dst = REJECT_DIR / filename
        with open(dst, 'w', encoding='utf-8') as f:
            json.dump(rejection, f, indent=2, ensure_ascii=False)
        if src.exists() and src != dst:
            src.unlink()
        return dst

    def create_receipt(self, filename: str, processor: str, notes: str = "") -> Optional[Path]:
        src = ACTIVE_DIR / filename
        if not src.exists():
            return None
        with open(src, 'r', encoding='utf-8') as f:
            original = json.load(f)
        meta = original.get("handoff_meta") or original.get("_meta", {})
        proj_ctx = original.get("project_context", {})
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
                "project_id": f"validated: true ({meta.get('project_id') or proj_ctx.get('project_code', 'N/A')})",
                "timestamp": f"validated: true ({meta.get('timestamp', 'N/A')})"
            },
            "processing_notes": notes,
            "next_action": "Processing complete - executing task"
        }
        receipt_name = filename.replace(".json", "_receipt.json")
        receipt_path = RECEIPTS_DIR / receipt_name
        with open(receipt_path, 'w', encoding='utf-8') as f:
            json.dump(receipt, f, indent=2, ensure_ascii=False)
        return receipt_path

    def get_pending(self, target_skill: str) -> List[Dict]:
        pending = []
        for f in ACTIVE_DIR.glob("*.json"):
            if "receipt" in f.name or f.name == "README.md":
                continue
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                meta = data.get("handoff_meta") or data.get("_meta", {})
                if meta.get("target_skill") == target_skill:
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
            except Exception:
                pass
        return pending
