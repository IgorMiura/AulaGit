#!/usr/bin/env python3
"""
Quick Start Script - ClickUp Excel Integration
Script de inicialização rápida para criar o arquivo Excel e testar a conexão
"""

import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.clickup_client import ClickUpClient
from src.excel_handler import ExcelHandler

def main():
    print("🚀 ClickUp Excel Integration - Quick Start")
    print("=" * 50)
    
    # Configurações (já pré-configuradas com suas credenciais)
    API_TOKEN = "pk_55168429_CASI15FLV91IH3FZI06S02Q2YJOLXKRV"
    LIST_ID = "901323402543"
    EXCEL_FILE = "examples/projetos_em_andamento.xlsx"
    
    try:
        # 1. Testar conexão com ClickUp
        print("\n🔗 Testando conexão com ClickUp...")
        client = ClickUpClient(API_TOKEN)
        
        if client.test_connection():
            print("✅ Conexão com ClickUp bem-sucedida!")
        else:
            print("❌ Falha na conexão com ClickUp")
            return
        
        # 2. Buscar informações da lista
        print(f"\n📋 Buscando informações da lista {LIST_ID}...")
        try:
            list_info = client.get_list(LIST_ID)
            print(f"✅ Lista encontrada: {list_info.get('name', 'Nome não disponível')}")
            
            # Buscar tarefas da lista
            tasks = client.get_tasks(LIST_ID)
            print(f"📊 Encontradas {len(tasks)} tarefas na lista")
            
        except Exception as e:
            print(f"⚠️ Erro ao buscar lista: {e}")
            print("💡 Verifique se o LIST_ID está correto")
        
        # 3. Criar arquivo Excel com estrutura correta
        print(f"\n📊 Criando arquivo Excel: {EXCEL_FILE}")
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(EXCEL_FILE), exist_ok=True)
        
        # Criar handler Excel
        excel_handler = ExcelHandler(EXCEL_FILE, "Projetos")
        
        # Carregar/criar workbook
        excel_handler.load_workbook()
        
        # Adicionar dados de exemplo se a planilha estiver vazia
        if excel_handler.get_total_rows() <= 1:  # Apenas cabeçalho
            print("📝 Adicionando dados de exemplo...")
            
            # Dados de exemplo
            example_data = [
                {
                    "nome": "Projeto Website Corporativo",
                    "descricao": "Desenvolvimento do novo website da empresa",
                    "status": "Em andamento",
                    "prioridade": "Alta",
                    "responsavel": "Rodrigo Prado",
                    "data_inicio": "2024-01-15",
                    "data_fim": "2024-03-15",
                    "progresso": 65,
                    "tags": "website,desenvolvimento,corporativo",
                    "clickup_id": ""
                },
                {
                    "nome": "Sistema de Gestão Interna",
                    "descricao": "Implementação de sistema para gestão de processos internos",
                    "status": "A fazer",
                    "prioridade": "Normal",
                    "responsavel": "Equipe TI",
                    "data_inicio": "2024-02-01",
                    "data_fim": "2024-05-01",
                    "progresso": 0,
                    "tags": "sistema,gestao,interno",
                    "clickup_id": ""
                },
                {
                    "nome": "Campanha Marketing Digital",
                    "descricao": "Campanha de marketing digital para Q1 2024",
                    "status": "Concluído",
                    "prioridade": "Baixa",
                    "responsavel": "Marketing",
                    "data_inicio": "2024-01-01",
                    "data_fim": "2024-01-31",
                    "progresso": 100,
                    "tags": "marketing,digital,campanha",
                    "clickup_id": ""
                }
            ]
            
            for data in example_data:
                excel_handler.add_row(data)
        
        # Salvar arquivo
        excel_handler.save()
        print(f"✅ Arquivo Excel criado com sucesso: {EXCEL_FILE}")
        
        # 4. Mostrar próximos passos
        print("\n🎉 Configuração concluída!")
        print("\n📋 Próximos passos:")
        print("1. Instalar dependências:")
        print("   pip install -r requirements.txt")
        print("\n2. Testar a configuração:")
        print("   python clickup_excel_sync.py test")
        print("\n3. Sincronizar dados:")
        print("   python clickup_excel_sync.py sync")
        print("\n4. Ver status:")
        print("   python clickup_excel_sync.py status")
        
        print(f"\n📁 Arquivos criados:")
        print(f"   - config/config.yaml (configuração)")
        print(f"   - {EXCEL_FILE} (planilha de exemplo)")
        
        print("\n💡 Dica: O arquivo Excel foi criado com dados de exemplo.")
        print("   Você pode editá-lo e depois sincronizar com o ClickUp!")
        
    except Exception as e:
        print(f"❌ Erro durante inicialização: {e}")
        print("\n🔧 Verifique:")
        print("1. Se o token da API está correto")
        print("2. Se você tem acesso à lista especificada")
        print("3. Se as dependências estão instaladas (pip install -r requirements.txt)")

if __name__ == "__main__":
    main()
