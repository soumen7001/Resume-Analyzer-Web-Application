"""
Resume Parser Module
Handles text extraction from PDF and DOCX files.
"""

import os
import re
from typing import Dict, List, Optional


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from PDF file using pdfplumber (better than PyPDF2).
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text as string
    """
    try:
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except ImportError:
        # Fallback to PyPDF2 if pdfplumber not available
        try:
            import PyPDF2
            text = ""
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            raise Exception(f"Failed to extract text from PDF: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def extract_text_from_docx(file_path: str) -> str:
    """
    Extract text from DOCX file using python-docx.
    
    Args:
        file_path: Path to the DOCX file
        
    Returns:
        Extracted text as string
    """
    try:
        from docx import Document
        doc = Document(file_path)
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text.append(paragraph.text)
        return "\n".join(text)
    except Exception as e:
        raise Exception(f"Failed to extract text from DOCX: {str(e)}")


def extract_text_from_file(file_path: str) -> str:
    """
    Extract text from file based on extension.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Extracted text as string
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}")


def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    """
    Extract contact information from resume text.
    
    Args:
        text: Resume text
        
    Returns:
        Dictionary with contact information
    """
    contact = {
        'email': None,
        'phone': None,
        'linkedin': None,
        'github': None,
        'website': None
    }
    
    # Email regex
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    if emails:
        contact['email'] = emails[0]
    
    # Phone regex (various formats)
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    phones = re.findall(phone_pattern, text)
    if phones:
        contact['phone'] = phones[0]
    
    # LinkedIn
    linkedin_pattern = r'(?:linkedin\.com/in/|linkedin\.com/profile/view\?id=)([A-Za-z0-9_-]+)'
    linkedin = re.findall(linkedin_pattern, text, re.IGNORECASE)
    if linkedin:
        contact['linkedin'] = linkedin[0]
    
    # GitHub
    github_pattern = r'(?:github\.com/|github\.io/)([A-Za-z0-9_-]+)'
    github = re.findall(github_pattern, text, re.IGNORECASE)
    if github:
        contact['github'] = github[0]
    
    # Website/Portfolio
    website_pattern = r'(?:https?://)?(?:www\.)?([A-Za-z0-9-]+\.(?:com|io|dev|net|org|me|co))'
    websites = re.findall(website_pattern, text, re.IGNORECASE)
    # Filter out common false positives
    filtered_websites = [w for w in websites if not any(x in w.lower() for x in ['linkedin', 'github', 'gmail', 'yahoo', 'hotmail', 'outlook'])]
    if filtered_websites:
        contact['website'] = filtered_websites[0]
    
    return contact


def extract_education(text: str) -> List[Dict[str, str]]:
    """
    Extract education information from resume text.
    
    Args:
        text: Resume text
        
    Returns:
        List of education entries
    """
    education = []
    
    # Common degree patterns
    degree_patterns = [
        r'(?:Bachelor|Master|PhD|Doctorate|Associate|B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|Ph\.?D\.?|MBA|B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?)\s+(?:of\s+|in\s+)?([A-Za-z\s,]+)',
        r'(?:B\.?S\.?|M\.?S\.?|B\.?A\.?|M\.?A\.?|Ph\.?D\.?|MBA|B\.?Tech|M\.?Tech|B\.?E\.?|M\.?E\.?)\s+(?:in|of)\s+([A-Za-z\s,]+)',
    ]
    
    # University patterns
    university_patterns = [
        r'(?:University|College|Institute|School)\s+of\s+([A-Za-z\s,]+)',
        r'([A-Za-z\s]+)\s+(?:University|College|Institute)',
    ]
    
    # Year pattern
    year_pattern = r'\b(?:19|20)\d{2}\b'
    
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if any(keyword in line.lower() for keyword in ['university', 'college', 'institute', 'bachelor', 'master', 'phd', 'degree', 'diploma']):
            education.append({
                'raw': line,
                'degree': None,
                'institution': None,
                'year': None
            })
    
    return education


def extract_experience(text: str) -> List[Dict[str, str]]:
    """
    Extract work experience from resume text.
    
    Args:
        text: Resume text
        
    Returns:
        List of experience entries
    """
    experience = []
    
    # Look for experience sections
    exp_keywords = ['experience', 'employment', 'work history', 'professional experience', 'career']
    
    lines = text.split('\n')
    in_experience_section = False
    current_job = {}
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Check if we're entering experience section
        if any(keyword in line_lower for keyword in exp_keywords) and len(line_lower) < 50:
            in_experience_section = True
            continue
        
        # Check if we're leaving experience section (next major section)
        if in_experience_section and line_lower and any(keyword in line_lower for keyword in ['education', 'skills', 'projects', 'certifications', 'awards']):
            in_experience_section = False
        
        if in_experience_section and line.strip():
            # Try to parse job entries (company - role - dates)
            experience.append({
                'raw': line.strip()
            })
    
    return experience


def extract_skills(text: str) -> Dict[str, List[str]]:
    """
    Extract technical and soft skills from resume text.
    
    Args:
        text: Resume text
        
    Returns:
        Dictionary with technical and soft skills
    """
    # Comprehensive skill keywords
    technical_skills = [
        # Programming Languages
        'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'go', 'rust', 'ruby', 'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html', 'css', 'bash', 'powershell',
        # Web Frameworks
        'react', 'angular', 'vue', 'svelte', 'next.js', 'nuxt', 'django', 'flask', 'fastapi', 'spring', 'express', 'node.js', 'laravel', 'rails', 'asp.net', '.net core',
        # Databases
        'postgresql', 'mysql', 'mongodb', 'redis', 'sqlite', 'oracle', 'sql server', 'cassandra', 'dynamodb', 'elasticsearch', 'firebase', 'supabase',
        # Cloud & DevOps
        'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'jenkins', 'gitlab ci', 'github actions', 'terraform', 'ansible', 'prometheus', 'grafana', 'nginx', 'apache',
        # Tools & Platforms
        'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'vs code', 'intellij', 'eclipse', 'vim', 'postman', 'swagger', 'figma', 'sketch',
        # Data Science & ML
        'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'opencv', 'matplotlib', 'seaborn', 'plotly', 'tableau', 'power bi', 'spark', 'hadoop', 'kafka',
        # Mobile
        'android', 'ios', 'flutter', 'react native', 'xamarin', 'ionic', 'swiftui', 'jetpack compose',
        # Testing
        'jest', 'mocha', 'cypress', 'selenium', 'pytest', 'junit', 'testng', 'playwright',
        # Other
        'linux', 'unix', 'windows', 'macos', 'rest api', 'graphql', 'grpc', 'microservices', 'serverless', 'ci/cd', 'agile', 'scrum', 'kanban',
    ]
    
    soft_skills = [
        'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking', 'adaptability', 'time management', 'creativity', 'collaboration', 'organization', 'analytical', 'detail oriented', 'multitasking', 'decision making', 'negotiation', 'presentation', 'mentoring', 'project management', 'strategic planning', 'customer service', 'interpersonal',
    ]
    
    text_lower = text.lower()
    
    found_technical = []
    found_soft = []
    
    for skill in technical_skills:
        # Use word boundaries for better matching
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_technical.append(skill.title())
    
    for skill in soft_skills:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found_soft.append(skill.title())
    
    return {
        'technical': list(set(found_technical)),
        'soft': list(set(found_soft))
    }


def extract_projects(text: str) -> List[Dict[str, str]]:
    """
    Extract projects from resume text.
    
    Args:
        text: Resume text
        
    Returns:
        List of project entries
    """
    projects = []
    project_keywords = ['project', 'portfolio', 'github', 'personal project', 'side project']
    
    lines = text.split('\n')
    in_project_section = False
    
    for line in lines:
        line_lower = line.lower().strip()
        
        if any(keyword in line_lower for keyword in project_keywords) and len(line_lower) < 50:
            in_project_section = True
            continue
        
        if in_project_section and line_lower and any(keyword in line_lower for keyword in ['education', 'experience', 'skills', 'certifications', 'awards']):
            in_project_section = False
        
        if in_project_section and line.strip():
            projects.append({
                'raw': line.strip()
            })
    
    return projects


def extract_certifications(text: str) -> List[str]:
    """
    Extract certifications from resume text.
    
    Args:
        text: Resume text
        
    Returns:
        List of certifications
    """
    certifications = []
    cert_keywords = ['certification', 'certified', 'certificate', 'credential', 'license']
    
    lines = text.split('\n')
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in cert_keywords):
            certifications.append(line.strip())
    
    return certifications


def parse_resume(file_path: str) -> Dict:
    """
    Main function to parse resume and extract all information.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        Dictionary with all extracted information
    """
    text = extract_text_from_file(file_path)
    
    return {
        'raw_text': text,
        'contact_info': extract_contact_info(text),
        'education': extract_education(text),
        'experience': extract_experience(text),
        'skills': extract_skills(text),
        'projects': extract_projects(text),
        'certifications': extract_certifications(text),
        'word_count': len(text.split()),
        'char_count': len(text)
    }


if __name__ == "__main__":
    # Test with a sample file if provided
    import sys
    if len(sys.argv) > 1:
        result = parse_resume(sys.argv[1])
        import json
        print(json.dumps(result, indent=2))