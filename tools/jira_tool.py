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
            error_str = str(e).lower()
            if "does not exist for the field 'project'" in error_str:
                # Extract the invalid project key from error message
                import re
                match = re.search(r"The value '([^']+)' does not exist for the field 'project'", str(e))
                invalid_project = match.group(1) if match else "unknown"
                
                # Get available projects
                try:
                    available_projects = self.get_projects()
                    if available_projects:
                        project_list = ", ".join([f"{p['key']} ({p['name']})" for p in available_projects[:10]])
                        suggestion = f"Project '{invalid_project}' not found. Available projects: {project_list}"
                    else:
                        suggestion = f"Project '{invalid_project}' not found. No projects returned from API - check permissions."
                except Exception as proj_error:
                    logger.error(f"Error getting projects list: {proj_error}")
                    suggestion = f"Project '{invalid_project}' not found. Unable to retrieve available projects: {str(proj_error)}"
                
                raise Exception(suggestion)
            
            raise e
    
    def _build_jql_with_project(self, jql_query: str, project_key: Optional[str] = None) -> str:
        """Build JQL query with project filtering"""
        # Determine which project to use
        effective_project = project_key or self.default_project
        
        # Build project filter
        project_filter = ""
        if effective_project:
            project_filter = f'project = "{effective_project}"'
        
        # Combine with existing JQL
        if project_filter and jql_query and not jql_query.lower().startswith('order by'):
            final_jql = f"{project_filter} AND ({jql_query})"
        elif project_filter:
            if jql_query.lower().startswith('order by'):
                final_jql = f"{project_filter} {jql_query}"
            else:
                final_jql = f"{project_filter} ORDER BY created DESC"
        else:
            final_jql = jql_query or "ORDER BY created DESC"
        
        return final_jql
    
    def get_projects(self) -> List[Dict]:
        """Get list of available projects"""
        if not self.is_connected:
            raise Exception("Jira client not configured. Please set JIRA_SERVER_URL, JIRA_USERNAME, and JIRA_API_TOKEN in .env file")
        
        try:
            # Try the standard projects() method first
            projects = self.jira.projects()
            if projects:
                return [{"key": p["key"], "name": p["name"]} for p in projects]
            
            # If no projects returned, try an alternative approach using search
            logger.warning("No projects returned from projects() API, trying alternative method...")
            
            # Try to get projects by searching for recent issues and extracting project info
            try:
                result = self.jira.jql(
                    jql="ORDER BY created DESC",
                    limit=100,
                    fields="project"
                )
                
                # Extract unique projects from issues
                projects_dict = {}
                for issue in result.get("issues", []):
                    project_info = issue.get("fields", {}).get("project")
                    if project_info:
                        key = project_info.get("key")
                        name = project_info.get("name", key)
                        if key:
                            projects_dict[key] = {"key": key, "name": name}
                
                projects_list = list(projects_dict.values())
                if projects_list:
                    logger.info(f"Found {len(projects_list)} projects via issue search")
                    return projects_list
                    
            except Exception as search_error:
                logger.error(f"Alternative project search also failed: {search_error}")
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting projects: {str(e)}")
            raise e
    
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
