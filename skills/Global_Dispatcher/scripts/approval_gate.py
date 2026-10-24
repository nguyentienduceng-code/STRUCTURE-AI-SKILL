#!/usr/bin/env python3
"""
Approval Gate Middleware — Cổng phê duyệt trước khi thực thi pipeline.

Module này enforce Pre-Execution Approval Gate theo AGENTS.md §3:
- Chặn mọi pipeline >= 2 stages hoặc >= 3 tool calls
- Hiển thị Approval Card cho user
- Quản lý state machine PENDING → APPROVED/REJECTED

Version: 1.0.0
Created: 2026-10-12
Author: AI Assistant - Phase 1 Enhancement
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import json
import argparse
from pathlib import Path
from typing import Optional, Callable
from dataclasses import dataclass, field

# Import từ cùng package
from approval_state import (
    ApprovalContext,
    ExecutionStatus,
    ApprovalLevel,
    ApprovalLevel,
    generate_request_id,
    is_affirmative_response,
    is_negative_response,
    determine_approval_level,
    TOKEN_WARNING_THRESHOLD,
    TOKEN_CRITICAL_THRESHOLD,
)


# =============================================================================
# CONFIGURATION
# =============================================================================

SCRIPT_DIR = Path(__file__).parent
DEFAULT_OUTPUT_DIR = SCRIPT_DIR / "_approval_cache"


# =============================================================================
# APPROVAL CARD GENERATOR
# =============================================================================

class ApprovalCardGenerator:
    """
    Tạo Approval Card theo định dạng chuẩn trong AGENTS.md §3.2.
    """

    @staticmethod
    def generate(ctx: ApprovalContext) -> str:
        """
        Tạo Approval Card markdown.

        Format chuẩn:
        ### 📋 ĐỀ XUẤT KẾ HOẠCH TRIỂN KHAI (CHỜ DUYỆT)
        """
        # Geometry section
        geo = ctx.extracted_geometry
        geo_lines = []
        if geo:
            if geo.get('b') and geo.get('h'):
                geo_lines.append(f"- Hình học: b = {geo['b']}mm, h = {geo['h']}mm")
            if geo.get('L'):
                geo_lines.append(f"- Nhịp: L = {geo['L']}m")
            if geo.get('thickness'):
                geo_lines.append(f"- Chiều dày: {geo['thickness']}mm")
        if not geo_lines:
            geo_lines.append("- Hình học: Chưa trích xuất được ⚠️")
        geo_section = "\n".join(geo_lines)

        # Material section
        mat = ctx.extracted_materials
        mat_lines = []
        if mat:
            if mat.get('concrete'):
                mat_lines.append(f"- Bê tông: {mat['concrete']}")
            steel_val = mat.get('steel') or mat.get('rebar') or mat.get('steel_grade')
            if steel_val:
                mat_lines.append(f"- Thép: {steel_val}")
        if not mat_lines:
            mat_lines.append("- Vật liệu: Chưa trích xuất được ⚠️")
        mat_section = "\n".join(mat_lines)

        # Loads section
        loads = ctx.extracted_loads
        load_lines = []
        if loads:
            if loads.get('M'):
                load_lines.append(f"- Momen: M = {loads['M']} kNm")
            if loads.get('V'):
                load_lines.append(f"- Lực cắt: V = {loads['V']} kN")
            if loads.get('N'):
                load_lines.append(f"- Lực dọc: N = {loads['N']} kN")
            if loads.get('q'):
                load_lines.append(f"- Tải rải: q = {loads['q']} kN/m")
        if not load_lines:
            load_lines.append("- Tải trọng: Chưa trích xuất được ⚠️")
        load_section = "\n".join(load_lines)

        # Assumptions section
        if ctx.assumptions:
            assumptions_section = "\n".join(f"- ⚠️ `{a}` **[ASSUMED]**" for a in ctx.assumptions)
        else:
            assumptions_section = "- Không có giả định"

        # Stages section
        stages_section = "\n".join(
            f"  {i+1}. `{s}`" for i, s in enumerate(ctx.stages)
        )

        # Products section
        if ctx.expected_products:
            products_section = "\n".join(f"  - 📄 {p}" for p in ctx.expected_products)
        else:
            products_section = "  - 📄 Kết quả tính toán JSON\n  - 📄 Bản vẽ PNG (nếu cần)"

        # Token warning
        token_warning = ""
        if ctx.estimated_tokens >= TOKEN_CRITICAL_THRESHOLD:
            token_warning = f"\n⚠️ **CẢNH BÁO:** Ước tính ~{ctx.estimated_tokens:,} tokens — Pipeline nặng!"
        elif ctx.estimated_tokens >= TOKEN_WARNING_THRESHOLD:
            token_warning = f"\n⚠️ Lưu ý: ~{ctx.estimated_tokens:,} tokens"

        # Repair iteration warning
        repair_warning = ""
        if ctx.repair_iterations > 0:
            repair_warning = f"\n🔄 **Lần thử lại #{ctx.repair_iterations}/{ctx.max_repair_iterations}**"

        # Build card
        card = f"""
### 📋 ĐỀ XUẤT KẾ HOẠCH TRIỂN KHAI (CHỜ DUYỆT)

* **Mục tiêu nhận diện:** {ctx.user_prompt}
* **Pipeline ID:** `{ctx.pipeline_id or 'N/A'}`
{repair_warning}

* **Thông số đầu vào trích xuất:**
{geo_section}
{mat_section}
{load_section}

* **Giả định kỹ thuật:**
{assumptions_section}

* **Chuỗi Kỹ năng Đề xuất ({ctx.total_stages} stages):**
{stages_section}

* **Sản phẩm bàn giao:**
{products_section}

* **Dự toán thực thi:** ~{ctx.estimated_tokens:,} tokens{token_warning}

---

👉 **Anh/chị có đồng ý để hệ thống bắt đầu tính toán không?**
*(Gõ: "OK", "Đồng ý", "Duyệt", "Có" để tiếp tục)*
*(Gõ: "Không", "Hủy", "Dừng" để hủy bỏ)*
"""
        return card.strip()


# =============================================================================
# APPROVAL GATE
# =============================================================================

class ApprovalGate:
    """
    Middleware enforce Pre-Execution Approval.

    Workflow:
    1. intercept() — Kiểm tra xem có cần approval không
    2. hold() — Lưu context và hiển thị Approval Card
    3. validate_response() — Parse response từ user
    4. approve/reject() — Cập nhật trạng thái
    """

    def __init__(self, output_dir: str = None, max_repair_iterations: int = 3):
        self.output_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_repair_iterations = max_repair_iterations

        # In-memory cache cho current pending request
        self._current_context: Optional[ApprovalContext] = None
        self._approval_cache_file = self.output_dir / "_pending_approval.json"

        # Load cache nếu có
        self._load_cache()

    def _load_cache(self):
        """Load pending approval từ file cache."""
        if self._approval_cache_file.exists():
            try:
                data = json.loads(self._approval_cache_file.read_text(encoding='utf-8'))
                self._current_context = ApprovalContext.from_dict(data)
            except Exception:
                pass  # Ignore cache corruption

    def _save_cache(self):
        """Save pending approval vào file cache."""
        if self._current_context:
            self._approval_cache_file.write_text(
                json.dumps(self._current_context.to_dict(), ensure_ascii=False, indent=2),
                encoding='utf-8'
            )

    def _clear_cache(self):
        """Xóa cache."""
        if self._approval_cache_file.exists():
            self._approval_cache_file.unlink()
        self._current_context = None

    # =========================================================================
    # MAIN INTERFACE
    # =========================================================================

    def intercept(
        self,
        prompt: str,
        pipeline_id: str = None,
        stages: list = None,
        estimated_tools: int = 0,
        estimated_tokens: int = 0,
        extracted_geometry: dict = None,
        extracted_materials: dict = None,
        extracted_loads: dict = None,
        assumptions: list = None,
        expected_products: list = None,
    ) -> tuple[bool, str]:
        """
        Kiểm tra xem có cần approval không.

        Args:
            prompt: User prompt gốc
            pipeline_id: ID của pipeline (nếu có)
            stages: Danh sách skills cần chạy
            estimated_tools: Số lượng tool calls ước tính
            estimated_tokens: Số tokens ước tính
            extracted_*: Kết quả entity extraction (nếu có)
            expected_products: List sản phẩm mong đợi

        Returns:
            tuple: (is_halted, approval_card_or_empty_string)
            - Nếu is_halted=True → trả về Approval Card
            - Nếu is_halted=False → không cần approval
        """
        # Xác định mức approval
        stages = stages or []
        total_stages = len(stages)

        approval_level, requires_approval = determine_approval_level(
            total_stages, estimated_tools, estimated_tokens
        )

        # Nếu không cần approval
        if not requires_approval:
            return False, ""

        # Tạo ApprovalContext
        ctx = ApprovalContext(
            request_id=generate_request_id(),
            user_prompt=prompt,
            pipeline_id=pipeline_id,
            stages=stages,
            total_stages=total_stages,
            estimated_tools=estimated_tools,
            estimated_tokens=estimated_tokens,
            extracted_geometry=extracted_geometry or {},
            extracted_materials=extracted_materials or {},
            extracted_loads=extracted_loads or {},
            assumptions=assumptions or [],
            expected_products=expected_products or [],
            approval_level=approval_level,
            requires_approval=True,
            max_repair_iterations=self.max_repair_iterations,
        )

        # Lưu context
        self._current_context = ctx
        self._save_cache()

        # Generate approval card
        card = ApprovalCardGenerator.generate(ctx)

        return True, card

    def validate_response(self, user_response: str) -> tuple[bool, Optional[str]]:
        """
        Validate response từ user.

        Args:
            user_response: Response từ user

        Returns:
            tuple: (is_approved, error_message_or_none)
        """
        if not self._current_context:
            return False, "No pending approval request"

        ctx = self._current_context

        # Kiểm tra trạng thái hiện tại
        if ctx.status != ExecutionStatus.PENDING:
            return False, f"Approval already processed: {ctx.status.value}"

        # Check negative response
        if is_negative_response(user_response):
            ctx.status = ExecutionStatus.REJECTED
            ctx.rejected_reason = user_response
            self._save_cache()
            return False, "User rejected the execution plan"

        # Check affirmative response
        if is_affirmative_response(user_response):
            ctx.status = ExecutionStatus.APPROVED
            ctx.approved_by = "user"
            ctx.approved_at = __import__('datetime').datetime.now().isoformat()
            self._save_cache()
            return True, None

        # Ambiguous response
        return False, f"Ambiguous response: '{user_response}'. Please confirm with 'OK', 'Đồng ý', or 'Duyệt'"

    def get_current_context(self) -> Optional[ApprovalContext]:
        """Lấy context của pending approval."""
        return self._current_context

    def approve(self) -> bool:
        """Manual approve (nếu cần)."""
        if self._current_context:
            self._current_context.status = ExecutionStatus.APPROVED
            self._current_context.approved_by = "manual"
            self._current_context.approved_at = __import__('datetime').datetime.now().isoformat()
            self._save_cache()
            return True
        return False

    def reject(self, reason: str = None) -> bool:
        """Manual reject."""
        if self._current_context:
            self._current_context.status = ExecutionStatus.REJECTED
            self._current_context.rejected_reason = reason or "Manual rejection"
            self._save_cache()
            return True
        return False

    def cancel(self):
        """Hủy pending approval."""
        self._clear_cache()

    def increment_repair(self) -> bool:
        """
        Tăng repair iteration.
        Trả về True nếu còn quota, False nếu đã quá limit.
        """
        if self._current_context:
            self._current_context.repair_iterations += 1

            if not self._current_context.can_retry():
                self._current_context.status = ExecutionStatus.FAILED
                self._current_context.rejected_reason = "Max repair iterations exceeded"
                self._save_cache()
                return False

            self._save_cache()
            return True
        return False

    def is_approved(self) -> bool:
        """Kiểm tra xem đã approved chưa."""
        return (
            self._current_context is not None and
            self._current_context.status == ExecutionStatus.APPROVED
        )

    def is_pending(self) -> bool:
        """Kiểm tra xem có pending request không."""
        return (
            self._current_context is not None and
            self._current_context.status == ExecutionStatus.PENDING
        )

    def get_status_summary(self) -> dict:
        """Lấy tóm tắt trạng thái."""
        if not self._current_context:
            return {"status": "none", "message": "No pending approval"}

        ctx = self._current_context

        summary = {
            "status": ctx.status.value,
            "request_id": ctx.request_id,
            "prompt_preview": ctx.user_prompt[:50] + "..." if len(ctx.user_prompt) > 50 else ctx.user_prompt,
            "stages": ctx.stages,
            "approval_level": ctx.approval_level.value,
            "estimated_tokens": ctx.estimated_tokens,
        }

        if ctx.repair_iterations > 0:
            summary["repair_iterations"] = f"{ctx.repair_iterations}/{ctx.max_repair_iterations}"

        return summary


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Approval Gate Middleware — Pre-Execution Approval Control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ví dụ:
  python approval_gate.py --intercept --prompt "Tính dầm B1" --stages Structural_Design_Engineer
  python approval_gate.py --validate --response "OK"
  python approval_gate.py --status
  python approval_gate.py --approve
  python approval_gate.py --reject --reason "Cần sửa lại"
        """
    )

    # Create gate instance
    gate = ApprovalGate()

    # Subcommands
    parser.add_argument("--intercept", action="store_true", help="Intercept và kiểm tra approval")
    parser.add_argument("--prompt", type=str, help="User prompt")
    parser.add_argument("--pipeline-id", type=str, help="Pipeline ID")
    parser.add_argument("--stages", type=str, nargs="+", help="Danh sách stages")
    parser.add_argument("--tools", type=int, default=0, help="Số tool calls ước tính")
    parser.add_argument("--tokens", type=int, default=0, help="Số tokens ước tính")

    parser.add_argument("--validate", action="store_true", help="Validate user response")
    parser.add_argument("--response", type=str, help="User response")

    parser.add_argument("--approve", action="store_true", help="Manual approve")
    parser.add_argument("--reject", action="store_true", help="Manual reject")
    parser.add_argument("--reason", type=str, help="Lý do reject")
    parser.add_argument("--cancel", action="store_true", help="Cancel pending approval")

    parser.add_argument("--status", action="store_true", help="Hiển thị trạng thái")
    parser.add_argument("--clear", action="store_true", help="Clear cache")

    args = parser.parse_args()

    # Handle commands
    if args.intercept and args.prompt:
        is_halted, card = gate.intercept(
            prompt=args.prompt,
            pipeline_id=args.pipeline_id,
            stages=args.stages or [],
            estimated_tools=args.tools,
            estimated_tokens=args.tokens,
        )

        if is_halted:
            print(card)
            print("\n" + "="*60)
            print("Approval Card đã được tạo. Chờ phản hồi từ user...")
            print("Để validate response, chạy:")
            print("  python approval_gate.py --validate --response 'OK'")
        else:
            print("✅ Không cần approval — Pipeline có thể chạy trực tiếp")

    elif args.validate and args.response:
        approved, error = gate.validate_response(args.response)
        if approved:
            print("✅ APPROVED — User đã đồng ý. Pipeline có thể thực thi.")
        else:
            print(f"❌ REJECTED: {error}")

    elif args.approve:
        if gate.approve():
            print("✅ Manual approval thành công")
        else:
            print("❌ Không có pending approval để approve")

    elif args.reject:
        gate.reject(args.reason)
        print(f"❌ Rejected với lý do: {args.reason or 'User request'}")

    elif args.cancel:
        gate.cancel()
        print("🗑️ Đã hủy pending approval")

    elif args.status:
        summary = gate.get_status_summary()
        print(json.dumps(summary, ensure_ascii=False, indent=2))

    elif args.clear:
        gate.cancel()
        print("🗑️ Cache đã được xóa")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
