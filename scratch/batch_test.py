"""
Batch Analysis & Auto-Analyze Endpoint Test
Tests the new /upload-and-analyze and /batch-analyze endpoints.
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
    if payload and isinstance(payload, bytes):
        pass
    elif payload and isinstance(payload, dict):
        payload = json.dumps(payload).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    else:
        payload = None

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
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


MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R/Resources<<>>>>endobj\n"
    b"xref\n0 4\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"trailer<</Size 4/Root 1 0 R>>\n"
    b"startxref\n190\n%%EOF\n"
)

MINIMAL_DOCX = (
    b"PK\x03\x04\x14\x00\x00\x00\x08\x00\x00\x00!\x00\x00\x00word/document.xml"
    b"<?xml version=\"1.0\"?><document><body><p>Test resume content with skills: Python, Django, AWS</p></body></document>"
)


def make_multipart(files, fields=None):
    boundary = '----BatchTestBoundary'
    parts = []
    for item in files:
        name = item['name']
        filename = item['filename']
        content = item['content']
        parts.append(f'--{boundary}'.encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode())
        parts.append(b'Content-Type: application/octet-stream')
        parts.append(b'')
        parts.append(content if isinstance(content, bytes) else content.encode('utf-8'))
    if fields:
        for k, v in fields.items():
            parts.append(f'--{boundary}'.encode())
            parts.append(f'Content-Disposition: form-data; name="{k}"'.encode())
            parts.append(b'')
            parts.append(v.encode('utf-8') if isinstance(v, str) else v)
    parts.append(f'--{boundary}--'.encode())
    return b'\r\n'.join(parts), boundary


print("=" * 65)
print("  BATCH & AUTO-ANALYZE ENDPOINT TEST SUITE")
print("=" * 65)

jd = "Looking for Python Developer with Django, REST APIs, PostgreSQL, Docker, AWS."

# Test 1: /upload-and-analyze without JD
print("\n[1] POST /upload-and-analyze (single, no JD)")
body, boundary = make_multipart(
    [{'name': 'resume', 'filename': 'resume1.pdf', 'content': MINIMAL_PDF}],
    fields={'ai_mode': 'false'}
)
ua = run_test(
    "Upload + Analyze Single",
    BASE + '/upload-and-analyze',
    method='POST',
    payload=body,
    headers={'Content-Type': 'multipart/form-data; boundary=' + boundary}
)
if ua:
    d = ua.get('data', {})
    print(f"      Filename: {d.get('parsed_resume', {}).get('filename')}")
    print(f"      Overall: {d.get('analysis', {}).get('overall_score')}")

# Test 2: /upload-and-analyze with AI mode
print("\n[2] POST /upload-and-analyze (single, with AI)")
body, boundary = make_multipart(
    [{'name': 'resume', 'filename': 'resume2.pdf', 'content': MINIMAL_PDF + b"\nPython Django AWS"}],
    fields={'ai_mode': 'true'}
)
ua_ai = run_test(
    "Upload + Analyze with AI",
    BASE + '/upload-and-analyze',
    method='POST',
    payload=body,
    headers={'Content-Type': 'multipart/form-data; boundary=' + boundary}
)
if ua_ai:
    d = ua_ai.get('data', {})
    a = d.get('analysis', {})
    print(f"      Filename: {d.get('parsed_resume', {}).get('filename')}")
    print(f"      AI Overall: {a.get('ai_overall_score')}")
    print(f"      AI ATS: {a.get('ai_ats_score')}")
    print(f"      AI Enabled: {d.get('ai_enabled')}")

# Test 3: /batch-analyze multiple resumes
print("\n[3] POST /batch-analyze (multiple, no AI)")
body, boundary = make_multipart(
    [
        {'name': 'resumes', 'filename': 'resume_a.pdf', 'content': MINIMAL_PDF + b"\nPython React Docker"},
        {'name': 'resumes', 'filename': 'resume_b.pdf', 'content': MINIMAL_PDF + b"\nJava Spring MySQL"},
    ],
    fields={'ai_mode': 'false'}
)
batch = run_test(
    "Batch Analyze Multiple",
    BASE + '/batch-analyze',
    method='POST',
    payload=body,
    headers={'Content-Type': 'multipart/form-data; boundary=' + boundary}
)
if batch:
    print(f"      Total: {batch.get('total')}, Passed: {batch.get('passed')}, Failed: {batch.get('failed')}")
    for r in batch.get('results', []):
        status = 'PASS' if r.get('success') else 'FAIL'
        print(f"      [{status}] {r.get('filename')}: score={r.get('overall_score', 'N/A')}")

# Test 4: /batch-analyze with AI
print("\n[4] POST /batch-analyze (multiple, with AI)")
body, boundary = make_multipart(
    [
        {'name': 'resumes', 'filename': 'resume_a.pdf', 'content': MINIMAL_PDF + b"\nPython React Docker"},
        {'name': 'resumes', 'filename': 'resume_b.pdf', 'content': MINIMAL_PDF + b"\nJava Spring MySQL"},
    ],
    fields={'ai_mode': 'true'}
)
batch_ai = run_test(
    "Batch Analyze with AI",
    BASE + '/batch-analyze',
    method='POST',
    payload=body,
    headers={'Content-Type': 'multipart/form-data; boundary=' + boundary}
)
if batch_ai:
    print(f"      Total: {batch_ai.get('total')}, Passed: {batch_ai.get('passed')}, Failed: {batch_ai.get('failed')}")
    for r in batch_ai.get('results', []):
        status = 'PASS' if r.get('success') else 'FAIL'
        ai = r.get('analysis', {}).get('ai_overall_score', 'N/A')
        print(f"      [{status}] {r.get('filename')}: AI score={ai}")

# Test 5: Error case
print("\n[5] Error: no files (400 expected)")
run_test(
    "No files (400)",
    BASE + '/batch-analyze',
    method='POST',
    payload=b'',
    headers={'Content-Type': 'multipart/form-data; boundary=----empty'},
    expect_code=400
)

print("\n" + "=" * 65)
print(f"  TEST SUITE COMPLETE: {PASSED} Passed, {FAILED} Failed")
print("=" * 65)
