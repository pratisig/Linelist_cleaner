function renderMappingSections() {
  const llContainer = document.getElementById('ll-mapping-container');
  const refContainer = document.getElementById('ref-mapping-container');
  if (!llContainer || !refContainer) return;

  const linelistCols = AppState.columns || [];
  const refCols = AppState.referenceColumns || [];

  const getLinelistColForTag = (tag, spatialKey) => {
    if (spatialKey && AppState.spatialMapping[spatialKey]) return AppState.spatialMapping[spatialKey];
    for (const [col, t] of Object.entries(AppState.customMappings)) {
      if (t === tag) return col;
    }
    for (const [col, meta] of Object.entries(AppState.detectedMappings)) {
      if (meta && meta.mapped_tag === tag) return col;
    }
    for (const col of linelistCols) {
      const cl = col.toLowerCase();
      if (tag === 'locality' && (cl.includes('loc') || cl.includes('vil') || cl.includes('rue') || cl.includes('quartier') || cl.includes('site') || cl.includes('camp') || cl.includes('rq'))) return col;
      if (tag === 'admin3' && (cl.includes('ward') || cl.includes('sous') || cl.includes('aire') || cl.includes('adm3'))) return col;
      if (tag === 'admin2' && (cl.includes('dist') || cl.includes('lga') || cl.includes('cercle') || cl.includes('commune') || cl.includes('zone') || cl.includes('adm2'))) return col;
      if (tag === 'admin1' && (cl.includes('state') || cl.includes('reg') || cl.includes('prov') || cl.includes('dep') || cl.includes('adm1'))) return col;
      if (tag === 'date_admission' && (cl.includes('date') || cl.includes('dt_') || cl.includes('jour') || cl.includes('admission') || cl.includes('onset') || cl.includes('consult'))) return col;
      if (tag === 'case_id' && (cl.includes('id') || cl.includes('code') || cl.includes('num'))) return col;
      if (tag === 'age' && cl.includes('age')) return col;
      if (tag === 'sex' && (cl.includes('sex') || cl.includes('genr'))) return col;
      if (tag === 'outcome' && (cl.includes('out') || cl.includes('issu') || cl.includes('statut') || cl.includes('etat') || cl.includes('evol'))) return col;
      if (tag === 'case_definition' && (cl.includes('class') || cl.includes('diag') || cl.includes('def'))) return col;
    }
    return '';
  };

  // 1. Line List Fields (Version 1 Streamlit structure)
  const llFields = [
    { tag: 'date_admission', spatialKey: null, label: "📅 Date d'admission / de notification", desc: "Date principale pour la courbe épidémique OMS" },
    { tag: 'locality', spatialKey: 'linelist_locality_col', label: "🏘️ Localité / Village / Rue (Admin 4)", desc: "Niveau 1 de la cascade de géocodage" },
    { tag: 'admin3', spatialKey: 'linelist_admin3_col', label: "Ward / Canton / Aire de Santé (Admin 3)", desc: "Niveau 2 (Fallback 1)" },
    { tag: 'admin2', spatialKey: 'linelist_admin2_col', label: "🏛️ LGA / District / Cercle (Admin 2)", desc: "Niveau 3 (Fallback 2)" },
    { tag: 'admin1', spatialKey: 'linelist_admin1_col', label: "🗺️ State / Région / Province (Admin 1)", desc: "Niveau 4 (Fallback 3)" },
    { tag: 'case_id', spatialKey: null, label: "🆔 Identifiant Unique (Case ID)", desc: "Code patient unique" },
    { tag: 'age', spatialKey: null, label: "🎂 Âge du patient", desc: "Âge pour la pyramide démographique" },
    { tag: 'sex', spatialKey: null, label: "⚧ Sexe / Genre", desc: "Masculin / Féminin" },
    { tag: 'outcome', spatialKey: null, label: "🏥 Issue Clinique / Statut vital", desc: "Guéri, Décédé, Sortie" },
    { tag: 'case_definition', spatialKey: null, label: "🩺 Classification du Cas", desc: "Confirmé, Suspect, Probable" }
  ];

  let llHtml = '';
  llFields.forEach(f => {
    const currentVal = getLinelistColForTag(f.tag, f.spatialKey);
    if (f.spatialKey && currentVal && !AppState.spatialMapping[f.spatialKey]) {
      AppState.spatialMapping[f.spatialKey] = currentVal;
    }
    if (currentVal && !AppState.customMappings[currentVal]) {
      AppState.customMappings[currentVal] = f.tag;
    }

    llHtml += `
      <div class="bg-blue-50/60 border border-blue-100 rounded-lg p-2.5">
        <label class="block font-bold text-xs text-blue-950 mb-0.5">${escapeHtml(f.label)}</label>
        <span class="text-[10px] text-slate-500 block mb-1.5">${escapeHtml(f.desc)}</span>
        <select class="ll-mapping-select w-full text-xs rounded-lg border-blue-200 py-1.5 px-2 bg-white text-slate-800 focus:ring-1 focus:ring-blue-500" data-tag="${f.tag}" data-spkey="${f.spatialKey || ''}">
          <option value="">-- Non renseigné / Absent --</option>
          ${linelistCols.map(c => `<option value="${escapeHtml(c)}" ${currentVal === c ? 'selected' : ''}>${escapeHtml(c)}</option>`).join('')}
        </select>
      </div>
    `;
  });
  llContainer.innerHTML = llHtml;

  // 2. Reference Fields (Version 1 Streamlit structure)
  const refFields = [
    { role: 'locality_name', label: "🏷️ Nom Localité (Admin 4)", desc: "Colonne du référentiel à matcher au Niveau 1" },
    { role: 'locality_pcode', label: "🔑 P-Code Localité", desc: "P-Code officiel à extraire pour la localité" },
    { role: 'admin3_name', label: "🏷️ Nom Admin 3 (Ward / Aire de Santé)", desc: "Colonne du référentiel à matcher au Niveau 2" },
    { role: 'admin3_pcode', label: "🔑 P-Code Admin 3", desc: "P-Code Admin 3 à extraire" },
    { role: 'admin2_name', label: "🏷️ Nom Admin 2 (LGA / District)", desc: "Colonne du référentiel à matcher au Niveau 3" },
    { role: 'admin2_pcode', label: "🔑 P-Code Admin 2", desc: "P-Code Admin 2 à extraire" },
    { role: 'admin1_name', label: "🏷️ Nom Admin 1 (State / Région)", desc: "Colonne du référentiel à matcher au Niveau 4" },
    { role: 'admin1_pcode', label: "🔑 P-Code Admin 1", desc: "P-Code Admin 1 à extraire" },
    { role: 'lat', label: "🌐 Latitude (Y) WGS84", desc: "Coordonnée Y pour la carte SIG" },
    { role: 'long', label: "🌐 Longitude (X) WGS84", desc: "Coordonnée X pour la carte SIG" }
  ];

  let refHtml = '';
  refFields.forEach(f => {
    const currentVal = AppState.spatialMapping[f.role] || '';
    refHtml += `
      <div class="bg-emerald-50/60 border border-emerald-100 rounded-lg p-2.5">
        <label class="block font-bold text-xs text-emerald-950 mb-0.5">${escapeHtml(f.label)}</label>
        <span class="text-[10px] text-slate-500 block mb-1.5">${escapeHtml(f.desc)}</span>
        <select class="ref-mapping-select w-full text-xs rounded-lg border-emerald-200 py-1.5 px-2 bg-white text-slate-800 focus:ring-1 focus:ring-emerald-500" data-role="${f.role}">
          <option value="">-- ${refCols.length > 0 ? 'Non renseigné' : 'Référentiel COD-AB intégré'} --</option>
          ${refCols.map(c => `<option value="${escapeHtml(c)}" ${currentVal === c ? 'selected' : ''}>${escapeHtml(c)}</option>`).join('')}
        </select>
      </div>
    `;
  });
  refContainer.innerHTML = refHtml;

  // Attach event listeners
  document.querySelectorAll('.ll-mapping-select').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const tag = e.target.dataset.tag;
      const spKey = e.target.dataset.spkey;
      const colName = e.target.value;
      if (spKey) AppState.spatialMapping[spKey] = colName || '';
      for (const [c, t] of Object.entries(AppState.customMappings)) {
        if (t === tag) delete AppState.customMappings[c];
      }
      if (colName) {
        AppState.customMappings[colName] = tag;
      }
      renderColumnMapper();
    });
  });

  document.querySelectorAll('.ref-mapping-select').forEach(sel => {
    sel.addEventListener('change', (e) => {
      const role = e.target.dataset.role;
      AppState.spatialMapping[role] = e.target.value || '';
    });
  });
}