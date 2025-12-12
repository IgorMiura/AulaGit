# Guia de Configuração - ClickUp Excel Integration

Este guia irá ajudá-lo a configurar e usar a integração entre ClickUp e Excel.

## 📋 Pré-requisitos

- Python 3.8 ou superior
- Conta no ClickUp com acesso à API
- Microsoft Excel ou LibreOffice Calc

## 🚀 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/IgorMiura/AulaGit.git
cd AulaGit
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Execute a configuração inicial

```bash
python clickup_excel_sync.py setup
```

## 🔑 Obtendo Token da API do ClickUp

1. Acesse [ClickUp Settings](https://app.clickup.com/settings/apps)
2. Clique em "Generate" na seção "API Token"
3. Copie o token gerado (mantenha-o seguro!)

## 🆔 Encontrando IDs do ClickUp

### Team/Workspace ID

1. Acesse seu workspace no ClickUp
2. Observe a URL: `https://app.clickup.com/{TEAM_ID}/...`
3. O número após o primeiro `/` é seu Team ID

### List ID

1. Acesse a lista "Projetos em andamento" no ClickUp
2. Observe a URL: `https://app.clickup.com/{TEAM_ID}/v/li/{LIST_ID}`
3. O número após `/li/` é seu List ID

## ⚙️ Configuração Manual

Se preferir configurar manualmente, edite o arquivo `config/config.yaml`:

```yaml
clickup:
  api_token: "seu_token_aqui"
  team_id: "seu_team_id"
  list_id: "sua_lista_id"
  base_url: "https://api.clickup.com/api/v2"

excel:
  file_path: "examples/projetos_em_andamento.xlsx"
  worksheet_name: "Projetos"
  data_start_row: 2

sync:
  direction: "bidirectional"  # excel_to_clickup, clickup_to_excel, bidirectional
  interval_minutes: 30
  create_backup: true

logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  file_path: "logs/clickup_excel_sync.log"
```

## 📊 Estrutura do Excel

O arquivo Excel deve ter as seguintes colunas (na ordem):

| Coluna | Campo | Descrição |
|--------|-------|-----------|
| A | Nome do Projeto | Nome da tarefa no ClickUp |
| B | Descrição | Descrição detalhada |
| C | Status | Status atual (A fazer, Em andamento, etc.) |
| D | Prioridade | Prioridade (Baixa, Normal, Alta, Urgente) |
| E | Responsável | Nome do responsável |
| F | Data de Início | Data no formato YYYY-MM-DD |
| G | Data de Fim | Data no formato YYYY-MM-DD |
| H | Progresso (%) | Percentual de conclusão (0-100) |
| I | Tags | Tags separadas por vírgula |
| J | ClickUp ID | ID da tarefa no ClickUp (preenchido automaticamente) |

## 🧪 Testando a Configuração

```bash
python clickup_excel_sync.py test
```

Este comando irá:
- Validar a configuração
- Testar conexão com ClickUp
- Verificar estrutura do Excel
- Mostrar estatísticas básicas

## 🔄 Primeira Sincronização

### Sincronização Completa (Recomendado)

```bash
python clickup_excel_sync.py sync
```

### Sincronização Unidirecional

```bash
# Excel para ClickUp
python clickup_excel_sync.py sync --direction excel_to_clickup

# ClickUp para Excel
python clickup_excel_sync.py sync --direction clickup_to_excel
```

### Simulação (Dry Run)

```bash
python clickup_excel_sync.py sync --dry-run
```

## 📊 Monitoramento

### Ver Status Atual

```bash
python clickup_excel_sync.py status
```

### Logs

Os logs são salvos em `logs/clickup_excel_sync.log` e incluem:
- Operações de sincronização
- Erros e avisos
- Estatísticas de performance

## 🛠️ Solução de Problemas

### Erro de Autenticação

```
❌ Falha na conexão com ClickUp
```

**Solução:**
1. Verifique se o token da API está correto
2. Confirme se o token não expirou
3. Teste o token em: https://api.clickup.com/api/v2/team

### Erro de Lista Não Encontrada

```
❌ Erro ao acessar lista
```

**Solução:**
1. Verifique se o List ID está correto
2. Confirme se você tem acesso à lista
3. Verifique se a lista não foi arquivada

### Erro de Estrutura do Excel

```
❌ Estrutura do Excel inválida
```

**Solução:**
1. Verifique se as colunas estão na ordem correta
2. Confirme se a primeira linha contém os cabeçalhos
3. Execute `python clickup_excel_sync.py setup` para criar um arquivo de exemplo

### Conflitos de Sincronização

A integração resolve conflitos automaticamente usando a estratégia "latest_wins" (mais recente ganha). Para alterar:

```python
# Em src/sync_engine.py
conflict_resolver = ConflictResolver(resolution_strategy="excel_wins")
# Opções: "latest_wins", "excel_wins", "clickup_wins"
```

## 🔒 Segurança

- **Nunca** compartilhe seu token da API
- Use variáveis de ambiente para tokens em produção
- Mantenha backups regulares dos seus dados
- Monitore os logs para atividades suspeitas

## 📈 Otimização

### Performance

- Use sincronização incremental quando possível
- Configure intervalos apropriados para sincronização automática
- Monitore o uso da API para evitar rate limiting

### Backup

A integração cria backups automaticamente antes de cada sincronização:
- Localização: mesmo diretório do arquivo Excel
- Formato: `arquivo.xlsx.backup_YYYYMMDD_HHMMSS`
- Retenção: manual (remova backups antigos conforme necessário)

## 🆘 Suporte

Se encontrar problemas:

1. Verifique os logs em `logs/clickup_excel_sync.log`
2. Execute `python clickup_excel_sync.py test` para diagnóstico
3. Consulte a documentação da API do ClickUp
4. Abra uma issue no repositório do projeto
