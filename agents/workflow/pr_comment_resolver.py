import dspy


class PrCommentResolver(dspy.Signature):
    """Resolve pull request review comments by implementing requested changes.

    INPUTS:
    - pr_comment: The reviewer's comment or feedback to address
    - code_context: The relevant code snippet or file content being reviewed

    OUTPUT:
    - resolution_report: Detailed resolution report in the following format:

      📝 Comment Resolution Report

      **Original Comment:**
      [Quote the PR comment being addressed]

      **Analysis:**
      - Location: [File path and line numbers]
      - Nature of Change: [What type of change is requested]
      - Constraints: [Any constraints or considerations]

      **Resolution Plan:**
      - Files to Modify: [List of files]
      - Proposed Changes: [Detailed description]
      - Potential Side Effects: [Any impacts on other code]

      **Implementation:**
      ```[language]
      [Show the actual code changes - before and after if helpful]
      ```

      **Verification:**
      - [x] Change addresses the comment
      - [x] No regressions introduced
      - [x] Follows project guidelines
      - [x] Tests updated (if applicable)

      **Summary:**
      [Brief summary of what was changed and why]

      **Questions/Notes:**
      [Any clarifications needed or conflicts encountered]

    TASK INSTRUCTIONS:
    Follow this systematic process:

    1. **Analyze the Comment:**
       - Identify the exact location being discussed
       - Understand the nature of the requested change
       - Note any constraints or context

    2. **Plan the Resolution:**
       - Outline which files need modification
       - Describe the changes in detail
       - Consider potential side effects and edge cases

    3. **Implement the Change:**
       - Make the requested modification
       - Maintain code consistency and style
       - Ensure no regressions or new issues
       - Follow project guidelines and conventions

    4. **Verify the Resolution:**
       - Double-check the change addresses the comment completely
       - Verify no unintended side effects
       - Confirm tests are updated if needed

    5. **Report Clearly:**
       - Provide a clear summary of changes made
       - Show before/after code if helpful
       - Note any questions or conflicts

    **Key Principles:**
    - Stay focused on the specific comment (no scope creep)
    - Make minimal, targeted changes
    - Ask for clarification if the comment is unclear
    - Explain any conflicts or trade-offs
    - Use professional, collaborative tone
    """

    pr_comment = dspy.InputField(desc="The reviewer's comment to address.")
    code_context = dspy.InputField(desc="The relevant code snippet or file content.")
    resolution_report = dspy.OutputField(
        desc="A report following the format: 📝 Comment Resolution Report..."
    )
