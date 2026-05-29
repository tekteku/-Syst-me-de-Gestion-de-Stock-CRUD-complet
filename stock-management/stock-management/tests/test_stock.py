"""
Tests unitaires — Logique métier Gestion de Stock
Run: python -m pytest tests/ -v
"""
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from models import db


@pytest.fixture
def app():
    app = create_app(testing=True)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def cat_id(client):
    """Crée une catégorie et retourne son id."""
    r = client.post('/api/categories/', json={'nom': 'Électronique', 'description': 'Matériel électronique'})
    return r.get_json()['categorie']['id']


@pytest.fixture
def produit_id(client, cat_id):
    """Crée un produit de base et retourne son id."""
    r = client.post('/api/produits/', json={
        'reference': 'REF-001',
        'nom': 'Écran 24"',
        'prix_unitaire': 299.99,
        'quantite_stock': 10,
        'seuil_alerte': 3,
        'categorie_id': cat_id
    })
    assert r.status_code == 201
    return r.get_json()['produit']['id']


# ── Tests Catégories ───────────────────────────────────────

class TestCategories:
    def test_create_categorie(self, client):
        r = client.post('/api/categories/', json={'nom': 'Fournitures', 'description': 'Papeterie'})
        assert r.status_code == 201
        data = r.get_json()
        assert data['categorie']['nom'] == 'Fournitures'

    def test_create_categorie_sans_nom(self, client):
        r = client.post('/api/categories/', json={'description': 'Sans nom'})
        assert r.status_code == 400

    def test_create_categorie_duplicate(self, client):
        client.post('/api/categories/', json={'nom': 'Test'})
        r = client.post('/api/categories/', json={'nom': 'Test'})
        assert r.status_code == 409

    def test_list_categories(self, client, cat_id):
        r = client.get('/api/categories/')
        assert r.status_code == 200
        assert r.get_json()['count'] >= 1

    def test_update_categorie(self, client, cat_id):
        r = client.put(f'/api/categories/{cat_id}', json={'nom': 'Électronique pro'})
        assert r.status_code == 200
        assert r.get_json()['categorie']['nom'] == 'Électronique pro'

    def test_delete_categorie(self, client, cat_id):
        r = client.delete(f'/api/categories/{cat_id}')
        assert r.status_code == 200
        r2 = client.get(f'/api/categories/{cat_id}')
        assert r2.status_code == 404


# ── Tests Produits ─────────────────────────────────────────

class TestProduits:
    def test_create_produit(self, client, cat_id):
        r = client.post('/api/produits/', json={
            'reference': 'REF-002',
            'nom': 'Clavier mécanique',
            'prix_unitaire': 89.0,
            'quantite_stock': 20,
            'categorie_id': cat_id
        })
        assert r.status_code == 201
        p = r.get_json()['produit']
        assert p['reference'] == 'REF-002'
        assert p['quantite_stock'] == 20

    def test_create_produit_sans_reference(self, client):
        r = client.post('/api/produits/', json={'nom': 'Test', 'prix_unitaire': 10})
        assert r.status_code == 422

    def test_create_produit_reference_duplicate(self, client, produit_id):
        r = client.post('/api/produits/', json={
            'reference': 'REF-001',
            'nom': 'Autre',
            'prix_unitaire': 50
        })
        assert r.status_code == 409

    def test_create_produit_prix_negatif(self, client):
        r = client.post('/api/produits/', json={
            'reference': 'REF-NEG',
            'nom': 'Négatif',
            'prix_unitaire': -5
        })
        assert r.status_code == 422

    def test_get_produit(self, client, produit_id):
        r = client.get(f'/api/produits/{produit_id}')
        assert r.status_code == 200
        assert r.get_json()['id'] == produit_id

    def test_get_produit_inexistant(self, client):
        r = client.get('/api/produits/9999')
        assert r.status_code == 404

    def test_update_produit(self, client, produit_id):
        r = client.put(f'/api/produits/{produit_id}', json={'nom': 'Écran 27"', 'prix_unitaire': 349.0})
        assert r.status_code == 200
        assert r.get_json()['produit']['nom'] == 'Écran 27"'

    def test_delete_produit(self, client, produit_id):
        r = client.delete(f'/api/produits/{produit_id}')
        assert r.status_code == 200
        assert client.get(f'/api/produits/{produit_id}').status_code == 404

    def test_liste_avec_recherche(self, client, produit_id):
        r = client.get('/api/produits/?q=Écran')
        assert r.status_code == 200
        assert r.get_json()['count'] >= 1

    def test_alerte_stock(self, client, produit_id):
        # seuil_alerte=3, stock=10 → pas d'alerte
        r = client.get(f'/api/produits/{produit_id}')
        assert r.get_json()['alerte_stock'] is False

        # Descendre le stock à 2
        client.post(f'/api/produits/{produit_id}/mouvement', json={
            'type_mouvement': 'sortie', 'quantite': 8, 'motif': 'Test alerte'
        })
        r2 = client.get(f'/api/produits/{produit_id}')
        assert r2.get_json()['alerte_stock'] is True


# ── Tests Mouvements de stock ──────────────────────────────

class TestMouvementsStock:
    def test_entree_stock(self, client, produit_id):
        r = client.post(f'/api/produits/{produit_id}/mouvement', json={
            'type_mouvement': 'entree',
            'quantite': 5,
            'motif': 'Réapprovisionnement'
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data['produit']['quantite_stock'] == 15  # 10 + 5
        assert data['mouvement']['quantite_avant'] == 10
        assert data['mouvement']['quantite_apres'] == 15

    def test_sortie_stock(self, client, produit_id):
        r = client.post(f'/api/produits/{produit_id}/mouvement', json={
            'type_mouvement': 'sortie',
            'quantite': 3,
            'motif': 'Vente client'
        })
        assert r.status_code == 200
        assert r.get_json()['produit']['quantite_stock'] == 7

    def test_sortie_stock_insuffisant(self, client, produit_id):
        r = client.post(f'/api/produits/{produit_id}/mouvement', json={
            'type_mouvement': 'sortie',
            'quantite': 999
        })
        assert r.status_code == 409

    def test_ajustement_stock(self, client, produit_id):
        r = client.post(f'/api/produits/{produit_id}/mouvement', json={
            'type_mouvement': 'ajustement',
            'quantite': 50,
            'motif': 'Inventaire annuel'
        })
        assert r.status_code == 200
        assert r.get_json()['produit']['quantite_stock'] == 50

    def test_mouvement_type_invalide(self, client, produit_id):
        r = client.post(f'/api/produits/{produit_id}/mouvement', json={
            'type_mouvement': 'inconnu',
            'quantite': 5
        })
        assert r.status_code == 422

    def test_mouvement_quantite_zero(self, client, produit_id):
        r = client.post(f'/api/produits/{produit_id}/mouvement', json={
            'type_mouvement': 'entree',
            'quantite': 0
        })
        assert r.status_code == 422

    def test_historique_mouvements(self, client, produit_id):
        # Faire 3 mouvements
        client.post(f'/api/produits/{produit_id}/mouvement', json={'type_mouvement': 'entree', 'quantite': 10})
        client.post(f'/api/produits/{produit_id}/mouvement', json={'type_mouvement': 'sortie', 'quantite': 2})
        client.post(f'/api/produits/{produit_id}/mouvement', json={'type_mouvement': 'entree', 'quantite': 5})

        r = client.get(f'/api/mouvements/?produit_id={produit_id}')
        assert r.status_code == 200
        # 3 mouvements + 1 initial (création) = 4
        assert r.get_json()['count'] >= 3

    def test_horodatage_present(self, client, produit_id):
        r = client.post(f'/api/produits/{produit_id}/mouvement', json={
            'type_mouvement': 'entree', 'quantite': 1
        })
        mv = r.get_json()['mouvement']
        assert 'horodatage' in mv
        assert mv['horodatage'] is not None


# ── Tests Fournisseurs ─────────────────────────────────────

class TestFournisseurs:
    def test_create_fournisseur(self, client):
        r = client.post('/api/fournisseurs/', json={
            'nom': 'TechDistrib', 'email': 'contact@techdistrib.tn',
            'telephone': '+216 71 000 100'
        })
        assert r.status_code == 201
        assert r.get_json()['fournisseur']['nom'] == 'TechDistrib'

    def test_create_fournisseur_sans_nom(self, client):
        r = client.post('/api/fournisseurs/', json={'email': 'x@y.com'})
        assert r.status_code == 400

    def test_list_fournisseurs(self, client):
        client.post('/api/fournisseurs/', json={'nom': 'F1'})
        client.post('/api/fournisseurs/', json={'nom': 'F2'})
        r = client.get('/api/fournisseurs/')
        assert r.get_json()['count'] >= 2
