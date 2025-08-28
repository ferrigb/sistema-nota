from flask import Blueprint, request, jsonify
from src.models.venda import Venda, ItemVenda
from src.models.user import db

venda_bp = Blueprint("venda", __name__)

@venda_bp.route("/vendas", methods=["GET"])
def listar_vendas():
    """Listar todas as vendas finalizadas para o histórico"""
    try:
        vendas = Venda.query.filter_by(finalizada=True).order_by(Venda.data_venda.desc()).all()
        return jsonify([venda.to_dict() for venda in vendas]), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@venda_bp.route("/vendas/todas", methods=["GET"])
def listar_todas_vendas():
    """Listar todas as vendas (para debug)"""
    try:
        vendas = Venda.query.all()
        return jsonify([{
            "id": venda.id,
            "finalizada": venda.finalizada,
            "total": float(venda.total),
            "data_venda": venda.data_venda.isoformat(),
            "itens_count": len(venda.itens)
        } for venda in vendas]), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@venda_bp.route("/vendas/atual", methods=["GET"])
def obter_venda_atual():
    """Obter a venda atual (não finalizada) - sempre garantir venda limpa"""
    try:
        # Buscar venda não finalizada
        venda_atual = Venda.query.filter_by(finalizada=False).first()
        
        # Se não existe venda não finalizada, criar uma nova
        if not venda_atual:
            nova_venda = Venda()
            db.session.add(nova_venda)
            db.session.commit()
            return jsonify(nova_venda.to_dict()), 200
        
        # Se existe venda não finalizada, verificar se tem itens
        # Se tiver itens, retornar a venda atual
        # Se não tiver itens, também retornar (venda limpa)
        return jsonify(venda_atual.to_dict()), 200
        
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@venda_bp.route("/vendas/limpar-atual", methods=["POST"])
def limpar_venda_atual():
    """Limpar completamente a venda atual e criar uma nova"""
    try:
        # Buscar venda não finalizada
        venda_atual = Venda.query.filter_by(finalizada=False).first()
        
        if venda_atual:
            # Remover todos os itens da venda atual
            for item in venda_atual.itens:
                db.session.delete(item)
            
            # Remover a venda atual
            db.session.delete(venda_atual)
            db.session.commit()
        
        # Criar nova venda limpa
        nova_venda = Venda()
        db.session.add(nova_venda)
        db.session.commit()
        
        return jsonify(nova_venda.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

@venda_bp.route("/vendas", methods=["POST"])
def criar_venda():
    """Criar uma nova venda"""
    try:
        nova_venda = Venda()
        db.session.add(nova_venda)
        db.session.commit()
        
        return jsonify(nova_venda.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

@venda_bp.route("/vendas/<int:venda_id>", methods=["GET"])
def obter_venda(venda_id):
    """Obter uma venda específica"""
    try:
        venda = Venda.query.get_or_404(venda_id)
        return jsonify(venda.to_dict()), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@venda_bp.route("/vendas/<int:venda_id>/itens", methods=["POST"])
def adicionar_item(venda_id):
    """Adicionar item à venda"""
    try:
        venda = Venda.query.get_or_404(venda_id)
        
        if venda.finalizada:
            return jsonify({"erro": "Não é possível adicionar itens a uma venda finalizada"}), 400
        
        dados = request.get_json()
        
        if not dados or "nome_produto" not in dados or "preco_unitario" not in dados:
            return jsonify({"erro": "Nome do produto e preço unitário são obrigatórios"}), 400
        
        quantidade = dados.get("quantidade", 1.0)
        tipo_quantidade = dados.get("tipo_quantidade", "unidade")      
        novo_item = ItemVenda(
            venda_id=venda_id,
            nome_produto=dados["nome_produto"],
            quantidade=quantidade,
            tipo_quantidade=tipo_quantidade,
            preco_unitario=dados["preco_unitario"]
        )
        # Calcular subtotal
        novo_item.calcular_subtotal()
        
        db.session.add(novo_item)
        
        # Recalcular total da venda
        venda.calcular_total()
        
        db.session.commit()
        
        return jsonify(venda.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

@venda_bp.route("/vendas/<int:venda_id>/itens/<int:item_id>", methods=["PUT"])
def atualizar_item(venda_id, item_id):
    """Atualizar quantidade ou preço de um item"""
    try:
        venda = Venda.query.get_or_404(venda_id)
        
        if venda.finalizada:
            return jsonify({"erro": "Não é possível modificar itens de uma venda finalizada"}), 400
        
        item = ItemVenda.query.filter_by(id=item_id, venda_id=venda_id).first_or_404()
        dados = request.get_json()
        if not dados:
            return jsonify({"erro": "Dados não fornecidos"}), 400
        
        if "quantidade" in dados:
            item.quantidade = dados["quantidade"]
        if "tipo_quantidade" in dados:
            item.tipo_quantidade = dados["tipo_quantidade"]
        if "preco_unitario" in dados:
            item.preco_unitario = dados["preco_unitario"]   
        # Recalcular subtotal do item
        item.calcular_subtotal()
        
        # Recalcular total da venda
        venda.calcular_total()
        
        db.session.commit()
        
        return jsonify(venda.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

@venda_bp.route("/vendas/<int:venda_id>/itens/<int:item_id>", methods=["DELETE"])
def remover_item(venda_id, item_id):
    """Remover item da venda"""
    try:
        venda = Venda.query.get_or_404(venda_id)
        
        if venda.finalizada:
            return jsonify({"erro": "Não é possível remover itens de uma venda finalizada"}), 400
        
        item = ItemVenda.query.filter_by(id=item_id, venda_id=venda_id).first_or_404()
        
        db.session.delete(item)
        
        # Recalcular total da venda
        venda.calcular_total()
        
        db.session.commit()
        
        return jsonify(venda.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

@venda_bp.route("/vendas/<int:venda_id>/finalizar", methods=["PUT"])
def finalizar_venda(venda_id):
    """Finalizar uma venda"""
    try:
        print(f"DEBUG: Iniciando finalização da venda {venda_id}")
        venda = Venda.query.get_or_404(venda_id)
        print(f"DEBUG: Venda encontrada - ID: {venda.id}, Finalizada: {venda.finalizada}")
        
        if venda.finalizada:
            return jsonify({"erro": "Venda já está finalizada"}), 400
        
        if not venda.itens:
            return jsonify({"erro": "Não é possível finalizar uma venda sem itens"}), 400
        
        # Verificar se foi enviado nome do cliente e forma de pagamento
        dados = request.get_json()
        if dados:
            if "nome_cliente" in dados:
                venda.nome_cliente = dados["nome_cliente"]
                print(f"DEBUG: Nome do cliente definido: {venda.nome_cliente}")
            if "forma_pagamento" in dados:
                venda.forma_pagamento = dados["forma_pagamento"]
                print(f"DEBUG: Forma de pagamento definida: {venda.forma_pagamento}")
        
        print(f"DEBUG: Marcando venda como finalizada")
        venda.finalizada = True
        venda.calcular_total()
        
        print(f"DEBUG: Antes do commit - Finalizada: {venda.finalizada}")
        
        # Forçar o flush e commit
        db.session.flush()
        db.session.commit()
        
        # Verificar imediatamente após commit
        db.session.refresh(venda)
        print(f"DEBUG: Após commit e refresh - Finalizada: {venda.finalizada}")
        
        # Verificar se realmente foi salvo com nova query
        venda_verificacao = db.session.query(Venda).filter_by(id=venda_id).first()
        print(f"DEBUG: Verificação com nova query - Finalizada: {venda_verificacao.finalizada}")
        
        return jsonify(venda.to_dict()), 200
    except Exception as e:
        print(f"DEBUG: Erro na finalização: {str(e)}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500

@venda_bp.route("/vendas/<int:venda_id>", methods=["DELETE"])
def excluir_venda(venda_id):
    """Excluir uma venda (apenas se não estiver finalizada)"""
    try:
        venda = Venda.query.get_or_404(venda_id)
        
        if venda.finalizada:
            return jsonify({"erro": "Não é possível excluir uma venda finalizada"}), 400
        
        db.session.delete(venda)
        db.session.commit()
        
        return jsonify({"mensagem": "Venda excluída com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"erro": str(e)}), 500



