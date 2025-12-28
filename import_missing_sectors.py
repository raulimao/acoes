
import os
import sys
from dotenv import load_dotenv

# Setup path to import services
sys.path.append(os.getcwd())

from services.setores_service import save_setor_to_cache

def import_missing_sectors():
    load_dotenv()
    
    # List of manually resolved sectors
    # Source: Web Search & B3 Data
    manual_data = [
        {"ativo": "ADMF3", "setor": "Financeiro", "subsetor": "Serviços Financeiros Diversos"},
        {"ativo": "ARND3", "setor": "Tecnologia da Informação", "subsetor": "Programas e Serviços"},
        {"ativo": "AXIA3", "setor": "Utilidade Pública", "subsetor": "Energia Elétrica"},
        {"ativo": "AXIA6", "setor": "Utilidade Pública", "subsetor": "Energia Elétrica"},
        {"ativo": "EMBJ3", "setor": "Bens Industriais", "subsetor": "Material de Transporte"},
        {"ativo": "FICT3", "setor": "Consumo não Cíclico", "subsetor": "Alimentos Processados"},
        {"ativo": "FIGE3", "setor": "Financeiro", "subsetor": "Intermediários Financeiros"},
        {"ativo": "IFCM3", "setor": "Tecnologia da Informação", "subsetor": "Programas e Serviços"},
        {"ativo": "MBRF3", "setor": "Consumo não Cíclico", "subsetor": "Alimentos Processados"},
        {"ativo": "MERC3", "setor": "Financeiro", "subsetor": "Intermediários Financeiros"},
        {"ativo": "SOND3", "setor": "Bens Industriais", "subsetor": "Construção e Engenharia"},
        {"ativo": "WDCN3", "setor": "Tecnologia da Informação", "subsetor": "Programas e Serviços"}
    ]
    
    print(f"Iniciando importação de {len(manual_data)} setores...")
    
    success_count = 0
    for item in manual_data:
        ticker = item['ativo']
        setor = item['setor']
        subsetor = item['subsetor']
        
        if save_setor_to_cache(ticker, setor, subsetor):
            print(f"✅ {ticker}: {setor} / {subsetor}")
            success_count += 1
        else:
            print(f"❌ Erro ao salvar {ticker}")
            
    print("\n" + "="*40)
    print(f"Importação concluída: {success_count}/{len(manual_data)} sucessos.")
    print("="*40)

if __name__ == "__main__":
    import_missing_sectors()
