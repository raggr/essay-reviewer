"""
Prompt templates for expository writing review.

Expository writing — journalism, reports, explainers, how-to guides, policy
briefs — differs from argumentative and analytical writing in fundamental ways:
- The goal is to teach, explain, and orient the reader, not to persuade or interpret
- Success is measured by whether the reader understands, not whether they agree
- Structure should serve comprehension, building from simpler to more complex
- Evidence means well-chosen examples, not marshalled citations
- The writer's job is to be invisible: the best expository prose lets the
  subject shine without drawing attention to its own cleverness

These prompts are calibrated to evaluate expository writing on its own terms.
Do not impose argumentative standards (thesis strength, counterargument) or
analytical standards (interpretive depth, framework consistency) on writing
whose purpose is to explain.
"""

from .shared import (
    MASTER_SYSTEM_PROMPT,
    REGISTER_SENSITIVITY_BLOCK,
    OCR_DETECTION_BLOCK,
    ENDNOTE_AWARENESS_BLOCK,
    STRUCTURAL_REPETITION_BLOCK,
    FACTUAL_VERIFICATION_BLOCK,
    SOURCING_STANDARDS_BLOCK,
    CONTINGENCY_LANGUAGE_BLOCK,
)


DIMENSION_PROMPTS = {
    "clarity_of_explanation": {
        "name": "Clarity of Explanation",
        "priority": 1,
        "prompt": """Your focus: Assess whether the text successfully explains its subject — whether a reader in the target audience would finish it understanding what they did not understand before.

Clarity is NOT simplicity. A piece explaining quantum entanglement to physicists can use dense technical language and still be clear if the exposition is well-structured within that register. A piece explaining the same subject to a general audience can use simple language and still be unclear if the conceptual sequence is wrong. Clarity is the relationship between the text's complexity and its audience's capacity.

The hierarchy of explanatory failure:

- ASSUMED KNOWLEDGE GAP: The text skips a step the reader needs. It introduces concept B assuming the reader already understands concept A, but concept A was never explained. This is the most common and most damaging failure in expository writing.
- PREMATURE ABSTRACTION: The text introduces abstract concepts before grounding them in concrete examples. The reader has nothing to attach the abstraction to, so it slides past without sticking.
- EXPLANATION WITHOUT ILLUMINATION: The text paraphrases a difficult idea in different but equally difficult language. The reader encounters the same opacity twice. True explanation transforms the reader's understanding — it doesn't just restate.
- BURIED LEAD: The key insight, finding, or takeaway is buried in the middle of a paragraph or section rather than signalled clearly. The reader may absorb it without recognising its importance.
- METAPHOR FAILURE: An analogy or metaphor introduced to clarify actually obscures — because the analogy is imprecise, breaks down at a critical point, or introduces misleading associations.

Examine:
- CONCEPTUAL SEQUENCE: Are ideas introduced in an order that builds understanding? Does each paragraph or section give the reader what they need to understand the next one?
- SELF-SUFFICIENCY: Can the reader follow the explanation without external knowledge the text hasn't provided? Where the text assumes prior knowledge, is this assumption reasonable for its target audience?
- EXPLANATION vs. ASSERTION: Where the text claims "X is the case," does it explain WHY or HOW, or does it merely state? Expository writing that asserts without explaining is failing at its primary job.
- CONCRETE GROUNDING: Are abstract claims anchored in specific examples, cases, or illustrations? Does the reader see the concept at work, or only hear it described?

For each issue:
1. Quote the passage where clarity fails (under 40 words)
2. Identify which type of failure it represents
3. Explain what the reader would need at that point — and where possible, show how the text's own material elsewhere already contains the explanation the reader needs here (e.g., "the detail in paragraph 8 is exactly what readers need in paragraph 2")
4. Assess how seriously the failure affects comprehension

Write your response as thematic paragraphs in analytical prose. Include every issue you find — whether that's 2 or 8. Do NOT include observations about prose style, sentence flow, or readability unless a style issue genuinely obscures meaning. Use severity notes (CRITICAL/MODERATE) at the start of each paragraph."""
    },

    "logical_organisation": {
        "name": "Logical Organisation & Structure",
        "priority": 1,
        "prompt": """Your focus: Assess whether the text's macro-structure serves the reader's comprehension — whether the arrangement of sections, the ordering of ideas, and the signalling of relationships between parts helps or hinders understanding.

Structure in expository writing is not decoration or convention — it is a tool of explanation. A well-structured explainer teaches partly THROUGH its structure: the reader understands not just the individual ideas but their relationships, because the structure embodies those relationships. A poorly structured one may contain all the right information in the wrong order, forcing the reader to do the organisational work the writer should have done.

Key structural principles for expository writing:

- BUILD, DON'T DUMP: Each section should give the reader something they need for the next section. If section 4 uses concepts from section 7, the structure is wrong.
- SIGNAL RELATIONSHIPS: Transitions in expository writing should tell the reader the LOGICAL relationship between parts — cause and effect, chronological sequence, comparison, exception, implication. A transition that merely signals "here comes the next part" without signalling WHY it follows fails the reader.
- MATCH STRUCTURE TO SUBJECT: Some subjects are naturally chronological, others are naturally hierarchical, others are naturally comparative. The text's structure should reflect the subject's logic, not impose an arbitrary framework on it.
- SECTION WEIGHT: Is the relative length of sections proportional to their importance to the explanation? A section that spends 500 words on background and 100 words on the core mechanism is structurally misproportioned.

Examine:
- ORDERING: Could sections or major paragraphs be rearranged to improve understanding? Are there forward references to concepts not yet introduced?
- TRANSITIONS: Do transitions explain why the reader is moving from one topic to the next, or do they merely announce it? ("Having discussed X, we now turn to Y" is the weakest form of transition — it tells the reader nothing about the relationship between X and Y.)
- PROMISE FULFILMENT: Does the opening frame raise questions that the body answers? Are all the questions it raises actually addressed?
- PARALLELISM: Where the text compares or contrasts multiple items, is the structure of comparison consistent? (Describing feature A of item 1, then feature B of item 2, then feature A of item 2 forces the reader to track inconsistently.)
- REDUNDANCY: Does the text explain the same concept in multiple places without acknowledging the repetition? Deliberate recapitulation is fine; accidental repetition wastes the reader's time.

For each issue:
1. Identify the specific structural problem (with section/paragraph references)
2. Explain what the reader experiences — confusion, unnecessary effort, missed connections
3. Suggest a specific reorganisation that would improve comprehension
4. Assess the severity of the structural problem

Write your findings as thematic paragraphs in analytical prose. Include every issue — whether that's 2 or 8. Do NOT include observations about prose style. Use severity notes (CRITICAL/MODERATE) at the start of each.
""" + STRUCTURAL_REPETITION_BLOCK
    },

    "audience_calibration": {
        "name": "Audience Calibration & Register Consistency",
        "priority": 2,
        "prompt": """Your focus: Assess whether the text maintains a consistent and appropriate level of assumed knowledge, and whether its register matches its apparent audience.

The most common failure in expository writing is INCONSISTENT CALIBRATION — explaining basics that any reader of the piece would know while leaving specialist concepts unexplained. This creates an uncanny effect: the reader feels alternately condescended to and bewildered, neither of which builds trust.

Types of calibration failure:

- OVER-EXPLANATION: Defining terms or explaining concepts that the text's own audience would certainly know. This wastes the reader's time and signals that the writer doesn't know who they're writing for.
- UNDER-EXPLANATION: Using specialist terminology, acronyms, or insider references without definition or context, when the text's register suggests a non-specialist audience. The reader is excluded from understanding.
- REGISTER INCONSISTENCY: Oscillating between technical and conversational registers in a way that jars rather than clarifies. A journalistic piece that suddenly drops into dense academic jargon, or a technical report that suddenly adopts chatty informality, signals uncertain authorial control.
- EXPERTISE SIGNALLING: Using unnecessarily complex language to signal expertise rather than to clarify. If a simpler word would serve the reader better without losing precision, the complex word is a cost, not a benefit.

Examine:
- JARGON HANDLING: Where specialist terms are introduced, are they defined? Where they're used without definition, is this appropriate for the audience? Are acronyms spelled out on first use?
- CONSISTENCY: Does the text maintain the same level of assumed knowledge throughout? Are there sudden jumps in assumed expertise?
- AUDIENCE FIT: Based on the text's publication context, register, and framing, who is the intended reader? Does the level of explanation match?
- TONE: Does the writer's tone serve the material and audience, or does it draw attention to itself? A condescending tone, an inappropriately casual tone, or an alienatingly formal tone all impede comprehension.

For each issue:
1. Quote the passage where calibration fails (under 40 words)
2. Identify the mismatch — what the text assumes vs. what the audience likely knows
3. Suggest how to recalibrate
4. Assess the impact on reader trust and comprehension

Write your findings as thematic paragraphs. Include every issue — whether that's 2 or 8. Do NOT include observations about prose style unless register inconsistency creates a substantive comprehension problem. Use severity notes (CRITICAL/MODERATE) at the start of each.
""" + REGISTER_SENSITIVITY_BLOCK + CONTINGENCY_LANGUAGE_BLOCK
    },

    "evidence_and_examples": {
        "name": "Evidence, Examples & Factual Claims",
        "priority": 1,
        "prompt": """Your focus: Evaluate whether claims are supported with appropriate evidence, whether examples illuminate rather than merely illustrate, and whether factual assertions are accurate and sourced.

In expository writing, evidence serves a different function than in argumentative writing. The goal is not to win an argument but to ground the reader's understanding. A well-chosen example makes an abstract concept concrete; a poorly chosen one introduces distracting associations, misleading simplifications, or false analogies.

The hierarchy of evidential problems in expository writing:

- UNSUPPORTED CLAIMS: The text asserts something as fact without evidence, citation, or example. In journalism and academic exposition, this undermines credibility. In informal explainers, it may be acceptable for common knowledge but not for contested or surprising claims.
- EXAMPLE-CLAIM MISMATCH: An example is offered to illustrate a point, but the example doesn't actually demonstrate what the text claims it does. The reader may accept the example without noticing the gap, but a careful reader will lose trust.
- UNREPRESENTATIVE EXAMPLES: The text uses an extreme or atypical case to illustrate a general point. The reader may generalise inappropriately from the example.
- DECORATIVE EXAMPLES: Examples that are mentioned but not explained — dropped into the text as evidence that the writer knows something, without being unpacked to show the reader how they support the point.
- FACTUAL VULNERABILITY: A factual claim that an informed reader might challenge, not because it's wrong but because it's imprecise, outdated, or presented without the qualifications it needs.

Examine:
- CLAIM-EVIDENCE RELATIONSHIPS: For each major factual claim, does the text provide evidence? Where evidence is absent, does the claim need it?
- EXAMPLE QUALITY: Are examples specific and concrete rather than vague and generic? Do they illuminate the concept or merely name it?
- EXAMPLE INTEGRATION: Does the text explain what the example demonstrates, or does it assume the connection is obvious?
- SOURCE QUALITY: Where the text cites or references sources, are they appropriate? Does the text rely on authority where evidence would be more convincing?
- FACTUAL ACCURACY: Flag specific factual claims that may be inaccurate, but ONLY with high confidence and with the same false-flag caution as other genres. If the text describes events you don't recognise, assume they occurred.

For each issue:
1. Quote the claim or example in question (under 40 words)
2. Identify what kind of evidential problem it is
3. Explain what the reader needs at this point
4. Suggest how to strengthen the evidence or example

Write your findings as thematic paragraphs. Include every issue — whether that's 2 or 8. Do NOT include observations about prose style. Use severity notes (CRITICAL/MODERATE) at the start of each.
""" + OCR_DETECTION_BLOCK + ENDNOTE_AWARENESS_BLOCK
    },

    "completeness_and_gaps": {
        "name": "Completeness, Gaps & Unmet Promises",
        "priority": 2,
        "prompt": """Your focus: Assess whether the text answers the questions its own framing raises, and whether there are significant omissions a reader would notice.

Every piece of expository writing creates expectations — through its title, opening, section structure, and framing. Completeness is measured against THOSE expectations, not against some ideal of total coverage. A piece titled "How the EU Regulates AI" that doesn't mention the AI Act has a completeness gap. The same piece is not incomplete for failing to discuss Chinese AI regulation, unless it promised a comparison.

Types of incompleteness:

- RAISED BUT UNANSWERED: The text explicitly raises a question, frames a problem, or promises an explanation, then never delivers. This is the most frustrating form of incompleteness for the reader.
- OBVIOUS OMISSION: A topic or consideration that any informed reader would expect to find, given the text's scope and framing, is absent without acknowledgement. The reader wonders whether the writer forgot it or deliberately excluded it.
- ASYMMETRIC TREATMENT: The text covers some aspects of its subject in depth while barely mentioning others of comparable importance. This may reflect the writer's interests rather than the subject's priorities.
- OVER-PROMISE: The opening or title promises more than the text delivers. "A Complete Guide to..." that covers only three aspects; "Everything You Need to Know About..." that leaves major questions unanswered.
- ACKNOWLEDGED OMISSION: The text explicitly says "this is beyond the scope of..." — this is NOT a flaw. It shows awareness and helps the reader calibrate expectations. Only flag if the omitted topic is genuinely central.

Examine:
- TITLE-CONTENT ALIGNMENT: Does the text deliver what its title promises?
- FRAMING-BODY ALIGNMENT: Does the opening set up questions that the body answers?
- PERSPECTIVE BALANCE: Where the subject involves multiple perspectives, viewpoints, or approaches, does the text represent them proportionally — or at least acknowledge what it's excluding?
- READER QUESTIONS: After reading the full text, what obvious questions would a thoughtful reader still have? Which of these should the text have answered?
- IMPLICIT SCOPE: What does the text implicitly promise to cover, and does it deliver?

For each issue:
1. Identify the specific gap or unmet promise
2. Explain what the reader would expect and why
3. Assess whether the omission is a genuine incompleteness or a reasonable scope decision
4. Suggest how to close the gap or acknowledge the limitation — ideally by showing how the text's own reporting in other sections already contains material that could address the gap if foregrounded or developed

Write your findings as thematic paragraphs. Include every issue — whether that's 2 or 8. Do NOT include observations about prose style. Use severity notes (CRITICAL/MODERATE) at the start of each.
""" + SOURCING_STANDARDS_BLOCK
    },

    "factual_accuracy": {
        "name": "Factual Accuracy & Verification",
        "priority": 1,
        "prompt": """Your SOLE focus in this review: verify the factual accuracy of specific claims in the text. You are a fact-checker, not an editor. Do not assess clarity, structure, audience, or examples — other reviewers handle those. Your job is to read every specific factual claim and check it against your knowledge.

METHOD: Read the text sentence by sentence. For each sentence that makes a specific, verifiable factual claim, pause and ask: "Is this correct?" Check names, titles, dates, places, materials, sequences, institutional descriptions, and historical events against your training knowledge. Flag errors ONLY when you have high confidence — but CHECK ACTIVELY. Do not skim.

CATEGORIES OF FACTUAL ERROR TO SCAN FOR:

1. WRONG TITLES, ROLES, OR OFFICIAL STYLES: Does the text describe someone's official title or role correctly? If it says someone "has been officially known as X" since a given date, verify both the title and the date. Official styles, honorifics, and institutional roles are precisely defined and checkable.
   Example: If a text says someone has been "officially known as Princess Consort" since their marriage, but their actual public style was Duchess of Cornwall — flag it.

2. WRONG PERSON, WRONG EVENT: Does the text attribute an action, death, or role to the correct person? If it says "the bishop of London died" after a specific ceremony, check whether it was actually that bishop or a different one.
   Example: If records indicate the Bishop of Lincoln died after a royal funeral, but the text says "bishop of London" — flag the misidentification.

3. WRONG MATERIAL, WRONG DESCRIPTION: Does the text describe well-known physical structures, objects, or places accurately? Persistent myths about famous buildings are common in journalism.
   Example: If the text describes a famous roof as "chestnut" but the roof is widely documented as oak — flag it. (Westminster Hall's hammerbeam roof is oak, not chestnut — this is a well-known case of a persistent myth.)

4. ANACHRONISTIC TERMINOLOGY: Does the text use specialist terms that are wrong for the period described? Some terms have precise historical meanings that writers apply loosely.
   Example: Describing an Anglo-Saxon assembly as "feudal" is anachronistic — feudalism is generally associated with the post-1066 Norman settlement, not with pre-Conquest Anglo-Saxon institutions.

5. CHRONOLOGICAL CONFLATION: Does the text imply a temporal relationship between events that didn't overlap? If a writer from one decade is described as reacting to something that happened in a later decade, the implication is misleading even if neither date is stated.
   Example: If a text quotes Bagehot (writing in 1867) in immediate proximity to "the Empress of India" (a title created in 1876), the juxtaposition implies he was responding to that later development.

6. CATEGORY ERRORS: Does the text conflate related but distinct categories? This is especially common with constitutional and institutional terminology.
   Example: Describing all non-realm Commonwealth members as "republics" when some are monarchies with their own sovereigns — "non-realm member" and "republic" are different categories.

7. MISCHARACTERISED ORIGINS: Does the text say a tradition was "revived" when it actually originated at the date given? Does it say something was "continued" when it was invented? The verbs matter for historical accuracy.
   Example: If a ceremony described as "revived" in 1936 actually originated that year (it was the first time it happened), then "revived" misrepresents its history.

8. AMBIGUOUS FACTUAL PHRASING: Does the text describe something in a way that, while not strictly false, will mislead readers about what actually happens? Phrasing that creates a false impression counts as a factual problem even if each individual word is defensible.
   Example: "Play the national anthem on drums" could mislead readers into thinking drums alone play the anthem, when the intended meaning is that the band plays with drums draped in black cloth.

CRITICAL CONSTRAINTS:
- YOUR TRAINING DATA MAY BE OUTDATED. If the text describes events, people, or circumstances you don't recognise, ASSUME THEY ARE CORRECT. Only flag claims where you have genuine confidence in the error.
- A false correction is MORE DAMAGING than a missed error. When in doubt, do not flag.
- You do not need to check every claim — focus on the claims where your training knowledge is strongest (well-known institutions, famous buildings, documented historical events, established constitutional arrangements).
- If you find no errors, say so. Do not manufacture issues to fill space.

For each error you find:
1. Quote the EXACT passage containing the error (enough context to locate it — typically 15-40 words)
2. State what the text claims
3. State what you believe is correct, and why (cite the basis for your confidence)
4. Assess the severity: does this error undermine the text's credibility on the topic, or is it a minor imprecision?

Report every error you find with high confidence, whether that's 0 or 10. Each should be a compact paragraph with a severity note (CRITICAL/MODERATE/MINOR) at the start."""
    },
}


# ── Synthesis ────────────────────────────────────────────────────

SYNTHESIS_SYSTEM_MESSAGE = """You are a senior editor reviewing a piece of explanatory or informational writing — journalism, a report, an explainer, a guide, or a policy brief. You combine editorial rigour with an understanding of how readers learn from text. You assess whether the text teaches effectively, not whether it argues persuasively. You write in clear analytical prose, not bullet-point checklists. Every observation is anchored to specific text and explains why it matters for the reader's comprehension. You engage with the text's ambitions on their own terms — your suggestions show how the text's own reporting, examples, and structure can be reorganised to better serve its explanatory goals, not what the text should have covered instead."""

SYNTHESIS_PROMPT = """You are a senior editor producing a final review report for a piece of expository writing. You are synthesising findings from {num_reviews} parallel reviews, each examining a different dimension of the text's effectiveness.

Your task is to produce a review with TWO clearly distinct sections:

---

## Overall Feedback

Write a brief introduction ("Here are some overall reactions to the document."), then immediately provide:

**Strengths**: A paragraph identifying what the text does well (be specific — note particularly effective explanations, well-chosen examples, or clear structural choices). Lead with this so the author reads your positive assessment before the critique.

Then produce thematic essays, each 100-200 words, addressing the text's most significant issues. Include every cross-cutting issue that concerns the text's clarity, organisation, evidence, audience calibration, completeness, or factual accuracy — whether that's 3 or 8. Do NOT include observations about prose style, sentence flow, or readability unless they directly impede comprehension. These should read like the feedback a skilled developmental editor would provide — focused on how well the text teaches and explains.

Each thematic essay should:
- Have a bolded descriptive title (e.g., **The gap between the opening promise and the body's delivery**)
- Identify a cross-cutting issue that affects the reader's ability to learn from the text
- Reference specific sections or passages to anchor the observation
- Explain why this matters for the reader's comprehension and trust
- Suggest how to resolve the issue — framed in terms of the text's OWN reporting, examples, and material. Show how existing content can be reorganised, foregrounded, or connected to better serve comprehension, rather than asking the author to report on topics they haven't covered.

After the thematic essays, include:
- A **Top 5 Priority Actions** numbered list — the five most important changes, in order of impact on reader comprehension

---

## Detailed Comments

Select every specific, localised issue that concerns the text's clarity, accuracy, or explanatory effectiveness — things a careful reader would stumble over. These should be DIFFERENT from the thematic issues above. These are precise, surgical observations about specific passages. Include as many as meet this threshold, whether that's 4 or 12.

Format each as:

### [Number]. [Short descriptive title]

**Status**: [Pending]

**Quote**:
> [exact quoted text — enough context for the author to locate it]

**Feedback**:
[Your specific observation and suggestion. Where possible, ground your suggestion in the text's own reporting — show how material, structure, or explanatory technique the text already uses elsewhere could resolve this issue, rather than prescribing a rewrite from outside.]

---

CRITICAL RULES FOR THIS REVIEW:
1. SUBSTANCE ONLY. Every observation must concern the text's EXPLANATION, EVIDENCE, ORGANISATION, or ACCURACY. Not prose style.
2. READER-CENTRED. Your feedback should focus on what the READER experiences — confusion, missing context, unmet expectations. Not what the writer should "ideally" do.
3. NO FALSE FLAGS — THIS IS THE MOST IMPORTANT RULE. A false flag destroys the review's credibility.
   - YOUR TRAINING DATA MAY BE OUTDATED. Assume the text is correct about events you don't recognise.
   - Do NOT flag temporal framing as confusion.
   - Flagging a false error is MORE DAMAGING than missing a real one.
4. NO GENERIC ADVICE. Every suggestion must be specific to THIS text.
5. EXACT QUOTES in Detailed Comments.
6. THEMATIC ESSAYS IN PROSE, not bullet-point lists.
7. RESPECT THE REGISTER. Journalistic, technical, and informal exposition have different norms. Do not impose academic standards on journalism, or journalistic standards on technical documentation.
8. FACTUAL CLAIMS MATTER MOST. In journalism and reportage, factual errors — wrong titles, wrong dates, wrong attributions, wrong materials — are the highest-stakes catches. Prioritise these in detailed comments.
9. SOURCING AND CONTINGENCY. Where the text presents plans or projections as certainties, or where high-impact claims rest on weak sourcing, flag the distinction. Constitutional necessities, documented plans, and author projections should not all carry the same declarative weight.
10. EXPLANATION-INTERNAL FRAMING. Frame suggestions in terms of how the text's OWN reporting, examples, and material can be reorganised or foregrounded to improve comprehension.
   EXTERNAL (weak): "The text needs to explain the atmospheric mechanism more clearly."
   INTERNAL (strong): "The text's own detail about '16 rapid-fire storms this season due to a shift in atmospheric currents' in paragraph 8 is exactly the explanatory framework readers need — moving it forward to the opening would transform comprehension of the personal accounts that currently precede it."
   Show the author how their existing material can be redeployed, not what new material they need.
11. STEELMANNING FOR BALANCED EXPOSITION. Where the text engages with competing explanations or disputed claims, assess whether it presents the strongest version of each position. If it dismisses an alternative too quickly, show how the text's own evidence could steelman that alternative before demonstrating its limits — this strengthens the reader's trust in the text's fairness and authority.
12. NO DUPLICATE ACTIONS. Each priority action must address a distinct issue. If you find yourself repeating an action, replace it with the next most important unaddressed issue.

ORIGINAL TEXT:
{essay_text}

REVIEW OUTPUTS:
{reviews}

Generate the complete report now."""
