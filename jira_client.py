#!/usr/bin/env python3
"""
Simplified Jira Client
Core Jira API functionality without unused features
"""

import os
import requests
from atlassian import Jira
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

class JiraClient:
    """Simplified Jira client for fetching issues and basic analytics"""
    
    def __init__(self):
        """Initialize Jira client with environment variables"""
        self.server_url = os.getenv('JIRA_SERVER_URL')
        self.username = os.getenv('JIRA_USERNAME')
        self.api_token = os.getenv('JIRA_API_TOKEN')
        
        self.jira = None
        self.is_connected = False
        
        if self.server_url and self.username and self.api_token:
            try:
                self.jira = Jira(
                    url=self.server_url,
                    username=self.username,
                    password=self.api_token,
                    cloud=True
                )
                self.is_connected = True
                logger.info(f"Connected to Jira: {self.server_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Jira: {e}")
                self.is_connected = False
        else:
            logger.warning("Jira credentials not found. Using sample data mode.")
    
    def fetch_issues(self, jql_query: str = "ORDER BY created DESC", max_results: int = 100) -> list:
        """
        Fetch issues from Jira using JQL query
        
        Args:
            jql_query: JQL query string
            max_results: Maximum number of results to fetch
            
        Returns:
            List of issue dictionaries
        """
        if not self.is_connected:
            return self._get_sample_data()
        
        try:
            # Fetch issues with required fields
            fields = [
                'key', 'summary', 'status', 'assignee', 'reporter', 
                'created', 'updated', 'issuetype', 'priority', 'labels', 
                'description'
            ]
            
            issues = self.jira.jql(
                jql_query,
                fields=','.join(fields),
                limit=max_results
            )
            
            processed_issues = []
            for issue in issues['issues']:
                processed_issue = self._process_issue(issue)
                processed_issues.append(processed_issue)
            
            logger.info(f"Fetched {len(processed_issues)} issues")
            return processed_issues
            
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            return self._get_sample_data()
    
    def get_issue_detail(self, issue_key: str) -> dict:
        """
        Get detailed information for a specific issue
        
        Args:
            issue_key: Jira issue key (e.g., 'PROJ-123')
            
        Returns:
            Issue detail dictionary
        """
        if not self.is_connected:
            return self._get_sample_issue_detail(issue_key)
        
        try:
            issue = self.jira.issue(issue_key)
            return self._process_issue(issue)
        except Exception as e:
            logger.error(f"Error fetching issue {issue_key}: {e}")
            return self._get_sample_issue_detail(issue_key)
    
    def _process_issue(self, issue: dict) -> dict:
        """Process raw Jira issue into simplified format"""
        fields = issue.get('fields', {})
        
        # Helper function to safely get nested values
        def safe_get(obj, path, default=''):
            try:
                for key in path:
                    obj = obj[key]
                return obj if obj is not None else default
            except (KeyError, TypeError):
                return default
        
        return {
            'key': issue.get('key', ''),
            'summary': safe_get(fields, ['summary'], 'No summary'),
            'description': safe_get(fields, ['description'], ''),
            'status': safe_get(fields, ['status', 'name'], 'Unknown'),
            'assignee': safe_get(fields, ['assignee', 'displayName'], 'Unassigned'),
            'reporter': safe_get(fields, ['reporter', 'displayName'], 'Unknown'),
            'issue_type': safe_get(fields, ['issuetype', 'name'], 'Unknown'),
            'priority': safe_get(fields, ['priority', 'name'], 'Unknown'),
            'created': safe_get(fields, ['created'], ''),
            'updated': safe_get(fields, ['updated'], ''),
            'labels': ', '.join(safe_get(fields, ['labels'], []))
        }
    
    def _get_sample_data(self) -> list:
        """Return sample data when Jira is not connected"""
        return [
            {
                'key': 'DEMO-001',
                'summary': 'Sample issue for development',
                'description': 'This is a sample issue used when Jira is not connected',
                'status': 'In Progress',
                'assignee': 'John Doe',
                'reporter': 'Jane Smith',
                'issue_type': 'Task',
                'priority': 'Medium',
                'created': '2024-01-01T10:00:00.000+0000',
                'updated': '2024-01-02T15:30:00.000+0000',
                'labels': 'development, sample'
            },
            {
                'key': 'DEMO-002',
                'summary': 'Another sample issue',
                'description': 'Second sample issue for testing',
                'status': 'Done',
                'assignee': 'Alice Johnson',
                'reporter': 'Bob Wilson',
                'issue_type': 'Bug',
                'priority': 'High',
                'created': '2024-01-03T09:15:00.000+0000',
                'updated': '2024-01-04T14:20:00.000+0000',
                'labels': 'bug, testing'
            },
            {
                'key': 'DEMO-003',
                'summary': 'Feature request sample',
                'description': 'Sample feature request',
                'status': 'To Do',
                'assignee': 'Unassigned',
                'reporter': 'Charlie Brown',
                'issue_type': 'Story',
                'priority': 'Low',
                'created': '2024-01-05T11:45:00.000+0000',
                'updated': '2024-01-05T11:45:00.000+0000',
                'labels': 'feature, enhancement'
            }
        ]
    
    def _get_sample_issue_detail(self, issue_key: str) -> dict:
        """Return sample issue detail"""
        sample_data = self._get_sample_data()
        
        # Try to find matching issue
        for issue in sample_data:
            if issue['key'] == issue_key:
                return issue
        
        # Return first sample if not found
        return sample_data[0] if sample_data else {}
