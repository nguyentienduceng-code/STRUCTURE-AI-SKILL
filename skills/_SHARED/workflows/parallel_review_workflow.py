"""
parallel_review_workflow.py — Workflow template cho parallel review

Cho phép review song song nhiều phần của hồ sơ:
- Dầm, cột, móng review cùng lúc
- Cross-verify sau đó
- Synthesize thành báo cáo

Usage:
    python parallel_review_workflow.py --project DUAN_A --scope "beam,column,foundation"
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

# =============================================================================
# WORKFLOW STAGES
# =============================================================================

@dataclass
class ReviewTask:
    """Một task review"""
    task_id: str
    task_type: str  # beam, column, foundation, connection
    element_ids: List[str]  # ["B1", "B2", "B3"]
    priority: int = 1  # 1=high, 2=medium, 3=low

@dataclass
class ReviewResult:
    """Kết quả của một review task"""
    task_id: str
    status: str  # PASS, FAIL, WARNING, PENDING
    findings: List[Dict] = field(default_factory=list)
    eta_summary: Dict[str, float] = field(default_factory=dict)  # element_id -> max_eta
    calculation_logs: List[Dict] = field(default_factory=list)

@dataclass
class WorkflowReport:
    """Report tổng hợp của workflow"""
    workflow_id: str
    project_code: str
    start_time: str
    end_time: Optional[str] = None
    tasks: List[ReviewTask] = field(default_factory=list)
    results: List[ReviewResult] = field(default_factory=list)
    cross_verify_issues: List[Dict] = field(default_factory=list)
    synthesis: Optional[str] = None

# =============================================================================
# WORKFLOW ENGINE
# =============================================================================

class ParallelReviewWorkflow:
    """
    Workflow engine cho parallel review.

    Luồng:
    1. Parse scope (beam, column, foundation, connection)
    2. Tạo tasks cho mỗi loại
    3. (Simulate) Run tasks in parallel
    4. Collect results
    5. Cross-verify
    6. Synthesize report
    """

    def __init__(self, project_code: str, scope: List[str]):
        self.project_code = project_code
        self.scope = scope
        self.tasks: List[ReviewTask] = []
        self.results: List[ReviewResult] = []
        self.workflow_id = f"WRF-{datetime.now().strftime('%Y%m%d%H%M%S')}"

    def parse_scope(self, scope_str: str) -> List[str]:
        """Parse scope string thành list"""
        return [s.strip() for s in scope_str.split(',')]

    def generate_tasks(self, elements: Dict[str, List[str]]) -> List[ReviewTask]:
        """Tạo tasks từ elements"""
        tasks = []
        task_id = 1

        for task_type in self.scope:
            if task_type in elements:
                task = ReviewTask(
                    task_id=f"T{task_id:03d}",
                    task_type=task_type,
                    element_ids=elements[task_type]
                )
                tasks.append(task)
                task_id += 1

        self.tasks = tasks
        return tasks

    def run_parallel_review(self, skill_module: Any = None) -> List[ReviewResult]:
        """
        Chạy review song song (simulated).

        Trong thực tế, đây sẽ gọi AI agents để review mỗi phần.
        Hiện tại chỉ return placeholder results.
        """
        results = []

        for task in self.tasks:
            # Simulate review
            # Trong thực tế: gọi Design_Evaluation với scope cụ thể
            result = ReviewResult(
                task_id=task.task_id,
                status="PENDING",
                findings=[],
                eta_summary={e: 0.0 for e in task.element_ids}
            )
            results.append(result)

        self.results = results
        return results

    def cross_verify(self) -> List[Dict]:
        """
        Cross-verify giữa các kết quả.

        Kiểm tra:
        - Consistency của eta giữa các elements
        - Xung đột tiêu chuẩn
        - Calculation logs consistency
        """
        issues = []

        # Group results by task type
        by_type = {}
        for r in self.results:
            for t in self.tasks:
                if t.task_id == r.task_id:
                    if t.task_type not in by_type:
                        by_type[t.task_type] = []
                    by_type[t.task_type].append(r)

        # Check for high eta values
        for task_type, results in by_type.items():
            for result in results:
                for elem_id, eta in result.eta_summary.items():
                    if eta > 0.95:
                        issues.append({
                            "type": "HIGH_UTILIZATION",
                            "element": elem_id,
                            "eta": eta,
                            "task": result.task_id,
                            "message": f"{elem_id} co eta = {eta:.1%} - sat nguong"
                        })

        self.cross_verify_issues = issues
        return issues

    def synthesize(self) -> str:
        """Tạo synthesis text"""
        total_elements = sum(len(t.element_ids) for t in self.tasks)
        pass_count = sum(1 for r in self.results if r.status == "PASS")
        fail_count = sum(1 for r in self.results if r.status == "FAIL")
        warning_count = sum(1 for r in self.results if r.status == "WARNING")

        synthesis = f"""
## Tong hop Parallel Review

**Project:** {self.project_code}
**Workflow ID:** {self.workflow_id}
**Scope:** {', '.join(self.scope)}
**Tong elements reviewed:** {total_elements}

### Ket qua tong quan:
- PASS: {pass_count} tasks
- FAIL: {fail_count} tasks
- WARNING: {warning_count} tasks

### Cross-verify Issues:
"""

        if self.cross_verify_issues:
            for i in self.cross_verify_issues:
                synthesis += f"- {i['type']}: {i['message']}\n"
        else:
            synthesis += "- Khong co issues\n"

        synthesis += "\n### Khuyen nghi:\n"
        if any(i['type'] == 'HIGH_UTILIZATION' for i in self.cross_verify_issues):
            synthesis += "Can review lai cac elements co eta cao truoc khi xuat bao cao.\n"
        else:
            synthesis += "Co the xuat bao cao sau khi duoc duyet.\n"

        self.synthesis = synthesis
        return synthesis

    def generate_report(self) -> WorkflowReport:
        """Generate full workflow report"""
        return WorkflowReport(
            workflow_id=self.workflow_id,
            project_code=self.project_code,
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            tasks=self.tasks,
            results=self.results,
            cross_verify_issues=self.cross_verify_issues,
            synthesis=self.synthesis
        )

# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Parallel Review Workflow")
    parser.add_argument("--project", required=True, help="Project code")
    parser.add_argument("--scope", required=True,
                        help="Scope: beam,column,foundation,connection (comma-separated)")
    parser.add_argument("--output", help="Output JSON file")

    args = parser.parse_args()

    workflow = ParallelReviewWorkflow(args.project, args.scope.split(','))

    print(f"Parallel Review Workflow: {workflow.workflow_id}")
    print(f"Project: {args.project}")
    print(f"Scope: {args.scope}")
    print()

    # Generate tasks
    # Sample elements - trong thực tế se parse tu input
    sample_elements = {
        "beam": ["B1", "B2", "B3", "B4", "B5"],
        "column": ["C1", "C2", "C3"],
        "foundation": ["F1", "F2", "F3"],
        "connection": ["N1", "N2", "N3"]
    }
    tasks = workflow.generate_tasks(sample_elements)

    print("Tasks:")
    for t in tasks:
        print(f"  {t.task_id}: {t.task_type} ({len(t.element_ids)} elements)")
    print()

    # Run parallel review (simulated)
    print("Running parallel review...")
    results = workflow.run_parallel_review(None)
    print("Review complete.")
    print()

    # Cross-verify
    print("Cross-verifying...")
    issues = workflow.cross_verify()
    print(f"Found {len(issues)} issues")
    print()

    # Synthesize
    synthesis = workflow.synthesize()
    print(synthesis)

    # Save report
    if args.output:
        report = workflow.generate_report()
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False, default=str)
        print(f"\nReport saved to: {args.output}")

if __name__ == "__main__":
    main()
