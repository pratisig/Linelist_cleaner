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
    linelist_locality_col: '',
    locality_name: '',
    locality_pcode: '',
    linelist_admin3_col: '',
    admin3_name: '',
    admin3_pcode: '',
    linelist_admin2_col: '',
    admin2_name: '',
    admin2_pcode: '',
    linelist_admin1_col: '',
    admin1_name: '',
    admin1_pcode: '',
    lat: '',
    long: ''
  },
  rawPreview: [],
  cleanedPreview: [],
  cleanedColumns: [],
  mapPoints: [],
  report: null,
  advancedMetrics: null,
  qualityDelta: 0,
  outbreakAlerts: [],
  incidenceTrend: null,
  indicators: null,
  epiDaily: null,
  epiWeekly: null,
  delays: {},
  pyramid: {},
  activeTab: 'dashboard',
  viewMode: 'cleaned',
  searchQuery: '',
  filterMatchLevel: 'ALL',
  language: 'FR',
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
    fuzzy_similarity_threshold: 0.80,
    clean_coordinates: true,
    clean_phone_numbers: true,
    default_phone_country_code: '+221',
    detect_outbreak_signals: true,
    outbreak_alert_threshold_multiplier: 1.5,
    preset: null
  },
  leafletMap: null,
  leafletMarkersLayer: null,
  charts: {
    cascadeDonut: null,
    whoEpiCurve: null,
    detailedEpiCurve: null
  }
};

let CANONICAL_DICT = {};

const I18N_TEXTS = {
  FR: {
    header_subtitle: "PratiSIG Consulting Services : La pratique des SIG, notre métier",
    btn_clean: "Nettoyer V2",
    btn_browse_linelist: "Choisir un fichier",
    btn_browse_ref: "Choisir un référentiel",
    tab_dashboard: "Tableau de bord V2",
    tab_map: "Carte SIG",
    tab_data: "Données nettoyées",
    tab_mapper: "Mapping",
    tab_epicurve: "Courbe épi",
    tab_issues: "Qualité",
    tab_export: "Export V2",
    kpi_total_cases: "Cas totaux",
    kpi_geocoded: "Géocodés",
    kpi_quality: "Qualité",
    kpi_epiweeks: "EpiWeeks",
    kpi_trend: "Tendance V2",
    kpi_coords: "Coords validées",
    kpi_phones: "Tél. normalisés",
    kpi_alerts: "Alertes",
    kpi_delta: "Δ Qualité V2",
    alert_no_file: "Veuillez d'abord charger un fichier de linelist ou cliquer sur l'un des exemples.",
    btn_export_excel: "Télécharger Excel V2",
    btn_export_csv: "Télécharger CSV",
    btn_export_geojson: "Télécharger GeoJSON",
    btn_export_script: "Télécharger .py",
    reapply_mapping: "Appliquer et Recalculer le Nettoyage"
  },
  EN: {
    header_subtitle: "PratiSIG Consulting Services: GIS in practice, our expertise",
    btn_clean: "Clean V2",
    btn_browse_linelist: "Browse Linelist",
    btn_browse_ref: "Browse Reference",
    tab_dashboard: "Dashboard V2",
    tab_map: "GIS Map",
    tab_data: "Cleaned Data",
    tab_mapper: "Mapping",
    tab_epicurve: "Epi Curve",
    tab_issues: "Quality",
    tab_export: "Export V2",
    kpi_total_cases: "Total Cases",
    kpi_geocoded: "Geocoded",
    kpi_quality: "Quality",
    kpi_epiweeks: "EpiWeeks",
    kpi_trend: "Trend V2",
    kpi_coords: "Valid Coords",
    kpi_phones: "Normalized Phones",
    kpi_alerts: "Alerts",
    kpi_delta: "Δ Quality V2",
    alert_no_file: "Please upload a linelist file first or select a sample dataset.",
    btn_export_excel: "Download Excel V2",
    btn_export_csv: "Download CSV",
    btn_export_geojson: "Download GeoJSON",
    btn_export_script: "Download .py",
    reapply_mapping: "Apply & Re-run Cleaning"
  }
};

function formatApiError(err) {
  if (!err) return 'Une erreur est survenue.';
  if (typeof err === 'string') return err;
  if (typeof err.detail === 'string') return err.detail;
  if (Array.isArray(err.detail)) {
    return err.detail.map(d => {
      if (typeof d === 'string') return d;
      const field = d.loc ? d.loc.filter(x => x !== 'body').join('.') : '';
      return (field ? `${field}: ` : '') + (d.msg || JSON.stringify(d));
    }).join('\n');
  }
  if (err.detail && typeof err.detail === 'object') {
    return JSON.stringify(err.detail);
  }
  if (err.message) return err.message;
  return JSON.stringify(err);
}

// Safe DOM Manipulation helpers
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

function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
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
  // Tab buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const tab = e.currentTarget.dataset.tab;
      if (tab) switchTab(tab);
    });
  });

  // Linelist Upload & Drag-and-Drop
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const btnBrowseLinelist = document.getElementById('btn-browse-linelist');

  if (dropZone && fileInput) {
    dropZone.addEventListener('click', (e) => {
      if (e.target.closest('input, select, button, label')) return;
      fileInput.click();
    });

    if (btnBrowseLinelist) {
      btnBrowseLinelist.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.click();
      });
    }

    fileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        AppState.linelistFile = e.target.files[0];
        uploadLinelistFile(e.target.files[0]);
        fileInput.value = '';
      }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.add('border-blue-500', 'bg-blue-100/50');
      });
    });

    ['dragleave', 'dragend'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropZone.classList.remove('border-blue-500', 'bg-blue-100/50');
      });
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove('border-blue-500', 'bg-blue-100/50');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        AppState.linelistFile = e.dataTransfer.files[0];
        uploadLinelistFile(e.dataTransfer.files[0]);
      }
    });
  }

  // Reference P-Code Upload & Drag-and-Drop
  const refDropZone = document.getElementById('ref-drop-zone');
  const refFileInput = document.getElementById('ref-file-input');
  const btnBrowseRef = document.getElementById('btn-browse-ref');

  if (refDropZone && refFileInput) {
    refDropZone.addEventListener('click', (e) => {
      if (e.target.closest('input, select, button, label')) return;
      refFileInput.click();
    });

    if (btnBrowseRef) {
      btnBrowseRef.addEventListener('click', (e) => {
        e.stopPropagation();
        refFileInput.click();
      });
    }

    refFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        AppState.refFile = e.target.files[0];
        uploadReferenceFile(e.target.files[0]);
        refFileInput.value = '';
      }
    });

    ['dragenter', 'dragover'].forEach(eventName => {
      refDropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        refDropZone.classList.add('border-emerald-500', 'bg-emerald-100/50');
      });
    });

    ['dragleave', 'dragend'].forEach(eventName => {
      refDropZone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        refDropZone.classList.remove('border-emerald-500', 'bg-emerald-100/50');
      });
    });

    refDropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      refDropZone.classList.remove('border-emerald-500', 'bg-emerald-100/50');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        AppState.refFile = e.dataTransfer.files[0];
        uploadReferenceFile(e.dataTransfer.files[0]);
      }
    });
  }

  // Reload options buttons
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

  // Slider similarity threshold
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

  // Search input in table
  const searchInput = document.getElementById('table-search');
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      AppState.searchQuery = e.target.value.toLowerCase().trim();
      renderTable();
    });
  }

  // Map MATCH_LEVEL filter
  const mapLevelFilter = document.getElementById('map-filter-level');
  if (mapLevelFilter) {
    mapLevelFilter.addEventListener('change', () => renderLeafletMap());
  }

  // Table MATCH_LEVEL filter
  const levelFilter = document.getElementById('data-filter-level');
  if (levelFilter) {
    levelFilter.addEventListener('change', (e) => {
      AppState.filterMatchLevel = e.target.value;
      renderTable();
    });
  }

  // View mode switcher (Cleaned / Raw)
  document.querySelectorAll('.view-mode-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('.view-mode-btn').forEach(b => {
        b.classList.remove('bg-white', 'shadow-xs', 'text-emerald-700', 'font-semibold');
        b.classList.add('text-slate-600');
      });
      e.currentTarget.classList.remove('text-slate-600');
      e.currentTarget.classList.add('bg-white', 'shadow-xs', 'text-emerald-700', 'font-semibold');
      AppState.viewMode = e.currentTarget.dataset.mode;
      renderTable();
    });
  });

  // Global Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      const q = document.getElementById('table-search');
      if (q) {
        switchTab('data');
        setTimeout(() => q.focus(), 100);
      }
    }
    if (e.key.toLowerCase() === 'd' && !e.ctrlKey && !e.metaKey && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'SELECT') {
      toggleDarkMode();
    }
  });
}

function renderEmptyState() {
  if (!AppState.report && !AppState.filename) {
    safeRemoveClass('dashboard-empty-state', 'hidden');
    safeAddClass('dashboard-active-content', 'hidden');
  } else {
    safeAddClass('dashboard-empty-state', 'hidden');
    safeRemoveClass('dashboard-active-content', 'hidden');
  }
}

function switchTab(tabId) {
  AppState.activeTab = tabId;

  document.querySelectorAll('.tab-btn').forEach(btn => {
    if (btn.dataset.tab === tabId) {
      btn.classList.add('border-emerald-600', 'text-emerald-600', 'font-semibold', 'bg-emerald-50/60');
      btn.classList.remove('border-transparent', 'text-slate-500', 'hover:text-slate-700');
    } else {
      btn.classList.remove('border-emerald-600', 'text-emerald-600', 'font-semibold', 'bg-emerald-50/60');
      btn.classList.add('border-transparent', 'text-slate-500', 'hover:text-slate-700');
    }
  });

  safeAddClass('dashboard-empty-state', 'hidden');
  safeRemoveClass('dashboard-active-content', 'hidden');

  document.querySelectorAll('.tab-content').forEach(pane => {
    if (pane.id === `tab-${tabId}`) {
      pane.classList.remove('hidden');
    } else {
      pane.classList.add('hidden');
    }
  });

  if (tabId === 'dashboard') {
    renderV2Kpis();
    setTimeout(renderCharts, 100);
  } else if (tabId === 'map') {
    setTimeout(() => {
      renderLeafletMap();
      if (AppState.leafletMap) {
        AppState.leafletMap.invalidateSize();
      }
    }, 150);
  } else if (tabId === 'epicurve') {
    setTimeout(() => {
      renderDetailedEpiChart();
      renderCharts();
    }, 100);
  } else if (tabId === 'data') {
    renderTable();
  } else if (tabId === 'mapper') {
    renderSpatialMappingPairs();
    renderKeyEpiVariables();
    renderColumnMapper();
  } else if (tabId === 'issues') {
    renderIssues();
  }
}

async function loadSampleDataset(sampleType = 'cholera') {
  showLoader(`Chargement du jeu de données exemple (${sampleType})...`);
  try {
    const formData = new FormData();
    formData.append('sample_type', sampleType);
    formData.append('load_ref', 'true');

    const res = await fetch('/api/load_sample', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(formatApiError(err) || 'Erreur lors du chargement de l\'exemple.');
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

    AppState.refFilename = data.ref_filename;
    AppState.referenceColumns = data.reference_columns || [];
    if (data.detected_spatial_mapping) {
      for (const [k, v] of Object.entries(data.detected_spatial_mapping)) {
        if (v) AppState.spatialMapping[k] = v;
      }
    }

    safeSetText('label-linelist-file', `✔️ Linelist : ${data.filename}`);
    safeSetText('sublabel-linelist-file', `${data.rows_count} cas chargés (${data.columns_count} colonnes)`);
    safeSetText('label-ref-file', `✔️ Référentiel : ${data.ref_filename || 'COD-AB'}`);
    safeSetText('sublabel-ref-file', `${data.reference_rows || 0} entités administratives prêtes`);

    updateHeaderStats();
    updateStepper(2);

    await cleanDataset();
  } catch (e) {
    alert(`Erreur: ${e.message}`);
  } finally {
    hideLoader();
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
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(formatApiError(err) || 'Échec du chargement du fichier.');
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

    safeSetText('label-linelist-file', `✔️ Linelist : ${file.name}`);
    safeSetText('sublabel-linelist-file', `${data.rows_count} cas chargés (${data.columns_count} colonnes)`);

    const sheetSelect = document.getElementById('linelist-sheet-select');
    if (data.sheets && data.sheets.length > 1 && sheetSelect) {
      safeRemoveClass('linelist-sheet-container', 'hidden');
      sheetSelect.innerHTML = data.sheets.map(s => `<option value="${escapeHtml(s)}" ${data.selected_sheet === s ? 'selected' : ''}>${escapeHtml(s)}</option>`).join('');
      safeRemoveClass('btn-reload-linelist', 'hidden');
    }

    updateHeaderStats();
    updateStepper(2);
    await cleanDataset();
  } catch (e) {
    alert(`Erreur lors du chargement de la line list : ${e.message}`);
  } finally {
    hideLoader();
  }
}

async function uploadReferenceFile(file, skiprows = 0, sheetName = null) {
  showLoader(`Chargement et analyse de votre référentiel ${file.name}...`);
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
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(formatApiError(err) || 'Échec du chargement du référentiel.');
    }
    const data = await res.json();

    AppState.sessionId = data.session_id;
    AppState.refFilename = data.ref_filename;
    AppState.referenceColumns = data.reference_columns || [];
    if (data.detected_spatial_mapping) {
      for (const [k, v] of Object.entries(data.detected_spatial_mapping)) {
        if (v) AppState.spatialMapping[k] = v;
      }
    }

    safeSetText('label-ref-file', `✔️ Référentiel : ${file.name}`);
    safeSetText('sublabel-ref-file', `${data.reference_rows} entités prêtes pour le géocodage`);
    safeSetText('stat-ref-filename', file.name);

    const sheetSelect = document.getElementById('ref-sheet-select');
    if (data.sheets && data.sheets.length > 1 && sheetSelect) {
      safeRemoveClass('ref-sheet-container', 'hidden');
      sheetSelect.innerHTML = data.sheets.map(s => `<option value="${escapeHtml(s)}" ${data.selected_sheet === s ? 'selected' : ''}>${escapeHtml(s)}</option>`).join('');
      safeRemoveClass('btn-reload-ref', 'hidden');
    }

    renderSpatialMappingPairs();
    renderKeyEpiVariables();
    renderColumnMapper();

    if (AppState.filename) {
      await cleanDataset();
    } else {
      alert(`Référentiel chargé avec succès (${data.reference_rows} entités). Vous pouvez maintenant charger votre Line List.`);
    }
  } catch (e) {
    alert(`Erreur lors du chargement du référentiel : ${e.message}`);
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
    const lang = AppState.language || 'FR';
    alert(I18N_TEXTS[lang]?.alert_no_file || 'Veuillez d abord charger un fichier de linelist ou cliquer sur un jeu de données exemple.');
    return;
  }

  showLoader('Exécution du nettoyage épidémiologique et du géocodage en cascade...');

  try {
    const cleanColMapping = {};
    for (const [k, v] of Object.entries(AppState.customMappings)) {
      if (v) cleanColMapping[k] = v;
    }
    const cleanSpatialMapping = {};
    for (const [k, v] of Object.entries(AppState.spatialMapping)) {
      if (v) cleanSpatialMapping[k] = v;
    }

    const payload = {
      session_id: AppState.sessionId,
      config: AppState.config,
      column_mapping: cleanColMapping,
      spatial_mapping: cleanSpatialMapping
    };

    const res = await fetch('/api/clean', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(formatApiError(err) || 'Erreur lors du nettoyage');
    }

    const data = await res.json();
    AppState.report = data.report;
    AppState.indicators = data.indicators;
    AppState.advancedMetrics = data.advanced_metrics || null;
    AppState.qualityDelta = data.quality_delta ?? 0;
    AppState.outbreakAlerts = data.outbreak_alerts || data.report?.outbreak_alerts || [];
    AppState.incidenceTrend = data.incidence_trend || data.report?.incidence_trend || null;
    AppState.epiWeekly = data.epi_curve_weekly || AppState.epiWeekly;
    AppState.epiDaily = data.epi_curve_daily || AppState.epiDaily;
    AppState.delays = data.delays || {};
    AppState.pyramid = data.pyramid || {};
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
    renderSpatialMappingPairs();
    renderKeyEpiVariables();
    renderColumnMapper();
    renderIssues();
    renderV2Kpis();
    renderCharts();
    renderDetailedEpiChart();
    updateStepper(4);

    if (AppState.activeTab === 'map') {
      setTimeout(() => {
        renderLeafletMap();
        if (AppState.leafletMap) AppState.leafletMap.invalidateSize();
      }, 150);
    }
  } catch (e) {
    alert(`Erreur: ${e.message}`);
  } finally {
    hideLoader();
  }
}

function updateStepper(step) {
  for (let i = 1; i <= 5; i++) {
    const dot = document.getElementById('step-' + i);
    const line = document.getElementById('step-line-' + i);
    if (!dot) continue;
    if (i < step) {
      dot.classList.remove('active');
      dot.classList.add('done');
      dot.innerText = '✓';
      if (line) line.classList.add('bg-emerald-500');
    } else if (i === step) {
      dot.classList.add('active');
      dot.classList.remove('done');
      dot.innerText = String(i);
    } else {
      dot.classList.remove('active', 'done');
      dot.innerText = String(i);
      if (line) line.classList.remove('bg-emerald-500');
    }
  }
  const hints = {
    1: 'Chargez votre linelist',
    2: 'Vérifiez le mapping',
    3: 'Géocodage en cascade',
    4: 'Analyse épidémique',
    5: 'Export prêt'
  };
  const h = document.getElementById('step-hint');
  if (h) h.innerText = hints[step] || '';
}

function updateHeaderStats() {
  const fileNameText = AppState.filename ? `${AppState.filename} (${AppState.report ? AppState.report.cleaned_shape[0] : AppState.rowsCount} cas)` : 'Aucun';
  safeSetText('stat-filename', fileNameText);
  safeSetText('stat-ref-filename', AppState.refFilename || 'Aucun (COD-AB intégré)');

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
    safeSetText('tab-issues-count', String(AppState.report.validation_issues ? AppState.report.validation_issues.length : 0));
  }
}

function renderDashboard() {
  if (!AppState.report) return;
  renderV2Kpis();
}

function renderV2Kpis() {
  const r = AppState.report;
  if (!r) return;
  const s = r.spatial_summary;
  const ind = AppState.indicators || {};

  safeSetText('kpi-total', String(r.cleaned_shape ? r.cleaned_shape[0] : AppState.rowsCount));
  safeSetText('kpi-total-sub', `${r.original_shape ? r.original_shape[0] : AppState.rowsCount} brutes → ${r.cleaned_shape ? r.cleaned_shape[0] : '-'} nettoyées`);

  if (s) {
    safeSetText('kpi-geo', `${s.geocoded_rate_pct}%`);
    const lvlBreakdown = [];
    if (s.level_distribution) {
      if (s.level_distribution['Locality']) lvlBreakdown.push(`${s.level_distribution['Locality']} localité`);
      if (s.level_distribution['Admin3_Ward']) lvlBreakdown.push(`${s.level_distribution['Admin3_Ward']} admin3`);
      if (s.level_distribution['Admin2_LGA']) lvlBreakdown.push(`${s.level_distribution['Admin2_LGA']} admin2`);
      if (s.level_distribution['Admin1_State']) lvlBreakdown.push(`${s.level_distribution['Admin1_State']} admin1`);
    }
    const breakdownText = lvlBreakdown.length > 0 ? lvlBreakdown.join(' • ') : '0 localisés';
    safeSetText('kpi-geo-sub', `${s.geocoded_count}/${s.total_records} cas (${breakdownText})`);
  } else {
    safeSetText('kpi-geo', 'N/A');
    safeSetText('kpi-geo-sub', '0 géocodés');
  }

  const qs = r.quality_scores_after;
  if (qs) {
    safeSetText('kpi-quality', `${qs.overall_score}%`);
    safeSetText('kpi-quality-grade', `Grade ${qs.grade} • Complétude: ${qs.completeness_score}% • Validité: ${qs.validity_score}%`);
  }

  safeSetText('kpi-epi', String(r.epi_weeks_computed || 0));
  safeSetText('kpi-coords', String(r.coordinates_cleaned ?? 0));
  safeSetText('kpi-phones', String(r.phones_standardized ?? 0));

  const alerts = AppState.outbreakAlerts || r.outbreak_alerts || [];
  safeSetText('kpi-alerts', String(alerts.length));
  safeSetText('kpi-alerts-sub', alerts.length ? `${alerts.length} semaine(s) > seuil` : 'Aucune alerte');
  safeSetText('kpi-delta', `${(AppState.qualityDelta ?? 0) > 0 ? '+' + AppState.qualityDelta : AppState.qualityDelta}%`);

  const tr = AppState.incidenceTrend || r.incidence_trend;
  if (tr) {
    const t = tr.trend || tr['trend'];
    const g = tr.weekly_growth_pct ?? tr['weekly_growth_pct'];
    const peak = tr.peak_week || tr['peak_week'];
    let label = '→ Stable';
    let cls = 'text-slate-700';
    if (t === 'increasing') {
      label = '↗ Hausse';
      cls = 'text-rose-600';
    } else if (t === 'decreasing') {
      label = '↘ Baisse';
      cls = 'text-emerald-600';
    }
    safeSetText('kpi-trend', `${label} ${g ?? 0}%`);
    const el = document.getElementById('kpi-trend');
    if (el) el.className = 'text-sm font-extrabold mt-1 ' + cls;
    safeSetText('kpi-trend-sub', peak ? `Pic ${peak}` : (ind.peak_week ? `Pic ${ind.peak_week}` : ''));
  }

  // Outbreak banner
  const banner = document.getElementById('outbreak-banner');
  if (alerts && alerts.length > 0 && banner) {
    banner.classList.remove('hidden');
    safeSetText('outbreak-title', `🚨 ${alerts.length} alerte(s) épidémique(s) détectée(s) (V2)`);
    safeSetText('outbreak-details', `Tendance: ${tr ? tr.trend : '—'} | Pic: ${ind.peak_week || (tr ? tr.peak_week : '—')} | Croissance hebdo: ${tr ? tr.weekly_growth_pct : 0}%`);
    const list = document.getElementById('outbreak-list');
    if (list) {
      list.innerHTML = alerts.slice(0, 5).map(a => `<span class="px-2 py-1 bg-amber-100 border border-amber-200 rounded font-mono text-[11px]">${escapeHtml(a.epi_week)}: ${escapeHtml(a.cases)} cas</span>`).join('');
    }
  } else if (banner) {
    banner.classList.add('hidden');
  }

  // Advanced metrics & Epi summary
  const adv = AppState.advancedMetrics;
  if (adv || ind) {
    const doublingText = adv && adv.estimated_doubling_time_weeks ? `Doubling: ${adv.estimated_doubling_time_weeks} sem` : (ind.peak_week ? `Pic: ${ind.peak_week}` : 'Doubling: N/A');
    safeSetText('epi-doubling', doublingText);

    let cfrText = 'CFR: N/A (non renseigné)';
    if (ind.has_outcome) {
      cfrText = `CFR Global: ${ind.case_fatality_ratio_pct}% (${ind.deaths} décès)`;
    } else if (ind.deaths > 0) {
      cfrText = `CFR Global: ${ind.case_fatality_ratio_pct}% (${ind.deaths} décès)`;
    } else {
      cfrText = '0 décès documenté';
    }
    safeSetText('epi-cfr', cfrText);

    const cont = document.getElementById('advanced-metrics');
    if (cont) {
      const cfrSex = adv?.cfr_by_sex_pct || {};
      const sexStr = Object.entries(cfrSex).map(([k, v]) => `${escapeHtml(k)}: ${escapeHtml(v)}%`).join(' | ') || 'Non stratifié';
      cont.innerHTML = `
        <div class="flex justify-between border-b pb-1.5"><span>Période épidémie</span><span class="font-mono font-semibold">${escapeHtml(ind.first_week || '—')} → ${escapeHtml(ind.last_week || '—')} (${ind.total_weeks || 0} sem)</span></div>
        <div class="flex justify-between border-b py-1.5"><span>Semaine Pic</span><span class="font-mono font-bold text-rose-600">${escapeHtml(ind.peak_week || '—')} (${ind.peak_cases || 0} cas)</span></div>
        <div class="flex justify-between border-b py-1.5"><span>Moyenne hebdo</span><span class="font-mono font-semibold">${ind.mean_weekly_cases || 0} cas / sem</span></div>
        <div class="flex justify-between border-b py-1.5"><span>CFR par sexe</span><span class="font-mono">${sexStr}</span></div>
        <div class="flex justify-between pt-1.5"><span>Temps de doublement</span><span class="font-mono">${adv?.estimated_doubling_time_weeks ? adv.estimated_doubling_time_weeks + ' sem' : '—'}</span></div>
      `;
    }

    const ek = document.getElementById('epicurve-kpis');
    if (ek) {
      ek.innerHTML = `
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 shadow-2xs">
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Semaine Pic (Max Cas)</div>
          <div class="text-lg font-extrabold text-rose-600 mt-0.5">${escapeHtml(ind.peak_week || '—')}</div>
          <div class="text-[11px] text-slate-500">${ind.peak_cases || 0} cas enregistrés</div>
        </div>
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 shadow-2xs">
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Moyenne Hebdomadaire</div>
          <div class="text-lg font-extrabold text-slate-900 mt-0.5">${ind.mean_weekly_cases || 0} cas / sem</div>
          <div class="text-[11px] text-slate-500">Min: ${ind.min_weekly_cases || 0} • Max: ${ind.max_weekly_cases || 0}</div>
        </div>
        <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 shadow-2xs">
          <div class="text-[11px] font-bold text-slate-500 uppercase tracking-wide">Étendue & Létalité</div>
          <div class="text-lg font-extrabold text-indigo-700 mt-0.5">${ind.total_weeks || 0} semaines</div>
          <div class="text-[11px] text-slate-500">${ind.has_outcome ? `CFR: ${ind.case_fatality_ratio_pct}% (${ind.deaths} décès)` : '0 décès documenté'}</div>
        </div>
      `;
    }

    const cards = document.getElementById('epi-advanced-cards');
    if (cards) {
      const byAge = adv?.cfr_by_age_group_pct || {};
      const entries = Object.entries(byAge);
      if (entries.length > 0) {
        cards.innerHTML = entries.slice(0, 6).map(([k, v]) => `
          <div class="bg-white border border-slate-200 rounded-xl p-3 shadow-xs">
            <div class="text-[11px] font-semibold text-slate-500">Létalité Tranche : ${escapeHtml(k)}</div>
            <div class="text-lg font-bold text-rose-700 mt-1">${v}%</div>
          </div>
        `).join('');
      } else {
        cards.innerHTML = '<div class="text-xs text-slate-500 col-span-3">Aucune issue fatale ou stratification par âge nécessaire.</div>';
      }
    }
  }

  // Quality badge in Stepper
  const qb = document.getElementById('quality-badge');
  if (qb && qs) {
    qb.classList.remove('hidden');
    qb.innerText = `Qualité ${qs.overall_score}% Grade ${qs.grade}`;
    qb.className = `px-2.5 py-1 rounded-full font-bold text-[11px] ${qs.overall_score >= 80 ? 'bg-emerald-100 text-emerald-800 border border-emerald-300' : 'bg-amber-100 text-amber-800'}`;
  }

  // Duplicates container with explanation
  const dups = r.duplicate_groups || [];
  const dupsCont = document.getElementById('dups-container');
  if (dupsCont) {
    if (dups.length === 0) {
      dupsCont.innerHTML = '<div class="text-slate-500 py-2">Aucun doublon patient détecté sur les clés d\'identité.</div>';
    } else {
      dupsCont.innerHTML = `
        <div class="text-[11px] text-slate-500 mb-2">
          ${dups.length} groupe(s) de doublons potentiels identifiés sur les critères d'identité (Nom, Âge, Sexe, Date).
        </div>
        ${dups.slice(0, 8).map(g => `
          <div class="border border-amber-200 rounded-lg p-2.5 bg-amber-50/70">
            <div class="font-bold text-slate-800 text-xs">Groupe #${escapeHtml(g.group_id)} • ${escapeHtml(g.duplicate_type)} • Score de similarité : ${Math.round((g.match_score || 0) * 100)}%</div>
            <div class="font-mono text-[11px] text-slate-600 mt-0.5">Lignes concernées : ${escapeHtml(g.row_indices ? g.row_indices.join(', ') : '')}</div>
            <div class="text-[11px] text-slate-500">IDs Patients : ${(g.case_ids || []).map(escapeHtml).join(', ') || 'N/A'}</div>
          </div>
        `).join('')}
      `;
    }
  }

  // Profiles container
  const profiles = r.column_profiles || {};
  const profCont = document.getElementById('profiles-container');
  if (profCont) {
    const rows = Object.entries(profiles).slice(0, 15).map(([col, pr]) => `
      <div class="flex items-center justify-between border-b border-slate-100 py-1.5">
        <span class="font-mono font-semibold text-slate-800">${escapeHtml(col)}</span>
        <span class="text-slate-500 font-mono text-[11px]">${pr.missing_percentage}% manq • ${pr.unique_count} uniques</span>
      </div>
    `).join('');
    profCont.innerHTML = rows || '<div class="text-slate-500">Aucun profil</div>';
  }

  // Delays container
  const delays = AppState.delays || {};
  const dCont = document.getElementById('delays-container');
  if (dCont) {
    const entries = Object.entries(delays).filter(([k, v]) => v && v.count > 0);
    if (entries.length === 0) {
      dCont.innerHTML = '<div class="text-slate-500 py-2">Pas de délais calculables (dates d\'apparition, d\'admission ou de sortie manquantes).</div>';
    } else {
      dCont.innerHTML = entries.map(([k, v]) => `
        <div class="border border-slate-200 rounded-lg p-2.5 bg-slate-50/50">
          <div class="font-bold text-slate-800 text-xs">${escapeHtml(v.name || k)}</div>
          <div class="flex justify-between text-[11px] text-slate-600 mt-1">
            <span>Médiane : <strong class="text-slate-900">${v.median_days} j</strong></span>
            <span>Moyenne : <strong class="text-slate-900">${v.mean_days} j</strong></span>
            <span>n = ${v.count} cas</span>
          </div>
        </div>
      `).join('');
    }
  }
}

function renderLeafletMap() {
  const mapContainer = document.getElementById('leaflet-map');
  if (!mapContainer || typeof L === 'undefined') return;

  if (!AppState.leafletMap) {
    AppState.leafletMap = L.map('leaflet-map').setView([14.6937, -17.4441], 6);

    const cartoVoyager = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/">CARTO</a> | PratiSIG',
      subdomains: 'abcd',
      maxZoom: 19
    });

    const cartoPositron = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO | PratiSIG',
      subdomains: 'abcd',
      maxZoom: 19
    });

    const osmFr = L.tileLayer('https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap France | PratiSIG',
      maxZoom: 20
    });

    const esriSatellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community | PratiSIG',
      maxZoom: 18
    });

    cartoVoyager.addTo(AppState.leafletMap);

    const baseMaps = {
      "🗺️ Plan CartoDB Voyager": cartoVoyager,
      "🏢 Plan CartoDB Positron": cartoPositron,
      "🌍 OpenStreetMap": osmFr,
      "🛰️ Image Satellite (Esri)": esriSatellite
    };

    L.control.layers(baseMaps, null, { position: 'topright' }).addTo(AppState.leafletMap);
    AppState.leafletMarkersLayer = L.layerGroup().addTo(AppState.leafletMap);
  }

  AppState.leafletMarkersLayer.clearLayers();

  const filterLevel = document.getElementById('map-filter-level')?.value || 'ALL';
  let pts = AppState.mapPoints || [];
  if (filterLevel !== 'ALL') {
    pts = pts.filter(p => p.match_level === filterLevel);
  }

  const mapStatsEl = document.getElementById('map-stats');
  if (mapStatsEl) {
    mapStatsEl.innerText = `${pts.length} point(s) affiché(s)`;
  }

  if (pts.length > 0) {
    const latlngs = [];
    const colors = {
      'Locality': '#10b981',
      'Admin3_Ward': '#0d9488',
      'Admin2_LGA': '#2563eb',
      'Admin1_State': '#d97706',
      'Unmatched': '#ef4444'
    };

    pts.forEach(pt => {
      if (pt.lat && pt.lng && !isNaN(pt.lat) && !isNaN(pt.lng)) {
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
          <div class="text-xs space-y-1 p-1">
            <div class="font-bold text-slate-900">${escapeHtml(pt.id)}</div>
            <div><strong>Entité :</strong> ${escapeHtml(pt.name || 'N/A')}</div>
            <div><strong>P-Code :</strong> <code class="text-emerald-700 font-bold">${escapeHtml(pt.pcode || 'N/A')}</code></div>
            <div><strong>Niveau :</strong> <span class="font-semibold">${escapeHtml(pt.match_level || 'N/A')}</span></div>
            <div><strong>Score :</strong> ${pt.score}%</div>
            <div><strong>Semaine Épi :</strong> ${escapeHtml(pt.epi_week || 'N/A')}</div>
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

function clearMapFilter() {
  const sel = document.getElementById('map-filter-level');
  if (sel) sel.value = 'ALL';
  renderLeafletMap();
}

function renderTable() {
  const tableHead = document.getElementById('data-table-head');
  const tableBody = document.getElementById('data-table-body');
  if (!tableHead || !tableBody) return;

  const mode = AppState.viewMode || 'cleaned';
  const isCleanedMode = mode === 'cleaned' || mode === 'diff';
  const cols = isCleanedMode ? (AppState.cleanedColumns || AppState.columns) : AppState.columns;
  let rows = isCleanedMode ? (AppState.cleanedPreview || AppState.rawPreview) : AppState.rawPreview;

  if (isCleanedMode && AppState.filterMatchLevel !== 'ALL') {
    rows = rows.filter(r => r['MATCH_LEVEL'] === AppState.filterMatchLevel);
  }

  if (AppState.searchQuery) {
    rows = rows.filter(r => {
      return Object.values(r).some(val => String(val).toLowerCase().includes(AppState.searchQuery));
    });
  }

  const countEl = document.getElementById('data-count');
  if (countEl) {
    countEl.innerText = `${rows.length} lignes affichées`;
  }

  let thHtml = `<tr class="bg-slate-900 text-white border-b border-slate-700">
    <th class="px-3 py-2.5 text-left text-xs font-semibold uppercase tracking-wider sticky left-0 bg-slate-900 z-10 w-12">#</th>`;

  cols.forEach(c => {
    let tagBadge = '';
    if (c === 'PCODE_ASSIGNED') tagBadge = '<span class="px-1.5 py-0.5 text-[10px] bg-emerald-500/30 text-emerald-300 font-bold rounded border border-emerald-500/40">P-Code</span>';
    else if (c === 'MATCH_LEVEL') tagBadge = '<span class="px-1.5 py-0.5 text-[10px] bg-teal-500/30 text-teal-300 font-bold rounded border border-teal-500/40">Niveau</span>';
    else if (c === 'EPI_WEEK') tagBadge = '<span class="px-1.5 py-0.5 text-[10px] bg-indigo-500/30 text-indigo-300 font-bold rounded border border-indigo-500/40">OMS</span>';
    else if (c === 'AGE_YEARS') tagBadge = '<span class="px-1.5 py-0.5 text-[10px] bg-blue-500/30 text-blue-300 font-bold rounded border border-blue-500/40">Âge</span>';

    thHtml += `
      <th class="px-3 py-2.5 text-left text-xs font-semibold tracking-wider whitespace-nowrap">
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
    if (matchLvl === 'Locality') rowBg = 'bg-emerald-50/30';
    else if (matchLvl === 'Unmatched') rowBg = 'bg-rose-50/40';

    tbHtml += `<tr class="hover:bg-blue-50/50 border-b border-slate-100 transition-colors ${rowBg}">
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
        displayVal = `<span class="px-2 py-0.5 rounded text-[10px] font-bold border ${lvlColors[val] || 'bg-slate-100 text-slate-700'}">${escapeHtml(val)}</span>`;
      } else if (c === 'PCODE_ASSIGNED' && !isNull) {
        displayVal = `<span class="font-mono font-bold text-emerald-800">${escapeHtml(val)}</span>`;
      } else if (c === 'EPI_WEEK' && !isNull) {
        displayVal = `<span class="font-mono font-semibold text-indigo-700 bg-indigo-50 px-1.5 py-0.5 rounded border border-indigo-200">${escapeHtml(val)}</span>`;
      }

      tbHtml += `<td class="px-3 py-2 text-xs text-slate-700 whitespace-nowrap">${displayVal}</td>`;
    });

    tbHtml += `</tr>`;
  });

  tableBody.innerHTML = tbHtml;
}

function renderSpatialMappingPairs() {
  const container = document.getElementById('spatial-mapping-pairs-grid');
  if (!container) return;

  const linelistCols = AppState.columns || [];
  const refCols = AppState.referenceColumns || [];

  const getLinelistColForTag = (tag, spatialKey) => {
    if (AppState.spatialMapping[spatialKey]) return AppState.spatialMapping[spatialKey];
    for (const [col, t] of Object.entries(AppState.customMappings)) {
      if (t === tag) return col;
    }
    for (const [col, meta] of Object.entries(AppState.detectedMappings)) {
      if (meta && meta.mapped_tag === tag) return col;
    }
    for (const col of linelistCols) {
      const cl = col.toLowerCase();
      if (tag === 'locality' && (cl.includes('loc') || cl.includes('vil') || cl.includes('rue') || cl.includes('quartier') || cl.includes('site') || cl.includes('camp'))) return col;
      if (tag === 'admin3' && (cl.includes('ward') || cl.includes('sous') || cl.includes('aire'))) return col;
      if (tag === 'admin2' && (cl.includes('dist') || cl.includes('lga') || cl.includes('cercle') || cl.includes('commune') || cl.includes('zone'))) return col;
      if (tag === 'admin1' && (cl.includes('state') || cl.includes('reg') || cl.includes('prov') || cl.includes('dep'))) return col;
    }
    return '';
  };

  const levels = [
    {
      id: 'locality',
      tag: 'locality',
      label: 'Localité / Village / Rue / Quartier (Niveau 1)',
      desc: 'Niveau le plus précis : village, camp, quartier, rue, structure sanitaire',
      linelistKey: 'linelist_locality_col',
      refNameKey: 'locality_name',
      refPcodeKey: 'locality_pcode',
      badge: 'bg-emerald-100 text-emerald-800'
    },
    {
      id: 'admin3',
      tag: 'admin3',
      label: 'Admin 3 : Ward / Sous-district / Aire de Santé (Niveau 2)',
      desc: 'Division administrative de niveau 3 (Ward, Sous-district, Aire de santé)',
      linelistKey: 'linelist_admin3_col',
      refNameKey: 'admin3_name',
      refPcodeKey: 'admin3_pcode',
      badge: 'bg-teal-100 text-teal-800'
    },
    {
      id: 'admin2',
      tag: 'admin2',
      label: 'Admin 2 : District / LGA / Cercle / Département (Niveau 3)',
      desc: 'Division administrative de niveau 2 (District sanitaire, LGA, Cercle, Département)',
      linelistKey: 'linelist_admin2_col',
      refNameKey: 'admin2_name',
      refPcodeKey: 'admin2_pcode',
      badge: 'bg-blue-100 text-blue-800'
    },
    {
      id: 'admin1',
      tag: 'admin1',
      label: 'Admin 1 : Région / État / Province (Niveau 4)',
      desc: 'Division administrative de niveau 1 (Région, État fédéral, Province)',
      linelistKey: 'linelist_admin1_col',
      refNameKey: 'admin1_name',
      refPcodeKey: 'admin1_pcode',
      badge: 'bg-amber-100 text-amber-800'
    }
  ];

  let html = '';
  levels.forEach(lvl => {
    const currentLinelistCol = getLinelistColForTag(lvl.tag, lvl.linelistKey);
    const currentRefNameCol = AppState.spatialMapping[lvl.refNameKey] || '';
    const currentRefPcodeCol = AppState.spatialMapping[lvl.refPcodeKey] || '';

    if (currentLinelistCol && !AppState.spatialMapping[lvl.linelistKey]) {
      AppState.spatialMapping[lvl.linelistKey] = currentLinelistCol;
    }

    html += `
      <div class="border border-slate-200 rounded-xl p-4 bg-slate-50/70 shadow-2xs flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between mb-1.5">
            <span class="font-bold text-xs text-slate-800">${escapeHtml(lvl.label)}</span>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${lvl.badge}">Étape #${lvl.id === 'locality' ? '1' : (lvl.id === 'admin3' ? '2' : (lvl.id === 'admin2' ? '3' : '4'))}</span>
          </div>
          <p class="text-[11px] text-slate-500 mb-3">${escapeHtml(lvl.desc)}</p>
          <div class="space-y-2.5">
            <div>
              <label class="block text-[11px] font-semibold text-blue-900 mb-1">
                📊 1. Colonne dans votre Line List :
              </label>
              <select class="linelist-spatial-select w-full text-xs rounded-lg border-blue-300 py-1.5 px-2 bg-white text-slate-800 focus:ring-1 focus:ring-blue-500" data-tag="${lvl.tag}" data-spkey="${lvl.linelistKey}">
                <option value="">-- Non présente dans ma Line List --</option>
                ${linelistCols.map(c => `<option value="${escapeHtml(c)}" ${currentLinelistCol === c ? 'selected' : ''}>${escapeHtml(c)}</option>`).join('')}
              </select>
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-emerald-900 mb-1">
                🗺️ 2. Colonne Nom dans le Référentiel :
              </label>
              <select class="ref-spatial-select w-full text-xs rounded-lg border-emerald-300 py-1.5 px-2 bg-white text-slate-800 focus:ring-1 focus:ring-emerald-500" data-role="${lvl.refNameKey}">
                <option value="">-- ${refCols.length > 0 ? 'Non renseigné' : 'COD-AB par défaut'} --</option>
                ${refCols.map(c => `<option value="${escapeHtml(c)}" ${currentRefNameCol === c ? 'selected' : ''}>${escapeHtml(c)}</option>`).join('')}
              </select>
            </div>
            <div>
              <label class="block text-[11px] font-semibold text-teal-900 mb-1">
                🏷️ 3. Colonne P-Code à extraire du Référentiel :
              </label>
              <select class="ref-spatial-select w-full text-xs rounded-lg border-teal-300 py-1.5 px-2 bg-white text-slate-800 focus:ring-1 focus:ring-teal-500" data-role="${lvl.refPcodeKey}">
                <option value="">-- ${refCols.length > 0 ? 'Non renseigné (Auto-généré)' : 'COD-AB P-Code par défaut'} --</option>
                ${refCols.map(c => `<option value="${escapeHtml(c)}" ${currentRefPcodeCol === c ? 'selected' : ''}>${escapeHtml(c)}</option>`).join('')}
              </select>
            </div>
          </div>
        </div>
      </div>
    `;
  });

  // Coordinates row
  const currentLat = AppState.spatialMapping['lat'] || '';
  const currentLng = AppState.spatialMapping['long'] || '';
  html += `
    <div class="border border-slate-200 rounded-xl p-4 bg-slate-50/70 shadow-2xs md:col-span-2">
      <div class="flex items-center justify-between mb-1.5">
        <span class="font-bold text-xs text-slate-800">Coordonnées GPS dans le Référentiel (Latitude Y / Longitude X)</span>
        <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-violet-100 text-violet-800">WGS84</span>
      </div>
      <p class="text-[11px] text-slate-500 mb-3">Colonnes de coordonnées géographiques à extraire du référentiel pour la carte SIG et l'export GeoJSON.</p>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div>
          <label class="block text-[11px] font-semibold text-slate-700 mb-1">🌐 Latitude (Y) Référentiel :</label>
          <select class="ref-spatial-select w-full text-xs rounded-lg border-slate-300 py-1.5 px-2 bg-white text-slate-800 focus:ring-1 focus:ring-emerald-500" data-role="lat">
            <option value="">-- ${refCols.length > 0 ? 'Auto-détecté' : 'COD-AB par défaut'} --</option>
            ${refCols.map(c => `<option value="${escapeHtml(c)}" ${currentLat === c ? 'selected' : ''}>${escapeHtml(c)}</option>`).join('')}
          </select>
        </div>
        <div>
          <label class="block text-[11px] font-semibold text-slate-700 mb-1">🌐 Longitude (X) Référentiel :</label>
          <select class="ref-spatial-select w-full text-xs rounded-lg border-slate-300 py-1.5 px-2 bg-white text-slate-800 focus:ring-1 focus:ring-emerald-500" data-role="long">
            <option value="">-- ${refCols.length > 0 ? 'Auto-détecté' : 'COD-AB par défaut'} --</option>
            ${refCols.map(c => `<option value="${escapeHtml(c)}" ${currentLng === c ? 'selected' : ''}>${escapeHtml(c)}</option>`).join('')}
          </select>
        </div>
      </div>
    </div>
  `;

  container.innerHTML = html;

  document.querySelectorAll('.linelist-spatial-select').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const tag = e.target.dataset.tag;
      const spKey = e.target.dataset.spkey;
      const colName = e.target.value;
      AppState.spatialMapping[spKey] = colName || '';
      for (const [c, t] of Object.entries(AppState.customMappings)) {
        if (t === tag) delete AppState.customMappings[c];
      }
      if (colName) {
        AppState.customMappings[colName] = tag;
      }
      renderColumnMapper();
    });
  });

  document.querySelectorAll('.ref-spatial-select').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const roleKey = e.target.dataset.role;
      AppState.spatialMapping[roleKey] = e.target.value || '';
    });
  });
}

function renderKeyEpiVariables() {
  const container = document.getElementById('key-epi-variables-grid');
  if (!container) return;

  const linelistCols = AppState.columns || [];

  const getLinelistColForTag = (tag) => {
    for (const [col, t] of Object.entries(AppState.customMappings)) {
      if (t === tag) return col;
    }
    for (const [col, meta] of Object.entries(AppState.detectedMappings)) {
      if (meta && meta.mapped_tag === tag) return col;
    }
    return '';
  };

  const keyVariables = [
    { tag: 'date_admission', label: '📅 Date Principale (Courbe Épi)', desc: 'Date d admission, de début ou de visite pour la courbe OMS' },
    { tag: 'case_id', label: '🆔 Identifiant Unique (Case ID)', desc: 'Code ou numéro de patient' },
    { tag: 'age', label: '🎂 Âge du patient', desc: 'Âge en années, mois ou jours' },
    { tag: 'sex', label: '⚧ Sexe / Genre', desc: 'Masculin / Féminin' },
    { tag: 'outcome', label: '🏥 Issue Clinique (Outcome)', desc: 'Guéri, Décédé, Sortie, En cours' },
    { tag: 'case_definition', label: '🩺 Classification du Cas', desc: 'Confirmé, Suspect, Probable, Non-cas' }
  ];

  let html = '';
  keyVariables.forEach(v => {
    const currentVal = getLinelistColForTag(v.tag);
    html += `
      <div class="border border-slate-200 rounded-xl p-3 bg-slate-50/50 shadow-2xs">
        <label class="block font-bold text-xs text-slate-800 mb-0.5">${escapeHtml(v.label)}</label>
        <p class="text-[10px] text-slate-500 mb-2">${escapeHtml(v.desc)}</p>
        <select class="key-epi-select w-full text-xs rounded-lg border-slate-300 py-1.5 px-2 bg-white text-slate-800 focus:ring-1 focus:ring-blue-500" data-tag="${v.tag}">
          <option value="">-- Non renseigné / Absent --</option>
          ${linelistCols.map(c => `<option value="${escapeHtml(c)}" ${currentVal === c ? 'selected' : ''}>${escapeHtml(c)}</option>`).join('')}
        </select>
      </div>
    `;
  });

  container.innerHTML = html;

  document.querySelectorAll('.key-epi-select').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const tag = e.target.dataset.tag;
      const colName = e.target.value;
      for (const [c, t] of Object.entries(AppState.customMappings)) {
        if (t === tag) delete AppState.customMappings[c];
      }
      if (colName) {
        AppState.customMappings[colName] = tag;
      }
      renderColumnMapper();
    });
  });
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
        <td class="px-4 py-2.5 text-xs font-mono font-semibold text-slate-800">${escapeHtml(col)}</td>
        <td class="px-4 py-2.5">
          <select class="col-map-select text-xs rounded-lg border-slate-300 py-1.5 px-2 bg-white text-slate-800 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500" data-col="${escapeHtml(col)}">
            <option value="">-- Conserver tel quel / Non Mappé --</option>
            ${Object.entries(CANONICAL_DICT).map(([t, m]) => `
              <option value="${t}" ${selectedTag === t ? 'selected' : ''}>${escapeHtml(m.label)} (${t})</option>
            `).join('')}
          </select>
        </td>
        <td class="px-4 py-2.5 text-center">
          <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${
            cat === 'geographic' ? 'bg-emerald-100 text-emerald-800' :
            (cat === 'timeline' ? 'bg-indigo-100 text-indigo-800' :
            (cat === 'demographic' ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-700'))
          }">
            ${escapeHtml(cat)}
          </span>
        </td>
        <td class="px-4 py-2.5">
          <div class="flex items-center gap-2">
            <div class="w-16 bg-slate-200 rounded-full h-1.5 overflow-hidden">
              <div class="bg-emerald-600 h-1.5 rounded-full" style="width: ${score}%"></div>
            </div>
            <span class="text-xs text-slate-500 font-mono">${score}%</span>
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
      renderSpatialMappingPairs();
      renderKeyEpiVariables();
    });
  });
}

function renderCharts() {
  if (typeof Chart === 'undefined') return;

  // Donut Chart - Cascade Spatiale
  const donutCanvas = document.getElementById('chart-cascade-donut');
  if (donutCanvas && AppState.report && AppState.report.spatial_summary) {
    if (AppState.charts.cascadeDonut) AppState.charts.cascadeDonut.destroy();

    const dist = AppState.report.spatial_summary.level_distribution || {};
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

  // Bar Chart - Courbe Épidémique Hebdomadaire OMS
  const epiCanvas = document.getElementById('chart-who-epicurve');
  if (epiCanvas) {
    if (AppState.charts.whoEpiCurve) AppState.charts.whoEpiCurve.destroy();

    const periods = AppState.epiWeekly?.periods || [];
    const seriesObj = AppState.epiWeekly?.series || {};
    const colors = ['#10b981', '#ef4444', '#3b82f6', '#f59e0b', '#8b5cf6'];

    const subEl = document.getElementById('epi-curve-subtitle');
    if (subEl) {
      if (periods.length > 0) {
        subEl.innerText = `${periods.length} semaine(s) OMS (${periods[0]} → ${periods[periods.length - 1]})`;
      } else {
        subEl.innerText = 'Aucune date valide détectée pour la courbe';
      }
    }

    if (periods.length > 0 && Object.keys(seriesObj).length > 0) {
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
}

function renderDetailedEpiChart() {
  if (typeof Chart === 'undefined') return;

  const canvas = document.getElementById('chart-epi-detailed');
  if (!canvas) return;

  if (AppState.charts.detailedEpiCurve) AppState.charts.detailedEpiCurve.destroy();

  const periods = AppState.epiWeekly?.periods || [];
  const seriesObj = AppState.epiWeekly?.series || {};
  const colors = ['#059669', '#dc2626', '#2563eb', '#d97706', '#7c3aed'];

  const subEl = document.getElementById('detailed-epicurve-subtitle');
  if (subEl) {
    if (periods.length > 0) {
      subEl.innerText = `Courbe épidémique agrégée sur ${periods.length} périodes OMS (${periods[0]} → ${periods[periods.length - 1]}).`;
    } else {
      subEl.innerText = 'Veuillez mapper la colonne Date dans l\'onglet Mapping pour générer la courbe.';
    }
  }

  if (periods.length > 0 && Object.keys(seriesObj).length > 0) {
    const datasets = Object.entries(seriesObj).map(([label, vals], idx) => ({
      label: label,
      data: vals,
      backgroundColor: colors[idx % colors.length],
      borderRadius: 4,
      stack: 'stack-detailed'
    }));

    AppState.charts.detailedEpiCurve = new Chart(canvas, {
      type: 'bar',
      data: { labels: periods, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { boxWidth: 14, font: { size: 11, weight: 'bold' } } },
          tooltip: { mode: 'index', intersect: false }
        },
        scales: {
          x: { grid: { display: false }, ticks: { font: { size: 11 } } },
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

  const issues = AppState.report.validation_issues || [];
  const summaryEl = document.getElementById('issues-summary');
  if (summaryEl) {
    summaryEl.innerText = `${issues.length} anomalie(s) détectée(s)`;
  }

  if (issues.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="text-center py-10 text-slate-400">Aucune incohérence chronologique ou clinique détectée. Félicitations !</td></tr>`;
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
        <td class="px-3 py-2 text-slate-600">${escapeHtml(iss.issue_type)}</td>
        <td class="px-3 py-2 font-mono text-slate-700">${escapeHtml(iss.column || 'N/A')}</td>
        <td class="px-3 py-2 text-slate-800">${escapeHtml(iss.message)}</td>
        <td class="px-3 py-2 text-slate-500 italic">${escapeHtml(iss.suggested_action || 'N/A')}</td>
      </tr>
    `;
  });

  tbody.innerHTML = html;
}

async function triggerDownload(url, fallbackFilename) {
  if (!AppState.sessionId) {
    alert('Veuillez d abord charger un jeu de données.');
    return;
  }
  showLoader('Génération et téléchargement du fichier...');
  try {
    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Erreur lors de la génération du fichier (${res.status})`);
    }
    const blob = await res.blob();
    const disposition = res.headers.get('content-disposition');
    let filename = fallbackFilename;
    if (disposition && disposition.includes('filename=')) {
      const match = disposition.match(/filename=["']?([^"';]+)["']?/);
      if (match && match[1]) filename = match[1];
    }
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    }, 1000);
  } catch (e) {
    window.location.href = url;
  } finally {
    hideLoader();
  }
}

function downloadExcel() {
  triggerDownload(`/api/export/excel/${AppState.sessionId}`, 'LineList_Nettoyee_PCode_PratiSIG_V2.xlsx');
}

function downloadCSV() {
  triggerDownload(`/api/export/csv/${AppState.sessionId}`, 'LineList_Nettoyee_PCode_PratiSIG.csv');
}

function downloadGeoJSON() {
  triggerDownload(`/api/export/geojson/${AppState.sessionId}`, 'LineList_Geocoded_V2.geojson');
}

function downloadScript() {
  triggerDownload(`/api/export/script/${AppState.sessionId}`, 'linelist_spatial_pipeline.py');
}

function showLoader(msg) {
  safeRemoveClass('loader-overlay', 'hidden');
  safeSetText('loader-text', msg || 'Traitement en cours...');
}

function hideLoader() {
  safeAddClass('loader-overlay', 'hidden');
}

function toggleDarkMode() {
  const isDark = document.documentElement.classList.toggle('dark');
  localStorage.setItem('lc_v2_dark', isDark ? '1' : '0');
  document.body.classList.toggle('dark', isDark);
}

function toggleLanguage() {
  const curr = AppState.language || 'FR';
  const next = curr === 'FR' ? 'EN' : 'FR';
  AppState.language = next;
  safeSetText('btn-lang', next);

  const t = I18N_TEXTS[next];
  if (t) {
    document.querySelectorAll('[data-i18n="header.subtitle"]').forEach(el => el.innerText = t.header_subtitle);
    document.querySelectorAll('[data-i18n="btn.clean"]').forEach(el => el.innerText = t.btn_clean);
  }
}

// Modal functions
function openConfigModal() {
  safeRemoveClass('config-modal', 'hidden');
}

function closeConfigModal() {
  safeAddClass('config-modal', 'hidden');
}

function openAboutModal() {
  safeRemoveClass('about-modal', 'hidden');
}

function closeAboutModal() {
  safeAddClass('about-modal', 'hidden');
}

function saveConfigAndClean() {
  AppState.config.date_order_preference = document.getElementById('cfg-date-order').value;
  AppState.config.dedup_action = document.getElementById('cfg-dedup-action').value;
  AppState.config.enable_spatial_cascade = document.getElementById('cfg-cascade').checked;
  AppState.config.compute_epi_weeks = document.getElementById('cfg-epiweek').checked;
  AppState.config.standardize_headers = document.getElementById('cfg-headers').checked;
  AppState.config.standardize_sex = document.getElementById('cfg-sex').checked;
  AppState.config.standardize_ages = document.getElementById('cfg-age').checked;
  AppState.config.validate_chronology = document.getElementById('cfg-chrono').checked;
  AppState.config.clean_coordinates = document.getElementById('cfg-coords').checked;
  AppState.config.clean_phone_numbers = document.getElementById('cfg-phones').checked;
  AppState.config.detect_outbreak_signals = document.getElementById('cfg-outbreak').checked;
  AppState.config.default_phone_country_code = document.getElementById('cfg-phone-code').value;

  const pc = document.getElementById('cfg-preset')?.value;
  AppState.config.preset = pc || null;

  closeConfigModal();
  cleanDataset();
}

// Check Dark Mode on load
if (localStorage.getItem('lc_v2_dark') === '1') {
  document.documentElement.classList.add('dark');
  document.body.classList.add('dark');
}

// Expose functions and AppState for global UI access
window.AppState = AppState;
window.cleanDataset = cleanDataset;
window.loadSampleDataset = loadSampleDataset;
window.uploadLinelistFile = uploadLinelistFile;
window.uploadReferenceFile = uploadReferenceFile;
window.reloadLinelistWithOptions = reloadLinelistWithOptions;
window.reloadReferenceWithOptions = reloadReferenceWithOptions;
window.switchTab = switchTab;
window.clearMapFilter = clearMapFilter;
window.downloadExcel = downloadExcel;
window.downloadCSV = downloadCSV;
window.downloadGeoJSON = downloadGeoJSON;
window.downloadScript = downloadScript;
window.toggleDarkMode = toggleDarkMode;
window.toggleLanguage = toggleLanguage;
window.openConfigModal = openConfigModal;
window.closeConfigModal = closeConfigModal;
window.openAboutModal = openAboutModal;
window.closeAboutModal = closeAboutModal;
window.saveConfigAndClean = saveConfigAndClean;
