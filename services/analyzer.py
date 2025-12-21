import os

import orjson
from dotenv import load_dotenv
from openai import OpenAI

from models.criteria import CriterionEvidence, O1Assessment
from models.resume import ParsedResume

load_dotenv()

# O-1A criteria with exact regulatory language from USCIS Policy Manual
O1A_CRITERIA = [
    {
        "name": "Awards",
        "description": "Nationally or internationally recognized prizes or awards for excellence in the field of endeavor",
    },
    {
        "name": "Membership",
        "description": "Membership in associations in the field which require outstanding achievements of their members, as judged by recognized national or international experts",
    },
    {
        "name": "Published Material",
        "description": "Published material in professional or major trade publications or major media about the beneficiary, relating to the beneficiary's work in the field",
    },
    {
        "name": "Judging",
        "description": "Participation on a panel, or individually, as a judge of the work of others in the same or in an allied field of specialization",
    },
    {
        "name": "Original Contributions",
        "description": "Original scientific, scholarly, or business-related contributions of major significance in the field",
    },
    {
        "name": "Scholarly Articles",
        "description": "Authorship of scholarly articles in the field, in professional journals, or other major media",
    },
    {
        "name": "Critical Employment",
        "description": "Employment in a critical or essential capacity for organizations and establishments that have a distinguished reputation",
    },
    {
        "name": "High Salary",
        "description": "High salary or other remuneration for services, as evidenced by contracts or other reliable evidence",
    },
]

SYSTEM_PROMPT = """You are an O-1A visa criteria analyst. Your task is to analyze a resume and determine which of the 8 O-1A visa criteria the candidate may meet based on the evidence in their resume.

The O-1A visa requires demonstrating extraordinary ability. A beneficiary must satisfy at least 3 of 8 evidentiary criteria.

For each criterion, you must:
1. Determine if there is clear, specific evidence in the resume that supports this criterion
2. If met, quote or summarize the specific evidence from the resume
3. Provide brief reasoning for your assessment

Be CONSERVATIVE in your assessment. Only mark a criterion as "met" if there is clear, explicit evidence in the resume. Do not infer or assume qualifications that are not stated.

The 8 O-1A criteria (with exact USCIS regulatory language):

1. AWARDS: "Documentation of the beneficiary's receipt of nationally or internationally recognized prizes or awards for excellence in the field of endeavor."
   - Must be for excellence in the field (not participation awards)
   - Must have national or international recognition

2. MEMBERSHIP: "Documentation of the beneficiary's membership in associations in the field for which classification is sought, which require outstanding achievements of their members, as judged by recognized national or international experts in their disciplines or fields."
   - Membership must require outstanding achievements (not just paying dues or having experience)
   - Must be judged by recognized experts

3. PUBLISHED MATERIAL: "Published material in professional or major trade publications or major media about the beneficiary, relating to the beneficiary's work in the field."
   - Material must be ABOUT the beneficiary (not just authored by them)
   - Must be in professional publications or major media

4. JUDGING: "Evidence of the beneficiary's participation on a panel, or individually, as a judge of the work of others in the same or in an allied field of specialization for which classification is sought."
   - Peer review, dissertation committees, grant review panels, conference review
   - Must show actual participation as judge

5. ORIGINAL CONTRIBUTIONS: "Evidence of the beneficiary's original scientific, scholarly, or business-related contributions of major significance in the field."
   - Must be ORIGINAL contributions
   - Must be of MAJOR SIGNIFICANCE (widely adopted, highly cited, commercially successful)

6. SCHOLARLY ARTICLES: "Evidence of the beneficiary's authorship of scholarly articles in the field, in professional journals, or other major media."
   - Must be scholarly/academic articles
   - Published in professional journals or major media

7. CRITICAL EMPLOYMENT: "Evidence that the beneficiary has been employed in a critical or essential capacity for organizations and establishments that have a distinguished reputation."
   - Role must be critical/essential (not just any employment)
   - Organization must have distinguished reputation

8. HIGH SALARY: "Evidence that the beneficiary has either commanded a high salary or will command a high salary or other remuneration for services as evidenced by contracts or other reliable evidence."
   - Must be demonstrably HIGH relative to the field
   - Requires evidence of actual compensation

Respond with a JSON object in this exact format:
{
  "criteria": [
    {
      "name": "Awards",
      "description": "Nationally or internationally recognized prizes or awards for excellence in the field of endeavor",
      "met": true/false,
      "evidence": "Specific evidence from resume or null if not met",
      "reasoning": "Brief explanation of why criterion is/isn't met"
    },
    ... (all 8 criteria in order)
  ]
}"""


def analyze_resume(parsed_resume: ParsedResume) -> O1Assessment:
    """Analyze a parsed resume against O-1A criteria using OpenAI.

    Args:
        parsed_resume: The parsed resume with extracted text

    Returns:
        O1Assessment with criteria analysis results
    """
    # Handle parse failures gracefully
    if not parsed_resume.parse_success or not parsed_resume.raw_text.strip():
        return _create_empty_assessment("Resume could not be parsed or is empty")

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Analyze this resume against the O-1A criteria:\n\n{parsed_resume.raw_text}",
                },
            ],
            response_format={"type": "json_object"},
            max_tokens=4096,
        )

        content = response.choices[0].message.content
        data = orjson.loads(content)

        return O1Assessment(criteria=[CriterionEvidence(**c) for c in data["criteria"]])

    except Exception as e:
        return _create_empty_assessment(f"Analysis failed: {e}")


def _create_empty_assessment(error_reason: str) -> O1Assessment:
    """Create an assessment with all criteria unmet due to an error."""
    return O1Assessment(
        criteria=[
            CriterionEvidence(
                name=c["name"],
                description=c["description"],
                met=False,
                evidence=None,
                reasoning=error_reason,
            )
            for c in O1A_CRITERIA
        ]
    )
