"""
ClickUp API Client for Excel Integration

This module provides a robust client for interacting with the ClickUp API,
specifically designed for syncing with Excel spreadsheets.
"""

import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ClickUpAPIError(Exception):
    """Custom exception for ClickUp API errors"""
    pass


class ClickUpClient:
    """
    A robust client for interacting with the ClickUp API
    
    Features:
    - Rate limiting handling
    - Automatic retries
    - Error handling and logging
    - Task CRUD operations
    - List and workspace management
    """
    
    def __init__(self, api_token: str, base_url: str = "https://api.clickup.com/api/v2"):
        """
        Initialize the ClickUp client
        
        Args:
            api_token: Your ClickUp API token
            base_url: ClickUp API base URL
        """
        self.api_token = api_token
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': api_token,
            'Content-Type': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """
        Make a rate-limited request to the ClickUp API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            **kwargs: Additional arguments for requests
            
        Returns:
            JSON response as dictionary
            
        Raises:
            ClickUpAPIError: If the API request fails
        """
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            self.last_request_time = time.time()
            
            if response.status_code == 429:  # Rate limited
                retry_after = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                time.sleep(retry_after)
                return self._make_request(method, endpoint, **kwargs)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise ClickUpAPIError(f"API request failed: {e}")
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """
        Get all teams (workspaces) for the authenticated user
        
        Returns:
            List of team dictionaries
        """
        logger.info("Fetching teams...")
        response = self._make_request('GET', '/team')
        return response.get('teams', [])
    
    def get_spaces(self, team_id: str) -> List[Dict[str, Any]]:
        """
        Get all spaces in a team
        
        Args:
            team_id: The team ID
            
        Returns:
            List of space dictionaries
        """
        logger.info(f"Fetching spaces for team {team_id}...")
        response = self._make_request('GET', f'/team/{team_id}/space')
        return response.get('spaces', [])
    
    def get_lists(self, space_id: str) -> List[Dict[str, Any]]:
        """
        Get all lists in a space
        
        Args:
            space_id: The space ID
            
        Returns:
            List of list dictionaries
        """
        logger.info(f"Fetching lists for space {space_id}...")
        response = self._make_request('GET', f'/space/{space_id}/list')
        return response.get('lists', [])
    
    def get_list_by_name(self, space_id: str, list_name: str) -> Optional[Dict[str, Any]]:
        """
        Find a list by name in a space
        
        Args:
            space_id: The space ID
            list_name: Name of the list to find
            
        Returns:
            List dictionary if found, None otherwise
        """
        lists = self.get_lists(space_id)
        for list_item in lists:
            if list_item.get('name', '').lower() == list_name.lower():
                return list_item
        return None
    
    def get_tasks(self, list_id: str, include_closed: bool = False) -> List[Dict[str, Any]]:
        """
        Get all tasks in a list
        
        Args:
            list_id: The list ID
            include_closed: Whether to include closed tasks
            
        Returns:
            List of task dictionaries
        """
        logger.info(f"Fetching tasks for list {list_id}...")
        params = {
            'include_closed': str(include_closed).lower()
        }
        response = self._make_request('GET', f'/list/{list_id}/task', params=params)
        return response.get('tasks', [])
    
    def get_task(self, task_id: str) -> Dict[str, Any]:
        """
        Get a specific task by ID
        
        Args:
            task_id: The task ID
            
        Returns:
            Task dictionary
        """
        logger.info(f"Fetching task {task_id}...")
        return self._make_request('GET', f'/task/{task_id}')
    
    def create_task(self, list_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new task in a list
        
        Args:
            list_id: The list ID
            task_data: Task data dictionary
            
        Returns:
            Created task dictionary
        """
        logger.info(f"Creating task in list {list_id}: {task_data.get('name', 'Unnamed')}")
        return self._make_request('POST', f'/list/{list_id}/task', json=task_data)
    
    def update_task(self, task_id: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing task
        
        Args:
            task_id: The task ID
            task_data: Updated task data
            
        Returns:
            Updated task dictionary
        """
        logger.info(f"Updating task {task_id}")
        return self._make_request('PUT', f'/task/{task_id}', json=task_data)
    
    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task
        
        Args:
            task_id: The task ID
            
        Returns:
            True if successful
        """
        logger.info(f"Deleting task {task_id}")
        try:
            self._make_request('DELETE', f'/task/{task_id}')
            return True
        except ClickUpAPIError:
            return False
    
    def search_tasks(self, team_id: str, query: str) -> List[Dict[str, Any]]:
        """
        Search for tasks across the team
        
        Args:
            team_id: The team ID
            query: Search query
            
        Returns:
            List of matching tasks
        """
        logger.info(f"Searching tasks in team {team_id} for: {query}")
        params = {'query': query}
        response = self._make_request('GET', f'/team/{team_id}/task', params=params)
        return response.get('tasks', [])
    
    def get_custom_fields(self, list_id: str) -> List[Dict[str, Any]]:
        """
        Get custom fields for a list
        
        Args:
            list_id: The list ID
            
        Returns:
            List of custom field dictionaries
        """
        logger.info(f"Fetching custom fields for list {list_id}")
        response = self._make_request('GET', f'/list/{list_id}/field')
        return response.get('fields', [])
    
    def test_connection(self) -> bool:
        """
        Test the API connection
        
        Returns:
            True if connection is successful
        """
        try:
            self.get_teams()
            logger.info("ClickUp API connection successful")
            return True
        except ClickUpAPIError:
            logger.error("ClickUp API connection failed")
            return False
