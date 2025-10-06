"""
Enhanced AWS Bedrock Claude query processor with auto-correction capabilities
"""

import json
import re
from datetime import datetime
from typing import Any, Dict, Optional
import boto3


class EnhancedBedrockQueryProcessor:
    def __init__(self, region_name: str = "us-east-1"):
        """Initialize AWS Bedrock client with enhanced capabilities"""
        self.bedrock = boto3.client("bedrock-runtime", region_name=region_name)
        
        # Available Claude models in Bedrock (using model IDs and inference profiles)
        self.model_ids = {
            "claude-opus-4-1": "anthropic.claude-opus-4-1-20250805-v1:0",  # Claude 4.1 primary
            "claude-3-5-sonnet": "anthropic.claude-3-5-sonnet-20240620-v1:0",
        }
        
        # Common inference profile formats to try for Claude 4.1
        self.claude_4_1_profiles = [
            "us.anthropic.claude-opus-4-1-20250805-v1:0",  # Correct regional inference profile
            f"arn:aws:bedrock:{region_name}::inference-profile/us.anthropic.claude-opus-4-1-20250805-v1:0",  # ARN format
            "anthropic.claude-opus-4-1-20250805-v1:0",  # Direct format (fallback)
        ]
        
        self.default_model = "claude-opus-4-1"  # Default to most accurate Claude 4.1 Opus
        
        # AWS service name mappings for common shortcuts
        self.service_name_mappings = {
            # EC2 variations
            "EC2": "Amazon Elastic Compute Cloud - Compute",
            "ec2": "Amazon Elastic Compute Cloud - Compute", 
            "Elastic Compute Cloud": "Amazon Elastic Compute Cloud - Compute",
            "Amazon EC2": "Amazon Elastic Compute Cloud - Compute",
            
            # RDS variations
            "RDS": "Amazon Relational Database Service",
            "rds": "Amazon Relational Database Service",
            "Relational Database": "Amazon Relational Database Service",
            
            # S3 variations
            "S3": "Amazon Simple Storage Service",
            "s3": "Amazon Simple Storage Service",
            "Simple Storage": "Amazon Simple Storage Service",
            
            # Lambda variations
            "Lambda": "AWS Lambda",
            "lambda": "AWS Lambda",
            
            # CloudWatch variations
            "CloudWatch": "AmazonCloudWatch",
            "cloudwatch": "AmazonCloudWatch",
        }
        
        # Purchase type mappings
        self.purchase_type_mappings = {
            "Reserved": "Standard Reserved Instances",
            "reserved": "Standard Reserved Instances",
            "Reserved Instances": "Standard Reserved Instances",
            "RI": "Standard Reserved Instances",
            "OnDemand": "On Demand Instances",
            "On-Demand": "On Demand Instances",
            "Spot": "Spot Instances",
            "SavingsPlans": "Savings Plans",
            "Savings Plan": "Savings Plans",
            "SP": "Savings Plans",
        }

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
            model_id = self.model_ids.get(model_id, model_id)
            return self.bedrock.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )

    def _get_enhanced_system_prompt(self) -> str:
        """Get enhanced system prompt with AWS service name examples"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        return f"""You are an AWS Cost Explorer query processor with STRICT AWS service name requirements.

CRITICAL AWS SERVICE NAME RULES:
1. NEVER use shortcuts like "EC2", "RDS", "S3" - AWS Cost Explorer requires EXACT full names
2. ALWAYS use the complete AWS service names as they appear in billing

COMMON MISTAKES TO AVOID:
WRONG: "EC2" -> CORRECT: "Amazon Elastic Compute Cloud - Compute" 
WRONG: "RDS" -> CORRECT: "Amazon Relational Database Service"
WRONG: "S3" -> CORRECT: "Amazon Simple Storage Service"
WRONG: "Lambda" -> CORRECT: "AWS Lambda"
WRONG: "CloudWatch" -> CORRECT: "AmazonCloudWatch"
WRONG: "Reserved" -> CORRECT: "Standard Reserved Instances"

EXACT SERVICE NAMES FOR COMMON SERVICES:
- EC2 Compute: "Amazon Elastic Compute Cloud - Compute"
- EC2 Other: "EC2 - Other" 
- RDS: "Amazon Relational Database Service"
- S3: "Amazon Simple Storage Service"
- Lambda: "AWS Lambda"
- CloudWatch: "AmazonCloudWatch"
- ElastiCache: "Amazon ElastiCache"
- Load Balancer: "Amazon Elastic Load Balancing"
- VPC: "Amazon Virtual Private Cloud"

EXACT PURCHASE TYPES:
- Reserved Instances: "Standard Reserved Instances" (NOT "Reserved")
- On-Demand: "On Demand Instances"
- Spot: "Spot Instances"
- Savings Plans: "Savings Plans"

FILTERING RULES:
1. For "EC2 costs" queries, use: "Amazon Elastic Compute Cloud - Compute"
2. For broader EC2 including storage/networking, also include: "EC2 - Other"
3. For reserved instances, use: "Standard Reserved Instances"
4. ALWAYS include filter_expression when user asks for specific services

Current date: {current_date}

Available tools:
- get_cost_and_usage: Retrieve cost and usage data with filtering and grouping
- get_cost_forecast: Generate cost forecasts for future periods
- get_cost_and_usage_comparisons: Compare costs between two time periods
- get_dimension_values: Get available values for dimensions like SERVICE, REGION
- get_tag_values: Get available tag values
- get_cost_comparison_drivers: Analyze what drove cost changes

For each query, provide:
1. tool_name: The appropriate tool to use
2. parameters: Complete parameters with proper AWS service names
3. visualization: Chart type and title
4. explanation: Brief explanation of the approach

CRITICAL: Use exact AWS service names in all filter expressions."""

    def _fix_service_names(self, filter_expression: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-correct common service name mistakes"""
        if not filter_expression or 'Dimensions' not in filter_expression:
            return filter_expression
            
        dimensions = filter_expression['Dimensions']
        if dimensions.get('Key') == 'SERVICE' and 'Values' in dimensions:
            corrected_values = []
            for value in dimensions['Values']:
                # Try exact mapping first
                if value in self.service_name_mappings:
                    corrected_values.append(self.service_name_mappings[value])
                    print(f"Auto-corrected service name: '{value}' -> '{self.service_name_mappings[value]}'")
                else:
                    corrected_values.append(value)
            dimensions['Values'] = corrected_values
            
        elif dimensions.get('Key') == 'PURCHASE_TYPE' and 'Values' in dimensions:
            corrected_values = []
            for value in dimensions['Values']:
                if value in self.purchase_type_mappings:
                    corrected_values.append(self.purchase_type_mappings[value])
                    print(f"Auto-corrected purchase type: '{value}' -> '{self.purchase_type_mappings[value]}'")
                else:
                    corrected_values.append(value)
            dimensions['Values'] = corrected_values
            
        return filter_expression

    async def process_query(self, query: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Process query with enhanced auto-correction"""
        model_id = self.model_ids.get(model or self.default_model)
        
        system_prompt = self._get_enhanced_system_prompt()
        
        # Enhanced user prompt with examples
        user_prompt = f"""
Query: "{query}"

Analyze this query and provide the tool call with EXACT AWS service names.

Remember:
- Use "Amazon Elastic Compute Cloud - Compute" for EC2
- Use "Standard Reserved Instances" for Reserved Instances
- Always include proper filter_expression for specific services

Respond with JSON containing:
{{
  "tool_name": "appropriate_tool",
  "parameters": {{
    "date_range": {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}},
    "filter_expression": {{"Dimensions": {{"Key": "SERVICE", "Values": ["exact_service_name"], "MatchOptions": ["EQUALS"]}}}},
    "metric": "appropriate_metric",
    "granularity": "appropriate_granularity",
    "group_by": "appropriate_grouping"
  }},
  "visualization": {{
    "chart_type": "appropriate_chart",
    "title": "descriptive_title"
  }},
  "explanation": "brief_explanation"
}}
"""

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": 0.1,
        }

        try:
            response = self._invoke_model_with_retry(model_id, request_body)
            response_body = json.loads(response["body"].read())
            
            if "content" in response_body and response_body["content"]:
                content = response_body["content"][0]["text"]
                
                # Parse JSON response
                try:
                    # Extract JSON from response
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start != -1 and json_end != -1:
                        json_content = content[json_start:json_end]
                        parsed_response = json.loads(json_content)
                        
                        # Apply auto-correction to parameters
                        if 'parameters' in parsed_response and 'filter_expression' in parsed_response['parameters']:
                            parsed_response['parameters']['filter_expression'] = self._fix_service_names(
                                parsed_response['parameters']['filter_expression']
                            )
                        
                        return parsed_response
                    else:
                        raise ValueError("No valid JSON found in response")
                        
                except json.JSONDecodeError as e:
                    print(f"JSON parsing error: {e}")
                    print(f"Raw content: {content}")
                    raise ValueError(f"Failed to parse JSON response: {e}")
            else:
                raise ValueError("No content in response")
                
        except Exception as e:
            print(f"Error in process_query: {e}")
            raise

    async def generate_explanation(self, query: str, tool_result: Dict[str, Any]) -> str:
        """Generate natural language explanation of results"""
        model_id = self.model_ids.get(self.default_model)
        
        system_prompt = """You are an AWS cost analysis expert. Provide clear, concise explanations of cost data results."""
        
        user_prompt = f"""
Original query: "{query}"

Tool result: {json.dumps(tool_result, indent=2)}

Provide a clear, helpful explanation of these results for the user. Focus on:
1. What the data shows
2. Key insights or patterns
3. Actionable recommendations if appropriate

Keep it concise but informative.
"""

        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "temperature": 0.3,
        }

        try:
            response = self._invoke_model_with_retry(model_id, request_body)
            response_body = json.loads(response["body"].read())
            
            if "content" in response_body and response_body["content"]:
                return response_body["content"][0]["text"]
            else:
                return "Unable to generate explanation."
                
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return f"Error generating explanation: {str(e)}"
