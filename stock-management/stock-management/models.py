from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


# ── Catégorie ──────────────────────────────────────────────
class Categorie(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    produits = db.relationship('Produit', backref='categorie', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'description': self.description,
            'nb_produits': len(self.produits),
            'created_at': self.created_at.isoformat()
        }


# ── Fournisseur ────────────────────────────────────────────
class Fournisseur(db.Model):
    __tablename__ = 'fournisseurs'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(120), unique=True)
    telephone = db.Column(db.String(30))
    adresse = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    produits = db.relationship('Produit', backref='fournisseur', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'nom': self.nom,
            'email': self.email,
            'telephone': self.telephone,
            'adresse': self.adresse,
            'created_at': self.created_at.isoformat()
        }


# ── Produit ────────────────────────────────────────────────
class Produit(db.Model):
    __tablename__ = 'produits'

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), unique=True, nullable=False)
    nom = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    prix_unitaire = db.Column(db.Float, nullable=False, default=0.0)
    quantite_stock = db.Column(db.Integer, nullable=False, default=0)
    seuil_alerte = db.Column(db.Integer, default=5)          # Alerte si stock < seuil
    categorie_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mouvements = db.relationship('MouvementStock', backref='produit', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'reference': self.reference,
            'nom': self.nom,
            'description': self.description,
            'prix_unitaire': self.prix_unitaire,
            'quantite_stock': self.quantite_stock,
            'seuil_alerte': self.seuil_alerte,
            'alerte_stock': self.quantite_stock <= self.seuil_alerte,
            'categorie_id': self.categorie_id,
            'categorie_nom': self.categorie.nom if self.categorie else None,
            'fournisseur_id': self.fournisseur_id,
            'fournisseur_nom': self.fournisseur.nom if self.fournisseur else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


# ── Mouvement de stock ─────────────────────────────────────
class MouvementStock(db.Model):
    __tablename__ = 'mouvements_stock'

    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits.id'), nullable=False)
    type_mouvement = db.Column(db.String(20), nullable=False)   # entree | sortie | ajustement
    quantite = db.Column(db.Integer, nullable=False)
    quantite_avant = db.Column(db.Integer, nullable=False)       # stock avant mouvement
    quantite_apres = db.Column(db.Integer, nullable=False)       # stock après mouvement
    motif = db.Column(db.String(255))
    horodatage = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'produit_id': self.produit_id,
            'produit_nom': self.produit.nom if self.produit else None,
            'produit_reference': self.produit.reference if self.produit else None,
            'type_mouvement': self.type_mouvement,
            'quantite': self.quantite,
            'quantite_avant': self.quantite_avant,
            'quantite_apres': self.quantite_apres,
            'motif': self.motif,
            'horodatage': self.horodatage.isoformat()
        }
