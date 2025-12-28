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
    
    # Clean sector data - remove N/A, NA, empty strings, None
    if 'setor' in df.columns:
        df = df[df['setor'].notna()]
        df = df[~df['setor'].isin(['N/A', 'NA', 'n/a', 'na', '', ' ', 'None', 'null'])]
        df = df[df['setor'].str.strip() != '']
    
    # Create PDF in memory with Full HD aspect ratio
    buffer = io.BytesIO()
    
    # A4 landscape for better layout (bigger than Full HD in print terms)
    fig_width = 16.54  # A4 landscape width in inches
    fig_height = 11.69  # A4 landscape height in inches
    dpi = 150  # High DPI for better quality
    
    with PdfPages(buffer) as pdf:
        # ========== PAGE 1: Cover + Summary ==========
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi, facecolor=COLORS['bg'])
        
        # Title
        fig.text(0.5, 0.75, 'RELATÓRIO SEMANAL', fontsize=48, fontweight='bold', 
                 color=COLORS['primary'], ha='center', va='center')
        fig.text(0.5, 0.65, 'Análise de Ações', fontsize=28, 
                 color=COLORS['text'], ha='center', va='center')
        fig.text(0.5, 0.55, datetime.now().strftime('%d/%m/%Y'), fontsize=20, 
                 color=COLORS['text_muted'], ha='center', va='center')
        
        # Summary stats
        total_stocks = len(df)
        avg_score = df['super_score'].mean() if 'super_score' in df.columns else 0
        top_stock = df.iloc[0]['papel'] if len(df) > 0 else 'N/A'
        top_score = df.iloc[0]['super_score'] if len(df) > 0 else 0
        
        stats_text = f"""
        Total de Ações Analisadas: {total_stocks}
        Score Médio: {avg_score:.1f}
        TOP 1: {top_stock} (Score: {top_score:.1f})
        """
        fig.text(0.5, 0.35, stats_text, fontsize=16, 
                 color=COLORS['text'], ha='center', va='center', 
                 family='monospace', linespacing=2)
        
        fig.text(0.5, 0.1, 'NORTE AÇÕES - Análise Quantitativa de Mercado', 
                 fontsize=14, color=COLORS['text_muted'], ha='center')
        
        pdf.savefig(fig, facecolor=COLORS['bg'])
        plt.close(fig)
        
        # ========== PAGE 2: Sector Analysis (FIXED LAYOUT) ==========
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi, facecolor=COLORS['bg'])
        
        # Title
        fig.text(0.5, 0.95, 'ANÁLISE SETORIAL', fontsize=32, fontweight='bold', 
                 color=COLORS['primary'], ha='center')
        
        # Create subplots with proper spacing
        gs = fig.add_gridspec(1, 2, left=0.08, right=0.92, top=0.85, bottom=0.15, 
                              wspace=0.25)
        
        # Pie Chart (Left) - Distribution by Sector
        ax1 = fig.add_subplot(gs[0])
        ax1.set_facecolor(COLORS['bg'])
        
        if 'setor' in df.columns:
            sector_counts = df['setor'].value_counts().head(6)
            # Filter out empty sectors
            sector_counts = sector_counts[sector_counts.index.notna()]
            sector_counts = sector_counts[sector_counts.index != '']
            
            if len(sector_counts) > 0:
                wedges, texts, autotexts = ax1.pie(
                    sector_counts.values, 
                    labels=[s[:15] for s in sector_counts.index],  # Truncate labels
                    autopct='%1.0f%%',
                    colors=SECTOR_COLORS[:len(sector_counts)],
                    pctdistance=0.75,
                    labeldistance=1.15,
                    startangle=90,
                    wedgeprops={'linewidth': 2, 'edgecolor': COLORS['bg']}
                )
                for text in texts:
                    text.set_color(COLORS['text'])
                    text.set_fontsize(10)
                for autotext in autotexts:
                    autotext.set_color(COLORS['bg'])
                    autotext.set_fontsize(9)
                    autotext.set_fontweight('bold')
        
        ax1.set_title('Distribuição por Setor', color=COLORS['text'], fontsize=14, pad=15)
        
        # Bar Chart (Right) - P/L by Sector  
        ax2 = fig.add_subplot(gs[1])
        ax2.set_facecolor(COLORS['bg'])
        
        if 'setor' in df.columns and 'p_l' in df.columns:
            # Filter valid P/L values only
            valid_df = df[(df['p_l'].notna()) & (df['p_l'] > 0) & (df['p_l'] < 50)]
            
            if len(valid_df) > 0:
                sector_pl = valid_df.groupby('setor')['p_l'].mean().dropna()
                sector_pl = sector_pl[sector_pl.index.notna()]
                sector_pl = sector_pl[sector_pl.index != '']
                sector_pl = sector_pl.sort_values().head(5)  # Top 5 cheapest
                
                if len(sector_pl) > 0:
                    y_pos = np.arange(len(sector_pl))
                    bars = ax2.barh(y_pos, sector_pl.values, color=SECTOR_COLORS[:len(sector_pl)], height=0.6)
                    ax2.set_yticks(y_pos)
                    ax2.set_yticklabels([s[:15] for s in sector_pl.index], fontsize=10)
                    ax2.tick_params(colors=COLORS['text'])
                    ax2.spines['top'].set_visible(False)
                    ax2.spines['right'].set_visible(False)
                    ax2.spines['bottom'].set_color(COLORS['text_muted'])
                    ax2.spines['left'].set_color(COLORS['text_muted'])
                    
                    # Add value labels
                    for bar, val in zip(bars, sector_pl.values):
                        ax2.text(val + 0.1, bar.get_y() + bar.get_height()/2, 
                                f'{val:.1f}x', va='center', fontsize=9, color=COLORS['text'])
        
        ax2.set_title('P/L Médio por Setor (Menores)', color=COLORS['text'], fontsize=14, pad=15)
        ax2.set_xlabel('P/L', color=COLORS['text_muted'])
        
        pdf.savefig(fig, facecolor=COLORS['bg'])
        plt.close(fig)
        
        # ========== PAGE 3: Top 10 Ranking ==========
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi, facecolor=COLORS['bg'])
        
        # Title
        fig.text(0.5, 0.95, 'TOP 10 OPORTUNIDADES', fontsize=32, fontweight='bold', 
                 color=COLORS['primary'], ha='center')
        fig.text(0.5, 0.90, 'Ranking por Super Score', fontsize=16, 
                 color=COLORS['text_muted'], ha='center')
        
        # Table
        ax = fig.add_axes([0.08, 0.15, 0.84, 0.70])  # [left, bottom, width, height]
        ax.set_facecolor(COLORS['bg'])
        ax.axis('off')
        
        # Prepare data
        top10 = df.nlargest(10, 'super_score')
        
        columns = ['#', 'Ticker', 'Setor', 'Preço', 'P/L', 'P/VP', 'DY', 'ROE', 'Score']
        data = []
        for i, row in enumerate(top10.itertuples(), 1):
            data.append([
                str(i),
                row.papel,
                str(row.setor)[:15] if pd.notna(row.setor) else '-',
                f"R$ {row.cotacao:.2f}" if pd.notna(row.cotacao) else '-',
                f"{row.p_l:.1f}x" if pd.notna(row.p_l) else '-',
                f"{row.p_vp:.2f}" if pd.notna(row.p_vp) else '-',
                f"{row.dividend_yield:.1f}%" if pd.notna(row.dividend_yield) else '-',
                f"{row.roe:.1f}%" if pd.notna(row.roe) else '-',
                f"{row.super_score:.1f}"
            ])
        
        # Create table
        table = ax.table(
            cellText=data,
            colLabels=columns,
            loc='upper center',
            cellLoc='center',
            colWidths=[0.05, 0.10, 0.15, 0.12, 0.10, 0.10, 0.10, 0.10, 0.10]
        )
        
        # Style table
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1.2, 2.2)  # Scale for better readability
        
        # Header styling
        for (row, col), cell in table.get_celld().items():
            cell.set_facecolor(COLORS['bg'])
            cell.set_edgecolor(COLORS['text_muted'])
            if row == 0:
                cell.set_text_props(color=COLORS['primary'], weight='bold')
                cell.set_facecolor(COLORS['card'])
            else:
                cell.set_text_props(color=COLORS['text'])
                # Alternate row colors
                if row % 2 == 0:
                    cell.set_facecolor('#1a1a2e')
        
        pdf.savefig(fig, facecolor=COLORS['bg'])
        plt.close(fig)
        
        # ========== PAGE 4: Score Distribution ==========
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi, facecolor=COLORS['bg'])
        
        # Title
        fig.text(0.5, 0.95, 'DISTRIBUIÇÃO DE SCORES', fontsize=32, fontweight='bold', 
                 color=COLORS['primary'], ha='center')
        
        # Histogram
        ax = fig.add_axes([0.15, 0.20, 0.70, 0.60])
        ax.set_facecolor(COLORS['card'])
        
        scores = df['super_score'].dropna()
        
        n, bins, patches = ax.hist(scores, bins=20, color=COLORS['primary'], 
                                    edgecolor=COLORS['bg'], alpha=0.8)
        
        # Color gradient
        for i, patch in enumerate(patches):
            if bins[i] < 8:
                patch.set_facecolor(COLORS['danger'])
            elif bins[i] < 12:
                patch.set_facecolor(COLORS['warning'])
            else:
                patch.set_facecolor(COLORS['success'])
        
        ax.axvline(scores.mean(), color=COLORS['text'], linestyle='--', linewidth=2, 
                    label=f'Média: {scores.mean():.1f}')
        ax.legend(loc='upper right', facecolor=COLORS['card'], edgecolor=COLORS['text_muted'])
        
        ax.set_xlabel('Super Score', color=COLORS['text'], fontsize=12)
        ax.set_ylabel('Quantidade de Ações', color=COLORS['text'], fontsize=12)
        ax.tick_params(colors=COLORS['text'])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(COLORS['text_muted'])
        ax.spines['left'].set_color(COLORS['text_muted'])
        
        # Legend
        fig.text(0.25, 0.10, '■ Score < 8 (Alto Risco)', fontsize=12, color=COLORS['danger'])
        fig.text(0.45, 0.10, '■ Score 8-12 (Moderado)', fontsize=12, color=COLORS['warning'])
        fig.text(0.65, 0.10, '■ Score > 12 (Qualidade)', fontsize=12, color=COLORS['success'])
        
        pdf.savefig(fig, facecolor=COLORS['bg'])
        plt.close(fig)
        
        # ========== PAGE 5: Disclaimer ==========
        fig = plt.figure(figsize=(fig_width, fig_height), dpi=dpi, facecolor=COLORS['bg'])
        
        fig.text(0.5, 0.70, 'DISCLAIMER', fontsize=32, fontweight='bold', 
                 color=COLORS['warning'], ha='center')
        
        disclaimer_text = """
Este relatório é gerado automaticamente com base em indicadores fundamentalistas.

As informações contidas neste documento não constituem recomendação de compra ou venda.

Rentabilidade passada não é garantia de rentabilidade futura.

Consulte um profissional certificado antes de tomar decisões de investimento.

Os dados são obtidos de fontes públicas e podem conter imprecisões.
        """
        
        fig.text(0.5, 0.45, disclaimer_text, fontsize=14, 
                 color=COLORS['text'], ha='center', va='center',
                 linespacing=2.5, style='italic')
        
        fig.text(0.5, 0.15, f'Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M")}', 
                 fontsize=12, color=COLORS['text_muted'], ha='center')
        fig.text(0.5, 0.10, 'NORTE AÇÕES © 2024', fontsize=14, 
                 color=COLORS['primary'], ha='center', fontweight='bold')
        
        pdf.savefig(fig, facecolor=COLORS['bg'])
        plt.close(fig)
    
    buffer.seek(0)
    return buffer.read()
