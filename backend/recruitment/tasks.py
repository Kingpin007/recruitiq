import time
from datetime import datetime

from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .models import Candidate, Evaluation, ProcessingLog, Resume
from .services.ai_evaluator import AIEvaluator
from .services.github_analyzer import GitHubAnalyzer
from .services.pdf_parser import PDFParser
from .services.telegram_notifier import TelegramNotifier


def log_processing_stage(candidate_id, stage, status, message="", error_message="", metadata=None):
    """Helper function to log processing stages."""
    try:
        ProcessingLog.objects.create(
            candidate_id=candidate_id,
            stage=stage,
            status=status,
            message=message,
            error_message=error_message,
            metadata=metadata or {},
        )
    except Exception as e:
        # Don't fail the task if logging fails
        print(f"Failed to log processing stage: {e}")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_candidate_task(self, candidate_id):
    """
    Main task to orchestrate the complete candidate processing pipeline.
    """
    start_time = time.time()

    try:
        candidate = Candidate.objects.select_for_update().get(id=candidate_id)
    except Candidate.DoesNotExist:
        return {"error": f"Candidate {candidate_id} not found"}

    log_processing_stage(
        candidate_id,
        "pipeline_start",
        "started",
        message="Starting candidate processing pipeline",
    )

    try:
        # Update candidate status
        with transaction.atomic():
            candidate.status = "processing"
            candidate.save(update_fields=["status"])

        # Step 1: Extract resume text
        resume_text = extract_resume_text(candidate_id)
        if not resume_text:
            raise Exception("Failed to extract resume text")

        # Step 2: Detect and fetch GitHub profile
        github_data = None
        try:
            github_username = detect_github_profile(candidate_id, resume_text)
            if github_username:
                github_data = fetch_github_data(candidate_id, github_username)
        except Exception as e:
            log_processing_stage(
                candidate_id,
                "github_analysis",
                "failed",
                error_message=str(e),
                message="GitHub analysis failed, continuing without it",
            )

        # Step 3: Analyze candidate with AI
        evaluation_id = analyze_candidate(candidate_id, resume_text, github_data)
        if not evaluation_id:
            raise Exception("Failed to generate candidate evaluation")

        # Step 4: Generate assessment document
        try:
            generate_assessment_document(evaluation_id)
        except Exception as e:
            log_processing_stage(
                candidate_id,
                "document_generation",
                "failed",
                error_message=str(e),
                message="Document generation failed, continuing without it",
            )

        # Step 5: Send Telegram notification
        try:
            send_telegram_notification(evaluation_id)
        except Exception as e:
            log_processing_stage(
                candidate_id,
                "telegram_notification",
                "failed",
                error_message=str(e),
                message="Telegram notification failed",
            )

        # Mark candidate as completed
        with transaction.atomic():
            candidate.status = "completed"
            candidate.save(update_fields=["status"])

        processing_time = time.time() - start_time
        log_processing_stage(
            candidate_id,
            "pipeline_complete",
            "completed",
            message="Candidate processing completed successfully",
            metadata={"processing_time_seconds": processing_time},
        )

        return {
            "candidate_id": candidate_id,
            "status": "completed",
            "evaluation_id": evaluation_id,
            "processing_time": processing_time,
        }

    except Exception as e:
        # Mark candidate as failed
        error_message = str(e)
        with transaction.atomic():
            candidate.status = "failed"
            candidate.error_message = error_message
            candidate.save(update_fields=["status", "error_message"])

        log_processing_stage(
            candidate_id,
            "pipeline_error",
            "failed",
            error_message=error_message,
            message="Candidate processing failed",
        )

        # Retry on certain errors
        if "rate limit" in error_message.lower() or "timeout" in error_message.lower():
            raise self.retry(exc=e)

        return {
            "candidate_id": candidate_id,
            "status": "failed",
            "error": error_message,
        }


def extract_resume_text(candidate_id):
    """Extract text from uploaded resume file."""
    start_time = time.time()

    try:
        log_processing_stage(
            candidate_id, "resume_parsing", "in_progress", message="Parsing resume file"
        )

        resume = Resume.objects.get(candidate_id=candidate_id)
        parser = PDFParser()

        if resume.file_type.lower() == "pdf":
            text = parser.extract_from_pdf(resume.file)
        elif resume.file_type.lower() in ["txt", "text"]:
            text = parser.extract_from_text(resume.file)
        elif resume.file_type.lower() in ["doc", "docx"]:
            text = parser.extract_from_docx(resume.file)
        else:
            raise ValueError(f"Unsupported file type: {resume.file_type}")

        # Save parsed text
        resume.parsed_text = text
        resume.save(update_fields=["parsed_text"])

        duration = time.time() - start_time
        log_processing_stage(
            candidate_id,
            "resume_parsing",
            "completed",
            message=f"Successfully parsed resume ({len(text)} characters)",
            metadata={"text_length": len(text), "duration_seconds": duration},
        )

        return text

    except Exception as e:
        error_message = str(e)
        try:
            resume = Resume.objects.get(candidate_id=candidate_id)
            resume.parsing_error = error_message
            resume.save(update_fields=["parsing_error"])
        except Exception:
            pass

        log_processing_stage(
            candidate_id, "resume_parsing", "failed", error_message=error_message
        )
        raise


def detect_github_profile(candidate_id, resume_text):
    """Detect GitHub username from resume text."""
    try:
        log_processing_stage(
            candidate_id,
            "github_detection",
            "in_progress",
            message="Detecting GitHub profile",
        )

        analyzer = GitHubAnalyzer()
        username = analyzer.extract_github_username(resume_text)

        if username:
            log_processing_stage(
                candidate_id,
                "github_detection",
                "completed",
                message=f"Found GitHub username: {username}",
                metadata={"username": username},
            )
        else:
            log_processing_stage(
                candidate_id,
                "github_detection",
                "skipped",
                message="No GitHub profile found in resume",
            )

        return username

    except Exception as e:
        log_processing_stage(
            candidate_id, "github_detection", "failed", error_message=str(e)
        )
        return None


def fetch_github_data(candidate_id, username):
    """Fetch and analyze GitHub profile data."""
    start_time = time.time()

    try:
        log_processing_stage(
            candidate_id,
            "github_fetch",
            "in_progress",
            message=f"Fetching GitHub data for {username}",
        )

        from .models import GitHubProfile

        analyzer = GitHubAnalyzer()
        profile_data = analyzer.fetch_user_profile(username)
        repos_data = analyzer.fetch_repositories(username)
        analysis = analyzer.analyze_profile(repos_data)

        # Save GitHub profile
        github_profile, created = GitHubProfile.objects.update_or_create(
            candidate_id=candidate_id,
            defaults={
                "username": username,
                "profile_url": f"https://github.com/{username}",
                "repos_data": repos_data,
                "analysis": analysis,
            },
        )

        duration = time.time() - start_time
        log_processing_stage(
            candidate_id,
            "github_fetch",
            "completed",
            message=f"Successfully fetched GitHub data for {username}",
            metadata={"repos_count": len(repos_data), "duration_seconds": duration},
        )

        return {"profile": profile_data, "repos": repos_data, "analysis": analysis}

    except Exception as e:
        error_message = str(e)

        try:
            from .models import GitHubProfile

            GitHubProfile.objects.update_or_create(
                candidate_id=candidate_id,
                defaults={
                    "username": username,
                    "profile_url": f"https://github.com/{username}",
                    "fetch_error": error_message,
                },
            )
        except Exception:
            pass

        log_processing_stage(
            candidate_id, "github_fetch", "failed", error_message=error_message
        )
        raise


def analyze_candidate(candidate_id, resume_text, github_data=None):
    """Use AI to analyze candidate and generate evaluation."""
    start_time = time.time()

    try:
        log_processing_stage(
            candidate_id, "ai_evaluation", "in_progress", message="Analyzing candidate with AI"
        )

        candidate = Candidate.objects.select_related("job_description").get(id=candidate_id)
        evaluator = AIEvaluator()

        result = evaluator.evaluate_candidate(
            job_description=candidate.job_description,
            resume_text=resume_text,
            github_data=github_data,
        )

        # Create evaluation record
        processing_time = time.time() - start_time
        evaluation = Evaluation.objects.create(
            candidate=candidate,
            overall_score=result["overall_score"],
            detailed_analysis=result["detailed_analysis"],
            recommendation=result["recommendation"],
            processing_logs=result.get("processing_logs", []),
            ai_model_used=result.get("model", "gpt-4"),
            processing_time_seconds=processing_time,
        )

        log_processing_stage(
            candidate_id,
            "ai_evaluation",
            "completed",
            message=f"AI evaluation completed (Score: {result['overall_score']}/10)",
            metadata={
                "evaluation_id": evaluation.id,
                "score": result["overall_score"],
                "recommendation": result["recommendation"],
                "duration_seconds": processing_time,
            },
        )

        return evaluation.id

    except Exception as e:
        log_processing_stage(
            candidate_id, "ai_evaluation", "failed", error_message=str(e)
        )
        raise


def generate_assessment_document(evaluation_id):
    """Generate a PDF assessment document."""
    start_time = time.time()

    try:
        evaluation = Evaluation.objects.select_related("candidate").get(id=evaluation_id)

        log_processing_stage(
            evaluation.candidate.id,
            "document_generation",
            "in_progress",
            message="Generating assessment document",
        )

        from .services.document_generator import DocumentGenerator

        generator = DocumentGenerator()
        pdf_file = generator.generate_assessment_pdf(evaluation)

        # Save document
        evaluation.assessment_document = pdf_file
        evaluation.save(update_fields=["assessment_document"])

        duration = time.time() - start_time
        log_processing_stage(
            evaluation.candidate.id,
            "document_generation",
            "completed",
            message="Assessment document generated successfully",
            metadata={"duration_seconds": duration},
        )

    except Exception as e:
        log_processing_stage(
            evaluation.candidate.id, "document_generation", "failed", error_message=str(e)
        )
        raise


def send_telegram_notification(evaluation_id):
    """Send evaluation summary to hiring team via Telegram."""
    try:
        evaluation = Evaluation.objects.select_related("candidate").get(id=evaluation_id)

        log_processing_stage(
            evaluation.candidate.id,
            "telegram_notification",
            "in_progress",
            message="Sending Telegram notification",
        )

        notifier = TelegramNotifier()
        message_id = notifier.send_evaluation_summary(evaluation)

        log_processing_stage(
            evaluation.candidate.id,
            "telegram_notification",
            "completed",
            message="Telegram notification sent successfully",
            metadata={"message_id": message_id},
        )

        return message_id

    except Exception as e:
        log_processing_stage(
            evaluation.candidate.id, "telegram_notification", "failed", error_message=str(e)
        )
        raise

