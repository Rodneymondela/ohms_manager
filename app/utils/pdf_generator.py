import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from datetime import datetime # To format dates

def generate_exposure_pdf(exposure_record):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer,
                            rightMargin=0.75*inch, leftMargin=0.75*inch,
                            topMargin=1*inch, bottomMargin=1*inch,
                            title=f"Exposure Record - ID {exposure_record.id}")

    styles = getSampleStyleSheet()
    # Custom styles
    title_style = ParagraphStyle(name='TitleCustom', parent=styles['h1'], alignment=TA_CENTER, spaceAfter=0.3*inch, fontSize=16)
    heading_style = ParagraphStyle(name='HeadingCustom', parent=styles['h2'], spaceAfter=0.1*inch, spaceBefore=0.2*inch, fontSize=14)
    body_style = styles['BodyText']
    body_style_bold_label = ParagraphStyle(name='BodyTextBoldLabel', parent=body_style, fontName='Helvetica-Bold')
    body_style_justify = ParagraphStyle(name='BodyTextJustify', parent=styles['BodyText'], alignment=TA_JUSTIFY)

    story = []

    # Title
    story.append(Paragraph(f"Occupational Exposure Record - ID: {exposure_record.id}", title_style))

    # Employee and Hazard Info
    story.append(Paragraph("Subject and Hazard Information", heading_style))
    data_employee_hazard = [
        [Paragraph("Employee:", body_style_bold_label), Paragraph(exposure_record.employee.name if exposure_record.employee else 'N/A', body_style)],
        [Paragraph("Job Title:", body_style_bold_label), Paragraph(exposure_record.employee.job_title if exposure_record.employee else 'N/A', body_style)],
        [Paragraph("Department:", body_style_bold_label), Paragraph(exposure_record.employee.department if exposure_record.employee else 'N/A', body_style)],
        [Paragraph("Hazard:", body_style_bold_label), Paragraph(exposure_record.hazard.name if exposure_record.hazard else 'N/A', body_style)],
        [Paragraph("Hazard Category:", body_style_bold_label), Paragraph(exposure_record.hazard.category if exposure_record.hazard else 'N/A', body_style)],
    ]
    table_eh = Table(data_employee_hazard, colWidths=[1.7*inch, 4.8*inch]) # Adjusted colWidths
    table_eh.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0), # Less padding for labels
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
    ]))
    story.append(table_eh)
    story.append(Spacer(1, 0.2*inch))

    # Exposure Details
    story.append(Paragraph("Exposure Details", heading_style))
    exposure_date_str = exposure_record.date.strftime('%Y-%m-%d %H:%M') if exposure_record.date else 'N/A'
    hazard_unit_str = exposure_record.hazard.unit if exposure_record.hazard else ''
    duration_str = f"{exposure_record.duration} hours" if exposure_record.duration is not None else 'N/A'

    data_exposure = [
        [Paragraph("Date of Exposure:", body_style_bold_label), Paragraph(exposure_date_str, body_style)],
        [Paragraph("Exposure Level:", body_style_bold_label), Paragraph(f"{exposure_record.exposure_level} {hazard_unit_str}", body_style)],
        [Paragraph("Duration:", body_style_bold_label), Paragraph(duration_str, body_style)],
        [Paragraph("Location:", body_style_bold_label), Paragraph(exposure_record.location if exposure_record.location else 'N/A', body_style)],
    ]
    table_exp = Table(data_exposure, colWidths=[1.7*inch, 4.8*inch])
    table_exp.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey),
    ]))
    story.append(table_exp)
    story.append(Spacer(1, 0.2*inch))

    # Hazard Information (Description and Safety Measures)
    if exposure_record.hazard:
        if exposure_record.hazard.description or exposure_record.hazard.safety_measures:
            story.append(Paragraph("Hazard Information", heading_style))
            if exposure_record.hazard.description:
                story.append(Paragraph("<b>Description:</b>", body_style)) # Using <b> for inline bold
                story.append(Paragraph(exposure_record.hazard.description, body_style_justify))
                story.append(Spacer(1, 0.05*inch))
            if exposure_record.hazard.safety_measures:
                story.append(Paragraph("<b>Control Measures:</b>", body_style))
                story.append(Paragraph(exposure_record.hazard.safety_measures, body_style_justify))
            story.append(Spacer(1, 0.2*inch))

    # Notes
    if exposure_record.notes:
        story.append(Paragraph("Exposure Notes", heading_style))
        story.append(Paragraph(exposure_record.notes, body_style_justify))
        story.append(Spacer(1, 0.2*inch))

    # Footer Info
    story.append(Paragraph(f"Recorded By: {exposure_record.recorder.username if exposure_record.recorder else 'N/A'}", body_style))
    created_at_str = exposure_record.created_at.strftime('%Y-%m-%d %H:%M:%S') if exposure_record.created_at else 'N/A'
    story.append(Paragraph(f"Record Created At: {created_at_str} UTC", body_style)) # Assuming UTC
    story.append(Paragraph(f"Report Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC", body_style))

    doc.build(story)
    pdf_value = buffer.getvalue()
    buffer.close()
    return pdf_value
