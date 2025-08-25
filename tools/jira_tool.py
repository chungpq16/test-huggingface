import logging
from typing import Optional, Type, List, Dict
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from atlassian import Jira
from config import config

logger = logging.getLogger(__name__)

class JiraClient:
    """Simplified Jira client for fetching issues and basic analytics"""
    
    def __init__(self):
        """Initialize Jira client with environment variables"""
        self.server_url = config.JIRA_SERVER_URL
        self.username = config.JIRA_USERNAME
        self.api_token = config.JIRA_API_TOKEN
        self.default_project = config.JIRA_PROJECT
        self.verify_ssl = config.VERIFY_SSL
        
        # Debug logging to see what values are loaded
        logger.debug(f"Jira config loaded - URL: {self.server_url}")
        logger.debug(f"Jira config loaded - Username: {self.username}")
        logger.debug(f"Jira config loaded - API Token: {'***' if self.api_token else 'NOT SET'}")
        logger.debug(f"Jira config loaded - Default Project: {self.default_project}")
        logger.debug(f"Jira config loaded - Verify SSL: {self.verify_ssl}")
        
        self.jira = None
        self.is_connected = False
        
        if self.server_url and self.username and self.api_token:
            try:
                self.jira = Jira(
                    url=self.server_url,
                    username=self.username,
                    password=self.api_token,
                    verify_ssl=self.verify_ssl
                )
                self.is_connected = True
                logger.info(f"Connected to Jira: {self.server_url}")
                if self.default_project:
                    logger.info(f"Default project: {self.default_project}")
                else:
                    logger.warning("No default project set in JIRA_PROJECT environment variable")
            except Exception as e:
                logger.error(f"Failed to connect to Jira: {e}")
                self.is_connected = False
        else:
            logger.error("Jira credentials not found. Please set JIRA_SERVER_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file")
            raise Exception("Jira credentials not configured. Please set JIRA_SERVER_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file")
    
    def fetch_issues(self, jql_query: str = "ORDER BY created DESC", max_results: int = 100, project_key: Optional[str] = None) -> list:
        """
        Fetch issues from Jira using JQL query with optional project filtering
        
        Args:
            jql_query: JQL query string
            max_results: Maximum number of results to fetch
            project_key: Optional project key to filter by
            
        Returns:
            List of issue dictionaries
        """
        if not self.is_connected:
            raise Exception("Jira client not configured. Please set JIRA_SERVER_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file")
        
        try:
            # Build JQL with project filtering
            final_jql = self._build_jql_with_project(jql_query, project_key)
            
            logger.info(f"Executing JQL query: '{final_jql}'")
            
            # Fetch issues with required fields
            fields = [
                'key', 'summary', 'status', 'assignee', 'reporter', 
                'created', 'updated', 'issuetype', 'priority', 'labels', 
                'description', 'project'
            ]
            
            result = self.jira.jql(
                final_jql,
                fields=','.join(fields),
                limit=max_results
            )
            
            processed_issues = []
            for issue in result.get('issues', []):
                processed_issue = self._process_issue(issue)
                processed_issues.append(processed_issue)
            
            logger.info(f"Fetched {len(processed_issues)} issues")
            return processed_issues
            
        except Exception as e:
            logger.error(f"Error fetching issues: {e}")
            
            # Check if it's a project-not-found error
            error_str = str(e)
            if "does not exist for the field 'project'" in error_str:
                # Extract the invalid project key from error message - improved regex
                import re
                # Look for the pattern: The value 'PROJECT_KEY' does not exist for the field 'project'
                match = re.search(r"The value '([^']+)' does not exist for the field 'project'", error_str)
                invalid_project = match.group(1) if match else "unknown"
                
                # Additional debug logging
                logger.debug(f"Project not found error detected. Full error: {error_str}")
                logger.debug(f"Extracted invalid project: '{invalid_project}'")
                
                suggestion = f"Project '{invalid_project}' not found. Please check the project key or contact your Jira administrator."
                raise Exception(suggestion)
            
            raise e
    
    def _build_jql_with_project(self, jql_query: str, project_key: Optional[str] = None) -> str:
        """Build JQL query with project filtering"""
        # Debug logging
        logger.debug(f"Building JQL - Input query: '{jql_query}', project_key: '{project_key}', default_project: '{self.default_project}'")
        
        # Determine which project to use - be explicit about None checking
        effective_project = None
        if project_key is not None and project_key.strip():
            effective_project = project_key.strip()
        elif self.default_project and self.default_project.strip():
            effective_project = self.default_project.strip()
        
        logger.debug(f"Effective project determined: '{effective_project}'")
        
        # Build project filter
        project_filter = ""
        if effective_project:
            project_filter = f'project = "{effective_project}"'
        
        # Combine with existing JQL
        if project_filter:
            if jql_query and not jql_query.lower().strip().startswith('order by'):
                # If we have both project filter and custom JQL (not just ORDER BY)
                final_jql = f"{project_filter} AND ({jql_query})"
            else:
                # Just project filter with optional ordering
                if jql_query and jql_query.lower().strip().startswith('order by'):
                    final_jql = f"{project_filter} {jql_query}"
                else:
                    final_jql = f"{project_filter} ORDER BY created DESC"
        else:
            # No project filtering
            final_jql = jql_query or "ORDER BY created DESC"
        
        logger.debug(f"Built JQL: '{final_jql}'")
        return final_jql
    
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
            'description': safe_get(fields, ['description'], '')[:200] + "..." if safe_get(fields, ['description'], '') else '',
            'status': safe_get(fields, ['status', 'name'], 'Unknown'),
            'assignee': safe_get(fields, ['assignee', 'displayName'], 'Unassigned'),
            'reporter': safe_get(fields, ['reporter', 'displayName'], 'Unknown'),
            'issue_type': safe_get(fields, ['issuetype', 'name'], 'Unknown'),
            'priority': safe_get(fields, ['priority', 'name'], 'Unknown'),
            'project': safe_get(fields, ['project', 'key'], 'Unknown'),
            'created': safe_get(fields, ['created'], ''),
            'updated': safe_get(fields, ['updated'], ''),
            'labels': ', '.join(safe_get(fields, ['labels'], []))
        }

class JiraGetIssuesInput(BaseModel):
    """Input for Jira get issues tool"""
    project_key: Optional[str] = Field(
        description="Optional project key to filter issues (e.g., 'PROJ', 'DEV'). Leave empty or set to None to get issues from default project or all projects.",
        default=None
    )
    limit: int = Field(
        description="Maximum number of issues to retrieve",
        default=50
    )

class JiraGetIssuesTool(BaseTool):
    """A tool to get Jira issues with optional project filtering"""
    
    name: str = "jira_get_issues"
    description: str = """Get Jira issues from projects with optional project filtering. Usage:
    - To get issues from default project: call with no parameters
    - To get issues from specific project: set project_key to the project code (e.g., 'PROJ')
    - To limit results: set limit parameter (default 50)
    
    Examples:
    - jira_get_issues() -> gets issues from default project or all accessible projects
    - jira_get_issues(project_key='PROJ') -> gets issues from PROJ project
    - jira_get_issues(limit=10) -> gets 10 issues from default project"""
    args_schema: Type[BaseModel] = JiraGetIssuesInput
    
    def _run(self, project_key: Optional[str] = None, limit: int = 50) -> str:
        """Execute the Jira get issues tool"""
        logger.info(f"Jira tool called with project_key: {project_key}, limit: {limit}")
        
        # Validate and sanitize project_key input
        # Handle cases where LLM passes descriptive text instead of actual project key
        if project_key and (
            project_key.lower() == 'none' or  # Handle when LLM passes 'None' as string
            project_key.lower() == 'null' or  # Handle when LLM passes 'null' as string
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
            issues = jira_client.fetch_issues(
                jql_query="ORDER BY created DESC",
                max_results=limit,
                project_key=project_key
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
                issue_line += f" (Status: {issue['status']}, Assignee: {issue['assignee']}"
                if issue['project'] != "Unknown":
                    issue_line += f", Project: {issue['project']}"
                if issue['priority'] != "Unknown":
                    issue_line += f", Priority: {issue['priority']}"
                issue_line += ")"
                result_lines.append(issue_line)
            
            # Add configuration note
            result_lines.append("")
            result_lines.append(f"✅ Connected to Jira: {jira_client.server_url}")
            
            result = "\n".join(result_lines)
            logger.info(f"Successfully retrieved {len(issues)} issues")
            return result
            
        except Exception as e:
            error_msg = f"Error retrieving Jira issues: {str(e)}"
            logger.error(error_msg)
            return error_msg

class JiraListProjectsInput(BaseModel):
    """Input for Jira list projects tool"""
    pass

class JiraListProjectsTool(BaseTool):
    """A tool to list all available Jira projects"""
    
    name: str = "jira_list_projects"
    description: str = "List all available Jira projects that you have access to. Use this when you need to know what project keys are available."
    args_schema: Type[BaseModel] = JiraListProjectsInput
    
    def _run(self) -> str:
        """Execute the Jira list projects tool"""
        logger.info("Jira list projects tool called")
        
        # Create Jira client instance
        jira_client = JiraClient()
        
        try:
            # Get projects from Jira
            projects = jira_client.get_projects()
            
            if not projects:
                return "No projects found or unable to retrieve projects list. This could be due to permissions."
            
            # Format response
            result_lines = [f"Found {len(projects)} accessible Jira projects:", ""]
            
            for project in projects:
                result_lines.append(f"• {project['key']}: {project['name']}")
            
            # Add configuration note
            result_lines.append("")
            result_lines.append(f"✅ Connected to Jira: {jira_client.server_url}")
            
            result = "\n".join(result_lines)
            logger.info(f"Successfully retrieved {len(projects)} projects")
            return result
            
        except Exception as e:
            error_msg = f"Error retrieving Jira projects: {str(e)}"
            logger.error(error_msg)
            return error_msg
