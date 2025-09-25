#!/usr/bin/env python3
"""
AWS Bedrock Claude query processor for enhanced natural language understanding
"""

import json
from datetime import datetime, timedelta
from typing import Any, Dict

import boto3


class BedrockQueryProcessor:
    def __init__(self, region_name: str = "us-east-1"):
        """Initialize AWS Bedrock client"""
        self.bedrock = boto3.client("bedrock-runtime", region_name=region_name)
        # Available Claude models in Bedrock (using model IDs)
        self.model_ids = {
            "claude-3-5-sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "claude-3-5-haiku": "anthropic.claude-3-5-haiku-20241022-v1:0",
            "claude-3-opus": "anthropic.claude-3-opus-20240229-v1:0",
            "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
            "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
        }
        self.default_model = "claude-3-5-sonnet"

    async def process_query(self, query: str, model: str = None) -> Dict[str, Any]:
        """Process natural language query with AWS Bedrock Claude"""

        model_id = self.model_ids.get(model or self.default_model)

        current_date = datetime.now().strftime("%Y-%m-%d")
        system_prompt = f"""You are an AWS Cost Explorer query processor.

Your job is to analyze natural language queries about AWS costs and return structured JSON responses that specify:
1. Query type (cost_analysis, forecast, comparison, meta)
2. AWS Cost Explorer tool to use
3. Parameters for the tool call
4. Visualization preferences

Available AWS Cost Explorer MCP tools:
- get_cost_and_usage: Get cost data for date ranges
  * Parameters: {{"date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "granularity": "DAILY|MONTHLY", "metric": "NetAmortizedCost", "group_by": "SERVICE"}}
- get_cost_forecast: Predict future costs
  * Parameters: {{"date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "granularity": "MONTHLY", "metric": "NET_AMORTIZED_COST"}}
  * IMPORTANT: start_date must be TODAY or earlier, end_date must be in the FUTURE
  * CRITICAL: Forecast metrics use UNDERSCORE format: NET_AMORTIZED_COST, UNBLENDED_COST, etc.
- get_cost_and_usage_comparisons: Compare two time periods
  * Parameters: {{"baseline_date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "comparison_date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "metric_for_comparison": "NetAmortizedCost"}}
- get_dimension_values: Get available services, regions, etc.
  * Parameters: {{"date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "dimension": {{"dimension_key": "SERVICE|REGION|LINKED_ACCOUNT"}}}}
- get_tag_values: Get available tag values
  * Parameters: {{"date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "tag_key": "tag_name"}}

IMPORTANT: AWS Cost Metrics - Choose the correct metric based on user query:
- "unblended cost/costs" → "UnblendedCost" (or "UNBLENDED_COST" for forecasts)
- "net amortized cost/costs" → "NetAmortizedCost" (or "NET_AMORTIZED_COST" for forecasts) (default)
- "amortized cost/costs" → "AmortizedCost" (or "AMORTIZED_COST" for forecasts)
- "blended cost/costs" → "BlendedCost" (or "BLENDED_COST" for forecasts)
- "net unblended cost/costs" → "NetUnblendedCost" (or "NET_UNBLENDED_COST" for forecasts)
- DEFAULT (no specific metric mentioned) → "NetAmortizedCost" (or "NET_AMORTIZED_COST" for forecasts)
- "usage quantity" → "UsageQuantity"

CRITICAL: For get_cost_forecast tool, use UNDERSCORE format: NET_AMORTIZED_COST, UNBLENDED_COST, etc.

Always return valid JSON with this structure:
{{
    "query_type": "cost_analysis|forecast|comparison|meta",
    "tool_name": "tool_name_here",
    "parameters": {{
        "date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}},
        "granularity": "DAILY|MONTHLY|HOURLY",
        "metric": "NetAmortizedCost|UnblendedCost|AmortizedCost|BlendedCost|NetUnblendedCost|UsageQuantity",
        "group_by": "SERVICE|REGION|etc",
        ...
    }},
    "visualization": {{
        "chart_type": "sparkline|timeline|bar|pie|table",
        "title": "Chart title",
        "description": "Brief explanation"
    }},
    "explanation": "Natural language explanation of what will be done"
}}

Current date context: {current_date}"""

        user_prompt = f"""
Analyze this AWS cost query and return the structured JSON response:

Query: "{query}"

Examples with EXACT parameter formats:

1. Cost Analysis Query:
"Show my EC2 costs last month" →
{{
  "query_type": "cost_analysis",
  "tool_name": "get_cost_and_usage",
  "parameters": {{
    "date_range": {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-DD"}},
    "granularity": "DAILY",
    "metric": "NetAmortizedCost",
    "group_by": "SERVICE"
  }}
}}

2. Comparison Query (NOTE: ONLY use COMPLETE months):
"Why did my AWS bill increase last month?" →
{{
  "query_type": "comparison",
  "tool_name": "get_cost_and_usage_comparisons",
  "parameters": {{
    "baseline_date_range": {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-01"}},
    "comparison_date_range": {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-01"}},
    "metric_for_comparison": "NetAmortizedCost"
  }}
}}

CRITICAL: For {current_date} queries, use COMPLETE months ONLY:
- Compare most recent complete month vs previous complete month
- DO NOT use current incomplete month in comparisons unless specifically asked for

Example for current time ({current_date}):
"What are cost drivers for recent changes?" →
{{
  "query_type": "comparison",
  "tool_name": "get_cost_and_usage_comparisons",
  "parameters": {{
    "baseline_date_range": {{"start_date": "PREVIOUS_MONTH_START", "end_date": "PREVIOUS_MONTH_END"}},
    "comparison_date_range": {{"start_date": "RECENT_MONTH_START", "end_date": "RECENT_MONTH_END"}},
    "metric_for_comparison": "NetAmortizedCost"
  }}
}}

4. Forecast Query (CRITICAL: start_date = TODAY, end_date = FUTURE):
"Forecast my AWS costs for next month" →
{{
  "query_type": "forecast",
  "tool_name": "get_cost_forecast",
  "parameters": {{
    "date_range": {{"start_date": "{current_date}", "end_date": "NEXT_MONTH_END"}},
    "granularity": "MONTHLY",
    "metric": "NET_AMORTIZED_COST"
  }},
  "visualization": {{
    "chart_type": "sparkline",
    "title": "Cost Forecast Sparkline"
  }}
}}

5. Meta Query:
"Which services are available?" →
{{
  "query_type": "meta",
  "tool_name": "get_dimension_values",
  "parameters": {{
    "date_range": {{"start_date": "LAST_MONTH_START", "end_date": "{current_date}"}},
    "dimension": {{"dimension_key": "SERVICE"}}
  }}
}}

CRITICAL FORMAT REQUIREMENTS:
- group_by: Use STRING like "SERVICE", NOT array like ["SERVICE"]
- dimension: Use OBJECT like {{"dimension_key": "SERVICE"}}, NOT string
- Comparisons: MUST have both "baseline_date_range" AND "comparison_date_range"
- AWS DATE REQUIREMENT: end_date MUST be first day of NEXT month, NOT last day of current month
  * WRONG: {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-31"}}
  * CORRECT: {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM+1-01"}}
- COMPLETE MONTHS ONLY: Since today is {current_date}, current month may be INCOMPLETE
  * For comparisons, use: LAST_COMPLETE_MONTH vs PREVIOUS_COMPLETE_MONTH
  * NEVER include incomplete current month in comparisons
- FORECAST DATES: start_date must be TODAY or earlier, end_date must be FUTURE
  * For "forecast next month" on {current_date}, use: start_date="{current_date}", end_date="NEXT_MONTH_END"
  * NEVER set start_date to a future date

Cost Metric Keywords:
- "net amortized" = NetAmortizedCost
- "amortized" = AmortizedCost
- "blended" = BlendedCost
- "net unblended" = NetUnblendedCost
- "unblended" = UnblendedCost
- no metric specified = NetAmortizedCost (default)
"""

        try:
            # Prepare request for Claude via Bedrock
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            }

            response = self.bedrock.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )

            # Parse response
            response_body = json.loads(response["body"].read())
            content = response_body["content"][0]["text"]

            # Extract JSON from Claude's response
            start_idx = content.find("{")
            end_idx = content.rfind("}") + 1
            json_content = content[start_idx:end_idx]

            return json.loads(json_content)

        except Exception as e:
            print(f"Bedrock Claude processing failed: {e}")
            # Fallback to simple processing
            return self._fallback_processing(query)

    async def generate_explanation(
        self, query: str, mcp_result: Dict[str, Any], model: str = None
    ) -> str:
        """Generate natural language explanation of results using Bedrock Claude"""

        model_id = self.model_ids.get(model or self.default_model)

        explanation_prompt = f"""
Generate a clear, concise explanation of these AWS cost analysis results for the user.

Original query: "{query}"

Results: {json.dumps(mcp_result, indent=2)}

Provide:
1. A summary of what the data shows
2. Key insights or notable patterns
3. Any recommendations if appropriate

Keep it conversational and helpful, under 500 words.
"""

        try:
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": explanation_prompt}],
            }

            response = self.bedrock.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )

            response_body = json.loads(response["body"].read())
            return response_body["content"][0]["text"]

        except Exception as e:
            print(f"Bedrock explanation generation failed: {e}")
            return "Analysis complete. Review the data and visualizations above."

    def _fallback_processing(self, query: str) -> Dict[str, Any]:
        """Fallback to simple keyword processing if Bedrock fails"""
        query_lower = query.lower()

        # Detect cost metric
        metric = self._detect_cost_metric(query_lower)

        if "forecast" in query_lower or "predict" in query_lower:
            return {
                "query_type": "forecast",
                "tool_name": "get_cost_forecast",
                "parameters": {
                    "date_range": {
                        "start_date": datetime.now().strftime("%Y-%m-%d"),
                        "end_date": (datetime.now() + timedelta(days=30)).strftime(
                            "%Y-%m-%d"
                        ),
                    },
                    "granularity": "MONTHLY",
                    "metric": "NET_AMORTIZED_COST",  # Forecast API uses different format
                },
                "visualization": {
                    "chart_type": "sparkline",
                    "title": "Cost Forecast Sparkline",
                },
                "explanation": f"Generating {metric.lower()} forecast for next month",
            }
        elif "compare" in query_lower:
            comparison_dates = self._parse_comparison_dates(query_lower)
            return {
                "query_type": "comparison",
                "tool_name": "get_cost_and_usage_comparisons",
                "parameters": {
                    "baseline_date_range": comparison_dates["baseline_date_range"],
                    "comparison_date_range": comparison_dates["comparison_date_range"],
                    "metric_for_comparison": metric,
                },
                "visualization": {"chart_type": "bar", "title": "Cost Comparison"},
                "explanation": f"Comparing {metric.lower()} between time periods",
            }
        else:
            return {
                "query_type": "cost_analysis",
                "tool_name": "get_cost_and_usage",
                "parameters": {
                    "date_range": {
                        "start_date": (datetime.now() - timedelta(days=30)).strftime(
                            "%Y-%m-%d"
                        ),
                        "end_date": datetime.now().strftime("%Y-%m-%d"),
                    },
                    "granularity": "DAILY",
                    "metric": metric,
                    "group_by": "SERVICE",  # String format, not array
                },
                "visualization": {
                    "chart_type": "table",
                    "title": f"{metric.replace('Cost', ' Cost').title()} Analysis",
                },
                "explanation": f"Analyzing {metric.lower().replace('cost', ' costs')} for the last 30 days",
            }

    def _parse_comparison_dates(self, query: str) -> Dict[str, Any]:
        """Parse comparison dates from query - ONLY use complete months"""
        today = datetime.now()
        current_month = today.month
        current_year = today.year

        # For comparison queries, we need two complete months
        # Current month is incomplete, so we use previous months
        # TODO: this seems funky, update this or remove it completely eventually
        if current_month >= 3:
            # Can compare (current-2) vs (current-1)
            baseline_month = current_month - 2
            comparison_month = current_month - 1
            baseline_year = comparison_year = current_year
        elif current_month == 2:
            # February: compare November vs December of previous year
            baseline_month = 11
            comparison_month = 12
            baseline_year = comparison_year = current_year - 1
        else:  # January
            # January: compare October vs November of previous year
            baseline_month = 10
            comparison_month = 11
            baseline_year = comparison_year = current_year - 1

        # Calculate end dates (first day of next month)
        if comparison_month < 12:
            comparison_end_month = comparison_month + 1
            comparison_end_year = comparison_year
        else:
            comparison_end_month = 1
            comparison_end_year = comparison_year + 1

        return {
            "baseline_date_range": {
                "start_date": f"{baseline_year}-{baseline_month:02d}-01",
                "end_date": f"{comparison_year}-{comparison_month:02d}-01",
            },
            "comparison_date_range": {
                "start_date": f"{comparison_year}-{comparison_month:02d}-01",
                "end_date": f"{comparison_end_year}-{comparison_end_month:02d}-01",
            },
        }

    def _detect_cost_metric(self, query_lower: str) -> str:
        """Detect cost metric from query text"""
        # Check for specific metric keywords (order matters - check specific terms first)
        if "net amortized" in query_lower:
            return "NetAmortizedCost"
        elif "net unblended" in query_lower:
            return "NetUnblendedCost"
        elif "amortized" in query_lower:
            return "AmortizedCost"
        elif "blended" in query_lower:
            return "BlendedCost"
        elif "unblended" in query_lower:
            return "UnblendedCost"
        elif "usage quantity" in query_lower or "usage" in query_lower:
            return "UsageQuantity"
        else:
            # Default to NetAmortizedCost
            return "NetAmortizedCost"

    def list_available_models(self) -> Dict[str, str]:
        """Return available Claude models in Bedrock"""
        return self.model_ids
