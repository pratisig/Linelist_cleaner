/**
 * Linelist Cleaner & Spatial Fallback Cascade (OCHA COD-AB) - Interactive Web Application
 * PratiSIG Consulting Services - Dakar, Sénégal
 * Auteur : Youssoupha MBODJI (pratisig.consulting@gmail.com)
 */

const AppState = {
  sessionId: null,
  filename: null,
  refFilename: null,
  linelistFile: null,
  refFile: null,
  linelistSkiprows: 0,
  refSkiprows: 0,
  linelistSheet: null,
  refSheet: null,
  rowsCount: 0,
  columnsCount: 0,
  columns: [],
  detectedMappings: {},
  customMappings: {},
  referenceColumns: [],
  spatialMapping: {
    admin1_name: '',
    admin1_pcode: '',
    admin2_name: '',
    admin2_pcode: '',
    admin3_name: '',
    admin3_pcode: '',
    locality_name: '',
    locality_pcode: '',
    lat: '',
    long: ''
  },
  rawPreview: [],
  cleanedPreview: [],
  cleanedColumns: [],
  mapPoints: [],
  report: null,
  indicators: null,
  epiDaily: null,
  epiWeekly: null,
  activeTab: 'dashboard',
  viewMode: 'cleaned',
  searchQuery: '',
  filterMatchLevel: 'ALL',
  config: {
    standardize_headers: true,
    auto_map_epi_tags: true,
    standardize_missing_values: true,
    standardize_dates: true,
    date_output_format: '%Y-%m-%d',
    date_order_preference: 'auto',
    compute_epi_weeks: true,
    enable_spatial_cascade: true,
    spatial_similarity_threshold: 80.0,
    standardize_sex: true,
    standardize_outcomes: true,
    standardize_case_definitions: true,
    standardize_binary_fields: true,
    standardize_ages: true,
    create_age_groups: true,
    validate_chronology: true,
    detect_duplicates: true,
    dedup_action: 'flag',
    fuzzy_similarity_threshold: 0.80
  },
  leafletMap: null,
  leafletMarkersLayer: null,
  charts: {
    cascadeDonut: null,
    whoEpiCurve: null
  }
};

let CANONICAL_DICT = {};

// Fonctions d'acces securise au DOM pour eviter les erreurs null
function safeSetText(id, text) {
  const el = document.getElementById(id);
  if (el) el.innerText = text;
}

function safeSetHtml(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
}

function safeAddClass(id, className) {
  const el = document.getElementById(id);
  if (el) el.classList.add(className);
}

function safeRemoveClass(id, className) {
  const el = document.getElementById(id);
  if (el) el.classList.remove(className);
}

document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await loadDictionary();
  renderEmptyState();
});

async function loadDictionary() {
  try {
    const res = await fetch('/api/dictionary');
    if (res.ok) {
      CANONICAL_DICT = await res.json();
    }
  } catch (e) {
    console.error('Erreur lors du chargement du dictionnaire', e);
  }
}

function setupEventListeners() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const tab = e.currentTarget.dataset.tab;
      switchTab(tab);
    });
  });

  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  if (dropZone && fileInput) {
    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        AppState.linelistFile = e.target.files[0];
        uploadLinelistFile(e.target.files[0]);
      }
    });
  }

  const refDropZone = document.getElementById('ref-drop-zone');
  const refFileInput = document.getElementById('ref-file-input');
  if (refDropZone && refFileInput) {
    refDropZone.addEventListener('click', () => refFileInput.click());
    refFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        AppState.refFile = e.target.files[0];
        uploadReferenceFile(e.target.files[0]);
      }
    });
  }

  const linelistSkipInput = document.getElementById('linelist-skiprows');
  if (linelistSkipInput) {
    linelistSkipInput.addEventListener('change', () => {
      if (AppState.linelistFile) safeRemoveClass('btn-reload-linelist', 'hidden');
    });
  }

  const refSkipInput = document.getElementById('ref-skiprows');
  if (refSkipInput) {
    refSkipInput.addEventListener('change', () => {
      if (AppState.refFile) safeRemoveClass('btn-reload-ref', 'hidden');
    });
  }

  const slider = document.getElementById('slider-threshold');
  if (slider) {
    slider.addEventListener('input', (e) => {
      const val = parseFloat(e.target.value);
      safeSetText('slider-val', `${val}%`);
      AppState.config.spatial_similarity_threshold = val;
    });
    slider.addEventListener('change', async () => {
      if (AppState.sessionId && AppState.filename) {
        await cleanDataset();
      }
    });
  }

  const searchInput = document.getElementById('table-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      AppState.searchQuery = e.target.value.toLowerCase().trim();
      renderTable();
    });
  }

  const levelFilter = document.getElementById('data-filter-level');
  if (levelFilter) {
    levelFilter.addEventListener('change', (e) => {
      AppState.filterMatchLevel = e.target.value;
      renderTable();
    });
  }

  document.querySelectorAll('.view-mode-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.view-mode-btn').forEach(b => b.classList.remove('bg-white', 'shadow-xs', 'text-emerald-700', 'font-semibold'));
      e.currentTarget.classList.add('bg-white', 'shadow-xs', 'text-emerald-700', 'font-semibold');
      AppState.viewMode = e.currentTarget.dataset.mode;
      renderTable();
    });
  });
}

function renderEmptyState() {
  safeRemoveClass('dashboard-empty-state', 'hidden');
  safeAddClass('dashboard-active-content', 'hidden');
}

function switchTab(tabId) {
  AppState.activeTab = tabId;
  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.dataset.tab === tabId) {
      btn.classList.add('border-emerald-600', 'text-emerald-600', 'font-semibold');
      btn.classList.remove('border-transparent', 'text-slate-500', 'hover:text-slate-700');
    } else {
      btn.classList.remove('border-emerald-600', 'text-emerald-600', 'font-semibold');
      btn.classList.add('border-transparent', 'text-slate-500', 'hover:text-slate-700');
    }
  });

  document.querySelectorAll('.tab-content').forEach(pane => {
    if (pane.id === `tab-${tabId}`) {
      pane.classList.remove('hidden');
    } else {
      pane.classList.add('hidden');
    }
  });

  if (tabId === 'map') {
    setTimeout(renderLeafletMap, 200);
  } else if (tabId === 'epicurve' || tabId === 'dashboard') {
    setTimeout(renderCharts, 100);
  }
}

async function uploadLinelistFile(file, skiprows = 0, sheetName = null) {
  showLoader(`Chargement de votre fichier ${file.name}...`);
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('skiprows', skiprows);
    if (sheetName) formData.append('sheet_name', sheetName);
    if (AppState.sessionId) formData.append('session_id', AppState.sessionId);

    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Échec du chargement du fichier.');
    }
    const data = await res.json();

    AppState.sessionId = data.session_id;
    AppState.filename = data.filename;
    AppState.rowsCount = data.rows_count;
    AppState.columnsCount = data.columns_count;
    AppState.columns = data.columns;
    AppState.detectedMappings = data.detected_mappings;
    AppState.customMappings = {};
    for (const [col, meta] of Object.entries(data.detected_mappings)) {
      if (meta.mapped_tag) {
        AppState.customMappings[col] = meta.mapped_tag;
      }
    }

    safeSetText('label-linelist-file', `✔️ Line list : ${file.name}`);
    safeSetText('sublabel-linelist-file', `${data.rows_count} cas chargés (${data.columns_count} colonnes)`);

    const sheetSelect = document.getElementById('linelist-sheet-select');
    if (data.sheets && data.sheets.length > 1 && sheetSelect) {
      safeRemoveClass('linelist-sheet-container', 'hidden');
      sheetSelect.innerHTML = data.sheets.map(s => `<option value="${escapeHtml(s)}" ${data.selected_sheet === s ? 'selected' : ''}>${escapeHtml(s)}</option>`).join('');
      safeRemoveClass('btn-reload-linelist', 'hidden');
    }

    updateHeaderStats();
    await cleanDataset();
  } catch (e) {
    alert(`Erreur lors du chargement de la line list : ${e.message}`);
  } finally {
    hideLoader();
  }
}

async function uploadReferenceFile(file, skiprows = 0, sheetName = null) {
  showLoader(`Chargement et analyse de votre référentiel P-Code ${file.name}...`);
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('skiprows', skiprows);
    if (sheetName) formData.append('sheet_name', sheetName);
    if (AppState.sessionId) formData.append('session_id', AppState.sessionId);

    const res = await fetch('/api/upload_reference', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Échec du chargement du référentiel.');
    }
    const data = await res.json();

    AppState.sessionId = data.session_id;
    AppState.refFilename = data.ref_filename;
    AppState.referenceColumns = data.reference_columns || [];
    if (data.detected_spatial_mapping) {
      AppState.spatialMapping = Object.assign(AppState.spatialMapping, data.detected_spatial_mapping);
    }

    safeSetText('label-ref-file', `✔️ Référentiel : ${file.name}`);
    safeSetText('sublabel-ref-file', `${data.reference_rows} entités administratives prêtes pour la cascade`);
    safeSetText('stat-ref-filename', file.name);

    const sheetSelect = document.getElementById('ref-sheet-select');
    if (data.sheets && data.sheets.length > 1 && sheetSelect) {
      safeRemoveClass('ref-sheet-container', 'hidden');
      sheetSelect.innerHTML = data.sheets.map(s => `<option value="${escapeHtml(s)}" ${data.selected_sheet === s ? 'selected' : ''}>${escapeHtml(s)}</option>`).join('');
      safeRemoveClass('btn-reload-ref', 'hidden');
    }

    renderReferenceMapping();

    if (AppState.filename) {
      await cleanDataset();
    } else {
      alert(`Référentiel P-Code chargé avec succès (${data.reference_rows} entités). Vous pouvez maintenant charger votre Line List.`);
    }
  } catch (e) {
    alert(`Erreur lors du chargement du référentiel P-Code : ${e.message}`);
  } finally {
    hideLoader();
  }
}

async function reloadLinelistWithOptions() {
  if (!AppState.linelistFile) return;
  const skipEl = document.getElementById('linelist-skiprows');
  const skiprows = skipEl ? parseInt(skipEl.value) || 0 : 0;
  const sheetSelect = document.getElementById('linelist-sheet-select');
  const sheetName = sheetSelect ? sheetSelect.value : null;
  await uploadLinelistFile(AppState.linelistFile, skiprows, sheetName);
}

async function reloadReferenceWithOptions() {
  if (!AppState.refFile) return;
  const skipEl = document.getElementById('ref-skiprows');
  const skiprows = skipEl ? parseInt(skipEl.value) || 0 : 0;
  const sheetSelect = document.getElementById('ref-sheet-select');
  const sheetName = sheetSelect ? sheetSelect.value : null;
  await uploadReferenceFile(AppState.refFile, skiprows, sheetName);
}

async function cleanDataset() {
  if (!AppState.sessionId || !AppState.filename) {
    alert('Veuillez d abord charger un fichier de line list.');
    return;
  }
  showLoader('Exécution du nettoyage épidémiologique et du géocodage en cascade...');

  try {
    const payload = {
      session_id: AppState.sessionId,
      config: AppState.config,
      column_mapping: AppState.customMappings,
      spatial_mapping: AppState.spatialMapping
    };

    const res = await fetch('/api/clean', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Erreur lors du nettoyage');
    }

    const data = await res.json();
    AppState.report = data.report;
    AppState.indicators = data.indicators;
    AppState.epiDaily = data.epi_curve_daily;
    AppState.epiWeekly = data.epi_curve_weekly;
    AppState.mapPoints = data.map_points || [];
    AppState.cleanedColumns = data.cleaned_columns;
    AppState.cleanedPreview = data.cleaned_preview;
    AppState.rawPreview = data.raw_preview;

    if (data.reference_columns && data.reference_columns.length > 0) {
      AppState.referenceColumns = data.reference_columns;
    }

    safeAddClass('dashboard-empty-state', 'hidden');
    safeRemoveClass('dashboard-active-content', 'hidden');

    updateHeaderStats();
    renderDashboard();
    renderTable();
    renderColumnMapper();
    renderReferenceMapping();
    renderIssues();
    renderCharts();
    if (AppState.activeTab === 'map') {
      renderLeafletMap();
    }
  } catch (e) {
    alert(`Erreur: ${e.message}`);
  } finally {
    hideLoader();
  }
}

function updateHeaderStats() {
  const fileNameText = AppState.filename ? `${AppState.filename} (${AppState.report ? AppState.report.cleaned_shape[0] : AppState.rowsCount} cas)` : 'Aucun fichier chargé';
  safeSetText('stat-filename', fileNameText);
  safeSetText('stat-ref-filename', AppState.refFilename || 'Aucun référentiel chargé');

  if (AppState.report) {
    const spatial = AppState.report.spatial_summary;
    const geoRate = spatial ? spatial.geocoded_rate_pct : 0.0;
    const scoreHtml = `
      <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold ${
        geoRate >= 80 ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-amber-100 text-amber-800'
      }">
        Taux Géocodage : ${geoRate}%
      </span>
    `;
    safeSetHtml('stat-score', scoreHtml);
    safeSetText('tab-issues-count', String(AppState.report.validation_issues.length));
  }
}

function renderDashboard() {
  if (!AppState.report) return;
  const spatial = AppState.report.spatial_summary;

  safeSetText('kpi-total-cases', String(AppState.report.cleaned_shape[0]));
  safeSetText('kpi-geocoded-rate', spatial ? `${spatial.geocoded_rate_pct}%` : '0%');
  safeSetText('kpi-geocoded-count', spatial ? `${spatial.geocoded_count} / ${spatial.total_records} cas localisés` : 'N/A');
  safeSetText('kpi-avg-score', spatial ? `${spatial.average_match_score}%` : '0%');
  safeSetText('kpi-epiweeks-count', `${AppState.report.epi_weeks_computed} cas`);

  const tbody = document.getElementById('precision-breakdown-tbody');
  if (tbody && spatial) {
    const levels = [
      { id: 'Locality', name: 'Étape 1 : Localité / Village', badge: 'bg-emerald-100 text-emerald-800 border-emerald-300', dot: 'bg-emerald-500' },
      { id: 'Admin3_Ward', name: 'Étape 2 (Fallback 1) : Admin 3 / Ward', badge: 'bg-teal-100 text-teal-800 border-teal-300', dot: 'bg-teal-500' },
      { id: 'Admin2_LGA', name: 'Étape 3 (Fallback 2) : Admin 2 / LGA', badge: 'bg-blue-100 text-blue-800 border-blue-300', dot: 'bg-blue-500' },
      { id: 'Admin1_State', name: 'Étape 4 (Fallback 3) : Admin 1 / State', badge: 'bg-amber-100 text-amber-800 border-amber-300', dot: 'bg-amber-500' },
      { id: 'Unmatched', name: 'Étape 5 : Non Localisé (Unmatched)', badge: 'bg-rose-100 text-rose-800 border-rose-300', dot: 'bg-rose-500' },
    ];

    let html = '';
    levels.forEach(lvl => {
      const cnt = spatial.level_distribution[lvl.id] || 0;
      const pct = spatial.level_percentages[lvl.id] || 0.0;
      html += `
        <tr class="border-b border-slate-100 hover:bg-slate-50/60">
          <td class="px-3 py-2.5 font-semibold text-slate-800 flex items-center gap-2">
            <span class="w-2.5 h-2.5 rounded-full ${lvl.dot}"></span>
            ${lvl.name}
          </td>
          <td class="px-3 py-2.5 font-mono text-slate-600">${lvl.id}</td>
          <td class="px-3 py-2.5 text-right font-bold text-slate-800">${cnt}</td>
          <td class="px-3 py-2.5 text-right font-semibold text-slate-700">${pct}%</td>
          <td class="px-3 py-2.5 text-center">
            <span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border ${lvl.badge}">
              ${lvl.id === 'Unmatched' ? 'Échec' : 'Succès'}
            </span>
          </td>
        </tr>
      `;
    });
    tbody.innerHTML = html;
  }
}

function renderLeafletMap() {
  const mapContainer = document.getElementById('leaflet-map');
  if (!mapContainer || typeof L === 'undefined') return;

  if (!AppState.leafletMap) {
    AppState.leafletMap = L.map('leaflet-map').setView([14.6937, -17.4441], 7);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors | PratiSIG Consulting Services'
    }).addTo(AppState.leafletMap);
    AppState.leafletMarkersLayer = L.layerGroup().addTo(AppState.leafletMap);
  }

  AppState.leafletMarkersLayer.clearLayers();

  if (AppState.mapPoints && AppState.mapPoints.length > 0) {
    const latlngs = [];
    const colors = {
      'Locality': '#10b981',
      'Admin3_Ward': '#0d9488',
      'Admin2_LGA': '#2563eb',
      'Admin1_State': '#d97706'
    };

    AppState.mapPoints.forEach(pt => {
      if (pt.lat && pt.lng) {
        const markerColor = colors[pt.match_level] || '#64748b';
        const marker = L.circleMarker([pt.lat, pt.lng], {
          radius: 6,
          fillColor: markerColor,
          color: '#ffffff',
          weight: 1.5,
          opacity: 1,
          fillOpacity: 0.85
        });

        marker.bindPopup(`
          <div class="text-xs space-y-1">
            <div class="font-bold text-slate-900">${escapeHtml(pt.id)}</div>
            <div><strong>Entité :</strong> ${escapeHtml(pt.name)}</div>
            <div><strong>P-Code :</strong> <code class="text-emerald-700 font-bold">${escapeHtml(pt.pcode)}</code></div>
            <div><strong>Niveau :</strong> <span class="font-semibold">${escapeHtml(pt.match_level)}</span></div>
            <div><strong>Score :</strong> ${pt.score}%</div>
            <div><strong>Semaine Épi :</strong> ${escapeHtml(pt.epi_week)}</div>
          </div>
        `);

        marker.addTo(AppState.leafletMarkersLayer);
        latlngs.push([pt.lat, pt.lng]);
      }
    });

    if (latlngs.length > 0) {
      AppState.leafletMap.fitBounds(L.latLngBounds(latlngs), { padding: [30, 30] });
    }
  }
}

function renderTable() {
  const tableHead = document.getElementById('data-table-head');
  const tableBody = document.getElementById('data-table-body');
  if (!tableHead || !tableBody) return;

  const isCleanedMode = AppState.viewMode === 'cleaned';
  const cols = isCleanedMode ? AppState.cleanedColumns : AppState.columns;
  let rows = isCleanedMode ? AppState.cleanedPreview : AppState.rawPreview;

  if (isCleanedMode && AppState.filterMatchLevel !== 'ALL') {
    rows = rows.filter(r => r['MATCH_LEVEL'] === AppState.filterMatchLevel);
  }

  if (AppState.searchQuery) {
    rows = rows.filter(r => {
      return Object.values(r).some(val => String(val).toLowerCase().includes(AppState.searchQuery));
    });
  }

  let thHtml = `<tr class="bg-slate-50 border-b border-slate-200">
    <th class="px-3 py-3 text-left text-xs font-semibold text-slate-600 uppercase tracking-wider sticky left-0 bg-slate-50 z-10 w-12">#</th>`;

  cols.forEach(c => {
    let tagBadge = '';
    if (c === 'PCODE_ASSIGNED') tagBadge = '<span class="px-1.5 py-0.5 text-[10px] bg-emerald-100 text-emerald-800 font-bold rounded">P-Code</span>';
    else if (c === 'MATCH_LEVEL') tagBadge = '<span class="px-1.5 py-0.5 text-[10px] bg-teal-100 text-teal-800 font-bold rounded">Niveau</span>';
    else if (c === 'EPI_WEEK') tagBadge = '<span class="px-1.5 py-0.5 text-[10px] bg-indigo-100 text-indigo-800 font-bold rounded">OMS</span>';

    thHtml += `
      <th class="px-3 py-3 text-left text-xs font-semibold text-slate-700 tracking-wider whitespace-nowrap">
        <div class="flex items-center gap-1.5">
          <span>${escapeHtml(c)}</span>
          ${tagBadge}
        </div>
      </th>
    `;
  });
  thHtml += `</tr>`;
  tableHead.innerHTML = thHtml;

  if (rows.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="${cols.length + 1}" class="text-center py-10 text-slate-400">Aucun enregistrement disponible. Veuillez charger une line list.</td></tr>`;
    return;
  }

  let tbHtml = '';
  rows.forEach((row, idx) => {
    const matchLvl = row['MATCH_LEVEL'];
    let rowBg = '';
    if (matchLvl === 'Locality') rowBg = 'bg-emerald-50/20';
    else if (matchLvl === 'Unmatched') rowBg = 'bg-rose-50/30';

    tbHtml += `<tr class="hover:bg-blue-50/40 border-b border-slate-100 transition-colors ${rowBg}">
      <td class="px-3 py-2 text-xs font-mono text-slate-400 sticky left-0 bg-white">${idx + 1}</td>`;

    cols.forEach(c => {
      const val = row[c];
      const isNull = val === null || val === undefined || val === '';
      let displayVal = isNull ? '<span class="text-slate-300 italic">null</span>' : escapeHtml(String(val));

      if (c === 'MATCH_LEVEL' && !isNull) {
        const lvlColors = {
          'Locality': 'bg-emerald-100 text-emerald-800 border-emerald-200',
          'Admin3_Ward': 'bg-teal-100 text-teal-800 border-teal-200',
          'Admin2_LGA': 'bg-blue-100 text-blue-800 border-blue-200',
          'Admin1_State': 'bg-amber-100 text-amber-800 border-amber-200',
          'Unmatched': 'bg-rose-100 text-rose-800 border-rose-200'
        };
        displayVal = `<span class="px-2 py-0.5 rounded text-[10px] font-bold border ${lvlColors[val] || 'bg-slate-100 text-slate-700'}">${val}</span>`;
      } else if (c === 'PCODE_ASSIGNED' && !isNull) {
        displayVal = `<span class="font-mono font-bold text-emerald-800">${val}</span>`;
      } else if (c === 'EPI_WEEK' && !isNull) {
        displayVal = `<span class="font-mono font-semibold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded">${val}</span>`;
      }

      tbHtml += `<td class="px-3 py-2 text-xs text-slate-700 whitespace-nowrap">${displayVal}</td>`;
    });

    tbHtml += `</tr>`;
  });

  tableBody.innerHTML = tbHtml;
}

function renderColumnMapper() {
  const container = document.getElementById('column-mapper-tbody');
  if (!container) return;

  const rawCols = AppState.columns;
  if (!rawCols || rawCols.length === 0) {
    container.innerHTML = `<tr><td colspan="4" class="text-center py-6 text-slate-400">Veuillez charger une line list pour mapper les colonnes.</td></tr>`;
    return;
  }

  let html = '';
  rawCols.forEach(col => {
    const detectedMeta = AppState.detectedMappings[col] || {};
    const selectedTag = AppState.customMappings[col] || detectedMeta.mapped_tag || '';
    const score = detectedMeta.score ? Math.round(detectedMeta.score * 100) : 0;
    const cat = detectedMeta.category || 'other';

    html += `
      <tr class="border-b border-slate-100 hover:bg-slate-50/60">
        <td class="px-4 py-3 text-xs font-mono font-medium text-slate-800">${escapeHtml(col)}</td>
        <td class="px-4 py-3">
          <select class="col-map-select text-xs rounded border-slate-200 py-1.5 px-2 bg-white text-slate-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500" data-col="${escapeHtml(col)}">
            <option value="">-- Conserver tel quel / Non Mappé --</option>
            ${Object.entries(CANONICAL_DICT).map(([t, m]) => `
              <option value="${t}" ${selectedTag === t ? 'selected' : ''}>${m.label} (${t})</option>
            `).join('')}
          </select>
        </td>
        <td class="px-4 py-3">
          <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${
            cat === 'geographic' ? 'bg-emerald-100 text-emerald-800' :
            (cat === 'timeline' ? 'bg-indigo-100 text-indigo-800' :
            (cat === 'demographic' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-700'))
          }">
            ${cat}
          </span>
        </td>
        <td class="px-4 py-3">
          <div class="flex items-center gap-2">
            <div class="w-16 bg-slate-100 rounded-full h-1.5">
              <div class="bg-emerald-600 h-1.5 rounded-full" style="width: ${score}%"></div>
            </div>
            <span class="text-xs text-slate-500">${score}%</span>
          </div>
        </td>
      </tr>
    `;
  });

  container.innerHTML = html;

  document.querySelectorAll('.col-map-select').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const colName = e.target.dataset.col;
      const tagVal = e.target.value;
      if (tagVal) AppState.customMappings[colName] = tagVal;
      else delete AppState.customMappings[colName];
    });
  });
}

function renderReferenceMapping() {
  const container = document.getElementById('reference-mapping-grid');
  if (!container) return;

  const refCols = AppState.referenceColumns;
  if (!refCols || refCols.length === 0) {
    container.innerHTML = `<div class="col-span-3 text-center py-6 text-slate-400">Aucun référentiel P-Code externe chargé. Vous pouvez en charger un dans la zone verte en haut.</div>`;
    return;
  }

  const spatialRoles = [
    { key: 'locality_name', label: '1. Nom Localité / Village', desc: 'Colonne contenant le nom du village' },
    { key: 'locality_pcode', label: 'P-Code Localité', desc: 'Code P-Code localité' },
    { key: 'admin3_name', label: '2. Nom Admin 3 / Ward', desc: 'Nom du Ward / Sous-district' },
    { key: 'admin3_pcode', label: 'P-Code Admin 3', desc: 'Code P-Code Admin 3' },
    { key: 'admin2_name', label: '3. Nom Admin 2 / LGA', desc: 'Nom du District / LGA' },
    { key: 'admin2_pcode', label: 'P-Code Admin 2', desc: 'Code P-Code Admin 2' },
    { key: 'admin1_name', label: '4. Nom Admin 1 / State', desc: 'Nom de la Région / Province' },
    { key: 'admin1_pcode', label: 'P-Code Admin 1', desc: 'Code P-Code Admin 1' },
    { key: 'lat', label: 'Latitude (Y)', desc: 'Coordonnée Y (WGS84)' },
    { key: 'long', label: 'Longitude (X)', desc: 'Coordonnée X (WGS84)' }
  ];

  let html = '';
  spatialRoles.forEach(role => {
    const currentVal = AppState.spatialMapping[role.key] || '';
    html += `
      <div class="bg-slate-50 border border-slate-200 rounded-lg p-3">
        <label class="block font-semibold text-slate-800 mb-1">${role.label}</label>
        <select class="ref-map-select w-full text-xs rounded border-slate-300 py-1 px-2 bg-white text-slate-700 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500" data-role="${role.key}">
          <option value="">-- Non renseigné --</option>
          ${refCols.map(c => `<option value="${escapeHtml(c)}" ${currentVal === c ? 'selected' : ''}>${escapeHtml(c)}</option>`).join('')}
        </select>
        <span class="text-[10px] text-slate-400 mt-1 block">${role.desc}</span>
      </div>
    `;
  });

  container.innerHTML = html;

  document.querySelectorAll('.ref-map-select').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const roleKey = e.target.dataset.role;
      AppState.spatialMapping[roleKey] = e.target.value;
    });
  });
}

function renderCharts() {
  if (typeof Chart === 'undefined') return;

  const donutCanvas = document.getElementById('chart-cascade-donut');
  if (donutCanvas && AppState.report && AppState.report.spatial_summary) {
    if (AppState.charts.cascadeDonut) AppState.charts.cascadeDonut.destroy();

    const dist = AppState.report.spatial_summary.level_distribution;
    const labels = ['Localité (Village)', 'Admin 3 (Ward)', 'Admin 2 (LGA)', 'Admin 1 (State)', 'Non Localisé'];
    const dataVals = [
      dist['Locality'] || 0,
      dist['Admin3_Ward'] || 0,
      dist['Admin2_LGA'] || 0,
      dist['Admin1_State'] || 0,
      dist['Unmatched'] || 0
    ];

    AppState.charts.cascadeDonut = new Chart(donutCanvas, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: dataVals,
          backgroundColor: ['#10b981', '#0d9488', '#2563eb', '#d97706', '#ef4444'],
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 } } }
        },
        cutout: '65%'
      }
    });
  }

  const epiCanvas = document.getElementById('chart-who-epicurve');
  if (epiCanvas && AppState.epiWeekly) {
    if (AppState.charts.whoEpiCurve) AppState.charts.whoEpiCurve.destroy();

    const periods = AppState.epiWeekly.periods;
    const seriesObj = AppState.epiWeekly.series;
    const colors = ['#10b981', '#ef4444', '#3b82f6', '#f59e0b', '#8b5cf6'];

    const datasets = Object.entries(seriesObj).map(([label, vals], idx) => ({
      label: label,
      data: vals,
      backgroundColor: colors[idx % colors.length],
      borderRadius: 3,
      stack: 'stack1'
    }));

    AppState.charts.whoEpiCurve = new Chart(epiCanvas, {
      type: 'bar',
      data: { labels: periods, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 12, font: { size: 11 } } },
          tooltip: { mode: 'index', intersect: false }
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 10 } } },
          y: { stacked: true, beginAtZero: true, grid: { color: '#f1f5f9' }, ticks: { precision: 0 } }
        }
      }
    });
  }
}

function renderIssues() {
  if (!AppState.report) return;
  const tbody = document.getElementById('issues-tbody');
  if (!tbody) return;

  const issues = AppState.report.validation_issues;
  if (issues.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-10 text-slate-400">Aucune incohérence chronologique ou clinique détectée.</td></tr>`;
    return;
  }

  let html = '';
  issues.forEach(iss => {
    const sevBadge = iss.severity === 'ERROR'
      ? 'bg-rose-100 text-rose-800 border-rose-200'
      : (iss.severity === 'WARNING' ? 'bg-amber-100 text-amber-800 border-amber-200' : 'bg-blue-100 text-blue-800 border-blue-200');

    html += `
      <tr class="border-b border-slate-100 hover:bg-slate-50/60">
        <td class="px-3 py-2 font-mono font-medium text-slate-600">${iss.row_idx}</td>
        <td class="px-3 py-2 font-mono text-slate-700">${escapeHtml(iss.case_id || 'N/A')}</td>
        <td class="px-3 py-2"><span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold border ${sevBadge}">${iss.severity}</span></td>
        <td class="px-3 py-2 text-slate-600">${iss.issue_type}</td>
        <td class="px-3 py-2 font-mono text-slate-700">${escapeHtml(iss.column || 'N/A')}</td>
        <td class="px-3 py-2 text-slate-800">${escapeHtml(iss.message)}</td>
        <td class="px-3 py-2 text-slate-500 italic">${escapeHtml(iss.suggested_action || 'N/A')}</td>
      </tr>
    `;
  });

  tbody.innerHTML = html;
}

function downloadExcel() {
  if (!AppState.sessionId) return;
  window.open(`/api/export/excel/${AppState.sessionId}`, '_blank');
}

function downloadCSV() {
  if (!AppState.sessionId) return;
  window.open(`/api/export/csv/${AppState.sessionId}`, '_blank');
}

function downloadScript() {
  if (!AppState.sessionId) return;
  window.open(`/api/export/script/${AppState.sessionId}`, '_blank');
}

function showLoader(msg) {
  safeRemoveClass('loader-overlay', 'hidden');
  safeSetText('loader-text', msg || 'Traitement en cours...');
}

function hideLoader() {
  safeAddClass('loader-overlay', 'hidden');
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
