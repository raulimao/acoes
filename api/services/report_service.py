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
import qrcode
from PIL import Image
from io import BytesIO
import matplotlib.image as mpimg

# Set style
plt.style.use('dark_background')

# --- PROFESSIONAL DESIGN SYSTEM ---
COLORS = {
    'bg': '#0f172a',        # Slam 900 (Deep Navy)
    'card': '#1e293b',      # Slate 800
    'primary': '#fbbf24',   # Amber 400 (Gold-like) for accents
    'secondary': '#38bdf8', # Sky 400 (Professional Blue)
    'success': '#4ade80',   # Green 400
    'warning': '#facc15',   # Yellow 400
    'danger': '#f87171',    # Red 400
    'text': '#f8fafc',      # Slate 50
    'text_muted': '#94a3b8',# Slate 400
    'border': '#334155'     # Slate 700
}

SECTOR_COLORS = ['#38bdf8', '#fbbf24', '#4ade80', '#f87171', '#a78bfa', 
                  '#f472b6', '#2dd4bf', '#fb923c', '#94a3b8', '#a3e635']

# Dimensions (A4 Landscape)
FIG_WIDTH = 16.54
FIG_HEIGHT = 11.69
DPI = 150

def generate_pdf_report(df: pd.DataFrame) -> bytes:
    """
    Generate a professional PDF report from stock data.
    Returns PDF as bytes.
    """
    
    # Filter and Clean Data
    df = _clean_data(df)
    
    # Create PDF in memory
    buffer = io.BytesIO()
    
    with PdfPages(buffer) as pdf:
        # 1. Cover Page
        _create_cover_page(pdf, df)
        
        # 2. Top Opportunities
        _create_top_stocks_page(pdf, df)
        
        # 3. Market Analysis
        _create_market_analysis_page(pdf, df)
        
        # 4. Detailed Analysis (Top Stock)
        if len(df) > 0:
            top_stock = df.iloc[0]
            _create_one_pager(pdf, top_stock)

        # 5. Glossary
        _create_glossary_page(pdf)

    buffer.seek(0)
    return buffer.read()

def _clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocesses the dataframe."""
    df = df.dropna(subset=['super_score'])
    df = df[df['super_score'] > 0]
    
    if 'setor' in df.columns:
        df = df[df['setor'].notna()]
        df['setor'] = df['setor'].astype(str).str.strip()
        invalid_sectors = ['N/A', 'NA', 'n/a', 'na', '', 'None', 'null', 'nan', 'NaN']
        df = df[~df['setor'].isin(invalid_sectors)]
    
    return df

def _setup_page():
    """Creates a blank page with correct dimensions and background."""
    fig = plt.figure(figsize=(FIG_WIDTH, FIG_HEIGHT), dpi=DPI, facecolor=COLORS['bg'])
    return fig

def _draw_header(fig, title, subtitle=None):
    """Draws the consistent header."""
    # Logo / Brand Area
    fig.text(0.05, 0.95, "NORTE AÇÕES", fontsize=18, fontweight='bold', 
             color=COLORS['primary'], ha='left', va='top')
    
    # Title
    fig.text(0.95, 0.95, title, fontsize=24, fontweight='bold', 
             color=COLORS['text'], ha='right', va='top')
    
    if subtitle:
        fig.text(0.95, 0.91, subtitle, fontsize=12, 
                 color=COLORS['text_muted'], ha='right', va='top')
        
    # Divider
    line = plt.Line2D([0.05, 0.95], [0.89, 0.89], color=COLORS['border'], 
                      linewidth=1, transform=fig.transFigure)
    fig.add_artist(line)

def _draw_footer(fig, page_num, total_pages=5):
    """Draws the consistent footer."""
    # Divider
    line = plt.Line2D([0.05, 0.95], [0.06, 0.06], color=COLORS['border'], 
                      linewidth=1, transform=fig.transFigure)
    fig.add_artist(line)
    
    # Text
    date_str = datetime.now().strftime('%d/%m/%Y')
    fig.text(0.05, 0.03, f"Relatório Semanal - {date_str}", fontsize=10, 
             color=COLORS['text_muted'], ha='left')
    
    fig.text(0.95, 0.03, f"Página {page_num}", fontsize=10, 
             color=COLORS['text_muted'], ha='right')

def _create_cover_page(pdf, df):
    fig = _setup_page()
    
    # 1. Background Elements (Abstract Art)
    # Circle 1
    circle1 = plt.Circle((0.1, 0.9), 0.3, color=COLORS['card'], alpha=0.3, transform=fig.transFigure)
    fig.add_artist(circle1)
    # Circle 2
    circle2 = plt.Circle((0.9, 0.1), 0.4, color=COLORS['primary'], alpha=0.05, transform=fig.transFigure)
    fig.add_artist(circle2)
    
    # 2. Main Title using a "Hero" layout
    fig.text(0.5, 0.65, "RELATÓRIO SEMANAL", fontsize=60, fontweight='bold', 
             color=COLORS['text'], ha='center', va='center')
    
    fig.text(0.5, 0.55, "ANÁLISE QUANTITATIVA DE AÇÕES", fontsize=24, 
             color=COLORS['primary'], ha='center', va='center')
    
    # 3. Date Badge
    date_str = datetime.now().strftime('%B %Y').upper()
    fig.text(0.5, 0.48, date_str, fontsize=14, color=COLORS['text_muted'], 
             ha='center', va='center', bbox=dict(facecolor=COLORS['card'], edgecolor=COLORS['primary'], pad=10, boxstyle='round,pad=0.5'))

    # 4. Key Stats Strip
    stats_y = 0.25
    
    # Metrics
    total_stocks = len(df)
    avg_score = df['super_score'].mean() if 'super_score' in df.columns else 0
    best_sector = df['setor'].mode()[0] if 'setor' in df.columns else "Diversos"
    
    metrics = [
        ("AÇÕES ANALISADAS", f"{total_stocks}"),
        ("SCORE MÉDIO", f"{avg_score:.1f}"),
        ("SETOR DESTAQUE", f"{best_sector[:15]}")
    ]
    
    # Draw centered cards
    start_x = 0.2
    gap = 0.25
    
    for i, (label, value) in enumerate(metrics):
        x = start_x + (i * gap)
        
        # Card settings
        rect = plt.Rectangle((x - 0.1, stats_y - 0.08), 0.2, 0.16, 
                           facecolor=COLORS['card'], edgecolor=COLORS['border'],
                           transform=fig.transFigure, zorder=2)
        fig.add_artist(rect)
        
        fig.text(x, stats_y + 0.03, value, fontsize=28, color=COLORS['primary'], 
                 ha='center', va='center', fontweight='bold', zorder=3)
        fig.text(x, stats_y - 0.03, label, fontsize=10, color=COLORS['text_muted'], 
                 ha='center', va='center', zorder=3)

    # Branding
    fig.text(0.5, 0.05, "NorteAções Intelligence", fontsize=12, 
             color=COLORS['text_muted'], ha='center')
    
    pdf.savefig(fig, facecolor=COLORS['bg'])
    plt.close(fig)

def _create_top_stocks_page(pdf, df):
    fig = _setup_page()
    _draw_header(fig, "RANKING DE OPORTUNIDADES", "Top 10 Ações por Super Score")
    
    # Main Table
    ax_table = fig.add_axes([0.05, 0.15, 0.9, 0.7])
    ax_table.axis('off')
    
    top10 = df.nlargest(10, 'super_score')
    
    # Columns
    columns = ['RANK', 'ATIVO', 'SETOR', 'PREÇO', 'P/L', 'DY', 'ROE', 'SUPER SCORE', 'ALERTA']
    
    data = []
    for i, row in enumerate(top10.itertuples(), 1):
        # Determine Alert Symbol
        flags = getattr(row, 'red_flags', [])
        alert = ""
        if 'LOW_LIQ' in flags: alert += " [!LIQ]"
        if 'DIV_TRAP' in flags: alert += " [!DIV]"
        if 'HIGH_DEBT' in flags: alert += " [!DIVIDA]"
        
        data.append([
            f"#{i}",
            row.papel,
            str(row.setor)[:20],
            f"R$ {row.cotacao:.2f}",
            f"{row.p_l:.1f}x",
            f"{row.dividend_yield * 100:.1f}%",  # Convert decimal to percentage
            f"{row.roe * 100:.1f}%",             # Convert decimal to percentage
            f"{row.super_score:.1f}",
            alert
        ])
    
    # Table Styling
    table = ax_table.table(cellText=data, colLabels=columns, loc='center', cellLoc='center')
    
    # Adjust layout
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1, 2.5) # More vertical space
    
    # Custom Cell Styling
    for (row, col), cell in table.get_celld().items():
        cell.set_edgecolor(COLORS['bg']) # Hide borders with BG color
        cell.set_linewidth(2)
        
        # Header
        if row == 0:
            cell.set_facecolor(COLORS['card'])
            cell.set_text_props(color=COLORS['primary'], weight='bold', fontsize=12)
            cell.set_height(0.08)
        else:
            # Body
            cell.set_height(0.06)
            is_odd = row % 2 != 0
            cell.set_facecolor(COLORS['card'] if is_odd else COLORS['bg'])
            cell.set_text_props(color=COLORS['text'])
            
            # Highlight Score (Last Column - 1)
            if col == 7:
                cell.set_text_props(color=COLORS['primary'], weight='bold', fontsize=12)
                
            # Highlight Alert (Last Column)
            if col == 8:
                cell.set_text_props(color=COLORS['danger'], weight='bold', fontsize=9)
            
            # Highlight Ticker (Col 1)
            if col == 1:
                cell.set_text_props(weight='bold')

    # Legend/Notes
    fig.text(0.05, 0.12, "* Critérios: Graham, Bazin, Greenblatt e Liquidez", 
             fontsize=10, color=COLORS['text_muted'], ha='left')

    _draw_footer(fig, 2)
    pdf.savefig(fig, facecolor=COLORS['bg'])
    plt.close(fig)

def _create_market_analysis_page(pdf, df):
    fig = _setup_page()
    _draw_header(fig, "PANORAMA DE MERCADO", "Análise Setorial e Distribuição")
    
    gs = fig.add_gridspec(2, 2, left=0.1, right=0.9, top=0.85, bottom=0.15, wspace=0.3, hspace=0.4)
    
    # 1. Sector Distribution (Pie)
    ax1 = fig.add_subplot(gs[0, 0])
    if 'setor' in df.columns:
        counts = df['setor'].value_counts().head(6)
        wedges, texts, autotexts = ax1.pie(counts, labels=counts.index, 
               autopct='%1.0f%%', colors=SECTOR_COLORS, startangle=90, pctdistance=0.85)
        
        # Donut style
        centre_circle = plt.Circle((0,0),0.70,fc=COLORS['bg'])
        ax1.add_artist(centre_circle)
        
        # Style text
        plt.setp(texts, size=9, color=COLORS['text'])
        plt.setp(autotexts, size=9, color=COLORS['bg'], weight='bold')
        
    ax1.set_title('Distribuição por Setor', color=COLORS['primary'], pad=20)
    
    # 2. Cheapest Sectors (Bar)
    ax2 = fig.add_subplot(gs[0, 1])
    if 'p_l' in df.columns and 'setor' in df.columns:
        sec_pl = df[df['p_l'] > 0].groupby('setor')['p_l'].median().sort_values().head(6)
        
        y_pos = np.arange(len(sec_pl))
        ax2.barh(y_pos, sec_pl.values, color=COLORS['secondary'], alpha=0.8)
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(sec_pl.index, color=COLORS['text'])
        
        # Remove spines
        for s in ['top', 'right', 'bottom']: ax2.spines[s].set_visible(False)
        ax2.spines['left'].set_color(COLORS['border'])
        ax2.tick_params(axis='x', colors=COLORS['text_muted'])
        
    ax2.set_title('Setores Mais Descontados (P/L Mediano)', color=COLORS['primary'], pad=20)
    
    # 3. Score Distribution (Hist)
    ax3 = fig.add_subplot(gs[1, :]) # Full width bottom
    ax3.set_facecolor(COLORS['bg'])
    
    scores = df['super_score'].dropna()
    n, bins, patches = ax3.hist(scores, bins=30, color=COLORS['card'], edgecolor=COLORS['border'])
    
    # Colorize bars based on score
    for patch, bin_start in zip(patches, bins):
        if bin_start >= 80: patch.set_facecolor(COLORS['success'])
        elif bin_start >= 60: patch.set_facecolor(COLORS['warning'])
        else: patch.set_facecolor(COLORS['card'])
        
    ax3.set_title('Distribuição de Quality Score do Mercado', color=COLORS['primary'], pad=20)
    ax3.set_ylabel('Quantidade de Ações', color=COLORS['text_muted'])
    ax3.set_xlabel('Super Score (0-100)', color=COLORS['text_muted'])
    
    # Remove spines
    for s in ['top', 'right']: ax3.spines[s].set_visible(False)
    ax3.spines['bottom'].set_color(COLORS['border'])
    ax3.spines['left'].set_color(COLORS['border'])
    ax3.tick_params(colors=COLORS['text_muted'])

    _draw_footer(fig, 3)
    pdf.savefig(fig, facecolor=COLORS['bg'])
    plt.close(fig)

def _create_one_pager(pdf, row):
    fig = _setup_page()
    
    # Custom Header for Stock
    fig.text(0.05, 0.95, f"{row.papel}", fontsize=32, fontweight='bold', 
             color=COLORS['primary'], ha='left', va='top')
    fig.text(0.05, 0.90, f"{row.setor}", fontsize=14, 
             color=COLORS['text_muted'], ha='left', va='top')
    
    # Score Badge
    fig.text(0.95, 0.95, f"{row.super_score:.1f}", fontsize=42, fontweight='bold', 
             color=COLORS['success'], ha='right', va='top')
    fig.text(0.95, 0.89, "SUPER SCORE", fontsize=10, 
             color=COLORS['text_muted'], ha='right', va='top')
             
    # Divider
    line = plt.Line2D([0.05, 0.95], [0.85, 0.85], color=COLORS['border'], 
                      linewidth=1, transform=fig.transFigure)
    fig.add_artist(line)

    # 1. Metrics Grid
    metrics = [
        ("Cotação", f"R$ {row.cotacao:.2f}"),
        ("P/L", f"{row.p_l:.1f}x"),
        ("P/VP", f"{getattr(row, 'p_vp', 0):.1f}x"),
        ("Div. Yield", f"{row.dividend_yield * 100:.1f}%"),  # Convert decimal to percentage
        ("ROE", f"{row.roe * 100:.1f}%"),                    # Convert decimal to percentage
        ("Liq. 2M", f"R$ {row.liquidez_2meses/1e6:.0f}M")
    ]
    
    start_y = 0.75
    start_x = 0.1
    gap_x = 0.28
    gap_y = 0.15
    
    for i, (label, val) in enumerate(metrics):
        row_idx = i // 3
        col_idx = i % 3
        
        x = start_x + (col_idx * gap_x)
        y = start_y - (row_idx * gap_y)
        
        # Card Background
        rect = plt.Rectangle((x - 0.02, y - 0.08), 0.22, 0.10, 
                           facecolor=COLORS['card'], edgecolor=COLORS['border'],
                           transform=fig.transFigure, alpha=0.8)
        fig.add_artist(rect)
        
        fig.text(x, y, label, fontsize=12, color=COLORS['text_muted'])
        fig.text(x, y - 0.05, val, fontsize=20, color=COLORS['text'], fontweight='bold')

    # 2. Radar Chart (Qualidade)
    try:
        ax_radar = fig.add_axes([0.1, 0.15, 0.35, 0.35], polar=True)
        categories = ['Valor', 'Qualidade', 'Div.', 'Cresc.', 'Liq.']
        N = len(categories)
        
        # Mock normalized scores for visualization (would need real normalization logic)
        values = [80, 70, 60, 50, 90] # Placeholder logic for visual 
        values += values[:1]
        
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        
        ax_radar.set_facecolor(COLORS['card'])
        ax_radar.grid(color=COLORS['border'])
        ax_radar.spines['polar'].set_visible(False)
        ax_radar.set_yticklabels([])
        ax_radar.set_xticks(angles[:-1])
        ax_radar.set_xticklabels(categories, color=COLORS['text'], size=10)
        
        ax_radar.plot(angles, values, color=COLORS['primary'], linewidth=2)
        ax_radar.fill(angles, values, color=COLORS['primary'], alpha=0.3)
        
    except Exception as e:
        print(f"Radar Error: {e}")

    # 3. Strategy Checklist
    fig.text(0.55, 0.45, "Checklist de Estratégias", fontsize=16, 
             color=COLORS['primary'], fontweight='bold')
             
    strategies = [
        ("Graham (Valor)", getattr(row, 'score_graham', 0) > 0),
        ("Bazin (Dividendos)", getattr(row, 'score_bazin', 0) > 0),
        ("Greenblatt (Fórmula Mágica)", getattr(row, 'score_greenblatt', 0) > 0)
    ]
    
    y_check = 0.40
    for name, passed in strategies:
        symbol = "[OK]" if passed else "[  ]"
        color = COLORS['success'] if passed else COLORS['text_muted']
        
        fig.text(0.55, y_check, f"{symbol}  {name}", fontsize=14, color=color, weight='bold')
        y_check -= 0.05

    _draw_footer(fig, 4)
    pdf.savefig(fig, facecolor=COLORS['bg'])
    plt.close(fig)

def _create_glossary_page(pdf):
    fig = _setup_page()
    _draw_header(fig, "GLOSSÁRIO", "Conceitos Fundamentais")
    
    items = [
        ("Super Score", "Nota de 0 a 100 baseada na convergência de múltiplas estratégias."),
        ("P/L (Preço/Lucro)", "Quantos anos levaria para recuperar o capital via lucros."),
        ("ROE", "Retorno sobre o Patrimônio Líquido. Mede a eficiência da gestão."),
        ("Graham", "Estratégia focada em ativos descontados e seguros (Valor)."),
        ("Bazin", "Estratégia focada em empresas pagadoras de dividendos."),
        ("Greenblatt", "Ranking combinado de Preço baixo e Qualidade alta.")
    ]
    
    y = 0.8
    for term, desc in items:
        fig.text(0.1, y, term, fontsize=16, color=COLORS['primary'], fontweight='bold')
        fig.text(0.1, y - 0.04, desc, fontsize=12, color=COLORS['text'])
        y -= 0.12

    _draw_footer(fig, 5)
    pdf.savefig(fig, facecolor=COLORS['bg'])
    plt.close(fig)
