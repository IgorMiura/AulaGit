"""
Synchronization Engine for ClickUp Excel Integration

This module handles the core synchronization logic between ClickUp and Excel,
managing bidirectional data flow and conflict resolution.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from tqdm import tqdm

from .clickup_client import ClickUpClient, ClickUpAPIError
from .excel_handler import ExcelHandler, ExcelHandlerError
from .data_mapper import DataMapper
from .conflict_resolver import ConflictResolver

logger = logging.getLogger(__name__)


class SyncEngineError(Exception):
    """Custom exception for sync engine errors"""
    pass


class SyncEngine:
    """
    Main synchronization engine for ClickUp Excel integration
    
    Features:
    - Bidirectional synchronization
    - Conflict detection and resolution
    - Progress tracking
    - Error handling and recovery
    - Incremental sync support
    """
    
    def __init__(self, clickup_client: ClickUpClient, excel_handler: ExcelHandler, 
                 data_mapper: DataMapper, conflict_resolver: ConflictResolver):
        """
        Initialize the sync engine
        
        Args:
            clickup_client: ClickUp API client
            excel_handler: Excel file handler
            data_mapper: Data mapping utility
            conflict_resolver: Conflict resolution utility
        """
        self.clickup = clickup_client
        self.excel = excel_handler
        self.mapper = data_mapper
        self.resolver = conflict_resolver
        
        self.sync_stats = {
            'created_in_clickup': 0,
            'updated_in_clickup': 0,
            'created_in_excel': 0,
            'updated_in_excel': 0,
            'conflicts_resolved': 0,
            'errors': 0
        }
    
    def sync_excel_to_clickup(self, list_id: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Sync data from Excel to ClickUp
        
        Args:
            list_id: ClickUp list ID to sync to
            create_backup: Whether to create backup before sync
            
        Returns:
            Dictionary containing sync results
        """
        logger.info("Starting Excel to ClickUp synchronization...")
        
        if create_backup:
            try:
                backup_path = self.excel.create_backup()
                logger.info(f"Backup created: {backup_path}")
            except ExcelHandlerError as e:
                logger.warning(f"Failed to create backup: {e}")
        
        try:
            # Read Excel data
            excel_data = self.excel.read_data()
            logger.info(f"Found {len(excel_data)} rows in Excel")
            
            # Get existing ClickUp tasks
            clickup_tasks = self.clickup.get_tasks(list_id)
            clickup_task_map = {task['id']: task for task in clickup_tasks}
            
            results = {
                'processed': 0,
                'created': 0,
                'updated': 0,
                'errors': [],
                'sync_stats': self.sync_stats
            }
            
            # Process each Excel row
            for row_data in tqdm(excel_data, desc="Syncing to ClickUp"):
                try:
                    self._sync_excel_row_to_clickup(row_data, list_id, clickup_task_map)
                    results['processed'] += 1
                except Exception as e:
                    error_msg = f"Error syncing row {row_data.get('excel_row', 'unknown')}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    self.sync_stats['errors'] += 1
            
            results['created'] = self.sync_stats['created_in_clickup']
            results['updated'] = self.sync_stats['updated_in_clickup']
            
            logger.info(f"Excel to ClickUp sync completed: {results['processed']} processed, "
                       f"{results['created']} created, {results['updated']} updated")
            
            return results
            
        except Exception as e:
            logger.error(f"Excel to ClickUp sync failed: {e}")
            raise SyncEngineError(f"Excel to ClickUp sync failed: {e}")
    
    def sync_clickup_to_excel(self, list_id: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Sync data from ClickUp to Excel
        
        Args:
            list_id: ClickUp list ID to sync from
            create_backup: Whether to create backup before sync
            
        Returns:
            Dictionary containing sync results
        """
        logger.info("Starting ClickUp to Excel synchronization...")
        
        if create_backup:
            try:
                backup_path = self.excel.create_backup()
                logger.info(f"Backup created: {backup_path}")
            except ExcelHandlerError as e:
                logger.warning(f"Failed to create backup: {e}")
        
        try:
            # Get ClickUp tasks
            clickup_tasks = self.clickup.get_tasks(list_id)
            logger.info(f"Found {len(clickup_tasks)} tasks in ClickUp")
            
            # Read existing Excel data
            excel_data = self.excel.read_data()
            excel_task_map = {}
            for row in excel_data:
                clickup_id = row.get('clickup_id')
                if clickup_id:
                    excel_task_map[clickup_id] = row
            
            results = {
                'processed': 0,
                'created': 0,
                'updated': 0,
                'errors': [],
                'sync_stats': self.sync_stats
            }
            
            # Process each ClickUp task
            for task in tqdm(clickup_tasks, desc="Syncing to Excel"):
                try:
                    self._sync_clickup_task_to_excel(task, excel_task_map)
                    results['processed'] += 1
                except Exception as e:
                    error_msg = f"Error syncing task {task.get('id', 'unknown')}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    self.sync_stats['errors'] += 1
            
            # Save Excel file
            self.excel.save()
            
            results['created'] = self.sync_stats['created_in_excel']
            results['updated'] = self.sync_stats['updated_in_excel']
            
            logger.info(f"ClickUp to Excel sync completed: {results['processed']} processed, "
                       f"{results['created']} created, {results['updated']} updated")
            
            return results
            
        except Exception as e:
            logger.error(f"ClickUp to Excel sync failed: {e}")
            raise SyncEngineError(f"ClickUp to Excel sync failed: {e}")
    
    def bidirectional_sync(self, list_id: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Perform bidirectional synchronization
        
        Args:
            list_id: ClickUp list ID
            create_backup: Whether to create backup before sync
            
        Returns:
            Dictionary containing sync results
        """
        logger.info("Starting bidirectional synchronization...")
        
        if create_backup:
            try:
                backup_path = self.excel.create_backup()
                logger.info(f"Backup created: {backup_path}")
            except ExcelHandlerError as e:
                logger.warning(f"Failed to create backup: {e}")
        
        try:
            # Get data from both sources
            excel_data = self.excel.read_data()
            clickup_tasks = self.clickup.get_tasks(list_id)
            
            logger.info(f"Found {len(excel_data)} rows in Excel, {len(clickup_tasks)} tasks in ClickUp")
            
            # Create mappings
            excel_task_map = {}
            clickup_task_map = {task['id']: task for task in clickup_tasks}
            
            for row in excel_data:
                clickup_id = row.get('clickup_id')
                if clickup_id:
                    excel_task_map[clickup_id] = row
            
            results = {
                'excel_to_clickup': {'processed': 0, 'created': 0, 'updated': 0},
                'clickup_to_excel': {'processed': 0, 'created': 0, 'updated': 0},
                'conflicts_resolved': 0,
                'errors': [],
                'sync_stats': self.sync_stats
            }
            
            # Process Excel rows (Excel -> ClickUp)
            for row_data in tqdm(excel_data, desc="Syncing Excel to ClickUp"):
                try:
                    action = self._sync_excel_row_to_clickup(row_data, list_id, clickup_task_map)
                    results['excel_to_clickup']['processed'] += 1
                    if action == 'created':
                        results['excel_to_clickup']['created'] += 1
                    elif action == 'updated':
                        results['excel_to_clickup']['updated'] += 1
                except Exception as e:
                    error_msg = f"Error syncing Excel row {row_data.get('excel_row', 'unknown')}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    self.sync_stats['errors'] += 1
            
            # Process ClickUp tasks (ClickUp -> Excel)
            for task in tqdm(clickup_tasks, desc="Syncing ClickUp to Excel"):
                try:
                    action = self._sync_clickup_task_to_excel(task, excel_task_map)
                    results['clickup_to_excel']['processed'] += 1
                    if action == 'created':
                        results['clickup_to_excel']['created'] += 1
                    elif action == 'updated':
                        results['clickup_to_excel']['updated'] += 1
                except Exception as e:
                    error_msg = f"Error syncing ClickUp task {task.get('id', 'unknown')}: {e}"
                    logger.error(error_msg)
                    results['errors'].append(error_msg)
                    self.sync_stats['errors'] += 1
            
            # Save Excel file
            self.excel.save()
            
            results['conflicts_resolved'] = self.sync_stats['conflicts_resolved']
            
            logger.info(f"Bidirectional sync completed: "
                       f"Excel->ClickUp: {results['excel_to_clickup']['processed']} processed, "
                       f"ClickUp->Excel: {results['clickup_to_excel']['processed']} processed")
            
            return results
            
        except Exception as e:
            logger.error(f"Bidirectional sync failed: {e}")
            raise SyncEngineError(f"Bidirectional sync failed: {e}")
    
    def _sync_excel_row_to_clickup(self, row_data: Dict[str, Any], list_id: str, 
                                   clickup_task_map: Dict[str, Any]) -> str:
        """
        Sync a single Excel row to ClickUp
        
        Args:
            row_data: Excel row data
            list_id: ClickUp list ID
            clickup_task_map: Map of existing ClickUp tasks
            
        Returns:
            Action taken ('created', 'updated', 'skipped')
        """
        clickup_id = row_data.get('clickup_id')
        
        if not clickup_id:
            # Create new task in ClickUp
            task_data = self.mapper.excel_to_clickup(row_data)
            if task_data.get('name'):  # Only create if has name
                created_task = self.clickup.create_task(list_id, task_data)
                
                # Update Excel with ClickUp ID
                excel_row = row_data.get('excel_row')
                if excel_row:
                    self.excel.update_row(excel_row, {'clickup_id': created_task['id']})
                
                self.sync_stats['created_in_clickup'] += 1
                return 'created'
        else:
            # Update existing task
            if clickup_id in clickup_task_map:
                existing_task = clickup_task_map[clickup_id]
                
                # Check for conflicts
                if self.resolver.has_conflict(row_data, existing_task):
                    resolved_data = self.resolver.resolve_conflict(row_data, existing_task)
                    self.sync_stats['conflicts_resolved'] += 1
                else:
                    resolved_data = row_data
                
                # Update task
                task_data = self.mapper.excel_to_clickup(resolved_data)
                if task_data:  # Only update if has data
                    self.clickup.update_task(clickup_id, task_data)
                    self.sync_stats['updated_in_clickup'] += 1
                    return 'updated'
        
        return 'skipped'
    
    def _sync_clickup_task_to_excel(self, task: Dict[str, Any], 
                                    excel_task_map: Dict[str, Any]) -> str:
        """
        Sync a single ClickUp task to Excel
        
        Args:
            task: ClickUp task data
            excel_task_map: Map of existing Excel rows
            
        Returns:
            Action taken ('created', 'updated', 'skipped')
        """
        task_id = task['id']
        
        if task_id not in excel_task_map:
            # Create new row in Excel
            excel_data = self.mapper.clickup_to_excel(task)
            if excel_data.get('nome'):  # Only create if has name
                self.excel.add_row(excel_data)
                self.sync_stats['created_in_excel'] += 1
                return 'created'
        else:
            # Update existing row
            existing_row = excel_task_map[task_id]
            
            # Check for conflicts
            if self.resolver.has_conflict(existing_row, task):
                resolved_data = self.resolver.resolve_conflict(existing_row, task)
                self.sync_stats['conflicts_resolved'] += 1
            else:
                resolved_data = self.mapper.clickup_to_excel(task)
            
            # Update row
            excel_row = existing_row.get('excel_row')
            if excel_row and resolved_data:
                self.excel.update_row(excel_row, resolved_data)
                self.sync_stats['updated_in_excel'] += 1
                return 'updated'
        
        return 'skipped'
    
    def get_sync_status(self, list_id: str) -> Dict[str, Any]:
        """
        Get current synchronization status
        
        Args:
            list_id: ClickUp list ID
            
        Returns:
            Dictionary containing sync status information
        """
        try:
            excel_stats = self.excel.get_stats()
            clickup_tasks = self.clickup.get_tasks(list_id)
            
            # Count synced items
            excel_data = self.excel.read_data()
            synced_count = sum(1 for row in excel_data if row.get('clickup_id'))
            
            status = {
                'excel': {
                    'total_rows': excel_stats['total_rows'],
                    'synced_rows': synced_count,
                    'unsynced_rows': excel_stats['total_rows'] - synced_count,
                    'last_modified': excel_stats['last_modified']
                },
                'clickup': {
                    'total_tasks': len(clickup_tasks),
                    'list_id': list_id
                },
                'sync_stats': self.sync_stats,
                'last_sync': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            raise SyncEngineError(f"Failed to get sync status: {e}")
    
    def reset_sync_stats(self) -> None:
        """Reset synchronization statistics"""
        self.sync_stats = {
            'created_in_clickup': 0,
            'updated_in_clickup': 0,
            'created_in_excel': 0,
            'updated_in_excel': 0,
            'conflicts_resolved': 0,
            'errors': 0
        }
        logger.info("Sync statistics reset")
