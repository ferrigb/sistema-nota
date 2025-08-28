from flask import Blueprint, request, jsonify
from src.models.nota import Nota
from src.models.user import db

nota_bp = Blueprint('nota', __name__)

@nota_bp.route('/notas', methods=['GET'])
def listar_notas():
    """Listar todas as notas"""
    try:
        notas = Nota.query.order_by(Nota.data_modificacao.desc()).all()
        return jsonify([nota.to_dict() for nota in notas]), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@nota_bp.route('/notas', methods=['POST'])
def criar_nota():
    """Criar uma nova nota"""
    try:
        dados = request.get_json()
        
        if not dados or 'titulo' not in dados or 'conteudo' not in dados:
            return jsonify({'erro': 'Título e conteúdo são obrigatórios'}), 400
        
        nova_nota = Nota(
            titulo=dados['titulo'],
            conteudo=dados['conteudo']
        )
        
        db.session.add(nova_nota)
        db.session.commit()
        
        return jsonify(nova_nota.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@nota_bp.route('/notas/<int:nota_id>', methods=['GET'])
def obter_nota(nota_id):
    """Obter uma nota específica"""
    try:
        nota = Nota.query.get_or_404(nota_id)
        return jsonify(nota.to_dict()), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@nota_bp.route('/notas/<int:nota_id>', methods=['PUT'])
def atualizar_nota(nota_id):
    """Atualizar uma nota existente"""
    try:
        nota = Nota.query.get_or_404(nota_id)
        dados = request.get_json()
        
        if not dados:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        if 'titulo' in dados:
            nota.titulo = dados['titulo']
        if 'conteudo' in dados:
            nota.conteudo = dados['conteudo']
        
        db.session.commit()
        return jsonify(nota.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@nota_bp.route('/notas/<int:nota_id>', methods=['DELETE'])
def excluir_nota(nota_id):
    """Excluir uma nota"""
    try:
        nota = Nota.query.get_or_404(nota_id)
        db.session.delete(nota)
        db.session.commit()
        return jsonify({'mensagem': 'Nota excluída com sucesso'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

