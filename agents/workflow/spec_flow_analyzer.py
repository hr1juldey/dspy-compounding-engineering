import dspy


class SpecFlowAnalyzer(dspy.Signature):
    """Analyze user experience flows and identify specification gaps for features.

    INPUTS:
    - feature_description: The feature description, plan, or specification document to analyze
    - research_findings: Optional findings from research agents that provide additional context
      (can be None or empty string if not available)

    OUTPUT:
    - flow_analysis: Comprehensive markdown-formatted analysis structured as follows:

      ### User Flow Overview
      Clear, structured breakdown of all identified user flows. Use mermaid diagrams when
      helpful. Number each flow and describe it concisely.

      ### Flow Permutations Matrix
      Matrix or table showing different variations of each flow based on:
      - User state (logged in, guest, admin, etc.)
      - Context (first-time user, returning user, etc.)
      - Device/platform (mobile, desktop, tablet, etc.)
      - Other relevant dimensions

      ### Missing Elements & Gaps
      Organized by category, list all identified gaps:
      - Description: What is missing or unclear
      - Impact: How this affects implementation or user experience
      - Current Ambiguity: Why this needs clarification

      ### Critical Questions Requiring Clarification
      Numbered list of specific questions, prioritized as:
      1. Critical: Must be answered before implementation
      2. Important: Should be clarified early in development
      3. Nice-to-have: Can be deferred but worth considering

      ### Recommended Next Steps
      Concrete actions to resolve the gaps and questions

    TASK INSTRUCTIONS:
    - Map out ALL possible user flows and permutations through the feature
    - Identify gaps, ambiguities, and missing specifications
    - Ask specific, actionable clarifying questions about unclear elements
    - Consider edge cases and error states (failures, timeouts, invalid input)
    - Think through different user contexts and device scenarios
    - Highlight areas that need further definition before implementation
    - Present findings in a clear, structured markdown format
    - Use visual aids (mermaid diagrams) when they add clarity
    """

    feature_description: str = dspy.InputField(
        desc="The feature description, plan, or specification"
    )
    research_findings: str = dspy.InputField(
        desc="Findings from research agents (optional)", default=None
    )
    flow_analysis: str = dspy.OutputField(
        desc="The comprehensive flow analysis and gap identification"
    )
