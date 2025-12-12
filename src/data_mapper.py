"""
Data Mapper for ClickUp Excel Integration

This module handles data transformation between Excel and ClickUp formats,
providing flexible field mapping and data conversion.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class DataMapper:
    """
    Handles data mapping between Excel and ClickUp formats
    
    Features:
    - Flexible field mapping
    - Data type conversion
    - Custom field handling
    - Validation and sanitization
    """
    
    def __init__(self, field_mapping: Optional[Dict[str, str]] = None):
        """
        Initialize the data mapper
        
        Args:
            field_mapping: Custom field mapping dictionary
        """
        # Default field mapping (Excel -> ClickUp)
        self.default_mapping = {
            'nome': 'name',
            'descricao': 'description',
            'status': 'status',
            'prioridade': 'priority',
            'responsavel': 'assignees',
            'data_inicio': 'start_date',
            'data_fim': 'due_date',
            'progresso': 'progress',
            'tags': 'tags',
            'clickup_id': 'id'
        }
        
        # Reverse mapping (ClickUp -> Excel)
        self.reverse_mapping = {v: k for k, v in self.default_mapping.items()}
        
        # Use custom mapping if provided
        if field_mapping:
            self.default_mapping.update(field_mapping)
            self.reverse_mapping = {v: k for k, v in self.default_mapping.items()}
        
        # Priority mapping
        self.priority_mapping = {
            'Baixa': 4,
            'Normal': 3,
            'Alta': 2,
            'Urgente': 1,
            'Low': 4,
            'Normal': 3,
            'High': 2,
            'Urgent': 1
        }
        
        self.reverse_priority_mapping = {
            4: 'Baixa',
            3: 'Normal',
            2: 'Alta',
            1: 'Urgente'
        }
        
        # Status mapping (can be customized based on ClickUp list configuration)
        self.status_mapping = {
            'A fazer': 'to do',
            'Em andamento': 'in progress',
            'Em revisão': 'review',
            'Concluído': 'complete',
            'Cancelado': 'cancelled'
        }
        
        self.reverse_status_mapping = {v: k for k, v in self.status_mapping.items()}
    
    def excel_to_clickup(self, excel_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Excel row data to ClickUp task format
        
        Args:
            excel_data: Dictionary containing Excel row data
            
        Returns:
            Dictionary in ClickUp task format
        """
        clickup_data = {}
        
        try:
            # Map basic fields
            for excel_field, clickup_field in self.default_mapping.items():
                value = excel_data.get(excel_field)
                if value is not None and value != "":
                    clickup_data[clickup_field] = self._convert_excel_to_clickup_value(
                        excel_field, value
                    )
            
            # Handle special fields
            self._handle_excel_special_fields(excel_data, clickup_data)
            
            logger.debug(f"Converted Excel data to ClickUp: {clickup_data}")
            return clickup_data
            
        except Exception as e:
            logger.error(f"Error converting Excel to ClickUp data: {e}")
            return {}
    
    def clickup_to_excel(self, clickup_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert ClickUp task data to Excel row format
        
        Args:
            clickup_data: Dictionary containing ClickUp task data
            
        Returns:
            Dictionary in Excel row format
        """
        excel_data = {}
        
        try:
            # Map basic fields
            for clickup_field, excel_field in self.reverse_mapping.items():
                value = clickup_data.get(clickup_field)
                if value is not None:
                    excel_data[excel_field] = self._convert_clickup_to_excel_value(
                        clickup_field, value
                    )
            
            # Handle special fields
            self._handle_clickup_special_fields(clickup_data, excel_data)
            
            logger.debug(f"Converted ClickUp data to Excel: {excel_data}")
            return excel_data
            
        except Exception as e:
            logger.error(f"Error converting ClickUp to Excel data: {e}")
            return {}
    
    def _convert_excel_to_clickup_value(self, field_name: str, value: Any) -> Any:
        """
        Convert Excel field value to ClickUp format
        
        Args:
            field_name: Name of the Excel field
            value: Value to convert
            
        Returns:
            Converted value
        """
        if value is None or value == "":
            return None
        
        # Handle different field types
        if field_name == 'prioridade':
            return self._convert_priority_to_clickup(value)
        elif field_name == 'status':
            return self._convert_status_to_clickup(value)
        elif field_name in ['data_inicio', 'data_fim']:
            return self._convert_date_to_clickup(value)
        elif field_name == 'responsavel':
            return self._convert_assignee_to_clickup(value)
        elif field_name == 'tags':
            return self._convert_tags_to_clickup(value)
        elif field_name == 'progresso':
            return self._convert_progress_to_clickup(value)
        else:
            return str(value) if value is not None else None
    
    def _convert_clickup_to_excel_value(self, field_name: str, value: Any) -> Any:
        """
        Convert ClickUp field value to Excel format
        
        Args:
            field_name: Name of the ClickUp field
            value: Value to convert
            
        Returns:
            Converted value
        """
        if value is None:
            return ""
        
        # Handle different field types
        if field_name == 'priority':
            return self._convert_priority_to_excel(value)
        elif field_name == 'status':
            return self._convert_status_to_excel(value)
        elif field_name in ['start_date', 'due_date']:
            return self._convert_date_to_excel(value)
        elif field_name == 'assignees':
            return self._convert_assignee_to_excel(value)
        elif field_name == 'tags':
            return self._convert_tags_to_excel(value)
        else:
            return str(value) if value is not None else ""
    
    def _convert_priority_to_clickup(self, value: Any) -> Optional[int]:
        """Convert Excel priority to ClickUp priority"""
        if isinstance(value, (int, float)):
            return int(value) if 1 <= value <= 4 else None
        
        priority_str = str(value).strip()
        return self.priority_mapping.get(priority_str)
    
    def _convert_priority_to_excel(self, value: Any) -> str:
        """Convert ClickUp priority to Excel priority"""
        if isinstance(value, dict):
            priority_value = value.get('priority')
        else:
            priority_value = value
        
        if isinstance(priority_value, (int, float)):
            return self.reverse_priority_mapping.get(int(priority_value), "Normal")
        
        return "Normal"
    
    def _convert_status_to_clickup(self, value: Any) -> Optional[str]:
        """Convert Excel status to ClickUp status"""
        status_str = str(value).strip()
        return self.status_mapping.get(status_str, status_str.lower())
    
    def _convert_status_to_excel(self, value: Any) -> str:
        """Convert ClickUp status to Excel status"""
        if isinstance(value, dict):
            status_value = value.get('status', '')
        else:
            status_value = str(value) if value else ''
        
        return self.reverse_status_mapping.get(status_value, status_value.title())
    
    def _convert_date_to_clickup(self, value: Any) -> Optional[int]:
        """Convert Excel date to ClickUp timestamp"""
        if not value:
            return None
        
        try:
            if isinstance(value, datetime):
                return int(value.timestamp() * 1000)  # ClickUp uses milliseconds
            elif isinstance(value, str):
                # Try to parse date string
                date_obj = datetime.strptime(value, "%Y-%m-%d")
                return int(date_obj.timestamp() * 1000)
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to convert date '{value}': {e}")
        
        return None
    
    def _convert_date_to_excel(self, value: Any) -> str:
        """Convert ClickUp timestamp to Excel date"""
        if not value:
            return ""
        
        try:
            if isinstance(value, (int, float)):
                # ClickUp timestamps are in milliseconds
                timestamp = value / 1000 if value > 1000000000000 else value
                date_obj = datetime.fromtimestamp(timestamp)
                return date_obj.strftime("%Y-%m-%d")
            elif isinstance(value, str):
                return value  # Already a string
        except (ValueError, TypeError, OSError) as e:
            logger.warning(f"Failed to convert timestamp '{value}': {e}")
        
        return ""
    
    def _convert_assignee_to_clickup(self, value: Any) -> Optional[List[int]]:
        """Convert Excel assignee to ClickUp assignee list"""
        if not value:
            return None
        
        # For now, return None as we need user ID mapping
        # This would require a separate user mapping configuration
        logger.warning(f"Assignee conversion not implemented: {value}")
        return None
    
    def _convert_assignee_to_excel(self, value: Any) -> str:
        """Convert ClickUp assignee list to Excel assignee"""
        if not value:
            return ""
        
        try:
            if isinstance(value, list):
                # Extract usernames from assignee list
                names = []
                for assignee in value:
                    if isinstance(assignee, dict):
                        name = assignee.get('username') or assignee.get('email', '')
                        if name:
                            names.append(name)
                return ", ".join(names)
        except Exception as e:
            logger.warning(f"Failed to convert assignees '{value}': {e}")
        
        return str(value) if value else ""
    
    def _convert_tags_to_clickup(self, value: Any) -> Optional[List[str]]:
        """Convert Excel tags to ClickUp tags list"""
        if not value:
            return None
        
        tags_str = str(value).strip()
        if not tags_str:
            return None
        
        # Split by comma and clean up
        tags = [tag.strip() for tag in tags_str.split(',') if tag.strip()]
        return tags if tags else None
    
    def _convert_tags_to_excel(self, value: Any) -> str:
        """Convert ClickUp tags list to Excel tags"""
        if not value:
            return ""
        
        try:
            if isinstance(value, list):
                # Extract tag names
                tag_names = []
                for tag in value:
                    if isinstance(tag, dict):
                        name = tag.get('name', '')
                    else:
                        name = str(tag)
                    if name:
                        tag_names.append(name)
                return ", ".join(tag_names)
        except Exception as e:
            logger.warning(f"Failed to convert tags '{value}': {e}")
        
        return str(value) if value else ""
    
    def _convert_progress_to_clickup(self, value: Any) -> Optional[int]:
        """Convert Excel progress to ClickUp progress"""
        if not value:
            return None
        
        try:
            progress = float(value)
            # Ensure progress is between 0 and 100
            return max(0, min(100, int(progress)))
        except (ValueError, TypeError):
            return None
    
    def _handle_excel_special_fields(self, excel_data: Dict[str, Any], 
                                     clickup_data: Dict[str, Any]) -> None:
        """Handle special Excel fields that need custom processing"""
        # Add any special field handling here
        pass
    
    def _handle_clickup_special_fields(self, clickup_data: Dict[str, Any], 
                                       excel_data: Dict[str, Any]) -> None:
        """Handle special ClickUp fields that need custom processing"""
        # Ensure ClickUp ID is included
        if 'id' in clickup_data:
            excel_data['clickup_id'] = clickup_data['id']
        
        # Handle custom fields if present
        custom_fields = clickup_data.get('custom_fields', [])
        for field in custom_fields:
            field_name = field.get('name', '').lower()
            field_value = field.get('value')
            
            # Map common custom fields
            if 'progresso' in field_name or 'progress' in field_name:
                excel_data['progresso'] = field_value
    
    def validate_excel_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate Excel data before conversion
        
        Args:
            data: Excel data to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required fields
        if not data.get('nome'):
            errors.append("Nome do projeto é obrigatório")
        
        # Validate dates
        for date_field in ['data_inicio', 'data_fim']:
            date_value = data.get(date_field)
            if date_value and not self._is_valid_date(date_value):
                errors.append(f"Data inválida em {date_field}: {date_value}")
        
        # Validate progress
        progress = data.get('progresso')
        if progress is not None:
            try:
                progress_val = float(progress)
                if not (0 <= progress_val <= 100):
                    errors.append("Progresso deve estar entre 0 e 100")
            except (ValueError, TypeError):
                errors.append(f"Progresso inválido: {progress}")
        
        return errors
    
    def _is_valid_date(self, date_value: Any) -> bool:
        """Check if a date value is valid"""
        if isinstance(date_value, datetime):
            return True
        
        if isinstance(date_value, str):
            try:
                datetime.strptime(date_value, "%Y-%m-%d")
                return True
            except ValueError:
                return False
        
        return False
