"""
DOCX Exporter Module
Exports structured resume data to a beautifully styled, ATS-compliant Microsoft Word (.docx) document.
"""

import io
from typing import Dict, Any
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


# Color Schemes for templates
TEMPLATE_COLORS = {
    'modern': {
        'primary': RGBColor(79, 70, 229),      # Indigo
        'secondary': RGBColor(30, 41, 59),     # Dark Slate
        'text': RGBColor(51, 65, 85),          # Slate Text
        'accent': RGBColor(14, 165, 233)       # Sky
    },
    'classic': {
        'primary': RGBColor(15, 23, 42),       # Black/Dark Navy
        'secondary': RGBColor(30, 41, 59),
        'text': RGBColor(30, 41, 59),
        'accent': RGBColor(71, 85, 105)
    },
    'minimalist': {
        'primary': RGBColor(31, 41, 55),       # Charcoal
        'secondary': RGBColor(75, 85, 99),
        'text': RGBColor(55, 65, 81),
        'accent': RGBColor(107, 114, 128)
    },
    'tech': {
        'primary': RGBColor(2, 132, 199),      # Cyan/Blue
        'secondary': RGBColor(15, 23, 42),
        'text': RGBColor(51, 65, 85),
        'accent': RGBColor(16, 185, 129)       # Emerald
    },
    'executive': {
        'primary': RGBColor(120, 53, 15),      # Amber/Bronze
        'secondary': RGBColor(30, 41, 59),
        'text': RGBColor(51, 65, 85),
        'accent': RGBColor(180, 83, 9)
    }
}


def add_horizontal_line(paragraph, color_hex="CCCCCC"):
    """Insert a clean horizontal rule under a heading."""
    pPr = paragraph._element.get_or_add_pPr()
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="4" w:color="{color_hex}"/></w:pBdr>')
    pPr.append(pBdr)


def generate_resume_docx(resume_data: Dict[str, Any], template: str = 'modern') -> io.BytesIO:
    """
    Generate a formatted DOCX document from resume dictionary.
    Returns: in-memory BytesIO buffer containing the DOCX file.
    """
    doc = Document()
    
    # 0.75-inch margins for ideal ATS and readability balance
    for section in doc.sections:
        section.top_margin = Inches(0.65)
        section.bottom_margin = Inches(0.65)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

    colors = TEMPLATE_COLORS.get(template, TEMPLATE_COLORS['modern'])
    primary_color = colors['primary']
    text_color = colors['text']

    contact = resume_data.get('contact', {})
    name = contact.get('name', 'Professional Candidate')
    title = contact.get('title', '')
    
    # --- 1. HEADER (Candidate Name & Title) ---
    header_p = doc.add_paragraph()
    header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    header_p.paragraph_format.space_after = Pt(2)
    header_p.paragraph_format.space_before = Pt(0)
    
    name_run = header_p.add_run(name)
    name_run.font.name = 'Arial' if template != 'executive' else 'Georgia'
    name_run.font.size = Pt(20)
    name_run.font.bold = True
    name_run.font.color.rgb = primary_color

    if title:
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_p.paragraph_format.space_after = Pt(4)
        title_p.paragraph_format.space_before = Pt(0)
        title_run = title_p.add_run(title)
        title_run.font.name = 'Arial' if template != 'executive' else 'Georgia'
        title_run.font.size = Pt(11)
        title_run.font.bold = True
        title_run.font.color.rgb = colors['secondary']

    # --- Contact Links / Info Row ---
    contact_parts = []
    if contact.get('email'):
        contact_parts.append(contact['email'])
    if contact.get('phone'):
        contact_parts.append(contact['phone'])
    if contact.get('location'):
        contact_parts.append(contact['location'])
    if contact.get('linkedin'):
        contact_parts.append(f"linkedin.com/in/{contact['linkedin']}")
    if contact.get('github'):
        contact_parts.append(f"github.com/{contact['github']}")
    if contact.get('website'):
        contact_parts.append(contact['website'])

    if contact_parts:
        info_p = doc.add_paragraph()
        info_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        info_p.paragraph_format.space_after = Pt(12)
        info_p.paragraph_format.space_before = Pt(0)
        
        info_run = info_p.add_run("  |  ".join(contact_parts))
        info_run.font.name = 'Arial' if template != 'executive' else 'Georgia'
        info_run.font.size = Pt(9)
        info_run.font.color.rgb = text_color

    def add_section_header(title_text: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(4)
        run = p.add_run(title_text.upper())
        run.font.name = 'Arial' if template != 'executive' else 'Georgia'
        run.font.size = Pt(11)
        run.font.bold = True
        run.font.color.rgb = primary_color
        add_horizontal_line(p, "4F46E5" if template == 'modern' else "475569")
        return p

    # --- 2. PROFESSIONAL SUMMARY ---
    summary_text = resume_data.get('summary', '')
    if summary_text:
        add_section_header("Professional Summary")
        sum_p = doc.add_paragraph()
        sum_p.paragraph_format.space_before = Pt(2)
        sum_p.paragraph_format.space_after = Pt(6)
        sum_p.paragraph_format.line_spacing = 1.15
        r = sum_p.add_run(summary_text)
        r.font.name = 'Arial' if template != 'executive' else 'Georgia'
        r.font.size = Pt(9.5)
        r.font.color.rgb = text_color

    # --- 3. SKILLS ---
    skills_data = resume_data.get('skills', {})
    tech_skills = skills_data.get('technical', [])
    soft_skills = skills_data.get('soft', [])
    
    if tech_skills or soft_skills:
        add_section_header("Skills & Competencies")
        
        if tech_skills:
            p_tech = doc.add_paragraph()
            p_tech.paragraph_format.space_before = Pt(2)
            p_tech.paragraph_format.space_after = Pt(2)
            lbl = p_tech.add_run("Technical Skills: ")
            lbl.bold = True
            lbl.font.size = Pt(9.5)
            lbl.font.color.rgb = colors['secondary']
            val = p_tech.add_run(", ".join(tech_skills))
            val.font.size = Pt(9.5)
            val.font.color.rgb = text_color

        if soft_skills:
            p_soft = doc.add_paragraph()
            p_soft.paragraph_format.space_before = Pt(2)
            p_soft.paragraph_format.space_after = Pt(6)
            lbl2 = p_soft.add_run("Soft & Leadership Skills: ")
            lbl2.bold = True
            lbl2.font.size = Pt(9.5)
            lbl2.font.color.rgb = colors['secondary']
            val2 = p_soft.add_run(", ".join(soft_skills))
            val2.font.size = Pt(9.5)
            val2.font.color.rgb = text_color

    # --- 4. PROFESSIONAL EXPERIENCE ---
    experience = resume_data.get('experience', [])
    if experience:
        add_section_header("Professional Experience")
        for exp in experience:
            exp_p = doc.add_paragraph()
            exp_p.paragraph_format.space_before = Pt(4)
            exp_p.paragraph_format.space_after = Pt(1)
            
            role_run = exp_p.add_run(exp.get('role', 'Role'))
            role_run.bold = True
            role_run.font.size = Pt(10)
            role_run.font.color.rgb = colors['secondary']

            comp = exp.get('company', '')
            if comp:
                comp_run = exp_p.add_run(f" | {comp}")
                comp_run.bold = True
                comp_run.font.size = Pt(10)
                comp_run.font.color.rgb = primary_color

            duration = exp.get('duration', '')
            if duration:
                dur_run = exp_p.add_run(f"  ({duration})")
                dur_run.italic = True
                dur_run.font.size = Pt(9)
                dur_run.font.color.rgb = colors['accent']

            for b in exp.get('bullets', []):
                if b.strip():
                    bp = doc.add_paragraph(style='List Bullet')
                    bp.paragraph_format.space_before = Pt(1)
                    bp.paragraph_format.space_after = Pt(2)
                    bp.paragraph_format.line_spacing = 1.1
                    brun = bp.add_run(b.strip())
                    brun.font.name = 'Arial' if template != 'executive' else 'Georgia'
                    brun.font.size = Pt(9.5)
                    brun.font.color.rgb = text_color

    # --- 5. PROJECTS ---
    projects = resume_data.get('projects', [])
    if projects:
        add_section_header("Projects & Portfolio")
        for proj in projects:
            p_p = doc.add_paragraph()
            p_p.paragraph_format.space_before = Pt(4)
            p_p.paragraph_format.space_after = Pt(1)
            
            p_title = p_p.add_run(proj.get('title', 'Project'))
            p_title.bold = True
            p_title.font.size = Pt(10)
            p_title.font.color.rgb = colors['secondary']

            tech = proj.get('tech', '')
            if tech:
                t_run = p_p.add_run(f" [{tech}]")
                t_run.italic = True
                t_run.font.size = Pt(9)
                t_run.font.color.rgb = primary_color

            for b in proj.get('bullets', []):
                if b.strip():
                    bp = doc.add_paragraph(style='List Bullet')
                    bp.paragraph_format.space_before = Pt(1)
                    bp.paragraph_format.space_after = Pt(2)
                    brun = bp.add_run(b.strip())
                    brun.font.name = 'Arial' if template != 'executive' else 'Georgia'
                    brun.font.size = Pt(9.5)
                    brun.font.color.rgb = text_color

    # --- 6. EDUCATION ---
    education = resume_data.get('education', [])
    if education:
        add_section_header("Education")
        for edu in education:
            edu_p = doc.add_paragraph()
            edu_p.paragraph_format.space_before = Pt(3)
            edu_p.paragraph_format.space_after = Pt(2)
            
            deg = edu_p.add_run(edu.get('degree', 'Degree'))
            deg.bold = True
            deg.font.size = Pt(10)
            deg.font.color.rgb = colors['secondary']

            inst = edu.get('institution', '')
            if inst:
                inst_run = edu_p.add_run(f" - {inst}")
                inst_run.font.size = Pt(9.5)
                inst_run.font.color.rgb = text_color

            yr = edu.get('year', '')
            if yr:
                yr_run = edu_p.add_run(f" ({yr})")
                yr_run.italic = True
                yr_run.font.size = Pt(9)
                yr_run.font.color.rgb = colors['accent']

    # --- 7. CERTIFICATIONS ---
    certifications = resume_data.get('certifications', [])
    if certifications:
        add_section_header("Certifications & Credentials")
        for cert in certifications:
            cert_name = cert.get('name', cert) if isinstance(cert, dict) else str(cert)
            if cert_name.strip():
                cp = doc.add_paragraph(style='List Bullet')
                cp.paragraph_format.space_before = Pt(1)
                cp.paragraph_format.space_after = Pt(2)
                c_run = cp.add_run(cert_name.strip())
                c_run.font.size = Pt(9.5)
                c_run.font.color.rgb = text_color

    # Save to BytesIO stream
    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer
