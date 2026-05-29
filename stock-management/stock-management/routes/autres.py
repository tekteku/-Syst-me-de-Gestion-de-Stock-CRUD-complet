from flask import Blueprint, request, jsonify
from models import db, Categorie, Fournisseur, MouvementStock

# ── Catégories ─────────────────────────────────────────────
categories_bp = Blueprint('categories', __name__, url_prefix='/api/categories')

@categories_bp.route('/', methods=['GET'])
def list_categories():
    cats = Categorie.query.order_by(Categorie.nom).all()
    return jsonify({'count': len(cats), 'categories': [c.to_dict() for c in cats]})

@categories_bp.route('/<int:id>', methods=['GET'])
def get_categorie(id):
    return jsonify(Categorie.query.get_or_404(id).to_dict())

@categories_bp.route('/', methods=['POST'])
def create_categorie():
    data = request.get_json()
    if not data or not data.get('nom'):
        return jsonify({'error': 'Le champ nom est requis'}), 400
    if Categorie.query.filter_by(nom=data['nom']).first():
        return jsonify({'error': 'Cette catégorie existe déjà'}), 409
    c = Categorie(nom=data['nom'], description=data.get('description'))
    db.session.add(c)
    db.session.commit()
    return jsonify({'message': 'Catégorie créée', 'categorie': c.to_dict()}), 201

@categories_bp.route('/<int:id>', methods=['PUT'])
def update_categorie(id):
    c = Categorie.query.get_or_404(id)
    data = request.get_json()
    if 'nom' in data: c.nom = data['nom']
    if 'description' in data: c.description = data['description']
    db.session.commit()
    return jsonify({'message': 'Catégorie mise à jour', 'categorie': c.to_dict()})

@categories_bp.route('/<int:id>', methods=['DELETE'])
def delete_categorie(id):
    c = Categorie.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({'message': 'Catégorie supprimée'})


# ── Fournisseurs ───────────────────────────────────────────
fournisseurs_bp = Blueprint('fournisseurs', __name__, url_prefix='/api/fournisseurs')

@fournisseurs_bp.route('/', methods=['GET'])
def list_fournisseurs():
    fs = Fournisseur.query.order_by(Fournisseur.nom).all()
    return jsonify({'count': len(fs), 'fournisseurs': [f.to_dict() for f in fs]})

@fournisseurs_bp.route('/<int:id>', methods=['GET'])
def get_fournisseur(id):
    return jsonify(Fournisseur.query.get_or_404(id).to_dict())

@fournisseurs_bp.route('/', methods=['POST'])
def create_fournisseur():
    data = request.get_json()
    if not data or not data.get('nom'):
        return jsonify({'error': 'Le champ nom est requis'}), 400
    f = Fournisseur(
        nom=data['nom'], email=data.get('email'),
        telephone=data.get('telephone'), adresse=data.get('adresse')
    )
    db.session.add(f)
    db.session.commit()
    return jsonify({'message': 'Fournisseur créé', 'fournisseur': f.to_dict()}), 201

@fournisseurs_bp.route('/<int:id>', methods=['PUT'])
def update_fournisseur(id):
    f = Fournisseur.query.get_or_404(id)
    data = request.get_json()
    for field in ['nom', 'email', 'telephone', 'adresse']:
        if field in data: setattr(f, field, data[field])
    db.session.commit()
    return jsonify({'message': 'Fournisseur mis à jour', 'fournisseur': f.to_dict()})

@fournisseurs_bp.route('/<int:id>', methods=['DELETE'])
def delete_fournisseur(id):
    f = Fournisseur.query.get_or_404(id)
    db.session.delete(f)
    db.session.commit()
    return jsonify({'message': 'Fournisseur supprimé'})


# ── Mouvements ─────────────────────────────────────────────
mouvements_bp = Blueprint('mouvements', __name__, url_prefix='/api/mouvements')

@mouvements_bp.route('/', methods=['GET'])
def list_mouvements():
    produit_id = request.args.get('produit_id', type=int)
    type_mv = request.args.get('type')
    limit = request.args.get('limit', 100, type=int)

    query = MouvementStock.query
    if produit_id:
        query = query.filter_by(produit_id=produit_id)
    if type_mv:
        query = query.filter_by(type_mouvement=type_mv)

    mvs = query.order_by(MouvementStock.horodatage.desc()).limit(limit).all()
    return jsonify({'count': len(mvs), 'mouvements': [m.to_dict() for m in mvs]})
