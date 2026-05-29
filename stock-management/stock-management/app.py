from flask import Flask, jsonify, send_from_directory
from models import db, Categorie, Fournisseur, Produit, MouvementStock
from routes.produits import produits_bp
from routes.autres import categories_bp, fournisseurs_bp, mouvements_bp
import os


def create_app(testing=False):
    app = Flask(__name__, static_folder='static', template_folder='templates')

    if testing:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock.db'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)

    # Enregistrer les blueprints
    app.register_blueprint(produits_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(fournisseurs_bp)
    app.register_blueprint(mouvements_bp)

    # Health check
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'OK', 'message': 'Stock Management API opérationnel'})

    # Stats globales
    @app.route('/api/stats')
    def stats():
        total_produits = Produit.query.count()
        total_categories = Categorie.query.count()
        total_fournisseurs = Fournisseur.query.count()
        alertes = Produit.query.filter(Produit.quantite_stock <= Produit.seuil_alerte).count()
        valeur_stock = db.session.query(
            db.func.sum(Produit.prix_unitaire * Produit.quantite_stock)
        ).scalar() or 0

        return jsonify({
            'total_produits': total_produits,
            'total_categories': total_categories,
            'total_fournisseurs': total_fournisseurs,
            'produits_en_alerte': alertes,
            'valeur_totale_stock': round(valeur_stock, 2)
        })

    # Servir l'interface frontend
    @app.route('/')
    def index():
        return send_from_directory('templates', 'index.html')

    return app


def seed_data(app):
    """Données de démonstration."""
    with app.app_context():
        if Categorie.query.count() > 0:
            return  # Déjà initialisé

        # Catégories
        cats = [
            Categorie(nom='Électronique', description='Matériel informatique et électronique'),
            Categorie(nom='Fournitures bureau', description='Papeterie et consommables'),
            Categorie(nom='Outillage', description='Outils et équipements'),
        ]
        db.session.add_all(cats)
        db.session.flush()

        # Fournisseurs
        frs = [
            Fournisseur(nom='TechDistrib Tunisie', email='contact@techdistrib.tn', telephone='+216 71 000 100'),
            Fournisseur(nom='Bureau Plus', email='info@bureauplus.tn', telephone='+216 71 000 200'),
        ]
        db.session.add_all(frs)
        db.session.flush()

        # Produits
        produits_data = [
            ('ELEC-001', 'Écran 24" Full HD', 299.99, 15, 5, cats[0].id, frs[0].id),
            ('ELEC-002', 'Clavier mécanique USB', 89.90, 30, 8, cats[0].id, frs[0].id),
            ('ELEC-003', 'Souris ergonomique', 45.00, 2, 5, cats[0].id, frs[0].id),  # En alerte
            ('FOUR-001', 'Ramette papier A4 (500f)', 12.50, 100, 20, cats[1].id, frs[1].id),
            ('FOUR-002', 'Stylos bille (boîte 12)', 8.00, 50, 10, cats[1].id, frs[1].id),
            ('OUTIL-001', 'Perceuse électrique 750W', 189.00, 4, 2, cats[2].id, None),
        ]

        for ref, nom, prix, qte, seuil, cat_id, four_id in produits_data:
            p = Produit(
                reference=ref, nom=nom, prix_unitaire=prix,
                quantite_stock=qte, seuil_alerte=seuil,
                categorie_id=cat_id, fournisseur_id=four_id
            )
            db.session.add(p)
            db.session.flush()
            # Mouvement initial
            if qte > 0:
                mv = MouvementStock(
                    produit_id=p.id, type_mouvement='entree',
                    quantite=qte, quantite_avant=0, quantite_apres=qte,
                    motif='Stock initial'
                )
                db.session.add(mv)

        db.session.commit()
        print('✅ Données de démonstration insérées')


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        seed_data(app)
    print('\n🚀 Stock Management API démarré')
    print('   → http://localhost:5000')
    app.run(debug=True, port=5000)
