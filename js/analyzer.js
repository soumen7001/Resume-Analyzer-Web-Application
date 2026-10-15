/**
 * Resume Analyzer — Analyzer Page Script (analyzer.html)
 * Handles: file upload, drag-drop, job description input,
 *          API calls, localStorage save, navigation to results.
 */

(function () {
    'use strict';

    const API = window.RESUME_ANALYZER;
    const API_BASE_URL = API.API_BASE_URL;

    const ALLOWED_EXTENSIONS = ['pdf', 'docx', 'doc'];
    const MAX_FILE_SIZE = 16 * 1024 * 1024; // 16 MB

    let currentFile = null;

    // ==========================================
    // Utility: File Size Formatter
    // ==========================================
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // ==========================================
    // File Upload Handling
    // ==========================================
    function initFileUpload() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const browseBtn = document.getElementById('browseBtn');
        const removeFileBtn = document.getElementById('removeFileBtn');

        if (!dropZone || !fileInput) return;

        // Browse button
        if (browseBtn) {
            browseBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.click();
            });
        }

        // Click on drop zone (not on the remove button)
        dropZone.addEventListener('click', (e) => {
            if (removeFileBtn && (e.target === removeFileBtn || removeFileBtn.contains(e.target))) return;
            if (e.target === browseBtn || (browseBtn && browseBtn.contains(e.target))) return;
            fileInput.click();
        });

        // File input change
        fileInput.addEventListener('change', (e) => {
            if (e.target.files[0]) handleFileSelect(e.target.files[0]);
        });

        // Drag & Drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
        });
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) handleFileSelect(file);
        });

        // Remove file
        if (removeFileBtn) {
            removeFileBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                removeFile();
            });
        }
    }

    function handleFileSelect(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        if (!ALLOWED_EXTENSIONS.includes(ext)) {
            API.showNotification('❌ Invalid file type. Please upload a PDF or DOCX file.', 'error');
            return;
        }
        if (file.size > MAX_FILE_SIZE) {
            API.showNotification('❌ File is too large. Maximum size is 16 MB.', 'error');
            return;
        }
        currentFile = file;
        showFilePreview(file);
        API.showNotification('✅ File selected: ' + file.name, 'success');
    }

    function showFilePreview(file) {
        const dropZoneContent = document.getElementById('dropZoneContent');
        const filePreview = document.getElementById('filePreview');
        const fileNameEl = document.getElementById('fileName');
        const fileSizeEl = document.getElementById('fileSize');
        const fileTypeEl = document.getElementById('fileType');

        if (dropZoneContent) dropZoneContent.style.display = 'none';
        if (filePreview) filePreview.style.display = 'flex';
        if (fileNameEl) fileNameEl.textContent = file.name;
        if (fileSizeEl) fileSizeEl.textContent = formatFileSize(file.size);
        if (fileTypeEl) fileTypeEl.textContent = file.name.split('.').pop().toUpperCase();
    }

    function removeFile() {
        currentFile = null;
        const fileInput = document.getElementById('fileInput');
        const dropZoneContent = document.getElementById('dropZoneContent');
        const filePreview = document.getElementById('filePreview');

        if (fileInput) fileInput.value = '';
        if (dropZoneContent) dropZoneContent.style.display = 'flex';
        if (filePreview) filePreview.style.display = 'none';
        API.showNotification('File removed.', 'info');
    }

    // ==========================================
    // Job Description: character counter
    // ==========================================
    function initJDCounter() {
        const textarea = document.getElementById('jobDescription');
        const counter = document.getElementById('jdCharCount');
        if (!textarea || !counter) return;
        textarea.addEventListener('input', () => {
            counter.textContent = textarea.value.length.toLocaleString();
        });
    }

    // ==========================================
    // AI Mode Toggle
    // ==========================================
    let aiModeEnabled = false;

    async function checkAIAvailability() {
        const aiStatus = document.getElementById('aiStatus');
        if (!aiStatus) return;
        aiStatus.textContent = 'Checking AI availability...';
        aiStatus.className = 'ai-status checking';

        try {
            const res = await fetch(`${API_BASE_URL}/health`);
            if (!res.ok) throw new Error('Health check failed');
            const data = await res.json();
            if (data.services && data.services.ai_analyzer) {
                aiStatus.textContent = '✨ AI Ready';
                aiStatus.className = 'ai-status available';
            } else {
                aiStatus.textContent = 'AI unavailable (install google-generativeai)';
                aiStatus.className = 'ai-status unavailable';
                const toggle = document.getElementById('aiModeToggle');
                if (toggle) toggle.disabled = true;
            }
        } catch (_) {
            aiStatus.textContent = 'Backend offline';
            aiStatus.className = 'ai-status unavailable';
        }
    }

    function initAIModeToggle() {
        const toggle = document.getElementById('aiModeToggle');
        if (!toggle) return;
        toggle.addEventListener('change', () => {
            aiModeEnabled = toggle.checked;
        });
    }

    // ==========================================
    // Loading Steps
    // ==========================================
    const BASE_LOADING_STEPS = [
        { text: '📄 Extracting text from resume...', delay: 0 },
        { text: '🔍 Detecting skills & sections...', delay: 1200 },
        { text: '📊 Calculating ATS score...', delay: 2400 },
    ];

    const AI_LOADING_STEPS = [
        { text: '🤖 Running AI-powered deep analysis...', delay: 3000 },
        { text: '✨ Generating AI insights...', delay: 4500 },
        { text: '📝 Analyzing grammar & clarity...', delay: 5500 },
        { text: '🚀 Finalizing recommendations...', delay: 6500 },
    ];

    function animateLoadingSteps(hasJD, useAI) {
        const loadingText = document.getElementById('loadingText');
        const stepsToShow = hasJD ? BASE_LOADING_STEPS : BASE_LOADING_STEPS.slice(0, 3);
        const allSteps = useAI ? [...stepsToShow, ...AI_LOADING_STEPS] : stepsToShow;

        allSteps.forEach(({ text, delay }) => {
            setTimeout(() => {
                if (loadingText) loadingText.textContent = text;
            }, delay);
        });
    }

    // ==========================================
    // API Calls
    // ==========================================
    async function uploadAndParse(file) {
        const formData = new FormData();
        formData.append('resume', file);
        const res = await fetch(`${API_BASE_URL}/upload-resume`, { method: 'POST', body: formData });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `Upload failed (HTTP ${res.status})`);
        }
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Upload failed');
        return data.data;
    }

    async function analyzeResume(resumeText, jobDescription) {
        const res = await fetch(`${API_BASE_URL}/analyze-resume`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume_text: resumeText, job_description: jobDescription }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `Analysis failed (HTTP ${res.status})`);
        }
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Analysis failed');
        return data.data;
    }

    async function analyzeResumeWithAI(resumeText, jobDescription) {
        const res = await fetch(`${API_BASE_URL}/ai-analyze-resume`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ resume_text: resumeText, job_description: jobDescription }),
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `AI analysis failed (HTTP ${res.status})`);
        }
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'AI analysis failed');
        return data.data;
    }

    // ==========================================
    // Main Analysis Flow
    // ==========================================
    async function performAnalysis() {
        if (!currentFile) {
            API.showNotification('⚠️ Please select a resume file first.', 'error');
            return;
        }

        const jdEl = document.getElementById('jobDescription');
        const jobDescription = jdEl ? jdEl.value.trim() : '';
        const analyzeBtn = document.getElementById('analyzeBtn');
        const useAI = aiModeEnabled;

        try {
            if (analyzeBtn) { analyzeBtn.disabled = true; analyzeBtn.textContent = '⏳ Analyzing...'; }
            API.showLoading('📤 Uploading resume...');
            animateLoadingSteps(jobDescription.length > 0, useAI);

            // Step 1: Upload & parse
            const parsed = await uploadAndParse(currentFile);

            // Step 2: Analyze
            let analysis;
            if (useAI) {
                analysis = await analyzeResumeWithAI(parsed.raw_text, jobDescription);
            } else {
                analysis = await analyzeResume(parsed.raw_text, jobDescription);
            }

            // Step 3: Save to localStorage and navigate to results
            try {
                localStorage.setItem('resumeAnalysis', JSON.stringify({
                    result: analysis,
                    filename: currentFile.name,
                    timestamp: new Date().toISOString(),
                    hasJD: jobDescription.length > 0,
                    jobDescription: jobDescription,
                    aiMode: useAI,
                }));
            } catch (e) {
                console.warn('localStorage write failed:', e);
            }

            API.hideLoading();
            window.location.href = 'results.html';

        } catch (error) {
            API.hideLoading();
            API.showNotification('❌ ' + error.message, 'error');
            console.error('Analysis error:', error);
        } finally {
            if (analyzeBtn) { analyzeBtn.disabled = false; analyzeBtn.textContent = '🔍 Analyze Resume'; }
        }
    }

    // ==========================================
    // Try Sample Analysis (demo button)
    // ==========================================
    async function trySample() {
        const sampleBtn = document.getElementById('sampleBtn');
        try {
            if (sampleBtn) { sampleBtn.disabled = true; sampleBtn.textContent = '⏳ Loading...'; }
            API.showLoading('📋 Loading sample resume...');

            const res = await fetch(`${API_BASE_URL}/api/analyze-sample`);
            if (!res.ok) throw new Error('Sample analysis failed');
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Sample analysis failed');

            try {
                localStorage.setItem('resumeAnalysis', JSON.stringify({
                    result: data.data,
                    filename: 'sample_resume.pdf',
                    timestamp: new Date().toISOString(),
                    hasJD: false,
                    isSample: true,
                }));
            } catch (e) {
                console.warn('localStorage write failed:', e);
            }

            API.hideLoading();
            window.location.href = 'results.html';
        } catch (error) {
            API.hideLoading();
            API.showNotification('❌ ' + error.message, 'error');
        } finally {
            if (sampleBtn) { sampleBtn.disabled = false; sampleBtn.textContent = '📋 Try Sample Resume'; }
        }
    }

    // ==========================================
    // Auto-Analyze Toggle
    // ==========================================
    function initAutoAnalyzeToggle() {
        const toggle = document.getElementById('autoAnalyzeToggle');
        const status = document.getElementById('autoAnalyzeStatus');
        if (!toggle || !status) return;
        toggle.addEventListener('change', () => {
            const enabled = toggle.checked;
            status.textContent = enabled ? '⚡ Auto-analyze ON' : 'Manual mode';
            status.className = enabled ? 'ai-status available' : 'ai-status';
        });
    }

    // ==========================================
    // Batch Upload
    // ==========================================
    let batchFiles = [];

    function initBatchUpload() {
        const dropZone = document.getElementById('batchDropZone');
        const fileInput = document.getElementById('batchFileInput');
        const browseBtn = document.getElementById('browseBatchBtn');
        const batchAnalyzeBtn = document.getElementById('batchAnalyzeBtn');
        const clearBatchBtn = document.getElementById('clearBatchBtn');
        const fileCountEl = document.getElementById('batchFileCount');
        const toggleBatchBtn = document.getElementById('toggleBatchBtn');
        const batchSection = document.getElementById('batchSection');

        if (toggleBatchBtn && batchSection) {
            toggleBatchBtn.addEventListener('click', () => {
                const isHidden = batchSection.style.display === 'none';
                batchSection.style.display = isHidden ? 'block' : 'none';
                toggleBatchBtn.textContent = isHidden ? '📦 Hide Batch Mode' : '📦 Batch Mode';
            });
        }

        if (!dropZone || !fileInput) return;

        if (browseBtn) {
            browseBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                fileInput.click();
            });
        }

        dropZone.addEventListener('click', (e) => {
            if (browseBtn && (e.target === browseBtn || browseBtn.contains(e.target))) return;
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            handleBatchFiles(e.target.files);
            fileInput.value = '';
        });

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            handleBatchFiles(e.dataTransfer.files);
        });

        if (clearBatchBtn) {
            clearBatchBtn.addEventListener('click', () => {
                batchFiles = [];
                renderBatchFileList();
                updateBatchButton();
            });
        }

        if (batchAnalyzeBtn) {
            batchAnalyzeBtn.addEventListener('click', performBatchAnalysis);
        }
    }

    function handleBatchFiles(fileList) {
        const allowed = ['pdf', 'docx', 'doc'];
        const maxSize = 16 * 1024 * 1024;

        for (const file of fileList) {
            const ext = file.name.split('.').pop().toLowerCase();
            if (!allowed.includes(ext)) {
                API.showNotification('❌ Invalid file type: ' + file.name, 'error');
                continue;
            }
            if (file.size > maxSize) {
                API.showNotification('❌ File too large: ' + file.name, 'error');
                continue;
            }
            if (batchFiles.some(f => f.name === file.name && f.size === file.size)) {
                API.showNotification('⚠️ Duplicate file skipped: ' + file.name, 'info');
                continue;
            }
            batchFiles.push(file);
        }
        renderBatchFileList();
        updateBatchButton();
    }

    function renderBatchFileList() {
        const container = document.getElementById('batchFileList');
        if (!container) return;
        if (batchFiles.length === 0) {
            container.innerHTML = '';
            return;
        }
        container.innerHTML = batchFiles.map((file, idx) => `
            <div class="batch-file-item">
                <span class="name">📄 ${API.sanitize(file.name)}</span>
                <span class="size">${formatFileSize(file.size)}</span>
                <button class="remove" data-index="${idx}" type="button">✕</button>
            </div>
        `).join('');

        container.querySelectorAll('.remove').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const i = parseInt(e.currentTarget.dataset.index, 10);
                batchFiles.splice(i, 1);
                renderBatchFileList();
                updateBatchButton();
            });
        });
    }

    function updateBatchButton() {
        const countEl = document.getElementById('batchFileCount');
        const batchAnalyzeBtn = document.getElementById('batchAnalyzeBtn');
        if (countEl) countEl.textContent = String(batchFiles.length);
        if (batchAnalyzeBtn) batchAnalyzeBtn.disabled = batchFiles.length === 0;
    }

    async function uploadAndAnalyzeSingle(file, jobDescription, useAI) {
        const formData = new FormData();
        formData.append('resume', file);
        formData.append('job_description', jobDescription);
        formData.append('ai_mode', useAI ? 'true' : 'false');

        const res = await fetch(`${API_BASE_URL}/upload-and-analyze`, {
            method: 'POST',
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `Upload and analyze failed (HTTP ${res.status})`);
        }
        const data = await res.json();
        if (!data.success) throw new Error(data.error || 'Upload and analyze failed');
        return data.data;
    }

    async function performBatchAnalysis() {
        if (!batchFiles.length) {
            API.showNotification('⚠️ No files selected for batch analysis.', 'error');
            return;
        }

        const jdEl = document.getElementById('jobDescription');
        const jobDescription = jdEl ? jdEl.value.trim() : '';
        const aiModeToggle = document.getElementById('aiModeToggle');
        const useAI = aiModeToggle ? aiModeToggle.checked : false;
        const batchAnalyzeBtn = document.getElementById('batchAnalyzeBtn');

        try {
            if (batchAnalyzeBtn) {
                batchAnalyzeBtn.disabled = true;
                batchAnalyzeBtn.textContent = `⏳ Analyzing ${batchFiles.length}...`;
            }
            API.showLoading('📦 Uploading and analyzing batch...');

            const formData = new FormData();
            for (const file of batchFiles) {
                formData.append('resumes', file);
            }
            formData.append('job_description', jobDescription);
            formData.append('ai_mode', useAI ? 'true' : 'false');

            const res = await fetch(`${API_BASE_URL}/batch-analyze`, {
                method: 'POST',
                body: formData,
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `Batch analysis failed (HTTP ${res.status})`);
            }
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Batch analysis failed');

            const successful = data.results.filter(r => r.success);
            if (successful.length > 0) {
                localStorage.setItem('batchAnalysisResults', JSON.stringify({
                    results: data.results,
                    total: data.total,
                    passed: data.passed,
                    failed: data.failed,
                    timestamp: new Date().toISOString(),
                    aiMode: useAI,
                }));
            }

            API.hideLoading();
            API.showNotification(`✅ Batch complete: ${data.passed}/${data.total} analyzed`, 'success');

            if (successful.length === 1) {
                const single = successful[0];
                localStorage.setItem('resumeAnalysis', JSON.stringify({
                    result: single.analysis,
                    filename: single.filename,
                    timestamp: new Date().toISOString(),
                    hasJD: jobDescription.length > 0,
                    jobDescription: jobDescription,
                    aiMode: useAI,
                }));
                window.location.href = 'results.html';
            } else if (successful.length > 1) {
                window.location.href = 'batch_results.html';
            } else {
                API.showNotification('❌ All batch analyses failed.', 'error');
            }
        } catch (error) {
            API.hideLoading();
            API.showNotification('❌ ' + error.message, 'error');
            console.error('Batch analysis error:', error);
        } finally {
            if (batchAnalyzeBtn) {
                batchAnalyzeBtn.disabled = false;
                batchAnalyzeBtn.textContent = `🔍 Analyze All (${batchFiles.length})`;
            }
        }
    }

    // ==========================================
    // Init
    // ==========================================
    function init() {
        initFileUpload();
        initJDCounter();
        initAIModeToggle();
        initAutoAnalyzeToggle();
        initBatchUpload();
        checkAIAvailability();

        const analyzeBtn = document.getElementById('analyzeBtn');
        if (analyzeBtn) analyzeBtn.addEventListener('click', performAnalysis);

        const sampleBtn = document.getElementById('sampleBtn');
        if (sampleBtn) sampleBtn.addEventListener('click', trySample);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
