/**
 * Simple E-Commerce Store - Cart Interaction Script
 * Handles quantity adjustments, AJAX adding, and live total calculations
 */

document.addEventListener('DOMContentLoaded', () => {
  initQuantitySteppers();
  initAjaxAddToCart();
});

/**
 * Initialize quantity steppers (+ / - buttons)
 */
function initQuantitySteppers() {
  document.querySelectorAll('.quantity-stepper').forEach(stepper => {
    const decBtn = stepper.querySelector('.btn-dec');
    const incBtn = stepper.querySelector('.btn-inc');
    const input = stepper.querySelector('.stepper-input');

    if (!input) return;

    const maxStock = parseInt(input.getAttribute('max') || '999', 10);
    const minVal = parseInt(input.getAttribute('min') || '1', 10);

    if (decBtn) {
      decBtn.addEventListener('click', (e) => {
        e.preventDefault();
        let val = parseInt(input.value || '1', 10);
        if (val > minVal) {
          input.value = val - 1;
          input.dispatchEvent(new Event('change'));
        }
      });
    }

    if (incBtn) {
      incBtn.addEventListener('click', (e) => {
        e.preventDefault();
        let val = parseInt(input.value || '1', 10);
        if (val < maxStock) {
          input.value = val + 1;
          input.dispatchEvent(new Event('change'));
        } else {
          window.showToast?.(`Maximum available stock is ${maxStock}`, 'info');
        }
      });
    }

    input.addEventListener('change', () => {
      let val = parseInt(input.value, 10);
      if (isNaN(val) || val < minVal) input.value = minVal;
      if (val > maxStock) {
        input.value = maxStock;
        window.showToast?.(`Adjusted to maximum available stock (${maxStock})`, 'info');
      }
    });
  });
}

/**
 * Intercept Add-to-Cart form submissions to provide instant AJAX feedback
 */
function initAjaxAddToCart() {
  document.querySelectorAll('.ajax-add-cart-form').forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();

      const submitBtn = form.querySelector('button[type="submit"]');
      const originalText = submitBtn ? submitBtn.innerHTML : '';
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span>Adding...</span>`;
      }

      const formData = new FormData(form);
      const actionUrl = form.getAttribute('action');

      fetch(actionUrl, {
        method: 'POST',
        headers: {
          'x-requested-with': 'XMLHttpRequest',
          'X-CSRFToken': window.getCSRFToken(),
        },
        body: formData,
      })
      .then(res => res.json())
      .then(data => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }

        if (data.success) {
          window.showToast?.(data.message || 'Item added to your cart!', 'success');
          if (data.cart) {
            window.updateCartBadge?.(data.cart.total_count);
            localStorage.setItem('ecommerce_cart', JSON.stringify(data.cart));
          }
        } else {
          window.showToast?.(data.message || 'Could not add item to cart.', 'error');
        }
      })
      .catch(err => {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = originalText;
        }
        // Fallback to standard form submit if fetch fails
        form.submit();
      });
    });
  });
}
