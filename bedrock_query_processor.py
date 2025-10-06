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
        # Available Claude models in Bedrock (using model IDs and inference profiles)
        self.model_ids = {
            "claude-opus-4-1": "anthropic.claude-opus-4-1-20250805-v1:0",  # Claude 4.1 primary
            "claude-3-5-sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
            "claude-3-opus": "anthropic.claude-3-opus-20240229-v1:0",
            "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
            "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
        }
        # Common inference profile formats to try for Claude 4.1
        self.claude_4_1_profiles = [
            "us.anthropic.claude-opus-4-1-20250805-v1:0",  # Correct regional inference profile
            f"arn:aws:bedrock:{region_name}::inference-profile/us.anthropic.claude-opus-4-1-20250805-v1:0",  # ARN format
            "anthropic.claude-opus-4-1-20250805-v1:0",  # Direct format (fallback)
        ]
        self.default_model = "claude-3-5-sonnet"  # Default to faster Claude 3.5 Sonnet

    def _invoke_model_with_retry(self, model_id: str, request_body: dict) -> dict:
        """Invoke Bedrock model with Claude 4.1 inference profile retry logic"""
        
        # If it's Claude 4.1, try different inference profile formats
        if "claude-opus-4-1" in model_id:
            print(f"Claude 4.1 requested, trying {len(self.claude_4_1_profiles)} profiles...")
            for i, profile_id in enumerate(self.claude_4_1_profiles):
                try:
                    print(f"Attempting Claude 4.1 profile {i+1}/{len(self.claude_4_1_profiles)}: {profile_id}")
                    response = self.bedrock.invoke_model(
                        modelId=profile_id,
                        contentType="application/json",
                        accept="application/json",
                        body=json.dumps(request_body),
                    )
                    print(f"Success with Claude 4.1 profile: {profile_id}")
                    return response
                except Exception as e:
                    error_msg = str(e)
                    print(f"Claude 4.1 profile {i+1} failed: {error_msg}")
                    
                    # Check if it's a throughput/profile error
                    if "on-demand throughput" in error_msg or "inference profile" in error_msg:
                        print(f"Profile {i+1} failed due to throughput/profile issue, trying next...")
                        continue
                    else:
                        # If it's a different error, re-raise it
                        raise e
            
            # If all Claude 4.1 profiles failed, fall back to Claude 3.5 Sonnet
            print("All Claude 4.1 profiles failed, falling back to Claude 3.5 Sonnet")
            fallback_model_id = self.model_ids["claude-3-5-sonnet"]
            return self.bedrock.invoke_model(
                modelId=fallback_model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )
        else:
            # For other models, use direct invocation
            return self.bedrock.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )

    async def process_query(self, query: str, model: str = None) -> Dict[str, Any]:
        """Process natural language query with AWS Bedrock Claude"""

        model_id = self.model_ids.get(model or self.default_model)

        current_date = datetime.now().strftime("%Y-%m-%d")
        system_prompt = """You are an AWS Cost Explorer query processor.

CRITICAL FILTERING RULES - READ FIRST

RULE 1: When user mentions a SPECIFIC TAG VALUE (like "squad-one-jam", "production", "dev"), you MUST:
1. Set group_by to TAG format: {{"Type": "TAG", "Key": "tag_name"}}
2. Add filter_expression to filter to that specific value
3. NEVER group by "SERVICE" when filtering by tag values

RULE 2: Tag Value Detection - These phrases REQUIRE filtering:
- "costs for [tag-value]" → MUST filter by that tag value
- "show me [tag-value] costs" → MUST filter by that tag value  
- "[tag-value] deployment.environment tag" → MUST filter by that tag value
- "[tag-value] environment" → MUST filter by that tag value
- "untagged" or "no tag" or "missing tag" → Use empty string "" as the tag value
- "what costs are untagged" → Filter by tag value ""

RULE 3: Filter Expression Format (MANDATORY):
- Parameter name MUST be "filter_expression" (NOT "filter")
- For tag filtering: "filter_expression": {{"Tags": {{"Key": "tag_name", "Values": ["tag_value"], "MatchOptions": ["EQUALS"]}}}}
- ALWAYS include "MatchOptions": ["EQUALS"]

WRONG: "Give me costs for squad-one-jam" → group_by: "SERVICE" (NO filter_expression)
CORRECT: "Give me costs for squad-one-jam" → group_by: {{"Type": "TAG", "Key": "deployment.environment"}}, filter_expression: {{"Tags": {{"Key": "deployment.environment", "Values": ["squad-one-jam"], "MatchOptions": ["EQUALS"]}}}}

DECISION TREE FOR EVERY QUERY:
1. Does the query mention a specific tag value? (squad-one-jam, production, dev, etc.)
   → YES: Use group_by TAG format + filter_expression
   → NO: Use group_by "SERVICE"

2. Does the query ask for "costs for [specific-value]"?
   → YES: MUST include filter_expression
   → NO: No filter needed

TEMPLATE FOR TAG VALUE QUERIES - COPY EXACTLY:
When user asks for costs for a specific tag value, use this EXACT template:
{{
  "query_type": "cost_analysis",
  "tool_name": "get_cost_and_usage",
  "parameters": {{
    "date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}},
    "granularity": "MONTHLY",
    "metric": "NetAmortizedCost",
    "group_by": {{"Type": "TAG", "Key": "REPLACE_WITH_TAG_KEY"}},
    "filter_expression": {{"Tags": {{"Key": "REPLACE_WITH_TAG_KEY", "Values": ["REPLACE_WITH_TAG_VALUE"], "MatchOptions": ["EQUALS"]}}}}
  }}
}}

For "squad-one-jam deployment.environment tag":
- REPLACE_WITH_TAG_KEY = "deployment.environment"  
- REPLACE_WITH_TAG_VALUE = "squad-one-jam"

Your job is to analyze natural language queries about AWS costs and return structured JSON responses that specify:
1. Query type (cost_analysis, forecast, comparison, meta)
2. AWS Cost Explorer tool to use
3. Parameters for the tool call
4. Visualization preferences

Available AWS Cost Explorer MCP tools:
- get_cost_and_usage: Get cost data for date ranges
  * Parameters: {{"date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "granularity": "DAILY|MONTHLY", "metric": "NetAmortizedCost", "group_by": "SERVICE", "filter_expression": {{"Tags": {{"Key": "tag_name", "Values": ["tag_value"], "MatchOptions": ["EQUALS"]}}}}}
- get_cost_forecast: Predict future costs
  * Parameters: {{"date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "granularity": "MONTHLY", "metric": "NET_AMORTIZED_COST"}}
  * IMPORTANT: start_date must be TODAY or earlier, end_date must be in the FUTURE
  * CRITICAL: Forecast metrics use UNDERSCORE format: NET_AMORTIZED_COST, UNBLENDED_COST, etc.
- get_cost_and_usage_comparisons: Compare two time periods
  * Parameters: {{"baseline_date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "comparison_date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "metric_for_comparison": "NetAmortizedCost"}}
- get_dimension_values: Get available services, regions, etc.
  * Parameters: {{"date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "dimension": {{"dimension_key": "SERVICE|REGION|LINKED_ACCOUNT"}}}}
- get_tag_values: Get available tag values for a SPECIFIC tag
  * Parameters: {{"date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}, "tag_key": "specific_tag_name"}}
  * IMPORTANT: Requires knowing the exact tag name. For discovering tag keys, use get_dimension_values instead.

IMPORTANT: AWS Cost Metrics - Choose the correct metric based on user query:
- "unblended cost/costs" → "UnblendedCost" (or "UNBLENDED_COST" for forecasts)
- "net amortized cost/costs" → "NetAmortizedCost" (or "NET_AMORTIZED_COST" for forecasts) (default)
- "amortized cost/costs" → "AmortizedCost" (or "AMORTIZED_COST" for forecasts)
- "blended cost/costs" → "BlendedCost" (or "BLENDED_COST" for forecasts)
- "net unblended cost/costs" → "NetUnblendedCost" (or "NET_UNBLENDED_COST" for forecasts)
- DEFAULT (no specific metric mentioned) → "NetAmortizedCost" (or "NET_AMORTIZED_COST" for forecasts)
- "usage quantity" → "UsageQuantity"

CRITICAL: For get_cost_forecast tool, use UNDERSCORE format: NET_AMORTIZED_COST, UNBLENDED_COST, etc.

CRITICAL: Group By Format Rules - THIS IS MANDATORY!:
- Dimensions (SERVICE, REGION, etc.): Use string format: "SERVICE"
- Tags (owner, wk.cat.owner, etc.): ALWAYS use object format: {{"Type": "TAG", "Key": "tag_name"}}
- NEVER EVER use "TAG:tag_name" format - AWS will reject this with validation error

TAG FORMAT EXAMPLES - COPY THESE EXACTLY:
- For wk.cat.owner tag: {{"Type": "TAG", "Key": "wk.cat.owner"}}
- For wk.cat tag: {{"Type": "TAG", "Key": "wk.cat"}}
- For owner tag: {{"Type": "TAG", "Key": "owner"}}
- For environment tag: {{"Type": "TAG", "Key": "environment"}}

CRITICAL: Tag Discovery Queries:
- "What tag keys are available" → Use get_dimension_values with dimension_key: "TAG"
- "List available tags" → Use get_dimension_values with dimension_key: "TAG" 
- "Show me tag keys" → Use get_dimension_values with dimension_key: "TAG"

CRITICAL: Filter Expression Format - THIS IS MANDATORY!:
- Parameter name MUST be "filter_expression" (NOT "filter")
- For tag filtering: "filter_expression": {{"Tags": {{"Key": "tag_name", "Values": ["tag_value"], "MatchOptions": ["EQUALS"]}}}}
- For dimension filtering: "filter_expression": {{"Dimensions": {{"Key": "SERVICE", "Values": ["service_name"], "MatchOptions": ["EQUALS"]}}}}
- NEVER use "filter" - it will be ignored by the MCP server
- ALWAYS include "MatchOptions": ["EQUALS"] for proper filtering
- Example: "filter_expression": {{"Tags": {{"Key": "deployment.environment", "Values": ["squad-one-jam"], "MatchOptions": ["EQUALS"]}}}}

CRITICAL: Tag Comparison vs Time Period Comparison:
- "Which tag VALUES are more expensive" (same tag key) → Use get_cost_and_usage grouped by that tag
- "Compare costs between July and August" → Use get_cost_and_usage_comparisons (compares time periods)  
- "wk.cat.service vs wk.cat.repository" (different tag keys) → Use get_cost_and_usage filtered by first tag only, explain limitation
- "This month vs last month" → Use get_cost_and_usage_comparisons (time comparison)

IMPORTANT: AWS Cost Explorer cannot easily compare different tag keys in a single query.
For "wk.cat.service vs wk.cat.repository" queries, focus on one tag and explain the limitation.

Always return valid JSON with this structure:
{
    "query_type": "cost_analysis|forecast|comparison|meta",
    "tool_name": "tool_name_here", 
    "parameters": {
        "date_range": {"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"},
        "granularity": "DAILY|MONTHLY|HOURLY",
        "metric": "NetAmortizedCost|UnblendedCost|AmortizedCost|BlendedCost|NetUnblendedCost|UsageQuantity",
        "group_by": "SERVICE" (for dimensions) OR {"Type": "TAG", "Key": "tag_name"} (for tags),
        ...
    },
    "visualization": {
        "chart_type": "sparkline|timeline|bar|pie|table",
        "title": "Chart title",
        "description": "Brief explanation"
    },
    "explanation": "Natural language explanation of what will be done"
}

Current date context: """ + current_date

        user_prompt = f"MANDATORY CHECK: Does the query \"{query}\" mention any specific tag value?\nIf YES: You MUST use group_by TAG format and include filter_expression!\n\nAnalyze this AWS cost query and return the structured JSON response:\n\nQuery: \"{query}\"\n\nExamples with EXACT parameter formats:" + """

1. Cost Analysis Query:
"Show my EC2 costs last month" →
{
  "query_type": "cost_analysis",
  "tool_name": "get_cost_and_usage",
  "parameters": {
    "date_range": {"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-31"},
    "granularity": "DAILY",
    "metric": "NetAmortizedCost",
    "group_by": "SERVICE"
  }
}

1b. Tag-based Cost Analysis Query:
"Show me costs grouped by owner tags" →
{{
  "query_type": "cost_analysis",
  "tool_name": "get_cost_and_usage",
  "parameters": {{
    "date_range": {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-31"}},
    "granularity": "MONTHLY",
    "metric": "NetAmortizedCost",
    "group_by": {{"Type": "TAG", "Key": "owner"}}
  }}
}}

1c. Account Context Query (still group by SERVICE):
"Show me my AWS costs from july 1st to september 29th in the Dev AWS account" →
{{
  "query_type": "cost_analysis",
  "tool_name": "get_cost_and_usage",
  "parameters": {{
    "date_range": {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-31"}},
    "granularity": "MONTHLY",
    "metric": "NetAmortizedCost",
    "group_by": "SERVICE"
  }}
}}

"Give me costs by wk.cat.owner tags" →
{{
  "query_type": "cost_analysis", 
  "tool_name": "get_cost_and_usage",
  "parameters": {{
    "date_range": {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-31"}},
    "granularity": "MONTHLY",
    "metric": "NetAmortizedCost",
    "group_by": {{"Type": "TAG", "Key": "wk.cat.owner"}}
  }}
}}

FILTERING EXAMPLE - COPY THIS PATTERN:
"Give me costs for squad-one-jam deployment.environment tag" →
{{
  "query_type": "cost_analysis",
  "tool_name": "get_cost_and_usage", 
  "parameters": {{
    "date_range": {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-31"}},
    "granularity": "MONTHLY",
    "metric": "NetAmortizedCost",
    "group_by": {{"Type": "TAG", "Key": "deployment.environment"}},
    "filter_expression": {{"Tags": {{"Key": "deployment.environment", "Values": ["squad-one-jam"], "MatchOptions": ["EQUALS"]}}}}
  }}
}}

"Show me production environment costs" →
{{
  "query_type": "cost_analysis",
  "tool_name": "get_cost_and_usage", 
  "parameters": {{
    "date_range": {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-31"}},
    "granularity": "MONTHLY",
    "metric": "NetAmortizedCost",
    "group_by": {{"Type": "TAG", "Key": "environment"}},
    "filter_expression": {{"Tags": {{"Key": "environment", "Values": ["production"], "MatchOptions": ["EQUALS"]}}}}
  }}
}}

"What deployment.environment costs are untagged?" →
{{
  "query_type": "cost_analysis",
  "tool_name": "get_cost_and_usage", 
  "parameters": {{
    "date_range": {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-31"}},
    "granularity": "MONTHLY",
    "metric": "NetAmortizedCost",
    "group_by": "SERVICE",
    "filter_expression": {{"Tags": {{"Key": "deployment.environment", "Values": [""], "MatchOptions": ["EQUALS"]}}}}
  }}
}}

1c. Tag Discovery Query:
"What tag keys are available for my AWS costs?" →
{{
  "query_type": "cost_analysis",
  "tool_name": "get_dimension_values",
  "parameters": {{
    "date_range": {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-31"}},
    "dimension": {{"dimension_key": "TAG"}}
  }}
}}

1d. Tag Key Comparison Query (Limited):
"Which tag was more expensive for last month, wk.cat.service, or wk.cat.repository?" →
{{
  "query_type": "cost_analysis", 
  "tool_name": "get_cost_and_usage",
  "parameters": {{
    "date_range": {{"start_date": "YYYY-MM-01", "end_date": "YYYY-MM-31"}},
    "granularity": "MONTHLY", 
    "metric": "NetAmortizedCost",
    "group_by": "SERVICE"
  }},
  "explanation": "AWS Cost Explorer cannot easily compare different tag keys in a single query. I'll show overall costs and suggest separate queries for each tag."
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
- GROUP BY LOGIC: Use "SERVICE" for cost breakdowns, "LINKED_ACCOUNT" only when explicitly asking to compare accounts
- Comparisons: MUST have both "baseline_date_range" AND "comparison_date_range"
- AWS DATE REQUIREMENT: 
  * For SINGLE MONTH queries: end_date MUST be BEFORE the beginning of next month (e.g., "2025-09-30" for September)
  * For COMPARISON queries: end_date MUST be first day of next month (e.g., "2025-10-01" for September)
  * WRONG single month: {{"start_date": "2025-09-01", "end_date": "2025-10-01"}}
  * CORRECT single month: {{"start_date": "2025-09-01", "end_date": "2025-09-30"}}
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

FINAL CHECK BEFORE RESPONDING:
1. Does the query mention any specific tag value?
   → If YES: MUST include filter_expression and use TAG group_by
2. Is group_by set to "SERVICE" when filtering by tag values?
   → If YES: This is WRONG - change to TAG format
3. Is filter_expression missing when user asks for specific tag value?
   → If YES: This is WRONG - add filter_expression
"""

        try:
            # Prepare request for Claude via Bedrock
            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "system": system_prompt,
                "messages": [{"role": "user", "content": user_prompt}],
            }

            response = self._invoke_model_with_retry(model_id, request_body)

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

            response = self._invoke_model_with_retry(model_id, request_body)

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

        baseline_start = f"{baseline_year}-{baseline_month:02d}-01"
        baseline_end = f"{comparison_year}-{comparison_month:02d}-01"
        comparison_start = f"{comparison_year}-{comparison_month:02d}-01"
        comparison_end = f"{comparison_year}-{comparison_month + 1:02d}-01"

        return {
            "baseline_date_range": {
                "start_date": baseline_start,
                "end_date": baseline_end,
            },
            "comparison_date_range": {
                "start_date": comparison_start,
                "end_date": comparison_end,
            },
        }

    def _detect_cost_metric(self, query: str) -> str:
        """Detect cost metric from query keywords"""
        if "unblended" in query:
            return "UnblendedCost"
        elif "net amortized" in query:
            return "NetAmortizedCost"
        elif "amortized" in query:
            return "AmortizedCost"
        elif "blended" in query:
            return "BlendedCost"
        elif "net unblended" in query:
            return "NetUnblendedCost"
        elif "usage quantity" in query:
            return "UsageQuantity"
        else:
            return "NetAmortizedCost"  # Default