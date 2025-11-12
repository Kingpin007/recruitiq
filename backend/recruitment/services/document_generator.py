import io
from datetime import datetime

from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class DocumentGenerator:
    """Service for generating assessment documents."""

    def generate_assessment_pdf(self, evaluation):
        """
        Generate a 2-page PDF assessment document for a candidate.

        Args:
            evaluation: Evaluation model instance

        Returns:
            ContentFile: Django file object
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch, bottomMargin=0.5 * inch)

        # Build the document content
        story = []
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle", parent=styles["Heading1"], fontSize=24, textColor=colors.HexColor("#1a1a1a"), spaceAfter=6
        )

        heading_style = ParagraphStyle(
            "CustomHeading", parent=styles["Heading2"], fontSize=14, textColor=colors.HexColor("#2563eb"), spaceBefore=12, spaceAfter=6
        )

        # Get data
        candidate = evaluation.candidate
        job_desc = candidate.job_description
        detailed = evaluation.detailed_analysis

        # Title
        story.append(Paragraph("CANDIDATE ASSESSMENT REPORT", title_style))
        story.append(Spacer(1, 0.1 * inch))

        # Header information
        header_data = [
            ["Candidate:", candidate.name, "Score:", f"{evaluation.overall_score}/10"],
            ["Email:", candidate.email, "Recommendation:", evaluation.recommendation.upper()],
            ["Position:", job_desc.title, "Date:", datetime.now().strftime("%Y-%m-%d")],
        ]

        header_table = Table(header_data, colWidths=[1 * inch, 2.5 * inch, 1 * inch, 1.5 * inch])
        header_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f3f4f6")),
                    ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#f3f4f6")),
                ]
            )
        )
        story.append(header_table)
        story.append(Spacer(1, 0.2 * inch))

        # Summary
        if "summary" in detailed:
            story.append(Paragraph("Executive Summary", heading_style))
            story.append(Paragraph(detailed["summary"], styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

        # Key Highlights
        if "key_highlights" in detailed and detailed["key_highlights"]:
            story.append(Paragraph("Key Strengths", heading_style))
            for highlight in detailed["key_highlights"]:
                story.append(Paragraph(f"• {highlight}", styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

        # Concerns
        if "concerns" in detailed and detailed["concerns"]:
            story.append(Paragraph("Areas of Concern", heading_style))
            for concern in detailed["concerns"]:
                story.append(Paragraph(f"• {concern}", styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

        # Skill Assessment
        if "skill_matches" in detailed:
            story.append(Paragraph("Technical Skills Assessment", heading_style))

            skill_data = [["Skill", "Score", "Match", "Notes"]]
            for skill, data in list(detailed["skill_matches"].items())[:10]:  # Limit to 10
                match_status = "✓" if data.get("matched") else "✗"
                score = f"{data.get('score', 0)}/10"
                evidence = data.get("evidence", "")[:50]  # Truncate
                skill_data.append([skill, score, match_status, evidence])

            skill_table = Table(
                skill_data, colWidths=[1.5 * inch, 0.7 * inch, 0.7 * inch, 3.1 * inch]
            )
            skill_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (1, 0), (2, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f9fafb")]),
                    ]
                )
            )
            story.append(skill_table)
            story.append(Spacer(1, 0.15 * inch))

        # Page break
        story.append(PageBreak())

        # Page 2: Detailed Analysis
        story.append(Paragraph("Detailed Analysis", title_style))
        story.append(Spacer(1, 0.1 * inch))

        # Experience Assessment
        if "experience_assessment" in detailed:
            exp = detailed["experience_assessment"]
            story.append(Paragraph("Experience Evaluation", heading_style))
            story.append(
                Paragraph(
                    f"Estimated Years: {exp.get('years_of_experience', 'N/A')}",
                    styles["Normal"],
                )
            )
            story.append(
                Paragraph(
                    f"Meets Requirement: {'Yes' if exp.get('meets_requirement') else 'No'}",
                    styles["Normal"],
                )
            )
            story.append(Paragraph(exp.get("notes", ""), styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

        # Technical Depth
        if "technical_depth" in detailed:
            tech = detailed["technical_depth"]
            story.append(Paragraph("Technical Depth", heading_style))
            story.append(Paragraph(f"Score: {tech.get('score', 0)}/10", styles["Normal"]))
            story.append(Paragraph(tech.get("notes", ""), styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

        # GitHub Contribution
        if "github_contribution" in detailed:
            gh = detailed["github_contribution"]
            story.append(Paragraph("GitHub Activity", heading_style))
            story.append(Paragraph(f"Score: {gh.get('score', 0)}/10", styles["Normal"]))
            story.append(Paragraph(gh.get("notes", ""), styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

        # Recommendation
        story.append(Paragraph("Final Recommendation", heading_style))
        recommendation_color = (
            colors.HexColor("#10b981")
            if evaluation.recommendation == "interview"
            else colors.HexColor("#ef4444")
        )
        rec_style = ParagraphStyle(
            "Recommendation", parent=styles["Normal"], fontSize=12, textColor=recommendation_color, fontName="Helvetica-Bold"
        )
        story.append(Paragraph(f"RECOMMENDATION: {evaluation.recommendation.upper()}", rec_style))
        story.append(Spacer(1, 0.1 * inch))

        if "recommendation_reasoning" in detailed:
            story.append(Paragraph(detailed["recommendation_reasoning"], styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

        # Interview Questions
        if "interview_questions" in detailed and detailed["interview_questions"]:
            story.append(Paragraph("Suggested Interview Questions", heading_style))
            for i, question in enumerate(detailed["interview_questions"][:5], 1):
                story.append(Paragraph(f"{i}. {question}", styles["Normal"]))
            story.append(Spacer(1, 0.15 * inch))

        # Footer
        story.append(Spacer(1, 0.2 * inch))
        footer_style = ParagraphStyle(
            "Footer", parent=styles["Normal"], fontSize=8, textColor=colors.grey
        )
        story.append(
            Paragraph(
                f"Generated by RecruitIQ on {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
                f"Model: {evaluation.ai_model_used}",
                footer_style,
            )
        )

        # Build PDF
        doc.build(story)

        # Get PDF content
        pdf_content = buffer.getvalue()
        buffer.close()

        # Create Django file
        filename = f"assessment_{candidate.name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        return ContentFile(pdf_content, name=filename)

