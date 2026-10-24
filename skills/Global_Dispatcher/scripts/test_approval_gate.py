#!/usr/bin/env python3
"""
Test Suite cho Approval Gate Module.

Chạy: python test_approval_gate.py

Version: 1.0.1 (Fixed: Ambiguous response handling)
Created: 2026-10-12
"""

import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import unittest
import tempfile
import shutil
from pathlib import Path

# Add script dir to path
SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPT_DIR))

from approval_state import (
    ApprovalContext,
    ExecutionStatus,
    ApprovalLevel,
    generate_request_id,
    is_affirmative_response,
    is_negative_response,
    is_ambiguous_response,
    determine_approval_level,
    TOKEN_WARNING_THRESHOLD,
    TOKEN_CRITICAL_THRESHOLD,
)
from approval_gate import ApprovalGate, ApprovalCardGenerator


# =============================================================================
# TEST: Approval State
# =============================================================================

class TestApprovalState(unittest.TestCase):
    """Test cases cho ApprovalState module."""

    def test_generate_request_id(self):
        """Test request ID generation."""
        id1 = generate_request_id()
        id2 = generate_request_id()

        self.assertTrue(id1.startswith("APR-"))
        self.assertNotEqual(id1, id2)  # Unique IDs

    def test_approval_context_creation(self):
        """Test ApprovalContext creation."""
        ctx = ApprovalContext(
            request_id="TEST-001",
            user_prompt="Test prompt",
            stages=["SkillA", "SkillB"],
            total_stages=2,
            estimated_tools=5,
            estimated_tokens=30000,
        )

        self.assertEqual(ctx.request_id, "TEST-001")
        self.assertEqual(ctx.total_stages, 2)
        self.assertEqual(ctx.status, ExecutionStatus.PENDING)
        self.assertTrue(ctx.needs_approval())
        self.assertTrue(ctx.can_retry())

    def test_approval_context_to_dict(self):
        """Test serialization."""
        ctx = ApprovalContext(
            request_id="TEST-002",
            user_prompt="Test",
            stages=["SkillA"],
        )

        data = ctx.to_dict()
        self.assertIsInstance(data, dict)
        self.assertEqual(data['request_id'], "TEST-002")
        self.assertEqual(data['status'], 'pending')

    def test_approval_context_from_dict(self):
        """Test deserialization."""
        data = {
            'request_id': 'TEST-003',
            'user_prompt': 'Test',
            'stages': ['SkillA'],
            'status': 'approved',
            'approval_level': 'low',
        }

        ctx = ApprovalContext.from_dict(data)
        self.assertEqual(ctx.request_id, 'TEST-003')
        self.assertEqual(ctx.status, ExecutionStatus.APPROVED)
        self.assertEqual(ctx.approval_level, ApprovalLevel.LOW)

    def test_repair_iterations(self):
        """Test repair iteration tracking."""
        ctx = ApprovalContext(
            request_id="TEST-004",
            max_repair_iterations=3,
        )

        self.assertTrue(ctx.can_retry())

        ctx.repair_iterations = 3
        self.assertFalse(ctx.can_retry())


# =============================================================================
# TEST: Approval Level Thresholds
# =============================================================================

class TestApprovalThresholds(unittest.TestCase):
    """Test cases cho approval level determination."""

    def test_no_approval_needed(self):
        """Test: 1 stage, 0-1 tools → no approval."""
        level, requires = determine_approval_level(1, 0, 0)
        self.assertEqual(level, ApprovalLevel.NONE)
        self.assertFalse(requires)

        level, requires = determine_approval_level(1, 1, 0)
        self.assertEqual(level, ApprovalLevel.NONE)
        self.assertFalse(requires)

    def test_low_approval(self):
        """Test: 1 stage với 2 tools → low approval."""
        level, requires = determine_approval_level(1, 2, 0)
        self.assertEqual(level, ApprovalLevel.LOW)
        self.assertTrue(requires)

    def test_medium_approval(self):
        """Test: 2 stages với 3+ tools → medium approval."""
        level, requires = determine_approval_level(2, 3, 0)
        self.assertEqual(level, ApprovalLevel.MEDIUM)
        self.assertTrue(requires)

        level, requires = determine_approval_level(3, 0, 0)
        self.assertEqual(level, ApprovalLevel.MEDIUM)
        self.assertTrue(requires)

    def test_high_approval(self):
        """Test: 5+ stages → high approval."""
        level, requires = determine_approval_level(5, 0, 0)
        self.assertEqual(level, ApprovalLevel.HIGH)
        self.assertTrue(requires)

    def test_token_thresholds(self):
        """Test token thresholds."""
        self.assertEqual(TOKEN_WARNING_THRESHOLD, 20000)
        self.assertEqual(TOKEN_CRITICAL_THRESHOLD, 50000)


# =============================================================================
# TEST: Response Parsing
# =============================================================================

class TestResponseParsing(unittest.TestCase):
    """Test cases cho response parsing."""

    def test_affirmative_responses(self):
        """Test các affirmative responses."""
        affirmatives = [
            "OK", "ok", "Oke", "oke",
            "đồng ý", "Đồng ý", "đồng ý!",
            "duyệt", "Duyệt",
            "có", "Có",
            "yes", "Yes", "YES",
            "proceed", "go", "thực hiện", "bắt đầu",
            "được", "tốt",
        ]

        for resp in affirmatives:
            self.assertTrue(
                is_affirmative_response(resp),
                f"Should be affirmative: '{resp}'"
            )

    def test_negative_responses(self):
        """Test các negative responses."""
        negatives = [
            "không", "Không", "no", "No",
            "từ chối", "hủy", "cancel",
            "dừng", "stop", "sửa",
            "chưa", "chưa đồng ý",
        ]

        for resp in negatives:
            self.assertTrue(
                is_negative_response(resp),
                f"Should be negative: '{resp}'"
            )

    def test_negative_does_not_catch_ambiguous(self):
        """Test: 'để tôi xem lại' không phải negative."""
        # Theo AGENTS.md §3: "để tôi xem lại" không phải negative/affirmative
        self.assertFalse(is_negative_response("để tôi xem lại"))
        self.assertFalse(is_affirmative_response("để tôi xem lại"))
        self.assertTrue(is_ambiguous_response("để tôi xem lại"))

    def test_ambiguous_responses(self):
        """Test các ambiguous responses."""
        ambiguous = [
            "để tôi xem lại",
            "chờ một chút",
            "cần suy nghĩ",
            "để xem",
        ]

        for resp in ambiguous:
            self.assertTrue(
                is_ambiguous_response(resp),
                f"Should be ambiguous: '{resp}'"
            )

    def test_affirmative_takes_priority(self):
        """Test: Affirmative keywords override ambiguous."""
        # "OK" là affirmative, không phải ambiguous
        self.assertTrue(is_affirmative_response("OK"))
        self.assertFalse(is_ambiguous_response("OK"))

    def test_negative_takes_priority(self):
        """Test: Negative keywords override ambiguous."""
        # "không" là negative, không phải ambiguous
        self.assertTrue(is_negative_response("không"))
        self.assertFalse(is_ambiguous_response("không"))


# =============================================================================
# TEST: Approval Gate
# =============================================================================

class TestApprovalGate(unittest.TestCase):
    """Test cases cho ApprovalGate class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.gate = ApprovalGate(output_dir=self.test_dir)

    def tearDown(self):
        """Clean up."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_intercept_single_stage_no_approval(self):
        """Test: 1 stage, 1 tool → không cần approval."""
        is_halted, card = self.gate.intercept(
            prompt="Simple query",
            stages=["SkillA"],
            estimated_tools=1,
            estimated_tokens=5000,
        )

        self.assertFalse(is_halted)
        self.assertEqual(card, "")

    def test_intercept_multi_stage_requires_approval(self):
        """Test: 2 stages → cần approval."""
        is_halted, card = self.gate.intercept(
            prompt="Complex query",
            stages=["SkillA", "SkillB"],
            estimated_tools=5,
            estimated_tokens=30000,
        )

        self.assertTrue(is_halted)
        self.assertIn("ĐỀ XUẤT KẾ HOẠCH TRIỂN KHAI", card)
        self.assertIn("CHỜ DUYỆT", card)

    def test_validate_affirmative_response(self):
        """Test validation affirmative response."""
        self.gate.intercept(
            prompt="Test",
            stages=["SkillA", "SkillB"],
            estimated_tools=3,
        )

        approved, error = self.gate.validate_response("OK")
        self.assertTrue(approved)
        self.assertIsNone(error)
        self.assertTrue(self.gate.is_approved())

    def test_validate_negative_response(self):
        """Test validation negative response."""
        self.gate.intercept(
            prompt="Test",
            stages=["SkillA", "SkillB"],
            estimated_tools=3,
        )

        approved, error = self.gate.validate_response("Không")
        self.assertFalse(approved)
        self.assertIsNotNone(error)

    def test_validate_ambiguous_response(self):
        """Test validation ambiguous response."""
        self.gate.intercept(
            prompt="Test",
            stages=["SkillA", "SkillB"],
            estimated_tools=3,
        )

        # Ambiguous responses được xử lý như negative
        approved, error = self.gate.validate_response("để tôi xem lại")
        self.assertFalse(approved)
        # Error message có thể là "Ambiguous" hoặc "User rejected"
        self.assertIn("Ambiguous", error)

    def test_manual_approve(self):
        """Test manual approve."""
        self.gate.intercept(
            prompt="Test",
            stages=["SkillA"],
            estimated_tools=5,  # Cần approval vì > 2 tools
        )

        result = self.gate.approve()
        self.assertTrue(result)
        self.assertTrue(self.gate.is_approved())

    def test_manual_reject(self):
        """Test manual reject."""
        self.gate.intercept(
            prompt="Test",
            stages=["SkillA", "SkillB"],
        )

        result = self.gate.reject("Test rejection")
        self.assertTrue(result)

        ctx = self.gate.get_current_context()
        self.assertEqual(ctx.status, ExecutionStatus.REJECTED)
        self.assertEqual(ctx.rejected_reason, "Test rejection")

    def test_cancel(self):
        """Test cancel."""
        self.gate.intercept(
            prompt="Test",
            stages=["SkillA", "SkillB"],
        )

        self.gate.cancel()
        self.assertFalse(self.gate.is_pending())
        self.assertIsNone(self.gate.get_current_context())

    def test_repair_iteration_limit(self):
        """Test repair iteration limit."""
        self.gate.intercept(
            prompt="Test",
            stages=["SkillA"],
            estimated_tools=5,
        )

        ctx = self.gate.get_current_context()
        self.assertEqual(ctx.repair_iterations, 0)

        # Increment 3 times (max)
        for i in range(3):
            can_retry = self.gate.increment_repair()
            if i < 2:
                self.assertTrue(can_retry)
            else:
                self.assertFalse(can_retry)
                self.assertEqual(ctx.status, ExecutionStatus.FAILED)

    def test_status_summary(self):
        """Test status summary."""
        self.gate.intercept(
            prompt="Test prompt",
            stages=["SkillA", "SkillB"],
            estimated_tokens=30000,
        )

        summary = self.gate.get_status_summary()
        self.assertEqual(summary['status'], 'pending')
        self.assertEqual(len(summary['stages']), 2)
        self.assertEqual(summary['estimated_tokens'], 30000)


# =============================================================================
# TEST: Approval Card Generator
# =============================================================================

class TestApprovalCardGenerator(unittest.TestCase):
    """Test cases cho ApprovalCardGenerator."""

    def test_generate_basic_card(self):
        """Test generate card với basic info."""
        ctx = ApprovalContext(
            request_id="TEST-CARD-001",
            user_prompt="Tính cốt thép dầm B1",
            stages=["Structural_Design_Engineer"],
            total_stages=1,
            estimated_tools=3,
            estimated_tokens=25000,
        )

        card = ApprovalCardGenerator.generate(ctx)

        self.assertIn("Tính cốt thép dầm B1", card)
        self.assertIn("Structural_Design_Engineer", card)
        self.assertIn("25,000", card)

    def test_generate_card_with_geometry(self):
        """Test generate card với geometry extracted."""
        ctx = ApprovalContext(
            request_id="TEST-CARD-002",
            user_prompt="Tính dầm",
            stages=["SDE", "DE"],
            total_stages=2,
            estimated_tokens=40000,
            extracted_geometry={
                'b': 300,
                'h': 600,
                'L': 6.0,
            },
        )

        card = ApprovalCardGenerator.generate(ctx)

        self.assertIn("300", card)
        self.assertIn("600", card)
        self.assertIn("6.0", card)

    def test_generate_card_with_materials(self):
        """Test generate card với materials."""
        ctx = ApprovalContext(
            request_id="TEST-CARD-003",
            user_prompt="Tính dầm",
            stages=["SDE"],
            extracted_materials={
                'concrete': 'B25',
                'steel': 'CB400-V',
            },
        )

        card = ApprovalCardGenerator.generate(ctx)

        self.assertIn("B25", card)
        self.assertIn("CB400-V", card)

    def test_generate_card_with_assumptions(self):
        """Test generate card với assumptions."""
        ctx = ApprovalContext(
            request_id="TEST-CARD-004",
            user_prompt="Tính dầm",
            stages=["SDE"],
            assumptions=[
                "Chiều dài neo = 40d",
                "Lớp bảo vệ = 25mm",
            ],
        )

        card = ApprovalCardGenerator.generate(ctx)

        self.assertIn("ASSUMED", card)
        self.assertIn("Chiều dài neo", card)

    def test_generate_card_with_repair_warning(self):
        """Test generate card với repair warning."""
        ctx = ApprovalContext(
            request_id="TEST-CARD-005",
            user_prompt="Tính dầm",
            stages=["SDE"],
            repair_iterations=2,
            max_repair_iterations=3,
        )

        card = ApprovalCardGenerator.generate(ctx)

        self.assertIn("Lần thử lại #2", card)
        self.assertIn("/3", card)

    def test_generate_card_token_warning(self):
        """Test generate card với token warning."""
        ctx = ApprovalContext(
            request_id="TEST-CARD-006",
            user_prompt="Tính dầm",
            stages=["SDE", "DE", "VE", "VI"],
            estimated_tokens=55000,  # > 50000 threshold
        )

        card = ApprovalCardGenerator.generate(ctx)

        self.assertIn("CẢNH BÁO", card)
        self.assertIn("55,000", card)


# =============================================================================
# RUN TESTS
# =============================================================================

def run_tests():
    """Run all tests."""
    print("=" * 70)
    print("  APPROVAL GATE TEST SUITE v1.0.1")
    print("=" * 70)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestApprovalState))
    suite.addTests(loader.loadTestsFromTestCase(TestApprovalThresholds))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseParsing))
    suite.addTests(loader.loadTestsFromTestCase(TestApprovalGate))
    suite.addTests(loader.loadTestsFromTestCase(TestApprovalCardGenerator))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("  TEST SUMMARY")
    print("=" * 70)
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Pass rate: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
    print("=" * 70)

    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
