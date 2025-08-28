from flask import Blueprint, request, jsonify, make_response
from src.models.venda import Venda, ItemVenda
from src.models.user import db
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import io

ticket_bp = Blueprint('ticket', __name__)

@ticket_bp.route('/vendas/<int:venda_id>/ticket', methods=['GET'])
def gerar_ticket(venda_id):
    """Gerar ticket da venda em PDF"""
    try:
        venda = Venda.query.get_or_404(venda_id)
        
        if not venda.finalizada:
            return jsonify({'erro': 'Só é possível gerar ticket de vendas finalizadas'}), 400
        
        # Criar PDF em memória
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1,  # Centralizado
            textColor=colors.darkgreen
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.darkblue
        )
        
        normal_style = styles['Normal']
        normal_style.fontSize = 11
        
        # Conteúdo do PDF
        story = []
        
        # Título
        story.append(Paragraph("🛒 TICKET DE VENDA", title_style))
        story.append(Spacer(1, 20))
        
        # Informações da venda
        data_formatada = venda.data_venda.strftime("%d/%m/%Y às %H:%M")
        story.append(Paragraph(f"<b>Venda #{venda.id}</b>", header_style))
        story.append(Paragraph(f"Data: {data_formatada}", normal_style))
        story.append(Spacer(1, 20))
        
        # Tabela de produtos
        story.append(Paragraph("Produtos:", header_style))
        
        # Dados da tabela
        data = [['Produto', 'Qtd', 'Preço Unit.', 'Subtotal']]
        
        for item in venda.itens:
            data.append([
                item.nome_produto,
                f"{item.quantidade:.1f}",
                f"R$ {item.preco_unitario:.2f}",
                f"R$ {item.subtotal:.2f}"
            ])
        
        # Criar tabela
        table = Table(data, colWidths=[3*inch, 0.8*inch, 1.2*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Alinhar números ao centro
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
        
        # Total
        total_style = ParagraphStyle(
            'Total',
            parent=styles['Normal'],
            fontSize=16,
            alignment=1,  # Centralizado
            textColor=colors.darkgreen,
            spaceAfter=20
        )
        
        story.append(Paragraph(f"<b>TOTAL: R$ {venda.total:.2f}</b>", total_style))
        story.append(Spacer(1, 30))
        
        # Rodapé
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            alignment=1,  # Centralizado
            textColor=colors.grey
        )
        
        story.append(Paragraph("Obrigado pela preferência!", footer_style))
        story.append(Paragraph("Volte sempre!", footer_style))
        
        # Gerar PDF
        doc.build(story)
        
        # Preparar resposta
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=ticket_venda_{venda.id}.pdf'
        
        return response
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

