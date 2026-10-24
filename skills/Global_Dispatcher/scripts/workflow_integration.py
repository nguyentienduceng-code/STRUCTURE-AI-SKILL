#!/usr/bin/env python3
"""
Approval Workflow Integration Helper.

Module này cung cấp wrapper để tích hợp Approval Gate vào workflow hiện tại.

Usage:
    from workflow_integration import ApprovalWorkflow

    workflow = ApprovalWorkflow()
    result = workflow.execute_with_approval(
        prompt="Tính cốt thép dầm B1",
        stages=["Structural_Design_Engineer"],
        execute_func=my_execute_func
    )

Version: 1.0.1 (Fixed: decorator variable shadowing)
Created: 2026-10-12
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
from typing import Callable, Optional, Any
from pathlib import Path

# Import từ cùng package
from approval_gate import ApprovalGate, ApprovalCardGenerator
from approval_state import ApprovalContext, ExecutionStatus


class ApprovalWorkflow:
    """
    Wrapper class để tích hợp Approval Gate vào workflow.

    Cung cấp interface đơn giản để:
    1. Intercept request và kiểm tra approval
    2. Hiển thị approval card
    3. Chờ và validate response
    4. Execute nếu approved
    """

    def __init__(self, output_dir: str = None, max_repair_iterations: int = 3):
        self.gate = ApprovalGate(output_dir=output_dir, max_repair_iterations=max_repair_iterations)
        self._pending_card: Optional[str] = None

    def check(self, prompt: str, stages: list, **kwargs) -> tuple[bool, str]:
        """
        Kiểm tra xem có cần approval không và trả về card nếu cần.

        Args:
            prompt: User prompt
            stages: Danh sách stages
            **kwargs: Các tham số bổ sung cho ApprovalGate.intercept()

        Returns:
            tuple: (needs_approval, approval_card_or_empty_string)
        """
        return self.gate.intercept(
            prompt=prompt,
            stages=stages,
            **kwargs
        )

    def execute_with_approval(
        self,
        prompt: str,
        stages: list,
        execute_func: Callable[[], Any],
        user_response: str = None,
        **kwargs
    ) -> dict:
        """
        Execute với approval workflow.

        Args:
            prompt: User prompt
            stages: Danh sách stages
            execute_func: Function để execute nếu approved
            user_response: Response từ user (nếu đã có)
            **kwargs: Các tham số bổ sung

        Returns:
            dict: {
                "status": "approved" | "pending" | "rejected",
                "card": "approval_card_markdown" (nếu pending),
                "result": execute_func_result (nếu approved)
            }
        """
        # Step 1: Intercept và kiểm tra approval
        needs_approval, card = self.check(prompt, stages, **kwargs)

        if not needs_approval:
            # Không cần approval → execute trực tiếp
            result = execute_func()
            return {
                "status": "approved",
                "card": None,
                "result": result,
                "message": "Executed without approval (simple request)"
            }

        # Lưu card để hiển thị
        self._pending_card = card

        # Nếu chưa có response → trả về pending
        if user_response is None:
            return {
                "status": "pending",
                "card": card,
                "result": None,
                "message": "Approval card generated. Awaiting user response."
            }

        # Step 2: Validate response
        approved, error = self.gate.validate_response(user_response)

        if not approved:
            return {
                "status": "rejected",
                "card": card,
                "result": None,
                "error": error,
                "message": f"Execution rejected: {error}"
            }

        # Step 3: Execute
        result = execute_func()

        return {
            "status": "approved",
            "card": card,
            "result": result,
            "message": "Execution approved and completed"
        }

    def handle_response(self, response: str, execute_func: Callable[[], Any] = None) -> dict:
        """
        Xử lý response từ user khi đã có pending approval.

        Args:
            response: Response từ user
            execute_func: Function để execute nếu approved

        Returns:
            dict: Kết quả tương tự execute_with_approval()
        """
        if not self.gate.is_pending():
            return {
                "status": "error",
                "message": "No pending approval to process"
            }

        approved, error = self.gate.validate_response(response)

        if not approved:
            return {
                "status": "rejected",
                "card": self._pending_card,
                "error": error,
                "message": f"Execution rejected: {error}"
            }

        if execute_func is None:
            return {
                "status": "approved",
                "card": self._pending_card,
                "result": None,
                "message": "Approved but no execute_func provided"
            }

        result = execute_func()
        return {
            "status": "approved",
            "card": self._pending_card,
            "result": result,
            "message": "Execution approved and completed"
        }

    def get_pending_card(self) -> Optional[str]:
        """Lấy pending approval card."""
        return self._pending_card

    def cancel(self):
        """Hủy pending approval."""
        self.gate.cancel()
        self._pending_card = None


# =============================================================================
# DECORATOR VERSION
# =============================================================================

def requires_approval(
    stages_func: Callable = None,
    stages: list = None,
    gate_config: dict = None
):
    """
    Decorator để enforce approval trước khi execute function.

    Args:
        stages_func: Function trả về danh sách stages dựa trên args
        stages: Static list of stages
        gate_config: kwargs cho ApprovalGate

    Usage:
        @requires_approval(stages=["Structural_Design_Engineer"])
        def my_func():
            ...

        @requires_approval(stages_func=lambda args: ["SDE", "DE"])
        def my_func2(args):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Xác định stages
            if stages_func:
                actual_stages = stages_func(*args, **kwargs)
            elif stages:
                actual_stages = stages
            else:
                actual_stages = []

            # Xác định prompt từ kwargs hoặc args
            prompt = kwargs.get('prompt', args[0] if args else '')

            # Create workflow
            config = gate_config or {}
            gate = ApprovalGate(**config)

            # Intercept
            needs_approval, card = gate.intercept(
                prompt=prompt,
                stages=actual_stages,
                estimated_tools=kwargs.get('estimated_tools', 0),
                estimated_tokens=kwargs.get('estimated_tokens', 0),
            )

            if not needs_approval:
                return func(*args, **kwargs)

            # Check user response
            user_response = kwargs.get('user_response')
            if user_response is None:
                raise PendingApprovalError(card)

            approved, error = gate.validate_response(user_response)
            if not approved:
                raise ApprovalRejectedError(error)

            return func(*args, **kwargs)

        return wrapper
    return decorator


class PendingApprovalError(Exception):
    """Exception raised khi cần approval nhưng chưa có response."""
    def __init__(self, approval_card: str):
        self.approval_card = approval_card
        super().__init__("Approval required")


class ApprovalRejectedError(Exception):
    """Exception raised khi user từ chối approval."""
    pass


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Example 1: Basic usage
    print("=== Example 1: Basic Usage ===")

    workflow = ApprovalWorkflow()

    def sample_execute():
        return {"result": "Calculation complete", "data": [1, 2, 3]}

    # Test 1: Simple request (1 stage, 1 tool) → no approval needed
    result = workflow.execute_with_approval(
        prompt="Tính dầm B1",
        stages=["SDE"],
        execute_func=sample_execute,
        estimated_tools=1,
        estimated_tokens=5000,
    )
    print(f"Result: {result['status']}")
    print(f"Message: {result['message']}")

    # Test 2: Complex request → needs approval
    result = workflow.execute_with_approval(
        prompt="Tính dầm rồi vẽ hình",
        stages=["SDE", "TI"],
        execute_func=sample_execute,
        estimated_tools=5,
        estimated_tokens=25000,
    )
    print(f"\nResult: {result['status']}")
    print(f"Card generated: {result['card'] is not None}")

    # Test 3: Approve and execute
    result = workflow.handle_response("OK", sample_execute)
    print(f"\nAfter 'OK' response:")
    print(f"Result: {result['status']}")
    print(f"Execution output: {result.get('result')}")

    # Test 4: Reject
    result = workflow.handle_response("Không", sample_execute)
    print(f"\nAfter 'Không' response:")
    print(f"Result: {result['status']}")
    print(f"Error: {result.get('error')}")

    print("\n=== Example 2: Decorator ===")

    @requires_approval(stages=["SDE", "DE"], gate_config={"max_repair_iterations": 3})
    def complex_calculation(prompt: str, user_response: str = None):
        print("Executing complex calculation...")
        return {"status": "done"}

    try:
        result = complex_calculation(
            prompt="Tính dầm B1 rồi review",
            user_response="OK"
        )
        print(f"Result: {result}")
    except PendingApprovalError as e:
        print(f"Needs approval: {e.approval_card[:100]}...")
    except ApprovalRejectedError as e:
        print(f"Rejected: {e}")
