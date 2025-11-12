**Assignment: AI-Powered Recruitment Agent**

**Objective**

Build a recruitment system that accepts one or more resumes (limit 10) at a time and provides an assessment of the candidate (score 1 - 10) relative to a pre-defined Job Description. The assessment must leverage AI models (not limited to LLMs) and may include evaluations of the resume content, GitHub repos, LinkedIn, and such.

The output is an overall fit score and a two-page assessment of the candidate, along with a recommendation on "Interview" (pass to interview stage) or "Decline" (do not pass to interview stage).

The solution must be developed as a webapp. Django + Python backend and react + typescript frontend.

The system must be able to handle multiple candidates concurrently.

**Required Features**

**→ Core Processing**
*   Accept resume uploads (PDF/text) and extract candidate information
*   Detect and analyze Github profiles when available
*   Generate structured AI evaluations with scores and recommendations
*   Store all artifacts and maintain processing audit trails

**→ Stakeholder Integration**
*   Send evaluation summaries to hiring teams via Telegram

**→ System Requirements**
*   Process multiple candidates simultaneously without cross-contamination
*   Handle failures gracefully (API timeouts, missing data, etc.)
*   Maintain traceability of all processing steps and decisions

**Technical Constraints**

*   **Concurrency:** System receives 10+ candidate submissions within minutes
*   **Data Integrity:** Candidate A's information never appears in Candidate B's evaluation
*   **Async Feedback:** Stakeholders respond hours or days after initial notification via Telegram
*   **Failure Recovery:** Individual candidate processing failures don't crash the system
*   **GitHub Integration:** Handle rate limits and unavailable profiles.

**Critical Scenarios to Handle**

1.  Multiple candidates submitted simultaneously - ensure no data leakage
2.  Stakeholder replies to the wrong candidate - prevent misattribution
3.  Github API failures during processing - graceful degradation
4.  Conflicting feedback from different stakeholders - manage resolution
5.  Late feedback on already-processed candidates - handle state updates

**What We're Looking For**

*   Clean concurrent processing without data contamination
*   Robust error handling and recovery mechanisms
*   Clear audit trails and processing transparency
*   Thoughtful approach to stakeholder coordination
*   Production-ready code organization and testing

**Deliverables**

*   Working full-stack application
*   Clear setup and deployment instructions
*   Architecture explanation and design trade-offs
*   Demonstration of concurrent processing safety
*   Test coverage for critical failure scenarios

**Other items**
*   Add "ruff" linter to the project along with a github action to check "ruff"
*   Add "pyrefly" for type checking from https://pyrefly.org/ into the project
*   Use "shadcn" components for building the UI exclusively.
*   This project should be deployable on vercel.
*   Add unit tests and execute then using "pytest". Create a github action to execute them.
*   For frontend linting remove eslint and use "biome" instead.
*   Use Django-allauth for authentication, do password based authentication for now, but add an instructions file on how to add other logins (login with google, microsoft, slack, github, etc)