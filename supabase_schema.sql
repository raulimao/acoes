-- ==============================================================
-- SUPABASE SCHEMA FOR TOPACOES
-- Execute este SQL no SQL Editor do Supabase
-- ==============================================================

-- Tabela de Setores (cache)
CREATE TABLE IF NOT EXISTS setores (
    id BIGSERIAL PRIMARY KEY,
    ativo TEXT UNIQUE NOT NULL,
    setor TEXT NOT NULL DEFAULT 'N/A',
    subsetor TEXT NOT NULL DEFAULT 'N/A',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabela de Histórico
CREATE TABLE IF NOT EXISTS historico (
    id BIGSERIAL PRIMARY KEY,
    data TIMESTAMPTZ DEFAULT NOW(),
    papel TEXT NOT NULL,
    cotacao DECIMAL(12,2),
    p_l DECIMAL(12,4),
    p_vp DECIMAL(12,4),
    dividend_yield DECIMAL(12,6),
    roe DECIMAL(12,6),
    roic DECIMAL(12,6),
    score_graham DECIMAL(8,2),
    score_greenblatt DECIMAL(8,2),
    score_bazin DECIMAL(8,2),
    score_qualidade DECIMAL(8,2),
    super_score DECIMAL(8,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_historico_papel ON historico(papel);
CREATE INDEX IF NOT EXISTS idx_historico_data ON historico(data DESC);
CREATE INDEX IF NOT EXISTS idx_historico_super_score ON historico(super_score DESC);
CREATE INDEX IF NOT EXISTS idx_setores_ativo ON setores(ativo);

-- Enable Row Level Security (RLS)
ALTER TABLE setores ENABLE ROW LEVEL SECURITY;
ALTER TABLE historico ENABLE ROW LEVEL SECURITY;

-- Políticas de acesso público (para anon key)
CREATE POLICY "Allow public read setores" ON setores FOR SELECT USING (true);
CREATE POLICY "Allow public insert setores" ON setores FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public update setores" ON setores FOR UPDATE USING (true);

CREATE POLICY "Allow public read historico" ON historico FOR SELECT USING (true);
CREATE POLICY "Allow public insert historico" ON historico FOR INSERT WITH CHECK (true);
CREATE POLICY "Allow public delete historico" ON historico FOR DELETE USING (true);

-- Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para setores
CREATE TRIGGER update_setores_updated_at
    BEFORE UPDATE ON setores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
