import logging
from typing import Optional, Type, List, Dict
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from atlassian import Jira
from config import config

logger = logging.getLogger(__name__)

class JiraClient:
    """Simple Jira API client using atlassian library"""
    
    def __init__(self):
        self.base_url = config.JIRA_SERVER_URL
        self.username = config.JIRA_USERNAME
        self.api_token = config.JIRA_API_TOKEN
        self.default_project = config.JIRA_PROJECT
        self.verify_ssl = config.VERIFY_SSL
        
        self.is_configured = bool(self.base_url and self.username and self.api_token)
        
        if self.is_configured:
            # Initialize Jira client from atlassian library
            self.jira = Jira(
                url=self.base_url,
                username=self.username,
                password=self.api_token,  # API token is used as password
                verify_ssl=self.verify_ssl
            )
            logger.info(f"Jira client configured for: {self.base_url}")
            if self.default_project:
                logger.info(f"Default project: {self.default_project}")
        else:
            self.jira = None
            logger.error("Jira client not properly configured - please set JIRA_SERVER_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file")
    
    def search_issues(self, jql: str = "", project_key: Optional[str] = None, max_results: int = 50) -> List[Dict]:
        """Search for Jira issues using atlassian library"""
        
        if not self.is_configured:
            raise Exception("Jira client not configured. Please set JIRA_SERVER_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file")
        
        # Build JQL query based on parameters
        final_jql = ""
        
        # Handle project filtering
        if project_key:
            # Specific project requested
            final_jql = f"project = \"{project_key}\""
        elif self.default_project:
            # Use default project
            final_jql = f"project = \"{self.default_project}\""
        # If no project specified, search all projects (no project filter)
        
        # Add custom JQL if provided
        if jql:
            if final_jql:
                final_jql = f"{final_jql} AND ({jql})"
            else:
                final_jql = jql
        
        # Add ordering
        if final_jql:
            final_jql = f"{final_jql} ORDER BY created DESC"
        else:
            # No filters at all, just order by created date
            final_jql = "ORDER BY created DESC"
        
        logger.debug(f"Searching Jira with JQL: {final_jql}")
        
        try:
            # Use atlassian library to search issues
            result = self.jira.jql(
                jql=final_jql,
                limit=max_results,
                fields="key,summary,status,assignee,project,created,updated,priority,labels,description"
            )
            
            issues = []
            for issue_data in result.get("issues", []):
                issue = self._format_issue(issue_data)
                issues.append(issue)
            
            logger.info(f"Found {len(issues)} Jira issues")
            return issues
            
        except Exception as e:
            logger.error(f"Error searching Jira issues: {str(e)}")
            raise e
    
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
        description="Optional project key to filter issues (e.g., 'PROJ', 'DEV'). Leave empty or set to None to get issues from all projects or default project.",
        default=None
    )
    limit: int = Field(
        description="Maximum number of issues to retrieve",
        default=50
    )

class JiraGetIssuesTool(BaseTool):
    """A tool to get Jira issues with optional project filtering"""
    
    name: str = "jira_get_issues"
    description: str = """Get Jira issues from projects. Usage:
    - To get all issues: call with no parameters or project_key=None
    - To get issues from specific project: set project_key to the project code (e.g., 'PROJ')
    - To limit results: set limit parameter (default 50)
    
    Examples:
    - jira_get_issues() -> gets all issues from default/all projects  
    - jira_get_issues(project_key='PROJ') -> gets issues from PROJ project
    - jira_get_issues(limit=10) -> gets 10 issues from default/all projects"""
    args_schema: Type[BaseModel] = JiraGetIssuesInput
    
    def _run(self, project_key: Optional[str] = None, limit: int = 50) -> str:
        """Execute the Jira get issues tool"""
        logger.info(f"Jira tool called with project_key: {project_key}, limit: {limit}")
        
        # Validate and sanitize project_key input
        # Handle cases where LLM passes descriptive text instead of actual project key
        if project_key and (
            len(project_key) > 20 or  # Project keys are typically short
            '(' in project_key or 
            ')' in project_key or
            'all issues' in project_key.lower() or
            'default' in project_key.lower() or
            'without any input' in project_key.lower()
        ):
            logger.warning(f"Invalid project_key detected: '{project_key}' - treating as None")
            project_key = None
        
        # Create Jira client instance
        jira_client = JiraClient()
        
        try:
            # Get issues from Jira
            issues = jira_client.search_issues(
                project_key=project_key,  # Pass project_key directly
                max_results=limit
            )
            
            if not issues:
                if project_key:
                    return f"No issues found in project '{project_key}'"
                elif jira_client.default_project:
                    return f"No issues found in default project '{jira_client.default_project}'"
                else:
                    return "No issues found"
            
            # Format response
            result_lines = []
            
            # Determine which project context we're showing
            if project_key:
                result_lines.append(f"Found {len(issues)} issues in project '{project_key}':")
            elif jira_client.default_project:
                result_lines.append(f"Found {len(issues)} issues in default project '{jira_client.default_project}':")
            else:
                result_lines.append(f"Found {len(issues)} issues from all accessible projects:")
            
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
