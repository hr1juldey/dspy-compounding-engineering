import dspy


class EveryStyleEditor(dspy.Signature):
    """Review and edit text content according to Every's house style guide.

    INPUTS:
    - content_to_review: The text content to review (article, blog post, documentation, etc.)

    OUTPUT:
    - style_edits: Numbered list of suggested edits in the format:
      "Original quote" -> "Corrected version" (Rule: explanation)

      Example:
      1. "The company are launching" -> "The company is launching"
         (Rule: Companies are singular)
      2. "Click here for more" -> "Learn more about the API"
         (Rule: Hyperlinks should be 2-4 descriptive words)

    TASK INSTRUCTIONS:
    Follow Every's house style guide rules systematically:

    **Capitalization & Case:**
    - Headlines: Title case
    - Everything else: Sentence case
    - Job titles: Lowercase
    - Buttons: Sentence case

    **Grammar & Voice:**
    - Companies: Singular ("it")
    - Teams/people: Plural
    - Active voice over passive
    - Oxford commas: Yes
    - Commas between independent clauses only
    - Colons: Capitalize after only if independent clause follows

    **Word Choice:**
    - Remove: "actually", "very", "just"
    - Cut adverbs where possible
    - Direction: "earlier/later/previously" (not "above/below")
    - Quantity: "more/less/fewer" (not "over/under")
    - Avoid "We have"/"We get"
    - Avoid clichés and jargon
    - No "This" at sentence start without clear antecedent

    **Numbers & Quantities:**
    - Spell out 1-9 (except when starting with a year)
    - Numerals for 10+
    - Percentages: "7 percent" (spell out)
    - Large numbers: Use commas (1,000)
    - Money: "£1 billion"
    - "Two times faster" (not "2x", except "10x")

    **Formatting & Punctuation:**
    - Emphasis: Italics only (no bold/underline)
    - Ellipsis: No space after...
    - Em dashes: —like this— (no spaces, max 2 per paragraph)
    - Compound adjectives: Hyphenate (except -ly adverbs)
    - Titles (books/movies): Italicize
    - No slashes (use hyphens instead)
    - Punctuation: Outside parentheses (unless full sentence), inside quotes
    - Quotes: Single for quotes within quotes, comma before if introduced

    **Links & References:**
    - Hyperlinks: 2-4 descriptive words
    - Image credits: "Source: X/Name" or "Source: Website name"
    - Names: Full name on first mention, last name thereafter
    - People: Identify by company/title

    For each violation found:
    1. Quote the original text
    2. Provide the corrected version
    3. Cite the specific rule
    4. Maintain the author's voice and intent
    """

    content_to_review = dspy.InputField(desc="The text content (article, post, doc) to review.")
    style_edits = dspy.OutputField(
        desc="Numbered list of suggested edits: Quote Original -> Corrected Version "
        "(Rule Explanation)."
    )
