const api = async (url, opts = {}) => {
  const r = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  const d = await r.json();
  if (!r.ok) throw new Error(d.error || 'Erreur');
  return d;
};

// ── Navigation ─────────────────────────────────────────────
function showTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.sidebar li').forEach(l => l.classList.remove('active'));
  document.getElementById(`tab-${name}`).classList.add('active');
  document.querySelectorAll('.sidebar li').forEach(l => {
    if (l.textContent.toLowerCase().includes(name.substring(0, 5))) l.classList.add('active');
  });
  const loaders = { dashboard: loadDashboard, produits: loadProduits, mouvements: loadMouvements, categories: loadCategories, fournisseurs: loadFournisseurs };
  if (loaders[name]) loaders[name]();
}

function openModal(id) { document.getElementById(id).classList.remove('hidden'); }
function closeModal(id) { document.getElementById(id).classList.add('hidden'); }

// ── Dashboard ─────────────────────────────────────────────
async function loadDashboard() {
  const [stats, alertes] = await Promise.all([
    api('/api/stats'),
    api('/api/produits/?alerte=true')
  ]);
  document.getElementById('s-produits').textContent = stats.total_produits;
  document.getElementById('s-valeur').textContent = stats.valeur_totale_stock.toLocaleString('fr-FR', { minimumFractionDigits: 2 });
  document.getElementById('s-alertes').textContent = stats.produits_en_alerte;
  document.getElementById('s-cats').textContent = stats.total_categories;

  const tbody = document.querySelector('#tbl-alertes tbody');
  tbody.innerHTML = alertes.produits.length === 0
    ? '<tr><td colspan="5" style="text-align:center;color:#10b981">✅ Tous les stocks sont suffisants</td></tr>'
    : alertes.produits.map(p => `
      <tr>
        <td><code>${p.reference}</code></td>
        <td>${p.nom}</td>
        <td><strong style="color:#ef4444">${p.quantite_stock}</strong></td>
        <td>${p.seuil_alerte}</td>
        <td><button class="btn sm success" onclick="openMouvement(${p.id}, '${p.nom}')">+ Entrée</button></td>
      </tr>`).join('');
}

// ── Produits ──────────────────────────────────────────────
async function loadProduits(q = '') {
  const url = q ? `/api/produits/?q=${encodeURIComponent(q)}` : '/api/produits/';
  const data = await api(url);
  const tbody = document.querySelector('#tbl-produits tbody');
  tbody.innerHTML = data.produits.map(p => `
    <tr>
      <td><code>${p.reference}</code></td>
      <td>${p.nom}</td>
      <td>${p.categorie_nom || '—'}</td>
      <td>${p.prix_unitaire.toFixed(2)} TND</td>
      <td><strong ${p.alerte_stock ? 'style="color:#ef4444"' : ''}>${p.quantite_stock}</strong></td>
      <td>${p.alerte_stock ? '<span class="badge b-red">⚠ Bas</span>' : '<span class="badge b-green">OK</span>'}</td>
      <td>
        <div class="acts">
          <button class="btn sm success" onclick="openMouvement(${p.id},'${p.nom}')">📦</button>
          <button class="btn danger" onclick="deleteProduit(${p.id})">✕</button>
        </div>
      </td>
    </tr>`).join('');
}

function searchProduits() {
  const q = document.getElementById('search-produit').value;
  loadProduits(q);
}

async function loadCategoriesSelect() {
  const data = await api('/api/categories/');
  document.getElementById('p-cat').innerHTML =
    '<option value="">— Aucune —</option>' +
    data.categories.map(c => `<option value="${c.id}">${c.nom}</option>`).join('');
}

async function createProduit() {
  try {
    await api('/api/produits/', {
      method: 'POST',
      body: JSON.stringify({
        reference: document.getElementById('p-ref').value,
        nom: document.getElementById('p-nom').value,
        prix_unitaire: parseFloat(document.getElementById('p-prix').value),
        quantite_stock: parseInt(document.getElementById('p-qte').value) || 0,
        seuil_alerte: parseInt(document.getElementById('p-seuil').value) || 5,
        categorie_id: document.getElementById('p-cat').value || null,
        description: document.getElementById('p-desc').value
      })
    });
    closeModal('modal-produit');
    loadProduits();
  } catch (e) { alert(e.message); }
}

async function deleteProduit(id) {
  if (!confirm('Supprimer ce produit et tout son historique ?')) return;
  try { await api(`/api/produits/${id}`, { method: 'DELETE' }); loadProduits(); }
  catch (e) { alert(e.message); }
}

// ── Mouvement ─────────────────────────────────────────────
function openMouvement(id, nom) {
  document.getElementById('mv-produit-id').value = id;
  document.getElementById('mv-title').textContent = `Mouvement — ${nom}`;
  openModal('modal-mouvement');
}

async function doMouvement() {
  const id = document.getElementById('mv-produit-id').value;
  try {
    await api(`/api/produits/${id}/mouvement`, {
      method: 'POST',
      body: JSON.stringify({
        type_mouvement: document.getElementById('mv-type').value,
        quantite: parseInt(document.getElementById('mv-qte').value),
        motif: document.getElementById('mv-motif').value
      })
    });
    closeModal('modal-mouvement');
    loadProduits();
    loadDashboard();
  } catch (e) { alert(e.message); }
}

// ── Mouvements historique ─────────────────────────────────
async function loadMouvements() {
  const data = await api('/api/mouvements/?limit=50');
  const typeBadge = { entree: 'b-green', sortie: 'b-red', ajustement: 'b-blue' };
  const tbody = document.querySelector('#tbl-mouvements tbody');
  tbody.innerHTML = data.mouvements.map(m => `
    <tr>
      <td style="font-size:.8rem">${new Date(m.horodatage).toLocaleString('fr-FR')}</td>
      <td><strong>${m.produit_reference}</strong><br><small>${m.produit_nom}</small></td>
      <td><span class="badge ${typeBadge[m.type_mouvement] || 'b-gray'}">${m.type_mouvement}</span></td>
      <td>${m.quantite}</td>
      <td>${m.quantite_avant}</td>
      <td>${m.quantite_apres}</td>
      <td>${m.motif || '—'}</td>
    </tr>`).join('');
}

// ── Catégories ────────────────────────────────────────────
async function loadCategories() {
  const data = await api('/api/categories/');
  const tbody = document.querySelector('#tbl-cats tbody');
  tbody.innerHTML = data.categories.map(c => `
    <tr>
      <td><strong>${c.nom}</strong></td>
      <td>${c.description || '—'}</td>
      <td>${c.nb_produits}</td>
      <td><button class="btn danger" onclick="deleteCat(${c.id})">✕</button></td>
    </tr>`).join('');
}

async function createCategorie() {
  try {
    await api('/api/categories/', { method: 'POST', body: JSON.stringify({ nom: document.getElementById('cat-nom').value, description: document.getElementById('cat-desc').value }) });
    closeModal('modal-cat');
    loadCategories();
  } catch (e) { alert(e.message); }
}

async function deleteCat(id) {
  if (!confirm('Supprimer cette catégorie ?')) return;
  try { await api(`/api/categories/${id}`, { method: 'DELETE' }); loadCategories(); }
  catch (e) { alert(e.message); }
}

// ── Fournisseurs ──────────────────────────────────────────
async function loadFournisseurs() {
  const data = await api('/api/fournisseurs/');
  const tbody = document.querySelector('#tbl-fours tbody');
  tbody.innerHTML = data.fournisseurs.map(f => `
    <tr>
      <td><strong>${f.nom}</strong></td>
      <td>${f.email || '—'}</td>
      <td>${f.telephone || '—'}</td>
      <td><button class="btn danger" onclick="deleteFour(${f.id})">✕</button></td>
    </tr>`).join('');
}

async function createFournisseur() {
  try {
    await api('/api/fournisseurs/', { method: 'POST', body: JSON.stringify({ nom: document.getElementById('four-nom').value, email: document.getElementById('four-email').value, telephone: document.getElementById('four-tel').value }) });
    closeModal('modal-four');
    loadFournisseurs();
  } catch (e) { alert(e.message); }
}

async function deleteFour(id) {
  if (!confirm('Supprimer ce fournisseur ?')) return;
  try { await api(`/api/fournisseurs/${id}`, { method: 'DELETE' }); loadFournisseurs(); }
  catch (e) { alert(e.message); }
}

// ── Init ──────────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  // Pré-charger les catégories pour le formulaire produit
  document.getElementById('modal-produit').addEventListener('click', () => {}, { once: false });
  document.querySelector('[onclick="openModal(\'modal-produit\')"]')?.addEventListener('click', loadCategoriesSelect);
});
