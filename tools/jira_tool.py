import logging
import requests
import json
from typing import Optional, Type, List, Dict
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from config import config

logger = logging.getLogger(__name__)

class JiraClient:
    """Simple Jira API client"""
    
    def __init__(self):
        self.base_url = config.JIRA_SERVER_URL
        self.username = config.JIRA_USERNAME
        self.api_token = config.JIRA_API_TOKEN
        self.default_project = config.JIRA_PROJECT
        self.verify_ssl = config.VERIFY_SSL
        
        # Setup authentication
        self.auth = (self.username, self.api_token) if self.username and self.api_token else None
        
        # Common headers
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        self.is_configured = bool(self.base_url and self.username and self.api_token)
        
        if self.is_configured:
            logger.info(f"Jira client configured for: {self.base_url}")
            if self.default_project:
                logger.info(f"Default project: {self.default_project}")
        else:
            logger.error("Jira client not properly configured - please set JIRA_SERVER_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file")
    
    def search_issues(self, jql: str = "", project_key: Optional[str] = None, max_results: int = 50) -> List[Dict]:
        """Search for Jira issues"""
        
        if not self.is_configured:
            raise Exception("Jira client not configured. Please set JIRA_SERVER_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file")
        
        # Use default project if none specified
        effective_project = project_key or self.default_project
        
        # Build JQL query
        if effective_project and jql:
            final_jql = f"project = {effective_project} AND ({jql})"
        elif effective_project:
            final_jql = f"project = {effective_project} ORDER BY created DESC"
        elif jql:
            final_jql = jql
        else:
            final_jql = "ORDER BY created DESC"
        
        # API endpoint
        url = f"{self.base_url}/rest/api/2/search"
        
        params = {
            "jql": final_jql,
            "maxResults": max_results,
            "fields": "key,summary,status,assignee,project,created,updated,priority,labels,description"
        }
        
        logger.debug(f"Searching Jira with JQL: {final_jql}")
        
        response = requests.get(
            url,
            headers=self.headers,
            auth=self.auth,
            params=params,
            verify=self.verify_ssl,
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        issues = []
        for issue_data in result.get("issues", []):
            issue = self._format_issue(issue_data)
            issues.append(issue)
        
        logger.info(f"Found {len(issues)} Jira issues")
        return issues
    
    def _format_issue(self, issue_data: Dict) -> Dict:
        """Format Jira issue data"""
        fields = issue_data.get("fields", {})
        
        # Safe extraction with fallbacks
        assignee = "Unassigned"
        if fields.get("assignee"):
            assignee = fields["assignee"].get("displayName", "Unknown")
        
        status = "Unknown"
        if fields.get("status"):
            status = fields["status"].get("name", "Unknown")
        
        project = "Unknown"
        if fields.get("project"):
            project = fields["project"].get("key", "Unknown")
        
        priority = "Unknown"
        if fields.get("priority"):
            priority = fields["priority"].get("name", "Unknown")
        
        labels = ""
        if fields.get("labels"):
            labels = ", ".join(fields["labels"])
        
        return {
            "key": issue_data.get("key", ""),
            "summary": fields.get("summary", ""),
            "description": fields.get("description", "")[:200] + "..." if fields.get("description", "") else "",
            "status": status,
            "assignee": assignee,
            "project": project,
            "priority": priority,
            "labels": labels,
            "created": fields.get("created", ""),
            "updated": fields.get("updated", "")
        }

class JiraGetIssuesInput(BaseModel):
    """Input for Jira get issues tool"""
    project_key: Optional[str] = Field(
        description="Optional project key to filter issues (e.g., 'PROJ', 'DEV'). If not provided, gets issues from all projects.",
        default=None
    )
    limit: int = Field(
        description="Maximum number of issues to retrieve",
        default=50
    )

class JiraGetIssuesTool(BaseTool):
    """A tool to get Jira issues with optional project filtering"""
    
    name: str = "jira_get_issues"
    description: str = "Get Jira issues from all projects or filter by specific project. Use this when user asks about Jira issues, wants to see project issues, or needs to list tickets."
    args_schema: Type[BaseModel] = JiraGetIssuesInput
    
    def _run(self, project_key: Optional[str] = None, limit: int = 50) -> str:
        """Execute the Jira get issues tool"""
        logger.info(f"Jira tool called with project_key: {project_key}, limit: {limit}")
        
        # Create Jira client instance
        jira_client = JiraClient()
        
        try:
            # Use default project if none specified
            effective_project = project_key or jira_client.default_project
            
            # Get issues from Jira
            issues = jira_client.search_issues(
                project_key=effective_project,
                max_results=limit
            )
            
            if not issues:
                if effective_project:
                    return f"No issues found in project '{effective_project}'"
                else:
                    return "No issues found"
            
            # Format response
            result_lines = []
            
            if effective_project:
                if project_key:
                    result_lines.append(f"Found {len(issues)} issues in project '{effective_project}':")
                else:
                    result_lines.append(f"Found {len(issues)} issues in default project '{effective_project}':")
            else:
                result_lines.append(f"Found {len(issues)} issues from all projects:")
            
            result_lines.append("")
            
            for issue in issues:
                issue_line = f"• {issue['key']}: {issue['summary']}"
                issue_line += f" (Status: {issue['status']}, Assignee: {issue['assignee']})"
                if issue['priority'] != "Unknown":
                    issue_line += f" [Priority: {issue['priority']}]"
                result_lines.append(issue_line)
            
            # Add configuration note
            result_lines.append("")
            result_lines.append(f"✅ Connected to Jira: {jira_client.base_url}")
            
            result = "\n".join(result_lines)
            logger.info(f"Successfully retrieved {len(issues)} issues")
            return result
            
        except Exception as e:
            error_msg = f"Error retrieving Jira issues: {str(e)}"
            logger.error(error_msg)
            return error_msg
