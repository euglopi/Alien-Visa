import os

import orjson
from dotenv import load_dotenv
from openai import OpenAI

from models.criteria import ChatMessage, CriterionEvidence

load_dotenv()

# Detailed O-1A criteria with full USCIS guidance for educational prompts
O1A_CRITERIA_DETAILS = {
    "Awards": {
        "regulatory_language": "Documentation of the beneficiary's receipt of nationally or internationally recognized prizes or awards for excellence in the field of endeavor.",
        "what_uscis_evaluates": [
            "Whether the person was the recipient of prizes or awards in the field of endeavor",
            "Whether the award is a nationally or internationally recognized prize or award for excellence",
        ],
        "examples": [
            "Awards from well-known national institutions and well-known professional associations",
            "Certain doctoral dissertation awards and scholarships",
            "Certain awards recognizing presentations at nationally or internationally recognized conferences",
        ],
        "considerations": [
            "The criteria used to grant the awards or prizes",
            "The national or international significance of the awards or prizes in the field",
            "The number of awardees or prize recipients",
            "Limitations on eligible competitors",
        ],
        "notes": [
            "A person may rely on a team award, provided the person is one of the recipients",
            "This criterion does not require an award to have the same prestige as a Nobel Prize",
            "An award available only to persons within a single locality, employer, or school may have little national/international recognition",
            "An award open to members of a well-known national institution (including R1 or R2 doctoral universities) may be nationally recognized",
        ],
    },
    "Membership": {
        "regulatory_language": "Documentation of the beneficiary's membership in associations in the field for which classification is sought, which require outstanding achievements of their members, as judged by recognized national or international experts in their disciplines or fields.",
        "what_uscis_evaluates": [
            "Whether the association requires that members have outstanding achievements in the field as judged by recognized experts",
        ],
        "examples": [
            "Membership in certain professional associations",
            "Fellowships with certain organizations or institutions",
            "IEEE Fellow level membership (requires 'accomplishments that have contributed importantly to the advancement or application of engineering, science and technology')",
            "AAAI Fellow membership (based on 'significant, sustained contributions' to AI, judged by current fellows)",
        ],
        "does_not_qualify": [
            "Membership based solely on a level of education or years of experience",
            "Membership based on payment of a fee or subscribing to publications",
            "Membership based on a requirement for employment (such as union membership)",
        ],
    },
    "Published Material": {
        "regulatory_language": "Published material in professional or major trade publications or major media about the beneficiary, relating to the beneficiary's work in the field for which classification is sought. This evidence must include the title, date, and author of such published material and any necessary translation.",
        "what_uscis_evaluates": [
            "Whether the published material was related to the person and their specific work",
            "Whether the publication qualifies as a professional publication, major trade publication, or major media",
        ],
        "examples": [
            "Professional or major print publications (newspaper articles, journal articles, books, textbooks) regarding the beneficiary and their work",
            "Professional or major online publications regarding the beneficiary and their work",
            "Transcript of professional or major audio or video coverage of the beneficiary and their work",
        ],
        "considerations": [
            "Published material that includes only a brief citation or passing reference is NOT sufficient",
            "The beneficiary need not be the only subject; material covering a broader topic but including substantial discussion of the beneficiary's work qualifies",
            "Material focusing on work by a team qualifies if it mentions the beneficiary or documents their significant role",
            "Relevant factors include intended audience and relative circulation, readership, or viewership",
        ],
    },
    "Judging": {
        "regulatory_language": "Evidence of the beneficiary's participation on a panel, or individually, as a judge of the work of others in the same or in an allied field of specialization for which classification is sought.",
        "what_uscis_evaluates": [
            "Whether the person has acted as the judge of the work of others in the same or an allied field",
        ],
        "examples": [
            "Reviewer of abstracts or papers submitted for presentation at scholarly conferences",
            "Peer reviewer for scholarly publications",
            "Member of doctoral dissertation committees",
            "Peer reviewer for government research funding programs",
        ],
        "considerations": [
            "Must show actual participation in judging, not just invitations",
            "Example: A copy of a request from a journal to do a review, accompanied by evidence confirming the review was completed",
        ],
    },
    "Original Contributions": {
        "regulatory_language": "Evidence of the beneficiary's original scientific, scholarly, or business-related contributions of major significance in the field.",
        "what_uscis_evaluates": [
            "Whether the person has made original contributions in the field",
            "Whether the original contributions are of major significance to the field",
        ],
        "examples": [
            "Published materials about the significance of the beneficiary's original work",
            "Testimonials, letters, and affidavits about the beneficiary's original work and its significance",
            "Documentation that the work was cited at a level indicative of major significance",
            "Documentation that the work was published in a scholarly journal of distinguished reputation",
            "Patents or licenses deriving from the beneficiary's work",
            "Evidence of commercial use of the beneficiary's work (e.g., commercialization of a research innovation)",
            "Contributions to repositories of software, data, designs, protocols, or other technical resources with evidence of significant impact",
        ],
        "considerations": [
            "Evidence that work was funded, patented, or published does NOT alone establish major significance",
            "Published research that has provoked widespread commentary and high citations may be probative",
            "A patented technology that has attracted significant attention or commercialization may establish significance",
            "Detailed letters from experts explaining the nature and significance are valuable",
        ],
    },
    "Scholarly Articles": {
        "regulatory_language": "Evidence of the beneficiary's authorship of scholarly articles in the field, in professional journals, or other major media.",
        "what_uscis_evaluates": [
            "Whether the person has authored scholarly articles in the field",
            "Whether the publication qualifies as professional, major trade, or major media",
        ],
        "examples": [
            "Publications in professionally-relevant journals",
            "Published conference presentations at nationally or internationally recognized conferences",
        ],
        "considerations": [
            "The beneficiary must be a listed author but need not be the sole or first author",
            "A petitioner need NOT provide evidence that the work has been cited to meet this criterion",
            "Articles must be scholarly: reporting on original research, experimentation, or philosophical discourse",
            "Generally peer-reviewed with footnotes, endnotes, or bibliography",
            "In non-academic arenas, should be written for learned persons in that field",
        ],
    },
    "Critical Employment": {
        "regulatory_language": "Evidence that the beneficiary has been employed in a critical or essential capacity for organizations and establishments that have a distinguished reputation.",
        "what_uscis_evaluates": [
            "Whether the person has performed in a leading or critical role for an organization or establishment",
            "Whether the organization or establishment has a distinguished reputation",
        ],
        "examples": [
            "Faculty or research position for a distinguished academic department or program",
            "Research position for a distinguished non-academic institution, government entity, or company",
            "Principal or named investigator for a department that received a merit-based government award (e.g., SBIR grant)",
            "Member of a key committee or high-performing team within a distinguished organization",
            "Founder or co-founder of, or contributor of IP to, a startup business with a distinguished reputation",
            "Critical or essential supporting role for a distinguished organization",
        ],
        "critical_or_essential": [
            "Critical role: contributed in a way of significant importance to the organization's activities",
            "Essential role: role is or was integral to the entity",
            "A leadership role often qualifies as critical or essential",
            "It is the duties and performance, not the title, that determines if the role is critical",
        ],
        "distinguished_reputation": [
            "Scale of customer base, longevity, or relevant media coverage",
            "For academic departments: national rankings and receipt of government research grants",
            "For startups: evidence of significant funding from government entities, venture capital, angel investors",
        ],
    },
    "High Salary": {
        "regulatory_language": "Evidence that the beneficiary has either commanded a high salary or will command a high salary or other remuneration for services as evidenced by contracts or other reliable evidence.",
        "what_uscis_evaluates": [
            "Whether the person has commanded or will command a high salary or other remuneration",
        ],
        "examples": [
            "Tax returns, pay statements, or other evidence of past salary",
            "Contract, job offer letter, or other evidence of prospective salary",
            "Comparative wage or remuneration data for the beneficiary's field (e.g., compensation surveys)",
        ],
        "considerations": [
            "The burden is on the petitioner to provide evidence that compensation is high relative to others in the field",
            "Helpful resources: U.S. Bureau of Labor Statistics wage data, Department of Labor's Career One Stop",
            "For persons working outside the U.S.: evaluate based on wage statistics for that locality",
            "For entrepreneurs/founders: evidence of significant funding may help evaluate credibility of prospective salary evidence",
        ],
    },
}


def _format_criteria_details(criterion_name: str) -> str:
    """Format the detailed USCIS guidance for a criterion into readable text."""
    details = O1A_CRITERIA_DETAILS.get(criterion_name, {})
    if not details:
        return ""

    sections = []

    if "regulatory_language" in details:
        sections.append(
            f'**USCIS Regulatory Language:**\n"{details["regulatory_language"]}"'
        )

    if "what_uscis_evaluates" in details:
        items = "\n".join(f"- {item}" for item in details["what_uscis_evaluates"])
        sections.append(f"**What USCIS Evaluates:**\n{items}")

    if "examples" in details:
        items = "\n".join(f"- {item}" for item in details["examples"])
        sections.append(f"**Examples of Qualifying Evidence:**\n{items}")

    if "considerations" in details:
        items = "\n".join(f"- {item}" for item in details["considerations"])
        sections.append(f"**Key Considerations:**\n{items}")

    if "does_not_qualify" in details:
        items = "\n".join(f"- {item}" for item in details["does_not_qualify"])
        sections.append(f"**What Does NOT Qualify:**\n{items}")

    if "notes" in details:
        items = "\n".join(f"- {item}" for item in details["notes"])
        sections.append(f"**Important Notes:**\n{items}")

    if "critical_or_essential" in details:
        items = "\n".join(f"- {item}" for item in details["critical_or_essential"])
        sections.append(f"**What Makes a Role Critical/Essential:**\n{items}")

    if "distinguished_reputation" in details:
        items = "\n".join(f"- {item}" for item in details["distinguished_reputation"])
        sections.append(f"**What Makes an Organization Distinguished:**\n{items}")

    return "\n\n".join(sections)


def start_challenge(criterion: CriterionEvidence, resume_text: str) -> dict:
    """Generate initial educational message and prompt suggestions.

    Args:
        criterion: The criterion being challenged
        resume_text: Raw text from the parsed resume

    Returns:
        Dict with 'message' (initial assistant message) and 'suggestions' (list of prompt suggestions)
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    status = "MET" if criterion.met else "NOT MET"

    system_prompt = f"""You are a friendly O-1A visa advisor having a casual conversation.

CRITERION: "{criterion.name}"
USCIS DEFINITION: "{O1A_CRITERIA_DETAILS.get(criterion.name, {}).get("regulatory_language", criterion.description)}"

CURRENT STATUS: {status}
REASONING: {criterion.reasoning}

Respond with JSON in this exact format:
{{
  "message": "Your first message (under 50 words). One sentence about what this criterion looks for. One sentence about why it's {status}. One conversational question to explore evidence.",
  "suggestions": ["Short question 1?", "Short question 2?", "Short question 3?"]
}}

MESSAGE GUIDELINES:
- Write like you're texting a friend - casual, warm, direct
- No markdown, bullet points, or formal greetings

SUGGESTIONS GUIDELINES (these are things the USER might ask YOU):
- 2-3 short questions (under 8 words each)
- Written from the user's perspective, as if they're asking you
- Specific to the "{criterion.name}" criterion and their {status} status
- Examples: "How can I improve my score?", "What evidence are you looking for?", "Does my conference presentation count?"
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Resume context:\n{resume_text[:2000]}",
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=300,
    )

    data = orjson.loads(response.choices[0].message.content)
    return {
        "message": data.get("message", ""),
        "suggestions": data.get("suggestions", []),
    }


def process_chat_message(
    messages: list[ChatMessage],
    criterion: CriterionEvidence,
    resume_text: str,
    user_message: str,
) -> dict:
    """Process user message and generate assistant response with suggestions.

    Args:
        messages: Previous chat history
        criterion: The criterion being challenged
        resume_text: Raw text from the parsed resume
        user_message: The new message from the user

    Returns:
        Dict with 'message' (assistant response) and 'suggestions' (list of prompt suggestions)
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    status = "MET" if criterion.met else "NOT MET"

    # Reference material for the LLM (not shown to user)
    criteria_details = _format_criteria_details(criterion.name)

    system_prompt = f"""You are a friendly O-1A visa advisor chatting casually. Keep responses SHORT (2-3 sentences max).

CRITERION: "{criterion.name}"
CURRENT STATUS: {status}

USCIS GUIDANCE (for your reference, don't dump this on the user):
{criteria_details}

Respond with JSON in this exact format:
{{
  "message": "Your response (2-3 sentences max)",
  "suggestions": ["Short question 1?", "Short question 2?", "Short question 3?"]
}}

MESSAGE STYLE:
- Casual, like texting a knowledgeable friend
- Ask ONE follow-up question at a time
- When they share something relevant, acknowledge it briefly and dig deeper for specifics (names, numbers, dates, impact)
- After a few good exchanges, mention they can hit "Request Rescore" if they feel ready

SUGGESTIONS (things the USER might ask YOU next):
- 2-3 short questions (under 8 words each)
- Written from the user's perspective
- Relevant to what was just discussed
- Examples: "How can I improve my score?", "What evidence are you looking for?", "Does that count as evidence?"
"""

    # Build message history for the API
    api_messages = [{"role": "system", "content": system_prompt}]
    for msg in messages:
        api_messages.append({"role": msg.role, "content": msg.content})
    api_messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=api_messages,
        response_format={"type": "json_object"},
        max_tokens=400,
    )

    data = orjson.loads(response.choices[0].message.content)
    return {
        "message": data.get("message", ""),
        "suggestions": data.get("suggestions", []),
    }


def rescore_criterion(
    criterion: CriterionEvidence,
    messages: list[ChatMessage],
    resume_text: str,
) -> CriterionEvidence:
    """Re-evaluate criterion with chat transcript as additional evidence.

    Args:
        criterion: The original criterion assessment
        messages: Full chat history from the challenge session
        resume_text: Raw text from the parsed resume

    Returns:
        Updated CriterionEvidence with new assessment
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Format chat transcript
    transcript = "\n".join(
        f"{'User' if m.role == 'user' else 'Assistant'}: {m.content}" for m in messages
    )

    criteria_details = _format_criteria_details(criterion.name)

    system_prompt = f"""You are an O-1A visa criteria analyst. Re-evaluate the "{criterion.name}" criterion based on the original resume AND the additional information gathered in the interview.

## EXACT USCIS GUIDANCE FOR THIS CRITERION

{criteria_details}

## ORIGINAL ASSESSMENT

- Met: {criterion.met}
- Evidence: {criterion.evidence or "None"}
- Reasoning: {criterion.reasoning or "None"}

## YOUR TASK

Analyze the interview transcript below alongside the resume. Consider ALL evidence from BOTH sources.

Be rigorous but fair:
- Only mark as "met" if there is clear evidence meeting USCIS evidentiary standards
- If the interview revealed qualifying evidence not in the resume, factor that in
- Explain your reasoning clearly, referencing specific evidence

Respond with a JSON object:
{{
  "met": true or false,
  "evidence": "Combined evidence from resume and interview that supports this criterion, or null if not met",
  "reasoning": "Clear explanation of why this criterion is or isn't met based on USCIS standards"
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"## RESUME\n\n{resume_text}\n\n---\n\n## INTERVIEW TRANSCRIPT\n\n{transcript}\n\n---\n\nPlease provide your updated assessment.",
            },
        ],
        response_format={"type": "json_object"},
        max_tokens=1024,
    )

    data = orjson.loads(response.choices[0].message.content)

    return CriterionEvidence(
        name=criterion.name,
        description=criterion.description,
        met=data["met"],
        evidence=data.get("evidence"),
        reasoning=data.get("reasoning"),
    )
