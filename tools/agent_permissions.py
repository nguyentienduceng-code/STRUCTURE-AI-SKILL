#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1 role/capability boundary for TRUSTED built-in Python workers.

This broker is not an OS sandbox for arbitrary hostile Python plugins. Workers
cannot register tools from documents, run shell strings, or approve/publish.
No remote LLM calls are made. Documents are inert data; the host assigns roles.
"""
import sys
from dataclasses import dataclass
from types import MappingProxyType

if hasattr(sys.stdout, 'reconfigure') and sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

from system_controller import ExecutionGuard, GuardDecision

ROLE_ACTORS = MappingProxyType({'intake': 'intake-agent', 'calculator': 'calculation-agent',
                               'verifier': 'independent-verifier', 'reporter': 'report-agent'})
ROLE_TOOLS = MappingProxyType({
    'intake': frozenset({'project.validate', 'project.bind'}),
    'calculator': frozenset({'project.calculate', 'solver.rc_pm_3d'}),
    'verifier': frozenset({'section.verify'}),
    'reporter': frozenset({'report.draft'}),
})
OPERATOR_ACTIONS = frozenset({'review.approve', 'review.reject', 'report.publish', 'run.extend_budget'})
STAGES = (
    ('validate', 'intake', 'project.validate', 'Design_Evaluation'),
    ('bind', 'intake', 'project.bind', 'Design_Evaluation'),
    ('calculate', 'calculator', 'project.calculate', 'Structural_Design_Engineer'),
    ('verify', 'verifier', 'section.verify', 'SKILL_VERIFY'),
    ('draft', 'reporter', 'report.draft', 'SKILL_PHULUC'),
)


class CapabilityDenied(PermissionError):
    pass


@dataclass(frozen=True)
class AgentPrincipal:
    role: str
    actor: str


class AgentToolBroker:
    def __init__(self, principal, handlers, on_admit=None):
        if not isinstance(principal, AgentPrincipal) or ROLE_ACTORS.get(principal.role) != principal.actor:
            raise CapabilityDenied('Unknown or impersonated worker identity')
        if set(handlers)-set().union(*ROLE_TOOLS.values()):
            raise CapabilityDenied('Unregistered handler; executable plugins cannot come from input data')
        self.principal = principal
        self._handlers = dict(handlers)
        self._on_admit = on_admit
        self._guard = ExecutionGuard('SAFE')

    def invoke(self, tool, payload):
        if tool not in ROLE_TOOLS[self.principal.role] or tool not in self._handlers:
            raise CapabilityDenied(f'{self.principal.actor} cannot invoke {tool}')
        if not isinstance(payload, dict):
            raise CapabilityDenied('Tool payload must be an object')
        # These keys are authority, never facts extracted from a document.
        if set(payload) & {'role', 'actor', 'tools', 'command', 'operator_token', 'approval', 'approve'}:
            raise CapabilityDenied('Input data cannot grant authority or carry executable instructions')
        verdict = self._guard.evaluate_tool_call(tool, {})
        if verdict['decision'] != GuardDecision.ALLOW.value:
            raise CapabilityDenied(verdict['reason'])
        if self._on_admit:
            self._on_admit(self.principal, tool)
        return self._handlers[tool](payload)
