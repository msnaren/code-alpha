/**
 * Simple E-Commerce Store - Main Application Script
 * Vanilla JavaScript (No external libraries)
 */

document.addEventListener('DOMContentLoaded', () => {
  initUserDropdown();
  initAlertDismissal();
  initLocalStorageSync();
  initToastShelf();
});

/**
 * User profile dropdown toggle in navigation bar
 */
function initUserDropdown() {
  const userBtn = document.getElementById('user-menu-btn');
  const userDropdown = document.getElementById('user-dropdown');

  if (userBtn && userDropdown) {
    userBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle('show');
    });

    document.addEventListener('click', (e) => {
      if (!userDropdown.contains(e.target) && !userBtn.contains(e.target)) {
        userDropdown.classList.remove('show');
      }
    });
  }
}

/**
 * Auto-dismiss flash message alerts after 5 seconds
 */
function initAlertDismissal() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    // Close button
    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 250);
      });
    }

    // Auto-dismiss after 6s
    setTimeout(() => {
      if (document.body.contains(alert)) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 250);
      }
    }, 6000);
  });
}

/**
 * Initialize floating toast shelf container
 */
function initToastShelf() {
  if (!document.getElementById('toast-shelf')) {
    const shelf = document.createElement('div');
    shelf.id = 'toast-shelf';
    shelf.className = 'toast-shelf';
    document.body.appendChild(shelf);
  }
}

/**
 * Display a floating toast notification
 */
window.showToast = function(message, type = 'success') {
  let shelf = document.getElementById('toast-shelf');
  if (!shelf) {
    shelf = document.createElement('div');
    shelf.id = 'toast-shelf';
    shelf.className = 'toast-shelf';
    document.body.appendChild(shelf);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;

  const iconSvg = type === 'success' 
    ? `<svg width="18" height="18" fill="none" stroke="#10b981" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7"/></svg>`
    : `<svg width="18" height="18" fill="none" stroke="#ef4444" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>`;

  toast.innerHTML = `
    <span class="toast-icon">${iconSvg}</span>
    <span class="toast-msg">${message}</span>
  `;

  shelf.appendChild(toast);

  // Auto remove after 3.5s
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px) scale(0.95)';
    toast.style.transition = 'all 0.25s ease';
    setTimeout(() => toast.remove(), 250);
  }, 3500);
};

/**
 * Update the cart badge count in the header
 */
window.updateCartBadge = function(count) {
  const badge = document.getElementById('header-cart-badge');
  if (badge) {
    badge.textContent = count;
    // Little bump animation
    badge.style.transform = 'scale(1.35)';
    setTimeout(() => {
      badge.style.transform = 'scale(1)';
    }, 200);
  }
};

/**
 * Synchronize session cart data with localStorage for guests
 */
function initLocalStorageSync() {
  fetch('/cart/api/data/')
    .then(res => res.json())
    .then(data => {
      if (data && typeof data.total_count !== 'undefined') {
        localStorage.setItem('ecommerce_cart', JSON.stringify(data));
        updateCartBadge(data.total_count);
      }
    })
    .catch(() => {
      // Offline fallback: load from localStorage
      const cached = localStorage.getItem('ecommerce_cart');
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          if (parsed.total_count) updateCartBadge(parsed.total_count);
        } catch (e) {}
      }
    });
}

/**
 * Helper to get CSRF token from cookie or DOM
 */
window.getCSRFToken = function() {
  const input = document.querySelector('[name=csrfmiddlewaretoken]');
  if (input) return input.value;

  const cookieValue = document.cookie
    .split('; ')
    .find(row => row.startsWith('csrftoken='))
    ?.split('=')[1];
  return cookieValue || '';
};
