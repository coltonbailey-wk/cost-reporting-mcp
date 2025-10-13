import asyncio
import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, Any, List
import statistics

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bedrock_query_processor_enhanced import EnhancedBedrockQueryProcessor
from web_app import OfficialMCPClient
from benchmark import ModelBenchmark


class TestSuite:
    def __init__(self):
        self.enhanced_processor = EnhancedBedrockQueryProcessor()
        self.mcp_client = OfficialMCPClient()
        self.benchmark = ModelBenchmark()
        self.models = ["claude-opus-4-1", "claude-sonnet-4"]
        
        self.test_queries = [
            {
                "query": "What are my total EC2 costs for the current month?",
                "difficulty": "EASY",
                "expected_service": "Amazon Elastic Compute Cloud - Compute",
                "description": "Simple EC2 cost query"
            },
            {
                "query": "Show me S3 spending",
                "difficulty": "EASY", 
                "expected_service": "Amazon Simple Storage Service",
                "description": "Basic S3 cost request"
            },
            {
                "query": "Lambda costs for this month",
                "difficulty": "EASY",
                "expected_service": "AWS Lambda",
                "description": "Current month Lambda costs"
            },
            {
                "query": "Show me RDS spending for last month",
                "difficulty": "MEDIUM",
                "expected_service": "Amazon Relational Database Service",
                "description": "Historical RDS costs with time filter"
            },
            {
                "query": "What are my CloudWatch costs by region?",
                "difficulty": "MEDIUM",
                "expected_service": "AmazonCloudWatch",
                "description": "CloudWatch costs grouped by region"
            },
            {
                "query": "Show me daily EC2 costs for the past 2 weeks",
                "difficulty": "HARD",
                "expected_service": "Amazon Elastic Compute Cloud - Compute",
                "description": "Daily granularity with custom date range"
            },
            {
                "query": "Forecast my S3 costs for next 3 months",
                "difficulty": "HARD",
                "expected_service": "Amazon Simple Storage Service",
                "description": "Cost forecasting"
            },
            {
                "query": "Show me amortized costs vs blended costs for RIs", 
                #"query": "Make two separate API calls: first get amortized costs for Reserved Instances, then get blended costs for Reserved Instances", 
                # Use shorthand RI to see if it's correctly mapped to Standard Reserved Instances
                "difficulty": "EXPERT",
                "expected_purchase_type": "Standard Reserved Instances",
                "description": "Cost metric comparison for reserved instances"
            },
            {
                # Hardest queries - Tags
                "query": "What was the change in net amortized costs by AWS service for the wk.cat.system:cerberus tag?",
                "difficulty": "EXPERT",
                "expected_service": "Amazon Elastic Compute Cloud - Compute",
                "description": "Cost metric comparison for reserved instances"
            },
            {
                "query": "Show me cost allocation by cost center tags for EC2 instances",
                "difficulty": "EXPERT",
                "expected_service": "Amazon Elastic Compute Cloud - Compute",
                "description": "Tag-based cost allocation"
            }
        ]

    async def run_test_suite(self):
        """Run the test suite"""
        all_results = []
        
        for query_info in self.test_queries:
            print(f"\n {query_info['difficulty']}: {query_info['description']}")
            print(f"Query: \"{query_info['query']}\"")
            
            # Test both models on this query
            for model in self.models:
                result = await self.run_single_query(model, query_info)
                all_results.append(result)
            
            # delay between queries
            await asyncio.sleep(0.5)

        return {
            "benchmark_results": all_results,
            "models_tested": self.models,
            "total_queries_per_model": len(self.test_queries),
            "timestamp": datetime.now().isoformat()
        }
    
    async def run_single_query(self, model: str, query_info: Dict[str, Any]) -> Dict[str, Any]: 
        """Run a single query and get cost info - supports multiple tool calls"""
        query = query_info["query"]
        print(f"{model}: {query[:50]}")
        
        # Get the tool call(s) from the model
        tool_call = await self.enhanced_processor.process_query(query, model=model)
        
        # Post-process to split queries that need multiple calls
        tool_call = self._split_multiple_metric_queries(tool_call, query)
        
        # Handle both single tool call and multiple tool calls
        if isinstance(tool_call, list):
            # Multiple tool calls - execute each one
            print(f"  Multiple tool calls detected: {len(tool_call)}")
            actual_data = []
            
            for i, call in enumerate(tool_call):
                print(f"  Executing tool call {i+1}/{len(tool_call)}: {call.get('tool_name', 'Unknown')}")
                
                if call and 'tool_name' in call:
                    try:
                        # Basic parameter fixes for common issues
                        parameters = self._fix_basic_parameters(call.get('parameters', {}), call.get('tool_name'))
                        
                        result = await self.mcp_client.call_tool(
                            call['tool_name'], 
                            parameters
                        )
                        actual_data.append({
                            "tool_call": call,
                            "result": result,
                            "call_index": i + 1
                        })
                    except Exception as e:
                        actual_data.append({
                            "tool_call": call,
                            "result": {"error": str(e)},
                            "call_index": i + 1
                        })
                else:
                    actual_data.append({
                        "tool_call": call,
                        "result": {"error": "Invalid tool call format"},
                        "call_index": i + 1
                    })
        else:
            # Single tool call - original behavior
            actual_data = None
            if tool_call and 'tool_name' in tool_call:
                try:
                    # Basic parameter fixes for common issues
                    parameters = self._fix_basic_parameters(tool_call.get('parameters', {}), tool_call.get('tool_name'))
                    
                    actual_data = await self.mcp_client.call_tool(
                        tool_call['tool_name'], 
                        parameters
                    )
                except Exception as e:
                    actual_data = {"error": str(e)}
        
        return {
            "model": model,
            "query": query,
            "tool_call": tool_call,
            "actual_data": actual_data,
            "query_info": query_info,
            "timestamp": datetime.now().isoformat()
        }

    def _split_multiple_metric_queries(self, tool_call: Any, query: str) -> Any:
        """Post-process tool calls to split queries that need multiple metrics"""
        if not isinstance(tool_call, dict) or 'tool_name' not in tool_call:
            return tool_call
        
        query_lower = query.lower()
        parameters = tool_call.get('parameters', {})
        metric = parameters.get('metric', '')
        
        # Check if this is a query that needs multiple metrics
        needs_multiple_metrics = (
            ('amortized' in query_lower and 'blended' in query_lower) or
            ('amortized' in query_lower and 'unblended' in query_lower) or
            ('blended' in query_lower and 'unblended' in query_lower) or
            ('separate' in query_lower and ('metric' in query_lower or 'cost' in query_lower)) or
            ('both' in query_lower and ('metric' in query_lower or 'cost' in query_lower))
        )
        
        if needs_multiple_metrics and tool_call['tool_name'] == 'get_cost_and_usage':
            print(f"  Splitting query into multiple metric calls")
            
            # Create multiple tool calls for different metrics
            tool_calls = []
            
            # Determine which metrics to include based on query
            metrics_to_use = []
            if 'amortized' in query_lower:
                metrics_to_use.append('AmortizedCost')
            if 'blended' in query_lower:
                metrics_to_use.append('BlendedCost')
            if 'unblended' in query_lower:
                metrics_to_use.append('UnblendedCost')
            
            # Default to AmortizedCost and BlendedCost if not specified
            if not metrics_to_use:
                metrics_to_use = ['AmortizedCost', 'BlendedCost']
            
            # Create a tool call for each metric
            for metric_name in metrics_to_use:
                new_call = tool_call.copy()
                new_call['parameters'] = parameters.copy()
                new_call['parameters']['metric'] = metric_name
                tool_calls.append(new_call)
            
            return tool_calls
        
        return tool_call

    def _fix_basic_parameters(self, parameters: Dict[str, Any], tool_name: str = None) -> Dict[str, Any]:
        """Fix only the most common parameter issues"""
        from datetime import datetime
        
        fixed_params = parameters.copy()
        
        # Fix group_by array format to string format
        if 'group_by' in fixed_params and isinstance(fixed_params['group_by'], list):
            group_by = fixed_params['group_by']
            if len(group_by) > 0 and isinstance(group_by[0], dict) and 'Key' in group_by[0]:
                fixed_params['group_by'] = group_by[0]['Key']
            elif len(group_by) > 0 and isinstance(group_by[0], str):
                fixed_params['group_by'] = group_by[0]
            elif len(group_by) == 0:
                fixed_params['group_by'] = None
        
        # Fix forecast start date (must be <= today, but end date can be in future)
        if 'date_range' in fixed_params and 'start_date' in fixed_params['date_range']:
            today = datetime.now().strftime("%Y-%m-%d")
            # Only fix start date if it's in the future (forecasts start from today or earlier)
            if fixed_params['date_range']['start_date'] > today:
                fixed_params['date_range']['start_date'] = today
        
        # Fix metric names based on tool type
        if 'metric' in fixed_params:
            metric = fixed_params['metric']
            
            # Forecasting tools expect uppercase format
            if tool_name and 'forecast' in tool_name.lower():
                forecast_mapping = {
                    'UnblendedCost': 'UNBLENDED_COST',
                    'BlendedCost': 'BLENDED_COST',
                    'AmortizedCost': 'AMORTIZED_COST',
                    'NetAmortizedCost': 'NET_AMORTIZED_COST',
                    'NetUnblendedCost': 'NET_UNBLENDED_COST',
                    'UNBLENDED_COST': 'UNBLENDED_COST',
                    'BLENDED_COST': 'BLENDED_COST',
                    'AMORTIZED_COST': 'AMORTIZED_COST',
                    'NET_AMORTIZED_COST': 'NET_AMORTIZED_COST',
                    'NET_UNBLENDED_COST': 'NET_UNBLENDED_COST'
                }
                if metric in forecast_mapping:
                    fixed_params['metric'] = forecast_mapping[metric]
            else:
                # Regular cost and usage tools expect PascalCase format
                usage_mapping = {
                    'UNBLENDED_COST': 'UnblendedCost',
                    'BLENDED_COST': 'BlendedCost', 
                    'AMORTIZED_COST': 'AmortizedCost',
                    'NET_AMORTIZED_COST': 'NetAmortizedCost',
                    'NET_UNBLENDED_COST': 'NetUnblendedCost',
                    'USAGE_QUANTITY': 'UsageQuantity',
                    'UnblendedCost': 'UnblendedCost',
                    'BlendedCost': 'BlendedCost',
                    'AmortizedCost': 'AmortizedCost',
                    'NetAmortizedCost': 'NetAmortizedCost',
                    'NetUnblendedCost': 'NetUnblendedCost',
                    'UsageQuantity': 'UsageQuantity'
                }
                if metric in usage_mapping:
                    fixed_params['metric'] = usage_mapping[metric]
        
        # Fix invalid metrics
        if 'metric' in fixed_params and fixed_params['metric'] == 'BOTH':
            if tool_name and 'forecast' in tool_name.lower():
                fixed_params['metric'] = 'UNBLENDED_COST'
            else:
                # For cost and usage queries, 'BOTH' is not supported by AWS API
                # Default to AmortizedCost for Reserved Instances since that's what shows real data
                fixed_params['metric'] = 'AmortizedCost'
                print(f"WARNING: 'BOTH' metric not supported by AWS API, using AmortizedCost instead")
        
        # Handle requests for multiple metrics (like "amortized and blended costs")
        if 'metric' in fixed_params and isinstance(fixed_params['metric'], str):
            metric_lower = fixed_params['metric'].lower()
            if 'amortized' in metric_lower and 'blended' in metric_lower:
                # Default to AmortizedCost for Reserved Instances
                fixed_params['metric'] = 'AmortizedCost'
                print(f"WARNING: Multiple metrics requested, using AmortizedCost. Consider making separate calls for each metric.")
        
        # Fix group_by for tag dimensions
        if 'group_by' in fixed_params and isinstance(fixed_params['group_by'], list):
            for i, group in enumerate(fixed_params['group_by']):
                if isinstance(group, dict) and group.get('Type') == 'TAG':
                    # Tag grouping is not supported in group_by - convert to SERVICE grouping
                    # Tags can be used in filter_expression but not in group_by
                    fixed_params['group_by'][i] = 'SERVICE'
                    print(f"WARNING: Tag grouping not supported in group_by, converted to SERVICE grouping")
        
        # Handle single tag group_by (not in array format)
        if 'group_by' in fixed_params and isinstance(fixed_params['group_by'], str):
            # Check if it's a tag name that's not a valid dimension
            invalid_dimensions = ['CostCenter', 'Environment', 'Project', 'Team', 'Department', 'USAGE_TYPE_GROUP']
            if fixed_params['group_by'] in invalid_dimensions:
                fixed_params['group_by'] = 'SERVICE'
                print(f"WARNING: Invalid dimension '{fixed_params['group_by']}' not supported in group_by, converted to SERVICE grouping")
        
        # Fix comparison tool parameters
        if 'current_period' in fixed_params and 'previous_period' in fixed_params:
            # Convert to the correct parameter names for comparison tools
            fixed_params['baseline_date_range'] = fixed_params.pop('current_period')
            fixed_params['comparison_date_range'] = fixed_params.pop('previous_period')
        
        # Fix comparison tool date ranges to be first day of month and exactly one month
        if 'baseline_date_range' in fixed_params:
            baseline = fixed_params['baseline_date_range']
            if 'start_date' in baseline and 'end_date' in baseline:
                # Ensure start and end dates are first day of month
                start_date = baseline['start_date']
                end_date = baseline['end_date']
                
                # Convert to first day of month
                if len(start_date) >= 7:  # YYYY-MM-DD format
                    baseline['start_date'] = start_date[:7] + '-01'
                if len(end_date) >= 7:  # YYYY-MM-DD format
                    baseline['end_date'] = end_date[:7] + '-01'
                
                # Ensure exactly one month period
                start_year_month = baseline['start_date'][:7]  # YYYY-MM
                year, month = map(int, start_year_month.split('-'))
                # Calculate next month
                if month == 12:
                    next_year, next_month = year + 1, 1
                else:
                    next_year, next_month = year, month + 1
                baseline['end_date'] = f"{next_year:04d}-{next_month:02d}-01"
        
        if 'comparison_date_range' in fixed_params:
            comparison = fixed_params['comparison_date_range']
            if 'start_date' in comparison and 'end_date' in comparison:
                # Ensure start and end dates are first day of month
                start_date = comparison['start_date']
                end_date = comparison['end_date']
                
                # Convert to first day of month
                if len(start_date) >= 7:  # YYYY-MM-DD format
                    comparison['start_date'] = start_date[:7] + '-01'
                if len(end_date) >= 7:  # YYYY-MM-DD format
                    comparison['end_date'] = end_date[:7] + '-01'
                
                # Ensure exactly one month period
                start_year_month = comparison['start_date'][:7]  # YYYY-MM
                year, month = map(int, start_year_month.split('-'))
                # Calculate next month
                if month == 12:
                    next_year, next_month = year + 1, 1
                else:
                    next_year, next_month = year, month + 1
                comparison['end_date'] = f"{next_year:04d}-{next_month:02d}-01"
        
        # Fix current month issue - use previous complete months
        from datetime import datetime
        current_date = datetime.now()
        current_year_month = current_date.strftime("%Y-%m")
        
        if 'baseline_date_range' in fixed_params:
            baseline = fixed_params['baseline_date_range']
            if 'start_date' in baseline and baseline['start_date'].startswith(current_year_month):
                # Move to previous month if trying to use current month
                year, month = map(int, current_year_month.split('-'))
                if month == 1:
                    prev_year, prev_month = year - 1, 12
                else:
                    prev_year, prev_month = year, month - 1
                baseline['start_date'] = f"{prev_year:04d}-{prev_month:02d}-01"
                baseline['end_date'] = f"{year:04d}-{month:02d}-01"
        
        if 'comparison_date_range' in fixed_params:
            comparison = fixed_params['comparison_date_range']
            if 'start_date' in comparison and comparison['start_date'].startswith(current_year_month):
                # Move to previous month if trying to use current month
                year, month = map(int, current_year_month.split('-'))
                if month == 1:
                    prev_year, prev_month = year - 1, 12
                else:
                    prev_year, prev_month = year, month - 1
                comparison['start_date'] = f"{prev_year:04d}-{prev_month:02d}-01"
                comparison['end_date'] = f"{year:04d}-{month:02d}-01"
        
        # Ensure baseline period is after comparison period
        if 'baseline_date_range' in fixed_params and 'comparison_date_range' in fixed_params:
            baseline = fixed_params['baseline_date_range']
            comparison = fixed_params['comparison_date_range']
            
            if (baseline.get('start_date') == comparison.get('start_date') and 
                baseline.get('end_date') == comparison.get('end_date')):
                # If periods are the same, adjust comparison to be one month earlier
                start_year_month = comparison['start_date'][:7]  # YYYY-MM
                year, month = map(int, start_year_month.split('-'))
                if month == 1:
                    prev_year, prev_month = year - 1, 12
                else:
                    prev_year, prev_month = year, month - 1
                comparison['start_date'] = f"{prev_year:04d}-{prev_month:02d}-01"
                comparison['end_date'] = f"{year:04d}-{month:02d}-01"
        
        # Fix invalid TAG dimension in filter expressions
        if 'filter_expression' in fixed_params:
            filter_expr = fixed_params['filter_expression']
            if isinstance(filter_expr, dict):
                # Check for Dimensions with TAG key
                if 'Dimensions' in filter_expr:
                    dims = filter_expr['Dimensions']
                    if isinstance(dims, dict) and dims.get('Key') == 'TAG':
                        # Convert TAG dimension to Tags filter
                        tag_key_value = dims.get('Values', [''])[0]
                        if ':' in tag_key_value:
                            tag_key, tag_value = tag_key_value.split(':', 1)
                            filter_expr['Tags'] = {
                                'Key': tag_key,
                                'Values': [tag_value],
                                'MatchOptions': ['EQUALS']
                            }
                            del filter_expr['Dimensions']
                        else:
                            # Fallback: remove invalid filter
                            del filter_expr['Dimensions']
        
        return fixed_params

    def save_results(self, results: Dict[str, Any]) -> str:
        """Save test results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n Results saved to: {filename}")
        return filename


async def main():
    """Run the test suite"""
    test_suite = TestSuite()
    results = await test_suite.run_test_suite()
    # Print results
    filename = test_suite.save_results(results)
    print("\n" + "="*60)
    print("TEST SUITE RESULTS")
    print("="*60)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    asyncio.run(main())