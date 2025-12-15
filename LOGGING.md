# Sistema de Logging - Ways Solution Hub

## 📋 Visão Geral

Este projeto utiliza um sistema de logging profissional e centralizado para rastreamento de eventos, erros e operações do sistema. O sistema foi implementado para substituir os `print()` statements e fornecer logs estruturados e organizados.

## 🎯 Características

- **Logging Centralizado**: Módulo único `utils/logger.py` gerencia todo o sistema de logs
- **Rotação Automática**: Arquivos de log rotacionam automaticamente ao atingir 10MB
- **Múltiplos Níveis**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Logs por Módulo**: Cada módulo tem seu próprio arquivo de log
- **Formatação Padronizada**: Timestamp, nível, módulo e mensagem
- **Retenção**: Mantém até 5 backups de cada arquivo de log

## 📁 Estrutura de Logs

Os logs são armazenados no diretório `logs/` na raiz do projeto:

```
logs/
├── app.log                 # Log principal da aplicação
├── database.log           # Logs de conexão e operações de banco
├── user_manager.log       # Logs de gerenciamento de usuários
├── company_manager.log    # Logs de gerenciamento de empresas
├── auth_public.log        # Logs de autenticação
├── user_pages.log         # Logs das páginas de usuário
├── admin_pages.log        # Logs das páginas administrativas
└── bpo_processing.log     # Logs de processamento de arquivos BPO
```

## 🚀 Como Usar

### Importando o Logger

Em qualquer módulo do projeto:

```python
from utils.logger import get_logger

# Criar logger específico para o módulo
logger = get_logger('nome_do_modulo')
```

### Níveis de Log

```python
# INFO - Informações gerais e operações bem-sucedidas
logger.info("Usuário criado com sucesso")

# WARNING - Avisos que não são erros críticos
logger.warning("Email inválido fornecido")

# ERROR - Erros que precisam atenção
logger.error(f"Erro ao conectar ao banco: {err}")

# DEBUG - Informações detalhadas para debugging
logger.debug(f"Dados processados: {data}")

# CRITICAL - Erros críticos do sistema
logger.critical("Falha crítica no sistema")
```

### Exemplo Completo

```python
from utils.logger import get_logger
import mysql.connector

logger = get_logger('meu_modulo')

def conectar_banco():
    try:
        logger.info("Iniciando conexão com banco de dados")
        conexao = mysql.connector.connect(...)
        logger.info("Conexão estabelecida com sucesso")
        return conexao
    except mysql.connector.Error as err:
        logger.error(f"Erro ao conectar: {err}")
        return None
```

## 📊 Formato dos Logs

Cada linha de log segue o formato:

```
YYYY-MM-DD HH:MM:SS - [NÍVEL] - módulo - mensagem
```

Exemplo:
```
2025-12-15 14:30:25 - [INFO] - user_manager - Usuário 'João Silva' criado com sucesso. ID: 42
2025-12-15 14:30:26 - [ERROR] - database - Erro ao conectar ao banco de dados: Connection refused
```

## 🔧 Configuração

### Alterar Nível de Log

Por padrão, o nível está configurado como `INFO`. Para alterar:

```python
logger = get_logger('nome_modulo', log_level=logging.DEBUG)
```

### Habilitar Console Output

Para ver logs no console (útil em desenvolvimento), edite `src/utils/logger.py` e descomente:

```python
# Handler para console (opcional - apenas em desenvolvimento)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)
console_handler.setFormatter(log_format)
logger.addHandler(console_handler)
```

### Rotação de Logs

Configuração atual:
- **Tamanho máximo por arquivo**: 10MB
- **Backups mantidos**: 5 arquivos
- **Encoding**: UTF-8

Para alterar, edite `src/utils/logger.py`:

```python
file_handler = RotatingFileHandler(
    log_file,
    maxBytes=20 * 1024 * 1024,  # 20MB
    backupCount=10,              # 10 backups
    encoding='utf-8'
)
```

## 📖 Módulos Logados

| Módulo | Logger | Descrição |
|--------|--------|-----------|
| `app.py` | `app` | Inicialização da aplicação Flask |
| `models/auth.py` | `database` | Conexões e operações de banco |
| `models/user_manager.py` | `user_manager` | Gerenciamento de usuários |
| `models/company_manager.py` | `company_manager` | Gerenciamento de empresas |
| `pages/public/index.py` | `auth_public` | Autenticação pública |
| `pages/user/user.py` | `user_pages` | Páginas de usuário |
| `pages/admin/admin.py` | `admin_pages` | Páginas administrativas |
| `controllers/data_processing/bpo_file_processing.py` | `bpo_processing` | Processamento BPO |

## 🛠️ Manutenção

### Limpeza de Logs

Os logs são rotacionados automaticamente, mas você pode limpar manualmente:

```bash
# Limpar todos os logs
rm -rf logs/

# Limpar logs antigos (mais de 30 dias)
find logs/ -name "*.log*" -mtime +30 -delete
```

### Monitoramento em Produção

Para monitorar logs em tempo real (King Host):

```bash
# Ver últimas linhas de um log específico
tail -f logs/app.log

# Ver erros em tempo real
tail -f logs/*.log | grep ERROR

# Contar erros do dia
grep "$(date +%Y-%m-%d)" logs/*.log | grep ERROR | wc -l
```

## ⚠️ Importante

- ❌ **NUNCA** faça commit da pasta `logs/` (já está no .gitignore)
- ✅ Sempre use o logger ao invés de `print()`
- ✅ Escolha o nível de log apropriado (INFO, WARNING, ERROR)
- ✅ Inclua contexto útil nas mensagens de log
- ✅ Não logue informações sensíveis (senhas, tokens, dados pessoais)

## 📞 Suporte

Para dúvidas ou problemas com o sistema de logging, consulte:
- Documentação oficial do Python logging: https://docs.python.org/3/library/logging.html
- Código fonte: `src/utils/logger.py`

---

**Última atualização**: 2025-12-15
**Versão**: 1.0
