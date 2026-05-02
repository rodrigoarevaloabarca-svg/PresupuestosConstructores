const UNIT_LABELS = { un:'un', m2:'m²', m3:'m³', ml:'ml', kg:'kg', lt:'lt', hr:'hr', gl:'gl', bls:'bls', pk:'pk' };

const RECIPES = [
  {
    id: 'pintura_interior',
    name: 'Pintura interior (2 manos)',
    rubro: 'Pintura',
    icon: '🎨',
    inputs: [
      { id: 'area', label: 'Superficie a pintar', unit: 'm²', placeholder: 'Ej: 45' }
    ],
    items(v) {
      return [
        { name: 'Pintura látex interior', unit: 'lt', qty: Math.ceil(v.area * 0.25) },
        { name: 'Sellador / Fondo', unit: 'lt', qty: Math.ceil(v.area * 0.10) },
        { name: 'Lija N°100', unit: 'un', qty: Math.ceil(v.area / 5) },
        { name: 'Cinta de pintor', unit: 'un', qty: Math.max(1, Math.ceil(v.area / 20)) },
      ];
    }
  },
  {
    id: 'pintura_exterior',
    name: 'Pintura exterior (3 manos)',
    rubro: 'Pintura',
    icon: '🎨',
    inputs: [
      { id: 'area', label: 'Superficie a pintar', unit: 'm²', placeholder: 'Ej: 80' }
    ],
    items(v) {
      return [
        { name: 'Pintura látex exterior', unit: 'lt', qty: Math.ceil(v.area * 0.38) },
        { name: 'Sellador / Impermeabilizante', unit: 'lt', qty: Math.ceil(v.area * 0.12) },
        { name: 'Lija N°80', unit: 'un', qty: Math.ceil(v.area / 4) },
        { name: 'Cinta de pintor', unit: 'un', qty: Math.max(1, Math.ceil(v.area / 15)) },
      ];
    }
  },
  {
    id: 'ceramica_piso',
    name: 'Cerámica / Porcelanato piso',
    rubro: 'Cerámica',
    icon: '🟫',
    inputs: [
      { id: 'area', label: 'Superficie', unit: 'm²', placeholder: 'Ej: 20' }
    ],
    items(v) {
      return [
        { name: 'Cerámica de piso', unit: 'm2', qty: Math.ceil(v.area * 1.10) },
        { name: 'Adhesivo para cerámica', unit: 'kg', qty: Math.ceil(v.area * 5) },
        { name: 'Fragüe / Junta', unit: 'kg', qty: Math.ceil(v.area * 0.5) },
        { name: 'Crucetas 3mm', unit: 'pk', qty: Math.max(1, Math.ceil(v.area / 2)) },
      ];
    }
  },
  {
    id: 'ceramica_muro',
    name: 'Cerámica / Porcelanato muro',
    rubro: 'Cerámica',
    icon: '🟦',
    inputs: [
      { id: 'area', label: 'Superficie de muro', unit: 'm²', placeholder: 'Ej: 12' }
    ],
    items(v) {
      return [
        { name: 'Cerámica de muro', unit: 'm2', qty: Math.ceil(v.area * 1.10) },
        { name: 'Adhesivo para cerámica', unit: 'kg', qty: Math.ceil(v.area * 4.5) },
        { name: 'Fragüe / Junta', unit: 'kg', qty: Math.ceil(v.area * 0.4) },
        { name: 'Crucetas 2mm', unit: 'pk', qty: Math.max(1, Math.ceil(v.area / 2)) },
      ];
    }
  },
  {
    id: 'piso_flotante',
    name: 'Piso flotante / laminado',
    rubro: 'Pisos',
    icon: '🪵',
    inputs: [
      { id: 'area', label: 'Superficie', unit: 'm²', placeholder: 'Ej: 30' },
      { id: 'perimetro', label: 'Perímetro de la habitación', unit: 'ml', placeholder: 'Ej: 22' }
    ],
    items(v) {
      return [
        { name: 'Piso flotante / laminado', unit: 'm2', qty: Math.ceil(v.area * 1.08) },
        { name: 'Fieltro / Underlayment', unit: 'm2', qty: Math.ceil(v.area * 1.05) },
        { name: 'Zócalo', unit: 'ml', qty: Math.ceil(v.perimetro) },
        { name: 'Perfil de dilatación', unit: 'un', qty: Math.max(1, Math.ceil(v.perimetro / 3)) },
      ];
    }
  },
  {
    id: 'hormigon',
    name: 'Hormigón (dosificación 1:2:3)',
    rubro: 'Construcción',
    icon: '🏗️',
    inputs: [
      { id: 'volumen', label: 'Volumen de hormigón', unit: 'm³', placeholder: 'Ej: 2.5' }
    ],
    items(v) {
      return [
        { name: 'Cemento Portland', unit: 'bls', qty: Math.ceil(v.volumen * 7) },
        { name: 'Arena gruesa', unit: 'm3', qty: Math.round(v.volumen * 0.56 * 10) / 10 },
        { name: 'Gravilla / Ripio', unit: 'm3', qty: Math.round(v.volumen * 0.84 * 10) / 10 },
      ];
    }
  },
  {
    id: 'estuco',
    name: 'Estuco / Yeso muro',
    rubro: 'Terminaciones',
    icon: '🪣',
    inputs: [
      { id: 'area', label: 'Superficie de muro', unit: 'm²', placeholder: 'Ej: 50' }
    ],
    items(v) {
      return [
        { name: 'Yeso / Estuco', unit: 'kg', qty: Math.ceil(v.area * 1.2) },
        { name: 'Malla de fibra de vidrio', unit: 'm2', qty: Math.ceil(v.area) },
        { name: 'Perfil esquinero de yeso', unit: 'ml', qty: Math.max(1, Math.ceil(v.area / 5)) },
      ];
    }
  },
  {
    id: 'caneria',
    name: 'Cañería PVC',
    rubro: 'Gasfitería',
    icon: '🔧',
    inputs: [
      { id: 'metros', label: 'Metros de cañería', unit: 'ml', placeholder: 'Ej: 15' },
      { id: 'uniones', label: 'N° de uniones / codos', unit: 'un', placeholder: 'Ej: 8' }
    ],
    items(v) {
      return [
        { name: 'Tubo PVC', unit: 'ml', qty: Math.ceil(v.metros * 1.10) },
        { name: 'Codo PVC 90°', unit: 'un', qty: Math.max(1, Math.ceil(v.uniones * 0.6)) },
        { name: 'Unión / Copla PVC', unit: 'un', qty: Math.max(1, Math.ceil(v.uniones * 0.4)) },
        { name: 'Pegamento PVC', unit: 'un', qty: Math.max(1, Math.ceil(v.metros / 10)) },
        { name: 'Teflón', unit: 'un', qty: Math.max(1, Math.ceil(v.uniones * 0.5)) },
      ];
    }
  },
  {
    id: 'cableado',
    name: 'Cableado eléctrico',
    rubro: 'Electricidad',
    icon: '⚡',
    inputs: [
      { id: 'metros', label: 'Metros de cable', unit: 'ml', placeholder: 'Ej: 30' },
      { id: 'puntos', label: 'N° de puntos eléctricos', unit: 'un', placeholder: 'Ej: 6' }
    ],
    items(v) {
      return [
        { name: 'Cable eléctrico 2,5mm²', unit: 'ml', qty: Math.ceil(v.metros * 1.20) },
        { name: 'Conduit / Canaleta', unit: 'ml', qty: Math.ceil(v.metros) },
        { name: 'Caja de empalme', unit: 'un', qty: Math.ceil(v.puntos) },
        { name: 'Cinta aislante', unit: 'un', qty: Math.max(1, Math.ceil(v.puntos / 3)) },
      ];
    }
  },
];

function openCalc() {
  document.getElementById('calc-modal').classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeCalc() {
  document.getElementById('calc-modal').classList.add('hidden');
  document.body.style.overflow = '';
  document.getElementById('calc-recipe').value = '';
  document.getElementById('calc-inputs').innerHTML = '';
  document.getElementById('calc-preview').classList.add('hidden');
  document.getElementById('calc-apply-btn').disabled = true;
}

function loadRecipeInputs() {
  const recipeId = document.getElementById('calc-recipe').value;
  const inputsDiv = document.getElementById('calc-inputs');
  inputsDiv.innerHTML = '';
  document.getElementById('calc-preview').classList.add('hidden');
  document.getElementById('calc-apply-btn').disabled = true;

  if (!recipeId) return;
  const recipe = RECIPES.find(r => r.id === recipeId);
  if (!recipe) return;

  recipe.inputs.forEach(inp => {
    const div = document.createElement('div');
    div.innerHTML = `
      <label class="form-label">${inp.label} <span class="text-slate-400 font-normal">(${inp.unit})</span></label>
      <input type="number" id="calc-${inp.id}" class="form-input" min="0.1" step="0.1" placeholder="${inp.placeholder}">
    `;
    inputsDiv.appendChild(div);
    div.querySelector('input').addEventListener('input', previewCalc);
  });

  inputsDiv.querySelector('input')?.focus();
}

function previewCalc() {
  const recipeId = document.getElementById('calc-recipe').value;
  const recipe = RECIPES.find(r => r.id === recipeId);
  if (!recipe) return;

  const values = {};
  let allFilled = true;
  recipe.inputs.forEach(inp => {
    const val = parseFloat(document.getElementById(`calc-${inp.id}`)?.value);
    if (!val || val <= 0) allFilled = false;
    else values[inp.id] = val;
  });

  const preview = document.getElementById('calc-preview');
  const applyBtn = document.getElementById('calc-apply-btn');
  if (!allFilled) {
    preview.classList.add('hidden');
    applyBtn.disabled = true;
    return;
  }

  const items = recipe.items(values);
  document.getElementById('calc-preview-list').innerHTML = items.map(item => `
    <div class="flex justify-between items-center text-sm bg-slate-50 rounded-lg px-3 py-1.5">
      <span class="text-slate-700">${item.name}</span>
      <span class="font-mono text-blue-600 font-semibold ml-4 shrink-0">${item.qty} ${UNIT_LABELS[item.unit] || item.unit}</span>
    </div>
  `).join('');
  preview.classList.remove('hidden');
  applyBtn.disabled = false;
}

function applyCalc() {
  const recipeId = document.getElementById('calc-recipe').value;
  const recipe = RECIPES.find(r => r.id === recipeId);
  if (!recipe) return;

  const values = {};
  recipe.inputs.forEach(inp => {
    values[inp.id] = parseFloat(document.getElementById(`calc-${inp.id}`)?.value) || 0;
  });

  recipe.items(values).forEach(item => addMaterialRow(item.name, item.unit, item.qty, 0));
  closeCalc();
}

// Populate select grouped by rubro
(function () {
  const sel = document.getElementById('calc-recipe');
  const groups = {};
  RECIPES.forEach(r => {
    if (!groups[r.rubro]) groups[r.rubro] = [];
    groups[r.rubro].push(r);
  });
  Object.entries(groups).forEach(([rubro, recipes]) => {
    const og = document.createElement('optgroup');
    og.label = rubro;
    recipes.forEach(r => {
      const opt = document.createElement('option');
      opt.value = r.id;
      opt.textContent = `${r.icon} ${r.name}`;
      og.appendChild(opt);
    });
    sel.appendChild(og);
  });
})();

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeCalc(); });
