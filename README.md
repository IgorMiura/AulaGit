# ClickUp Excel Integration

Uma integração poderosa entre ClickUp e Excel para sincronizar projetos em andamento.

## 📋 Descrição

Este projeto permite sincronizar dados entre planilhas Excel e listas do ClickUp, especificamente focado na lista "Projetos em andamento". A integração suporta sincronização bidirecional, permitindo que mudanças feitas no Excel sejam refletidas no ClickUp e vice-versa.

## ✨ Funcionalidades

- 🔄 Sincronização bidirecional entre Excel e ClickUp
- 📊 Mapeamento flexível de campos entre planilha e tarefas
- 🔐 Autenticação segura com API do ClickUp
- 📝 Logs detalhados para auditoria e troubleshooting
- ⚙️ Interface de linha de comando fácil de usar
- 🛡️ Tratamento robusto de erros e conflitos
- 💾 Sistema de backup automático

## 🚀 Instalação Rápida

1. Clone o repositório:
```bash
git clone https://github.com/IgorMiura/AulaGit.git
cd AulaGit
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure suas credenciais:
```bash
cp config/config.yaml.example config/config.yaml
# Edite config/config.yaml com suas informações do ClickUp
```

4. Execute a sincronização:
```bash
python clickup_excel_sync.py sync
```

## 📖 Documentação

- [Guia de Configuração](docs/setup_guide.md)
- [Exemplos de Uso](docs/usage_examples.md)
- [Solução de Problemas](docs/troubleshooting.md)
- [Pesquisa da API ClickUp](docs/clickup_api_research.md)

## 🏗️ Estrutura do Projeto

```
├── src/                    # Código fonte principal
├── config/                 # Arquivos de configuração
├── docs/                   # Documentação
├── examples/               # Exemplos e templates
├── tests/                  # Testes automatizados
└── logs/                   # Arquivos de log
```

## 🤝 Contribuição

Este projeto foi desenvolvido para facilitar a integração entre ClickUp e Excel. Para sugestões ou melhorias, abra uma issue ou pull request.

## 📄 Licença

Este projeto é de código aberto e está disponível sob a licença MIT.
