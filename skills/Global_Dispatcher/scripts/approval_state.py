#!/usr/bin/env python3
"""
Approval State Machine v2.0 — Quản lý trạng thái Approval cho Pre-Execution Gate.

Nâng cấp v2.0 (2026-10-22):
- Fix BRAIN-BUG-07: Chặn triệt để lỗi False-Affirmative khi phản hồi có từ phủ định
  ("Không đồng ý", "Tôi không duyệt", "Đừng chạy vội", "Khoan chạy") hoặc câu điều kiện ("OK nhưng...").
- Fix BRAIN-BUG-08: Sửa lỗi bất đẳng thức kép 2 chiều trong determine_approval_level() và tích hợp ngưỡng token.
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import re
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


class ExecutionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ApprovalLevel(Enum):
    NONE = "none"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ApprovalContext:
    request_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    user_prompt: str = ""
    pipeline_id: Optional[str] = None
    stages: List[str] = field(default_factory=list)
    total_stages: int = 0
    estimated_tools: int = 0
    estimated_tokens: int = 0
    extracted_geometry: dict = field(default_factory=dict)
    extracted_materials: dict = field(default_factory=dict)
    extracted_loads: dict = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
    status: ExecutionStatus = ExecutionStatus.PENDING
    approval_level: ApprovalLevel = ApprovalLevel.MEDIUM
    requires_approval: bool = True
    repair_iterations: int = 0
    max_repair_iterations: int = 3
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_reason: Optional[str] = None
    expected_products: List[str] = field(default_factory=list)

    def needs_approval(self) -> bool:
        return self.requires_approval and self.status == ExecutionStatus.PENDING

    def can_retry(self) -> bool:
        return self.repair_iterations < self.max_repair_iterations

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "user_prompt": self.user_prompt,
            "pipeline_id": self.pipeline_id,
            "stages": self.stages,
            "total_stages": self.total_stages,
            "estimated_tools": self.estimated_tools,
            "estimated_tokens": self.estimated_tokens,
            "extracted_geometry": self.extracted_geometry,
            "extracted_materials": self.extracted_materials,
            "extracted_loads": self.extracted_loads,
            "assumptions": self.assumptions,
            "status": self.status.value,
            "approval_level": self.approval_level.value,
            "requires_approval": self.requires_approval,
            "repair_iterations": self.repair_iterations,
            "max_repair_iterations": self.max_repair_iterations,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at,
            "rejected_reason": self.rejected_reason,
            "expected_products": self.expected_products,
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ApprovalContext':
        data = data.copy()
        data['status'] = ExecutionStatus(data.get('status', 'pending'))
        data['approval_level'] = ApprovalLevel(data.get('approval_level', 'medium'))
        return cls(**data)


TOKEN_WARNING_THRESHOLD = 20000
TOKEN_CRITICAL_THRESHOLD = 50000


def determine_approval_level(total_stages: int, estimated_tools: int, estimated_tokens: int) -> tuple:
    """Xác định mức độ approval cần thiết (đã sửa lỗi bất đẳng thức kép 2 chiều & tích hợp ngưỡng token)."""
    if estimated_tokens >= TOKEN_CRITICAL_THRESHOLD or total_stages >= 5:
        return ApprovalLevel.HIGH, True
    if total_stages <= 1 and estimated_tools <= 1 and estimated_tokens < TOKEN_WARNING_THRESHOLD:
        return ApprovalLevel.NONE, False
    if (total_stages == 1 and estimated_tools == 2 and estimated_tokens < TOKEN_WARNING_THRESHOLD) or (
        total_stages == 2 and estimated_tools == 0 and estimated_tokens < TOKEN_WARNING_THRESHOLD
    ):
        return ApprovalLevel.LOW, True
    return ApprovalLevel.MEDIUM, True


def generate_request_id() -> str:
    from uuid import uuid4
    return f"APR-{uuid4().hex[:8].upper()}"


_AMBIGUOUS_PHRASES = [
    "để tôi xem", "để tôi kiểm", "để xem",
    "chờ một chút", "chờ tôi", "một chút", "đợi một chút", "đợi chút",
    "cần suy nghĩ", "suy nghĩ thêm",
    "chưa sẵn sàng", "chưa rõ",
    "ok nhưng", "okay nhưng", "đồng ý nhưng", "duyệt nhưng", "bắt đầu nhưng", "chạy nhưng", "nhưng mà",
    "khoan", "khoan chạy", "khoan đã", "tạm dừng",
]

_NEGATIVE_KEYWORDS = [
    "không", "no", "not", "từ chối", "hủy", "cancel",
    "dừng", "stop", "sửa", "thay đổi",
    "chưa", "chưa đồng ý", "đừng", "sai",
]

_AFFIRMATIVE_PATTERNS = [
    r"\bok\b", r"\boke\b", r"\bokay\b", r"\bo\s+k\b",
    r"\bđồng\s+ý\b", r"\bduyệt\b", r"^có[!.,\s]*$", r"^yes[!.,\s]*$",
    r"\bproceed\b", r"^go[!.,\s]*$", r"\bthực\s+hiện\b", r"\bbắt\s+đầu\b",
    r"^được[!.,\s]*$", r"\bvâng\b", r"^tốt[!.,\s]*$", r"\btiến\s+hành\b", r"^chạy(\s+đi)?[!.,\s]*$",
]


def is_negative_response(response: str) -> bool:
    response_lower = response.lower().strip()
    if any(p in response_lower for p in ("để tôi xem", "chờ một chút", "cần suy nghĩ", "để xem")):
        return False
    for kw in _NEGATIVE_KEYWORDS:
        if re.search(rf"(?<!\w){re.escape(kw)}(?!\w)", response_lower):
            return True
    return False


def is_affirmative_response(response: str) -> bool:
    response_lower = response.lower().strip()
    if not response_lower:
        return False
    if is_negative_response(response_lower):
        return False
    if any(phrase in response_lower for phrase in _AMBIGUOUS_PHRASES):
        return False
    if re.search(r"(?<!\w)(nhưng|khoan|đừng|chờ|đợi)(?!\w)", response_lower):
        return False
    for pat in _AFFIRMATIVE_PATTERNS:
        if re.search(pat, response_lower):
            return True
    return False


def is_ambiguous_response(response: str) -> bool:
    response_lower = response.lower().strip()
    if any(phrase in response_lower for phrase in _AMBIGUOUS_PHRASES):
        return True
    if is_negative_response(response):
        return False
    if is_affirmative_response(response):
        return False
    return True
