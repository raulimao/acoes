
import io
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from fpdf import FPDF
from datetime import datetime
import pandas as pd
import tempfile
import os

# ============================================
# HELPER FUNCTIONS
# ============================================

def safe_str(text):
    """Clean string for Latin-1 encoding (Standard FPDF constraint)."""
    if not isinstance(text, str):
        text = str(text)
    
    replacements = {
        'ã': 'a', 'á': 'a', 'à': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u',
        'ç': 'c',
        'Ã': 'A', 'Á': 'A', 'À': 'A', 'Â': 'A',
        'É': 'E', 'Ê': 'E',
        'Í': 'I',
        'Ó': 'O', 'Ô': 'O', 'Õ': 'O',
        'Ú': 'U',
        'Ç': 'C',
        'R$': 'R$', 
        '°': 'o', 'º': 'o', 'ª': 'a',
        '–': '-', '—': '-'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    
    # Encode/Decode to strip remaining non-latin chars
    return text.encode('latin-1', 'ignore').decode('latin-1')

def format_currency(value):
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def format_pct(value):
    return f"{value:,.1f}%".replace(".", ",")

# ============================================
# PDF CLASS
# ============================================

class ProfessionalReport(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # Brand Color Line
        self.set_fill_color(40, 50, 80) # Dark Blue
        self.rect(0, 0, 210, 20, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font('Arial', 'B', 20)
        self.cell(0, 5, 'TOP ACOES', 0, 1, 'L')
        
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Relatorio Semanal de Mercado', 0, 1, 'L')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Pagina {self.page_no()} | Gerado em {datetime.now().strftime("%d/%m/%Y")} | Exclusivo Membros Premium', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_fill_color(240, 240, 245)
        self.set_text_color(40, 50, 80)
        self.cell(0, 10, safe_str(title), 0, 1, 'L', 1)
        self.ln(4)

    def add_metric_card(self, x, y, label, value, color=(40, 50, 80)):
        self.set_xy(x, y)
        self.set_fill_color(250, 250, 250)
        self.set_draw_color(220, 220, 220)
        self.rect(x, y, 60, 25, 'DF')
        
        self.set_xy(x, y+5)
        self.set_font('Arial', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(60, 5, safe_str(label), 0, 2, 'C')
        
        self.set_font('Arial', 'B', 14)
        self.set_text_color(*color)
        self.cell(60, 8, safe_str(value), 0, 0, 'C')

# ============================================
# CHART GENERATOR
# ============================================

def create_sector_chart(df):
    """Generates a sector distribution pie chart."""
    plt.figure(figsize=(6, 4))
    sector_counts = df['setor'].value_counts().head(7)
    
    colors = ['#2c3e50', '#34495e', '#7f8c8d', '#95a5a6', '#bdc3c7', '#ecf0f1', '#e0e0e0']
    
    plt.pie(sector_counts, labels=None, autopct='%1.0f%%', colors=colors, startangle=90, pctdistance=0.85)
    plt.title('Distribuicao por Setor (Top 7)', fontsize=12)
    
    # Draw circle for donut chart
    centre_circle = plt.Circle((0,0),0.70,fc='white')
    fig = plt.gcf()
    fig.gca().add_artist(centre_circle)
    plt.legend(sector_counts.index, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
    
    plt.tight_layout()
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100)
    plt.close()
    return img_buffer

def create_valuation_chart(df):
    """Generates a bar chart comparing sector avg P/L."""
    plt.figure(figsize=(6, 4))
    
    # Filter reasonable P/L for visual sanity
    clean_df = df[(df['p_l'] > 0) & (df['p_l'] < 50)]
    sector_pl = clean_df.groupby('setor')['p_l'].mean().sort_values().head(8)
    
    bars = plt.barh(sector_pl.index, sector_pl.values, color='#34495e')
    plt.title('Media P/L por Setor (Mais Baratos)', fontsize=12)
    plt.xlabel('P/L')
    plt.grid(axis='x', alpha=0.3)
    
    # Remove borders
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100)
    plt.close()
    return img_buffer

# ============================================
# MAIN GENERATOR
# ============================================

def generate_pdf_report(df: pd.DataFrame) -> bytes:
    pdf = ProfessionalReport()
    pdf.add_page()
    
    # 1. OVERVIEW SECTION
    pdf.chapter_title("1. Visao Geral do Mercado")
    
    media_pl = df[(df['p_l'] > 0) & (df['p_l'] < 100)]['p_l'].mean()
    media_dy = df['dividend_yield'].mean()
    total_tickers = len(df)
    
    # Cards
    pdf.add_metric_card(15, 45, "Acoes Analisadas", str(total_tickers))
    pdf.add_metric_card(80, 45, "Media P/L", f"{media_pl:.1f}x")
    pdf.add_metric_card(145, 45, "Media Yield (DY)", f"{media_dy:.1f}%", color=(0, 100, 0))
    
    pdf.ln(35)
    
    # CHARTS (Save to temp files because FPDF needs path or file object)
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 10, "Composicao Setorial e Valuation Relativo:", 0, 1)
    
    # Sectors Chart
    sector_img_buf = create_sector_chart(df)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_sector:
        tmp_sector.write(sector_img_buf.getvalue())
        tmp_sector_path = tmp_sector.name
        
    # Valuation Chart
    val_img_buf = create_valuation_chart(df)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_val:
        tmp_val.write(val_img_buf.getvalue())
        tmp_val_path = tmp_val.name
        
    # Place Images
    start_y = pdf.get_y()
    pdf.image(tmp_sector_path, x=10, y=start_y, w=90)
    pdf.image(tmp_val_path, x=105, y=start_y, w=90)
    pdf.ln(70)
    
    # Clean up temp files
    try:
        os.remove(tmp_sector_path)
        os.remove(tmp_val_path)
    except:
        pass

    # 2. TOP PICKS SECTION
    pdf.ln(10)
    pdf.chapter_title("2. Top 10 Oportunidades (Super Score)")
    
    pdf.set_font('Arial', '', 9)
    top_10 = df.nlargest(10, 'super_score')
    
    # Table Header
    pdf.set_fill_color(230, 230, 230)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 9)
    
    cols = [30, 50, 30, 30, 30]
    headers = ["Ticker", "Setor", "Preco", "Score", "DY"]
    
    for i, h in enumerate(headers):
        pdf.cell(cols[i], 8, safe_str(h), 0, 0, 'C', 1)
    pdf.ln()
    
    # Table Rows
    pdf.set_font('Arial', '', 9)
    fill = False
    for _, row in top_10.iterrows():
        # Zebra striping
        if fill:
            pdf.set_fill_color(245, 245, 245)
        else:
            pdf.set_fill_color(255, 255, 255)
            
        pdf.cell(cols[0], 8, safe_str(row['papel']), 0, 0, 'C', fill)
        pdf.cell(cols[1], 8, safe_str(row['setor'][:18]), 0, 0, 'C', fill)
        pdf.cell(cols[2], 8, format_currency(row['cotacao'] or 0), 0, 0, 'C', fill)
        pdf.cell(cols[3], 8, f"{row['super_score']:.1f}", 0, 0, 'C', fill)
        pdf.cell(cols[4], 8, format_pct(row['dividend_yield']), 0, 0, 'C', fill)
        
        pdf.ln()
        fill = not fill

    # 3. DIVIDENDS SECTION
    pdf.ln(10)
    pdf.chapter_title("3. Maiores Pagadoras de Dividendos")
    
    top_dy = df[(df['p_l'] > 0)].nlargest(10, 'dividend_yield') # Filter positive P/L to avoid value traps
    
    # Table Header (Same structure)
    pdf.set_fill_color(230, 240, 230) # Slight Green for Dividends
    pdf.set_font('Arial', 'B', 9)
    for i, h in enumerate(headers):
        pdf.cell(cols[i], 8, safe_str(h), 0, 0, 'C', 1)
    pdf.ln()
    
    pdf.set_font('Arial', '', 9)
    fill = False
    for _, row in top_dy.iterrows():
        if fill: pdf.set_fill_color(245, 250, 245)
        else: pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(cols[0], 8, safe_str(row['papel']), 0, 0, 'C', fill)
        pdf.cell(cols[1], 8, safe_str(row['setor'][:18]), 0, 0, 'C', fill)
        pdf.cell(cols[2], 8, format_currency(row['cotacao'] or 0), 0, 0, 'C', fill)
        pdf.cell(cols[3], 8, f"{row['super_score']:.1f}", 0, 0, 'C', fill)
        pdf.set_text_color(0, 100, 0) # Green text for DY
        pdf.cell(cols[4], 8, format_pct(row['dividend_yield']), 0, 0, 'C', fill)
        pdf.set_text_color(0, 0, 0)
        
        pdf.ln()
        fill = not fill

    # 4. CONCLUSION
    pdf.ln(15)
    pdf.set_x(10) # Reset X to margin to ensure full width available
    pdf.set_draw_color(200, 200, 200)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 6, safe_str("Nota do Analista IA:"), 0, 1) # Changed to cell for title
    pdf.set_font('Arial', '', 9)
    pdf.multi_cell(0, 5, safe_str("O mercado apresenta oportunidades em setores descontados. O Super Score continua priorizando empresas com balanco solido e lucratividade crescente. Mantenha diversificacao e foco no longo prazo."))

    return bytes(pdf.output())  # Ensure bytes return for FPDF2
