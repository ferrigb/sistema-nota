from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.loja import Loja

loja_bp = Blueprint('loja', __name__)

@loja_bp.route('/loja', methods=['GET'])
def get_loja_info():
    loja = Loja.query.first()
    if loja:
        return jsonify(loja.to_dict()), 200
    return jsonify({'mensagem': 'Dados da loja não configurados'}), 404

@loja_bp.route('/loja', methods=['POST'])
def configure_loja_info():
    data = request.get_json()
    if not data:
        return jsonify({'erro': 'Dados não fornecidos'}), 400

    nome = data.get('nome')
    endereco = data.get('endereco')
    telefone = data.get('telefone')

    if not nome or not endereco or not telefone:
        return jsonify({'erro': 'Nome, endereço e telefone são obrigatórios'}), 400

    loja = Loja.query.first()
    if loja:
        loja.nome = nome
        loja.endereco = endereco
        loja.telefone = telefone
    else:
        loja = Loja(nome=nome, endereco=endereco, telefone=telefone)
        db.session.add(loja)
    
    db.session.commit()
    return jsonify(loja.to_dict()), 200


