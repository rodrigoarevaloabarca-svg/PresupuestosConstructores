/**
 * Autocomplete de sugerencias de ferreterías para campos de descripción de materiales.
 * Conecta con /api/v1/productos/sugerencias/?q=...
 */
(function () {
  'use strict';

  const API_URL = '/api/v1/productos/sugerencias/';
  const DEBOUNCE_MS = 300;
  const MIN_CHARS = 3;
  const BADGE_CLASSES = {
    catalog: 'ac-badge-catalog',
    sodimac: 'ac-badge-sodimac',
    easy: 'ac-badge-easy',
    imperial: 'ac-badge-imperial',
  };
  const BADGE_LABELS = {
    catalog: 'Mi catálogo',
    sodimac: 'Sodimac',
    easy: 'Easy',
    imperial: 'Imperial',
  };

  function getCsrf() {
    return document.cookie.split(';').map(c => c.trim()).find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
  }

  function debounce(fn, ms) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
  }

  function buildDropdown(items, input, onSelect) {
    removeDropdown();
    if (!items.length) return;

    const wrap = input.closest('.material-row') || input.parentElement;
    wrap.style.position = 'relative';

    const drop = document.createElement('div');
    drop.className = 'ac-dropdown';
    drop.id = 'ac-drop';

    const groups = { catalog: [], retailer: [] };
    items.forEach(item => (item.source === 'catalog' ? groups.catalog : groups.retailer).push(item));

    let focusIndex = -1;
    const allItems = [];

    function renderGroup(label, list) {
      if (!list.length) return;
      const lbl = document.createElement('div');
      lbl.className = 'ac-group-label';
      lbl.textContent = label;
      drop.appendChild(lbl);

      list.forEach(p => {
        const el = document.createElement('div');
        el.className = 'ac-item';
        el.setAttribute('role', 'option');
        const badge = `<span class="ac-badge ${BADGE_CLASSES[p.source] || ''}">${BADGE_LABELS[p.source] || p.source}</span>`;
        const link = p.url ? `<a href="${p.url}" target="_blank" rel="noopener" class="ac-link" onclick="event.stopPropagation()">↗</a>` : '';
        el.innerHTML = `
          <span class="ac-item-name" title="${p.name}">${p.name}</span>
          ${badge}
          <span class="ac-item-price">$${Number(p.price).toLocaleString('es-CL')}</span>
          ${link}`;
        el.addEventListener('mousedown', e => {
          e.preventDefault();
          onSelect(p);
          removeDropdown();
        });
        drop.appendChild(el);
        allItems.push(el);
      });
    }

    renderGroup('Mi catálogo', groups.catalog);
    renderGroup('Ferreterías', groups.retailer);

    const tip = document.createElement('div');
    tip.className = 'ac-tooltip';
    tip.textContent = 'Precio de referencia de tienda — ajusta tu margen antes de guardar';
    drop.appendChild(tip);

    wrap.appendChild(drop);

    // Keyboard nav
    input._acKeyHandler = e => {
      const rows = allItems;
      if (e.key === 'Escape') { removeDropdown(); return; }
      if (e.key === 'ArrowDown') { e.preventDefault(); focusIndex = Math.min(focusIndex + 1, rows.length - 1); rows.forEach((r, i) => r.classList.toggle('ac-focused', i === focusIndex)); }
      if (e.key === 'ArrowUp')   { e.preventDefault(); focusIndex = Math.max(focusIndex - 1, 0); rows.forEach((r, i) => r.classList.toggle('ac-focused', i === focusIndex)); }
      if (e.key === 'Enter' && focusIndex >= 0) { e.preventDefault(); rows[focusIndex].dispatchEvent(new Event('mousedown')); }
    };
    input.addEventListener('keydown', input._acKeyHandler);
  }

  function removeDropdown() {
    document.getElementById('ac-drop')?.remove();
  }

  function attachAutocomplete(nameInput) {
    if (nameInput.dataset.acAttached) return;
    nameInput.dataset.acAttached = '1';

    const fetchSuggestions = debounce(async (q) => {
      if (q.length < MIN_CHARS) { removeDropdown(); return; }
      try {
        const res = await fetch(`${API_URL}?q=${encodeURIComponent(q)}&limit=8`, {
          headers: { 'X-CSRFToken': getCsrf() },
        });
        if (!res.ok) return;
        const items = await res.json();
        buildDropdown(items, nameInput, p => {
          nameInput.value = p.name;
          const row = nameInput.closest('.material-row');
          if (row && p.price) {
            const priceInput = row.querySelector('.mat-price');
            if (priceInput) { priceInput.value = p.price; priceInput.dispatchEvent(new Event('input')); }
          }
          nameInput.dispatchEvent(new Event('input'));
        });
      } catch (_) {}
    }, DEBOUNCE_MS);

    nameInput.addEventListener('input', e => fetchSuggestions(e.target.value.trim()));
    nameInput.addEventListener('blur', () => setTimeout(removeDropdown, 150));
  }

  function observeMaterialRows() {
    function attach() {
      document.querySelectorAll('.material-row input[name="mat_name[]"]').forEach(attachAutocomplete);
    }
    attach();
    const observer = new MutationObserver(attach);
    const container = document.getElementById('material-rows');
    if (container) observer.observe(container, { childList: true, subtree: true });
  }

  document.addEventListener('DOMContentLoaded', observeMaterialRows);
  document.addEventListener('click', e => { if (!e.target.closest('#ac-drop') && !e.target.closest('[name="mat_name[]"]')) removeDropdown(); });
})();
