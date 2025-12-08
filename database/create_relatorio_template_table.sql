-- Tabela para armazenar templates de relatórios de viabilidade
-- Cada empresa pode ter um template diferente por ano

CREATE TABLE IF NOT EXISTS TbRelatorioTemplate (
    id INT AUTO_INCREMENT PRIMARY KEY,
    empresa_id INT NOT NULL,
    ano INT NOT NULL,
    template_texto TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (empresa_id) REFERENCES empresas(id) ON DELETE CASCADE,
    UNIQUE KEY unique_empresa_ano (empresa_id, ano)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Índice para melhorar performance de busca
CREATE INDEX idx_empresa_ano ON TbRelatorioTemplate(empresa_id, ano);
