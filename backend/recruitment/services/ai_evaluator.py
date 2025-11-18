import json
import time

import openai
from decouple import config
from django.conf import settings


class AIEvaluator:
    """Service for evaluating candidates using OpenAI GPT-4."""

    def __init__(self):
        self.api_key = config("OPENAI_API_KEY", default="")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        openai.api_key = self.api_key
        self.client = openai.OpenAI(api_key=self.api_key)
        self.model = config("OPENAI_MODEL", default="gpt-5-nano-2025-08-07")
        self.max_retries = 3
        self.retry_delay = 2

    def evaluate_candidate(self, job_description, resume_text, github_data=None):
        """
        Evaluate a candidate against a job description.

        Args:
            job_description: JobDescription model instance
            resume_text: Extracted resume text
            github_data: Optional GitHub profile data

        Returns:
            dict with evaluation results
        """
        prompt = self._build_evaluation_prompt(job_description, resume_text, github_data)

        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert technical recruiter and hiring manager with deep knowledge of software development, programming languages, and industry best practices. Your task is to evaluate candidates objectively and provide detailed, actionable insights.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                )

                result = json.loads(response.choices[0].message.content)
                return self._process_ai_response(result)

            except openai.RateLimitError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                    continue
                raise Exception(f"OpenAI rate limit exceeded: {e}")

            except openai.APITimeoutError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                raise Exception(f"OpenAI API timeout: {e}")

            except json.JSONDecodeError as e:
                raise Exception(f"Failed to parse AI response as JSON: {e}")

            except Exception as e:
                raise Exception(f"OpenAI API error: {e}")

        raise Exception("Max retries exceeded for OpenAI API")

    def _build_evaluation_prompt(self, job_description, resume_text, github_data):
        """Build the evaluation prompt for the AI."""
        prompt = f"""
Evaluate the following candidate for the job position described below.

JOB DESCRIPTION:
Title: {job_description.title}
Description: {job_description.description}
Required Skills: {', '.join(job_description.required_skills)}
Nice-to-Have Skills: {', '.join(job_description.nice_to_have_skills)}
Required Experience: {job_description.experience_years} years

CANDIDATE RESUME:
{resume_text[:5000]}  # Limit resume to prevent token overflow
"""

        if github_data:
            github_analysis = github_data.get("analysis", {})
            prompt += f"""

GITHUB PROFILE ANALYSIS:
- Total Repositories: {github_analysis.get('total_repos', 0)}
- Active Repositories: {github_analysis.get('active_repos', 0)}
- Primary Languages: {', '.join(github_analysis.get('languages', [])[:5])}
- Total Stars Received: {github_analysis.get('total_stars', 0)}
- Total Contributions: {github_analysis.get('total_contributions', 0)}
"""

        prompt += """

Please provide a comprehensive evaluation in JSON format with the following structure:
{
  "overall_score": <integer 1-10>,
  "recommendation": "<interview or decline>",
  "detailed_analysis": {
    "strengths": ["<strength 1>", "<strength 2>", ...],
    "weaknesses": ["<weakness 1>", "<weakness 2>", ...],
    "skill_matches": {
      "<skill_name>": {
        "score": <integer 1-10>,
        "evidence": "<brief explanation>",
        "matched": <boolean>
      },
      ...
    },
    "experience_assessment": {
      "years_of_experience": <estimated years>,
      "meets_requirement": <boolean>,
      "notes": "<explanation>"
    },
    "technical_depth": {
      "score": <integer 1-10>,
      "notes": "<explanation>"
    },
    "culture_fit": {
      "score": <integer 1-10>,
      "notes": "<explanation>"
    },
    "github_contribution": {
      "score": <integer 1-10>,
      "notes": "<explanation>"
    },
    "key_highlights": ["<highlight 1>", "<highlight 2>", ...],
    "concerns": ["<concern 1>", "<concern 2>", ...],
    "interview_questions": ["<question 1>", "<question 2>", ...]
  },
  "summary": "<2-3 sentence summary of the candidate>",
  "recommendation_reasoning": "<detailed explanation of why interview or decline>"
}

EVALUATION CRITERIA:
1. Score each required skill based on evidence from resume and GitHub
2. Assess overall technical competency and depth
3. Evaluate years of experience against job requirements
4. Consider GitHub activity as a positive indicator
5. Provide specific, actionable feedback
6. Recommend "interview" only if overall_score >= 6 and most required skills match
7. Be objective and fair in your assessment
"""

        return prompt

    def _process_ai_response(self, result):
        """Process and validate the AI response."""
        # Validate required fields
        required_fields = ["overall_score", "recommendation", "detailed_analysis"]
        for field in required_fields:
            if field not in result:
                raise ValueError(f"Missing required field in AI response: {field}")

        # Validate score range
        score = result["overall_score"]
        if not isinstance(score, int) or score < 1 or score > 10:
            raise ValueError(f"Invalid overall_score: {score}. Must be integer 1-10.")

        # Validate recommendation
        recommendation = result["recommendation"].lower()
        if recommendation not in ["interview", "decline"]:
            raise ValueError(f"Invalid recommendation: {recommendation}")

        # Ensure consistent recommendation based on score
        if score >= 6 and recommendation != "interview":
            result["recommendation"] = "interview"
        elif score < 6 and recommendation != "decline":
            result["recommendation"] = "decline"

        return {
            "overall_score": score,
            "recommendation": result["recommendation"],
            "detailed_analysis": result["detailed_analysis"],
            "processing_logs": [
                {
                    "timestamp": time.time(),
                    "stage": "ai_evaluation",
                    "model": self.model,
                    "status": "completed",
                }
            ],
            "model": self.model,
        }

