/**
 * Job Mitra — Frontend Application Engine
 * Handles Real-time Search, Filters, Dynamic Pagination, Bookmarks,
 * 1-Click Applications, Direct HR Mail, Fraud Reports, and Audited Pro UPI Pass.
 */

let currentPage = 1;
let currentPerPage = 10;
let searchDebounceTimer = null;
let selectedSubscriptionPlan = { name: 'Graduate Career Pro', amount: 199 };

// Retrieve CSRF token from meta tag
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute('content') : '';
}

// HTML escape helper
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Toast notification helper
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'fa-circle-info text-primary';
    if (type === 'success') icon = 'fa-circle-check text-success';
    else if (type === 'error') icon = 'fa-triangle-exclamation text-danger';
    else if (type === 'gold') icon = 'fa-crown text-gold';

    toast.innerHTML = `<i class="fa-solid ${icon}"></i> <span>${escapeHtml(message)}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Date string initializer
document.addEventListener('DOMContentLoaded', () => {
    const dateEl = document.getElementById('currentDateStr');
    if (dateEl) {
        const d = new Date();
        const opts = { month: 'short', year: 'numeric', day: 'numeric' };
        dateEl.innerHTML = `<i class="fa-regular fa-calendar-days"></i> ${d.toLocaleDateString('en-US', opts)}`;
    }
});

// User dropdown menu toggle
function toggleUserDropdown(e) {
    e.stopPropagation();
    const menu = document.getElementById('userDropdownMenu');
    if (menu) menu.classList.toggle('active');
}

document.addEventListener('click', () => {
    const menu = document.getElementById('userDropdownMenu');
    if (menu) menu.classList.remove('active');
});

// Mobile menu toggle
function toggleMobileMenu() {
    const nav = document.getElementById('mainNavLinks');
    if (nav) {
        if (nav.style.display === 'flex') {
            nav.style.display = '';
        } else {
            nav.style.display = 'flex';
            nav.style.flexDirection = 'column';
            nav.style.position = 'absolute';
            nav.style.top = '72px';
            nav.style.left = '0';
            nav.style.width = '100%';
            nav.style.background = 'rgba(11, 16, 32, 0.98)';
            nav.style.padding = '1rem';
            nav.style.borderBottom = '1px solid var(--border)';
        }
    }
}

// ==========================================
// Jobs Loading & Search Engine
// ==========================================

function debounceJobSearch() {
    const val = document.getElementById('searchInput')?.value.trim() || '';
    const clearBtn = document.getElementById('clearSearchBtn');
    if (clearBtn) clearBtn.style.display = val ? 'block' : 'none';

    clearTimeout(searchDebounceTimer);
    searchDebounceTimer = setTimeout(() => {
        loadJobsFromAPI(1);
    }, 280);
}

function clearJobSearch() {
    const input = document.getElementById('searchInput');
    if (input) input.value = '';
    const clearBtn = document.getElementById('clearSearchBtn');
    if (clearBtn) clearBtn.style.display = 'none';
    loadJobsFromAPI(1);
}

function triggerSearch() {
    loadJobsFromAPI(1);
}

function resetAllJobFilters() {
    const sInput = document.getElementById('searchInput');
    if (sInput) sInput.value = '';
    const city = document.getElementById('citySelect');
    if (city) city.value = 'all';
    const stream = document.getElementById('streamSelect');
    if (stream) stream.value = 'all';
    const wm = document.getElementById('workModeSelect');
    if (wm) wm.value = 'all';
    const exp = document.getElementById('experienceSelect');
    if (exp) exp.value = 'all';
    const minSal = document.getElementById('minSalarySelect');
    if (minSal) minSal.value = '';
    const prem = document.getElementById('premiumFilterToggle');
    if (prem) prem.checked = false;
    const urg = document.getElementById('urgentFilterToggle');
    if (urg) urg.checked = false;

    document.querySelectorAll('.stream-pill').forEach(b => b.classList.remove('active'));
    document.querySelector('.stream-pill')?.classList.add('active');

    loadJobsFromAPI(1);
    showToast('Filters reset to default', 'info');
}

async function loadJobsFromAPI(page = 1) {
    const container = document.getElementById('jobCardsContainer');
    if (!container) return; // Not on search page

    currentPage = page;
    const countBadge = document.getElementById('jobsCountBadge');
    const filterCountDisplay = document.getElementById('filterCountDisplay');
    if (countBadge) countBadge.textContent = 'Searching vacancies...';

    const q = document.getElementById('searchInput')?.value.trim() || '';
    const city = document.getElementById('citySelect')?.value || 'all';
    const stream = document.getElementById('streamSelect')?.value || 'all';
    const workMode = document.getElementById('workModeSelect')?.value || 'all';
    const experience = document.getElementById('experienceSelect')?.value || 'all';
    const minSal = document.getElementById('minSalarySelect')?.value || '';
    const premium = document.getElementById('premiumFilterToggle')?.checked || false;
    const urgent = document.getElementById('urgentFilterToggle')?.checked || false;
    const sort = document.getElementById('sortSelect')?.value || 'newest';

    const params = new URLSearchParams();
    if (q) params.set('q', q);
    if (city && city !== 'all') params.set('city', city);
    if (stream && stream !== 'all') params.set('stream', stream);
    if (workMode && workMode !== 'all') params.set('work_mode', workMode);
    if (experience && experience !== 'all') params.set('experience', experience);
    if (minSal) params.set('min_salary', minSal);
    if (premium) params.set('premium', 'true');
    if (urgent) params.set('urgent', 'true');
    params.set('sort', sort);
    params.set('page', page);
    params.set('per_page', currentPerPage);

    try {
        const res = await fetch(`/api/jobs?${params.toString()}`);
        if (!res.ok) throw new Error('API response failed');
        const data = await res.json();

        if (countBadge) countBadge.textContent = `${data.total} Vacancies Found`;
        if (filterCountDisplay) filterCountDisplay.textContent = data.total;

        renderJobCardsList(data.jobs, container);
        renderPaginationControls(data.page, data.total_pages);
    } catch (err) {
        console.error('Job search error:', err);
        container.innerHTML = `
            <div class="glass-panel" style="padding:2.5rem; text-align:center;">
                <i class="fa-solid fa-triangle-exclamation text-danger" style="font-size:2.5rem; margin-bottom:1rem;"></i>
                <h3 style="color:#fff;">Unable to Load Vacancies</h3>
                <p style="color:var(--text-secondary); margin-bottom:1rem;">An unexpected network error occurred while querying the job database.</p>
                <button class="btn-primary" onclick="loadJobsFromAPI(${page})">Try Again</button>
            </div>
        `;
    }
}

function renderJobCardsList(jobs, container) {
    container.innerHTML = '';

    if (!jobs || jobs.length === 0) {
        container.innerHTML = `
            <div class="glass-panel" style="padding:3rem 2rem; text-align:center;">
                <i class="fa-solid fa-magnifying-glass" style="font-size:3rem; color:var(--text-muted); margin-bottom:1rem;"></i>
                <h3 style="color:#fff; margin-bottom:0.5rem;">No Matching Vacancies Found</h3>
                <p style="color:var(--text-secondary); max-width:480px; margin:0 auto 1.5rem auto;">
                    We couldn't find any job vacancies matching your active filter criteria. Try broadening your keywords or resetting filters.
                </p>
                <button class="btn-primary" onclick="resetAllJobFilters()">Reset All Filters</button>
            </div>
        `;
        return;
    }

    jobs.forEach(job => {
        const card = document.createElement('article');
        card.className = `job-card ${job.is_premium ? 'is-premium-card' : ''}`;

        const reqSkills = (job.skills_required || '').split(',').map(s => s.trim()).filter(Boolean);
        const matchedSet = new Set((job.matched_skills || []).map(s => s.toLowerCase()));

        const skillsHtml = reqSkills.map(sk => {
            const isMatch = matchedSet.has(sk.toLowerCase());
            return `<span class="skill-tag ${isMatch ? 'matched' : ''}">${isMatch ? '✓ ' : ''}${escapeHtml(sk)}</span>`;
        }).join('');

        const formattedSalMin = Number(job.salary_min).toLocaleString('en-IN');
        const formattedSalMax = Number(job.salary_max).toLocaleString('en-IN');

        const matchPct = job.match_pct || 50;
        const matchClass = matchPct >= 70 ? 'match-badge' : 'match-badge low';

        card.innerHTML = `
            <div class="job-card-header">
                <div class="card-title-group">
                    <div class="card-badges-row">
                        <span class="stream-badge"><i class="fa-solid fa-graduation-cap"></i> ${escapeHtml(job.stream)}</span>
                        ${job.is_urgent ? '<span class="urgent-badge"><i class="fa-solid fa-bolt"></i> Urgent Hiring</span>' : ''}
                        ${job.is_premium ? '<span class="badge-gold-star"><i class="fa-solid fa-crown text-gold"></i> Pro Priority</span>' : ''}
                        ${job.is_demo ? '<span class="demo-badge"><i class="fa-solid fa-flask"></i> Sample Record</span>' : ''}
                        <span class="${matchClass}" title="${escapeHtml((job.match_reasons || []).join(' • '))}">
                            <i class="fa-solid fa-bullseye"></i> ${matchPct}% Match
                        </span>
                    </div>
                    <h3><a href="/jobs/${job.id}" style="color:#fff;">${escapeHtml(job.title)}</a></h3>
                    <div class="company-line">
                        <span><i class="fa-regular fa-building"></i> ${escapeHtml(job.company)}</span>
                        ${job.is_verified && !job.is_demo 
                            ? '<span class="badge-verified"><i class="fa-solid fa-circle-check"></i> Verified Employer</span>' 
                            : (job.is_demo ? '<span class="badge-unverified"><i class="fa-solid fa-circle-info"></i> Simulation Data</span>' : '<span class="badge-unverified">Unverified</span>')}
                    </div>
                </div>
                <button class="btn-icon-action ${job.bookmarked ? 'active' : ''}" onclick="toggleJobBookmark(${job.id}, this)" title="Save Job">
                    <i class="${job.bookmarked ? 'fa-solid text-gold' : 'fa-regular'} fa-bookmark"></i>
                </button>
            </div>

            <div class="salary-location-row">
                <div class="salary-tag">
                    <i class="fa-solid fa-indian-rupee-sign"></i> ${formattedSalMin} - ${formattedSalMax} <span style="font-size:0.75rem; color:var(--text-muted); font-weight:600;">/ mo</span>
                </div>
                <div class="location-tag">
                    <i class="fa-solid fa-location-dot text-primary"></i> ${escapeHtml(job.city)} • ${escapeHtml(job.work_mode || 'Onsite')}
                </div>
                <div class="exp-tag">
                    <i class="fa-solid fa-briefcase text-secondary"></i> ${escapeHtml(job.experience)}
                </div>
                <div class="qual-tag">
                    <i class="fa-solid fa-user-graduate text-secondary"></i> ${escapeHtml(job.qualification)}
                </div>
            </div>

            <div class="job-skills-bar">
                <span style="font-size:0.75rem; font-weight:700; color:var(--text-muted);">Skills:</span>
                ${skillsHtml}
            </div>

            <p class="job-desc-snippet">${escapeHtml(job.description)}</p>

            <div class="card-actions-bar">
                <div class="actions-left">
                    ${job.applied 
                        ? `<button class="btn-apply-quick applied" disabled><i class="fa-solid fa-circle-check"></i> Applied to HR</button>` 
                        : `<button class="btn-apply-quick" onclick="openApplyModal(${job.id}, '${escapeHtml(job.title)}', '${escapeHtml(job.company)}')"><i class="fa-solid fa-bolt"></i> 1-Click Apply</button>`
                    }
                    <button class="btn-send-mail" onclick="openSendMailModal(${job.id}, '${escapeHtml(job.title)}', '${escapeHtml(job.company)}', '${escapeHtml(job.hr_email)}', '${escapeHtml(job.hr_phone)}')">
                        <i class="fa-regular fa-envelope"></i> Send Mail to HR
                    </button>
                    <a href="tel:${escapeHtml(job.hr_phone)}" class="btn-call-hr" title="Direct recruiter phone line">
                        <i class="fa-solid fa-phone"></i> Call HR
                    </a>
                </div>
                <div class="actions-right">
                    <a href="/jobs/${job.id}" class="btn-view-details">View Full Specs →</a>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderPaginationControls(page, totalPages) {
    const container = document.getElementById('paginationContainer');
    if (!container) return;

    if (totalPages <= 1) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'flex';
    container.innerHTML = '';

    // Prev Button
    const prevBtn = document.createElement('button');
    prevBtn.className = 'page-btn';
    prevBtn.innerHTML = '<i class="fa-solid fa-chevron-left"></i>';
    prevBtn.disabled = page <= 1;
    prevBtn.onclick = () => loadJobsFromAPI(page - 1);
    container.appendChild(prevBtn);

    // Page Numbers
    for (let p = 1; p <= totalPages; p++) {
        if (p === 1 || p === totalPages || (p >= page - 1 && p <= page + 1)) {
            const numBtn = document.createElement('button');
            numBtn.className = `page-btn ${p === page ? 'active' : ''}`;
            numBtn.textContent = p;
            numBtn.onclick = () => loadJobsFromAPI(p);
            container.appendChild(numBtn);
        } else if (p === page - 2 || p === page + 2) {
            const ellipsis = document.createElement('span');
            ellipsis.textContent = '...';
            ellipsis.style.color = 'var(--text-muted)';
            container.appendChild(ellipsis);
        }
    }

    // Next Button
    const nextBtn = document.createElement('button');
    nextBtn.className = 'page-btn';
    nextBtn.innerHTML = '<i class="fa-solid fa-chevron-right"></i>';
    nextBtn.disabled = page >= totalPages;
    nextBtn.onclick = () => loadJobsFromAPI(page + 1);
    container.appendChild(nextBtn);
}

// ==========================================
// Bookmark Toggle Action
// ==========================================

async function toggleJobBookmark(jobId, btn) {
    try {
        const res = await fetch(`/api/jobs/${jobId}/bookmark`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            }
        });

        if (res.status === 401) {
            showToast('Please sign in to save job bookmarks.', 'error');
            setTimeout(() => window.location.href = '/auth/login', 1200);
            return;
        }

        const data = await res.json();
        if (data.bookmarked !== undefined) {
            if (btn) {
                const icon = btn.querySelector('i');
                if (data.bookmarked) {
                    btn.classList.add('active');
                    if (icon) icon.className = 'fa-solid fa-bookmark text-gold';
                } else {
                    btn.classList.remove('active');
                    if (icon) icon.className = 'fa-regular fa-bookmark';
                }
            }
            showToast(data.message, data.bookmarked ? 'gold' : 'info');
        } else {
            showToast(data.error || 'Could not update bookmark', 'error');
        }
    } catch (e) {
        showToast('Network error saving job', 'error');
    }
}

// ==========================================
// 1-Click Instant Apply Modal Handlers
// ==========================================

function openApplyModal(jobId, title, company) {
    const modal = document.getElementById('applyModal');
    if (!modal) return;
    const jIdInput = document.getElementById('applyJobId');
    if (jIdInput) jIdInput.value = jobId;
    const titleEl = document.getElementById('applyModalJobTitle');
    if (titleEl) titleEl.textContent = title;
    const compEl = document.getElementById('applyModalCompany');
    if (compEl) compEl.textContent = company;
    modal.classList.add('active');
}

function closeApplyModal() {
    const modal = document.getElementById('applyModal');
    if (modal) modal.classList.remove('active');
}

async function handleApplySubmit(e) {
    e.preventDefault();
    const jobId = document.getElementById('applyJobId').value;
    const note = document.getElementById('applyCoverNote')?.value.trim() || '';
    const btn = document.getElementById('btnConfirmApply');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting to HR...';

    try {
        const res = await fetch(`/api/jobs/${jobId}/apply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify({ cover_note: note })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            closeApplyModal();
            // Refresh cards if on search page
            if (document.getElementById('jobCardsContainer')) {
                loadJobsFromAPI(currentPage);
            }
        } else {
            showToast(data.error || 'Application failed', 'error');
        }
    } catch (err) {
        showToast('Network error submitting application', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit Application to HR';
    }
}

// ==========================================
// Send Mail to HR Handlers
// ==========================================

function openSendMailModal(jobId, title, company, hrEmail, hrPhone) {
    const modal = document.getElementById('sendMailModal');
    if (!modal) return;
    document.getElementById('mailJobId').value = jobId;
    document.getElementById('mailModalJobTitle').textContent = title;
    document.getElementById('mailModalCompany').textContent = company;
    const recEmail = document.getElementById('mailRecipientEmail');
    if (recEmail) recEmail.value = hrEmail;
    const recPhone = document.getElementById('mailRecipientPhone');
    if (recPhone) recPhone.value = hrPhone;
    modal.classList.add('active');
}

function closeSendMailModal() {
    const modal = document.getElementById('sendMailModal');
    if (modal) modal.classList.remove('active');
}

async function handleSendMailSubmit(e) {
    e.preventDefault();
    const jobId = document.getElementById('mailJobId').value;
    const recipient = document.getElementById('mailRecipientEmail').value;
    const subject = document.getElementById('mailSubject').value;
    const message = document.getElementById('mailMessage').value;
    const btn = document.getElementById('btnSubmitMail');

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Dispatching Email...';

    try {
        const res = await fetch('/api/send-mail', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify({
                job_id: jobId,
                recipient_email: recipient,
                subject: subject,
                message: message
            })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            closeSendMailModal();
        } else {
            showToast(data.error || 'Failed to dispatch email', 'error');
        }
    } catch (err) {
        showToast('Network error sending email to HR', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Send Direct Email';
    }
}

// ==========================================
// Report Job Handlers
// ==========================================

function openReportJobModal(jobId, title, company) {
    const modal = document.getElementById('reportJobModal');
    if (!modal) return;
    document.getElementById('reportJobId').value = jobId;
    document.getElementById('reportModalTitle').textContent = `Report: ${title}`;
    document.getElementById('reportModalCompany').textContent = company;
    modal.classList.add('active');
}

function closeReportJobModal() {
    const modal = document.getElementById('reportJobModal');
    if (modal) modal.classList.remove('active');
}

async function handleReportJobSubmit(e) {
    e.preventDefault();
    const jobId = document.getElementById('reportJobId').value;
    const reason = document.getElementById('reportReason').value;
    const details = document.getElementById('reportDetails').value;
    const btn = document.getElementById('btnSubmitReport');

    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting Report...';

    try {
        const res = await fetch(`/api/jobs/${jobId}/report`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify({ reason: reason, details: details })
        });
        const data = await res.json();
        if (data.success) {
            showToast(data.message, 'success');
            closeReportJobModal();
        } else {
            showToast(data.error || 'Failed to submit report', 'error');
        }
    } catch (err) {
        showToast('Network error submitting report', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-shield-halved"></i> Submit Report to Moderation';
    }
}

// ==========================================
// Pro UPI Subscription & Payment State Machine
// ==========================================

function openSubscriptionModal() {
    const modal = document.getElementById('subscriptionModal');
    if (modal) modal.classList.add('active');
}

function closeSubscriptionModal() {
    const modal = document.getElementById('subscriptionModal');
    if (modal) modal.classList.remove('active');
}

function selectSubscriptionPlan(name, amount, cardEl) {
    selectedSubscriptionPlan = { name, amount };
    document.querySelectorAll('.plan-selection-card').forEach(c => {
        c.classList.remove('active');
        c.style.borderColor = 'var(--border)';
        c.style.background = 'var(--bg-card)';
    });

    if (cardEl) {
        cardEl.classList.add('active');
        cardEl.style.borderColor = 'var(--gold)';
        cardEl.style.background = 'rgba(251, 191, 36, 0.05)';
    }

    document.getElementById('selectedPlanName').value = name;
    document.getElementById('selectedPlanAmount').value = amount;

    // Update dynamic QR code
    const officialUpi = document.getElementById('officialUpiIdStr')?.textContent || '7770009027-2@axl';
    const qrImg = document.getElementById('upiQrCodeImg');
    if (qrImg) {
        const upiPayload = `upi://pay?pa=${encodeURIComponent(officialUpi)}&pn=Job%20Mitra&cu=INR&am=${amount}`;
        qrImg.src = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(upiPayload)}`;
    }
}

function copyUpiIdToClipboard() {
    const upiStr = document.getElementById('officialUpiIdStr')?.textContent || '7770009027-2@axl';
    navigator.clipboard.writeText(upiStr).then(() => {
        const textSpan = document.getElementById('copyUpiText');
        if (textSpan) textSpan.textContent = 'Copied!';
        showToast(`UPI ID "${upiStr}" copied to clipboard!`, 'gold');
        setTimeout(() => { if (textSpan) textSpan.textContent = 'Copy UPI'; }, 3000);
    }).catch(() => {
        showToast(`UPI ID: ${upiStr}`, 'info');
    });
}

async function handleProActivationSubmit(e) {
    e.preventDefault();
    const utrInput = document.getElementById('upiUtrInput');
    const utr = utrInput.value.trim();

    if (!utr || utr.length < 8) {
        showToast('Please enter a valid 12-digit UPI UTR reference ID.', 'error');
        return;
    }

    const btn = document.getElementById('btnSubmitUtr');
    btn.disabled = true;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting to Audit Ledger...';

    const payload = {
        utr_number: utr,
        plan_name: selectedSubscriptionPlan.name,
        amount: selectedSubscriptionPlan.amount
    };

    try {
        const res = await fetch('/api/subscription/activate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': getCsrfToken()
            },
            body: JSON.stringify(payload)
        });

        if (res.status === 401) {
            showToast('Please sign in to submit subscription payment references.', 'error');
            setTimeout(() => window.location.href = '/auth/login', 1200);
            return;
        }

        const data = await res.json();
        if (data.success) {
            utrInput.value = '';
            closeSubscriptionModal();
            showToast(data.message, 'gold');
        } else {
            showToast(data.error || 'Submission failed', 'error');
        }
    } catch (err) {
        showToast('Network error submitting payment reference', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Submit Reference for Verification';
    }
}
