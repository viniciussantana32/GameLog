/**
 * Meus Jogos - Scripts Globais (main.js)
 * Gerenciamento de menu responsivo, dismiss de alertas e utilitários globais
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Menu Mobile Toggle
    const mobileToggle = document.querySelector('.mobile-toggle');
    const sidebar = document.querySelector('.site-sidebar');
    const appShell = document.querySelector('.app-shell');
    const sidebarBackdrop = document.querySelector('.sidebar-backdrop');

    const setSidebarOpen = (isOpen) => {
        if (!sidebar || !appShell || !mobileToggle) return;
        sidebar.classList.toggle('open', isOpen);
        appShell.classList.toggle('sidebar-open', isOpen);
        mobileToggle.setAttribute('aria-expanded', isOpen);
    };

    if (mobileToggle && sidebar) {
        mobileToggle.addEventListener('click', () => {
            setSidebarOpen(!sidebar.classList.contains('open'));
        });
    }

    if (sidebarBackdrop) {
        sidebarBackdrop.addEventListener('click', () => setSidebarOpen(false));
    }

    // 2. Fechamento de Alertas Flash
    const alertCloseButtons = document.querySelectorAll('.alert-close');
    alertCloseButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const alertElement = btn.closest('.alert');
            if (alertElement) {
                alertElement.style.opacity = '0';
                setTimeout(() => alertElement.remove(), 250);
            }
        });
    });

    // Auto-dismiss de alertas de sucesso após 6 segundos
    const successAlerts = document.querySelectorAll('.alert-success');
    successAlerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.4s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 400);
        }, 6000);
    });

    // 3. Fechamento de modais com a tecla ESC
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            setSidebarOpen(false);
            const activeModal = document.querySelector('.modal-overlay.active');
            if (activeModal) {
                activeModal.classList.remove('active');
            }
        }
    });
});
