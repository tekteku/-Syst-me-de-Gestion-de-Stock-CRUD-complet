# 📦 Système de Gestion de Stock — CRUD complet

API REST + interface web pour la gestion de stock avec historique horodaté.

## Stack

- **Backend** : Python / Flask
- **Base de données** : SQLite (via SQLAlchemy ORM)
- **Tests** : pytest (27 tests unitaires)
- **Frontend** : HTML / CSS / JavaScript Vanilla

## Fonctionnalités

- 🏷️ CRUD complet : Produits, Catégories, Fournisseurs
- 🔄 Mouvements de stock : entrée / sortie / ajustement
- ⏱️ Historique horodaté de tous les mouvements
- ⚠️ Alertes automatiques si stock ≤ seuil d'alerte
- 🔍 Recherche produits par nom ou référence
- 📊 Dashboard avec valeur totale du stock
- ✅ Validation des entrées + gestion d'erreurs HTTP

## Installation locale

### Prérequis

- Python >= 3.10

### 1. Cloner le dépôt

```bash
git clone https://github.com/tekteku/-Syst-me-de-Gestion-de-Stock-CRUD-complet.git
cd stock-management
```

### 2. Créer un environnement virtuel et installer les dépendances

```bash
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows

pip install -r requirements.txt
```

### 3. Démarrer l'application

```bash
python app.py
```

Ouvrir : http://localhost:5000

La base SQLite et les données de démo sont créées automatiquement au premier lancement.

### 4. Lancer les tests

```bash
pip install pytest
python -m pytest tests/ -v
```

## Structure du projet

```
stock-management/
├── app.py                   # Point d'entrée Flask + seed data
├── models.py                # Modèles SQLAlchemy (4 entités)
├── requirements.txt
├── routes/
│   ├── produits.py          # CRUD produits + mouvements
│   └── autres.py            # CRUD catégories, fournisseurs, historique
├── tests/
│   └── test_stock.py        # 27 tests unitaires pytest
├── templates/
│   └── index.html           # Interface SPA
└── static/
    ├── css/style.css
    └── js/app.js
```

## Modélisation des données

```
Categorie (1) ─────────── (N) Produit (N) ─────── (1) Fournisseur
                                 │
                                 │ (1)
                                 ▼
                          MouvementStock (N)
                    (horodatage, avant, après)
```

## API Endpoints

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/api/produits/` | Lister (filtre: q, categorie_id, alerte) |
| POST | `/api/produits/` | Créer produit |
| PUT | `/api/produits/:id` | Modifier |
| DELETE | `/api/produits/:id` | Supprimer |
| POST | `/api/produits/:id/mouvement` | Entrée / Sortie / Ajustement |
| GET | `/api/mouvements/` | Historique horodaté |
| GET | `/api/categories/` | CRUD catégories |
| GET | `/api/fournisseurs/` | CRUD fournisseurs |
| GET | `/api/stats` | Statistiques globales |

## Auteur

[tekteku](https://github.com/tekteku)
