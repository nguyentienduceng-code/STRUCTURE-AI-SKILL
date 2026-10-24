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
