"""
report_service.py - PDF Report Generator
Generates professional weekly stock reports with charts
"""

import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
from datetime import datetime
import pandas as pd

# Set style
plt.style.use('dark_background')

# Custom colors
COLORS = {
    'bg': '#0f172a',
    'card': '#1e293b',
    'primary': '#22d3ee',
    'secondary': '#a855f7',
    'success': '#22c55e',
    'warning': '#eab308',
    'danger': '#ef4444',
    'text': '#ffffff',
    'text_muted': '#94a3b8'
}

SECTOR_COLORS = ['#22d3ee', '#a855f7', '#22c55e', '#eab308', '#ef4444', 
                  '#3b82f6', '#ec4899', '#14b8a6', '#f97316', '#6366f1']


def generate_pdf_report(df: pd.DataFrame) -> bytes:
    """
    Generate a professional PDF report from stock data.
    Returns PDF as bytes.
    """
    
    # Filter out invalid data (remove N/A and null super_scores)
    df = df.dropna(subset=['super_score'])
    df = df[df['super_score'] > 0]
    
    # Clean sector data - remove N/A, NA, empty strings, None, and 'nan' string
    if 'setor' in df.columns:
        df = df[df['setor'].notna()]
        # Convert to string and strip
        df['setor'] = df['setor'].astype(str).str.strip()
        # Filter out invalid strings
        invalid_sectors = ['N/A', 'NA', 'n/a', 'na', '', 'None', 'null', 'nan', 'NaN']
        df = df[~df['setor'].isin(invalid_sectors)]
    
    # Create PDF in memory with Full HD aspect ratio
    buffer = io.BytesIO()
    
    # A4 landscape for better layout (bigger than Full HD in print terms)
    fig_width = 16.54  # A4 landscape width in inches
    fig_height = 11.69  # A4 landscape height in inches
    dpi = 150  # High DPI for better quality
    
    with PdfPages(buffer) as pdf:
        # ========== PAGE 1: COVER + SUMMARY ==========
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi, facecolor=COLORS['bg'])
        
        # 1. Header/Title Section (Top Half)
        fig.text(0.5, 0.85, 'RELATÓRIO SEMANAL', fontsize=48, fontweight='bold', 
                 color=COLORS['primary'], ha='center', va='center')
        fig.text(0.5, 0.75, 'Análise de Ações', fontsize=28, 
                 color=COLORS['text'], ha='center', va='center')
        fig.text(0.5, 0.70, datetime.now().strftime('%d/%m/%Y'), fontsize=20, 
                 color=COLORS['text_muted'], ha='center', va='center')
        
        # 2. Summary Stats (Bottom Half)
        total_stocks = len(df)
        avg_score = df['super_score'].mean() if 'super_score' in df.columns else 0
        top_stock = df.iloc[0]['papel'] if len(df) > 0 else 'N/A'
        top_score = df.iloc[0]['super_score'] if len(df) > 0 else 0
        
        # Create a visual card for stats
        rect = plt.Rectangle((0.2, 0.15), 0.6, 0.4, facecolor=COLORS['card'], 
                             edgecolor=COLORS['primary'], linewidth=2, transform=fig.transFigure,
                             zorder=0)
        fig.add_artist(rect)
        
        stats_text = f"RESUMO DE MERCADO\n\n" \
                     f"Total de Ações:   {total_stocks}\n" \
                     f"Score Médio:      {avg_score:.1f}\n" \
                     f"Melhor Ação:      {top_stock} ({top_score:.1f})\n" \
                     f"Data Base:        {datetime.now().strftime('%d/%m/%Y')}"
                     
        fig.text(0.5, 0.35, stats_text, fontsize=20, 
                 color=COLORS['text'], ha='center', va='center', 
                 family='monospace', linespacing=1.8)
        
        pdf.savefig(fig, facecolor=COLORS['bg'])
        plt.close(fig)
        
        # ========== PAGE 2: TOP 10 + SECTOR ANALYSIS ==========
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi, facecolor=COLORS['bg'])
        
        # 3. Top 10 Table (Top Half)
        fig.text(0.5, 0.95, 'TOP 10 OPORTUNIDADES', fontsize=24, fontweight='bold', 
                 color=COLORS['primary'], ha='center')
                 
        ax_table = fig.add_axes([0.1, 0.55, 0.8, 0.35])
        ax_table.axis('off')
        
        top10 = df.nlargest(10, 'super_score')
        columns = ['#', 'Ticker', 'Setor', 'Preço', 'P/L', 'DY', 'Score']
        data = []
        for i, row in enumerate(top10.itertuples(), 1):
             data.append([
                str(i),
                row.papel,
                str(row.setor)[:15] if pd.notna(row.setor) else '-',
                f"{row.cotacao:.2f}",
                f"{row.p_l:.1f}x",
                f"{row.dividend_yield:.1f}%",
                f"{row.super_score:.1f}"
            ])
            
        table = ax_table.table(cellText=data, colLabels=columns, loc='center', cellLoc='center',
                              colWidths=[0.05, 0.15, 0.2, 0.15, 0.15, 0.15, 0.15])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.8)
        
        # Style table
        for (row, col), cell in table.get_celld().items():
            cell.set_facecolor(COLORS['bg'])
            cell.set_edgecolor(COLORS['text_muted'])
            if row == 0:
                cell.set_text_props(color=COLORS['primary'], weight='bold')
                cell.set_facecolor(COLORS['card'])
            else:
                cell.set_text_props(color=COLORS['text'])
                if row % 2 == 0: cell.set_facecolor(COLORS['card'])

        # 4. Sector Analysis (Bottom Half - Two Charts)
        fig.text(0.5, 0.48, 'ANÁLISE SETORIAL', fontsize=24, fontweight='bold', 
                 color=COLORS['primary'], ha='center')

        gs = fig.add_gridspec(1, 2, left=0.1, right=0.9, top=0.42, bottom=0.08, wspace=0.3)
        
        # Pie Chart
        ax1 = fig.add_subplot(gs[0])
        if 'setor' in df.columns:
            sector_counts = df['setor'].value_counts().head(5)
            if len(sector_counts) > 0:
                ax1.pie(sector_counts.values, labels=[s[:15] for s in sector_counts.index], 
                       autopct='%1.0f%%', colors=SECTOR_COLORS, startangle=90,
                       textprops={'color': COLORS['text'], 'fontsize': 9})
        ax1.set_title('Distribuição', color=COLORS['text'], fontsize=12)
        
        # Bar Chart
        ax2 = fig.add_subplot(gs[1])
        if 'setor' in df.columns and 'p_l' in df.columns:
            valid_df = df[(df['p_l'].notna()) & (df['p_l'] > 0) & (df['p_l'] < 50)]
            if len(valid_df) > 0:
                sector_pl = valid_df.groupby('setor')['p_l'].mean().sort_values().head(5)
                ax2.barh(np.arange(len(sector_pl)), sector_pl.values, color=SECTOR_COLORS, height=0.6)
                ax2.set_yticks(np.arange(len(sector_pl)))
                ax2.set_yticklabels([s[:15] for s in sector_pl.index], fontsize=9, color=COLORS['text'])
                ax2.spines['top'].set_visible(False)
                ax2.spines['right'].set_visible(False)
                ax2.spines['bottom'].set_color(COLORS['text_muted'])
                ax2.spines['left'].set_color(COLORS['text_muted'])
                ax2.tick_params(colors=COLORS['text'])
                
        ax2.set_title('Setores Mais Baratos (P/L)', color=COLORS['text'], fontsize=12)

        pdf.savefig(fig, facecolor=COLORS['bg'])
        plt.close(fig)

        # ========== PAGE 3: SCORE DISTRIBUTION + METRICS ==========
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi, facecolor=COLORS['bg'])
        
        # 5. Score Distribution (Top Half)
        fig.text(0.5, 0.95, 'DISTRIBUIÇÃO DA QUALIDADE', fontsize=24, fontweight='bold', 
                 color=COLORS['primary'], ha='center')
                 
        ax_hist = fig.add_axes([0.15, 0.6, 0.7, 0.3])
        ax_hist.set_facecolor(COLORS['card'])
        
        scores = df['super_score'].dropna()
        n, bins, patches = ax_hist.hist(scores, bins=20, color=COLORS['primary'], alpha=0.8)
        
        for i, patch in enumerate(patches):
            if bins[i] < 8: patch.set_facecolor(COLORS['danger'])
            elif bins[i] < 12: patch.set_facecolor(COLORS['warning'])
            else: patch.set_facecolor(COLORS['success'])
            
        ax_hist.set_xlabel('Super Score', color=COLORS['text'])
        ax_hist.set_ylabel('Qtd Ações', color=COLORS['text'])
        ax_hist.spines['top'].set_visible(False)
        ax_hist.spines['right'].set_visible(False)
        ax_hist.tick_params(colors=COLORS['text'])
        
        # 6. Market Health Metrics (Bottom Half)
        fig.text(0.5, 0.45, 'MÉTRICAS DE MERCADO', fontsize=24, fontweight='bold', 
                 color=COLORS['primary'], ha='center')
                 
        # Create 3 cards for metrics
        metrics_data = [
            {'label': 'Média P/L', 'value': f"{df['p_l'].mean():.1f}x", 'desc': 'Valuation Médio'},
            {'label': 'Média DY', 'value': f"{df['dividend_yield'].mean():.1f}%", 'desc': 'Retorno em Dividendos'},
            {'label': 'Média ROE', 'value': f"{df['roe'].mean():.1f}%", 'desc': 'Rentabilidade Patrimonial'}
        ]
        
        for i, metric in enumerate(metrics_data):
            x_pos = 0.1 + (i * 0.3)
            rect = plt.Rectangle((x_pos, 0.15), 0.2, 0.2, facecolor=COLORS['card'], 
                               edgecolor=COLORS['secondary'], linewidth=1, transform=fig.transFigure)
            fig.add_artist(rect)
            
            fig.text(x_pos + 0.1, 0.28, metric['label'], fontsize=16, color=COLORS['text_muted'], ha='center')
            fig.text(x_pos + 0.1, 0.23, metric['value'], fontsize=24, color=COLORS['text'], ha='center', fontweight='bold')
            fig.text(x_pos + 0.1, 0.19, metric['desc'], fontsize=10, color=COLORS['text_muted'], ha='center')

        pdf.savefig(fig, facecolor=COLORS['bg'])
        plt.close(fig)

        # ========== PAGE 4: DISCLAIMER + FOOTER ==========
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi, facecolor=COLORS['bg'])
        
        # 8. Disclaimer (Main Content)
        fig.text(0.5, 0.8, 'AVISO LEGAL IMPORTANTE', fontsize=32, fontweight='bold', 
                 color=COLORS['warning'], ha='center')
                 
        disclaimer_text = """
        Este relatório foi gerado automaticamente por algoritmos de análise quantitativa.
        
        1. Natureza Informativa: Este documento tem caráter meramente informativo e educacional.
        
        2. Não é Recomendação: Nenhuma informação contida aqui deve ser interpretada como
           recomendação de compra, venda ou manutenção de ativos.
           
        3. Riscos: Investimentos em renda variável estão sujeitos a riscos de mercado,
           incluindo a perda do capital investido.
           
        4. Fonte de Dados: Os dados são provenientes de fontes públicas e podem conter
           imprecisões ou atrasos.
           
        5. Consulte um Profissional: Sempre consulte um analista CNPI ou consultor CVM
           antes de tomar decisões de investimento.
        """
        
        fig.text(0.1, 0.5, disclaimer_text, fontsize=16, color=COLORS['text'], 
                 ha='left', va='center', linespacing=2, family='sans-serif')
        
        # 9. Footer (Bottom)
        fig.text(0.5, 0.15, 'NORTE AÇÕES', fontsize=24, fontweight='bold', 
                 color=COLORS['primary'], ha='center')
        fig.text(0.5, 0.10, 'Tecnologia em Análise de Investimentos', fontsize=14, 
                 color=COLORS['text_muted'], ha='center')
        
        # Version marker for debug
        timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')
        fig.text(0.9, 0.05, f"Pág. 4/4 - {timestamp} (v2.1)", 
                 fontsize=10, color=COLORS['text_muted'], ha='right')
        
        pdf.savefig(fig, facecolor=COLORS['bg'])
        plt.close(fig)
    
    buffer.seek(0)
    return buffer.read()
