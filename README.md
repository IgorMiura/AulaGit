# 📊 ClickUp Excel Integration

Este repositório contém código Power Query/M para integração entre ClickUp API e Excel/Power BI.

## 🚀 Funcionalidades

- **Busca paginada** de tarefas da API do ClickUp
- **Organização hierárquica** automática (tarefas pai → filhos → netos)
- **Tratamento de erros** robusto
- **Informações de debug** para monitoramento
- **Configuração flexível** via parâmetros

## 📁 Arquivos

- `clickup-excel-integration.m` - Código original
- `clickup-excel-integration-improved.m` - Versão melhorada com tratamento de erros
- `DEBUGGING_GUIDE.md` - Guia completo de depuração e solução de problemas

## 🔧 Como Usar

### Versão Básica
```m
// Cole o código do arquivo clickup-excel-integration.m no Power Query Editor
```

### Versão Melhorada (Recomendada)
```m
// Cole o código do arquivo clickup-excel-integration-improved.m
// Pode ser usado com parâmetros:

// Usar configurações padrão
MinhaFuncao()

// Ou com parâmetros personalizados
MinhaFuncao("seu_token_aqui", "sua_lista_id", 100)
```

## ⚙️ Configuração

1. **Token do ClickUp**: Obtenha em Settings → Apps → API
2. **List ID**: Encontre na URL da lista no ClickUp
3. **Max Pages**: Limite de páginas para evitar timeouts (padrão: 50)

## 📈 Resultado

A função retorna uma tabela Excel com:
- Todas as tarefas organizadas hierarquicamente
- Coluna `Task_Level` com níveis de indentação
- Coluna `Parent_Task_Name` com nome da tarefa pai
- Informações de debug (versão melhorada)

## 🐛 Solução de Problemas

Consulte o arquivo `DEBUGGING_GUIDE.md` para:
- Problemas comuns e soluções
- Melhorias sugeridas
- Testes recomendados
- Monitoramento e alertas

## 👨‍💻 Autor

Igor Miura - Integração ClickUp para Excel/Power BI
