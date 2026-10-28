// FarmConnect - Unified Frontend JavaScript
// Features: Theme Toggle (Dark/Light), Dynamic Cart Totals, Live Calculators, Location Dropdown

document.addEventListener('DOMContentLoaded', function () {
  initThemeToggle();
  initCartCalculations();
  initProductDetailCalculator();
  initAutoDismissAlerts();
  initLocationSelector();
});

// 1. Theme Toggle (Dark / Light Mode)
function initThemeToggle() {
  const toggleBtn = document.getElementById('theme-toggle-btn');
  if (!toggleBtn) return;

  const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
  if (typeof updateThemeToggleUI === 'function') {
    updateThemeToggleUI(currentTheme);
  }

  // Avoid duplicate handlers if onclick is defined on button
  if (!toggleBtn.getAttribute('onclick') && typeof toggleFarmConnectTheme === 'function') {
    toggleBtn.addEventListener('click', toggleFarmConnectTheme);
  }
}

// 2. Dynamic Cart Total & Subtotal Calculations
function initCartCalculations() {
  const cartRows = document.querySelectorAll('.cart-item-row');
  const grandTotalDisplay = document.getElementById('cart-grand-total');

  if (!cartRows.length) return;

  function recalculateGrandTotal() {
    let grandTotal = 0;
    document.querySelectorAll('.cart-item-row').forEach(row => {
      const subtotalEl = row.querySelector('.item-subtotal');
      if (subtotalEl) {
        const val = parseFloat(subtotalEl.getAttribute('data-subtotal')) || 0;
        grandTotal += val;
      }
    });

    if (grandTotalDisplay) {
      grandTotalDisplay.innerText = `₹${grandTotal.toFixed(2)}`;
    }
  }

  cartRows.forEach(row => {
    const itemId = row.getAttribute('data-item-id');
    const price = parseFloat(row.getAttribute('data-price')) || 0;
    const maxStock = parseFloat(row.getAttribute('data-stock')) || 999;
    const qtyInput = row.querySelector('.cart-qty-input');
    const btnMinus = row.querySelector('.btn-qty-minus');
    const btnPlus = row.querySelector('.btn-qty-plus');
    const subtotalEl = row.querySelector('.item-subtotal');

    function updateRow(newQty) {
      if (isNaN(newQty) || newQty < 1) newQty = 1;
      if (newQty > maxStock) {
        alert(`Maximum stock available for this item is ${maxStock}`);
        newQty = maxStock;
      }

      qtyInput.value = newQty;
      const subtotal = newQty * price;
      if (subtotalEl) {
        subtotalEl.setAttribute('data-subtotal', subtotal);
        subtotalEl.innerText = `₹${subtotal.toFixed(2)}`;
      }
      recalculateGrandTotal();

      // Sync with backend via AJAX
      syncCartAjax(itemId, newQty);
    }

    if (btnMinus) {
      btnMinus.addEventListener('click', () => {
        let current = parseFloat(qtyInput.value) || 1;
        updateRow(current - 1);
      });
    }

    if (btnPlus) {
      btnPlus.addEventListener('click', () => {
        let current = parseFloat(qtyInput.value) || 1;
        updateRow(current + 1);
      });
    }

    if (qtyInput) {
      qtyInput.addEventListener('change', () => {
        let current = parseFloat(qtyInput.value) || 1;
        updateRow(current);
      });
    }
  });
}

// Sync cart change to backend via Fetch API
function syncCartAjax(itemId, quantity) {
  const csrfToken = getCookie('csrftoken');
  const formData = new FormData();
  formData.append('item_id', itemId);
  formData.append('quantity', quantity);

  fetch('/cart/update-ajax/', {
    method: 'POST',
    headers: {
      'X-CSRFToken': csrfToken
    },
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        const badge = document.querySelector('.cart-badge');
        if (badge) {
          badge.innerText = data.cart_count;
        }
      }
    })
    .catch(err => console.error('Error updating cart:', err));
}

// 3. Product Detail Subtotal Calculator
function initProductDetailCalculator() {
  const detailQtyInput = document.getElementById('detail-quantity-input');
  const detailPriceEl = document.getElementById('detail-unit-price');
  const detailTotalDisplay = document.getElementById('detail-total-display');

  if (detailQtyInput && detailPriceEl && detailTotalDisplay) {
    const unitPrice = parseFloat(detailPriceEl.getAttribute('data-price')) || 0;
    const maxStock = parseFloat(detailQtyInput.getAttribute('max')) || 999;

    function recalcDetail() {
      let qty = parseFloat(detailQtyInput.value) || 1;
      if (qty > maxStock) qty = maxStock;
      if (qty < 0.5) qty = 0.5;
      const total = qty * unitPrice;
      detailTotalDisplay.innerText = `₹${total.toFixed(2)}`;
    }

    detailQtyInput.addEventListener('input', recalcDetail);
    recalcDetail();
  }
}

// 4. Location quick selector helper
function initLocationSelector() {
  const locationSelect = document.getElementById('browse-location-select');
  if (locationSelect) {
    locationSelect.addEventListener('change', function () {
      this.form.submit();
    });
  }
}

// 5. Auto-dismiss alerts
function initAutoDismissAlerts() {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.5s ease';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 500);
    }, 6000);
  });
}

// Helper to get Django CSRF Cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
