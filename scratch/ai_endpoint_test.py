"""
AI Analysis Endpoint Test
Tests the new /ai-analyze-resume endpoint with Google AI Studio integration.
"""

import json
import urllib.request
import urllib.error

BASE = 'http://localhost:5000'
PASSED = 0
FAILED = 0


def run_test(name, url, method='GET', payload=None, headers=None, expect_code=200):
    global PASSED, FAILED
    if headers is None:
        headers = {}
    if payload and isinstance(payload, dict):
        payload_bytes = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    elif payload and isinstance(payload, bytes):
        payload_bytes = payload
    else:
        payload_bytes = None

    try:
        req = urllib.request.Request(url, data=payload_bytes, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=90) as resp:
            status = resp.status
            content_type = resp.headers.get('Content-Type', '')
            data = resp.read()
            
            if status == expect_code:
                print(f"  [PASS] ({status}) {name}")
                PASSED += 1
                if 'application/json' in content_type:
                    return json.loads(data.decode('utf-8'))
                return data
            else:
                print(f"  [FAIL] ({status} != {expect_code}) {name}")
                FAILED += 1
                return None
    except urllib.error.HTTPError as e:
        if e.code == expect_code:
            print(f"  [PASS] ({e.code}) {name} (Expected Error Handler Verified)")
            PASSED += 1
            try:
                return json.loads(e.read().decode('utf-8'))
            except Exception:
                return None
        else:
            print(f"  [FAIL] ({e.code} != {expect_code}) {name}")
            FAILED += 1
            return None
    except Exception as ex:
        print(f"  [FAIL] {name}: {ex}")
        FAILED += 1
        return None


print("=" * 65)
print("  AI ANALYSIS ENDPOINT TEST SUITE")
print("=" * 65)

resume_text = """
Alex Johnson
alex.johnson@email.com | (555) 111-2222
LinkedIn: linkedin.com/in/alexjohnson | GitHub: github.com/alexjohnson

SUMMARY
Full-stack developer with 3 years of experience in Python, React, and AWS.

SKILLS
Python, JavaScript, React, Django, PostgreSQL, Docker, AWS, Git

EXPERIENCE
Full-Stack Developer | Tech Solutions Inc. | 2021 - Present
- Built REST APIs using Django and PostgreSQL
- Developed React frontend dashboards
- Deployed applications on AWS using Docker

Junior Developer | StartupXYZ | 2019 - 2021
- Assisted in backend development with Python
- Participated in code reviews and agile sprints

EDUCATION
B.S. Computer Science, State University, 2019

PROJECTS
Task Manager API
Built a REST API with FastAPI and PostgreSQL.

CERTIFICATIONS
AWS Certified Developer Associate (2023)
"""

jd_text = """
We are looking for a Senior Python Developer with experience in Django, REST APIs, 
PostgreSQL, Docker, and AWS. Knowledge of CI/CD and Agile methodologies is a plus.
"""

# Test 1: AI Analysis without JD
print("\n[1] Testing POST /ai-analyze-resume (without JD)")
ai_result = run_test(
    "AI Analysis without JD",
    f"{BASE}/ai-analyze-resume",
    method="POST",
    payload={"resume_text": resume_text}
)
if ai_result:
    data = ai_result.get('data', {})
    print(f"      AI Enabled: {data.get('ai_enabled')}")
    print(f"      AI Provider: {data.get('ai_provider')}")
    print(f"      AI Model: {data.get('ai_model')}")
    print(f"      AI Overall Score: {data.get('ai_overall_score')}")
    print(f"      AI ATS Score: {data.get('ai_ats_score')}")
    print(f"      Grammar Corrections: {len(data.get('ai_grammar_corrections', []))}")
    print(f"      Clarity Improvements: {len(data.get('ai_clarity_improvements', []))}")
    print(f"      Action Verb Suggestions: {len(data.get('ai_action_verb_suggestions', []))}")
    print(f"      AI Strengths: {len(data.get('ai_strengths', []))}")
    print(f"      AI Improvements: {len(data.get('ai_improvements', []))}")
    print(f"      AI Recommendations: {len(data.get('ai_recommendations', []))}")
    print(f"      Has AI Error: {'ai_error' in data}")
    
    # Verify traditional scores are also present
    print(f"      Traditional Overall: {data.get('overall_score')}")
    print(f"      Traditional ATS: {data.get('ats_score')}")
    print(f"      Job Match Score: {data.get('job_match_score')}")

# Test 2: AI Analysis with JD
print("\n[2] Testing POST /ai-analyze-resume (with JD)")
ai_jd_result = run_test(
    "AI Analysis with JD",
    f"{BASE}/ai-analyze-resume",
    method="POST",
    payload={"resume_text": resume_text, "job_description": jd_text}
)
if ai_jd_result:
    data = ai_jd_result.get('data', {})
    print(f"      AI Enabled: {data.get('ai_enabled')}")
    print(f"      AI Overall Score: {data.get('ai_overall_score')}")
    print(f"      AI ATS Score: {data.get('ai_ats_score')}")
    print(f"      JD Alignment Present: {'ai_jd_alignment' in data}")
    if 'ai_jd_alignment' in data:
        jd_align = data.get('ai_jd_alignment', {})
        print(f"      JD Match Score: {jd_align.get('match_score')}")
        print(f"      Matching Points: {len(jd_align.get('matching_points', []))}")
        print(f"      Missing Points: {len(jd_align.get('missing_points', []))}")
        print(f"      Keyword Suggestions: {len(jd_align.get('keyword_suggestions', []))}")
    print(f"      Traditional Job Match: {data.get('job_match_score')}%")

# Test 3: Error case - no resume text
print("\n[3] Testing Error Handling: Empty resume_text (400 Expected)")
run_test(
    "Empty Resume Text (400 check)",
    f"{BASE}/ai-analyze-resume",
    method="POST",
    payload={},
    expect_code=400
)

# Test 4: Verify AI fields structure
print("\n[4] Verifying AI Response Structure")
if ai_result:
    data = ai_result.get('data', {})
    required_fields = [
        'ai_overall_score', 'ai_ats_score', 'ai_grammar_corrections',
        'ai_clarity_improvements', 'ai_action_verb_suggestions',
        'ai_quantified_achievements_feedback', 'ai_structure_feedback',
        'ai_strengths', 'ai_improvements', 'ai_recommendations',
        'ai_enabled', 'ai_provider', 'ai_model'
    ]
    missing = [f for f in required_fields if f not in data]
    if missing:
        print(f"  [FAIL] Missing fields: {missing}")
        FAILED += 1
    else:
        print(f"  [PASS] All required AI fields present")
        PASSED += 1

print("\n" + "=" * 65)
print(f"  TEST SUITE COMPLETE: {PASSED} Passed, {FAILED} Failed")
print("=" * 65)
