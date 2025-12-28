"""
Premium Report Service - Norte Acoes
Professional-grade PDF reports for SaaS subscribers
Version 3.0 - Fixed layout with strict position control
"""

import io
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime
import pandas as pd
import numpy as np
import tempfile
import os

# ============================================
# CONSTANTS
# ============================================

MIN_LIQUIDITY = 1_000_000  # R$ 1 million minimum liquidity
PAGE_WIDTH = 210
PAGE_HEIGHT = 297
MARGIN = 15
CONTENT_WIDTH = PAGE_WIDTH - (2 * MARGIN)

# ============================================
# PREMIUM COLOR PALETTE
# ============================================

COLORS = {
    'primary': (30, 41, 59),
    'primary_light': (51, 65, 85),
    'secondary': (16, 185, 129),
    'accent': (245, 158, 11),
    'success': (34, 197, 94),
    'warning': (234, 179, 8),
    'danger': (239, 68, 68),
    'text': (31, 41, 55),
    'text_muted': (107, 114, 128),
    'white': (255, 255, 255),
    'card_bg': (241, 245, 249),
    'table_alt': (248, 250, 252),
    'dividend_green': (5, 150, 105),
    'value_blue': (59, 130, 246),
    'quality_purple': (139, 92, 246)
}

# ============================================
# DATA PREPROCESSING
# ============================================

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter liquidity, remove duplicates, and clean outlier data.
    Removes stocks with unrealistic values that indicate data errors.
    """
    df = df.copy()
    
    # 1. Filter minimum liquidity (R$ 1 million)
    if 'liquidez_2meses' in df.columns:
        df = df[df['liquidez_2meses'] >= MIN_LIQUIDITY]
    
    # 2. SANITY FILTERS - Remove data with unrealistic values (data errors)
    # These values are impossible in real markets and indicate parsing errors
    
    # Filter ROE: realistic range is -100% to +100% (values above 100% are extremely rare)
    if 'roe' in df.columns:
        df = df[(df['roe'] > -100) & (df['roe'] < 100)]
    
    # Filter ROIC: realistic range is -50% to +50%
    if 'roic' in df.columns:
        df = df[(df['roic'] > -50) & (df['roic'] < 80)]
    
    # Filter Margem Liquida: realistic range is -100% to +100%
    if 'margem_liquida' in df.columns:
        df = df[(df['margem_liquida'] > -100) & (df['margem_liquida'] < 100)]
    
    # Filter P/L: must be positive and reasonable (0 < P/L < 200)
    # Negative P/L means losses, but we keep this filter for quality picks
    if 'p_l' in df.columns:
        # Keep stocks with positive P/L or mark negative as needing attention
        pass  # We'll filter per-section instead
    
    # 3. Remove duplicates - keep most liquid version (ON vs PN)
    if 'papel' in df.columns and 'liquidez_2meses' in df.columns:
        df['base_ticker'] = df['papel'].str[:-1]
        df = df.sort_values('liquidez_2meses', ascending=False)
        df = df.drop_duplicates(subset='base_ticker', keep='first')
        df = df.drop(columns=['base_ticker'])
        df = df.sort_values('super_score', ascending=False)
    
    return df.reset_index(drop=True)

# ============================================
# HELPER FUNCTIONS
# ============================================

def safe_str(text):
    """Clean string for Latin-1 encoding."""
    if not isinstance(text, str):
        text = str(text)
    
    replacements = {
        'ã': 'a', 'á': 'a', 'à': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e', 'è': 'e',
        'í': 'i', 'ì': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o', 'ò': 'o',
        'ú': 'u', 'ù': 'u',
        'ç': 'c',
        'Ã': 'A', 'Á': 'A', 'À': 'A', 'Â': 'A',
        'É': 'E', 'Ê': 'E', 'È': 'E',
        'Í': 'I', 'Ì': 'I',
        'Ó': 'O', 'Ô': 'O', 'Õ': 'O', 'Ò': 'O',
        'Ú': 'U', 'Ù': 'U',
        'Ç': 'C',
        '°': 'o', 'º': 'o', 'ª': 'a',
        '–': '-', '—': '-',
        '"': '"', '"': '"',
        ''': "'", ''': "'"
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    return text.encode('latin-1', 'ignore').decode('latin-1')

def format_currency(value):
    if pd.isna(value) or value is None:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_pct(value):
    if pd.isna(value) or value is None:
        return "0,0%"
    return f"{value:,.1f}%".replace(".", ",")

def format_large_number(value):
    if pd.isna(value) or value is None:
        return "-"
    if value >= 1_000_000_000:
        return f"R$ {value/1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"R$ {value/1_000_000:.1f}M"
    return f"R$ {value/1_000:.0f}K"

# ============================================
# PREMIUM PDF CLASS
# ============================================

class PremiumReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=False)  # Manual control
        self.report_date = datetime.now().strftime("%d/%m/%Y")
        self.header_height = 25
        self.footer_height = 15
        self.content_start = 32
        self.content_end = PAGE_HEIGHT - 20
        
    def header(self):
        self.set_fill_color(*COLORS['primary'])
        self.rect(0, 0, PAGE_WIDTH, self.header_height, 'F')
        
        self.set_fill_color(*COLORS['secondary'])
        self.rect(0, self.header_height, PAGE_WIDTH, 2, 'F')
        
        self.set_text_color(*COLORS['white'])
        self.set_font('Helvetica', 'B', 20)
        self.set_xy(MARGIN, 5)
        self.cell(0, 8, 'NORTE ACOES', 0, 0, 'L')
        
        self.set_font('Helvetica', '', 9)
        self.set_xy(MARGIN, 14)
        self.cell(0, 5, 'Relatorio Semanal Premium', 0, 0, 'L')
        
        self.set_fill_color(*COLORS['primary_light'])
        self.set_xy(155, 6)
        self.set_font('Helvetica', 'B', 9)
        self.cell(40, 12, self.report_date, 0, 0, 'C', 1)

    def footer(self):
        self.set_y(-self.footer_height)
        self.set_draw_color(*COLORS['secondary'])
        self.set_line_width(0.5)
        self.line(MARGIN, self.get_y(), PAGE_WIDTH - MARGIN, self.get_y())
        
        self.ln(2)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(*COLORS['text_muted'])
        self.cell(50, 4, f'Pagina {self.page_no()}', 0, 0, 'L')
        
        self.set_font('Helvetica', 'B', 7)
        self.set_text_color(*COLORS['secondary'])
        self.cell(80, 4, 'MEMBRO PREMIUM', 0, 0, 'C')
        
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(*COLORS['text_muted'])
        self.cell(50, 4, f'Gerado em {self.report_date}', 0, 0, 'R')

    def check_page_break(self, height_needed):
        """Check if we need a new page and add one if necessary."""
        if self.get_y() + height_needed > self.content_end:
            self.add_page()
            return True
        return False

    def section_title(self, number, title, color=None):
        """Create a section title."""
        if color is None:
            color = COLORS['primary']
        
        self.check_page_break(15)
        self.ln(5)
        
        self.set_fill_color(*color)
        self.set_text_color(*COLORS['white'])
        self.set_font('Helvetica', 'B', 9)
        
        self.set_x(MARGIN)
        self.cell(6, 6, str(number), 0, 0, 'C', 1)
        
        self.set_x(MARGIN + 8)
        self.set_text_color(*COLORS['text'])
        self.set_font('Helvetica', 'B', 11)
        self.cell(0, 6, safe_str(title), 0, 1, 'L')
        
        self.ln(2)

    def add_metric_card_small(self, x, y, label, value, color=None):
        """Create a small metric card."""
        if color is None:
            color = COLORS['primary']
        
        card_w = 42
        card_h = 20
        
        self.set_fill_color(*COLORS['card_bg'])
        self.set_draw_color(220, 220, 220)
        self.rect(x, y, card_w, card_h, 'DF')
        
        self.set_fill_color(*color)
        self.rect(x, y, card_w, 2, 'F')
        
        self.set_xy(x, y + 4)
        self.set_font('Helvetica', '', 6)
        self.set_text_color(*COLORS['text_muted'])
        self.cell(card_w, 3, safe_str(label), 0, 2, 'C')
        
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(*color)
        self.cell(card_w, 6, safe_str(value), 0, 0, 'C')

    def create_table(self, headers, data, col_widths, header_color=None, highlight_col=None, max_rows=10):
        """Create a table with strict height control."""
        if header_color is None:
            header_color = COLORS['primary']
        
        row_height = 5
        header_height = 6
        table_height = header_height + (min(len(data), max_rows) * row_height) + 2
        
        self.check_page_break(table_height)
        
        # Header
        self.set_fill_color(*header_color)
        self.set_text_color(*COLORS['white'])
        self.set_font('Helvetica', 'B', 7)
        
        self.set_x(MARGIN)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], header_height, safe_str(h), 0, 0, 'C', 1)
        self.ln()
        
        # Rows
        self.set_font('Helvetica', '', 6)
        fill = False
        
        for row_idx, row in enumerate(data[:max_rows]):
            if fill:
                self.set_fill_color(*COLORS['table_alt'])
            else:
                self.set_fill_color(*COLORS['white'])
            
            self.set_x(MARGIN)
            self.set_text_color(*COLORS['text'])
            
            for col_idx, (cell, width) in enumerate(zip(row, col_widths)):
                if highlight_col is not None and col_idx == highlight_col:
                    self.set_text_color(*COLORS['secondary'])
                    self.set_font('Helvetica', 'B', 6)
                else:
                    self.set_text_color(*COLORS['text'])
                    self.set_font('Helvetica', '', 6)
                
                self.cell(width, row_height, safe_str(str(cell)[:16]), 0, 0, 'C', 1)
            
            self.ln()
            fill = not fill


# ============================================
# CHART GENERATORS
# ============================================

def create_sector_chart(df):
    """Sector donut chart."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    
    sector_counts = df['setor'].value_counts().head(5)
    colors = ['#1e293b', '#334155', '#475569', '#64748b', '#94a3b8']
    
    wedges, texts, autotexts = ax.pie(
        sector_counts, labels=None, autopct='%1.0f%%', 
        colors=colors[:len(sector_counts)], startangle=90, pctdistance=0.75,
        wedgeprops=dict(width=0.5, edgecolor='white', linewidth=1.5)
    )
    
    for at in autotexts:
        at.set_color('white')
        at.set_fontsize(7)
        at.set_fontweight('bold')
    
    ax.set_title('Distribuicao por Setor', fontsize=9, fontweight='bold', pad=5)
    ax.legend([s[:10] for s in sector_counts.index], loc='center left', 
              bbox_to_anchor=(1, 0.5), fontsize=6, frameon=False)
    
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=90, bbox_inches='tight', facecolor='white')
    plt.close()
    return buf

def create_pl_chart(df):
    """P/L bar chart - ascending order (cheapest first)."""
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    
    clean_df = df[(df['p_l'] > 0) & (df['p_l'] < 50)]
    sector_pl = clean_df.groupby('setor')['p_l'].mean().sort_values(ascending=True).head(5)
    
    colors = plt.cm.RdYlGn_r(np.linspace(0.2, 0.8, len(sector_pl)))
    bars = ax.barh(range(len(sector_pl)), sector_pl.values, color=colors, height=0.5)
    
    ax.set_yticks(range(len(sector_pl)))
    ax.set_yticklabels([s[:10] for s in sector_pl.index], fontsize=6)
    ax.set_title('P/L por Setor (Baratos)', fontsize=9, fontweight='bold', pad=5)
    ax.set_xlabel('P/L', fontsize=7)
    
    for bar, val in zip(bars, sector_pl.values):
        ax.text(val + 0.1, bar.get_y() + bar.get_height()/2, f'{val:.1f}x', 
                va='center', fontsize=5)
    
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=90, bbox_inches='tight', facecolor='white')
    plt.close()
    return buf


# ============================================
# MAIN REPORT GENERATOR
# ============================================

def generate_pdf_report(df: pd.DataFrame) -> bytes:
    """Generate premium PDF report with strict layout control."""
    
    # Preprocess data
    df = preprocess_data(df)
    
    pdf = PremiumReport()
    
    # =============================================
    # PAGE 1
    # =============================================
    pdf.add_page()
    pdf.set_y(pdf.content_start)
    
    # SECTION 1: EXECUTIVE SUMMARY
    pdf.section_title(1, "Resumo Executivo do Mercado", COLORS['primary'])
    
    # Calculate ALL metrics
    total_tickers = len(df)
    media_pl = df[(df['p_l'] > 0) & (df['p_l'] < 100)]['p_l'].mean()
    media_dy = df['dividend_yield'].mean()
    media_roe = df[(df['roe'] > 0) & (df['roe'] < 100)]['roe'].mean() if 'roe' in df.columns else 0
    media_roic = df[(df['roic'] > 0) & (df['roic'] < 100)]['roic'].mean() if 'roic' in df.columns else 0
    media_pvp = df[(df['p_vp'] > 0) & (df['p_vp'] < 10)]['p_vp'].mean() if 'p_vp' in df.columns else 0
    media_margem = df[(df['margem_liquida'] > 0) & (df['margem_liquida'] < 100)]['margem_liquida'].mean() if 'margem_liquida' in df.columns else 0
    total_sectors = df['setor'].nunique() if 'setor' in df.columns else 0
    
    # Additional metrics
    acoes_baratas = len(df[(df['p_l'] > 0) & (df['p_l'] < 10)])
    acoes_dy_alto = len(df[df['dividend_yield'] > 6])
    acoes_roe_alto = len(df[df['roe'] > 15]) if 'roe' in df.columns else 0
    media_score = df['super_score'].mean()
    liquidez_total = df['liquidez_2meses'].sum() if 'liquidez_2meses' in df.columns else 0
    
    # Row 1: 4 cards
    y_cards = pdf.get_y()
    pdf.add_metric_card_small(MARGIN, y_cards, "Acoes Analisadas", str(total_tickers), COLORS['primary'])
    pdf.add_metric_card_small(MARGIN + 45, y_cards, "Media P/L", f"{media_pl:.1f}x", COLORS['primary'])
    pdf.add_metric_card_small(MARGIN + 90, y_cards, "Media P/VP", f"{media_pvp:.2f}x", COLORS['primary'])
    pdf.add_metric_card_small(MARGIN + 135, y_cards, "Setores", str(total_sectors), COLORS['accent'])
    
    # Row 2: 4 cards
    y_cards2 = y_cards + 23
    pdf.add_metric_card_small(MARGIN, y_cards2, "Media DY", f"{media_dy:.1f}%", COLORS['secondary'])
    pdf.add_metric_card_small(MARGIN + 45, y_cards2, "Media ROE", f"{media_roe:.1f}%", COLORS['value_blue'])
    pdf.add_metric_card_small(MARGIN + 90, y_cards2, "Media ROIC", f"{media_roic:.1f}%", COLORS['quality_purple'])
    pdf.add_metric_card_small(MARGIN + 135, y_cards2, "Media Margem", f"{media_margem:.1f}%", COLORS['success'])
    
    # Row 3: 4 cards (new valuable metrics)
    y_cards3 = y_cards2 + 23
    pdf.add_metric_card_small(MARGIN, y_cards3, "Acoes P/L<10", str(acoes_baratas), COLORS['value_blue'])
    pdf.add_metric_card_small(MARGIN + 45, y_cards3, "Acoes DY>6%", str(acoes_dy_alto), COLORS['dividend_green'])
    pdf.add_metric_card_small(MARGIN + 90, y_cards3, "Acoes ROE>15%", str(acoes_roe_alto), COLORS['quality_purple'])
    pdf.add_metric_card_small(MARGIN + 135, y_cards3, "Score Medio", f"{media_score:.1f}", COLORS['accent'])
    
    pdf.set_y(y_cards3 + 28)
    
    # SECTION 2: SECTOR ANALYSIS (Charts)
    pdf.section_title(2, "Analise Setorial", COLORS['primary'])
    
    # Generate charts
    sector_buf = create_sector_chart(df)
    pl_buf = create_pl_chart(df)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f1:
        f1.write(sector_buf.getvalue())
        sector_path = f1.name
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as f2:
        f2.write(pl_buf.getvalue())
        pl_path = f2.name
    
    chart_y = pdf.get_y()
    pdf.image(sector_path, x=MARGIN, y=chart_y, w=85)
    pdf.image(pl_path, x=MARGIN + 95, y=chart_y, w=85)
    pdf.set_y(chart_y + 48)  # Fixed height for charts
    
    try:
        os.remove(sector_path)
        os.remove(pl_path)
    except:
        pass
    
    # SECTION 3: TOP 10 SUPER SCORE
    pdf.section_title(3, "Top 10 Oportunidades (Super Score)", COLORS['primary'])
    
    top_10 = df.nlargest(10, 'super_score')
    headers = ["Ticker", "Setor", "Preco", "P/L", "P/VP", "DY", "ROE", "Score"]
    col_widths = [20, 38, 24, 18, 18, 18, 18, 18]
    
    data = []
    for _, row in top_10.iterrows():
        data.append([
            row['papel'],
            row['setor'][:14] if pd.notna(row.get('setor')) else '-',
            format_currency(row.get('cotacao', 0)),
            f"{row.get('p_l', 0):.1f}x" if row.get('p_l', 0) > 0 else "-",
            f"{row.get('p_vp', 0):.2f}" if row.get('p_vp', 0) > 0 else "-",
            format_pct(row.get('dividend_yield', 0)),
            f"{row.get('roe', 0):.1f}%" if row.get('roe', 0) > 0 else "-",
            f"{row['super_score']:.1f}"
        ])
    
    pdf.create_table(headers, data, col_widths, highlight_col=7)
    
    # =============================================
    # PAGE 2
    # =============================================
    pdf.add_page()
    pdf.set_y(pdf.content_start)
    
    # SECTION 4: DIVIDEND CHAMPIONS
    pdf.section_title(4, "Maiores Pagadoras de Dividendos", COLORS['dividend_green'])
    
    top_dy = df[(df['p_l'] > 0)].nlargest(10, 'dividend_yield')
    
    data_dy = []
    for _, row in top_dy.iterrows():
        data_dy.append([
            row['papel'],
            row['setor'][:14] if pd.notna(row.get('setor')) else '-',
            format_currency(row.get('cotacao', 0)),
            f"{row.get('p_l', 0):.1f}x" if row.get('p_l', 0) > 0 else "-",
            f"{row.get('p_vp', 0):.2f}" if row.get('p_vp', 0) > 0 else "-",
            format_pct(row.get('dividend_yield', 0)),
            f"{row.get('roe', 0):.1f}%" if row.get('roe', 0) > 0 else "-",
            f"{row['super_score']:.1f}"
        ])
    
    pdf.create_table(headers, data_dy, col_widths, header_color=COLORS['dividend_green'], highlight_col=5)
    
    pdf.ln(5)
    
    # SECTION 5: VALUE PICKS
    pdf.section_title(5, "Value Picks - Acoes Subvalorizadas", COLORS['value_blue'])
    
    value_df = df[(df['p_l'] > 0) & (df['p_l'] < 12) & 
                  (df['p_vp'] > 0) & (df['p_vp'] < 1.5) &
                  (df['super_score'] > 3)].copy()
    
    if len(value_df) > 0:
        value_df['value_rank'] = (12 - value_df['p_l']) + (1.5 - value_df['p_vp'])
        value_picks = value_df.nlargest(10, 'value_rank')
        
        data_value = []
        for _, row in value_picks.iterrows():
            data_value.append([
                row['papel'],
                row['setor'][:14] if pd.notna(row.get('setor')) else '-',
                format_currency(row.get('cotacao', 0)),
                f"{row['p_l']:.1f}x",
                f"{row['p_vp']:.2f}",
                format_pct(row.get('dividend_yield', 0)),
                f"{row.get('roe', 0):.1f}%" if row.get('roe', 0) > 0 else "-",
                f"{row['super_score']:.1f}"
            ])
        
        pdf.create_table(headers, data_value, col_widths, header_color=COLORS['value_blue'], highlight_col=3)
    else:
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_text_color(*COLORS['text_muted'])
        pdf.cell(0, 6, "Nenhuma acao atende aos criterios de valor.", 0, 1)
    
    pdf.ln(5)
    
    # SECTION 6: QUALITY PICKS
    pdf.section_title(6, "Quality Picks - Alta Qualidade", COLORS['quality_purple'])
    
    quality_df = df.copy()
    if 'roe' in quality_df.columns and 'roic' in quality_df.columns:
        quality_df = quality_df[
            (quality_df['roe'] > 15) & 
            (quality_df['roic'] > 10) &
            (quality_df['super_score'] > 3)
        ]
        
        if len(quality_df) > 0:
            quality_picks = quality_df.nlargest(10, 'roe')
            
            headers_q = ["Ticker", "Setor", "ROE", "ROIC", "Margem", "P/L", "DY", "Score"]
            
            data_quality = []
            for _, row in quality_picks.iterrows():
                data_quality.append([
                    row['papel'],
                    row['setor'][:14] if pd.notna(row.get('setor')) else '-',
                    f"{row['roe']:.1f}%",
                    f"{row.get('roic', 0):.1f}%",
                    f"{row.get('margem_liquida', 0):.1f}%" if row.get('margem_liquida', 0) > 0 else "-",
                    f"{row.get('p_l', 0):.1f}x" if row.get('p_l', 0) > 0 else "-",
                    format_pct(row.get('dividend_yield', 0)),
                    f"{row['super_score']:.1f}"
                ])
            
            pdf.create_table(headers_q, data_quality, col_widths, header_color=COLORS['quality_purple'], highlight_col=2)
        else:
            pdf.set_font('Helvetica', 'I', 8)
            pdf.set_text_color(*COLORS['text_muted'])
            pdf.cell(0, 6, "Nenhuma acao atende aos criterios de qualidade.", 0, 1)
    
    # =============================================
    # PAGE 3
    # =============================================
    pdf.add_page()
    pdf.set_y(pdf.content_start)
    
    # SECTION 7: GROWTH PICKS
    pdf.section_title(7, "Growth Picks - Crescimento", COLORS['accent'])
    
    growth_df = df.copy()
    if 'crescimento_receita_5a' in growth_df.columns:
        growth_df = growth_df[
            (growth_df['crescimento_receita_5a'] > 10) &
            (growth_df['roe'] > 10) &
            (growth_df['super_score'] > 3)
        ]
        
        if len(growth_df) > 0:
            growth_picks = growth_df.nlargest(10, 'crescimento_receita_5a')
            
            headers_g = ["Ticker", "Setor", "Cresc5a", "ROE", "ROIC", "P/L", "DY", "Score"]
            
            data_growth = []
            for _, row in growth_picks.iterrows():
                data_growth.append([
                    row['papel'],
                    row['setor'][:14] if pd.notna(row.get('setor')) else '-',
                    f"{row.get('crescimento_receita_5a', 0):.1f}%",
                    f"{row.get('roe', 0):.1f}%",
                    f"{row.get('roic', 0):.1f}%",
                    f"{row.get('p_l', 0):.1f}x" if row.get('p_l', 0) > 0 else "-",
                    format_pct(row.get('dividend_yield', 0)),
                    f"{row['super_score']:.1f}"
                ])
            
            pdf.create_table(headers_g, data_growth, col_widths, header_color=COLORS['accent'], highlight_col=2)
        else:
            pdf.set_font('Helvetica', 'I', 8)
            pdf.set_text_color(*COLORS['text_muted'])
            pdf.cell(0, 6, "Nenhuma acao atende aos criterios de crescimento.", 0, 1)
    
    pdf.ln(5)
    
    # SECTION 8: LOW DEBT PICKS
    pdf.section_title(8, "Low Debt - Baixo Endividamento", COLORS['success'])
    
    low_debt_df = df.copy()
    if 'div_bruta_patrimonio' in low_debt_df.columns:
        low_debt_df = low_debt_df[
            (low_debt_df['div_bruta_patrimonio'] >= 0) &
            (low_debt_df['div_bruta_patrimonio'] < 0.5) &
            (low_debt_df['super_score'] > 3)
        ]
        
        if len(low_debt_df) > 0:
            low_debt_picks = low_debt_df.nsmallest(10, 'div_bruta_patrimonio')
            
            headers_d = ["Ticker", "Setor", "Div/PL", "ROE", "ROIC", "P/L", "DY", "Score"]
            
            data_debt = []
            for _, row in low_debt_picks.iterrows():
                data_debt.append([
                    row['papel'],
                    row['setor'][:14] if pd.notna(row.get('setor')) else '-',
                    f"{row.get('div_bruta_patrimonio', 0):.2f}x",
                    f"{row.get('roe', 0):.1f}%",
                    f"{row.get('roic', 0):.1f}%",
                    f"{row.get('p_l', 0):.1f}x" if row.get('p_l', 0) > 0 else "-",
                    format_pct(row.get('dividend_yield', 0)),
                    f"{row['super_score']:.1f}"
                ])
            
            pdf.create_table(headers_d, data_debt, col_widths, header_color=COLORS['success'], highlight_col=2)
        else:
            pdf.set_font('Helvetica', 'I', 8)
            pdf.set_text_color(*COLORS['text_muted'])
            pdf.cell(0, 6, "Nenhuma acao atende aos criterios.", 0, 1)
    
    pdf.ln(5)
    
    # SECTION 9: STRATEGIC INSIGHTS
    pdf.section_title(9, "Insights Estrategicos", COLORS['primary'])
    
    try:
        best_sector = df.groupby('setor')['super_score'].mean().idxmax()
        cheapest_sector = df[(df['p_l'] > 0) & (df['p_l'] < 50)].groupby('setor')['p_l'].mean().idxmin()
        best_dy_sector = df.groupby('setor')['dividend_yield'].mean().idxmax()
        
        insights = [
            f"Foram analisadas {total_tickers} acoes de {total_sectors} setores diferentes.",
            f"Setor com maior score medio: {safe_str(best_sector)}.",
            f"Setor mais barato (P/L): {safe_str(cheapest_sector)}.",
            f"Setor com maior DY medio: {safe_str(best_dy_sector)}.",
            f"{acoes_baratas} acoes possuem P/L abaixo de 10x (potencial value).",
            f"{acoes_dy_alto} acoes pagam mais de 6% de dividendos ao ano.",
            f"{acoes_roe_alto} acoes possuem ROE acima de 15% (alta rentabilidade)."
        ]
    except:
        insights = ["Mantenha diversificacao e foco no longo prazo."]
    
    # Insights box
    pdf.set_fill_color(240, 253, 244)
    pdf.set_draw_color(*COLORS['secondary'])
    pdf.set_line_width(0.5)
    
    box_y = pdf.get_y()
    box_h = 8 + (len(insights) * 5)
    pdf.rect(MARGIN, box_y, CONTENT_WIDTH, box_h, 'DF')
    
    pdf.set_xy(MARGIN + 3, box_y + 2)
    pdf.set_font('Helvetica', 'B', 8)
    pdf.set_text_color(*COLORS['secondary'])
    pdf.cell(0, 4, "Analise da Semana", 0, 1)
    
    pdf.set_font('Helvetica', '', 7)
    pdf.set_text_color(*COLORS['text'])
    for insight in insights:
        pdf.set_x(MARGIN + 3)
        pdf.cell(0, 4, safe_str(f"- {insight}"), 0, 1)
    
    pdf.set_y(box_y + box_h + 8)
    
    # DISCLAIMER
    pdf.set_draw_color(*COLORS['text_muted'])
    pdf.set_line_width(0.3)
    pdf.line(MARGIN, pdf.get_y(), PAGE_WIDTH - MARGIN, pdf.get_y())
    pdf.ln(3)
    
    pdf.set_font('Helvetica', 'I', 6)
    pdf.set_text_color(*COLORS['text_muted'])
    disclaimer = (
        "DISCLAIMER: Relatorio exclusivo para membros premium Norte Acoes. "
        "Nao constitui recomendacao de compra ou venda. "
        "Consulte um profissional certificado antes de investir. "
        "Rentabilidade passada nao garante resultados futuros. "
        f"Criterio de liquidez: apenas acoes com volume > R$ {MIN_LIQUIDITY/1_000_000:.0f}M nos ultimos 2 meses."
    )
    pdf.multi_cell(CONTENT_WIDTH, 3, safe_str(disclaimer))
    
    return bytes(pdf.output())
