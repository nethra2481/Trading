document.addEventListener('DOMContentLoaded', () => {

    const reportsGrid = document.getElementById('reports-grid');
    const navItems = document.querySelectorAll('.nav-item');
    const modal = document.getElementById('pdf-modal');
    const closeModal = document.getElementById('close-modal');
    const iframe = document.getElementById('pdf-iframe');
    const modalTitle = document.getElementById('modal-title');

    let allReports = [];

    // Load reports immediately
    loadReports();

    // Auto-refresh every 60 seconds
    setInterval(loadReports, 60000);

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
            reportsGrid.innerHTML = '<div class="no-reports"><p>No reports yet. First reports will be generated at 9:00 AM IST on the next trading day.</p></div>';
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
                <div class="card-cta">View Report &rarr;</div>
            `;
            card.addEventListener('click', () => {
                modalTitle.textContent = formatFilename(report.filename);
                iframe.src = `/api/reports/${report.filename}`;
                modal.showModal();
            });
            reportsGrid.appendChild(card);
        });
    }

    // Nav filtering — use currentTarget so clicking inner <span> still reads the button
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            const btn = e.currentTarget;
            navItems.forEach(n => n.classList.remove('active'));
            btn.classList.add('active');
            const cat = btn.dataset.category;
            renderReports(cat === 'All' ? allReports : allReports.filter(r => r.category === cat));
        });
    });

    // Modal close button
    if (closeModal) {
        closeModal.addEventListener('click', () => {
            modal.close();
            iframe.src = '';
        });
    }

    // Close modal when clicking backdrop
    if (modal) {
        modal.addEventListener('click', (e) => {
            const rect = modal.getBoundingClientRect();
            if (e.clientX < rect.left || e.clientX > rect.right ||
                e.clientY < rect.top  || e.clientY > rect.bottom) {
                modal.close();
                iframe.src = '';
            }
        });
    }
});
