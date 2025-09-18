#!/usr/bin/env python3
"""
Web application that integrates with the official AWS Cost Explorer MCP server
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="AWS Cost Explorer - Management Dashboard", version="3.0.0")

# Mount static files and templates (only if directories exist)
import os
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

class MCPQuery(BaseModel):
    query: str
    tool_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class OfficialMCPClient:
    def __init__(self):
        self.mcp_process = None
        self.tools = []
    
    async def start_mcp_server(self):
        """Start the official AWS Cost Explorer MCP server process"""
        try:
            # Add uvx to PATH
            env = {
                **{k: v for k, v in os.environ.items() if not k.startswith('AWS_PROFILE')},  # Remove any AWS_PROFILE
                "PATH": f"{os.environ.get('HOME', '')}/.local/bin:{os.environ.get('PATH', '')}",
                "AWS_REGION": os.environ.get('AWS_REGION', 'us-east-1')
            }
            
            # Try using uvx to run the official MCP server
            self.mcp_process = subprocess.Popen(
                ["uvx", "awslabs.cost-explorer-mcp-server@latest"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env
            )
            await asyncio.sleep(5)  # Give it more time to start not sure if this is needed
            await self.load_tools()
            return True
        except Exception as e:
            print(f"Failed to start official MCP server with uvx: {e}")
            return False
    
    async def initialize_mcp_session(self):
        """Initialize MCP session with proper handshake"""
        try:
            # Step 1: Send initialize request
            initialize_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "clientInfo": {
                        "name": "cost-explorer-web-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            print(f"Sending initialize request: {json.dumps(initialize_request)}")
            self.mcp_process.stdin.write(json.dumps(initialize_request) + "\n")
            self.mcp_process.stdin.flush()
            
            response_line = self.mcp_process.stdout.readline()
            print(f"Initialize response: {response_line.strip()}")
            response = json.loads(response_line.strip())
            
            if "result" not in response:
                print(f"Initialize failed: {response}")
                return False
            
            # Step 2: Send initialized notification
            initialized_notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized"
            }
            
            print(f"Sending initialized notification: {json.dumps(initialized_notification)}")
            self.mcp_process.stdin.write(json.dumps(initialized_notification) + "\n")
            self.mcp_process.stdin.flush()
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize MCP session: {e}")
            return False

    async def load_tools(self):
        """Load available tools from the official MCP server"""
        try:
            # First initialize the MCP session
            if not await self.initialize_mcp_session():
                return False
            
            # Now request tools list
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list"
            }
            
            print(f"Sending tools/list request: {json.dumps(request)}")
            self.mcp_process.stdin.write(json.dumps(request) + "\n")
            self.mcp_process.stdin.flush()
            
            response_line = self.mcp_process.stdout.readline()
            print(f"Tools list response: {response_line.strip()}")
            response = json.loads(response_line.strip())
            
            if "result" in response:
                self.tools = response["result"]["tools"]
                print(f"Loaded {len(self.tools)} tools: {[tool.get('name', 'unnamed') for tool in self.tools]}")
                return True
            else:
                print(f"No result in tools/list response: {response}")
                return False
        except Exception as e:
            print(f"Failed to load tools: {e}")
            return False
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Call a specific MCP tool"""
        try:
            if not self.mcp_process:
                await self.start_mcp_server()
            
            request = {
                "jsonrpc": "2.0",
                "id": 3,  # Use ID 3 since 1 and 2 are used in initialization
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": parameters or {}
                }
            }
            
            print(f"Calling tool '{tool_name}' with request: {json.dumps(request)}")
            self.mcp_process.stdin.write(json.dumps(request) + "\n")
            self.mcp_process.stdin.flush()
            
            response_line = self.mcp_process.stdout.readline()
            print(f"Tool call response: {response_line.strip()}")
            response = json.loads(response_line.strip())
            
            if "result" in response:
                # Handle different response formats
                if "content" in response["result"]:
                    content = response["result"]["content"][0]["text"]
                    try:
                        parsed_content = json.loads(content)
                        # Handle potential JSON serialization issues with float values
                        return self._sanitize_json_response(parsed_content)
                    except json.JSONDecodeError as e:
                        return {"success": False, "error": f"Failed to parse MCP response: {str(e)}"}
                else:
                    return self._sanitize_json_response(response["result"])
            else:
                return {"success": False, "error": response.get("error", "Unknown error")}
                
        except BrokenPipeError:
            print(f"MCP server connection lost while calling tool '{tool_name}'")
            return {"success": False, "error": "MCP server connection lost. Please try again."}
        except Exception as e:
            print(f"Error calling tool '{tool_name}': {e}")
            return {"success": False, "error": str(e)}
    
    def _sanitize_json_response(self, data):
        """Sanitize response data to handle JSON serialization issues"""
        import math
        
        def sanitize_value(obj):
            if isinstance(obj, dict):
                return {k: sanitize_value(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_value(item) for item in obj]
            elif isinstance(obj, float):
                if math.isnan(obj) or math.isinf(obj):
                    return None  # Convert NaN and Infinity to None
                return obj
            else:
                return obj
        
        return sanitize_value(data)
    
    def _parse_comparison_dates(self, query: str) -> Dict[str, Dict[str, str]]:
        """Parse comparison dates from natural language query"""
        import re
        from calendar import monthrange
        
        # Month name to number mapping
        months = {
            'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
            'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
            'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
            'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
        }
        
        current_year = datetime.now().year
        
        # Extract months from query, this is kinda janky but it works
        found_months = []
        for month_name, month_num in months.items():
            if month_name in query.lower():
                found_months.append(month_num)
        
        # Remove duplicates and sort
        found_months = sorted(list(set(found_months)))
        
        if len(found_months) >= 2:
            # Use the first two months found, again kinda janky but it works
            baseline_month = found_months[0]
            comparison_month = found_months[1]
        else:
            # Fallback to previous completed months
            current_month = datetime.now().month
            if current_month >= 3:  # We need at least 2 complete months before current
                baseline_month = current_month - 2
                comparison_month = current_month - 1
            else:
                # Use last year's months
                # This should be updated
                baseline_month = 11  # November
                comparison_month = 12  # December
                current_year = current_year - 1
        
        # Ensure we don't use the current incomplete month
        current_month = datetime.now().month
        if comparison_month >= current_month:
            # Adjust to use complete months only
            # Need to update this in case a user wants to use the current month
            baseline_month = current_month - 2 if current_month >= 3 else 11
            comparison_month = current_month - 1 if current_month >= 2 else 12
            if baseline_month >= current_month or comparison_month >= current_month:
                current_year = current_year - 1
        
        # Generate date ranges
        baseline_start = f"{current_year}-{baseline_month:02d}-01"
        baseline_end = f"{current_year}-{comparison_month:02d}-01"
        
        comparison_start = f"{current_year}-{comparison_month:02d}-01"
        if comparison_month == 12:
            comparison_end = f"{current_year + 1}-01-01"
        else:
            comparison_end = f"{current_year}-{comparison_month + 1:02d}-01"
        
        return {
            "baseline": {"start_date": baseline_start, "end_date": baseline_end},
            "comparison": {"start_date": comparison_start, "end_date": comparison_end}
        }
    
    def _parse_date_range_and_granularity(self, query: str) -> Dict[str, Any]:
        """Parse date range and granularity from natural language query"""
        query_lower = query.lower()
        now = datetime.now()
        
        # Default values
        granularity = "MONTHLY"
        group_by = "SERVICE"
        
        # Parse time periods
        # There's probably a better way to do this
        if "this year" in query_lower or "year" in query_lower:
            start_date = datetime(now.year, 1, 1).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            if "monthly" in query_lower or "month" in query_lower:
                granularity = "MONTHLY"
        elif "last 6 months" in query_lower or "6 months" in query_lower:
            start_date = (now - timedelta(days=180)).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            granularity = "MONTHLY"
        elif "last 3 months" in query_lower or "3 months" in query_lower:
            start_date = (now - timedelta(days=90)).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            granularity = "MONTHLY"
        elif "last 30 days" in query_lower or "30 days" in query_lower:
            start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            granularity = "DAILY"
        elif "daily" in query_lower or "day" in query_lower:
            start_date = (now - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            granularity = "DAILY"
        else:
            # Default: last 3 months
            # TODO: Probably don't want to use a default
            start_date = (now - timedelta(days=90)).strftime('%Y-%m-%d')
            end_date = now.strftime('%Y-%m-%d')
            granularity = "MONTHLY"
        
        # Parse visualization hints
        # TODO: Look into NLP MCP or other tools to generate charts on the fly
        # Also, after conversation with Joey it might be worth it to update this
        # completely to allow the user to specify the chart type
        chart_type = "default"
        if "sparkline" in query_lower or "spark line" in query_lower:
            chart_type = "sparkline"
        elif "timeline" in query_lower or "time series" in query_lower:
            chart_type = "timeline"
        elif "bar chart" in query_lower or "bar graph" in query_lower:
            chart_type = "bar"
        elif "line chart" in query_lower or "line graph" in query_lower:
            chart_type = "line"
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "granularity": granularity,
            "group_by": group_by,
            "chart_type": chart_type
        }
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query to determine appropriate response"""
        query_lower = query.lower().strip()
        
        # Meta/informational questions
        # TODO: Look into NLP MCP or other tools to classify queries
        meta_keywords = [
            'which account', 'what account', 'aws account', 'account information',
            'what region', 'which region', 'where is this data',
            'how does this work', 'what is this', 'help',
            'what tools', 'what can you do', 'capabilities'
        ]
        
        for keyword in meta_keywords:
            if keyword in query_lower:
                return 'meta'
        
        # Cost analysis questions
        cost_keywords = [
            'cost', 'costs', 'spending', 'charges', 'bill', 'expense',
            'forecast', 'predict', 'budget', 'usage', 'service',
            'sparkline', 'chart', 'graph', 'timeline', 'bar'
        ]
        
        for keyword in cost_keywords:
            if keyword in query_lower:
                return 'cost_analysis'
        
        # Default to informational for short queries without clear intent
        if len(query_lower.split()) <= 3:
            return 'meta'
            
        # Default to cost analysis for longer queries
        return 'cost_analysis'

    async def execute_management_query(self, query: str) -> Dict[str, Any]:
        """Execute a management query using the official MCP server"""
        # Check if MCP server is available
        if not self.mcp_process:
            return {
                "success": False,
                "error": "Official MCP server is not available. Please ensure the AWS Cost Explorer MCP server is running."
            }
        
        # Handle meta/informational queries first
        query_lower = query.lower()
        
        # Direct meta query detection
        if any(keyword in query_lower for keyword in [
            'which account', 'what account', 'aws account', 'account information',
            'what region', 'which region', 'where is this data',
            'help', 'what can you do', 'capabilities', 'what tools'
        ]):
            return await self._handle_meta_query(query)
        
        # For short queries without clear intent, treat as meta
        if len(query_lower.split()) <= 3 and not any(keyword in query_lower for keyword in [
            'cost', 'costs', 'spending', 'charges', 'bill', 'expense',
            'forecast', 'predict', 'budget', 'usage', 'service'
        ]):
            return await self._handle_meta_query(query)
        
        # Map natural language queries to specific tools
        
        if "forecast" in query_lower or "predict" in query_lower:
            end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            result = await self.call_tool("get_cost_forecast", {
                "date_range": {
                    "start_date": datetime.now().strftime('%Y-%m-%d'),
                    "end_date": end_date
                },
                "granularity": "MONTHLY",
                "metric": "UNBLENDED_COST"
            })
            # Add chart type hint
            if isinstance(result, dict):
                result["_chart_type"] = "forecast"
            return result
            
        elif "compare" in query_lower or "comparison" in query_lower:
            # Parse specific months from the query
            dates = self._parse_comparison_dates(query_lower)
            
            result = await self.call_tool("get_cost_and_usage_comparisons", {
                "baseline_date_range": dates["baseline"],
                "comparison_date_range": dates["comparison"],
                "metric_for_comparison": "UnblendedCost",
                "group_by": "SERVICE"
            })
            # Add chart type hint
            if isinstance(result, dict):
                result["_chart_type"] = "comparison"
            return result
        else:
            # Parse the query for date range and visualization preferences
            parsed = self._parse_date_range_and_granularity(query)
            
            result = await self.call_tool("get_cost_and_usage", {
                "date_range": {
                    "start_date": parsed["start_date"],
                    "end_date": parsed["end_date"]
                },
                "granularity": parsed["granularity"],
                "group_by": parsed["group_by"],
                "metric": "UnblendedCost"
            })
            
            # Add chart type hint to the result
            if isinstance(result, dict):
                result["_chart_type"] = parsed["chart_type"]
                result["_granularity"] = parsed["granularity"]
            
            return result
    
    async def _handle_meta_query(self, query: str) -> Dict[str, Any]:
        """Handle meta/informational queries about the system"""
        query_lower = query.lower()
        
        # AWS Account information WITHOUT using the MCP server
        if any(keyword in query_lower for keyword in ['account', 'which account', 'what account']):
            try:
                # Try to get account info from STS
                import boto3
                sts = boto3.client('sts')
                account_info = sts.get_caller_identity()
                
                return {
                    "success": True,
                    "data": {
                        "type": "account_info",
                        "account_id": account_info.get('Account', 'Unknown'),
                        "user_arn": account_info.get('Arn', 'Unknown'),
                        "user_id": account_info.get('UserId', 'Unknown'),
                        "region": boto3.Session().region_name or 'us-east-1',
                        "message": f"This dashboard is connected to AWS Account: {account_info.get('Account', 'Unknown')}"
                    }
                }
            except Exception as e:
                return {
                    "success": True,
                    "data": {
                        "type": "account_info",
                        "message": f"Could not retrieve account information. Error: {str(e)}",
                        "note": "Make sure your AWS credentials are properly configured."
                    }
                }
        
        # Region information
        elif any(keyword in query_lower for keyword in ['region', 'where is this']):
            try:
                import boto3
                region = boto3.Session().region_name or 'us-east-1'
                return {
                    "success": True,
                    "data": {
                        "type": "region_info", 
                        "region": region,
                        "message": f"This dashboard is retrieving data from AWS region: {region}"
                    }
                }
            except Exception as e:
                return {
                    "success": True,
                    "data": {
                        "type": "region_info",
                        "message": "Could not determine AWS region",
                        "note": str(e)
                    }
                }
        
        # Tool capabilities
        elif any(keyword in query_lower for keyword in ['what can you do', 'capabilities', 'help', 'what tools']):
            return {
                "success": True,
                "data": {
                    "type": "capabilities",
                    "message": "AWS Cost Explorer Dashboard Capabilities",
                    "features": [
                        "📊 Cost Analysis: View costs grouped by service, region, or time period",
                        "📈 Visualizations: Sparklines, timelines, bar charts, and pie charts",
                        "🔮 Cost Forecasting: Predict future AWS spending",
                        "📋 Cost Comparisons: Compare costs between different time periods",
                        "💰 Usage Reports: Daily, monthly, or custom date range analysis",
                        "🎯 Smart Queries: Natural language questions about your AWS costs"
                    ],
                    "example_queries": [
                        "Show me my AWS costs for the last 3 months",
                        "Give me a sparkline of monthly charges this year",
                        "Compare October vs November costs",
                        "What will my costs be next month?",
                        "Create a timeline of daily costs for the last 30 days"
                    ]
                }
            }
        
        # Default meta response
        else:
            return {
                "success": True,
                "data": {
                    "type": "general_info",
                    "message": "AWS Cost Explorer Official MCP Dashboard",
                    "description": "This dashboard provides AWS cost analysis and visualization using the official AWS Cost Explorer MCP server.",
                    "note": "Ask me about your AWS costs, account information, or what I can do to help!"
                }
            }
    

# Global MCP client
mcp_client = OfficialMCPClient()

@app.on_event("startup")
async def startup_event():
    """Initialize official MCP server on startup"""
    success = await mcp_client.start_mcp_server()
    if not success:
        print("WARNING: Failed to start official MCP server. Cost analysis queries will fail.")
        print("Please ensure 'uvx' is installed and AWS credentials are configured.")
    else:
        print("Official AWS Cost Explorer MCP server started successfully!")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("official_mcp_dashboard.html", {
        "request": request,
        "tools": mcp_client.tools
    })

@app.post("/api/mcp-query")
async def execute_mcp_query(query: MCPQuery):
    """Execute an MCP query"""
    try:
        if query.tool_name:
            # Direct tool call
            result = await mcp_client.call_tool(query.tool_name, query.parameters)
        else:
            # Management query
            result = await mcp_client.execute_management_query(query.query)
        
        return {
            "success": result.get("success", True),
            "data": result.get("data", result),
            "error": result.get("error"),
            "query": query.query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")

@app.get("/api/tools")
async def get_available_tools():
    """Get list of available MCP tools"""
    return {"tools": mcp_client.tools}

@app.post("/api/management-query")
async def execute_management_query(query: MCPQuery):
    """Execute a broad management query"""
    try:
        result = await mcp_client.execute_management_query(query.query)
        return {
            "success": result.get("success", True),
            "data": result.get("data", result),
            "error": result.get("error"),
            "query": query.query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing management query: {str(e)}")

@app.post("/api/cost-analysis")
async def get_cost_analysis():
    """Get comprehensive cost analysis using official MCP tools"""
    try:
        # Get cost data for last 30 days
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Get cost and usage
        cost_data = await mcp_client.call_tool("get_cost_and_usage", {
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "granularity": "DAILY",
            "metric": "UnblendedCost"
        })
        
        # Get cost forecast
        forecast_end = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        forecast = await mcp_client.call_tool("get_cost_forecast", {
            "date_range": {
                "start_date": datetime.now().strftime('%Y-%m-%d'),
                "end_date": forecast_end
            },
            "granularity": "MONTHLY",
            "metric": "UNBLENDED_COST"
        })
        
        return {
            "success": True,
            "data": {
                "cost_data": cost_data,
                "forecast": forecast
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cost analysis: {str(e)}")

if __name__ == "__main__":
    import os
    uvicorn.run(app, host="0.0.0.0", port=8002)
