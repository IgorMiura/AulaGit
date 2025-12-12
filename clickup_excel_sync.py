#!/usr/bin/env python3
"""
ClickUp Excel Integration - Main CLI Application

Este é o ponto de entrada principal para a integração entre ClickUp e Excel.
Permite sincronizar dados entre planilhas Excel e listas do ClickUp.
"""

import os
import sys
import yaml
import click
import logging
from pathlib import Path
from typing import Dict, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.clickup_client import ClickUpClient, ClickUpAPIError
from src.excel_handler import ExcelHandler, ExcelHandlerError
from src.data_mapper import DataMapper
from src.conflict_resolver import ConflictResolver
from src.sync_engine import SyncEngine, SyncEngineError
from src.logger import setup_logger


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """
    Load configuration from YAML file
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        click.echo(f"❌ Arquivo de configuração não encontrado: {config_path}")
        click.echo("💡 Execute 'python clickup_excel_sync.py setup' para criar a configuração")
        sys.exit(1)
    except yaml.YAMLError as e:
        click.echo(f"❌ Erro ao ler configuração: {e}")
        sys.exit(1)


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration
    
    Args:
        config: Configuration dictionary
        
    Returns:
        True if valid
    """
    required_fields = [
        'clickup.api_token',
        'clickup.team_id',
        'clickup.list_id',
        'excel.file_path'
    ]
    
    for field in required_fields:
        keys = field.split('.')
        value = config
        try:
            for key in keys:
                value = value[key]
            if not value or value == f"YOUR_{key.upper()}_HERE":
                click.echo(f"❌ Campo obrigatório não configurado: {field}")
                return False
        except KeyError:
            click.echo(f"❌ Campo obrigatório ausente: {field}")
            return False
    
    return True


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    🔄 ClickUp Excel Integration
    
    Sincronize dados entre ClickUp e Excel de forma fácil e eficiente.
    """
    pass


@cli.command()
@click.option('--config', '-c', default='config/config.yaml', help='Caminho para arquivo de configuração')
def setup(config):
    """🛠️ Configurar a integração ClickUp Excel"""
    click.echo("🛠️ Configurando ClickUp Excel Integration...")
    
    # Create directories
    os.makedirs('config', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('examples', exist_ok=True)
    
    if os.path.exists(config):
        if not click.confirm(f"Arquivo de configuração já existe em {config}. Sobrescrever?"):
            return
    
    # Interactive setup
    click.echo("\n📝 Vamos configurar sua integração:")
    
    # ClickUp configuration
    click.echo("\n🔗 Configuração do ClickUp:")
    api_token = click.prompt("Token da API do ClickUp", hide_input=True)
    team_id = click.prompt("ID do Team/Workspace")
    list_id = click.prompt("ID da Lista 'Projetos em andamento'")
    
    # Excel configuration
    click.echo("\n📊 Configuração do Excel:")
    excel_path = click.prompt("Caminho para o arquivo Excel", default="examples/projetos_em_andamento.xlsx")
    worksheet_name = click.prompt("Nome da planilha", default="Projetos")
    
    # Sync configuration
    click.echo("\n⚙️ Configuração de Sincronização:")
    sync_direction = click.prompt(
        "Direção da sincronização",
        type=click.Choice(['excel_to_clickup', 'clickup_to_excel', 'bidirectional']),
        default='bidirectional'
    )
    
    # Create configuration
    config_data = {
        'clickup': {
            'api_token': api_token,
            'team_id': team_id,
            'list_id': list_id,
            'base_url': 'https://api.clickup.com/api/v2'
        },
        'excel': {
            'file_path': excel_path,
            'worksheet_name': worksheet_name,
            'data_start_row': 2
        },
        'sync': {
            'direction': sync_direction,
            'interval_minutes': 30,
            'create_backup': True
        },
        'logging': {
            'level': 'INFO',
            'file_path': 'logs/clickup_excel_sync.log'
        }
    }
    
    # Save configuration
    with open(config, 'w', encoding='utf-8') as f:
        yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
    
    click.echo(f"\n✅ Configuração salva em {config}")
    
    # Test connection
    if click.confirm("Testar conexão com ClickUp?"):
        try:
            client = ClickUpClient(api_token)
            if client.test_connection():
                click.echo("✅ Conexão com ClickUp bem-sucedida!")
            else:
                click.echo("❌ Falha na conexão com ClickUp")
        except Exception as e:
            click.echo(f"❌ Erro ao testar conexão: {e}")
    
    # Create example Excel file
    if click.confirm("Criar arquivo Excel de exemplo?"):
        try:
            excel_handler = ExcelHandler(excel_path, worksheet_name)
            excel_handler.load_workbook()
            excel_handler.save()
            click.echo(f"✅ Arquivo Excel de exemplo criado: {excel_path}")
        except Exception as e:
            click.echo(f"❌ Erro ao criar arquivo Excel: {e}")
    
    click.echo("\n🎉 Configuração concluída! Execute 'python clickup_excel_sync.py sync' para sincronizar.")


@cli.command()
@click.option('--config', '-c', default='config/config.yaml', help='Caminho para arquivo de configuração')
@click.option('--direction', '-d', type=click.Choice(['excel_to_clickup', 'clickup_to_excel', 'bidirectional']), 
              help='Direção da sincronização')
@click.option('--no-backup', is_flag=True, help='Não criar backup antes da sincronização')
@click.option('--dry-run', is_flag=True, help='Simular sincronização sem fazer alterações')
def sync(config, direction, no_backup, dry_run):
    """🔄 Sincronizar dados entre ClickUp e Excel"""
    
    # Load configuration
    config_data = load_config(config)
    if not validate_config(config_data):
        sys.exit(1)
    
    # Setup logging
    log_config = config_data.get('logging', {})
    logger = setup_logger(
        level=log_config.get('level', 'INFO'),
        log_file=log_config.get('file_path', 'logs/clickup_excel_sync.log')
    )
    
    # Override direction if specified
    sync_direction = direction or config_data['sync']['direction']
    create_backup = not no_backup and config_data['sync'].get('create_backup', True)
    
    if dry_run:
        click.echo("🧪 Modo de simulação ativado - nenhuma alteração será feita")
    
    click.echo(f"🔄 Iniciando sincronização: {sync_direction}")
    
    try:
        # Initialize components
        clickup_client = ClickUpClient(
            api_token=config_data['clickup']['api_token'],
            base_url=config_data['clickup'].get('base_url', 'https://api.clickup.com/api/v2')
        )
        
        excel_handler = ExcelHandler(
            file_path=config_data['excel']['file_path'],
            worksheet_name=config_data['excel'].get('worksheet_name', 'Projetos'),
            data_start_row=config_data['excel'].get('data_start_row', 2)
        )
        
        data_mapper = DataMapper()
        conflict_resolver = ConflictResolver(resolution_strategy="latest_wins")
        
        sync_engine = SyncEngine(
            clickup_client=clickup_client,
            excel_handler=excel_handler,
            data_mapper=data_mapper,
            conflict_resolver=conflict_resolver
        )
        
        # Test connections
        click.echo("🔍 Testando conexões...")
        if not clickup_client.test_connection():
            click.echo("❌ Falha na conexão com ClickUp")
            sys.exit(1)
        
        if not excel_handler.validate_structure():
            click.echo("❌ Estrutura do Excel inválida")
            sys.exit(1)
        
        click.echo("✅ Conexões validadas")
        
        if dry_run:
            # Show what would be synchronized
            status = sync_engine.get_sync_status(config_data['clickup']['list_id'])
            click.echo("\n📊 Status atual:")
            click.echo(f"  Excel: {status['excel']['total_rows']} linhas ({status['excel']['synced_rows']} sincronizadas)")
            click.echo(f"  ClickUp: {status['clickup']['total_tasks']} tarefas")
            return
        
        # Perform synchronization
        list_id = config_data['clickup']['list_id']
        
        if sync_direction == 'excel_to_clickup':
            results = sync_engine.sync_excel_to_clickup(list_id, create_backup)
        elif sync_direction == 'clickup_to_excel':
            results = sync_engine.sync_clickup_to_excel(list_id, create_backup)
        else:  # bidirectional
            results = sync_engine.bidirectional_sync(list_id, create_backup)
        
        # Display results
        click.echo("\n✅ Sincronização concluída!")
        
        if sync_direction == 'bidirectional':
            click.echo(f"📊 Excel → ClickUp: {results['excel_to_clickup']['processed']} processados, "
                      f"{results['excel_to_clickup']['created']} criados, "
                      f"{results['excel_to_clickup']['updated']} atualizados")
            click.echo(f"📊 ClickUp → Excel: {results['clickup_to_excel']['processed']} processados, "
                      f"{results['clickup_to_excel']['created']} criados, "
                      f"{results['clickup_to_excel']['updated']} atualizados")
            if results['conflicts_resolved'] > 0:
                click.echo(f"⚠️ Conflitos resolvidos: {results['conflicts_resolved']}")
        else:
            click.echo(f"📊 Processados: {results['processed']}")
            click.echo(f"📊 Criados: {results['created']}")
            click.echo(f"📊 Atualizados: {results['updated']}")
        
        if results.get('errors'):
            click.echo(f"❌ Erros: {len(results['errors'])}")
            for error in results['errors'][:5]:  # Show first 5 errors
                click.echo(f"  • {error}")
        
    except (ClickUpAPIError, ExcelHandlerError, SyncEngineError) as e:
        click.echo(f"❌ Erro durante sincronização: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception("Unexpected error during sync")
        click.echo(f"❌ Erro inesperado: {e}")
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', default='config/config.yaml', help='Caminho para arquivo de configuração')
def status(config):
    """📊 Mostrar status da sincronização"""
    
    config_data = load_config(config)
    if not validate_config(config_data):
        sys.exit(1)
    
    try:
        # Initialize components
        clickup_client = ClickUpClient(config_data['clickup']['api_token'])
        excel_handler = ExcelHandler(
            file_path=config_data['excel']['file_path'],
            worksheet_name=config_data['excel'].get('worksheet_name', 'Projetos')
        )
        data_mapper = DataMapper()
        conflict_resolver = ConflictResolver()
        
        sync_engine = SyncEngine(clickup_client, excel_handler, data_mapper, conflict_resolver)
        
        # Get status
        status_info = sync_engine.get_sync_status(config_data['clickup']['list_id'])
        
        click.echo("📊 Status da Sincronização")
        click.echo("=" * 50)
        
        click.echo(f"\n📄 Excel:")
        click.echo(f"  Arquivo: {status_info['excel'].get('last_modified', 'N/A')}")
        click.echo(f"  Total de linhas: {status_info['excel']['total_rows']}")
        click.echo(f"  Linhas sincronizadas: {status_info['excel']['synced_rows']}")
        click.echo(f"  Linhas não sincronizadas: {status_info['excel']['unsynced_rows']}")
        
        click.echo(f"\n🔗 ClickUp:")
        click.echo(f"  Lista ID: {status_info['clickup']['list_id']}")
        click.echo(f"  Total de tarefas: {status_info['clickup']['total_tasks']}")
        
        click.echo(f"\n📈 Estatísticas de Sincronização:")
        stats = status_info['sync_stats']
        click.echo(f"  Criados no ClickUp: {stats['created_in_clickup']}")
        click.echo(f"  Atualizados no ClickUp: {stats['updated_in_clickup']}")
        click.echo(f"  Criados no Excel: {stats['created_in_excel']}")
        click.echo(f"  Atualizados no Excel: {stats['updated_in_excel']}")
        click.echo(f"  Conflitos resolvidos: {stats['conflicts_resolved']}")
        click.echo(f"  Erros: {stats['errors']}")
        
    except Exception as e:
        click.echo(f"❌ Erro ao obter status: {e}")
        sys.exit(1)


@cli.command()
@click.option('--config', '-c', default='config/config.yaml', help='Caminho para arquivo de configuração')
def test(config):
    """🧪 Testar conexões e configuração"""
    
    config_data = load_config(config)
    
    click.echo("🧪 Testando configuração...")
    
    # Test configuration
    if not validate_config(config_data):
        click.echo("❌ Configuração inválida")
        return
    
    click.echo("✅ Configuração válida")
    
    # Test ClickUp connection
    try:
        clickup_client = ClickUpClient(config_data['clickup']['api_token'])
        if clickup_client.test_connection():
            click.echo("✅ Conexão com ClickUp bem-sucedida")
            
            # Test list access
            try:
                tasks = clickup_client.get_tasks(config_data['clickup']['list_id'])
                click.echo(f"✅ Lista acessível ({len(tasks)} tarefas encontradas)")
            except Exception as e:
                click.echo(f"❌ Erro ao acessar lista: {e}")
        else:
            click.echo("❌ Falha na conexão com ClickUp")
    except Exception as e:
        click.echo(f"❌ Erro na conexão com ClickUp: {e}")
    
    # Test Excel file
    try:
        excel_handler = ExcelHandler(
            file_path=config_data['excel']['file_path'],
            worksheet_name=config_data['excel'].get('worksheet_name', 'Projetos')
        )
        
        if os.path.exists(config_data['excel']['file_path']):
            excel_handler.load_workbook()
            if excel_handler.validate_structure():
                click.echo("✅ Arquivo Excel válido")
                stats = excel_handler.get_stats()
                click.echo(f"  📊 {stats['total_rows']} linhas encontradas")
            else:
                click.echo("❌ Estrutura do Excel inválida")
        else:
            click.echo("⚠️ Arquivo Excel não encontrado (será criado na primeira sincronização)")
    except Exception as e:
        click.echo(f"❌ Erro ao testar Excel: {e}")


if __name__ == '__main__':
    cli()
