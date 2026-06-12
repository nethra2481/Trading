document.addEventListener('DOMContentLoaded', () => {
    // Landing Page Logic
    const enterBtn = document.getElementById('enter-btn');
    const landingScreen = document.getElementById('landing-screen');
    const dashboardScreen = document.getElementById('dashboard-screen');
    const emailInput = document.getElementById('client-email');
    const landingEmailGroup = document.getElementById('landing-email-group');

    function isValidEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    // If email already exists, keep landing visible but hide input box.
    // User can continue to dashboard from landing screen.
    if (localStorage.getItem('clientEmail')) {
        landingEmailGroup.classList.add('hidden');
    }

    enterBtn.addEventListener('click', async () => {
        const existingEmail = localStorage.getItem('clientEmail');
        const email = emailInput.value.trim();

        if (!existingEmail) {
            if (!email || !isValidEmail(email)) {
                alert("Please enter a valid client email address to proceed (e.g., client@example.com)");
                emailInput.focus();
                return;
            }

            const originalText = enterBtn.innerHTML;
            enterBtn.innerHTML = '<span>S A V I N G . . .</span>';

            try {
                const resp = await fetch('/api/set_email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                if (!resp.ok) {
                    throw new Error('Email save request failed');
                }
                // Save locally so they aren't asked again
                localStorage.setItem('clientEmail', email);
            } catch (e) {
                console.error("Failed to update email", e);
                alert("Failed to save email. Please try again.");
                return;
            } finally {
                enterBtn.innerHTML = originalText;
            }
        }

        landingScreen.classList.add('hidden');
        dashboardScreen.classList.add('visible');
        
        // Load reports once dashboard is visible
        loadReports();
    });

    // Dashboard Logic
    const reportsGrid = document.getElementById('reports-grid');
    const navItems = document.querySelectorAll('.nav-item');
    const modal = document.getElementById('pdf-modal');
    const closeModal = document.getElementById('close-modal');
    const iframe = document.getElementById('pdf-iframe');
    const modalTitle = document.getElementById('modal-title');
    
    let allReports = [];

    async function loadReports() {
        try {
            const response = await fetch('/api/reports');
            allReports = await response.json();
            renderReports(allReports);
        } catch (error) {
            console.error('Failed to fetch reports:', error);
            reportsGrid.innerHTML = '<p style="color: red;">Failed to load reports.</p>';
        }
    }

    function renderReports(reports) {
        reportsGrid.innerHTML = '';
        
        if (reports.length === 0) {
            reportsGrid.innerHTML = '<p style="color: var(--text-secondary);">No reports generated yet.</p>';
            return;
        }

        reports.forEach(report => {
            const card = document.createElement('div');
            card.className = 'report-card';
            card.innerHTML = `
                <div class="card-header">
                    <span class="category-tag tag-${report.category}">${report.category}</span>
                </div>
                <div class="report-title">${formatFilename(report.filename)}</div>
                <div class="report-date">${report.date_str}</div>
            `;
            
            card.addEventListener('click', () => openPdf(report));
            reportsGrid.appendChild(card);
        });
    }

    function formatFilename(filename) {
        return filename.replace('.pdf', '').replace(/_/g, ' ');
    }

    // Filtering logic
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            navItems.forEach(nav => nav.classList.remove('active'));
            e.target.classList.add('active');
            
            const category = e.target.dataset.category;
            if (category === 'All') {
                renderReports(allReports);
            } else {
                const filtered = allReports.filter(r => r.category === category);
                renderReports(filtered);
            }
        });
    });

    // Modal Logic
    function openPdf(report) {
        modalTitle.textContent = formatFilename(report.filename);
        iframe.src = `/api/reports/${report.filename}`;
        modal.showModal();
    }

    closeModal.addEventListener('click', () => {
        modal.close();
        iframe.src = '';
    });

    // Close modal on outside click
    modal.addEventListener('click', (e) => {
        const dialogDimensions = modal.getBoundingClientRect()
        if (
            e.clientX < dialogDimensions.left ||
            e.clientX > dialogDimensions.right ||
            e.clientY < dialogDimensions.top ||
            e.clientY > dialogDimensions.bottom
        ) {
            modal.close();
            iframe.src = '';
        }
    });

    // Settings Modal Logic
    const profileBtn = document.getElementById('profile-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsBtn = document.getElementById('close-settings-modal');
    const saveSettingsBtn = document.getElementById('save-settings-btn');
    const updateEmailInput = document.getElementById('update-client-email');

    if (profileBtn) {
        profileBtn.addEventListener('click', () => {
            updateEmailInput.value = localStorage.getItem('clientEmail') || '';
            settingsModal.showModal();
        });
    }

    if (closeSettingsBtn) {
        closeSettingsBtn.addEventListener('click', () => {
            settingsModal.close();
        });
    }

    if (saveSettingsBtn) {
        saveSettingsBtn.addEventListener('click', async () => {
            const email = updateEmailInput.value.trim();
            if (!email || !isValidEmail(email)) {
                alert("Please enter a valid client email address");
                updateEmailInput.focus();
                return;
            }

            const originalText = saveSettingsBtn.innerHTML;
            saveSettingsBtn.innerHTML = '<span>S A V I N G . . .</span>';

            try {
                await fetch('/api/set_email', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ email })
                });
                
                localStorage.setItem('clientEmail', email);
                
                setTimeout(() => {
                    saveSettingsBtn.innerHTML = '<span>Saved!</span>';
                    setTimeout(() => {
                        saveSettingsBtn.innerHTML = originalText;
                        settingsModal.close();
                    }, 1000);
                }, 500);

            } catch (e) {
                console.error("Failed to update email", e);
                saveSettingsBtn.innerHTML = originalText;
            }
        });
    }
});
