"""
Main Flask Application for Resume Analyzer & Resume Builder
API Endpoints for resume upload, analysis, job matching, resume generation, and DOCX/PDF export.
"""

import os
import uuid
import io
from datetime import datetime
from typing import Tuple
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# Import our modules
from resume_parser import (
    parse_resume, extract_text_from_file,
    extract_contact_info, extract_skills, extract_education,
    extract_experience, extract_projects, extract_certifications
)
from analyzer import analyze_resume, match_job_description
from resume_generator import generate_optimized_resume
from docx_exporter import generate_resume_docx
from google_ai_analyzer import ai_analyze_resume, merge_ai_with_traditional


app = Flask(__name__)

# Enable CORS for all routes (allows file:// and localhost origins)
CORS(app, resources={r"/*": {"origins": "*"}})

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'docx', 'doc'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def save_uploaded_file(file) -> Tuple[str, str]:
    """Save uploaded file with unique name. Returns (file_path, unique_filename)."""
    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    file.save(file_path)
    return file_path, unique_filename


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    ai_available = False
    try:
        from google_ai_analyzer import ai_analyze_resume
        ai_available = True
    except Exception:
        pass

    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.2.0',
        'services': {
            'analyzer': True,
            'generator': True,
            'docx_exporter': True,
            'ai_analyzer': ai_available
        }
    })


@app.route('/upload-resume', methods=['POST'])
def upload_resume():
    """Upload and parse resume file (PDF/DOCX)."""
    try:
        if 'resume' not in request.files:
            return jsonify({'success': False, 'error': 'No resume file provided'}), 400

        file = request.files['resume']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Allowed: PDF, DOCX, DOC'}), 400

        file_path, unique_filename = save_uploaded_file(file)

        try:
            parsed_data = parse_resume(file_path)
            parsed_data['filename'] = file.filename
            parsed_data['stored_filename'] = unique_filename
            parsed_data['upload_time'] = datetime.utcnow().isoformat()
            parsed_data['file_size'] = os.path.getsize(file_path)

            return jsonify({
                'success': True,
                'message': 'Resume uploaded and parsed successfully',
                'data': parsed_data
            })
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    except RequestEntityTooLarge:
        return jsonify({'success': False, 'error': 'File too large. Maximum size: 16MB'}), 413
    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'}), 500


@app.route('/analyze-resume', methods=['POST'])
def analyze_resume_endpoint():
    """Analyze uploaded resume (supports JSON or multipart)."""
    try:
        job_description = ""
        parsed_resume = None

        if 'resume' in request.files:
            file = request.files['resume']
            if file.filename == '' or not allowed_file(file.filename):
                return jsonify({'success': False, 'error': 'Invalid file'}), 400

            file_path, _ = save_uploaded_file(file)
            try:
                parsed_resume = parse_resume(file_path)
                job_description = request.form.get('job_description', '')
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)

        elif request.is_json:
            data = request.get_json()
            resume_text = data.get('resume_text', '')
            job_description = data.get('job_description', '')

            if not resume_text:
                return jsonify({'success': False, 'error': 'No resume text provided'}), 400

            parsed_resume = {
                'raw_text': resume_text,
                'contact_info': extract_contact_info(resume_text),
                'skills': extract_skills(resume_text),
                'education': extract_education(resume_text),
                'experience': extract_experience(resume_text),
                'projects': extract_projects(resume_text),
                'certifications': extract_certifications(resume_text),
                'word_count': len(resume_text.split()),
                'char_count': len(resume_text)
            }
        else:
            return jsonify({'success': False, 'error': 'Invalid request format. Use multipart/form-data or JSON.'}), 400

        if not parsed_resume:
            return jsonify({'success': False, 'error': 'Failed to process resume'}), 500

        analysis_result = analyze_resume(parsed_resume, job_description)

        return jsonify({
            'success': True,
            'message': 'Analysis complete',
            'data': analysis_result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'Analysis failed: {str(e)}'}), 500


@app.route('/match-job', methods=['POST'])
def match_job_endpoint():
    """Match resume against job description."""
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        resume_text = data.get('resume_text', '')
        job_description = data.get('job_description', '')

        if not resume_text:
            return jsonify({'success': False, 'error': 'Resume text is required'}), 400
        if not job_description:
            return jsonify({'success': False, 'error': 'Job description is required'}), 400

        parsed_resume = {
            'raw_text': resume_text,
            'contact_info': extract_contact_info(resume_text),
            'skills': extract_skills(resume_text),
            'education': extract_education(resume_text),
            'experience': extract_experience(resume_text),
            'projects': extract_projects(resume_text),
            'certifications': extract_certifications(resume_text)
        }

        match_result = match_job_description(parsed_resume, job_description)
        from analyzer import generate_job_suggestions
        suggestions = generate_job_suggestions(match_result, parsed_resume)

        return jsonify({
            'success': True,
            'message': 'Job matching complete',
            'data': {
                'match_percentage': match_result['match_percentage'],
                'tfidf_similarity': match_result['tfidf_similarity'],
                'keyword_overlap_score': match_result['keyword_overlap_score'],
                'matching_keywords': match_result['matching_keywords'],
                'missing_keywords': match_result['missing_keywords'],
                'matching_skills': match_result['matching_skills'],
                'missing_skills': match_result['missing_skills'],
                'suggestions': suggestions
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'Job matching failed: {str(e)}'}), 500


@app.route('/ai-analyze-resume', methods=['POST'])
def ai_analyze_resume_endpoint():
    """
    Run AI-powered resume analysis using Google Gemini (Google AI Studio).

    Accepts the same JSON body as /analyze-resume:
      - resume_text (required): raw resume text
      - job_description (optional): job description for alignment analysis

    Returns merged traditional + AI analysis results.
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        resume_text = data.get('resume_text', '')
        job_description = data.get('job_description', '')

        if not resume_text:
            return jsonify({'success': False, 'error': 'No resume text provided'}), 400

        # Parse resume
        parsed_resume = {
            'raw_text': resume_text,
            'contact_info': extract_contact_info(resume_text),
            'skills': extract_skills(resume_text),
            'education': extract_education(resume_text),
            'experience': extract_experience(resume_text),
            'projects': extract_projects(resume_text),
            'certifications': extract_certifications(resume_text),
            'word_count': len(resume_text.split()),
            'char_count': len(resume_text)
        }

        # Traditional analysis
        traditional_result = analyze_resume(parsed_resume, job_description)

        # AI analysis (non-fatal if it fails)
        ai_result = ai_analyze_resume(parsed_resume, job_description)

        # Merge results
        merged = merge_ai_with_traditional(traditional_result, ai_result)

        return jsonify({
            'success': True,
            'message': 'AI analysis complete',
            'data': merged
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'AI analysis failed: {str(e)}'}), 500


@app.route('/upload-and-analyze', methods=['POST'])
def upload_and_analyze_endpoint():
    """
    Combined endpoint: upload a resume file, parse it, and run analysis in one call.

    Accepts multipart/form-data:
      - resume: file (PDF/DOCX)
      - job_description: optional text
      - ai_mode: optional 'true'/'false' (default false)
    """
    try:
        if 'resume' not in request.files:
            return jsonify({'success': False, 'error': 'No resume file provided'}), 400

        file = request.files['resume']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': 'Invalid file type. Allowed: PDF, DOCX, DOC'}), 400

        job_description = request.form.get('job_description', '')
        ai_mode = request.form.get('ai_mode', 'false').lower() in ('true', '1', 'yes')

        file_path, unique_filename = save_uploaded_file(file)
        try:
            parsed_resume = parse_resume(file_path)
            parsed_resume['filename'] = file.filename
            parsed_resume['stored_filename'] = unique_filename
            parsed_resume['upload_time'] = datetime.utcnow().isoformat()
            parsed_resume['file_size'] = os.path.getsize(file_path)

            traditional_result = analyze_resume(parsed_resume, job_description)

            if ai_mode:
                ai_result = ai_analyze_resume(parsed_resume, job_description)
                merged = merge_ai_with_traditional(traditional_result, ai_result)
                result_data = merged
            else:
                result_data = traditional_result

            return jsonify({
                'success': True,
                'message': 'Resume uploaded and analyzed successfully',
                'data': {
                    'parsed_resume': parsed_resume,
                    'analysis': result_data,
                    'ai_enabled': ai_mode,
                }
            })
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)

    except Exception as e:
        return jsonify({'success': False, 'error': f'Upload and analyze failed: {str(e)}'}), 500


@app.route('/batch-analyze', methods=['POST'])
def batch_analyze_endpoint():
    """
    Analyze multiple resumes at once.

    Accepts multipart/form-data:
      - resumes: multiple files (PDF/DOCX)
      - job_description: optional text
      - ai_mode: optional 'true'/'false' (default false)

    Returns an array of per-file results.
    """
    try:
        files = request.files.getlist('resumes')
        if not files:
            return jsonify({'success': False, 'error': 'No resume files provided'}), 400

        job_description = request.form.get('job_description', '')
        ai_mode = request.form.get('ai_mode', 'false').lower() in ('true', '1', 'yes')

        results = []
        for file in files:
            file_result = {
                'filename': file.filename,
                'success': False,
                'error': None,
                'analysis': None,
            }

            if file.filename == '' or not allowed_file(file.filename):
                file_result['error'] = 'Invalid or empty file'
                results.append(file_result)
                continue

            file_path = None
            try:
                _, unique_filename = save_uploaded_file(file)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

                parsed_resume = parse_resume(file_path)
                parsed_resume['filename'] = file.filename
                parsed_resume['upload_time'] = datetime.utcnow().isoformat()
                parsed_resume['file_size'] = os.path.getsize(file_path)

                traditional_result = analyze_resume(parsed_resume, job_description)

                if ai_mode:
                    ai_result = ai_analyze_resume(parsed_resume, job_description)
                    merged = merge_ai_with_traditional(traditional_result, ai_result)
                    analysis = merged
                else:
                    analysis = traditional_result

                file_result['success'] = True
                file_result['analysis'] = analysis
                file_result['overall_score'] = analysis.get('overall_score')
            except Exception as exc:
                file_result['error'] = str(exc)
            finally:
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)

            results.append(file_result)

        passed = sum(1 for r in results if r['success'])
        failed = sum(1 for r in results if not r['success'])

        return jsonify({
            'success': True,
            'message': f'Batch analysis complete: {passed} succeeded, {failed} failed',
            'total': len(results),
            'passed': passed,
            'failed': failed,
            'results': results,
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'Batch analysis failed: {str(e)}'}), 500


@app.route('/generate-resume', methods=['POST'])
def generate_resume_endpoint():
    """
    Generate an improved, ATS-tailored resume from parsed data or analysis result + target JD.
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        job_description = data.get('job_description', '')
        target_role = data.get('target_role', '')

        # Can receive either raw resume_text or structured parsed_resume
        if 'parsed_resume' in data:
            parsed_resume = data['parsed_resume']
        elif 'resume_text' in data:
            resume_text = data['resume_text']
            parsed_resume = {
                'raw_text': resume_text,
                'contact_info': extract_contact_info(resume_text),
                'skills': extract_skills(resume_text),
                'education': extract_education(resume_text),
                'experience': extract_experience(resume_text),
                'projects': extract_projects(resume_text),
                'certifications': extract_certifications(resume_text)
            }
        else:
            return jsonify({'success': False, 'error': 'Must provide either parsed_resume or resume_text'}), 400

        generated_resume = generate_optimized_resume(parsed_resume, job_description, target_role)

        return jsonify({
            'success': True,
            'message': 'Optimized resume generated successfully',
            'data': generated_resume
        })

    except Exception as e:
        return jsonify({'success': False, 'error': f'Resume generation failed: {str(e)}'}), 500


@app.route('/export-resume', methods=['POST'])
def export_resume_endpoint():
    """
    Export resume data as a downloadable DOCX document.
    """
    try:
        if not request.is_json:
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400

        payload = request.get_json()
        resume_data = payload.get('resume_data')
        template = payload.get('template', 'modern')
        export_format = payload.get('format', 'docx').lower()

        if not resume_data:
            return jsonify({'success': False, 'error': 'resume_data is required'}), 400

        candidate_name = resume_data.get('contact', {}).get('name', 'Resume').replace(' ', '_')
        filename = f"{candidate_name}_ATS_Resume.{export_format}"

        if export_format == 'docx':
            buffer = generate_resume_docx(resume_data, template)
            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        elif export_format == 'json':
            json_buffer = io.BytesIO(jsonify(resume_data).get_data())
            return send_file(
                json_buffer,
                as_attachment=True,
                download_name=f"{candidate_name}_Resume.json",
                mimetype='application/json'
            )
        else:
            return jsonify({'success': False, 'error': f'Unsupported export format: {export_format}'}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': f'Export failed: {str(e)}'}), 500


@app.route('/api/skills', methods=['GET'])
def get_skills_database():
    """Get the skills database for frontend autocomplete."""
    from analyzer import TECHNICAL_SKILLS_DB, SOFT_SKILLS_DB
    return jsonify({
        'success': True,
        'data': {
            'technical': sorted(TECHNICAL_SKILLS_DB),
            'soft': sorted(SOFT_SKILLS_DB)
        }
    })


@app.route('/api/analyze-sample', methods=['GET'])
def analyze_sample():
    """Analyze a built-in sample resume for demonstration."""
    sample_text = """
John Smith
Email: john.smith@email.com | Phone: (555) 123-4567
LinkedIn: linkedin.com/in/johnsmith | GitHub: github.com/johnsmith

SUMMARY
Full-stack software engineer with 4 years of experience building scalable web applications
using Python, React, and AWS. Passionate about clean code, CI/CD, and agile development.

EDUCATION
Bachelor of Science in Computer Science
State University, 2020

SKILLS
Technical: Python, JavaScript, TypeScript, React, Node.js, Django, Flask, REST API,
PostgreSQL, MongoDB, Docker, Kubernetes, AWS, Git, GitHub, Linux, Agile, Scrum,
CI/CD, Redis, Elasticsearch, TDD
Soft Skills: Communication, Teamwork, Problem Solving, Leadership, Time Management

EXPERIENCE
Software Engineer | Tech Solutions Inc. | Jan 2022 – Present
- Developed and maintained 3 microservices using Python and Flask, reducing latency by 40%
- Built React dashboards serving 50,000+ daily active users
- Led migration from monolith to Docker/Kubernetes architecture, improving deployment speed by 60%
- Implemented CI/CD pipelines using GitHub Actions

Junior Developer | StartupXYZ | Jun 2020 – Dec 2021
- Built RESTful APIs with Django and PostgreSQL
- Optimized database queries, reducing load times by 35%
- Collaborated with design team to deliver responsive UIs using React

PROJECTS
E-Commerce Platform (github.com/johnsmith/ecommerce)
Full-stack e-commerce app using React, Node.js, MongoDB, and Stripe payments. 1000+ users.

Task Manager API
REST API built with FastAPI and PostgreSQL, 95% test coverage using pytest.

CERTIFICATIONS
AWS Certified Developer Associate – Amazon Web Services, 2023
Docker Certified Associate – Docker Inc., 2022
"""
    parsed = {
        'raw_text': sample_text,
        'contact_info': extract_contact_info(sample_text),
        'skills': extract_skills(sample_text),
        'education': extract_education(sample_text),
        'experience': extract_experience(sample_text),
        'projects': extract_projects(sample_text),
        'certifications': extract_certifications(sample_text),
        'word_count': len(sample_text.split()),
        'char_count': len(sample_text)
    }
    result = analyze_resume(parsed, "")
    return jsonify({
        'success': True,
        'message': 'Sample analysis complete',
        'data': result
    })


@app.route('/')
def serve_root():
    """Serve the main index page."""
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..'), 'index.html')


@app.route('/<path:filename>')
def serve_static_files(filename):
    """Serve static frontend files from the project root."""
    return send_from_directory(os.path.join(os.path.dirname(__file__), '..'), filename)


@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


@app.errorhandler(RequestEntityTooLarge)
def handle_large_file(e):
    return jsonify({'success': False, 'error': 'File too large (max 16MB)'}), 413


if __name__ == '__main__':
    print("=" * 60)
    print("  AI Resume Analyzer & Builder Backend v2.1")
    print("  Running at: http://localhost:5000")
    print("  Health Check: http://localhost:5000/health")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)