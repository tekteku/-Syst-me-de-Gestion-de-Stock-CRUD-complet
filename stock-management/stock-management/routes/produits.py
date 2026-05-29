from flask import Blueprint, request, jsonify
from models import db, Produit, MouvementStock

produits_bp = Blueprint('produits', __name__, url_prefix='/api/produits')


def validate_produit(data, partial=False):
    """Validation des champs produit."""
    errors = []
    if not partial:
        if not data.get('reference'):
            errors.append('reference est requis')
        if not data.get('nom'):
            errors.append('nom est requis')
        if data.get('prix_unitaire') is None:
            errors.append('prix_unitaire est requis')
    if 'prix_unitaire' in data and data['prix_unitaire'] < 0:
        errors.append('prix_unitaire doit être positif')
    if 'quantite_stock' in data and data['quantite_stock'] < 0:
        errors.append('quantite_stock doit être positive ou nulle')
    return errors


# GET /api/produits
@produits_bp.route('/', methods=['GET'])
def list_produits():
    categorie_id = request.args.get('categorie_id', type=int)
    alerte = request.args.get('alerte')  # ?alerte=true
    search = request.args.get('q', '')

    query = Produit.query

    if categorie_id:
        query = query.filter_by(categorie_id=categorie_id)
    if search:
        query = query.filter(
            (Produit.nom.ilike(f'%{search}%')) | (Produit.reference.ilike(f'%{search}%'))
        )
    if alerte == 'true':
        query = query.filter(Produit.quantite_stock <= Produit.seuil_alerte)

    produits = query.order_by(Produit.nom).all()
    return jsonify({'count': len(produits), 'produits': [p.to_dict() for p in produits]})


# GET /api/produits/:id
@produits_bp.route('/<int:id>', methods=['GET'])
def get_produit(id):
    p = Produit.query.get_or_404(id, description='Produit introuvable')
    return jsonify(p.to_dict())


# POST /api/produits
@produits_bp.route('/', methods=['POST'])
def create_produit():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Corps JSON manquant'}), 400

    errors = validate_produit(data)
    if errors:
        return jsonify({'error': 'Validation échouée', 'details': errors}), 422

    if Produit.query.filter_by(reference=data['reference']).first():
        return jsonify({'error': f"Référence '{data['reference']}' déjà utilisée"}), 409

    p = Produit(
        reference=data['reference'],
        nom=data['nom'],
        description=data.get('description'),
        prix_unitaire=data['prix_unitaire'],
        quantite_stock=data.get('quantite_stock', 0),
        seuil_alerte=data.get('seuil_alerte', 5),
        categorie_id=data.get('categorie_id'),
        fournisseur_id=data.get('fournisseur_id')
    )
    db.session.add(p)
    db.session.flush()  # obtenir l'id

    # Enregistrer le mouvement initial si stock > 0
    if p.quantite_stock > 0:
        mv = MouvementStock(
            produit_id=p.id,
            type_mouvement='entree',
            quantite=p.quantite_stock,
            quantite_avant=0,
            quantite_apres=p.quantite_stock,
            motif='Stock initial à la création'
        )
        db.session.add(mv)

    db.session.commit()
    return jsonify({'message': 'Produit créé', 'produit': p.to_dict()}), 201


# PUT /api/produits/:id
@produits_bp.route('/<int:id>', methods=['PUT'])
def update_produit(id):
    p = Produit.query.get_or_404(id, description='Produit introuvable')
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Corps JSON manquant'}), 400

    errors = validate_produit(data, partial=True)
    if errors:
        return jsonify({'error': 'Validation échouée', 'details': errors}), 422

    for field in ['nom', 'description', 'prix_unitaire', 'seuil_alerte', 'categorie_id', 'fournisseur_id']:
        if field in data:
            setattr(p, field, data[field])

    db.session.commit()
    return jsonify({'message': 'Produit mis à jour', 'produit': p.to_dict()})


# DELETE /api/produits/:id
@produits_bp.route('/<int:id>', methods=['DELETE'])
def delete_produit(id):
    p = Produit.query.get_or_404(id, description='Produit introuvable')
    db.session.delete(p)
    db.session.commit()
    return jsonify({'message': 'Produit supprimé'})


# POST /api/produits/:id/mouvement — Entrée / Sortie / Ajustement
@produits_bp.route('/<int:id>/mouvement', methods=['POST'])
def mouvement_stock(id):
    p = Produit.query.get_or_404(id, description='Produit introuvable')
    data = request.get_json()

    type_mv = data.get('type_mouvement')
    quantite = data.get('quantite')
    motif = data.get('motif', '')

    if type_mv not in ('entree', 'sortie', 'ajustement'):
        return jsonify({'error': "type_mouvement doit être 'entree', 'sortie' ou 'ajustement'"}), 422
    if not isinstance(quantite, int) or quantite <= 0:
        return jsonify({'error': 'quantite doit être un entier strictement positif'}), 422

    avant = p.quantite_stock

    if type_mv == 'entree':
        p.quantite_stock += quantite
    elif type_mv == 'sortie':
        if p.quantite_stock < quantite:
            return jsonify({'error': f'Stock insuffisant ({p.quantite_stock} disponible)'}), 409
        p.quantite_stock -= quantite
    elif type_mv == 'ajustement':
        p.quantite_stock = quantite  # quantite = nouvelle valeur absolue

    mv = MouvementStock(
        produit_id=p.id,
        type_mouvement=type_mv,
        quantite=quantite,
        quantite_avant=avant,
        quantite_apres=p.quantite_stock,
        motif=motif
    )
    db.session.add(mv)
    db.session.commit()

    return jsonify({
        'message': 'Mouvement enregistré',
        'produit': p.to_dict(),
        'mouvement': mv.to_dict()
    })
