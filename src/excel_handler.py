"""
Excel Handler for ClickUp Integration

This module handles reading from and writing to Excel files,
providing a clean interface for data synchronization.
"""

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from typing import Dict, List, Any, Optional, Tuple
import os
import shutil
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExcelHandlerError(Exception):
    """Custom exception for Excel handling errors"""
    pass


class ExcelHandler:
    """
    Handles Excel file operations for ClickUp integration
    
    Features:
    - Read/write Excel files
    - Data validation
    - Backup creation
    - Formatting preservation
    - Error handling
    """
    
    def __init__(self, file_path: str, worksheet_name: str = "Projetos", data_start_row: int = 2):
        """
        Initialize the Excel handler
        
        Args:
            file_path: Path to the Excel file
            worksheet_name: Name of the worksheet to work with
            data_start_row: Row number where data starts (1-indexed)
        """
        self.file_path = file_path
        self.worksheet_name = worksheet_name
        self.data_start_row = data_start_row
        self.workbook = None
        self.worksheet = None
        
        # Standard column mapping (can be customized)
        self.default_columns = {
            'A': 'nome',           # Task name
            'B': 'descricao',      # Description
            'C': 'status',         # Status
            'D': 'prioridade',     # Priority
            'E': 'responsavel',    # Assignee
            'F': 'data_inicio',    # Start date
            'G': 'data_fim',       # Due date
            'H': 'progresso',      # Progress %
            'I': 'tags',           # Tags
            'J': 'clickup_id'      # ClickUp task ID (for sync)
        }
    
    def create_backup(self) -> str:
        """
        Create a backup of the Excel file
        
        Returns:
            Path to the backup file
        """
        if not os.path.exists(self.file_path):
            raise ExcelHandlerError(f"Excel file not found: {self.file_path}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.file_path}.backup_{timestamp}"
        
        try:
            shutil.copy2(self.file_path, backup_path)
            logger.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            raise ExcelHandlerError(f"Failed to create backup: {e}")
    
    def load_workbook(self) -> None:
        """Load the Excel workbook and worksheet"""
        try:
            if os.path.exists(self.file_path):
                self.workbook = openpyxl.load_workbook(self.file_path)
                logger.info(f"Loaded existing workbook: {self.file_path}")
            else:
                self.workbook = openpyxl.Workbook()
                logger.info(f"Created new workbook: {self.file_path}")
            
            # Get or create worksheet
            if self.worksheet_name in self.workbook.sheetnames:
                self.worksheet = self.workbook[self.worksheet_name]
            else:
                self.worksheet = self.workbook.create_sheet(self.worksheet_name)
                self._setup_headers()
                
        except Exception as e:
            raise ExcelHandlerError(f"Failed to load workbook: {e}")
    
    def _setup_headers(self) -> None:
        """Setup column headers in the worksheet"""
        headers = [
            'Nome do Projeto',
            'Descrição',
            'Status',
            'Prioridade',
            'Responsável',
            'Data de Início',
            'Data de Fim',
            'Progresso (%)',
            'Tags',
            'ClickUp ID'
        ]
        
        # Write headers
        for col, header in enumerate(headers, 1):
            cell = self.worksheet.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.alignment = Alignment(horizontal="center")
        
        logger.info("Headers setup completed")
    
    def read_data(self) -> List[Dict[str, Any]]:
        """
        Read all data from the Excel file
        
        Returns:
            List of dictionaries containing row data
        """
        if not self.workbook:
            self.load_workbook()
        
        data = []
        max_row = self.worksheet.max_row
        
        for row_num in range(self.data_start_row, max_row + 1):
            row_data = {}
            has_data = False
            
            for col_letter, field_name in self.default_columns.items():
                cell_value = self.worksheet[f"{col_letter}{row_num}"].value
                if cell_value is not None:
                    has_data = True
                    # Convert dates to string format
                    if isinstance(cell_value, datetime):
                        cell_value = cell_value.strftime("%Y-%m-%d")
                    row_data[field_name] = cell_value
                else:
                    row_data[field_name] = ""
            
            if has_data:
                row_data['excel_row'] = row_num
                data.append(row_data)
        
        logger.info(f"Read {len(data)} rows from Excel")
        return data
    
    def write_data(self, data: List[Dict[str, Any]], clear_existing: bool = False) -> None:
        """
        Write data to the Excel file
        
        Args:
            data: List of dictionaries containing data to write
            clear_existing: Whether to clear existing data first
        """
        if not self.workbook:
            self.load_workbook()
        
        if clear_existing:
            # Clear existing data (keep headers)
            for row in range(self.data_start_row, self.worksheet.max_row + 1):
                for col in range(1, len(self.default_columns) + 1):
                    self.worksheet.cell(row=row, column=col).value = None
        
        # Write data
        for row_idx, row_data in enumerate(data, self.data_start_row):
            for col_letter, field_name in self.default_columns.items():
                value = row_data.get(field_name, "")
                
                # Handle special formatting
                if field_name in ['data_inicio', 'data_fim'] and value:
                    try:
                        if isinstance(value, str):
                            value = datetime.strptime(value, "%Y-%m-%d")
                    except ValueError:
                        pass  # Keep original value if parsing fails
                
                self.worksheet[f"{col_letter}{row_idx}"].value = value
        
        logger.info(f"Wrote {len(data)} rows to Excel")
    
    def update_row(self, row_num: int, data: Dict[str, Any]) -> None:
        """
        Update a specific row with new data
        
        Args:
            row_num: Row number to update (1-indexed)
            data: Dictionary containing updated data
        """
        if not self.workbook:
            self.load_workbook()
        
        for col_letter, field_name in self.default_columns.items():
            if field_name in data:
                value = data[field_name]
                
                # Handle date formatting
                if field_name in ['data_inicio', 'data_fim'] and value:
                    try:
                        if isinstance(value, str):
                            value = datetime.strptime(value, "%Y-%m-%d")
                    except ValueError:
                        pass
                
                self.worksheet[f"{col_letter}{row_num}"].value = value
        
        logger.info(f"Updated row {row_num}")
    
    def add_row(self, data: Dict[str, Any]) -> int:
        """
        Add a new row with data
        
        Args:
            data: Dictionary containing row data
            
        Returns:
            Row number of the added row
        """
        if not self.workbook:
            self.load_workbook()
        
        # Find next empty row
        next_row = self.worksheet.max_row + 1
        
        for col_letter, field_name in self.default_columns.items():
            value = data.get(field_name, "")
            
            # Handle date formatting
            if field_name in ['data_inicio', 'data_fim'] and value:
                try:
                    if isinstance(value, str):
                        value = datetime.strptime(value, "%Y-%m-%d")
                except ValueError:
                    pass
            
            self.worksheet[f"{col_letter}{next_row}"].value = value
        
        logger.info(f"Added new row {next_row}")
        return next_row
    
    def find_row_by_clickup_id(self, clickup_id: str) -> Optional[int]:
        """
        Find a row by ClickUp ID
        
        Args:
            clickup_id: ClickUp task ID to search for
            
        Returns:
            Row number if found, None otherwise
        """
        if not self.workbook:
            self.load_workbook()
        
        clickup_col = 'J'  # Column J contains ClickUp IDs
        
        for row_num in range(self.data_start_row, self.worksheet.max_row + 1):
            cell_value = self.worksheet[f"{clickup_col}{row_num}"].value
            if str(cell_value) == str(clickup_id):
                return row_num
        
        return None
    
    def save(self) -> None:
        """Save the workbook to file"""
        if not self.workbook:
            raise ExcelHandlerError("No workbook loaded")
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            self.workbook.save(self.file_path)
            logger.info(f"Saved workbook: {self.file_path}")
        except Exception as e:
            raise ExcelHandlerError(f"Failed to save workbook: {e}")
    
    def close(self) -> None:
        """Close the workbook"""
        if self.workbook:
            self.workbook.close()
            self.workbook = None
            self.worksheet = None
    
    def validate_structure(self) -> bool:
        """
        Validate that the Excel file has the expected structure
        
        Returns:
            True if structure is valid
        """
        if not self.workbook:
            self.load_workbook()
        
        # Check if required columns exist
        expected_headers = len(self.default_columns)
        actual_headers = 0
        
        for col in range(1, expected_headers + 1):
            if self.worksheet.cell(row=1, column=col).value:
                actual_headers += 1
        
        is_valid = actual_headers >= expected_headers
        logger.info(f"Excel structure validation: {'PASSED' if is_valid else 'FAILED'}")
        return is_valid
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Excel file
        
        Returns:
            Dictionary containing file statistics
        """
        if not self.workbook:
            self.load_workbook()
        
        data = self.read_data()
        
        stats = {
            'total_rows': len(data),
            'file_path': self.file_path,
            'worksheet_name': self.worksheet_name,
            'last_modified': datetime.fromtimestamp(os.path.getmtime(self.file_path)).isoformat() if os.path.exists(self.file_path) else None,
            'has_clickup_ids': sum(1 for row in data if row.get('clickup_id')),
            'status_distribution': {}
        }
        
        # Count status distribution
        for row in data:
            status = row.get('status', 'Unknown')
            stats['status_distribution'][status] = stats['status_distribution'].get(status, 0) + 1
        
        return stats
