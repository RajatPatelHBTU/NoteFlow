/**
 * NoteFlow — app.js
 * Minimal vanilla JS: dark mode, toast notifications, sidebar, HTMX hooks.
 */

// ── Dark Mode ─────────────────────────────────────────────────────────────────

function toggleDarkMode() {
  const html = document.documentElement;
  if (html.classList.contains('dark')) {
    html.classList.remove('dark');
    localStorage.setItem('theme', 'light');
  } else {
    html.classList.add('dark');
    localStorage.setItem('theme', 'dark');
  }
}

// ── Mobile Sidebar ────────────────────────────────────────────────────────────

function openSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar && overlay) {
    sidebar.classList.remove('-translate-x-full');
    sidebar.classList.add('translate-x-0');
    overlay.classList.remove('hidden');
  }
}

function closeSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  if (sidebar && overlay) {
    sidebar.classList.add('-translate-x-full');
    sidebar.classList.remove('translate-x-0');
    overlay.classList.add('hidden');
  }
}

// Close sidebar on resize to desktop
window.addEventListener('resize', () => {
  if (window.innerWidth >= 1024) {
    closeSidebar();
  }
});

// ── Modal ─────────────────────────────────────────────────────────────────────

function closeModal() {
  const container = document.getElementById('modal-container');
  if (container) {
    container.innerHTML = '';
  }
}

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    closeModal();
  }
});

// ── Toast Notifications ───────────────────────────────────────────────────────

function showToast(message, type = 'success') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const icons = {
    success: `<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>`,
    error:   `<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>`,
    info:    `<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>`,
    warning: `<svg class="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>`,
  };

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    ${icons[type] || icons.info}
    <span class="flex-1">${message}</span>
    <button onclick="this.parentElement.remove()" 
            class="opacity-60 hover:opacity-100 transition-opacity ml-1 flex-shrink-0"
            aria-label="Dismiss">
      <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
    </button>
  `;

  container.appendChild(toast);

  // Auto-remove after 4 seconds
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    setTimeout(() => toast.remove(), 400);
  }, 4000);
}

// ── HTMX Event Hooks ──────────────────────────────────────────────────────────

// Listen for showToast custom event from HX-Trigger response headers
document.addEventListener('showToast', (e) => {
  const { message, type } = e.detail;
  if (message) showToast(message, type || 'success');
});

// HTMX request error handler
document.addEventListener('htmx:responseError', (e) => {
  const status = e.detail.xhr.status;
  const msg = status === 404 ? 'Not found.'
            : status === 422 ? 'Validation error. Please check your input.'
            : status >= 500  ? 'Server error. Please try again.'
            : 'Request failed.';
  showToast(msg, 'error');
});

// Loading indicator on HTMX requests
document.addEventListener('htmx:beforeRequest', () => {
  document.body.style.cursor = 'progress';
});
document.addEventListener('htmx:afterRequest', () => {
  document.body.style.cursor = '';
});

// Refresh sidebar stats after any note mutation
document.addEventListener('htmx:afterRequest', (e) => {
  const path = e.detail.requestConfig?.path || '';
  const method = e.detail.requestConfig?.verb || '';
  const isMutation = ['post', 'put', 'delete', 'patch'].includes(method.toLowerCase());
  if (isMutation && path.includes('/htmx/notes')) {
    // Update sidebar counts
    htmx.ajax('GET', '/htmx/sidebar-stats', {
      target: '#sidebar-total-count',
      swap: 'outerHTML',
    });
  }
});

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  // Sync sort select value from URL
  const url = new URL(window.location.href);
  const sortParam = url.searchParams.get('sort');
  const sortSelect = document.getElementById('sort-select');
  if (sortSelect && sortParam) {
    sortSelect.value = sortParam;
  }
});
