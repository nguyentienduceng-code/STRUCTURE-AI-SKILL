# -*- coding: utf-8 -*-
"""Cognitive Architecture v2: deterministic regressions, adversarial DAGs and resource admission.
Run: python .agents/tests/test_cognitive_architecture_v2.py
These tests establish measured coverage, not a guarantee for every natural-language input.
"""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.agents/tools'))
sys.path.insert(0, str(ROOT / '.agents/skills/Global_Dispatcher/scripts'))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import json
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from intent_classifier import IntentClassifier
from pipeline_builder import PipelineBuilder
from system_controller import (LoopBreaker, TokenBudget, CircuitBreaker, CircuitState,
                               CircuitBreakerTripped, BlackboxRecorder, SystemController)

SDE = 'Structural_Design_Engineer'
VERIFY = 'SKILL_VERIFY'
REPORT = 'SKILL_PHULUC'
RFI = 'SKILL_RFI'

class TestDynamicDAG(unittest.TestCase):
    def setUp(self):
        self.builder = PipelineBuilder()
        self.classifier = IntentClassifier()

    def test_preserves_requested_order_not_priority(self):
        plan = self.builder.build([SDE, VERIFY, REPORT])
        self.assertEqual(plan['skills'], [SDE, VERIFY, REPORT])
        self.assertEqual(plan['topological_order'], [1, 2, 3])
        self.assertFalse(plan['parallel_opportunities'])

    def test_real_multi_step_prompt(self):
        result = self.classifier.classify('Phân tích địa chất SPT rồi tính móng cọc rồi lập phụ lục tính toán')
        self.assertTrue(result['is_pipeline'])
        self.assertEqual(result['pipeline']['skills'], ['SKILL_GEOTECH', SDE, REPORT])
        self.assertEqual(result['workflow']['graph_type'], 'DAG')
        self.assertEqual(result['workflow']['edges'], [{'from': 1, 'to': 2}, {'from': 2, 'to': 3}])

    def test_multiline_parallel_group_has_join_barrier(self):
        text = 'Tính dầm B1\nsong song vẽ mặt cắt và tính chi phí\nlập phụ lục tính toán'
        result = self.classifier.classify(text)
        self.assertTrue(result['is_pipeline'])
        plan = result['workflow']
        self.assertEqual(plan['execution_batches'], [[1], [2, 3], [4]])
        self.assertEqual(plan['stages'][3]['depends_on'], [2, 3])

    def test_duplicate_skill_keeps_distinct_nodes(self):
        plan = self.builder.plan('Tính dầm B1 rồi kiểm chứng chéo với ETABS rồi tính dầm B2')
        self.assertEqual(plan['skills'], [SDE, VERIFY, SDE])
        self.assertEqual(len(plan['stages']), 3)

    def test_fanout_and_join_are_real_dependencies(self):
        plan = self.builder.plan('Tính dầm B1 rồi song song vẽ mặt cắt và tính chi phí rồi lập phụ lục tính toán')
        self.assertEqual(plan['stages'][1]['depends_on'], [1])
        self.assertEqual(plan['stages'][2]['depends_on'], [1])
        self.assertEqual(plan['stages'][3]['depends_on'], [2, 3])
        self.assertEqual(plan['execution_batches'], [[1], [2, 3], [4]])
        self.assertEqual(self.builder.ready_stages(plan, {1: 'SUCCESS'})['ready'], [2, 3])
        self.assertEqual(self.builder.ready_stages(plan, {1: 'SUCCESS', 2: 'SUCCESS'})['ready'], [3])
        self.assertEqual(self.builder.ready_stages(plan, {1: 'SUCCESS', 2: 'SUCCESS', 3: 'SUCCESS'})['ready'], [4])
        self.assertEqual(len(plan['handoff_schemas']), 4)

    def conditional(self):
        return self.builder.plan('Kiểm chứng chéo với ETABS; nếu đạt thì xuất phụ lục tính toán; ngược lại tạo RFI')

    def test_if_success_skips_else(self):
        plan = self.conditional()
        self.assertEqual(plan['skills'], [VERIFY, REPORT, RFI])
        result = self.builder.ready_stages(plan, {1: 'SUCCESS'})
        self.assertEqual(result['ready'], [2])
        self.assertEqual(result['skipped'], [3])

    def test_failure_branch_can_run_after_failed_check(self):
        result = self.builder.ready_stages(self.conditional(), {'1': {'status': 'FAILURE'}})
        self.assertEqual(result['ready'], [3])
        self.assertEqual(result['skipped'], [2])

    def test_missing_numeric_output_does_not_guess(self):
        plan = self.builder.plan('Kiểm chứng chéo với ETABS; nếu eta > 0.9 thì tạo RFI')
        self.assertEqual(self.builder.ready_stages(plan, {1: 'SUCCESS'})['ready'], [])
        self.assertEqual(self.builder.ready_stages(plan, {1: {'status': 'SUCCESS', 'outputs': {'eta': .95}}})['ready'], [2])
        self.assertEqual(self.builder.ready_stages(plan, {1: {'status': 'SUCCESS', 'eta': .8}})['skipped'], [2])

    def test_nonfinite_output_never_satisfies_condition(self):
        plan = self.builder.plan('Kiểm chứng chéo với ETABS; nếu eta > 0.9 thì tạo RFI')
        for eta in [float('nan'), float('inf'), True, '0.95']:
            with self.subTest(eta=eta):
                self.assertFalse(self.builder.ready_stages(plan, {1: {'status': 'SUCCESS', 'eta': eta}})['ready'])

    def test_unknown_condition_fails_closed(self):
        result = self.classifier.classify('Tính dầm B1; nếu thời tiết thuận lợi thì xuất phụ lục tính toán')
        self.assertFalse(result['is_pipeline'])
        self.assertTrue(result['requires_clarification'])
        self.assertEqual(result['confidence_level'], 'LOW')
        self.assertTrue(result['workflow']['error'])

    def test_unresolved_step_not_silently_dropped(self):
        with self.assertRaises(ValueError):
            self.builder.plan('Tính dầm B1 rồi zzzqqq unknown action')

    def test_nested_condition_is_explicitly_rejected(self):
        with self.assertRaises(ValueError):
            self.builder.plan('Kiểm chứng chéo với ETABS; nếu đạt thì tính dầm B1; nếu eta > 1 thì tạo RFI')

    def test_else_without_if_rejected(self):
        with self.assertRaises(ValueError):
            self.builder.plan('Tính dầm B1; ngược lại tạo RFI')

    def test_negated_action_is_excluded(self):
        plan = self.builder.plan('Tính dầm B1 rồi không vẽ mặt cắt rồi lập phụ lục tính toán')
        self.assertEqual(plan['skills'], [SDE, REPORT])
        self.assertEqual(len(plan['excluded_clauses']), 1)

    def test_graph_rejects_cycles(self):
        with self.assertRaises(ValueError):
            self.builder.build_dag([{'skill': SDE, 'depends_on': [2]}, {'skill': VERIFY, 'depends_on': [1]}])

    def test_unknown_dependency_and_skill_rejected(self):
        for definitions in [[{'skill': SDE, 'depends_on': [99]}], [{'skill': 'invented_skill'}]]:
            with self.subTest(definitions=definitions), self.assertRaises(ValueError):
                self.builder.build_dag(definitions)

    def test_condition_source_must_be_an_edge(self):
        with self.assertRaises(ValueError):
            self.builder.build_dag([{'skill': SDE}, {'skill': REPORT,
                'condition': {'source_stage': 1, 'field': 'status', 'op': 'in', 'value': ['SUCCESS']}}])

    def test_failed_dependency_never_exports(self):
        plan = self.builder.build([SDE, REPORT])
        result = self.builder.ready_stages(plan, {1: 'FAILURE'})
        self.assertFalse(result['ready'])
        self.assertEqual(result['blocked'], [2])

    def test_skipped_dependency_propagates(self):
        plan = self.builder.build([SDE, VERIFY, REPORT])
        result = self.builder.ready_stages(plan, {1: 'SKIPPED'})
        self.assertEqual(result['skipped'], [2, 3])

    def test_mention_override_is_backward_compatible(self):
        result = self.classifier.classify('@DE tính cốt thép dầm B1')
        self.assertEqual(result['primary_skill'], 'Design_Evaluation')
        self.assertFalse(result['is_pipeline'])

    def test_plan_is_deterministic_and_json_serializable(self):
        text = 'Tính dầm B1 rồi kiểm chứng chéo với ETABS rồi xuất phụ lục tính toán'
        one, two = self.builder.plan(text), self.builder.plan(text)
        for plan in [one, two]:
            plan.pop('created_at')
        self.assertEqual(json.loads(json.dumps(one)), two)

    def test_join_after_if_else_waits_for_selected_branch(self):
        plan = self.builder.plan('Kiểm chứng chéo với ETABS; nếu đạt thì tính dầm B1; ngược lại tạo RFI rồi xuất phụ lục tính toán')
        self.assertEqual(plan['stages'][3]['depends_on'], [2, 3])
        self.assertEqual(self.builder.ready_stages(plan, {1: 'SUCCESS', 2: 'SUCCESS'})['ready'], [4])
        self.assertEqual(self.builder.ready_stages(plan, {1: 'FAILURE', 3: 'SUCCESS'})['ready'], [4])
        self.assertNotIn(4, self.builder.ready_stages(plan, {1: 'SUCCESS'})['ready'])

    def test_scheduler_does_not_trust_cached_topological_order(self):
        plan = self.builder.build([SDE, VERIFY, REPORT])
        plan['topological_order'] = []
        self.assertEqual(self.builder.ready_stages(plan, {})['ready'], [1])

    def test_null_output_remains_pending(self):
        plan = self.builder.plan('Kiểm chứng chéo với ETABS; nếu eta > 0.9 thì tạo RFI')
        self.assertFalse(self.builder.ready_stages(plan, {1: {'status': 'SUCCESS', 'outputs': None}})['ready'])

    def test_malformed_conditions_rejected_before_scheduling(self):
        for value in [True, float('nan'), '1.0', None]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.builder.build_dag([{'skill': SDE}, {'skill': RFI, 'depends_on': [1],
                    'condition': {'source_stage': 1, 'field': 'eta', 'op': '>', 'value': value}}])

    def test_stage_limit_is_enforced(self):
        limited = PipelineBuilder(max_stages=2)
        with self.assertRaises(ValueError):
            limited.plan('Tính dầm B1 rồi tính dầm B2 rồi tính dầm B3')

class TestLoopAndBudget(unittest.TestCase):
    def test_first_triangle_closure_has_evidence(self):
        loop = LoopBreaker(max_hops=20)
        results = [loop.record_hop(agent) for agent in ['A', 'B', 'C', 'A']]
        self.assertTrue(results[-1]['cycle_detected'])
        self.assertEqual(results[-1]['cycle_path'], ['A', 'B', 'C', 'A'])
        self.assertFalse(results[-1]['is_loop'])

    def test_triangle_trip_and_sticky_state(self):
        loop = LoopBreaker(max_hops=20)
        results = [loop.record_hop(a) for a in ['A', 'B', 'C']*2]
        self.assertTrue(results[-1]['is_loop'])
        self.assertEqual(results[-1]['cycle_length'], 3)
        self.assertTrue(loop.record_hop('unrelated')['is_loop'])
        loop.reset()
        self.assertFalse(loop.record_hop('A')['is_loop'])

    def test_one_cycle_policy(self):
        loop = LoopBreaker(max_hops=20, max_cycle_repeats=1)
        for a in ['A', 'B', 'C']:
            self.assertFalse(loop.record_hop(a)['is_loop'])
        self.assertTrue(loop.record_hop('A')['is_loop'])

    def test_long_cycle_after_prefix(self):
        loop = LoopBreaker(max_hops=40, max_cycle_repeats=3)
        sequence = ['prefix'] + ['A', 'B', 'C', 'D']*3
        for a in sequence[:-1]:
            self.assertFalse(loop.record_hop(a)['is_loop'])
        self.assertTrue(loop.record_hop(sequence[-1])['is_loop'])

    def test_single_actor_calls_are_not_multiagent_cycles(self):
        loop = LoopBreaker(max_hops=10)
        for _ in range(5):
            self.assertFalse(loop.record_hop('A')['is_loop'])

    def test_acyclic_walk_and_hop_limit(self):
        loop = LoopBreaker(max_hops=4)
        for a in ['A', 'B', 'C', 'D']:
            self.assertFalse(loop.record_hop(a)['is_loop'])
        self.assertEqual(loop.record_hop('E')['code'], 'MAX_HOPS')

    def test_budget_throttles_smaller_calls(self):
        budget = TokenBudget(100)
        self.assertTrue(budget.reserve(80)['allowed'])
        self.assertEqual(budget.status()['state'], 'THROTTLED')
        self.assertEqual(budget.reserve(11)['decision'], 'BUDGET_THROTTLED')
        self.assertEqual(budget.used, 80)
        self.assertTrue(budget.reserve(10)['allowed'])
        self.assertTrue(budget.reserve(10)['allowed'])
        self.assertEqual(budget.reserve(0)['decision'], 'BUDGET_EXHAUSTED')

    def test_zero_and_unlimited_budget(self):
        self.assertFalse(TokenBudget(0).reserve(0)['allowed'])
        unlimited = TokenBudget()
        self.assertTrue(unlimited.reserve(10**9)['allowed'])
        self.assertIsNone(unlimited.status()['remaining_tokens'])

    def test_invalid_cost_does_not_mutate_trajectory(self):
        loop = LoopBreaker(token_budget=100)
        for cost in [-1, True, 1.5, float('nan')]:
            with self.subTest(cost=cost), self.assertRaises(ValueError):
                loop.record_hop('A', cost)
        self.assertEqual(loop.trajectory, [])
        self.assertEqual(loop.budget.used, 0)

    def test_atomic_concurrent_budget_never_overspends(self):
        budget = TokenBudget(1000, throttle_ratio=.99, throttle_fraction=1)
        with ThreadPoolExecutor(max_workers=12) as pool:
            results = list(pool.map(lambda _: budget.reserve(10), range(200)))
        self.assertEqual(sum(x['allowed'] for x in results), 100)
        self.assertEqual(budget.used, 1000)

class TestControllerIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Isolated controller without mutating the application singleton.
        self.controller = object.__new__(SystemController)
        self.controller._init_controller()
        self.controller.recorder = BlackboxRecorder(Path(self.temp.name))
        self.controller.breakers = {}

    def rows(self):
        return [json.loads(line) for path in Path(self.temp.name).glob('traces/*.jsonl')
                for line in path.read_text(encoding='utf-8').splitlines()]

    def test_session_budgets_are_independent(self):
        a = self.controller.start_session('A', token_budget=10)
        b = self.controller.start_session('B', token_budget=10)
        self.assertTrue(self.controller.preflight_check('worker', 'read', session_id=a, estimated_tokens=10)['allowed'])
        self.assertFalse(self.controller.preflight_check('worker', 'read', session_id=a)['allowed'])
        self.assertTrue(self.controller.preflight_check('worker', 'read', session_id=b, estimated_tokens=1)['allowed'])
        self.assertTrue(self.controller.end_session(a))
        with self.assertRaises(ValueError):
            self.controller.preflight_check('worker', 'read', session_id=a)

    def test_unknown_session_and_duplicate_session_fail(self):
        self.controller.start_session('known')
        with self.assertRaises(ValueError):
            self.controller.start_session('known')
        with self.assertRaises(ValueError):
            self.controller.preflight_check('A', 'read', session_id='unknown')

    def test_budget_block_keeps_approval_and_never_executes(self):
        session = self.controller.start_session(token_budget=0)
        self.controller.approve('delete_member')
        called = []
        result = self.controller.execute('A', 'delete_member', lambda: called.append(True), session_id=session)
        self.assertFalse(result['allowed'])
        self.assertTrue(self.controller.is_approved('delete_member'))
        self.assertFalse(called)
        self.assertEqual(self.rows()[-1]['action'], 'BUDGET_EXHAUSTED')

    def test_live_triangle_and_budget_events_have_shared_trace(self):
        session = self.controller.start_session(token_budget=100)
        first = self.controller.preflight_check('A', 'read', session_id=session, estimated_tokens=80)
        self.assertTrue(first['allowed'])
        for actor in ['B', 'C', 'A', 'B', 'C']:
            last = self.controller.preflight_check(actor, 'read', session_id=session)
        self.assertEqual(last['status'], 'LOOP_BLOCKED')
        rows = self.rows()
        self.assertTrue(any(x['action'] == 'BUDGET_THROTTLED' for x in rows))
        self.assertTrue(any(x['action'] == 'LOOP_BLOCKED' for x in rows))
        self.assertEqual({x['trace_id'] for x in rows}, {first['trace_id']})

    def test_circuit_trip_error_and_recovery_are_persisted(self):
        session = self.controller.start_session('circuit')
        cb = self.controller.get_breaker('etabs_api')
        cb.failure_threshold = 1
        with self.assertRaisesRegex(RuntimeError, 'service-down'):
            self.controller.execute('A', 'etabs_read', lambda: (_ for _ in ()).throw(RuntimeError('service-down')), session_id=session)
        self.assertEqual(cb.state, CircuitState.OPEN)
        denied = self.controller.execute('B', 'etabs_read', lambda: self.fail('Must not execute'), session_id=session)
        self.assertEqual(denied['status'], 'CIRCUIT_OPEN')
        cb.last_failure_time = 0
        with patch('system_controller.time.time', return_value=1000):
            self.assertEqual(self.controller.execute('C', 'etabs_read', lambda: 7, session_id=session)['result'], 7)
        rows = self.rows()
        self.assertTrue(any('service-down' in (x.get('error') or '') for x in rows))
        self.assertTrue(any(x['action'] == 'CIRCUIT_RECOVERED:etabs_api' for x in rows))
        self.assertEqual(len({x['trace_id'] for x in rows}), 1)

    def test_half_open_allows_single_concurrent_probe(self):
        cb = CircuitBreaker('probe', failure_threshold=1, recovery_timeout=0,
                            recorder=self.controller.recorder)
        cb.record_failure()
        entered, release = threading.Event(), threading.Event()
        def action():
            entered.set()
            if not release.wait(3):
                raise TimeoutError('test synchronization')
            return 1
        with ThreadPoolExecutor(max_workers=2) as pool:
            future = pool.submit(cb.call, action)
            self.assertTrue(entered.wait(3))
            try:
                with self.assertRaises(CircuitBreakerTripped):
                    cb.call(lambda: 2)
            finally:
                release.set()
            self.assertEqual(future.result(3), 1)
        self.assertEqual(cb.state, CircuitState.CLOSED)

    def test_jsonl_parallel_writes_are_complete_lines(self):
        recorder = self.controller.recorder
        def emit(i):
            span = recorder.start_span('same-trace', 'worker', str(i))
            recorder.end_span(span, metadata={'n': i})
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(emit, range(40)))
        self.assertEqual(len(self.rows()), 40)
        self.assertEqual({x['metadata']['n'] for x in self.rows()}, set(range(40)))
        self.assertFalse(recorder.persistence_errors)

    def test_persistence_failure_is_observable(self):
        recorder = self.controller.recorder
        with patch('system_controller.os.fsync', side_effect=OSError('disk unavailable')):
            recorder.end_span(recorder.start_span('t', 'A', 'read'))
        self.assertIn('disk unavailable', recorder.export_summary()['persistence_errors'][0])

    def test_old_success_does_not_close_newly_open_circuit(self):
        cb = CircuitBreaker('generation', failure_threshold=1, recorder=self.controller.recorder)
        entered, release = threading.Event(), threading.Event()
        def slow_success():
            entered.set()
            if not release.wait(3):
                raise TimeoutError('test synchronization')
            return 'old success'
        with ThreadPoolExecutor(max_workers=2) as pool:
            old = pool.submit(cb.call, slow_success)
            self.assertTrue(entered.wait(3))
            try:
                with self.assertRaises(RuntimeError):
                    cb.call(lambda: (_ for _ in ()).throw(RuntimeError('trip')))
            finally:
                release.set()
            self.assertEqual(old.result(3), 'old success')
        self.assertEqual(cb.state, CircuitState.OPEN)

    def test_concurrent_controller_admission_matches_executed_work(self):
        session = self.controller.start_session('budget-concurrency', token_budget=100)
        performed = []
        lock = threading.Lock()
        def action():
            with lock:
                performed.append(True)
        def attempt(_):
            return self.controller.execute('same-worker', 'read', action, session_id=session, estimated_tokens=10)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(attempt, range(30)))
        self.assertEqual(len(performed), 10)
        self.assertEqual(sum(x['allowed'] for x in results), 10)
        self.assertEqual(self.controller._sessions[session]['loop'].budget.used, 100)

    def test_invalid_circuit_configuration(self):
        for threshold, timeout in [(0, 1), (True, 1), (2, -1), (2, float('nan'))]:
            with self.subTest(threshold=threshold, timeout=timeout), self.assertRaises(ValueError):
                CircuitBreaker('bad', threshold, timeout)

if __name__ == '__main__':
    unittest.main(verbosity=2)
