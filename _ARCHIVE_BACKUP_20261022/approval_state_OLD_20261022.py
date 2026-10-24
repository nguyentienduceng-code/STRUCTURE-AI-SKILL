#!/usr/bin/env python3
"""
Approval State Machine — Quản lý trạng thái Approval cho Pre-Execution Gate.

Module này định nghĩa enum trạng thái và dataclass cho workflow phê duyệt.

Version: 1.0.1 (Fixed: Ambiguous response handling)
Created: 2026-10-12
Author: AI Assistant - Phase 1 Enhancement
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


class ExecutionStatus(Enum):
    """
    Các trạng thái trong workflow Approval Gate.

    Flow: PENDING → APPROVED → EXECUTING → COMPLETED/FAILED
         ↘ REJECTED
         ↘ CANCELLED
    """
    PENDING = "pending"           # Đang chờ user approve
    APPROVED = "approved"         # User đã duyệt
    REJECTED = "rejected"        # User từ chối
    EXECUTING = "executing"      # Đang thực thi pipeline
    COMPLETED = "completed"      # Hoàn thành thành công
    FAILED = "failed"            # Thực thi thất bại
    CANCELLED = "cancelled"      # User hủy
    TIMEOUT = "timeout"          # Quá thời gian chờ


class ApprovalLevel(Enum):
    """
    Mức độ phê duyệt dựa trên độ phức tạp của pipeline.
    """
    NONE = "none"                # Không cần approve (1 skill, <3 tools)
    LOW = "low"                 # Cần low-level approve
    MEDIUM = "medium"            # Cần medium-level approve
    HIGH = "high"               # Cần high-level approve (nhiều skills)


@dataclass
class ApprovalContext:
    """
    Ngữ cảnh cho một approval request.
    Lưu trữ đầy đủ thông tin về pipeline cần duyệt.
    """
    # Metadata
    request_id: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    # User request
    user_prompt: str = ""

    # Pipeline info
    pipeline_id: Optional[str] = None
    stages: List[str] = field(default_factory=list)
    total_stages: int = 0
    estimated_tools: int = 0
    estimated_tokens: int = 0

    # Entity extraction (nếu có)
    extracted_geometry: dict = field(default_factory=dict)
    extracted_materials: dict = field(default_factory=dict)
    extracted_loads: dict = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)

    # Approval state
    status: ExecutionStatus = ExecutionStatus.PENDING
    approval_level: ApprovalLevel = ApprovalLevel.MEDIUM
    requires_approval: bool = True

    # Tracking
    repair_iterations: int = 0
    max_repair_iterations: int = 3
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_reason: Optional[str] = None

    # Products expected
    expected_products: List[str] = field(default_factory=list)

    def needs_approval(self) -> bool:
        """Kiểm tra xem có cần approval không."""
        return self.requires_approval and self.status == ExecutionStatus.PENDING

    def can_retry(self) -> bool:
        """Kiểm tra xem còn quota để retry không."""
        return self.repair_iterations < self.max_repair_iterations

    def to_dict(self) -> dict:
        """Convert sang dictionary cho JSON serialization."""
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
        """Create instance từ dictionary."""
        data = data.copy()
        data['status'] = ExecutionStatus(data.get('status', 'pending'))
        data['approval_level'] = ApprovalLevel(data.get('approval_level', 'medium'))
        return cls(**data)


# =============================================================================
# APPROVAL THRESHOLDS
# =============================================================================

# Ngưỡng xác định mức độ cần approve
APPROVAL_THRESHOLDS = {
    # (total_stages, estimated_tools) → approval_level
    # Nếu vượt ngưỡng → cần approval
    (1, 0): ApprovalLevel.NONE,        # 1 stage, 0 tools → không cần
    (1, 1): ApprovalLevel.NONE,        # 1 stage, 1 tool → không cần
    (1, 2): ApprovalLevel.LOW,        # 1 stage, 2 tools → low
    (2, 0): ApprovalLevel.LOW,        # 2 stages → low
    (2, 3): ApprovalLevel.MEDIUM,     # 2 stages, 3+ tools → medium
    (3, 0): ApprovalLevel.MEDIUM,     # 3+ stages → medium
    (5, 0): ApprovalLevel.HIGH,       # 5+ stages → high
}

# Ngưỡng token để cảnh báo
TOKEN_WARNING_THRESHOLD = 20000
TOKEN_CRITICAL_THRESHOLD = 50000


def determine_approval_level(total_stages: int, estimated_tools: int, estimated_tokens: int) -> tuple:
    """
    Xác định mức độ approval cần thiết.

    Returns:
        tuple: (approval_level, requires_approval)
    """
    # Check thresholds
    for (max_stages, max_tools), level in APPROVAL_THRESHOLDS.items():
        if total_stages <= max_stages and estimated_tools <= max_tools:
            if level == ApprovalLevel.NONE:
                return level, False
            return level, True

    # Default: MEDIUM nếu không khớp
    return ApprovalLevel.MEDIUM, True


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_request_id() -> str:
    """Tạo request ID duy nhất."""
    from uuid import uuid4
    return f"APR-{uuid4().hex[:8].upper()}"


def is_affirmative_response(response: str) -> bool:
    """
    Kiểm tra xem response có phải là affirmative không.

    Args:
        response: Text từ user

    Returns:
        True nếu user đồng ý
    """
    affirmative_keywords = [
        "ok", "đồng ý", "duyệt", "có", "chạy", "yes",
        "proceed", "go", "thực hiện", "bắt đầu",
        "được", "OK", "OK!", "o k", "đồng ý!", "vâng",
        "tốt", "bắt đầu đi", "tiến hành"
    ]

    response_lower = response.lower().strip()
    return any(kw in response_lower for kw in affirmative_keywords)


def is_negative_response(response: str) -> bool:
    """
    Kiểm tra xem response có phải là negative rõ ràng không.

    Lưu ý: "để tôi xem lại", "chờ một chút" được coi là ambiguous,
    không phải negative rõ ràng. Theo AGENTS.md §3 định nghĩa.

    Args:
        response: Text từ user

    Returns:
        True nếu user từ chối rõ ràng
    """
    # Negative keywords rõ ràng - KHÔNG bao gồm ambiguous phrases
    negative_keywords = [
        "không", "no", "not", "từ chối", "hủy", "cancel",
        "dừng", "stop", "sửa", "thay đổi",
        "chưa", "chưa đồng ý",
    ]

    response_lower = response.lower().strip()
    return any(kw in response_lower for kw in negative_keywords)


def is_ambiguous_response(response: str) -> bool:
    """
    Kiểm tra xem response có phải là ambiguous không.

    Ambiguous = không affirmative rõ ràng, không negative rõ ràng.
    Theo AGENTS.md §3: "để tôi xem lại", "ok nhưng..." không phải xác nhận.

    Args:
        response: Text từ user

    Returns:
        True nếu response ambiguous
    """
    response_lower = response.lower().strip()

    # Các phrases được coi là ambiguous
    ambiguous_phrases = [
        "để tôi xem", "để tôi kiểm", "để xem",
        "chờ một chút", "chờ tôi", "một chút",
        "cần suy nghĩ", "suy nghĩ thêm",
        "chưa sẵn sàng", "chưa rõ",
        "ok nhưng", "okay nhưng", "nhưng mà",
    ]

    # Nếu là negative rõ ràng → không ambiguous
    if is_negative_response(response):
        return False

    # Nếu là affirmative rõ ràng → không ambiguous
    if is_affirmative_response(response):
        return False

    # Nếu chứa ambiguous phrase → ambiguous
    if any(phrase in response_lower for phrase in ambiguous_phrases):
        return True

    # Nếu quá ngắn hoặc không rõ ràng → ambiguous
    if len(response_lower) < 3:
        return True

    return False


# =============================================================================
# TEST
# =============================================================================

if __name__ == "__main__":
    # Test state machine
    print("=== Approval State Machine Test ===\n")

    # Test 1: Create approval context
    ctx = ApprovalContext(
        request_id=generate_request_id(),
        user_prompt="Tính cốt thép dầm B1 theo TCVN 5574",
        stages=["Structural_Design_Engineer"],
        total_stages=1,
        estimated_tools=2,
        estimated_tokens=15000,
    )

    print(f"Request ID: {ctx.request_id}")
    print(f"Status: {ctx.status.value}")
    print(f"Needs approval: {ctx.needs_approval()}")
    print(f"Can retry: {ctx.can_retry()}")

    # Test 2: Approval level determination
    print("\n=== Approval Level Test ===")
    for (stages, tools), expected_level in [
        ((1, 0), ApprovalLevel.NONE),
        ((1, 2), ApprovalLevel.LOW),
        ((2, 5), ApprovalLevel.MEDIUM),
        ((6, 0), ApprovalLevel.HIGH),
    ]:
        level, requires = determine_approval_level(stages, tools, 0)
        status = "✓" if level == expected_level else "✗"
        print(f"{status} stages={stages}, tools={tools} → {level.value} (requires={requires})")

    # Test 3: Affirmative detection
    print("\n=== Affirmative Response Test ===")
    test_responses = [
        ("OK", True),
        ("Đồng ý", True),
        ("Duyệt", True),
        ("Không đồng ý", False),
        ("Chờ tôi xem lại", False),
    ]
    for response, expected in test_responses:
        result = is_affirmative_response(response)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{response}' → {result}")

    print("\n=== All Tests Complete ===")
