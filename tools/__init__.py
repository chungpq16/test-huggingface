import logging
import json
import pandas as pd
from datetime import datetime
from typing import Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Import the JiraClient
try:
    from jira_client import JiraClient
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False
    logger.warning("jira_client not available, using mock data")

logger = logging.getLogger(__name__)

class HelloToolInput(BaseModel):
    """Input for hello tool"""
    name: str = Field(description="Name to greet", default="World")

class HelloTool(BaseTool):
    """A simple hello tool that greets users"""
    
    name: str = "hello_tool"
    description: str = "A simple greeting tool that says hello to someone. Use this when user asks for greetings or wants to say hello."
    args_schema: Type[BaseModel] = HelloToolInput
    
    def _run(self, name: str = "World") -> str:
        """Execute the hello tool"""
        logger.info(f"Hello tool called with name: {name}")
        result = f"Hello, {name}! Nice to meet you! 👋"
        logger.debug(f"Hello tool result: {result}")
        return result

class CalculatorToolInput(BaseModel):
    """Input for calculator tool"""
    expression: str = Field(description="Mathematical expression to calculate (e.g., '2+2', '10*5', '100/4')")

class CalculatorTool(BaseTool):
    """A simple calculator tool that evaluates mathematical expressions"""
    
    name: str = "calculator_tool"
    description: str = "A calculator tool that can perform basic mathematical operations. Use this when user asks for calculations or mathematical operations."
    args_schema: Type[BaseModel] = CalculatorToolInput
    
    def _run(self, expression: str) -> str:
        """Execute the calculator tool"""
        logger.info(f"Calculator tool called with expression: {expression}")
        
        try:
            # Simple safety check - only allow basic mathematical operations
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                logger.warning(f"Invalid characters in expression: {expression}")
                return "Error: Expression contains invalid characters. Only numbers and basic operators (+, -, *, /, parentheses) are allowed."
            
            # Evaluate the expression
            result = eval(expression)
            logger.info(f"Calculator result: {expression} = {result}")
            return f"{expression} = {result}"
            
        except ZeroDivisionError:
            logger.error(f"Division by zero in expression: {expression}")
            return "Error: Division by zero is not allowed."
            
        except Exception as e:
            logger.error(f"Error evaluating expression '{expression}': {e}")
            return f"Error: Could not evaluate the expression '{expression}'. Please check your syntax."

# Jira Tools Implementation

class GetAllJiraIssuesInput(BaseModel):
    """Input for get all jira issues tool"""
    limit: int = Field(description="Maximum number of issues to retrieve", default=50)

class GetAllJiraIssuesTool(BaseTool):
    """Tool to get all Jira issues"""
    
    name: str = "get_all_jira_issues"
    description: str = "Get all Jira issues. Use this for general queries about all issues or when counting total issues without filters."
    args_schema: Type[BaseModel] = GetAllJiraIssuesInput
    
    def __init__(self):
        super().__init__()
        if JIRA_AVAILABLE:
            self.jira_client = JiraClient()
        else:
            self.jira_client = None
    
    def _run(self, limit: int = 50) -> str:
        """Execute the get all issues tool"""
        logger.info(f"Get all issues tool called with limit: {limit}")
        
        try:
            if self.jira_client:
                issues = self.jira_client.fetch_issues(
                    jql_query="ORDER BY created DESC",
                    max_results=limit
                )
            else:
                # Mock data when Jira is not available
                issues = self._get_mock_data()[:limit]
            
            result = {
                "success": True,
                "count": len(issues),
                "message": f"Found {len(issues)} issues total",
                "issues": [f"{issue['key']}: {issue['summary']} (Status: {issue['status']}, Assignee: {issue['assignee']})" for issue in issues]
            }
            
            logger.info(f"Successfully retrieved {len(issues)} issues")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting all issues: {e}")
            return json.dumps({"error": f"Failed to fetch issues: {str(e)}"})
    
    def _get_mock_data(self) -> list:
        """Mock data when Jira client is not available"""
        return [
            {
                'key': 'PROJ-001',
                'summary': 'Implement user authentication system',
                'description': 'Add OAuth2 authentication system for secure user login',
                'status': 'In Progress',
                'assignee': 'john.doe',
                'reporter': 'jane.smith',
                'issue_type': 'Task',
                'priority': 'High',
                'created': '2025-08-20T10:00:00Z',
                'updated': '2025-08-20T15:30:00Z',
                'labels': 'feature, security'
            },
            {
                'key': 'PROJ-002',
                'summary': 'Fix critical login bug',
                'description': 'Users cannot login with special characters in password',
                'status': 'Done',
                'assignee': 'alice.brown',
                'reporter': 'bob.wilson',
                'issue_type': 'Bug',
                'priority': 'Critical',
                'created': '2025-08-19T14:30:00Z',
                'updated': '2025-08-19T16:45:00Z',
                'labels': 'bug, urgent'
            },
            {
                'key': 'PROJ-003',
                'summary': 'Update API documentation',
                'description': 'Update API documentation for v2.0 release',
                'status': 'To Do',
                'assignee': 'Unassigned',
                'reporter': 'charlie.davis',
                'issue_type': 'Story',
                'priority': 'Low',
                'created': '2025-08-18T09:15:00Z',
                'updated': '2025-08-18T09:15:00Z',
                'labels': 'documentation'
            }
        ]

class GetJiraIssueDetailInput(BaseModel):
    """Input for get jira issue detail tool"""
    issue_key: str = Field(description="The Jira issue key (e.g., 'PROJ-123', 'DEMO-001')")

class GetJiraIssueDetailTool(BaseTool):
    """Tool to get detailed information for a specific Jira issue"""
    
    name: str = "get_jira_issue_detail"
    description: str = "Get detailed information for a specific Jira issue by its key/ID."
    args_schema: Type[BaseModel] = GetJiraIssueDetailInput
    
    def __init__(self):
        super().__init__()
        if JIRA_AVAILABLE:
            self.jira_client = JiraClient()
        else:
            self.jira_client = None
    
    def _run(self, issue_key: str) -> str:
        """Execute the get issue detail tool"""
        logger.info(f"Get issue detail tool called with key: {issue_key}")
        
        try:
            if self.jira_client:
                issue = self.jira_client.get_issue_detail(issue_key)
            else:
                # Mock data lookup
                mock_data = GetAllJiraIssuesTool()._get_mock_data()
                issue = next((item for item in mock_data if item['key'] == issue_key), None)
            
            if not issue:
                result = {"error": f"Issue {issue_key} not found"}
                return json.dumps(result)
            
            result = {
                "success": True,
                "issue": issue,
                "message": f"Retrieved details for {issue_key}"
            }
            
            logger.info(f"Successfully retrieved details for {issue_key}")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting issue detail: {e}")
            return json.dumps({"error": f"Failed to get issue detail: {str(e)}"})

class GetJiraIssuesByFilterInput(BaseModel):
    """Input for get jira issues by filter tool"""
    status: Optional[str] = Field(description="Filter by status (e.g., 'In Progress', 'Done', 'To Do')", default=None)
    assignee: Optional[str] = Field(description="Filter by assignee name", default=None)
    labels: Optional[str] = Field(description="Filter by label (e.g., 'bug', 'feature', 'urgent')", default=None)
    priority: Optional[str] = Field(description="Filter by priority (e.g., 'High', 'Medium', 'Low')", default=None)
    topic: Optional[str] = Field(description="Search for issues containing this topic in summary or description", default=None)
    limit: int = Field(description="Maximum number of issues to retrieve", default=50)

class GetJiraIssuesByFilterTool(BaseTool):
    """Tool to get Jira issues filtered by various criteria"""
    
    name: str = "get_jira_issues_by_filter"
    description: str = "Get Jira issues filtered by status, assignee, labels, priority, or topic. Use this for specific filtered searches."
    args_schema: Type[BaseModel] = GetJiraIssuesByFilterInput
    
    def __init__(self):
        super().__init__()
        if JIRA_AVAILABLE:
            self.jira_client = JiraClient()
        else:
            self.jira_client = None
    
    def _run(self, status: str = None, assignee: str = None, labels: str = None, 
             priority: str = None, topic: str = None, limit: int = 50) -> str:
        """Execute the filter issues tool"""
        logger.info(f"Filter issues tool called with filters: status={status}, assignee={assignee}, labels={labels}, priority={priority}, topic={topic}")
        
        try:
            if self.jira_client:
                # Build JQL query
                jql_parts = []
                
                if status:
                    jql_parts.append(f"status = '{status}'")
                if assignee:
                    jql_parts.append(f"assignee = '{assignee}'")
                if labels:
                    jql_parts.append(f"labels = '{labels}'")
                if priority:
                    jql_parts.append(f"priority = '{priority}'")
                if topic:
                    jql_parts.append(f"(summary ~ '{topic}' OR description ~ '{topic}')")
                
                jql_query = " AND ".join(jql_parts) if jql_parts else ""
                jql_query += " ORDER BY created DESC"
                
                issues = self.jira_client.fetch_issues(jql_query, limit)
            else:
                # Mock filtering
                issues = self._filter_mock_data(status, assignee, labels, priority, topic, limit)
            
            # Create filter description
            filters = []
            if status: filters.append(f"status: {status}")
            if assignee: filters.append(f"assignee: {assignee}")
            if labels: filters.append(f"labels: {labels}")
            if priority: filters.append(f"priority: {priority}")
            if topic: filters.append(f"topic: {topic}")
            
            filter_desc = ", ".join(filters) if filters else "no filters"
            
            # Provide suggestions if no results
            suggestion = ""
            if len(issues) == 0:
                suggestion = self._get_filter_suggestions()
            
            result = {
                "success": True,
                "count": len(issues),
                "filters_applied": filter_desc,
                "message": f"Found {len(issues)} issues with filters: {filter_desc}",
                "suggestion": suggestion,
                "issues": [f"{issue['key']}: {issue['summary']} (Status: {issue['status']}, Assignee: {issue['assignee']})" for issue in issues]
            }
            
            logger.info(f"Successfully filtered {len(issues)} issues")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error filtering issues: {e}")
            return json.dumps({"error": f"Failed to filter issues: {str(e)}"})
    
    def _filter_mock_data(self, status, assignee, labels, priority, topic, limit):
        """Filter mock data based on criteria"""
        mock_data = GetAllJiraIssuesTool()._get_mock_data()
        filtered = mock_data.copy()
        
        if status:
            filtered = [issue for issue in filtered if issue['status'].lower() == status.lower()]
        if assignee:
            filtered = [issue for issue in filtered if assignee.lower() in issue['assignee'].lower()]
        if labels:
            filtered = [issue for issue in filtered if labels.lower() in issue['labels'].lower()]
        if priority:
            filtered = [issue for issue in filtered if issue['priority'].lower() == priority.lower()]
        if topic:
            filtered = [issue for issue in filtered 
                       if topic.lower() in issue['summary'].lower() or topic.lower() in issue['description'].lower()]
        
        return filtered[:limit]
    
    def _get_filter_suggestions(self) -> str:
        """Provide suggestions when no results found"""
        return "Available statuses: In Progress, Done, To Do | Available assignees: john.doe, alice.brown | Available labels: feature, security, bug, urgent, documentation"

class GetAnalyticalDashboardDataInput(BaseModel):
    """Input for get analytical dashboard data tool"""
    pass  # No parameters needed

class GetAnalyticalDashboardDataTool(BaseTool):
    """Tool to get comprehensive analytics and dashboard data"""
    
    name: str = "get_analytical_dashboard_data"
    description: str = "Get comprehensive analytics and dashboard data including metrics, charts, and insights about Jira issues."
    args_schema: Type[BaseModel] = GetAnalyticalDashboardDataInput
    
    def __init__(self):
        super().__init__()
        if JIRA_AVAILABLE:
            self.jira_client = JiraClient()
        else:
            self.jira_client = None
    
    def _run(self) -> str:
        """Execute the analytics dashboard tool"""
        logger.info("Analytics dashboard tool called")
        
        try:
            if self.jira_client:
                # Get all issues for analysis
                all_issues = self.jira_client.fetch_issues("ORDER BY created DESC", 200)
            else:
                # Use mock data
                all_issues = GetAllJiraIssuesTool()._get_mock_data()
            
            if not all_issues:
                return json.dumps({"error": "No issues found for analysis"})
            
            df = pd.DataFrame(all_issues)
            
            # Calculate metrics
            analytics = {
                "overview_metrics": {
                    "total_issues": len(df),
                    "in_progress": len(df[df['status'].str.contains('In Progress|Progress', case=False, na=False)]),
                    "completed": len(df[df['status'].str.contains('Done|Closed|Resolved', case=False, na=False)]),
                    "with_labels": len(df[df['labels'].str.strip() != ''])
                },
                "status_distribution": df['status'].value_counts().to_dict(),
                "assignee_distribution": df['assignee'].value_counts().head(10).to_dict(),
                "label_distribution": self._analyze_labels(df),
                "recent_issues": df.head(5)[['key', 'summary', 'status', 'assignee', 'created']].to_dict('records')
            }
            
            result = {
                "success": True,
                "analytics": analytics,
                "message": "Dashboard data generated successfully"
            }
            
            logger.info("Successfully generated analytics dashboard")
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating dashboard: {e}")
            return json.dumps({"error": f"Failed to generate dashboard: {str(e)}"})
    
    def _analyze_labels(self, df: pd.DataFrame) -> dict:
        """Analyze labels distribution"""
        all_labels = []
        for labels_str in df['labels'].dropna():
            if labels_str and labels_str.strip():
                labels = [label.strip() for label in labels_str.split(',')]
                all_labels.extend(labels)
        
        if not all_labels:
            return {}
        
        label_counts = pd.Series(all_labels).value_counts().head(10)
        return label_counts.to_dict()

# Export the tools
def get_available_tools():
    """Get list of available tools"""
    tools = [
        HelloTool(),
        CalculatorTool(),
        GetAllJiraIssuesTool(),
        GetJiraIssueDetailTool(),
        GetJiraIssuesByFilterTool(),
        GetAnalyticalDashboardDataTool()
    ]
    logger.info(f"Available tools: {[tool.name for tool in tools]}")
    return tools
