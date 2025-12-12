"""
Conflict Resolver for ClickUp Excel Integration

This module handles conflict detection and resolution when synchronizing
data between Excel and ClickUp.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ConflictResolver:
    """
    Handles conflict detection and resolution for data synchronization
    
    Features:
    - Conflict detection based on timestamps
    - Multiple resolution strategies
    - Configurable conflict rules
    - Detailed conflict logging
    """
    
    def __init__(self, resolution_strategy: str = "latest_wins"):
        """
        Initialize the conflict resolver
        
        Args:
            resolution_strategy: Strategy for resolving conflicts
                - "latest_wins": Use the most recently modified data
                - "excel_wins": Always prefer Excel data
                - "clickup_wins": Always prefer ClickUp data
                - "manual": Require manual resolution (not implemented)
        """
        self.resolution_strategy = resolution_strategy
        self.conflict_log = []
        
        # Fields that should be compared for conflicts
        self.conflict_fields = [
            'nome', 'name',
            'descricao', 'description',
            'status',
            'prioridade', 'priority',
            'data_inicio', 'start_date',
            'data_fim', 'due_date',
            'progresso', 'progress'
        ]
    
    def has_conflict(self, excel_data: Dict[str, Any], clickup_data: Dict[str, Any]) -> bool:
        """
        Check if there's a conflict between Excel and ClickUp data
        
        Args:
            excel_data: Data from Excel
            clickup_data: Data from ClickUp
            
        Returns:
            True if conflict exists
        """
        try:
            # Check if both sources have been modified recently
            excel_modified = self._get_modification_time(excel_data, 'excel')
            clickup_modified = self._get_modification_time(clickup_data, 'clickup')
            
            if not excel_modified or not clickup_modified:
                return False  # Can't determine conflict without timestamps
            
            # Check for field-level conflicts
            conflicts = self._detect_field_conflicts(excel_data, clickup_data)
            
            if conflicts:
                logger.info(f"Conflict detected between Excel and ClickUp data: {conflicts}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for conflicts: {e}")
            return False
    
    def resolve_conflict(self, excel_data: Dict[str, Any], 
                        clickup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve conflicts between Excel and ClickUp data
        
        Args:
            excel_data: Data from Excel
            clickup_data: Data from ClickUp
            
        Returns:
            Resolved data dictionary
        """
        try:
            conflict_info = {
                'timestamp': datetime.now().isoformat(),
                'strategy': self.resolution_strategy,
                'excel_data': excel_data.copy(),
                'clickup_data': clickup_data.copy()
            }
            
            if self.resolution_strategy == "latest_wins":
                resolved_data = self._resolve_latest_wins(excel_data, clickup_data)
            elif self.resolution_strategy == "excel_wins":
                resolved_data = self._resolve_excel_wins(excel_data, clickup_data)
            elif self.resolution_strategy == "clickup_wins":
                resolved_data = self._resolve_clickup_wins(excel_data, clickup_data)
            else:
                logger.warning(f"Unknown resolution strategy: {self.resolution_strategy}")
                resolved_data = self._resolve_latest_wins(excel_data, clickup_data)
            
            conflict_info['resolved_data'] = resolved_data.copy()
            self.conflict_log.append(conflict_info)
            
            logger.info(f"Conflict resolved using strategy: {self.resolution_strategy}")
            return resolved_data
            
        except Exception as e:
            logger.error(f"Error resolving conflict: {e}")
            # Return Excel data as fallback
            return excel_data
    
    def _detect_field_conflicts(self, excel_data: Dict[str, Any], 
                               clickup_data: Dict[str, Any]) -> List[str]:
        """
        Detect conflicts at the field level
        
        Args:
            excel_data: Data from Excel
            clickup_data: Data from ClickUp
            
        Returns:
            List of conflicting field names
        """
        conflicts = []
        
        # Map ClickUp fields to Excel fields for comparison
        field_mapping = {
            'name': 'nome',
            'description': 'descricao',
            'status': 'status',
            'priority': 'prioridade',
            'start_date': 'data_inicio',
            'due_date': 'data_fim',
            'progress': 'progresso'
        }
        
        for clickup_field, excel_field in field_mapping.items():
            excel_value = excel_data.get(excel_field)
            clickup_value = clickup_data.get(clickup_field)
            
            # Skip if either value is empty
            if not excel_value or not clickup_value:
                continue
            
            # Normalize values for comparison
            excel_normalized = self._normalize_value(excel_value)
            clickup_normalized = self._normalize_value(clickup_value)
            
            if excel_normalized != clickup_normalized:
                conflicts.append(f"{excel_field}/{clickup_field}")
        
        return conflicts
    
    def _normalize_value(self, value: Any) -> str:
        """
        Normalize a value for comparison
        
        Args:
            value: Value to normalize
            
        Returns:
            Normalized string value
        """
        if value is None:
            return ""
        
        if isinstance(value, (int, float)):
            return str(value)
        
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        
        if isinstance(value, dict):
            # Handle ClickUp objects
            if 'status' in value:
                return str(value.get('status', ''))
            elif 'priority' in value:
                return str(value.get('priority', ''))
            else:
                return str(value)
        
        if isinstance(value, list):
            # Handle lists (tags, assignees)
            return ", ".join(str(item) for item in value)
        
        return str(value).strip().lower()
    
    def _get_modification_time(self, data: Dict[str, Any], source: str) -> Optional[datetime]:
        """
        Get modification time from data
        
        Args:
            data: Data dictionary
            source: Source type ('excel' or 'clickup')
            
        Returns:
            Modification datetime if available
        """
        try:
            if source == 'clickup':
                # ClickUp provides date_updated field
                date_updated = data.get('date_updated')
                if date_updated:
                    # ClickUp timestamps are in milliseconds
                    timestamp = int(date_updated) / 1000
                    return datetime.fromtimestamp(timestamp)
            
            # For Excel, we don't have modification time in the data
            # This would need to be tracked separately
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get modification time from {source}: {e}")
            return None
    
    def _resolve_latest_wins(self, excel_data: Dict[str, Any], 
                            clickup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve conflict by using the most recently modified data
        
        Args:
            excel_data: Data from Excel
            clickup_data: Data from ClickUp
            
        Returns:
            Resolved data
        """
        excel_modified = self._get_modification_time(excel_data, 'excel')
        clickup_modified = self._get_modification_time(clickup_data, 'clickup')
        
        # If we can't determine modification times, prefer Excel
        if not clickup_modified:
            logger.info("Using Excel data (no ClickUp modification time)")
            return excel_data
        
        if not excel_modified:
            logger.info("Using ClickUp data (no Excel modification time)")
            return self._convert_clickup_to_excel_format(clickup_data)
        
        # Use the most recent data
        if clickup_modified > excel_modified:
            logger.info("Using ClickUp data (more recent)")
            return self._convert_clickup_to_excel_format(clickup_data)
        else:
            logger.info("Using Excel data (more recent or equal)")
            return excel_data
    
    def _resolve_excel_wins(self, excel_data: Dict[str, Any], 
                           clickup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve conflict by always preferring Excel data
        
        Args:
            excel_data: Data from Excel
            clickup_data: Data from ClickUp
            
        Returns:
            Excel data
        """
        logger.info("Using Excel data (excel_wins strategy)")
        return excel_data
    
    def _resolve_clickup_wins(self, excel_data: Dict[str, Any], 
                             clickup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve conflict by always preferring ClickUp data
        
        Args:
            excel_data: Data from Excel
            clickup_data: Data from ClickUp
            
        Returns:
            ClickUp data converted to Excel format
        """
        logger.info("Using ClickUp data (clickup_wins strategy)")
        return self._convert_clickup_to_excel_format(clickup_data)
    
    def _convert_clickup_to_excel_format(self, clickup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert ClickUp data to Excel format for conflict resolution
        
        Args:
            clickup_data: ClickUp data
            
        Returns:
            Data in Excel format
        """
        # This is a simplified conversion for conflict resolution
        # In practice, you'd use the DataMapper for this
        excel_format = {}
        
        field_mapping = {
            'name': 'nome',
            'description': 'descricao',
            'status': 'status',
            'priority': 'prioridade',
            'start_date': 'data_inicio',
            'due_date': 'data_fim',
            'progress': 'progresso',
            'id': 'clickup_id'
        }
        
        for clickup_field, excel_field in field_mapping.items():
            value = clickup_data.get(clickup_field)
            if value is not None:
                excel_format[excel_field] = self._convert_clickup_value(clickup_field, value)
        
        return excel_format
    
    def _convert_clickup_value(self, field_name: str, value: Any) -> Any:
        """
        Convert ClickUp value to Excel format
        
        Args:
            field_name: Name of the field
            value: Value to convert
            
        Returns:
            Converted value
        """
        if field_name == 'priority':
            priority_map = {1: 'Urgente', 2: 'Alta', 3: 'Normal', 4: 'Baixa'}
            if isinstance(value, dict):
                priority_val = value.get('priority')
            else:
                priority_val = value
            return priority_map.get(priority_val, 'Normal')
        
        elif field_name == 'status':
            if isinstance(value, dict):
                return value.get('status', '').title()
            return str(value).title()
        
        elif field_name in ['start_date', 'due_date']:
            if isinstance(value, (int, float)):
                timestamp = value / 1000 if value > 1000000000000 else value
                try:
                    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                except (ValueError, OSError):
                    return ""
            return str(value) if value else ""
        
        else:
            return value
    
    def get_conflict_log(self) -> List[Dict[str, Any]]:
        """
        Get the conflict resolution log
        
        Returns:
            List of conflict resolution records
        """
        return self.conflict_log.copy()
    
    def clear_conflict_log(self) -> None:
        """Clear the conflict resolution log"""
        self.conflict_log.clear()
        logger.info("Conflict log cleared")
    
    def get_conflict_stats(self) -> Dict[str, Any]:
        """
        Get statistics about conflicts
        
        Returns:
            Dictionary containing conflict statistics
        """
        total_conflicts = len(self.conflict_log)
        
        strategy_counts = {}
        for conflict in self.conflict_log:
            strategy = conflict.get('strategy', 'unknown')
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            'total_conflicts': total_conflicts,
            'strategy_distribution': strategy_counts,
            'current_strategy': self.resolution_strategy
        }
