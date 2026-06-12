document.addEventListener('DOMContentLoaded', () => {

    const landingScreen = document.getElementById('landing-screen');
    const dashboardScreen = document.getElementById('dashboard-screen');
    const enterBtn = document.getElementById('enter-btn');
    const emailInput = document.getElementById('client-email');
    const reportsGrid = document.getElementById('reports-grid');
    const navItems = document.querySelectorAll('.nav-item');
    const modal = document.getElementById('pdf-modal');
    const closeModal = document.getElementById('close-modal');
    const iframe = document.getElementById('pdf-iframe');
    const modalTitle = document.getElementById('modal-title');
    const profileBtn = document.getElementById('profile-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsBtn = document.getElementById('close-settings-modal');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const updateEmailInput = document.getElementById('update-client-email');

    let allReports = [];
    let refreshInterval = null;

    function isValidEmail(email) {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
    }

    function showDashboard() {
        landingScreen.style.display = 'none';
        dashboardScreen.style.display = 'flex';
        loadReports();
        if (!refreshInterval) {
            refreshInterval = setInterval(loadReports, 60000);
        }
    }

    // Auto-bypass if email already saved
    if (localStorage.getItem('clientEmail')) {
        showDashboard();
    }

    // Login button click
    enterBtn.addEventListener('click', async () => {
        const email = emailInput.value.trim();
        if (!email || !isValidEmail(email)) {
            alert('Please enter a valid email address.');
            emailInput.focus();
            return;
        }

        enterBtn.textContent = 'Connecting...';
        enterBtn.disabled = true;

        try {
            const resp = await fetch('/api/set_email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email })
            });
            if (!resp.ok) throw new Error('Server error');
            localStorage.setItem('clientEmail', email);
            showDashboard();
        } catch (e) {
            alert('Failed to connect. Please try again.');
            enterBtn.textContent = 'Access Terminal';
            enterBtn.disabled = false;
        }
    });

    // Load reports from backend
    async function loadReports() {
        try {
            const response = await fetch('/api/reports');
            allReports = await response.json();
            renderReports(allReports);
        } catch (error) {
            console.error('Failed to fetch reports:', error);
        }
    }

    function formatFilename(filename) {
        return filename.replace('.pdf', '').replace(/_/g, ' ');
    }

    function renderReports(reports) {
        const countEl = document.getElementById('report-count');
        if (countEl) countEl.textContent = reports.length + ' reports';
        reportsGrid.innerHTML = '';
        if (reports.length === 0) {
            reportsGrid.innerHTML = '<div class="no-reports"><p>No reports yet. First reports will be generated at 9:00 AM IST.</p></div>';
            return;
        }
        reports.forEach(report => {
            const card = document.createElement('div');
            card.className = 'report-card';
            card.innerHTML = `
                <div class="card-header">
                    <span class="category-tag tag-${report.category}">${report.category}</span>
                    <span class="report-date">${report.date_str}</span>
                </div>
                <div class="report-title">${formatFilename(report.filename)}</div>
                <div class="card-footer">View Report &rarr;</div>
            `;
            card.addEventListener('click', () => {
                modalTitle.textContent = formatFilename(report.filename);
                iframe.src = `/api/reports/${report.filename}`;
                modal.showModal();
            });
            reportsGrid.appendChild(card);
        });
    }

    // Nav filtering
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            navItems.forEach(n => n.classList.remove('active'));
            e.target.classList.add('active');
            const cat = e.target.dataset.category;
            renderReports(cat === 'All' ? allReports : allReports.filter(r => r.category === cat));
        });
    });

    // Modal close
    closeModal.addEventListener('click', () => { modal.close(); iframe.src = ''; });
    modal.addEventListener('click', (e) => {
        const rect = modal.getBoundingClientRect();
        if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) {
            modal.close(); iframe.src = '';
        }
    });

    // Settings modal
    if (profileBtn) {
        profileBtn.addEventListener('click', () => {
            updateEmailInput.value = localStorage.getItem('clientEmail') || '';
            settingsModal.showModal();
        });
    }
    if (closeSettingsBtn) closeSettingsBtn.addEventListener('click', () => settingsModal.close());
    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', async () => {
            const email = updateEmailInput.value.trim();
            if (!email || !isValidEmail(email)) { alert('Please enter a valid email.'); return; }
            saveSettingsBtn.textContent = 'Saving...';
            try {
                await fetch('/api/set_email', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email }) });
                localStorage.setItem('clientEmail', email);
                saveSettingsBtn.textContent = 'Saved!';
                setTimeout(() => { saveSettingsBtn.innerHTML = '<span>Update Email</span>'; settingsModal.close(); }, 1200);
            } catch (e) { saveSettingsBtn.innerHTML = '<span>Update Email</span>'; }
        });
    }
});
