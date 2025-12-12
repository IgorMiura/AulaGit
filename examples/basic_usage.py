#!/usr/bin/env python3
"""
Exemplo básico de uso da integração ClickUp Excel

Este script demonstra como usar a integração programaticamente,
sem usar a interface de linha de comando.
"""

import sys
import os
from datetime import datetime

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.clickup_client import ClickUpClient
from src.excel_handler import ExcelHandler
from src.data_mapper import DataMapper
from src.conflict_resolver import ConflictResolver
from src.sync_engine import SyncEngine


def main():
    """Exemplo básico de sincronização"""
    
    # Configuração (substitua pelos seus valores)
    CLICKUP_API_TOKEN = "seu_token_aqui"
    CLICKUP_LIST_ID = "sua_lista_id_aqui"
    EXCEL_FILE_PATH = "examples/projetos_exemplo.xlsx"
    
    print("🔄 Iniciando exemplo de sincronização ClickUp Excel...")
    
    try:
        # 1. Inicializar componentes
        print("📝 Inicializando componentes...")
        
        clickup_client = ClickUpClient(CLICKUP_API_TOKEN)
        excel_handler = ExcelHandler(EXCEL_FILE_PATH, "Projetos")
        data_mapper = DataMapper()
        conflict_resolver = ConflictResolver(resolution_strategy="latest_wins")
        
        sync_engine = SyncEngine(
            clickup_client=clickup_client,
            excel_handler=excel_handler,
            data_mapper=data_mapper,
            conflict_resolver=conflict_resolver
        )
        
        # 2. Testar conexões
        print("🔍 Testando conexões...")
        
        if not clickup_client.test_connection():
            print("❌ Falha na conexão com ClickUp")
            return
        
        print("✅ Conexão com ClickUp bem-sucedida")
        
        # 3. Criar dados de exemplo no Excel (se não existir)
        if not os.path.exists(EXCEL_FILE_PATH):
            print("📊 Criando arquivo Excel de exemplo...")
            create_example_excel_data(excel_handler)
        
        # 4. Obter status atual
        print("📊 Status atual:")
        status = sync_engine.get_sync_status(CLICKUP_LIST_ID)
        print(f"  Excel: {status['excel']['total_rows']} linhas")
        print(f"  ClickUp: {status['clickup']['total_tasks']} tarefas")
        
        # 5. Sincronizar Excel para ClickUp
        print("\n🔄 Sincronizando Excel → ClickUp...")
        results = sync_engine.sync_excel_to_clickup(CLICKUP_LIST_ID, create_backup=True)
        
        print(f"✅ Sincronização concluída:")
        print(f"  Processados: {results['processed']}")
        print(f"  Criados: {results['created']}")
        print(f"  Atualizados: {results['updated']}")
        
        if results['errors']:
            print(f"  Erros: {len(results['errors'])}")
            for error in results['errors'][:3]:
                print(f"    • {error}")
        
        # 6. Sincronizar ClickUp para Excel
        print("\n🔄 Sincronizando ClickUp → Excel...")
        results = sync_engine.sync_clickup_to_excel(CLICKUP_LIST_ID, create_backup=False)
        
        print(f"✅ Sincronização concluída:")
        print(f"  Processados: {results['processed']}")
        print(f"  Criados: {results['created']}")
        print(f"  Atualizados: {results['updated']}")
        
        print("\n🎉 Exemplo concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante execução: {e}")
        import traceback
        traceback.print_exc()


def create_example_excel_data(excel_handler: ExcelHandler):
    """Criar dados de exemplo no Excel"""
    
    # Dados de exemplo
    example_data = [
        {
            'nome': 'Desenvolvimento do Sistema de Login',
            'descricao': 'Implementar sistema de autenticação com JWT',
            'status': 'Em andamento',
            'prioridade': 'Alta',
            'responsavel': 'João Silva',
            'data_inicio': '2024-01-15',
            'data_fim': '2024-01-30',
            'progresso': 75,
            'tags': 'backend, segurança',
            'clickup_id': ''
        },
        {
            'nome': 'Design da Interface do Dashboard',
            'descricao': 'Criar mockups e protótipos do dashboard principal',
            'status': 'A fazer',
            'prioridade': 'Normal',
            'responsavel': 'Maria Santos',
            'data_inicio': '2024-01-20',
            'data_fim': '2024-02-05',
            'progresso': 0,
            'tags': 'frontend, design',
            'clickup_id': ''
        },
        {
            'nome': 'Integração com API de Pagamentos',
            'descricao': 'Integrar sistema com gateway de pagamento',
            'status': 'Em revisão',
            'prioridade': 'Urgente',
            'responsavel': 'Pedro Costa',
            'data_inicio': '2024-01-10',
            'data_fim': '2024-01-25',
            'progresso': 90,
            'tags': 'backend, pagamentos',
            'clickup_id': ''
        }
    ]
    
    # Criar arquivo Excel com dados de exemplo
    excel_handler.load_workbook()
    excel_handler.write_data(example_data, clear_existing=True)
    excel_handler.save()
    
    print(f"✅ Arquivo Excel criado com {len(example_data)} projetos de exemplo")


if __name__ == '__main__':
    main()
