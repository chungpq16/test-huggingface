#!/usr/bin/env python3
"""
Simplified Jira Tools for LLM Function Calling
Core tools without unused complexity
"""

import json
import pandas as pd
from datetime import datetime
import streamlit as st
from jira_client import JiraClient

class JiraTools:
    """Simplified tools for LLM function calling"""
    
    def __init__(self):
        self.jira_client = JiraClient()
    
    def call_tool(self, function_name: str, function_args: dict) -> dict:
        """Route tool calls to appropriate methods"""
        tool_methods = {
            'get_all_jira_issues': self.get_all_jira_issues,
            'get_jira_issue_detail': self.get_jira_issue_detail,
            'get_jira_issues_by_filter': self.get_jira_issues_by_filter,
            'get_analytical_dashboard_data': self.get_analytical_dashboard_data
        }
        
        if function_name in tool_methods:
            return tool_methods[function_name](**function_args)
        else:
            return {"error": f"Unknown function: {function_name}"}
    
    def get_all_jira_issues(self, limit: int = 50) -> dict:
        """Get all Jira issues"""
        try:
            issues = self.jira_client.fetch_issues(
                jql_query="ORDER BY created DESC",
                max_results=limit
            )
            
            # Store for display
            table_data = {
                "title": f"All Jira Issues ({len(issues)} total)",
                "subtitle": f"Showing latest {len(issues)} issues",
                "data": issues
            }
            st.session_state.table_to_display = table_data
            
            return {
                "success": True,
                "count": len(issues),
                "message": f"Found {len(issues)} issues total"
            }
            
        except Exception as e:
            return {"error": f"Failed to fetch issues: {str(e)}"}
    
    def get_jira_issue_detail(self, issue_key: str) -> dict:
        """Get detailed information for a specific Jira issue"""
        try:
            issue = self.jira_client.get_issue_detail(issue_key)
            
            if not issue:
                return {"error": f"Issue {issue_key} not found"}
            
            # Store for display
            st.session_state.issue_detail_to_display = {
                "title": f"Issue Details: {issue_key}",
                "data": issue
            }
            
            return {
                "success": True,
                "issue": issue,
                "message": f"Retrieved details for {issue_key}"
            }
            
        except Exception as e:
            return {"error": f"Failed to get issue detail: {str(e)}"}
    
    def get_jira_issues_by_filter(self, status: str = None, assignee: str = None, 
                                 labels: str = None, priority: str = None, 
                                 topic: str = None, limit: int = 50) -> dict:
        """Get Jira issues filtered by various criteria"""
        try:
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
                # Search in summary and description
                jql_parts.append(f"(summary ~ '{topic}' OR description ~ '{topic}')")
            
            jql_query = " AND ".join(jql_parts) if jql_parts else ""
            jql_query += " ORDER BY created DESC"
            
            issues = self.jira_client.fetch_issues(jql_query, limit)
            
            # Create filter description
            filters = []
            if status: filters.append(f"status: {status}")
            if assignee: filters.append(f"assignee: {assignee}")
            if labels: filters.append(f"labels: {labels}")
            if priority: filters.append(f"priority: {priority}")
            if topic: filters.append(f"topic: {topic}")
            
            filter_desc = ", ".join(filters) if filters else "no filters"
            
            # Store for display
            table_data = {
                "title": f"Filtered Jira Issues ({len(issues)} found)",
                "subtitle": f"Filters applied: {filter_desc}",
                "data": issues
            }
            st.session_state.table_to_display = table_data
            
            # Provide suggestions if no results
            suggestion = ""
            if len(issues) == 0:
                suggestion = self._get_filter_suggestions()
            
            return {
                "success": True,
                "count": len(issues),
                "filters_applied": filter_desc,
                "message": f"Found {len(issues)} issues with filters: {filter_desc}",
                "suggestion": suggestion
            }
            
        except Exception as e:
            return {"error": f"Failed to filter issues: {str(e)}"}
    
    def get_analytical_dashboard_data(self) -> dict:
        """Get comprehensive analytics data for dashboard"""
        try:
            # Get all issues for analysis
            all_issues = self.jira_client.fetch_issues("ORDER BY created DESC", 200)
            
            if not all_issues:
                return {"error": "No issues found for analysis"}
            
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
            
            # Store for display
            st.session_state.dashboard_to_display = {
                "title": "Jira Analytics Dashboard",
                "data": analytics
            }
            
            return {
                "success": True,
                "analytics": analytics,
                "message": "Dashboard data generated successfully"
            }
            
        except Exception as e:
            return {"error": f"Failed to generate dashboard: {str(e)}"}
    
    def _analyze_labels(self, df: pd.DataFrame) -> dict:
        """Analyze labels distribution"""
        all_labels = []
        for labels_str in df['labels'].dropna():
            if labels_str.strip():
                labels = [label.strip() for label in labels_str.split(',')]
                all_labels.extend(labels)
        
        label_counts = pd.Series(all_labels).value_counts().head(10)
        return label_counts.to_dict()
    
    def _get_filter_suggestions(self) -> str:
        """Provide suggestions when no results found"""
        try:
            # Get sample of statuses and labels for suggestions
            sample_issues = self.jira_client.fetch_issues("ORDER BY created DESC", 50)
            if not sample_issues:
                return ""
            
            df = pd.DataFrame(sample_issues)
            
            # Get unique values
            statuses = df['status'].unique()[:5]
            assignees = df['assignee'].unique()[:5]
            
            # Extract labels
            all_labels = []
            for labels_str in df['labels'].dropna():
                if labels_str.strip():
                    labels = [label.strip() for label in labels_str.split(',')]
                    all_labels.extend(labels)
            unique_labels = list(set(all_labels))[:5]
            
            suggestion_parts = []
            if len(statuses) > 0:
                suggestion_parts.append(f"Available statuses: {', '.join(statuses)}")
            if len(assignees) > 0:
                suggestion_parts.append(f"Available assignees: {', '.join([a for a in assignees if a != 'Unassigned'])}")
            if len(unique_labels) > 0:
                suggestion_parts.append(f"Available labels: {', '.join(unique_labels)}")
            
            return " | ".join(suggestion_parts)
            
        except Exception:
            return "Try using different filter values"

# Define tools for OpenAI function calling
JIRA_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_all_jira_issues",
            "description": "Get all Jira issues. Use this for general queries about all issues or when counting total issues without filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of issues to retrieve (default: 50)",
                        "default": 50
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_jira_issue_detail",
            "description": "Get detailed information for a specific Jira issue by its key/ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_key": {
                        "type": "string",
                        "description": "The Jira issue key (e.g., 'PROJ-123', 'DEMO-001')"
                    }
                },
                "required": ["issue_key"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_jira_issues_by_filter",
            "description": "Get Jira issues filtered by status, assignee, labels, priority, or topic. Use this for specific filtered searches.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filter by status (e.g., 'In Progress', 'Done', 'To Do')"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Filter by assignee name"
                    },
                    "labels": {
                        "type": "string",
                        "description": "Filter by label (e.g., 'bug', 'feature', 'urgent')"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Filter by priority (e.g., 'High', 'Medium', 'Low')"
                    },
                    "topic": {
                        "type": "string",
                        "description": "Search for issues containing this topic in summary or description"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of issues to retrieve (default: 50)",
                        "default": 50
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_analytical_dashboard_data",
            "description": "Get comprehensive analytics and dashboard data including metrics, charts, and insights about Jira issues.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]
