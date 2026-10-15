"""
Comprehensive End-to-End Test Suite for AI Resume Analyzer & Builder
Tests all 8 core API endpoints: health, skills, sample, analyze, match, generate, export DOCX, and error cases.
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
        with urllib.request.urlopen(req, timeout=20) as resp:
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
print("  AI RESUME ANALYZER & BUILDER -- END-TO-END TEST SUITE")
print("=" * 65)

# 1. Health check
print("\n[1] Testing GET /health")
h = run_test("Health Check", f"{BASE}/health")
if h:
    print(f"      Status: {h.get('status')}, Version: {h.get('version')}, Services: {h.get('services')}")

# 2. Skills endpoint
print("\n[2] Testing GET /api/skills")
sk = run_test("Skills Database", f"{BASE}/api/skills")
if sk:
    print(f"      Technical Skills: {len(sk.get('data', {}).get('technical', []))}")
    print(f"      Soft Skills: {len(sk.get('data', {}).get('soft', []))}")

# 3. Analyze Sample
print("\n[3] Testing GET /api/analyze-sample")
smp = run_test("Built-in Sample Analysis", f"{BASE}/api/analyze-sample")
if smp:
    d = smp.get('data', {})
    print(f"      Overall Score: {d.get('overall_score')}, ATS: {d.get('ats_score')}, Content: {d.get('content_score')}")
    print(f"      Detected Tech Skills: {len((d.get('skills_detected') or {}).get('technical', []))}")

# 4. Analyze Resume with JD
print("\n[4] Testing POST /analyze-resume (with Job Description)")
raw_sample_resume = """
Jane Doe
Email: jane.doe@example.com | Phone: (555) 987-6543
LinkedIn: linkedin.com/in/janedoe | GitHub: github.com/janedoe

PROFESSIONAL SUMMARY
Senior Software Developer with 5 years of experience in Python, Django, React, and cloud architecture.

SKILLS
Python, JavaScript, TypeScript, React, Django, Flask, PostgreSQL, Docker, AWS, Git, CI/CD, Agile

EXPERIENCE
Senior Backend Engineer | CloudScale Inc. | 2021 - Present
- Architected REST APIs and microservices using Python and Django
- Managed Docker and Kubernetes deployments on AWS
- Improved API response latency by 40% through database indexing

Software Engineer | AppVenture | 2019 - 2021
- Developed frontend user interfaces using React and Redux
- Collaborated with product team in bi-weekly agile sprints

EDUCATION
B.S. in Computer Science, Stanford University, 2019

PROJECTS
E-Commerce Engine (github.com/janedoe/ecommerce)
Built scalable e-commerce backend handling 50k monthly transactions using Django and PostgreSQL.

CERTIFICATIONS
AWS Certified Solutions Architect Associate (2022)
"""

target_jd = """
We are looking for a Senior Python Developer with deep experience in Django, REST APIs, PostgreSQL, Docker, and AWS. React knowledge is highly desired.
"""

ar = run_test(
    "Analyze Resume + JD",
    f"{BASE}/analyze-resume",
    method="POST",
    payload={"resume_text": raw_sample_resume, "job_description": target_jd}
)
if ar:
    ad = ar.get('data', {})
    print(f"      Overall: {ad.get('overall_score')}, Job Match: {ad.get('job_match_score')}%")
    print(f"      Matching Skills: {ad.get('job_match', {}).get('matching_skills', [])}")

# 5. Generate Improved Resume
print("\n[5] Testing POST /generate-resume (ATS Optimization & Action Verbs)")
gr = run_test(
    "Generate Tailored Resume",
    f"{BASE}/generate-resume",
    method="POST",
    payload={
        "resume_text": raw_sample_resume,
        "job_description": target_jd,
        "target_role": "Senior Python Backend Engineer"
    }
)
if gr:
    gd = gr.get('data', {})
    print(f"      Candidate Name: {gd.get('contact', {}).get('name')}")
    print(f"      Generated Summary: {gd.get('summary')[:100]}...")
    print(f"      Structured Experience Entries: {len(gd.get('experience', []))}")
    print(f"      Action Verb Enhanced Bullets: {gd.get('experience', [{}])[0].get('bullets', [])[:1]}")
    print(f"      Prioritized Tech Skills: {gd.get('skills', {}).get('technical', [])[:6]}")

# 6. Export DOCX Document
print("\n[6] Testing POST /export-resume (DOCX Binary Generation)")
if gr and gr.get('data'):
    docx_bytes = run_test(
        "Export DOCX Document",
        f"{BASE}/export-resume",
        method="POST",
        payload={
            "resume_data": gr.get('data'),
            "template": "modern",
            "format": "docx"
        }
    )
    if docx_bytes and len(docx_bytes) > 500:
        print(f"      DOCX Generated Successfully! File Size: {len(docx_bytes)} bytes")
    else:
        print(f"      DOCX payload unexpected length")

# 7. Error Cases Validation
print("\n[7] Testing Error Handling: Empty Payload (400 Expected)")
run_test("No Text Provided (400 check)", f"{BASE}/analyze-resume", method="POST", payload={}, expect_code=400)

print("\n[8] Testing Error Handling: Invalid Export Payload (400 Expected)")
run_test("Empty Export Data (400 check)", f"{BASE}/export-resume", method="POST", payload={}, expect_code=400)

print("\n" + "=" * 65)
print(f"  TEST SUITE COMPLETE: {PASSED} Passed, {FAILED} Failed")
print("=" * 65)
