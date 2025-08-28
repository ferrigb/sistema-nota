from flask import Blueprint, request, jsonify, make_response
from src.models.venda import Venda, ItemVenda
from src.models.user import db
from datetime import datetime
import io

ticket_bp = Blueprint('ticket', __name__)

@ticket_bp.route('/vendas/<int:venda_id>/ticket', methods=['GET'])
def gerar_ticket(venda_id):
    """Gerar ticket da venda em formato texto"""
    try:
        venda = Venda.query.get_or_404(venda_id)
        
        if not venda.finalizada:
            return jsonify({'erro': 'Só é possível gerar ticket de vendas finalizadas'}), 400
        
        # Gerar ticket em formato texto
        data_formatada = venda.data_venda.strftime("%d/%m/%Y às %H:%M")
        
        ticket_content = f"""
🛒 TICKET DE VENDA
{'='*50}

Venda #{venda.id}
Data: {data_formatada}

PRODUTOS:
{'-'*50}
"""
        
        for item in venda.itens:
            ticket_content += f"{item.nome_produto}\n"
            ticket_content += f"  Qtd: {item.quantidade:.1f} x R$ {item.preco_unitario:.2f} = R$ {item.subtotal:.2f}\n\n"
        
        ticket_content += f"""
{'-'*50}
TOTAL: R$ {venda.total:.2f}
{'='*50}

Obrigado pela preferência!
Volte sempre!

{'='*50}
"""
        
        # Preparar resposta
        response = make_response(ticket_content)
        response.headers['Content-Type'] = 'text/plain; charset=utf-8'
        response.headers['Content-Disposition'] = f'attachment; filename=ticket_venda_{venda.id}.txt'
        
        return response
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

