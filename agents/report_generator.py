from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import io


def generate_audit_pdf(report_data: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
            leftMargin=18 * mm,
            rightMargin=18 * mm
        )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Title'], fontSize=18, spaceAfter=4
    )
    subtitle_style = ParagraphStyle(
        'SubtitleStyle', parent=styles['Normal'], fontSize=10,
        textColor=colors.grey, spaceAfter=16
    )
    heading_style = ParagraphStyle(
        'HeadingStyle', parent=styles['Heading2'], fontSize=13,
        spaceBefore=16, spaceAfter=8, textColor=colors.HexColor('#1a1a1a')
    )
    normal_style = ParagraphStyle(
        'NormalSmall', parent=styles['Normal'], fontSize=9, leading=13
    )
    label_style = ParagraphStyle(
        'LabelStyle', parent=styles['Normal'], fontSize=9,
        textColor=colors.HexColor('#666666')
    )

    elements = []

    # Header
    elements.append(Paragraph("ClearBid — Procurement Audit Report", title_style))
    elements.append(Paragraph(
        f"Tender ID: {report_data['tender_id']} | "
        f"Document: {report_data['tender_filename']} | "
        f"Generated: {datetime.fromisoformat(report_data['report_generated_at']).strftime('%d %b %Y, %H:%M UTC')}",
        subtitle_style
    ))

    # Criteria summary
    elements.append(Paragraph("Eligibility Criteria", heading_style))
    criteria_data = [["ID", "Name", "Type", "Mandatory", "Threshold"]]
    for c in report_data["criteria"]:
        criteria_data.append([
            c["criterion_id"], c["name"], c["type"],
            "Yes" if c["mandatory"] else "No",
            str(c.get("threshold", "-"))
        ])

    criteria_table = Table(criteria_data, colWidths=[35, 150, 70, 60, 70])
    criteria_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(criteria_table)

    approval_status = "Confirmed by officer" if report_data["criteria_approved"] else "Not yet confirmed"
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(f"Criteria approval status: {approval_status}", label_style))

    # Per-bidder sections
    for bidder in report_data["bidders"]:
        elements.append(PageBreak())
        elements.append(Paragraph(f"Bidder: {bidder['filename']}", heading_style))
        elements.append(Paragraph(
            f"Submitted: {datetime.fromisoformat(bidder['submitted_at']).strftime('%d %b %Y, %H:%M UTC')}",
            label_style
        ))
        elements.append(Spacer(1, 8))

        for result in bidder["criteria_results"]:
            verdict = result["verdict"]
            verdict_color = {
                "PASS": colors.HexColor('#1a7f37'),
                "FAIL": colors.HexColor('#c5221f'),
                "NEEDS_REVIEW": colors.HexColor('#b06000')
            }.get(verdict, colors.black)

            header_data = [[
                Paragraph(f"<b>{result['criterion_name']}</b>", normal_style),
                Paragraph(f"<b><font color='{verdict_color.hexval()}'>{verdict.replace('_', ' ')}</font></b>", normal_style)
            ]]
            header_table = Table(header_data, colWidths=[380, 100])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#fafafa')),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(header_table)

            detail_text = (
                f"<b>Extracted value:</b> {result['extracted_value'] or '—'}<br/>"
                f"<b>Source page:</b> {result.get('source_page') or '—'}<br/>"
                f"<b>Evidence:</b> {result.get('raw_snippet') or '—'}<br/>"
                f"<b>Confidence:</b> {round((result.get('confidence') or 0) * 100)}%<br/>"
                f"<b>Reason:</b> {result['reason']}"
            )

            if result.get("officer_action"):
                detail_text += (
                    f"<br/><br/><b>Officer decision:</b> {result['officer_action']}<br/>"
                    f"<b>Justification:</b> {result['officer_justification']}<br/>"
                    f"<b>Decided at:</b> {datetime.fromisoformat(result['decided_at']).strftime('%d %b %Y, %H:%M UTC') if result.get('decided_at') else '—'}"
                )

            elements.append(Paragraph(detail_text, normal_style))
            elements.append(Spacer(1, 10))

    # Footer note
    elements.append(PageBreak())
    elements.append(Paragraph("Certification", heading_style))
    elements.append(Paragraph(
        "This report is system-generated by ClearBid and reflects the complete evaluation "
        "trail for this tender as of the generation timestamp above. All automated verdicts "
        "were produced by a deterministic rule engine based on evidence extracted from submitted "
        "documents. All officer decisions on ambiguous cases are recorded with justification and "
        "timestamp. This report is suitable for audit committee review, RTI response, or tribunal submission.",
        normal_style
    ))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("Officer signature: _______________________     Date: _______________", normal_style))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()