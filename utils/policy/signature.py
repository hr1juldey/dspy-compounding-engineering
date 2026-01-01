"""
Policy enforcement signature for DSPy agents.

This module defines the signature for policy validation that can be used
by agents to ensure their actions comply with the defined policies.
"""

from typing import List

import dspy


class PolicyCheckSignature(dspy.Signature):
    """
    Signature for validating actions against policy rules.

    DSPy agents can use this signature to check if their planned actions
    comply with the defined policies before executing them.
    """

    policy_rules: str = dspy.InputField(desc="The policy rules to validate against")
    planned_action: str = dspy.InputField(desc="The action the agent plans to take")
    context: str = dspy.InputField(desc="Context of the current task")

    is_compliant: bool = dspy.OutputField(desc="Whether the action complies with policies")
    violations: List[str] = dspy.OutputField(desc="List of policy violations found")
    suggestions: List[str] = dspy.OutputField(desc="Suggestions for making the action compliant")
    confidence: float = dspy.OutputField(desc="Confidence level in the assessment (0.0 to 1.0)")


class PolicyEnforcementSignature(dspy.Signature):
    """
    Signature for comprehensive policy enforcement.

    This signature takes a broader view, considering the overall task
    and ensuring all aspects of the agent's approach comply with policies.
    """

    policy_document: str = dspy.InputField(desc="Full policy document to enforce")
    current_task: str = dspy.InputField(desc="The current task being worked on")
    agent_reasoning: str = dspy.InputField(desc="The agent's current reasoning/plan")
    tools_available: List[str] = dspy.InputField(desc="List of tools available to the agent")

    compliance_status: str = dspy.OutputField(
        desc="Overall compliance status: 'compliant', 'partial', or 'non-compliant'"
    )
    critical_violations: List[str] = dspy.OutputField(
        desc="Critical policy violations that must be fixed"
    )
    warnings: List[str] = dspy.OutputField(desc="Less critical issues to consider")
    recommended_actions: List[str] = dspy.OutputField(
        desc="Recommended actions to ensure compliance"
    )
