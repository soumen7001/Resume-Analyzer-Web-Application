/**
 * Resume Analyzer — Results Page Script (results.html)
 * Reads analysis data from localStorage and renders the full results dashboard.
 */

(function () {
    'use strict';

    const API = window.RESUME_ANALYZER;
    const san = API.sanitize;

    // ==========================================
    // Load Data from localStorage
    // ==========================================
    function loadData() {
        try {
            const raw = localStorage.getItem('resumeAnalysis');
            if (!raw) return null;
            return JSON.parse(raw);
        } catch (e) {
            console.error('Failed to read analysis from localStorage:', e);
            return null;
        }
    }

    // ==========================================
    // Animated Score Circle (SVG)
    // ==========================================
    function createScoreCircle(score, size = 130, strokeWidth = 11) {
        const radius = (size - strokeWidth) / 2;
        const circumference = radius * 2 * Math.PI;
        const color = API.getScoreColor(score);
        const id = 'circle_' + Math.random().toString(36).substr(2, 6);

        // Start with offset = full (empty) → animate to actual value via JS
        return `
            <div class="score-circle" data-score="${score}" data-circum="${circumference.toFixed(2)}" data-id="${id}"
                 style="width:${size}px;height:${size}px;position:relative;">
                <svg width="${size}" height="${size}" viewBox="0 0 ${size} ${size}" style="transform:rotate(-90deg)">
                    <circle cx="${size / 2}" cy="${size / 2}" r="${radius}"
                        fill="none" stroke="#e5e7eb" stroke-width="${strokeWidth}" />
                    <circle id="${id}" cx="${size / 2}" cy="${size / 2}" r="${radius}"
                        fill="none" stroke="${color}" stroke-width="${strokeWidth}"
                        stroke-linecap="round"
                        stroke-dasharray="${circumference.toFixed(2)}"
                        stroke-dashoffset="${circumference.toFixed(2)}"
                        style="transition: stroke-dashoffset 1.2s cubic-bezier(.4,0,.2,1);" />
                </svg>
                <div class="score-circle-inner" style="position:absolute;top:0;left:0;width:100%;height:100%;
                    display:flex;flex-direction:column;align-items:center;justify-content:center;">
                    <span class="score-number" style="color:${color};font-size:2rem;font-weight:800;line-height:1;"
                        data-target="${score}">0</span>
                    <span style="font-size:0.7rem;color:#6b7280;font-weight:500;letter-spacing:0.05em;">/ 100</span>
                </div>
            </div>`;
    }

    function animateScores() {
        // Animate SVG stroke
        document.querySelectorAll('.score-circle[data-score]').forEach(el => {
            const score = parseInt(el.dataset.score, 10);
            const circum = parseFloat(el.dataset.circum);
            const id = el.dataset.id;
            const circleEl = document.getElementById(id);
            if (circleEl) {
                requestAnimationFrame(() => {
                    const offset = circum - (score / 100) * circum;
                    circleEl.style.strokeDashoffset = offset.toFixed(2);
                });
            }
        });

        // Animate number counters
        document.querySelectorAll('[data-target]').forEach(el => {
            const target = parseInt(el.dataset.target, 10);
            const duration = 1200;
            const start = performance.now();
            function step(now) {
                const progress = Math.min((now - start) / duration, 1);
                const eased = 1 - Math.pow(1 - progress, 3);
                el.textContent = Math.round(eased * target);
                if (progress < 1) requestAnimationFrame(step);
            }
            requestAnimationFrame(step);
        });

        // Animate progress bars
        document.querySelectorAll('.progress-bar-fill[data-width]').forEach(el => {
            const width = el.dataset.width;
            setTimeout(() => { el.style.width = width + '%'; }, 300);
        });
    }

    // ==========================================
    // Tab System
    // ==========================================
    function initTabs() {
        const tabs = document.querySelectorAll('.tab-btn');
        const panels = document.querySelectorAll('.tab-panel');
        tabs.forEach(tab => {
            tab.addEventListener('click', () => {
                tabs.forEach(t => t.classList.remove('active'));
                panels.forEach(p => p.classList.remove('active'));
                tab.classList.add('active');
                const panel = document.getElementById(tab.dataset.tab);
                if (panel) panel.classList.add('active');
            });
        });
    }

    // ==========================================
    // AI Insights Tab Renderers
    // ==========================================

    function renderAITab(result, stored) {
        const aiTabBtn = document.getElementById('aiTabBtn');
        const aiDisabledMsg = document.getElementById('aiDisabledMsg');
        const aiContent = document.getElementById('aiContent');

        if (!aiTabBtn) return;

        const hasAI = stored && stored.aiMode && result.ai_enabled;

        if (hasAI) {
            aiTabBtn.style.display = 'inline-flex';
            if (aiDisabledMsg) aiDisabledMsg.style.display = 'none';
            if (aiContent) aiContent.style.display = 'block';
        } else {
            aiTabBtn.style.display = 'none';
            if (aiDisabledMsg) aiDisabledMsg.style.display = 'block';
            if (aiContent) aiContent.style.display = 'none';
            return;
        }

        renderAIScores(result);
        renderAIStrengths(result);
        renderAIImprovements(result);
        renderAIGrammar(result);
        renderAIClarity(result);
        renderAIActionVerbs(result);
        renderAIAchievements(result);
        renderAIStructure(result);
        renderAIRecommendations(result);
    }

    function renderAIScores(result) {
        const overallEl = document.getElementById('aiOverallScore');
        const atsEl = document.getElementById('aiATSScore');

        const overallScore = result.ai_overall_score || 0;
        const atsScore = result.ai_ats_score || 0;

        const getScoreHTML = (score, label) => {
            const color = API.getScoreColor(score);
            return `
                <div style="text-align:center;padding:0.5rem;">
                    <span class="ai-score-value" style="color:${color}">${score}</span>
                    <span class="ai-score-label">${san(label)}</span>
                </div>`;
        };

        if (overallEl) overallEl.innerHTML = getScoreHTML(overallScore, 'AI Overall Score (out of 100)');
        if (atsEl) atsEl.innerHTML = getScoreHTML(atsScore, 'AI ATS Score (out of 100)');
    }

    function renderAIStrengths(result) {
        const strengths = result.ai_strengths || [];
        renderList('aiStrengthsList', strengths, {
            emptyMsg: 'No AI-identified strengths.',
            itemClass: 'ai-improvement-item',
            icon: '✅',
            iconClass: 'icon-success',
            textKey: 'text'
        });
    }

    function renderAIImprovements(result) {
        const improvements = result.ai_improvements || [];
        renderList('aiImprovementsList', improvements, {
            emptyMsg: 'No AI-suggested improvements.',
            itemClass: 'ai-improvement-item',
            icon: '⚠️',
            iconClass: 'icon-warning',
            textKey: 'text'
        });
    }

    function renderAIGrammar(result) {
        const container = document.getElementById('aiGrammarList');
        if (!container) return;
        const corrections = result.ai_grammar_corrections || [];
        if (!corrections.length) {
            container.innerHTML = '<p class="empty-msg">No grammar corrections needed — great work!</p>';
            return;
        }
        container.innerHTML = corrections.map(c => `
            <div class="ai-correction-item">
                <div class="original">${san(c.original || '')}</div>
                <div class="corrected">→ ${san(c.corrected || '')}</div>
                ${c.reason ? `<div class="reason">${san(c.reason)}</div>` : ''}
            </div>
        `).join('');
    }

    function renderAIClarity(result) {
        const container = document.getElementById('aiClarityList');
        if (!container) return;
        const improvements = result.ai_clarity_improvements || [];
        if (!improvements.length) {
            container.innerHTML = '<p class="empty-msg">No clarity issues detected.</p>';
            return;
        }
        container.innerHTML = improvements.map(c => `
            <div class="ai-correction-item" style="border-left-color:var(--info);">
                <div class="original">${san(c.original || '')}</div>
                <div class="corrected" style="color:var(--info);">→ ${san(c.improved || '')}</div>
                ${c.reason ? `<div class="reason">${san(c.reason)}</div>` : ''}
            </div>
        `).join('');
    }

    function renderAIActionVerbs(result) {
        const container = document.getElementById('aiActionVerbsList');
        if (!container) return;
        const suggestions = result.ai_action_verb_suggestions || [];
        if (!suggestions.length) {
            container.innerHTML = '<p class="empty-msg">No action verb suggestions.</p>';
            return;
        }
        container.innerHTML = suggestions.map(s => `
            <div class="ai-improvement-item">
                <span class="icon">💪</span>
                <div class="text">
                    <span style="color:var(--gray-500);font-size:0.85rem;">${san(s.original_phrase || '')}</span>
                    <br>
                    <span style="color:var(--primary);font-weight:600;">→ ${san(s.suggested_phrase || '')}</span>
                </div>
            </div>
        `).join('');
    }

    function renderAIAchievements(result) {
        const container = document.getElementById('aiAchievementsFeedback');
        if (!container) return;
        const feedback = result.ai_quantified_achievements_feedback || '';
        if (!feedback) {
            container.innerHTML = '<p class="empty-msg">No feedback available.</p>';
            return;
        }
        container.innerHTML = `<div class="ai-feedback-block">${san(feedback)}</div>`;
    }

    function renderAIStructure(result) {
        const container = document.getElementById('aiStructureList');
        if (!container) return;
        const items = result.ai_structure_feedback || [];
        if (!items.length) {
            container.innerHTML = '<p class="empty-msg">No structure feedback.</p>';
            return;
        }
        container.innerHTML = items.map(item => `
            <div class="ai-improvement-item">
                <span class="icon">🏗️</span>
                <div class="text">${san(item)}</div>
            </div>
        `).join('');
    }

    function renderAIRecommendations(result) {
        const container = document.getElementById('aiRecommendationsList');
        if (!container) return;
        const recommendations = result.ai_recommendations || [];
        if (!recommendations.length) {
            container.innerHTML = '<p class="empty-msg">No recommendations at this time.</p>';
            return;
        }
        container.innerHTML = recommendations.map((r, i) => `
            <div class="suggestion-item">
                <div class="suggestion-number">${i + 1}</div>
                <div class="suggestion-text">${san(r)}</div>
            </div>
        `).join('');
    }

    // ==========================================
    // Section Renderers
    // ==========================================

    function renderOverview(data, filename) {
        const overall = data.overall_score || 0;
        const ats = data.ats_score || 0;
        const content = data.content_score || 0;
        const jobMatch = data.job_match_score;
        const wordCount = data.word_count || 0;

        // Score cards
        const scoreCardsEl = document.getElementById('scoreCards');
        if (scoreCardsEl) {
            const jobMatchCard = (jobMatch !== null && jobMatch !== undefined) ? `
                <div class="score-card">
                    ${createScoreCircle(jobMatch)}
                    <div class="score-card-title">Job Match</div>
                    <div class="score-card-status ${API.getScoreStatus(jobMatch).cls}">${API.getScoreStatus(jobMatch).label}</div>
                </div>` : '';

            scoreCardsEl.innerHTML = `
                <div class="score-card featured">
                    ${createScoreCircle(overall, 150, 12)}
                    <div class="score-card-title">Overall Score</div>
                    <div class="score-card-status ${API.getScoreStatus(overall).cls}">${API.getScoreStatus(overall).label}</div>
                </div>
                <div class="score-card">
                    ${createScoreCircle(ats)}
                    <div class="score-card-title">ATS Compatibility</div>
                    <div class="score-card-status ${API.getScoreStatus(ats).cls}">${API.getScoreStatus(ats).label}</div>
                </div>
                <div class="score-card">
                    ${createScoreCircle(content)}
                    <div class="score-card-title">Content Quality</div>
                    <div class="score-card-status ${API.getScoreStatus(content).cls}">${API.getScoreStatus(content).label}</div>
                </div>
                ${jobMatchCard}`;
        }

        // Resume meta info
        const metaEl = document.getElementById('resumeMeta');
        if (metaEl) {
            metaEl.innerHTML = `
                <span class="meta-item">📄 ${san(filename || 'Unknown file')}</span>
                <span class="meta-item">📝 ${wordCount.toLocaleString()} words</span>
                <span class="meta-item">🕐 ${new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span>`;
        }

        // ATS Breakdown
        renderATSBreakdown(data);

        // Strengths
        renderList('strengthsList', data.strengths || [], {
            emptyMsg: 'No specific strengths identified yet.',
            itemClass: 'strength-item',
            icon: '✓',
            iconClass: 'icon-success'
        });

        // Improvements
        renderList('improvementsList', data.improvements || [], {
            emptyMsg: 'No major improvements needed — great work!',
            itemClass: 'improvement-item',
            icon: '!',
            iconClass: 'icon-warning'
        });
    }

    function renderATSBreakdown(data) {
        const container = document.getElementById('atsBreakdown');
        if (!container) return;
        const breakdown = data.ats_breakdown || {};
        const labels = {
            contact_info: { label: 'Contact Info', max: 15 },
            skills: { label: 'Skills', max: 25 },
            experience: { label: 'Experience', max: 25 },
            education: { label: 'Education', max: 15 },
            projects: { label: 'Projects', max: 10 },
            certifications: { label: 'Certifications', max: 10 },
            formatting_penalty: { label: 'Formatting', max: 0 },
        };

        let html = '';
        for (const [key, value] of Object.entries(breakdown)) {
            const meta = labels[key] || { label: key.replace(/_/g, ' '), max: 10 };
            const score = Math.max(0, value);
            const max = meta.max || 10;
            const pct = max > 0 ? Math.min(100, Math.round((score / max) * 100)) : 0;
            const color = pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#ef4444';

            html += `
                <div class="ats-item">
                    <div class="ats-item-header">
                        <span class="ats-item-label">${san(meta.label)}</span>
                        <span class="ats-item-score" style="color:${color}">${score}${max > 0 ? '/' + max : ''}</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" data-width="${pct}"
                             style="background:${color};width:0%;transition:width 0.9s ease;"></div>
                    </div>
                </div>`;
        }

        const feedback = data.ats_feedback || [];
        if (feedback.length > 0) {
            html += `<div class="ats-feedback-list">`;
            feedback.forEach(f => {
                html += `<div class="ats-feedback-item">💡 ${san(f)}</div>`;
            });
            html += `</div>`;
        }

        container.innerHTML = html || '<p class="empty-msg">No breakdown available.</p>';
    }

    function renderSkillsTab(data) {
        const skills = data.skills_detected || {};
        const technical = skills.technical || [];
        const soft = skills.soft || [];
        const missing = data.missing_skills || [];

        renderSkillTags('technicalSkillsList', technical, 'tag-technical', 'No technical skills detected.');
        renderSkillTags('softSkillsList', soft, 'tag-soft', 'No soft skills detected.');
        renderSkillTags('missingSkillsList', missing.slice(0, 15), 'tag-missing', 'None identified.');

        // Keyword clouds
        const kwAnalysis = data.keyword_analysis || {};
        renderKeywordTags('resumeKeywordsList', kwAnalysis.resume_keywords || [], 'No keywords extracted.');
    }

    function renderJobMatchTab(data) {
        const section = document.getElementById('jobMatchTab');
        const noJD = document.getElementById('noJDMessage');

        if (!data.job_match) {
            if (section) section.style.display = 'none';
            if (noJD) noJD.style.display = 'block';
            return;
        }
        if (noJD) noJD.style.display = 'none';

        const m = data.job_match;
        setTextContent('matchPct', (m.match_percentage || 0) + '%');
        setTextContent('tfidfScore', (m.tfidf_similarity || 0) + '%');
        setTextContent('kwOverlap', (m.keyword_overlap_score || 0) + '%');

        renderSkillTags('matchingSkillsList', m.matching_skills || [], 'tag-match', 'No matching skills found.');
        renderSkillTags('missingSkillsListJD', m.missing_skills || [], 'tag-missing', 'No missing skills — great!');
        renderKeywordTags('matchingKWList', m.matching_keywords || [], 'No matching keywords.');
        renderKeywordTags('missingKWList', m.missing_keywords || [], 'None missing — great!');
    }

    function renderDetailsTab(data) {
        renderContactInfo(data.contact_info || {});
        renderEducation(data.education || []);
        renderExperience(data.experience || []);
        renderProjects(data.projects || []);
        renderCertifications(data.certifications || []);
    }

    function renderSuggestionsTab(data) {
        const container = document.getElementById('suggestionsList');
        if (!container) return;
        const suggestions = data.suggestions || [];
        if (suggestions.length === 0) {
            container.innerHTML = '<p class="empty-msg">No specific suggestions at this time.</p>';
            return;
        }
        container.innerHTML = suggestions.map((s, i) => `
            <div class="suggestion-item">
                <div class="suggestion-number">${i + 1}</div>
                <div class="suggestion-text">${san(s)}</div>
            </div>`).join('');
    }

    // ==========================================
    // Helper Renderers
    // ==========================================

    function renderList(id, items, opts) {
        const el = document.getElementById(id);
        if (!el) return;
        if (!items || items.length === 0) {
            el.innerHTML = `<p class="empty-msg">${opts.emptyMsg}</p>`;
            return;
        }
        el.innerHTML = items.map(item => `
            <div class="${opts.itemClass || 'list-item'}">
                <div class="list-item-icon ${opts.iconClass || ''}">${opts.icon || '•'}</div>
                <div class="list-item-text">${san(item)}</div>
            </div>`).join('');
    }

    function renderSkillTags(id, items, tagClass, emptyMsg) {
        const el = document.getElementById(id);
        if (!el) return;
        if (!items || items.length === 0) {
            el.innerHTML = `<p class="empty-msg">${emptyMsg}</p>`;
            return;
        }
        el.innerHTML = items.map(s => `<span class="skill-tag ${tagClass}">${san(s)}</span>`).join('');
    }

    function renderKeywordTags(id, items, emptyMsg) {
        const el = document.getElementById(id);
        if (!el) return;
        if (!items || items.length === 0) {
            el.innerHTML = `<p class="empty-msg">${emptyMsg}</p>`;
            return;
        }
        el.innerHTML = items.map(k => `<span class="keyword-tag">${san(k)}</span>`).join('');
    }

    function renderContactInfo(contact) {
        const el = document.getElementById('contactInfoList');
        if (!el) return;
        const fields = [
            { key: 'email', label: 'Email', icon: '📧', link: v => `mailto:${v}` },
            { key: 'phone', label: 'Phone', icon: '📱', link: v => `tel:${v}` },
            { key: 'linkedin', label: 'LinkedIn', icon: '💼', link: v => `https://linkedin.com/in/${v}` },
            { key: 'github', label: 'GitHub', icon: '🐙', link: v => `https://github.com/${v}` },
            { key: 'website', label: 'Website', icon: '🌐', link: v => v.startsWith('http') ? v : `https://${v}` },
        ];
        const items = fields.filter(f => contact[f.key]);
        if (items.length === 0) {
            el.innerHTML = '<p class="empty-msg">No contact information detected.</p>';
            return;
        }
        el.innerHTML = items.map(f => {
            const val = contact[f.key];
            return `
                <div class="contact-item">
                    <div class="contact-icon">${f.icon}</div>
                    <div>
                        <div class="contact-label">${f.label}</div>
                        <a class="contact-value" href="${f.link(val)}" target="_blank" rel="noopener">${san(val)}</a>
                    </div>
                </div>`;
        }).join('');
    }

    function renderEducation(items) {
        renderList('educationList', items.map(e => e.raw || ''), {
            emptyMsg: 'No education information detected.',
            itemClass: 'detail-item',
            icon: '🎓', iconClass: 'icon-success'
        });
    }

    function renderExperience(items) {
        renderList('experienceList', items.slice(0, 12).map(e => e.raw || ''), {
            emptyMsg: 'No experience information detected.',
            itemClass: 'detail-item',
            icon: '💼', iconClass: 'icon-primary'
        });
    }

    function renderProjects(items) {
        renderList('projectsList', items.slice(0, 12).map(p => p.raw || ''), {
            emptyMsg: 'No projects detected.',
            itemClass: 'detail-item',
            icon: '🚀', iconClass: 'icon-accent'
        });
    }

    function renderCertifications(items) {
        const texts = items.slice(0, 12).map(c => typeof c === 'string' ? c : (c.raw || ''));
        renderList('certificationsList', texts, {
            emptyMsg: 'No certifications detected.',
            itemClass: 'detail-item',
            icon: '🏆', iconClass: 'icon-warning'
        });
    }

    function setTextContent(id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text;
    }

    // ==========================================
    // Download Report
    // ==========================================
    function downloadReport(data, filename) {
        const lines = [];
        lines.push('=' .repeat(60));
        lines.push('          AI RESUME ANALYZER — ANALYSIS REPORT');
        lines.push('=' .repeat(60));
        lines.push(`File: ${filename}`);
        lines.push(`Date: ${new Date().toLocaleString()}`);
        lines.push('');
        lines.push(`SCORES`);
        lines.push(`  Overall Score    : ${data.overall_score}/100`);
        lines.push(`  ATS Compatibility: ${data.ats_score}/100`);
        lines.push(`  Content Quality  : ${data.content_score}/100`);
        if (data.job_match_score !== null && data.job_match_score !== undefined) {
            lines.push(`  Job Match        : ${data.job_match_score}/100`);
        }
        lines.push('');
        lines.push('TECHNICAL SKILLS DETECTED');
        lines.push('  ' + ((data.skills_detected || {}).technical || []).join(', ') || 'None');
        lines.push('');
        lines.push('SOFT SKILLS DETECTED');
        lines.push('  ' + ((data.skills_detected || {}).soft || []).join(', ') || 'None');
        lines.push('');
        lines.push('STRENGTHS');
        (data.strengths || []).forEach((s, i) => lines.push(`  ${i+1}. ${s}`));
        lines.push('');
        lines.push('AREAS FOR IMPROVEMENT');
        (data.improvements || []).forEach((s, i) => lines.push(`  ${i+1}. ${s}`));
        lines.push('');
        lines.push('SUGGESTIONS');
        (data.suggestions || []).forEach((s, i) => lines.push(`  ${i+1}. ${s}`));
        lines.push('');
        lines.push('=' .repeat(60));
        lines.push('Generated by AI Resume Analyzer');

        const blob = new Blob([lines.join('\n')], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'resume_analysis_report.txt';
        a.click();
        URL.revokeObjectURL(url);
        API.showNotification('✅ Report downloaded!', 'success');
    }

    // ==========================================
    // Init
    // ==========================================
    function init() {
        const stored = loadData();

        if (!stored || !stored.result) {
            // No data — redirect back to analyzer
            const noData = document.getElementById('noDataMessage');
            const resultsContent = document.getElementById('resultsContent');
            if (noData) noData.style.display = 'block';
            if (resultsContent) resultsContent.style.display = 'none';
            return;
        }

        const { result, filename, isSample } = stored;

        // Show sample badge if applicable
        const sampleBadge = document.getElementById('sampleBadge');
        if (sampleBadge && isSample) sampleBadge.style.display = 'inline-flex';

        // Render all sections
        renderOverview(result, filename);
        renderSkillsTab(result);
        renderJobMatchTab(result);
        renderDetailsTab(result);
        renderAITab(result, stored);
        renderSuggestionsTab(result);

        // Init tabs
        initTabs();

        // Animate after a short delay (allow DOM paint)
        setTimeout(animateScores, 150);

        // Download button
        const downloadBtn = document.getElementById('downloadReportBtn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', () => downloadReport(result, filename));
        }

        // Generate Improved Resume button
        const genBtn = document.getElementById('generateResumeBtn');
        if (genBtn) {
            genBtn.addEventListener('click', async () => {
                try {
                    genBtn.disabled = true;
                    genBtn.textContent = '⏳ Generating...';
                    API.showLoading('✨ Optimizing your resume with AI action verbs...');
                    
                    const res = await fetch(`${API.API_BASE_URL || 'http://localhost:5000'}/generate-resume`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            parsed_resume: result,
                            job_description: stored.hasJD ? stored.jobDescription || '' : ''
                        })
                    });

                    if (res.ok) {
                        const data = await res.json();
                        if (data.success && data.data) {
                            localStorage.setItem('generatedResume', JSON.stringify(data.data));
                        }
                    }
                    API.hideLoading();
                    window.location.href = 'builder.html';
                } catch (e) {
                    console.warn('Generate direct call note:', e);
                    API.hideLoading();
                    window.location.href = 'builder.html';
                } finally {
                    genBtn.disabled = false;
                    genBtn.textContent = '✨ Generate Improved Resume';
                }
            });
        }

        // New analysis button
        const newBtn = document.getElementById('newAnalysisBtn');
        if (newBtn) {
            newBtn.addEventListener('click', () => {
                window.location.href = 'analyzer.html';
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
