/**
 * Resume Builder & Live Editor Script (builder.js)
 * Real-time two-way data binding, dynamic section editors, template switcher,
 * live A4 preview engine, DOCX export API integration, and print-ready PDF export.
 */

(function () {
    'use strict';

    const API = window.RESUME_ANALYZER || {};
    const API_BASE_URL = API.API_BASE_URL || 'http://localhost:5000';
    const san = API.sanitize || ((s) => s || '');

    // ==========================================
    // State Data Model
    // ==========================================
    let resumeState = {
        template: 'modern',
        accentColor: '#4f46e5',
        fontFamily: "'Inter', sans-serif",
        contact: {
            name: '',
            title: '',
            email: '',
            phone: '',
            location: '',
            linkedin: '',
            github: '',
            website: ''
        },
        summary: '',
        skills: {
            technical: [],
            soft: []
        },
        experience: [],
        projects: [],
        education: [],
        certifications: []
    };

    let zoomLevel = 1.0;

    // Sample fallback profile
    const SAMPLE_PROFILE = {
        template: 'modern',
        accentColor: '#4f46e5',
        fontFamily: "'Inter', sans-serif",
        contact: {
            name: 'Alex Morgan',
            title: 'Senior Full-Stack Software Engineer',
            email: 'alex.morgan@email.com',
            phone: '(555) 234-5678',
            location: 'San Francisco, CA',
            linkedin: 'linkedin.com/in/alexmorgan',
            github: 'github.com/alexmorgan',
            website: 'alexmorgan.dev'
        },
        summary: 'Results-driven Senior Full-Stack Engineer with 5+ years of experience designing, architecting, and scaling enterprise web applications. Proven track record of reducing API latency by 45%, leading cross-functional teams, and implementing robust CI/CD pipelines across AWS cloud infrastructure.',
        skills: {
            technical: ['Python', 'JavaScript (ES6+)', 'TypeScript', 'React.js', 'Node.js', 'Flask', 'FastAPI', 'PostgreSQL', 'Docker', 'Kubernetes', 'AWS (S3, EC2, Lambda)', 'Git', 'REST APIs', 'GraphQL', 'CI/CD'],
            soft: ['System Architecture', 'Agile & Scrum Leadership', 'Cross-Functional Collaboration', 'Technical Mentorship', 'Problem Solving']
        },
        experience: [
            {
                role: 'Senior Software Engineer',
                company: 'Apex Cloud Solutions',
                duration: '2022 - Present',
                location: 'San Francisco, CA',
                bullets: [
                    'Architected and deployed 4 high-throughput microservices using Python FastAPI and PostgreSQL, serving 120,000+ daily active users with 99.98% uptime.',
                    'Engineered real-time analytics dashboard with React and TypeScript, accelerating customer report generation speed by 55%.',
                    'Spearheaded Kubernetes container migration and optimized CI/CD workflows via GitHub Actions, reducing deployment cycle times by 60%.'
                ]
            },
            {
                role: 'Full-Stack Software Engineer',
                company: 'NovaTech Labs',
                duration: '2020 - 2022',
                location: 'Austin, TX',
                bullets: [
                    'Developed RESTful APIs and backend services with Python Flask and Redis caching, improving database query speeds by 40%.',
                    'Collaborated with product designers to implement responsive, accessible UI components utilizing modern CSS and React.',
                    'Authored unit and integration test suites achieving 94% code coverage using pytest and Jest.'
                ]
            }
        ],
        projects: [
            {
                title: 'AI Resume & Career Analyzer',
                tech: 'Python, Flask, NLP, scikit-learn, React',
                link: 'github.com/alexmorgan/resume-analyzer',
                bullets: [
                    'Engineered an ATS scoring engine utilizing TF-IDF cosine similarity to match candidates against job requirements with 95% precision.',
                    'Processed and extracted structured semantic data from PDF and DOCX documents with automated section classification.'
                ]
            },
            {
                title: 'Distributed Task Queue System',
                tech: 'Go, Redis, Docker, gRPC',
                link: 'github.com/alexmorgan/task-queue',
                bullets: [
                    'Implemented a scalable, asynchronous job queue capable of processing over 10,000 tasks/second with automatic retry mechanisms.'
                ]
            }
        ],
        education: [
            {
                degree: 'Bachelor of Science in Computer Science',
                institution: 'University of California, Berkeley',
                year: '2020',
                details: 'Dean\'s Honors List, GPA 3.85 / 4.0'
            }
        ],
        certifications: [
            { name: 'AWS Certified Solutions Architect – Associate', issuer: 'Amazon Web Services', year: '2023' },
            { name: 'Certified Kubernetes Administrator (CKA)', issuer: 'Linux Foundation', year: '2022' }
        ]
    };

    // ==========================================
    // Initialization & Data Loading
    // ==========================================
    async function init() {
        initAccordion();
        initToolbarControls();
        initDynamicListButtons();
        attachFormInputListeners();

        // Check if coming with existing analysis data
        const loaded = await tryLoadExistingData();
        if (!loaded) {
            // Pre-fill with sample profile for initial presentation
            loadState(SAMPLE_PROFILE);
        }

        renderLivePreview();
    }

    async function tryLoadExistingData() {
        try {
            // Check if generated resume already saved
            const savedGen = localStorage.getItem('generatedResume');
            if (savedGen) {
                const parsedGen = JSON.parse(savedGen);
                if (parsedGen && parsedGen.contact) {
                    loadState(parsedGen);
                    API.showNotification('✨ Loaded your tailored resume!', 'success');
                    return true;
                }
            }

            // Check if raw analysis result is available to auto-generate
            const rawAnalysis = localStorage.getItem('resumeAnalysis');
            if (rawAnalysis) {
                const parsed = JSON.parse(rawAnalysis);
                if (parsed && parsed.result) {
                    API.showNotification('⏳ Optimizing your resume with AI...', 'info');
                    const generated = await requestGenerateResume(parsed.result, parsed.hasJD ? parsed.jobDescription : '');
                    if (generated) {
                        loadState(generated);
                        API.showNotification('✅ Resume generated from your uploaded file!', 'success');
                        return true;
                    }
                }
            }
        } catch (e) {
            console.error('Failed to load existing data:', e);
        }
        return false;
    }

    async function requestGenerateResume(parsedResumeData, jobDescription = '') {
        try {
            const res = await fetch(`${API_BASE_URL}/generate-resume`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    parsed_resume: parsedResumeData,
                    job_description: jobDescription
                })
            });
            if (!res.ok) return null;
            const data = await res.json();
            return data.success ? data.data : null;
        } catch (e) {
            console.warn('API generate call fallback:', e);
            return null;
        }
    }

    function loadState(data) {
        resumeState = {
            ...resumeState,
            ...data,
            contact: { ...resumeState.contact, ...(data.contact || {}) },
            skills: {
                technical: Array.isArray(data.skills?.technical) ? [...data.skills.technical] : [],
                soft: Array.isArray(data.skills?.soft) ? [...data.skills.soft] : []
            },
            experience: Array.isArray(data.experience) ? JSON.parse(JSON.stringify(data.experience)) : [],
            projects: Array.isArray(data.projects) ? JSON.parse(JSON.stringify(data.projects)) : [],
            education: Array.isArray(data.education) ? JSON.parse(JSON.stringify(data.education)) : [],
            certifications: Array.isArray(data.certifications) ? JSON.parse(JSON.stringify(data.certifications)) : []
        };

        // Populate Form Inputs
        populateFormFromState();
        renderDynamicLists();
        renderLivePreview();
    }

    function populateFormFromState() {
        const c = resumeState.contact;
        setVal('inp-name', c.name);
        setVal('inp-title', c.title);
        setVal('inp-email', c.email);
        setVal('inp-phone', c.phone);
        setVal('inp-location', c.location);
        setVal('inp-linkedin', c.linkedin);
        setVal('inp-github', c.github);
        setVal('inp-website', c.website);

        setVal('inp-summary', resumeState.summary);
        setVal('inp-tech-skills', (resumeState.skills.technical || []).join(', '));
        setVal('inp-soft-skills', (resumeState.skills.soft || []).join(', '));

        if (resumeState.template) {
            const tSelect = document.getElementById('templateSelect');
            if (tSelect) tSelect.value = resumeState.template;
        }
        if (resumeState.fontFamily) {
            const fSelect = document.getElementById('fontSelect');
            if (fSelect) fSelect.value = resumeState.fontFamily;
        }
        if (resumeState.accentColor) {
            updateActiveSwatch(resumeState.accentColor);
        }
    }

    function setVal(id, val) {
        const el = document.getElementById(id);
        if (el) el.value = val || '';
    }

    // ==========================================
    // Dynamic Form Entries Rendering
    // ==========================================
    function renderDynamicLists() {
        renderExperienceEditor();
        renderProjectsEditor();
        renderEducationEditor();
        renderCertificationsEditor();
    }

    function renderExperienceEditor() {
        const container = document.getElementById('experienceListContainer');
        if (!container) return;
        container.innerHTML = '';

        resumeState.experience.forEach((exp, expIdx) => {
            const card = document.createElement('div');
            card.className = 'entry-card';
            card.innerHTML = `
                <div class="entry-card-header">
                    <strong>💼 ${san(exp.role || 'Position')} at ${san(exp.company || 'Company')}</strong>
                    <button type="button" class="btn-remove-sm" data-action="delete-exp" data-idx="${expIdx}">✕ Remove</button>
                </div>
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label>Job Title / Role</label>
                        <input type="text" class="form-control" data-field="role" data-idx="${expIdx}" value="${san(exp.role || '')}" placeholder="Software Engineer">
                    </div>
                    <div class="form-group flex-1">
                        <label>Company / Organization</label>
                        <input type="text" class="form-control" data-field="company" data-idx="${expIdx}" value="${san(exp.company || '')}" placeholder="Acme Corp">
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label>Dates / Duration</label>
                        <input type="text" class="form-control" data-field="duration" data-idx="${expIdx}" value="${san(exp.duration || '')}" placeholder="Jan 2022 - Present">
                    </div>
                    <div class="form-group flex-1">
                        <label>Location</label>
                        <input type="text" class="form-control" data-field="location" data-idx="${expIdx}" value="${san(exp.location || '')}" placeholder="City, State">
                    </div>
                </div>
                <div class="form-group">
                    <label>Accomplishments &amp; Bullet Points</label>
                    <div class="bullet-list-inputs" id="bullets-exp-${expIdx}">
                        ${(exp.bullets || []).map((b, bIdx) => `
                            <div class="bullet-input-row">
                                <span class="bullet-dot">•</span>
                                <input type="text" class="form-control bullet-input" data-exp="${expIdx}" data-bullet="${bIdx}" value="${san(b)}" placeholder="Action verb + task + measurable result...">
                                <button type="button" class="btn-remove-bullet" data-action="delete-bullet-exp" data-exp="${expIdx}" data-bullet="${bIdx}">✕</button>
                            </div>
                        `).join('')}
                    </div>
                    <button type="button" class="btn-micro mt-2" data-action="add-bullet-exp" data-exp="${expIdx}">➕ Add Bullet Point</button>
                </div>
            `;
            container.appendChild(card);
        });
    }

    function renderProjectsEditor() {
        const container = document.getElementById('projectsListContainer');
        if (!container) return;
        container.innerHTML = '';

        resumeState.projects.forEach((proj, projIdx) => {
            const card = document.createElement('div');
            card.className = 'entry-card';
            card.innerHTML = `
                <div class="entry-card-header">
                    <strong>🚀 ${san(proj.title || 'Project')}</strong>
                    <button type="button" class="btn-remove-sm" data-action="delete-proj" data-idx="${projIdx}">✕ Remove</button>
                </div>
                <div class="form-row">
                    <div class="form-group flex-1">
                        <label>Project Title</label>
                        <input type="text" class="form-control" data-pfield="title" data-idx="${projIdx}" value="${san(proj.title || '')}" placeholder="Project Name">
                    </div>
                    <div class="form-group flex-1">
                        <label>Technologies Used</label>
                        <input type="text" class="form-control" data-pfield="tech" data-idx="${projIdx}" value="${san(proj.tech || '')}" placeholder="React, Node.js, AWS">
                    </div>
                </div>
                <div class="form-group">
                    <label>Project Link / URL</label>
                    <input type="text" class="form-control" data-pfield="link" data-idx="${projIdx}" value="${san(proj.link || '')}" placeholder="github.com/user/project">
                </div>
                <div class="form-group">
                    <label>Bullet Points</label>
                    <div class="bullet-list-inputs" id="bullets-proj-${projIdx}">
                        ${(proj.bullets || []).map((b, bIdx) => `
                            <div class="bullet-input-row">
                                <span class="bullet-dot">•</span>
                                <input type="text" class="form-control bullet-input" data-proj="${projIdx}" data-pbullet="${bIdx}" value="${san(b)}" placeholder="Built X feature using Y...">
                                <button type="button" class="btn-remove-bullet" data-action="delete-bullet-proj" data-proj="${projIdx}" data-pbullet="${bIdx}">✕</button>
                            </div>
                        `).join('')}
                    </div>
                    <button type="button" class="btn-micro mt-2" data-action="add-bullet-proj" data-proj="${projIdx}">➕ Add Bullet Point</button>
                </div>
            `;
            container.appendChild(card);
        });
    }

    function renderEducationEditor() {
        const container = document.getElementById('educationListContainer');
        if (!container) return;
        container.innerHTML = '';

        resumeState.education.forEach((edu, eduIdx) => {
            const card = document.createElement('div');
            card.className = 'entry-card';
            card.innerHTML = `
                <div class="entry-card-header">
                    <strong>🎓 ${san(edu.degree || 'Degree')}</strong>
                    <button type="button" class="btn-remove-sm" data-action="delete-edu" data-idx="${eduIdx}">✕ Remove</button>
                </div>
                <div class="form-row">
                    <div class="form-group flex-2">
                        <label>Degree / Major</label>
                        <input type="text" class="form-control" data-efield="degree" data-idx="${eduIdx}" value="${san(edu.degree || '')}" placeholder="B.S. Computer Science">
                    </div>
                    <div class="form-group flex-1">
                        <label>Graduation Year</label>
                        <input type="text" class="form-control" data-efield="year" data-idx="${eduIdx}" value="${san(edu.year || '')}" placeholder="2022">
                    </div>
                </div>
                <div class="form-group">
                    <label>School / University / Institution</label>
                    <input type="text" class="form-control" data-efield="institution" data-idx="${eduIdx}" value="${san(edu.institution || '')}" placeholder="University of California">
                </div>
                <div class="form-group">
                    <label>Honors / GPA / Additional Details (Optional)</label>
                    <input type="text" class="form-control" data-efield="details" data-idx="${eduIdx}" value="${san(edu.details || '')}" placeholder="GPA: 3.8, Dean's List">
                </div>
            `;
            container.appendChild(card);
        });
    }

    function renderCertificationsEditor() {
        const container = document.getElementById('certificationsListContainer');
        if (!container) return;
        container.innerHTML = '';

        resumeState.certifications.forEach((cert, certIdx) => {
            const certName = typeof cert === 'object' ? cert.name : cert;
            const certIssuer = typeof cert === 'object' ? (cert.issuer || '') : '';
            const certYear = typeof cert === 'object' ? (cert.year || '') : '';

            const card = document.createElement('div');
            card.className = 'entry-card';
            card.innerHTML = `
                <div class="entry-card-header">
                    <strong>🏆 ${san(certName || 'Certification')}</strong>
                    <button type="button" class="btn-remove-sm" data-action="delete-cert" data-idx="${certIdx}">✕ Remove</button>
                </div>
                <div class="form-row">
                    <div class="form-group flex-2">
                        <label>Certification Name</label>
                        <input type="text" class="form-control" data-cfield="name" data-idx="${certIdx}" value="${san(certName)}" placeholder="AWS Certified Solutions Architect">
                    </div>
                    <div class="form-group flex-1">
                        <label>Year</label>
                        <input type="text" class="form-control" data-cfield="year" data-idx="${certIdx}" value="${san(certYear)}" placeholder="2023">
                    </div>
                </div>
                <div class="form-group">
                    <label>Issuing Authority / Organization</label>
                    <input type="text" class="form-control" data-cfield="issuer" data-idx="${certIdx}" value="${san(certIssuer)}" placeholder="Amazon Web Services">
                </div>
            `;
            container.appendChild(card);
        });
    }

    // ==========================================
    // Real-Time Live Preview Rendering Engine
    // ==========================================
    function renderLivePreview() {
        const paper = document.getElementById('resumePaper');
        if (!paper) return;

        // Apply template and typography styling
        paper.className = `resume-paper template-${resumeState.template}`;
        paper.style.fontFamily = resumeState.fontFamily;
        paper.style.setProperty('--accent-color', resumeState.accentColor);

        const { contact, summary, skills, experience, projects, education, certifications } = resumeState;

        // Build contact items array
        const contactLinks = [];
        if (contact.email) contactLinks.push(`<span class="p-contact-item">📧 <a href="mailto:${san(contact.email)}">${san(contact.email)}</a></span>`);
        if (contact.phone) contactLinks.push(`<span class="p-contact-item">📱 ${san(contact.phone)}</span>`);
        if (contact.location) contactLinks.push(`<span class="p-contact-item">📍 ${san(contact.location)}</span>`);
        if (contact.linkedin) contactLinks.push(`<span class="p-contact-item">💼 <a href="https://${san(contact.linkedin)}" target="_blank">${san(contact.linkedin.replace(/^https?:\/\//, ''))}</a></span>`);
        if (contact.github) contactLinks.push(`<span class="p-contact-item">🐙 <a href="https://${san(contact.github)}" target="_blank">${san(contact.github.replace(/^https?:\/\//, ''))}</a></span>`);
        if (contact.website) contactLinks.push(`<span class="p-contact-item">🌐 <a href="https://${san(contact.website)}" target="_blank">${san(contact.website.replace(/^https?:\/\//, ''))}</a></span>`);

        let html = `
            <!-- Header Section -->
            <header class="p-header">
                <h1 class="p-name">${san(contact.name || 'Your Full Name')}</h1>
                ${contact.title ? `<div class="p-title">${san(contact.title)}</div>` : ''}
                <div class="p-contact-row">
                    ${contactLinks.join(' <span class="p-sep">|</span> ')}
                </div>
            </header>
        `;

        // Summary Section
        if (summary && summary.trim()) {
            html += `
                <section class="p-section">
                    <h2 class="p-section-title">Professional Summary</h2>
                    <p class="p-summary-text">${san(summary)}</p>
                </section>
            `;
        }

        // Skills Section
        const techSkills = skills.technical || [];
        const softSkills = skills.soft || [];
        if (techSkills.length > 0 || softSkills.length > 0) {
            html += `
                <section class="p-section">
                    <h2 class="p-section-title">Skills &amp; Competencies</h2>
                    <div class="p-skills-container">
                        ${techSkills.length > 0 ? `
                            <div class="p-skills-row">
                                <strong class="p-skills-lbl">Technical Skills:</strong>
                                <span class="p-skills-val">${techSkills.map(s => san(s)).join(', ')}</span>
                            </div>
                        ` : ''}
                        ${softSkills.length > 0 ? `
                            <div class="p-skills-row">
                                <strong class="p-skills-lbl">Core Competencies:</strong>
                                <span class="p-skills-val">${softSkills.map(s => san(s)).join(', ')}</span>
                            </div>
                        ` : ''}
                    </div>
                </section>
            `;
        }

        // Experience Section
        if (experience && experience.length > 0) {
            html += `
                <section class="p-section">
                    <h2 class="p-section-title">Professional Experience</h2>
                    <div class="p-entries">
                        ${experience.map(exp => `
                            <div class="p-entry">
                                <div class="p-entry-header">
                                    <div class="p-role-company">
                                        <strong class="p-role">${san(exp.role || 'Role')}</strong>
                                        ${exp.company ? `<span class="p-company"> | ${san(exp.company)}</span>` : ''}
                                        ${exp.location ? `<span class="p-location">, ${san(exp.location)}</span>` : ''}
                                    </div>
                                    <div class="p-date">${san(exp.duration || '')}</div>
                                </div>
                                ${exp.bullets && exp.bullets.length > 0 ? `
                                    <ul class="p-bullets">
                                        ${exp.bullets.map(b => b.trim() ? `<li>${san(b)}</li>` : '').join('')}
                                    </ul>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </section>
            `;
        }

        // Projects Section
        if (projects && projects.length > 0) {
            html += `
                <section class="p-section">
                    <h2 class="p-section-title">Projects &amp; Portfolio</h2>
                    <div class="p-entries">
                        ${projects.map(proj => `
                            <div class="p-entry">
                                <div class="p-entry-header">
                                    <div class="p-proj-title-tech">
                                        <strong class="p-proj-title">${san(proj.title || 'Project')}</strong>
                                        ${proj.tech ? `<span class="p-tech-stack"> [${san(proj.tech)}]</span>` : ''}
                                    </div>
                                    ${proj.link ? `<div class="p-proj-link"><a href="https://${san(proj.link.replace(/^https?:\/\//, ''))}" target="_blank">${san(proj.link)}</a></div>` : ''}
                                </div>
                                ${proj.bullets && proj.bullets.length > 0 ? `
                                    <ul class="p-bullets">
                                        ${proj.bullets.map(b => b.trim() ? `<li>${san(b)}</li>` : '').join('')}
                                    </ul>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </section>
            `;
        }

        // Education Section
        if (education && education.length > 0) {
            html += `
                <section class="p-section">
                    <h2 class="p-section-title">Education</h2>
                    <div class="p-entries">
                        ${education.map(edu => `
                            <div class="p-entry">
                                <div class="p-entry-header">
                                    <div>
                                        <strong class="p-degree">${san(edu.degree || 'Degree')}</strong>
                                        ${edu.institution ? `<span class="p-institution"> — ${san(edu.institution)}</span>` : ''}
                                    </div>
                                    <div class="p-date">${san(edu.year || '')}</div>
                                </div>
                                ${edu.details ? `<div class="p-edu-details">${san(edu.details)}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                </section>
            `;
        }

        // Certifications Section
        if (certifications && certifications.length > 0) {
            html += `
                <section class="p-section">
                    <h2 class="p-section-title">Certifications &amp; Credentials</h2>
                    <ul class="p-bullets p-certs-list">
                        ${certifications.map(c => {
                            const name = typeof c === 'object' ? c.name : c;
                            const issuer = typeof c === 'object' && c.issuer ? ` (${c.issuer})` : '';
                            const yr = typeof c === 'object' && c.year ? ` — ${c.year}` : '';
                            return `<li><strong>${san(name)}</strong>${san(issuer)}${san(yr)}</li>`;
                        }).join('')}
                    </ul>
                </section>
            `;
        }

        paper.innerHTML = html;
    }

    // ==========================================
    // Event Handlers & Form Sync
    // ==========================================
    function attachFormInputListeners() {
        const bind = (id, fn) => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('input', fn);
        };

        bind('inp-name', (e) => { resumeState.contact.name = e.target.value; renderLivePreview(); });
        bind('inp-title', (e) => { resumeState.contact.title = e.target.value; renderLivePreview(); });
        bind('inp-email', (e) => { resumeState.contact.email = e.target.value; renderLivePreview(); });
        bind('inp-phone', (e) => { resumeState.contact.phone = e.target.value; renderLivePreview(); });
        bind('inp-location', (e) => { resumeState.contact.location = e.target.value; renderLivePreview(); });
        bind('inp-linkedin', (e) => { resumeState.contact.linkedin = e.target.value; renderLivePreview(); });
        bind('inp-github', (e) => { resumeState.contact.github = e.target.value; renderLivePreview(); });
        bind('inp-website', (e) => { resumeState.contact.website = e.target.value; renderLivePreview(); });

        bind('inp-summary', (e) => { resumeState.summary = e.target.value; renderLivePreview(); });

        bind('inp-tech-skills', (e) => {
            resumeState.skills.technical = e.target.value.split(',').map(s => s.trim()).filter(Boolean);
            renderLivePreview();
        });
        bind('inp-soft-skills', (e) => {
            resumeState.skills.soft = e.target.value.split(',').map(s => s.trim()).filter(Boolean);
            renderLivePreview();
        });

        // AI Summary Polisher Button
        const polishBtn = document.getElementById('aiEnhanceSummaryBtn');
        if (polishBtn) {
            polishBtn.addEventListener('click', () => {
                polishSummaryAction();
            });
        }
    }

    function polishSummaryAction() {
        const text = resumeState.summary;
        if (!text) {
            API.showNotification('Please enter a draft summary first.', 'info');
            return;
        }
        // Action verb enhancer
        let polished = text
            .replace(/\bworked on\b/gi, 'Spearheaded and engineered')
            .replace(/\bhelped with\b/gi, 'Collaborated on delivering')
            .replace(/\bresponsible for\b/gi, 'Led initiatives for')
            .replace(/\bgood at\b/gi, 'Highly proficient in');
        
        if (!polished.endsWith('.')) polished += '.';
        resumeState.summary = polished;
        setVal('inp-summary', polished);
        renderLivePreview();
        API.showNotification('✨ Summary polished with strong action verbs!', 'success');
    }

    function initDynamicListButtons() {
        // Experience Add Button
        const addExpBtn = document.getElementById('addExperienceBtn');
        if (addExpBtn) {
            addExpBtn.addEventListener('click', () => {
                resumeState.experience.push({
                    role: 'Software Engineer',
                    company: 'Tech Company',
                    duration: '2023 - Present',
                    location: 'City, State',
                    bullets: ['Engineered scalable features collaborating with cross-functional teams.']
                });
                renderExperienceEditor();
                renderLivePreview();
            });
        }

        // Projects Add Button
        const addProjBtn = document.getElementById('addProjectBtn');
        if (addProjBtn) {
            addProjBtn.addEventListener('click', () => {
                resumeState.projects.push({
                    title: 'New Featured Project',
                    tech: 'Python, React, AWS',
                    link: 'github.com/username/project',
                    bullets: ['Designed and deployed full-stack solution with 99% automated test coverage.']
                });
                renderProjectsEditor();
                renderLivePreview();
            });
        }

        // Education Add Button
        const addEduBtn = document.getElementById('addEducationBtn');
        if (addEduBtn) {
            addEduBtn.addEventListener('click', () => {
                resumeState.education.push({
                    degree: 'Bachelor of Science in Computer Science',
                    institution: 'State University',
                    year: '2023',
                    details: ''
                });
                renderEducationEditor();
                renderLivePreview();
            });
        }

        // Certification Add Button
        const addCertBtn = document.getElementById('addCertificationBtn');
        if (addCertBtn) {
            addCertBtn.addEventListener('click', () => {
                resumeState.certifications.push({
                    name: 'Professional Certification',
                    issuer: 'Issuing Body',
                    year: '2024'
                });
                renderCertificationsEditor();
                renderLivePreview();
            });
        }

        // Delegated clicks for experience, projects, education, certifications
        document.addEventListener('click', (e) => {
            const target = e.target;
            const action = target.dataset.action;
            if (!action) return;

            // Delete Experience
            if (action === 'delete-exp') {
                const idx = parseInt(target.dataset.idx, 10);
                resumeState.experience.splice(idx, 1);
                renderExperienceEditor();
                renderLivePreview();
            }
            // Add Bullet to Experience
            else if (action === 'add-bullet-exp') {
                const expIdx = parseInt(target.dataset.exp, 10);
                if (resumeState.experience[expIdx]) {
                    if (!resumeState.experience[expIdx].bullets) resumeState.experience[expIdx].bullets = [];
                    resumeState.experience[expIdx].bullets.push('Delivered measurable impact through optimized code architectures.');
                    renderExperienceEditor();
                    renderLivePreview();
                }
            }
            // Delete Bullet from Experience
            else if (action === 'delete-bullet-exp') {
                const expIdx = parseInt(target.dataset.exp, 10);
                const bulletIdx = parseInt(target.dataset.bullet, 10);
                if (resumeState.experience[expIdx] && resumeState.experience[expIdx].bullets) {
                    resumeState.experience[expIdx].bullets.splice(bulletIdx, 1);
                    renderExperienceEditor();
                    renderLivePreview();
                }
            }
            // Delete Project
            else if (action === 'delete-proj') {
                const idx = parseInt(target.dataset.idx, 10);
                resumeState.projects.splice(idx, 1);
                renderProjectsEditor();
                renderLivePreview();
            }
            // Add Bullet to Project
            else if (action === 'add-bullet-proj') {
                const projIdx = parseInt(target.dataset.proj, 10);
                if (resumeState.projects[projIdx]) {
                    if (!resumeState.projects[projIdx].bullets) resumeState.projects[projIdx].bullets = [];
                    resumeState.projects[projIdx].bullets.push('Implemented automated CI/CD deployment pipelines.');
                    renderProjectsEditor();
                    renderLivePreview();
                }
            }
            // Delete Bullet from Project
            else if (action === 'delete-bullet-proj') {
                const projIdx = parseInt(target.dataset.proj, 10);
                const bulletIdx = parseInt(target.dataset.pbullet, 10);
                if (resumeState.projects[projIdx] && resumeState.projects[projIdx].bullets) {
                    resumeState.projects[projIdx].bullets.splice(bulletIdx, 1);
                    renderProjectsEditor();
                    renderLivePreview();
                }
            }
            // Delete Education
            else if (action === 'delete-edu') {
                const idx = parseInt(target.dataset.idx, 10);
                resumeState.education.splice(idx, 1);
                renderEducationEditor();
                renderLivePreview();
            }
            // Delete Certification
            else if (action === 'delete-cert') {
                const idx = parseInt(target.dataset.idx, 10);
                resumeState.certifications.splice(idx, 1);
                renderCertificationsEditor();
                renderLivePreview();
            }
        });

        // Delegated input changes for dynamic inputs
        document.addEventListener('input', (e) => {
            const target = e.target;
            
            // Experience fields
            if (target.dataset.field) {
                const idx = parseInt(target.dataset.idx, 10);
                const field = target.dataset.field;
                if (resumeState.experience[idx]) {
                    resumeState.experience[idx][field] = target.value;
                    renderLivePreview();
                }
            }
            // Experience bullet inputs
            else if (target.dataset.exp !== undefined && target.dataset.bullet !== undefined) {
                const expIdx = parseInt(target.dataset.exp, 10);
                const bulletIdx = parseInt(target.dataset.bullet, 10);
                if (resumeState.experience[expIdx] && resumeState.experience[expIdx].bullets) {
                    resumeState.experience[expIdx].bullets[bulletIdx] = target.value;
                    renderLivePreview();
                }
            }
            // Project fields
            else if (target.dataset.pfield) {
                const idx = parseInt(target.dataset.idx, 10);
                const field = target.dataset.pfield;
                if (resumeState.projects[idx]) {
                    resumeState.projects[idx][field] = target.value;
                    renderLivePreview();
                }
            }
            // Project bullet inputs
            else if (target.dataset.proj !== undefined && target.dataset.pbullet !== undefined) {
                const projIdx = parseInt(target.dataset.proj, 10);
                const bulletIdx = parseInt(target.dataset.pbullet, 10);
                if (resumeState.projects[projIdx] && resumeState.projects[projIdx].bullets) {
                    resumeState.projects[projIdx].bullets[bulletIdx] = target.value;
                    renderLivePreview();
                }
            }
            // Education fields
            else if (target.dataset.efield) {
                const idx = parseInt(target.dataset.idx, 10);
                const field = target.dataset.efield;
                if (resumeState.education[idx]) {
                    resumeState.education[idx][field] = target.value;
                    renderLivePreview();
                }
            }
            // Certification fields
            else if (target.dataset.cfield) {
                const idx = parseInt(target.dataset.idx, 10);
                const field = target.dataset.cfield;
                if (resumeState.certifications[idx]) {
                    if (typeof resumeState.certifications[idx] !== 'object') {
                        resumeState.certifications[idx] = { name: resumeState.certifications[idx], issuer: '', year: '' };
                    }
                    resumeState.certifications[idx][field] = target.value;
                    renderLivePreview();
                }
            }
        });
    }

    // ==========================================
    // Toolbar & Controls (Template, Color, Font, Zoom, Export)
    // ==========================================
    function initToolbarControls() {
        // Template Switcher
        const tSelect = document.getElementById('templateSelect');
        if (tSelect) {
            tSelect.addEventListener('change', (e) => {
                resumeState.template = e.target.value;
                renderLivePreview();
                API.showNotification(`Applied ${e.target.options[e.target.selectedIndex].text} template`, 'info');
            });
        }

        // Font Switcher
        const fSelect = document.getElementById('fontSelect');
        if (fSelect) {
            fSelect.addEventListener('change', (e) => {
                resumeState.fontFamily = e.target.value;
                renderLivePreview();
            });
        }

        // Color Swatches
        const swatches = document.querySelectorAll('.swatch');
        swatches.forEach(swatch => {
            swatch.addEventListener('click', () => {
                const color = swatch.dataset.color;
                resumeState.accentColor = color;
                updateActiveSwatch(color);
                renderLivePreview();
            });
        });

        // Zoom Controls
        const zoomInBtn = document.getElementById('zoomInBtn');
        const zoomOutBtn = document.getElementById('zoomOutBtn');
        const zoomResetBtn = document.getElementById('zoomResetBtn');
        const zoomLabel = document.getElementById('zoomLabel');
        const paper = document.getElementById('resumePaper');

        function applyZoom(newZoom) {
            zoomLevel = Math.max(0.4, Math.min(1.6, newZoom));
            if (zoomLabel) zoomLabel.textContent = `${Math.round(zoomLevel * 100)}%`;
            if (paper) paper.style.transform = `scale(${zoomLevel})`;
        }

        if (zoomInBtn) zoomInBtn.addEventListener('click', () => applyZoom(zoomLevel + 0.1));
        if (zoomOutBtn) zoomOutBtn.addEventListener('click', () => applyZoom(zoomLevel - 0.1));
        if (zoomResetBtn) zoomResetBtn.addEventListener('click', () => applyZoom(1.0));

        // Load Sample Data Button
        const sampleBtn = document.getElementById('loadSampleDataBtn');
        if (sampleBtn) {
            sampleBtn.addEventListener('click', () => {
                loadState(SAMPLE_PROFILE);
                API.showNotification('📋 Sample profile loaded!', 'success');
            });
        }

        // Export DOCX Button
        const docxBtn = document.getElementById('exportDocxBtn');
        if (docxBtn) {
            docxBtn.addEventListener('click', () => exportDocxAction());
        }

        // Export PDF Button
        const pdfBtn = document.getElementById('exportPdfBtn');
        if (pdfBtn) {
            pdfBtn.addEventListener('click', () => exportPdfAction());
        }
    }

    function updateActiveSwatch(color) {
        document.querySelectorAll('.swatch').forEach(s => {
            s.classList.toggle('active', s.dataset.color === color);
        });
    }

    // ==========================================
    // Export Handlers
    // ==========================================
    async function exportDocxAction() {
        const btn = document.getElementById('exportDocxBtn');
        try {
            if (btn) { btn.disabled = true; btn.textContent = '⏳ Exporting...'; }
            API.showNotification('Generating Microsoft Word (.docx)...', 'info');

            const res = await fetch(`${API_BASE_URL}/export-resume`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    resume_data: resumeState,
                    template: resumeState.template,
                    format: 'docx'
                })
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `Export failed (${res.status})`);
            }

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const candidateName = (resumeState.contact.name || 'ATS_Resume').replace(/\s+/g, '_');
            a.download = `${candidateName}_ATS_Resume.docx`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);

            API.showNotification('✅ DOCX Resume downloaded successfully!', 'success');
        } catch (e) {
            console.error('Export DOCX error:', e);
            API.showNotification(`❌ DOCX export error: ${e.message}`, 'error');
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = '📝 Export DOCX'; }
        }
    }

    function exportPdfAction() {
        API.showNotification('🖨️ Opening print dialog (select "Save as PDF" for crisp vector output)', 'info');
        // Reset zoom to 100% prior to printing
        const paper = document.getElementById('resumePaper');
        const prevTransform = paper ? paper.style.transform : '';
        if (paper) paper.style.transform = 'scale(1)';

        setTimeout(() => {
            window.print();
            if (paper) paper.style.transform = prevTransform;
        }, 150);
    }

    // ==========================================
    // Accordion Helper
    // ==========================================
    function initAccordion() {
        window.toggleAccordion = function (secId) {
            const card = document.getElementById(secId);
            if (card) {
                card.classList.toggle('open');
            }
        };
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
