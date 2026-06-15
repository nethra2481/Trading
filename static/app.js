const state = { reports: [], category: 'All' };

const els = {
    status: document.getElementById('system-status'),
    subscriberCount: document.getElementById('subscriber-count'),
    reportCount: document.getElementById('report-count'),
    schedule: document.getElementById('schedule'),
    integrations: document.getElementById('integrations'),
    logs: document.getElementById('logs'),
    reports: document.getElementById('reports'),
    form: document.getElementById('subscriber-form'),
    email: document.getElementById('email'),
    message: document.getElementById('subscriber-message'),
    modal: document.getElementById('pdf-modal'),
    frame: document.getElementById('pdf-frame'),
    modalTitle: document.getElementById('modal-title'),
    closeModal: document.getElementById('close-modal'),
};

function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, (char) => ({
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;',
    }[char]));
}

async function getJson(url, options) {
    const response = await fetch(url, options);
    if (!response.ok) throw new Error(`${url} failed`);
    return response.json();
}

function renderStatus(data) {
    els.subscriberCount.textContent = data.subscriber_count;
    els.status.textContent = data.subscriber_count ? 'System active' : 'Needs subscriber';
    els.status.classList.toggle('degraded', !data.subscriber_count);
    els.schedule.innerHTML = data.scheduler.map((item) => `
        <div class="timeline-row">
            <time>${escapeHtml(item.time)}</time>
            <div>
                <strong>${escapeHtml(item.label)}</strong>
                <p>${escapeHtml(item.delivery)}</p>
            </div>
            <span>Weekdays</span>
        </div>
    `).join('');
    els.integrations.innerHTML = Object.entries(data.integrations).map(([key, ready]) => `
        <div class="integration-row ${ready ? 'ready' : 'missing'}">
            <span>${escapeHtml(key.replaceAll('_', ' '))}</span>
            <strong>${ready ? 'Ready' : 'Config needed'}</strong>
        </div>
    `).join('');
    els.logs.innerHTML = data.latest_logs.length ? data.latest_logs.map((log) => `
        <div class="log-row ${log.status === 'SUCCESS' ? 'success' : 'failed'}">
            <div>
                <strong>${escapeHtml(log.report_type)}</strong>
                <p>${escapeHtml(log.email)} · ${escapeHtml(log.created_at)}</p>
            </div>
            <span>${escapeHtml(log.status)}</span>
        </div>
    `).join('') : '<div class="empty">No delivery logs yet.</div>';
}

function renderReports() {
    const reports = state.category === 'All'
        ? state.reports
        : state.reports.filter((report) => report.category === state.category);
    els.reportCount.textContent = `${reports.length} report${reports.length === 1 ? '' : 's'}`;
    if (!reports.length) {
        els.reports.innerHTML = '<div class="empty">No generated PDFs found for this category.</div>';
        return;
    }
    els.reports.innerHTML = reports.map((report) => `
        <button class="report-card" data-id="${report.id}" data-title="${escapeHtml(report.title)}">
            <span>${escapeHtml(report.category)}</span>
            <strong>${escapeHtml(report.title)}</strong>
            <p>${escapeHtml(report.created_at)}</p>
        </button>
    `).join('');
    document.querySelectorAll('.report-card').forEach((card) => {
        card.addEventListener('click', () => {
            els.modalTitle.textContent = card.dataset.title;
            els.frame.src = `/api/reports/${card.dataset.id}/download`;
            els.modal.showModal();
        });
    });
}

async function load() {
    try {
        renderStatus(await getJson('/api/status'));
        state.reports = await getJson('/api/reports');
        renderReports();
    } catch (error) {
        console.error(error);
        els.status.textContent = 'Status unavailable';
        els.status.classList.add('degraded');
    }
}

document.querySelectorAll('.nav-item').forEach((button) => {
    button.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach((item) => item.classList.remove('active'));
        button.classList.add('active');
        state.category = button.dataset.category;
        renderReports();
    });
});

els.form.addEventListener('submit', async (event) => {
    event.preventDefault();
    els.message.textContent = 'Saving...';
    try {
        await getJson('/api/subscribers', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: els.email.value }),
        });
        els.email.value = '';
        els.message.textContent = 'Subscriber saved.';
        await load();
    } catch (error) {
        els.message.textContent = 'Enter a valid email address.';
    }
});

els.closeModal.addEventListener('click', () => {
    els.modal.close();
    els.frame.src = '';
});

load();
setInterval(load, 60000);
