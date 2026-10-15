"""
Resume Analyzer Module
Handles resume analysis, scoring, and job description matching.
"""

import re
import math
from typing import Dict, List, Any, Tuple
from collections import Counter

# Optional ML imports with fallback
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    np = None


# Common technical skills for ATS scoring
TECHNICAL_SKILLS_DB = [
    # Languages
    'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'go', 'rust', 'ruby',
    'php', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html', 'css', 'bash', 'powershell',
    # Frontend
    'react', 'angular', 'vue', 'svelte', 'next.js', 'nuxt', 'tailwind', 'bootstrap',
    'webpack', 'vite', 'sass', 'less',
    # Backend
    'django', 'flask', 'fastapi', 'spring', 'express', 'node.js', 'laravel', 'rails',
    'asp.net', '.net core', 'graphql', 'rest api', 'grpc',
    # Databases
    'postgresql', 'mysql', 'mongodb', 'redis', 'sqlite', 'oracle', 'sql server',
    'cassandra', 'dynamodb', 'elasticsearch', 'firebase', 'supabase',
    # Cloud & DevOps
    'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'jenkins',
    'gitlab ci', 'github actions', 'terraform', 'ansible', 'prometheus', 'grafana',
    'nginx', 'apache', 'ci/cd',
    # Data Science & ML
    'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras', 'opencv',
    'matplotlib', 'seaborn', 'plotly', 'tableau', 'power bi', 'spark', 'hadoop', 'kafka',
    # Mobile
    'android', 'ios', 'flutter', 'react native', 'xamarin', 'ionic', 'swiftui', 'jetpack compose',
    # Tools
    'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'vs code',
    'intellij', 'postman', 'figma', 'linux', 'unix',
    # Testing
    'jest', 'mocha', 'cypress', 'selenium', 'pytest', 'junit', 'testng', 'playwright',
    # Methodologies
    'agile', 'scrum', 'kanban', 'microservices', 'serverless', 'tdd', 'bdd',
]


SOFT_SKILLS_DB = [
    'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking',
    'adaptability', 'time management', 'creativity', 'collaboration', 'organization',
    'analytical', 'detail oriented', 'multitasking', 'decision making', 'negotiation',
    'presentation', 'mentoring', 'project management', 'strategic planning',
    'customer service', 'interpersonal', 'emotional intelligence', 'conflict resolution',
    'self motivated', 'quick learner', 'innovative',
]


ACTION_VERBS = [
    'achieved', 'improved', 'developed', 'created', 'designed', 'implemented', 'led', 'managed',
    'built', 'launched', 'optimized', 'increased', 'decreased', 'reduced', 'automated', 'streamlined',
    'spearheaded', 'orchestrated', 'delivered', 'executed', 'established', 'initiated', 'transformed',
    'accelerated', 'enhanced', 'modernized', 'refactored', 'architected', 'scaled', 'secured',
    'mentored', 'coached', 'trained', 'recruited', 'budgeted', 'forecasted', 'analyzed',
    'researched', 'investigated', 'diagnosed', 'resolved', 'troubleshot', 'configured', 'deployed',
    'monitored', 'maintained', 'upgraded', 'migrated', 'integrated', 'collaborated', 'partnered',
    'negotiated', 'presented', 'documented', 'standardized', 'validated', 'verified', 'tested',
]


def calculate_ats_score(parsed_resume: Dict) -> Dict[str, Any]:
    """
    Calculate ATS (Applicant Tracking System) compatibility score.

    Args:
        parsed_resume: Parsed resume data

    Returns:
        Dictionary with ATS score and breakdown
    """
    score = 0
    breakdown = {}

    text = parsed_resume.get('raw_text', '').lower()
    contact = parsed_resume.get('contact_info', {})
    skills = parsed_resume.get('skills', {})
    education = parsed_resume.get('education', [])
    experience = parsed_resume.get('experience', [])
    projects = parsed_resume.get('projects', [])
    certifications = parsed_resume.get('certifications', [])

    # 1. Contact Information (15 points)
    contact_score = 0
    if contact.get('email'):
        contact_score += 5
    if contact.get('phone'):
        contact_score += 5
    if contact.get('linkedin'):
        contact_score += 3
    if contact.get('github'):
        contact_score += 2
    breakdown['contact_info'] = min(contact_score, 15)
    score += breakdown['contact_info']

    # 2. Skills Section (25 points)
    technical_skills = skills.get('technical', [])
    soft_skills = skills.get('soft', [])
    skills_score = min(len(technical_skills) * 1.5 + len(soft_skills) * 1, 25)
    breakdown['skills'] = round(skills_score, 1)
    score += breakdown['skills']

    # 3. Experience Section (25 points)
    exp_score = min(len(experience) * 5, 25)
    # Bonus for action verbs
    action_verb_count = sum(1 for verb in ACTION_VERBS if verb in text)
    exp_score += min(action_verb_count * 0.5, 10)
    breakdown['experience'] = min(round(exp_score, 1), 25)
    score += breakdown['experience']

    # 4. Education Section (15 points)
    edu_score = min(len(education) * 5, 15)
    breakdown['education'] = edu_score
    score += breakdown['education']

    # 5. Projects (10 points)
    proj_score = min(len(projects) * 3, 10)
    breakdown['projects'] = proj_score
    score += breakdown['projects']

    # 6. Certifications (10 points)
    cert_score = min(len(certifications) * 3, 10)
    breakdown['certifications'] = cert_score
    score += breakdown['certifications']

    # 7. Formatting & Keywords (penalty/bonus)
    formatting_penalty = 0
    if len(text) < 300:
        formatting_penalty += 10  # Too short
    if not re.search(r'\b(?:experience|education|skills)\b', text, re.IGNORECASE):
        formatting_penalty += 10  # Missing standard sections
    if text.count('\n') < 10:
        formatting_penalty += 5  # Poor structure

    breakdown['formatting_penalty'] = -formatting_penalty
    score += breakdown['formatting_penalty']

    final_score = max(0, min(round(score), 100))

    return {
        'score': final_score,
        'breakdown': breakdown,
        'feedback': generate_ats_feedback(breakdown, parsed_resume)
    }


def generate_ats_feedback(breakdown: Dict, parsed_resume: Dict) -> List[str]:
    """Generate ATS improvement feedback."""
    feedback = []

    if breakdown.get('contact_info', 0) < 15:
        missing = []
        contact = parsed_resume.get('contact_info', {})
        if not contact.get('email'):
            missing.append('email')
        if not contact.get('phone'):
            missing.append('phone number')
        if not contact.get('linkedin'):
            missing.append('LinkedIn URL')
        if not contact.get('github'):
            missing.append('GitHub profile')
        if missing:
            feedback.append(f"Add missing contact information: {', '.join(missing)}")

    if breakdown.get('skills', 0) < 20:
        feedback.append("Add more relevant technical and soft skills to your resume")

    if breakdown.get('experience', 0) < 20:
        feedback.append("Expand your experience section with more details and action verbs")

    if breakdown.get('education', 0) < 10:
        feedback.append("Include your education details (degree, institution, graduation year)")

    if breakdown.get('projects', 0) < 5:
        feedback.append("Add relevant projects to showcase your practical experience")

    if breakdown.get('certifications', 0) < 5:
        feedback.append("Consider adding relevant certifications to strengthen your profile")

    if breakdown.get('formatting_penalty', 0) < 0:
        feedback.append("Improve resume formatting: use standard section headers and clear structure")

    return feedback


def calculate_resume_score(parsed_resume: Dict, job_description: str = "") -> Dict[str, Any]:
    """
    Calculate overall resume score out of 100.

    Args:
        parsed_resume: Parsed resume data
        job_description: Optional job description for matching

    Returns:
        Dictionary with overall score and components
    """
    ats_result = calculate_ats_score(parsed_resume)
    ats_score = ats_result['score']

    # Content quality score (based on completeness)
    content_score = calculate_content_quality(parsed_resume)

    # Job match score (if JD provided)
    job_match_score = 0
    if job_description:
        match_result = match_job_description(parsed_resume, job_description)
        job_match_score = match_result['match_percentage']

    # Weighted overall score
    if job_description:
        overall_score = round(0.4 * ats_score + 0.3 * content_score + 0.3 * job_match_score)
    else:
        overall_score = round(0.6 * ats_score + 0.4 * content_score)

    return {
        'overall_score': overall_score,
        'ats_score': ats_score,
        'content_score': content_score,
        'job_match_score': job_match_score if job_description else None,
        'ats_breakdown': ats_result['breakdown'],
        'ats_feedback': ats_result['feedback']
    }


def calculate_content_quality(parsed_resume: Dict) -> int:
    """Calculate content quality score based on resume completeness."""
    score = 0

    text = parsed_resume.get('raw_text', '')
    contact = parsed_resume.get('contact_info', {})
    skills = parsed_resume.get('skills', {})
    education = parsed_resume.get('education', [])
    experience = parsed_resume.get('experience', [])
    projects = parsed_resume.get('projects', [])
    certifications = parsed_resume.get('certifications', [])

    # Word count (optimal 400-800 words)
    word_count = len(text.split())
    if 400 <= word_count <= 800:
        score += 20
    elif 300 <= word_count < 400 or 800 < word_count <= 1000:
        score += 15
    elif 200 <= word_count < 300 or 1000 < word_count <= 1200:
        score += 10
    else:
        score += 5

    # Contact completeness
    contact_fields = sum(1 for v in contact.values() if v)
    score += min(contact_fields * 3, 15)

    # Skills
    tech_skills = len(skills.get('technical', []))
    soft_skills_count = len(skills.get('soft', []))
    score += min(tech_skills * 2 + soft_skills_count * 1, 25)

    # Experience depth
    score += min(len(experience) * 4, 20)

    # Education
    score += min(len(education) * 3, 10)

    # Projects
    score += min(len(projects) * 2, 10)

    # Certifications
    score += min(len(certifications) * 2, 10)

    return min(score, 100)


def match_job_description(parsed_resume: Dict, job_description: str) -> Dict[str, Any]:
    """
    Match resume against job description using TF-IDF and cosine similarity.

    Args:
        parsed_resume: Parsed resume data
        job_description: Job description text

    Returns:
        Dictionary with match results
    """
    resume_text = parsed_resume.get('raw_text', '')

    # Extract keywords from job description and resume
    jd_keywords = extract_keywords(job_description)
    resume_keywords = extract_keywords(resume_text)

    # Build keyword sets FIRST (Fix: was referenced before assignment in fallback)
    jd_kw_set = set(kw.lower() for kw in jd_keywords)
    resume_kw_set = set(kw.lower() for kw in resume_keywords)

    # Keyword overlap
    matching_keywords = list(jd_kw_set & resume_kw_set)
    missing_keywords = list(jd_kw_set - resume_kw_set)

    keyword_score = 0
    if jd_kw_set:
        keyword_score = round(len(matching_keywords) / len(jd_kw_set) * 100)

    # TF-IDF Cosine Similarity (with fallback to Jaccard if sklearn not available)
    tfidf_score = 0
    if SKLEARN_AVAILABLE:
        try:
            vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2), max_features=5000)
            tfidf_matrix = vectorizer.fit_transform([resume_text, job_description])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            tfidf_score = round(similarity * 100)
        except Exception:
            tfidf_score = 0

    # Fallback: Jaccard similarity on keyword sets
    if tfidf_score == 0 and jd_kw_set and resume_kw_set:
        union = jd_kw_set | resume_kw_set
        if union:
            tfidf_score = round(len(jd_kw_set & resume_kw_set) / len(union) * 100)

    # Combined match percentage
    match_percentage = round(0.6 * tfidf_score + 0.4 * keyword_score)

    # Skill matching
    resume_skills = set(s.lower() for s in parsed_resume.get('skills', {}).get('technical', []))
    jd_skills = extract_skills_from_text(job_description)

    matching_skills = list(resume_skills & set(s.lower() for s in jd_skills))
    missing_skills = list(set(s.lower() for s in jd_skills) - resume_skills)

    return {
        'match_percentage': match_percentage,
        'tfidf_similarity': tfidf_score,
        'keyword_overlap_score': keyword_score,
        'matching_keywords': matching_keywords[:20],
        'missing_keywords': missing_keywords[:20],
        'matching_skills': matching_skills[:15],
        'missing_skills': missing_skills[:15],
        'jd_keywords_count': len(jd_keywords),
        'resume_keywords_count': len(resume_keywords)
    }


def extract_keywords(text: str, top_n: int = 50) -> List[str]:
    """
    Extract important keywords from text using skill database + frequency analysis.

    Args:
        text: Input text
        top_n: Number of top keywords to return

    Returns:
        List of keywords
    """
    text_lower = text.lower()
    all_skills = TECHNICAL_SKILLS_DB + SOFT_SKILLS_DB
    found_keywords = []

    # Match known skills first
    for skill in all_skills:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found_keywords.append(skill)

    # Extract capitalized phrases (likely proper nouns / technologies)
    capitalized = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
    found_set_lower = {k.lower() for k in found_keywords}
    for word in capitalized:
        if len(word) > 2 and word.lower() not in found_set_lower:
            found_keywords.append(word)
            found_set_lower.add(word.lower())

    # High-frequency meaningful words
    stop_words = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
        'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'can', 'this', 'that', 'these', 'those', 'a', 'an', 'i', 'you', 'he', 'she',
        'it', 'we', 'they', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
        'not', 'no', 'nor', 'so', 'yet', 'both', 'either', 'neither', 'also',
    }
    word_freq = Counter(text_lower.split())
    for word, _ in word_freq.most_common(30):
        if word not in stop_words and len(word) > 3 and word.isalpha():
            if word not in found_set_lower:
                found_keywords.append(word)
                found_set_lower.add(word)

    return found_keywords[:top_n]


def extract_skills_from_text(text: str) -> List[str]:
    """Extract technical skills from text by matching against skills database."""
    text_lower = text.lower()
    found = []
    for skill in TECHNICAL_SKILLS_DB:
        if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
            found.append(skill)
    return found


def analyze_resume(parsed_resume: Dict, job_description: str = "") -> Dict[str, Any]:
    """
    Main analysis function — performs complete resume analysis.

    Args:
        parsed_resume: Parsed resume data
        job_description: Optional job description

    Returns:
        Complete analysis results dictionary
    """
    # Calculate scores
    score_result = calculate_resume_score(parsed_resume, job_description)

    # Detected skills
    skills = parsed_resume.get('skills', {})

    # Missing common skills (top skills not in resume)
    all_known_skills = set(TECHNICAL_SKILLS_DB)
    resume_tech_skills = set(s.lower() for s in skills.get('technical', []))
    missing_common_skills = list(all_known_skills - resume_tech_skills)[:15]

    # Strengths and improvements
    strengths = identify_strengths(parsed_resume, score_result)
    improvements = identify_improvements(parsed_resume, score_result)

    # Keyword analysis
    keyword_analysis = perform_keyword_analysis(parsed_resume, job_description)

    result = {
        'overall_score': score_result['overall_score'],
        'ats_score': score_result['ats_score'],
        'content_score': score_result['content_score'],
        'job_match_score': score_result['job_match_score'],
        'word_count': parsed_resume.get('word_count', len(parsed_resume.get('raw_text', '').split())),
        'skills_detected': {
            'technical': skills.get('technical', []),
            'soft': skills.get('soft', [])
        },
        'missing_skills': missing_common_skills,
        'strengths': strengths,
        'improvements': improvements,
        'keyword_analysis': keyword_analysis,
        'contact_info': parsed_resume.get('contact_info', {}),
        'education': parsed_resume.get('education', []),
        'experience': parsed_resume.get('experience', []),
        'projects': parsed_resume.get('projects', []),
        'certifications': parsed_resume.get('certifications', []),
        'ats_breakdown': score_result['ats_breakdown'],
        'ats_feedback': score_result['ats_feedback']
    }

    # Add job matching results if JD provided
    if job_description:
        match_result = match_job_description(parsed_resume, job_description)
        result['job_match'] = match_result
        result['suggestions'] = generate_job_suggestions(match_result, parsed_resume)
    else:
        result['suggestions'] = generate_general_suggestions(parsed_resume, score_result)

    return result


def identify_strengths(parsed_resume: Dict, score_result: Dict) -> List[str]:
    """Identify resume strengths."""
    strengths = []

    skills = parsed_resume.get('skills', {})
    experience = parsed_resume.get('experience', [])
    projects = parsed_resume.get('projects', [])
    certifications = parsed_resume.get('certifications', [])
    contact = parsed_resume.get('contact_info', {})
    text = parsed_resume.get('raw_text', '')

    tech_count = len(skills.get('technical', []))
    if tech_count >= 10:
        strengths.append(f"Strong technical skill set with {tech_count} technologies listed")
    elif tech_count >= 5:
        strengths.append(f"Good technical foundation with {tech_count} key technologies")

    if len(experience) >= 3:
        strengths.append(f"Substantial work experience with {len(experience)} positions")
    elif len(experience) >= 1:
        strengths.append("Relevant work experience included")

    if len(projects) >= 2:
        strengths.append(f"Portfolio of {len(projects)} projects demonstrating practical skills")
    elif len(projects) == 1:
        strengths.append("Hands-on project experience included")

    if len(certifications) >= 2:
        strengths.append(f"{len(certifications)} professional certifications validate expertise")
    elif len(certifications) == 1:
        strengths.append("Professional certification included")

    contact_count = sum(1 for v in contact.values() if v)
    if contact_count >= 4:
        strengths.append("Complete contact information with professional links")
    elif contact_count >= 2:
        strengths.append("Essential contact information present")

    if score_result.get('ats_score', 0) >= 80:
        strengths.append("Excellent ATS compatibility — well-structured for automated screening")
    elif score_result.get('ats_score', 0) >= 60:
        strengths.append("Good ATS compatibility with room for minor improvements")

    # Check for measurable achievements
    numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', text)
    if len(numbers) >= 5:
        strengths.append("Strong use of quantifiable achievements and metrics")
    elif len(numbers) >= 2:
        strengths.append("Some measurable achievements with numbers included")

    # Action verbs
    action_verb_count = sum(1 for verb in ACTION_VERBS if verb in text.lower())
    if action_verb_count >= 8:
        strengths.append(f"Strong use of action verbs ({action_verb_count} detected)")

    return strengths[:8]


def identify_improvements(parsed_resume: Dict, score_result: Dict) -> List[str]:
    """Identify areas for improvement."""
    improvements = []

    skills = parsed_resume.get('skills', {})
    experience = parsed_resume.get('experience', [])
    projects = parsed_resume.get('projects', [])
    certifications = parsed_resume.get('certifications', [])
    contact = parsed_resume.get('contact_info', {})
    text = parsed_resume.get('raw_text', '')

    if len(skills.get('technical', [])) < 5:
        improvements.append("Add more technical skills relevant to your target roles")

    if len(skills.get('soft', [])) < 3:
        improvements.append("Include key soft skills: communication, teamwork, problem-solving")

    if len(experience) == 0:
        improvements.append("Add work experience, internships, or relevant projects")
    elif len(experience) < 2:
        improvements.append("Expand experience section with more details and achievements")

    action_verb_count = sum(1 for verb in ACTION_VERBS if verb in text.lower())
    if action_verb_count < 5:
        improvements.append("Use more action verbs (achieved, developed, led, optimized, etc.)")

    numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', text)
    if len(numbers) < 3:
        improvements.append("Add measurable achievements with numbers, percentages, and metrics")

    if len(projects) < 2:
        improvements.append("Include more projects to showcase practical application of skills")

    if len(certifications) == 0:
        improvements.append("Consider obtaining relevant certifications for your field")

    missing_contact = [k for k, v in contact.items() if not v]
    if missing_contact:
        improvements.append(f"Add missing contact info: {', '.join(missing_contact)}")

    word_count = len(text.split())
    if word_count < 300:
        improvements.append("Resume is too brief — aim for 400–800 words with more detail")
    elif word_count > 1000:
        improvements.append("Resume may be too long — consider condensing to 1–2 pages")

    return improvements[:8]


def perform_keyword_analysis(parsed_resume: Dict, job_description: str) -> Dict[str, Any]:
    """Perform keyword analysis on resume and optionally against job description."""
    text = parsed_resume.get('raw_text', '')
    resume_keywords = extract_keywords(text)

    result = {
        'resume_keywords': resume_keywords[:30],
        'keyword_density': {}
    }

    # Keyword density for top skills
    text_lower = text.lower()
    word_count = max(len(text.split()), 1)

    for skill in TECHNICAL_SKILLS_DB[:30]:
        count = len(re.findall(r'\b' + re.escape(skill) + r'\b', text_lower))
        if count > 0:
            result['keyword_density'][skill] = round(count / word_count * 100, 2)

    if job_description:
        jd_keywords = extract_keywords(job_description)
        result['job_keywords'] = jd_keywords[:30]
        jd_set = set(k.lower() for k in jd_keywords)
        resume_set = set(k.lower() for k in resume_keywords)
        result['missing_important_keywords'] = list(jd_set - resume_set)[:15]

    return result


def generate_general_suggestions(parsed_resume: Dict, score_result: Dict) -> List[str]:
    """Generate general improvement suggestions when no JD is provided."""
    suggestions = []
    improvements = identify_improvements(parsed_resume, score_result)
    suggestions.extend(improvements[:5])

    suggestions.extend([
        "Tailor your resume for each job by matching keywords from the job description",
        "Use a clean, professional format with consistent fonts and spacing",
        "Start every bullet point with a strong action verb",
        "Quantify achievements with specific numbers and percentages where possible",
        "Include a professional summary at the top highlighting your key value proposition",
        "Ensure your LinkedIn profile is up to date and matches your resume",
        "Proofread carefully for spelling and grammatical errors",
    ])

    return suggestions[:10]


def generate_job_suggestions(match_result: Dict, parsed_resume: Dict) -> List[str]:
    """Generate job-specific improvement suggestions."""
    suggestions = []

    missing_skills = match_result.get('missing_skills', [])
    missing_keywords = match_result.get('missing_keywords', [])
    match_pct = match_result.get('match_percentage', 0)

    if match_pct < 50:
        suggestions.append("Low alignment with this job description — significant tailoring is needed")
    elif match_pct < 70:
        suggestions.append("Moderate alignment — targeted improvements can significantly increase your match rate")
    else:
        suggestions.append("Strong alignment — minor tweaks could make you a top candidate")

    if missing_skills:
        top_missing = missing_skills[:5]
        suggestions.append(f"Add these key missing skills: {', '.join(s.title() for s in top_missing)}")

    if missing_keywords:
        top_missing_kw = missing_keywords[:5]
        suggestions.append(f"Incorporate these important keywords: {', '.join(top_missing_kw)}")

    suggestions.extend([
        "Reorder your skills section to prioritize skills mentioned in the job description",
        "Adjust your professional summary to mirror the job requirements",
        "Highlight relevant projects that demonstrate the required skills",
        "Use the exact terminology from the job description for key technologies",
        "Ensure your experience descriptions address the job's key responsibilities",
    ])

    return suggestions[:8]


if __name__ == "__main__":
    # Test with sample data
    sample_resume = {
        'raw_text': 'John Doe Software Engineer Python JavaScript React AWS Docker Kubernetes',
        'contact_info': {'email': 'john@email.com', 'phone': '123-456-7890', 'linkedin': 'johndoe', 'github': 'johndoe'},
        'skills': {'technical': ['Python', 'JavaScript', 'React', 'AWS', 'Docker'], 'soft': ['Communication', 'Teamwork']},
        'education': [{'raw': 'BS Computer Science'}],
        'experience': [{'raw': 'Software Engineer at Tech Corp'}],
        'projects': [{'raw': 'E-commerce platform'}],
        'certifications': ['AWS Certified']
    }
    result = analyze_resume(sample_resume)
    import json
    print(json.dumps(result, indent=2))