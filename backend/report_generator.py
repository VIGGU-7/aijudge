"""
PDF Report Generator for AI Judge Platform.
Uses reportlab to generate participant and hackathon reports.
"""
import io
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def _get_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", fontSize=22, leading=28, fontName="Helvetica-Bold", textColor=colors.HexColor("#111111"), alignment=TA_CENTER, spaceAfter=6))
    styles.add(ParagraphStyle(name="ReportSubtitle", fontSize=11, leading=14, fontName="Helvetica", textColor=colors.HexColor("#888888"), alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle(name="SectionHeader", fontSize=14, leading=18, fontName="Helvetica-Bold", textColor=colors.HexColor("#111111"), spaceBefore=18, spaceAfter=8))
    styles.add(ParagraphStyle(name="BodyText2", fontSize=10, leading=14, fontName="Helvetica", textColor=colors.HexColor("#333333"), spaceAfter=4))
    styles.add(ParagraphStyle(name="SmallGrey", fontSize=9, leading=12, fontName="Helvetica", textColor=colors.HexColor("#999999"), spaceAfter=2))
    styles.add(ParagraphStyle(name="GradeStyle", fontSize=48, leading=56, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4))
    return styles


def _grade_color(grade):
    return {"A": colors.HexColor("#22c55e"), "B": colors.HexColor("#3b82f6"), "C": colors.HexColor("#f59e0b"), "F": colors.HexColor("#ef4444")}.get(grade, colors.HexColor("#888888"))


def _score_to_grade(score):
    if score >= 80: return "A"
    if score >= 60: return "B"
    if score >= 40: return "C"
    return "F"


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#bbbbbb"))
    canvas.drawString(40, 20, f"AI Judge Platform Report — Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas.drawRightString(A4[0] - 40, 20, f"Page {doc.page}")
    canvas.restoreState()


def _make_table_style(header_bg="#111111", header_fg="#ffffff"):
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_bg)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(header_fg)),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("TOPPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e0e0e0")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
    ])


def generate_participant_report(user, team, viva_sessions, project_info, plagiarism_report) -> bytes:
    """Generate a PDF report for a single participant."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=40, bottomMargin=40, leftMargin=40, rightMargin=40)
    styles = _get_styles()
    story = []

    # Title
    story.append(Paragraph("AI Judge — Participant Report", styles["ReportTitle"]))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles["ReportSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0"), spaceAfter=16))

    # Participant Info
    story.append(Paragraph("Participant Information", styles["SectionHeader"]))
    info_data = [
        ["Name", user.get("name", "N/A")],
        ["Email", user.get("email", "N/A")],
        ["Team", team.get("name", "N/A") if team else "No team"],
        ["Role", user.get("role", "participant").capitalize()],
    ]
    if project_info:
        if project_info.get("github_url"):
            info_data.append(["GitHub Repo", project_info["github_url"]])
        if project_info.get("project_description"):
            info_data.append(["Description", project_info["project_description"][:120]])
    t = Table(info_data, colWidths=[120, 380])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#f0f0f0")),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))

    # Tech Stack & Features
    if project_info:
        if project_info.get("tech_stack"):
            story.append(Paragraph("Tech Stack", styles["SectionHeader"]))
            story.append(Paragraph(", ".join(project_info["tech_stack"]), styles["BodyText2"]))
        if project_info.get("features"):
            story.append(Paragraph("Features Built", styles["SectionHeader"]))
            for feat in project_info["features"]:
                story.append(Paragraph(f"• {feat}", styles["BodyText2"]))
        story.append(Spacer(1, 6))

    # Viva Performance
    story.append(Paragraph("Viva Performance", styles["SectionHeader"]))
    all_questions = []
    for sess in (viva_sessions or []):
        for q in sess.get("questions", []):
            all_questions.append(q)

    total_asked = len(all_questions)
    total_answered = sum(1 for q in all_questions if q.get("answer"))
    scores = [q["evaluation"]["score"] for q in all_questions if q.get("evaluation", {}).get("score")]
    avg_viva = round(sum(scores) / len(scores), 1) if scores else 0

    story.append(Paragraph(f"Total Questions: {total_asked}  |  Answered: {total_answered}  |  Average Score: {avg_viva}/100", styles["BodyText2"]))
    story.append(Spacer(1, 8))

    # Per-question breakdown table
    if all_questions:
        q_header = ["#", "Question", "Answer", "Score", "Feedback"]
        q_rows = [q_header]
        for i, q in enumerate(all_questions, 1):
            question_text = (q.get("question", "") or "")[:80]
            answer_text = (q.get("answer", "") or "—")[:60]
            ev = q.get("evaluation", {})
            score_val = str(ev.get("score", "—"))
            feedback_text = (ev.get("feedback", "") or "—")[:80]
            q_rows.append([str(i), question_text, answer_text, score_val, feedback_text])

        qt = Table(q_rows, colWidths=[25, 150, 110, 40, 180])
        qt.setStyle(_make_table_style())
        story.append(qt)
    else:
        story.append(Paragraph("No viva sessions completed.", styles["SmallGrey"]))
    story.append(Spacer(1, 10))

    # Plagiarism Score
    story.append(Paragraph("Plagiarism Assessment", styles["SectionHeader"]))
    if plagiarism_report:
        plag_score = plagiarism_report.get("overall_score", 0)
        risk = plagiarism_report.get("risk_level", "unknown")
        story.append(Paragraph(f"Overall Plagiarism Score: {plag_score}%  |  Risk Level: {risk.upper()}", styles["BodyText2"]))
        if plagiarism_report.get("summary"):
            story.append(Paragraph(plagiarism_report["summary"], styles["SmallGrey"]))
    else:
        story.append(Paragraph("No plagiarism check has been run for this team.", styles["SmallGrey"]))
    story.append(Spacer(1, 16))

    # Overall Grade
    plag_score = plagiarism_report.get("overall_score", 0) if plagiarism_report else 0
    combined = max(0, avg_viva - (plag_score * 0.3))  # Penalty for plagiarism
    grade = _score_to_grade(combined)

    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0"), spaceBefore=6, spaceAfter=12))
    story.append(Paragraph("Overall Evaluation Grade", styles["SectionHeader"]))
    grade_style = ParagraphStyle("DynGrade", parent=styles["GradeStyle"], textColor=_grade_color(grade))
    story.append(Paragraph(grade, grade_style))
    grade_labels = {"A": "Excellent", "B": "Good", "C": "Needs Improvement", "F": "Unsatisfactory"}
    story.append(Paragraph(grade_labels.get(grade, ""), ParagraphStyle("GradeLabel", parent=styles["ReportSubtitle"], fontSize=13)))
    story.append(Paragraph(f"Composite Score: {round(combined, 1)}/100", styles["SmallGrey"]))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()


def generate_hackathon_report(hackathon, teams_data, leaderboard, plagiarism_reports, viva_data) -> bytes:
    """
    Generate a full hackathon report PDF for organizers.
    teams_data: list of {team, members, project_info}
    leaderboard: list of {rank, team_id, team_name, avg_score, count}
    plagiarism_reports: dict of {team_id: report}
    viva_data: dict of {team_id: [sessions]}
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=40, bottomMargin=40, leftMargin=40, rightMargin=40)
    styles = _get_styles()
    story = []

    # Title
    h_name = hackathon.get("name", "Hackathon") if hackathon else "Hackathon"
    story.append(Paragraph(f"AI Judge — {h_name} Report", styles["ReportTitle"]))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", styles["ReportSubtitle"]))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e0e0e0"), spaceAfter=16))

    # Winner highlight
    if leaderboard and len(leaderboard) > 0:
        winner = leaderboard[0]
        story.append(Paragraph("🏆 Winner", styles["SectionHeader"]))
        story.append(Paragraph(f"{winner['team_name']} — Score: {winner['avg_score']}/100", ParagraphStyle("WinnerText", parent=styles["BodyText2"], fontSize=14, fontName="Helvetica-Bold", textColor=colors.HexColor("#22c55e"))))
        story.append(Spacer(1, 10))

    # Summary Analytics
    story.append(Paragraph("Summary Analytics", styles["SectionHeader"]))
    total_teams = len(teams_data)
    all_scores = [e["avg_score"] for e in leaderboard] if leaderboard else []
    avg_all = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0
    highest = max(all_scores) if all_scores else 0
    lowest = min(all_scores) if all_scores else 0
    plag_scores = [r.get("overall_score", 0) for r in plagiarism_reports.values()]
    avg_plag = round(sum(plag_scores) / len(plag_scores), 1) if plag_scores else 0
    disqualified = sum(1 for s in plag_scores if s > 50)

    analytics_data = [
        ["Total Teams", str(total_teams)],
        ["Average Score", f"{avg_all}/100"],
        ["Highest Score", f"{highest}/100"],
        ["Lowest Score", f"{lowest}/100"],
        ["Teams Checked for Plagiarism", str(len(plag_scores))],
        ["Average Plagiarism Rate", f"{avg_plag}%"],
        ["Flagged Teams (>50%)", str(disqualified)],
    ]
    at = Table(analytics_data, colWidths=[220, 280])
    at.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#555555")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#f0f0f0")),
    ]))
    story.append(at)
    story.append(Spacer(1, 14))

    # Leaderboard Table
    story.append(Paragraph("Leaderboard", styles["SectionHeader"]))
    if leaderboard:
        lb_header = ["Rank", "Team", "Avg Score", "Evaluations", "Plagiarism", "Status"]
        lb_rows = [lb_header]
        for e in leaderboard:
            tid = e.get("team_id", "")
            plag = plagiarism_reports.get(tid, {})
            plag_score = plag.get("overall_score", "—")
            plag_str = f"{plag_score}%" if isinstance(plag_score, (int, float)) else plag_score
            flagged = isinstance(plag_score, (int, float)) and plag_score > 50
            status = "⛔ FLAGGED" if flagged else "✅ Clear"
            lb_rows.append([str(e["rank"]), e["team_name"], f"{e['avg_score']}", str(e.get("count", 0)), plag_str, status])

        lt = Table(lb_rows, colWidths=[40, 140, 70, 80, 80, 80])
        lt.setStyle(_make_table_style())
        # Highlight flagged rows
        for i, e in enumerate(leaderboard, 1):
            tid = e.get("team_id", "")
            plag = plagiarism_reports.get(tid, {})
            if isinstance(plag.get("overall_score"), (int, float)) and plag["overall_score"] > 50:
                lt.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), colors.HexColor("#fef2f2"))]))
        story.append(lt)
    else:
        story.append(Paragraph("No evaluations submitted yet.", styles["SmallGrey"]))
    story.append(Spacer(1, 10))

    # Per-team breakdown
    story.append(PageBreak())
    story.append(Paragraph("Per-Team Breakdown", styles["SectionHeader"]))
    story.append(Spacer(1, 6))

    for td in teams_data:
        team = td["team"]
        members = td.get("members", [])
        proj = td.get("project_info")
        tid = team.get("id", str(team.get("_id", "")))

        story.append(Paragraph(f"Team: {team.get('name', 'Unknown')}", ParagraphStyle("TeamName", parent=styles["SectionHeader"], fontSize=12, spaceBefore=10)))

        team_info = []
        member_names = ", ".join([m.get("name", "?") for m in members]) if members else "N/A"
        team_info.append(["Members", member_names])
        team_info.append(["GitHub", team.get("github_repo", "N/A")])

        # Viva score for this team
        sessions = viva_data.get(tid, [])
        v_scores = []
        for s in sessions:
            for q in s.get("questions", []):
                if q.get("evaluation", {}).get("score"):
                    v_scores.append(q["evaluation"]["score"])
        avg_v = round(sum(v_scores) / len(v_scores), 1) if v_scores else 0
        team_info.append(["Viva Avg Score", f"{avg_v}/100"])

        # Plagiarism
        pr = plagiarism_reports.get(tid, {})
        ps = pr.get("overall_score", "Not checked")
        ps_str = f"{ps}%" if isinstance(ps, (int, float)) else ps
        team_info.append(["Plagiarism Score", ps_str])

        # Eval score from leaderboard
        lb_entry = next((e for e in (leaderboard or []) if e.get("team_id") == tid), None)
        eval_score = lb_entry["avg_score"] if lb_entry else "N/A"
        team_info.append(["Evaluation Score", f"{eval_score}/100" if isinstance(eval_score, (int, float)) else eval_score])

        tt = Table(team_info, colWidths=[130, 370])
        tt.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#666666")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#f0f0f0")),
        ]))
        story.append(tt)
        story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e8e8e8"), spaceBefore=8, spaceAfter=8))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return buf.getvalue()
