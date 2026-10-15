/**
 * Batch Analysis Results Page
 * Reads batch analysis data from localStorage and renders the results.
 */

(function () {
    'use strict';

    const API = window.RESUME_ANALYZER;
    const san = API.sanitize;

    function loadBatchData() {
        try {
            const raw = localStorage.getItem('batchAnalysisResults');
            if (!raw) return null;
            return JSON.parse(raw);
        } catch (e) {
            console.error('Failed to read batch analysis from localStorage:', e);
            return null;
        }
    }

    function getScoreColor(score) {
        if (score >= 80) return '#10b981';
        if (score >= 60) return '#3b82f6';
        if (score >= 40) return '#f59e0b';
        return '#ef4444';
    }

    function getScoreStatus(score) {
        if (score >= 80) return { label: 'Excellent', cls: 'status-excellent' };
        if (score >= 60) return { label: 'Good', cls: 'status-good' };
        if (score >= 40) return { label: 'Fair', cls: 'status-fair' };
        return { label: 'Needs Work', cls: 'status-poor' };
    }

    function renderBatchResults(data) {
        const container = document.getElementById('batchResults');
        const meta = document.getElementById('batchMeta');
        if (!container) return;

        if (meta) {
            meta.innerHTML = `
                <span class="meta-item">📊 ${san(String(data.total))} resumes analyzed</span>
                <span class="meta-item">✅ ${san(String(data.passed))} succeeded</span>
                <span class="meta-item">❌ ${san(String(data.failed))} failed</span>
                <span class="meta-item">🕐 ${new Date(data.timestamp || Date.now()).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>
            `;
        }

        const results = data.results || [];
        if (results.length === 0) {
            container.innerHTML = '<p class="empty-msg">No batch results available.</p>';
            return;
        }

        container.innerHTML = results.map((item, index) => {
            const analysis = item.analysis || {};
            const score = analysis.overall_score || 0;
            const color = getScoreColor(score);
            const status = getScoreStatus(score);

            return `
                <div class="batch-card">
                    <div class="batch-card-header">
                        <div class="batch-card-title">
                            <span class="batch-index">#${index + 1}</span>
                            <span class="batch-filename">${san(item.filename || 'Unknown')}</span>
                        </div>
                        <div class="batch-score" style="color:${color}">${score}/100</div>
                    </div>
                    <div class="batch-card-body">
                        ${item.success ? `
                            <div class="batch-score-row">
                                <div class="batch-stat">
                                    <div class="batch-stat-label">ATS Score</div>
                                    <div class="batch-stat-value" style="color:${getScoreColor(analysis.ats_score || 0)}">${analysis.ats_score || 0}/100</div>
                                </div>
                                <div class="batch-stat">
                                    <div class="batch-stat-label">Content</div>
                                    <div class="batch-stat-value" style="color:${getScoreColor(analysis.content_score || 0)}">${analysis.content_score || 0}/100</div>
                                </div>
                                <div class="batch-stat">
                                    <div class="batch-stat-label">Job Match</div>
                                    <div class="batch-stat-value" style="color:${getScoreColor(analysis.job_match_score || 0)}">${analysis.job_match_score || 0}%</div>
                                </div>
                            </div>
                            <div class="batch-skills">
                                <strong>Skills:</strong> ${(analysis.skills_detected?.technical || []).slice(0, 8).map(s => `<span class="skill-tag tag-technical">${san(s)}</span>`).join(' ') || 'None'}
                            </div>
                            <div class="batch-actions">
                                <button class="btn btn-sm btn-primary" onclick="viewSingleResult(${index})">📊 View Full Results</button>
                            </div>
                        ` : `
                            <div class="batch-error">❌ ${san(item.error || 'Analysis failed')}</div>
                        `}
                    </div>
                </div>
            `;
        }).join('');
    }

    window.viewSingleResult = function (index) {
        const raw = localStorage.getItem('batchAnalysisResults');
        if (!raw) return;
        try {
            const data = JSON.parse(raw);
            const item = data.results[index];
            if (!item || !item.success) return;
            localStorage.setItem('resumeAnalysis', JSON.stringify({
                result: item.analysis,
                filename: item.filename,
                timestamp: new Date().toISOString(),
                hasJD: false,
                aiMode: data.aiMode || false,
            }));
            window.location.href = 'results.html';
        } catch (e) {
            console.error('Failed to navigate to single result:', e);
        }
    };

    function init() {
        const data = loadBatchData();
        if (!data) {
            const noData = document.getElementById('noDataMessage');
            const results = document.getElementById('batchResults');
            if (noData) noData.style.display = 'block';
            if (results) results.style.display = 'none';
            return;
        }

        const noData = document.getElementById('noDataMessage');
        const results = document.getElementById('batchResults');
        if (noData) noData.style.display = 'none';
        if (results) results.style.display = 'block';

        renderBatchResults(data);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
