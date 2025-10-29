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


# Benchmark testing for Opus 4.1 and Sonnet 4 to test their speed and accuracy
class ModelBenchmark:
    def __init__(self):
        self.enhanced_processor = EnhancedBedrockQueryProcessor()
        self.mcp_client = OfficialMCPClient()
        
        self.models = ["claude-opus-4-1", "claude-sonnet-4"]
        
        # Comprehensive test queries across all difficulty levels
        self.test_queries = [
            # easy queries - Basic service cost requests
            {
                "query": "What are my EC2 costs?",
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
                "query": "What did I spend on RDS?",
                "difficulty": "EASY",
                "expected_service": "Amazon Relational Database Service",
                "description": "RDS cost inquiry"
            },
            {
                "query": "Lambda costs for this month",
                "difficulty": "EASY",
                "expected_service": "AWS Lambda",
                "description": "Current month Lambda costs"
            },
            
            # medium queries - Time-based and grouped requests
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
                "query": "EC2 costs grouped by instance type",
                "difficulty": "MEDIUM",
                "expected_service": "Amazon Elastic Compute Cloud - Compute",
                "description": "EC2 costs with grouping"
            },
            {
                "query": "S3 storage costs vs data transfer costs",
                "difficulty": "MEDIUM",
                "expected_service": "Amazon Simple Storage Service",
                "description": "S3 cost breakdown by usage type"
            },
            
            # hard-ish queries - Comparisons and complex time ranges
            {
                "query": "Compare EC2 costs between last month and this month",
                "difficulty": "HARD",
                "expected_service": "Amazon Elastic Compute Cloud - Compute",
                "description": "Month-over-month EC2 comparison"
            },
            {
                "query": "Show me daily EC2 costs for the past 2 weeks",
                "difficulty": "HARD",
                "expected_service": "Amazon Elastic Compute Cloud - Compute",
                "description": "Daily granularity with custom date range"
            },
            {
                "query": "What's driving the increase in my RDS costs?",
                "difficulty": "HARD",
                "expected_service": "Amazon Relational Database Service",
                "description": "Cost driver analysis"
            },
            {
                "query": "Forecast my S3 costs for next 3 months",
                "difficulty": "HARD",
                "expected_service": "Amazon Simple Storage Service",
                "description": "Cost forecasting"
            },
            
            # hardest queries - Purchase types and advanced analysis
            {
                "query": "Show me amortized costs vs unblended costs for reserved instances",
                "difficulty": "EXPERT",
                "expected_purchase_type": "Standard Reserved Instances",
                "description": "Cost metric comparison for reserved instances"
            },
            {
                "query": "Compare on-demand vs reserved instance costs for EC2",
                "difficulty": "EXPERT",
                "expected_service": "Amazon Elastic Compute Cloud - Compute",
                "description": "Purchase type comparison"
            },
            {
                "query": "What are my savings from reserved instances vs on-demand pricing?",
                "difficulty": "EXPERT",
                "expected_purchase_type": "Standard Reserved Instances",
                "description": "Savings analysis"
            },
            {
                "query": "Show me cost allocation by cost center tags for EC2 instances",
                "difficulty": "EXPERT",
                "expected_service": "Amazon Elastic Compute Cloud - Compute",
                "description": "Tag-based cost allocation"
            }
        ]

    async def run_single_query(self, model: str, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single query and measure performance"""
        query = query_info["query"]
        print(f"{model}: {query[:50]}")
        
        start_time = time.time()
        success = False
        error_msg = None
        result = None
        
        try:
            # Test the enhanced processor
            parsed_query = await self.enhanced_processor.process_query(query, model=model)
            success = True
            result = parsed_query
            
        except Exception as e:
            error_msg = str(e)
            print(f"Error: {error_msg}")
            
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000
        
        # Analyze query quality
        quality_analysis = self._analyze_query_quality(result, query_info)
        
        print(f"{response_time_ms:.0f}ms | {quality_analysis['analysis']}")
        
        return {
            "model": model,
            "query": query,
            "difficulty": query_info["difficulty"],
            "description": query_info["description"],
            "expected_service": query_info.get("expected_service"),
            "expected_purchase_type": query_info.get("expected_purchase_type"),
            "response_time_ms": response_time_ms,
            "success": success,
            "error": error_msg,
            "result": result,
            "quality_analysis": quality_analysis,
            "timestamp": datetime.now().isoformat()
        }

    def _analyze_query_quality(self, result: Dict[str, Any], query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the quality and correctness of the query result"""
        if not result:
            return {
                "quality_score": 0,
                "has_filter": False,
                "correct_service_names": False,
                "correct_purchase_types": False,
                "matches_expected": False,
                "issues": ["Query failed"],
                "analysis": "Failed"
            }
        
        # Handle case where result is a list (multiple queries) - use first item
        if isinstance(result, list):
            result = result[0] if result else {}
        
        parameters = result.get("parameters", {})
        filter_expr = parameters.get("filter_expression", {})
        
        analysis = {
            "quality_score": 20,  # Base score for success
            "has_filter": bool(filter_expr),
            "correct_service_names": True,
            "correct_purchase_types": True,
            "matches_expected": False,
            "issues": []
        }
        
        # Check if filter is present when expected
        expected_service = query_info.get("expected_service")
        expected_purchase_type = query_info.get("expected_purchase_type")
        
        if expected_service or expected_purchase_type:
            if analysis["has_filter"]:
                analysis["quality_score"] += 30
            else:
                analysis["issues"].append("Missing expected filter")
        
        # Analyze filter content if present
        if filter_expr and "Dimensions" in filter_expr:
            dimensions = filter_expr["Dimensions"]
            
            # Check service names
            if dimensions.get("Key") == "SERVICE":
                values = dimensions.get("Values", [])
                
                # Check for shortcuts (should be fixed by enhanced processor)
                for value in values:
                    if value in ["EC2", "RDS", "S3", "Lambda"]:
                        analysis["correct_service_names"] = False
                        analysis["issues"].append(f"Uses shortcut '{value}'")
                    
                # Check if matches expected service
                if expected_service and expected_service in values:
                    analysis["matches_expected"] = True
                    analysis["quality_score"] += 30
                elif expected_service:
                    analysis["issues"].append(f"Expected '{expected_service}' not found")
                    
            # Check purchase types
            elif dimensions.get("Key") == "PURCHASE_TYPE":
                values = dimensions.get("Values", [])
                
                # Check for incorrect terminology (should be fixed by enhanced processor)
                for value in values:
                    if value == "Reserved":
                        analysis["correct_purchase_types"] = False
                        analysis["issues"].append("Uses 'Reserved' instead of 'Standard Reserved Instances'")
                
                # Check if matches expected purchase type
                if expected_purchase_type and expected_purchase_type in values:
                    analysis["matches_expected"] = True
                    analysis["quality_score"] += 30
                elif expected_purchase_type:
                    analysis["issues"].append(f"Expected '{expected_purchase_type}' not found")
        
        # Bonus points for correct terminology
        if analysis["correct_service_names"]:
            analysis["quality_score"] += 10
        if analysis["correct_purchase_types"]:
            analysis["quality_score"] += 10
        
        # Generate analysis summary
        if analysis["quality_score"] >= 90:
            analysis["analysis"] = f"Excellent ({analysis['quality_score']}/100)"
        elif analysis["quality_score"] >= 70:
            analysis["analysis"] = f"Good ({analysis['quality_score']}/100)"
        elif analysis["quality_score"] >= 50:
            analysis["analysis"] = f"Fair ({analysis['quality_score']}/100)"
        else:
            analysis["analysis"] = f"Poor ({analysis['quality_score']}/100)"
        
        return analysis

    async def run_benchmark(self) -> Dict[str, Any]:
        """Run benchmark for Claude 4.1 Opus and Claude Sonnet 4"""
        print("MODEL BENCHMARK")
        print("Testing Claude 4.1 Opus vs Claude Sonnet 4")
        print("=" * 60)
        
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
        
        # Generate comprehensive summary
        summary = self._generate_summary(all_results)
        
        return {
            "benchmark_results": all_results,
            "summary": summary,
            "models_tested": self.models,
            "total_queries_per_model": len(self.test_queries),
            "timestamp": datetime.now().isoformat()
        }

    def _generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate comprehensive summary comparing both models"""
        summary = {}
        
        for model in self.models:
            model_results = [r for r in results if r["model"] == model]
            success_results = [r for r in model_results if r["success"]]
            
            if success_results:
                summary[model] = {
                    "total_queries": len(model_results),
                    "successful_queries": len(success_results),
                    "success_rate": len(success_results) / len(model_results),
                    "avg_response_time_ms": statistics.mean([r["response_time_ms"] for r in success_results]),
                    "avg_quality_score": statistics.mean([r["quality_analysis"]["quality_score"] for r in success_results]),
                    "min_response_time": min([r["response_time_ms"] for r in success_results]),
                    "max_response_time": max([r["response_time_ms"] for r in success_results]),
                    "response_time_std": statistics.stdev([r["response_time_ms"] for r in success_results]) if len(success_results) > 1 else 0
                }
                
                # Quality by difficulty
                by_difficulty = {}
                for result in success_results:
                    diff = result["difficulty"]
                    if diff not in by_difficulty:
                        by_difficulty[diff] = {"times": [], "qualities": []}
                    by_difficulty[diff]["times"].append(result["response_time_ms"])
                    by_difficulty[diff]["qualities"].append(result["quality_analysis"]["quality_score"])
                
                summary[model]["by_difficulty"] = {}
                for diff, data in by_difficulty.items():
                    summary[model]["by_difficulty"][diff] = {
                        "avg_time_ms": statistics.mean(data["times"]),
                        "avg_quality": statistics.mean(data["qualities"]),
                        "count": len(data["times"])
                    }
        
        return summary

    def print_comprehensive_results(self, results: Dict[str, Any]):
        """Print comprehensive benchmark results"""
        print("\n" + "=" * 80)
        print("COMPREHENSIVE BENCHMARK RESULTS")
        print("=" * 80)
        
        summary = results["summary"]
        
        # Overall comparison table
        print(f"\n{'Metric':<25} {'Claude 4.1 Opus':<20} {'Claude Sonnet 4':<20} {'Winner':<15}")
        print("-" * 85)
        
        opus_data = summary.get("claude-opus-4-1", {})
        sonnet_data = summary.get("claude-sonnet-4", {})
        
        # Success Rate
        opus_success = opus_data.get("success_rate", 0) * 100
        sonnet_success = sonnet_data.get("success_rate", 0) * 100
        success_winner = "Opus" if opus_success > sonnet_success else "Sonnet" if sonnet_success > opus_success else "Tie"
        print(f"{'Success Rate':<25} {opus_success:>15.1f}%    {sonnet_success:>15.1f}%    {success_winner:<15}")
        
        # Quality Score
        opus_quality = opus_data.get("avg_quality_score", 0)
        sonnet_quality = sonnet_data.get("avg_quality_score", 0)
        quality_winner = "Opus" if opus_quality > sonnet_quality else "Sonnet" if sonnet_quality > opus_quality else "Tie"
        print(f"{'Quality Score':<25} {opus_quality:>15.1f}      {sonnet_quality:>15.1f}      {quality_winner:<15}")
        
        # Response Time (lower is better)
        opus_time = opus_data.get("avg_response_time_ms", 0)
        sonnet_time = sonnet_data.get("avg_response_time_ms", 0)
        time_winner = "Sonnet" if sonnet_time < opus_time else "Opus" if opus_time < sonnet_time else "Tie"
        print(f"{'Avg Response Time':<25} {opus_time:>12.0f}ms    {sonnet_time:>12.0f}ms    {time_winner:<15}")
        
        # Performance by difficulty
        print(f"\n sPERFORMANCE BY DIFFICULTY")
        print("-" * 60)
        
        for difficulty in ["EASY", "MEDIUM", "HARD", "EXPERT"]:
            print(f"\n{difficulty}:")
            
            opus_diff = opus_data.get("by_difficulty", {}).get(difficulty, {})
            sonnet_diff = sonnet_data.get("by_difficulty", {}).get(difficulty, {})
            
            if opus_diff and sonnet_diff:
                print(f"  Quality:  Opus {opus_diff.get('avg_quality', 0):.1f} | Sonnet {sonnet_diff.get('avg_quality', 0):.1f}")
                print(f"  Time:     Opus {opus_diff.get('avg_time_ms', 0):.0f}ms | Sonnet {sonnet_diff.get('avg_time_ms', 0):.0f}ms")
        
        # Final recommendation
        print(f"\n RECOMMENDATION")
        print("-" * 30)
        
        if opus_quality > sonnet_quality + 5:  # Significant quality difference
            print("Claude 4.1 Opus - Superior accuracy justifies longer response time")
            print("Best for: Production environments where accuracy is critical")
        elif sonnet_time < opus_time * 0.7 and abs(opus_quality - sonnet_quality) < 5: 
            print("Claude Sonnet 4 - Good balance of speed and accuracy")
            print("Best for: Interactive applications where response time matters")
        else:
            print("Both models have trade-offs - choose based on your priorities:")
            print(f"• Opus: Higher accuracy ({opus_quality:.1f}) but slower ({opus_time:.0f}ms)")
            print(f"• Sonnet: Faster ({sonnet_time:.0f}ms) with good accuracy ({sonnet_quality:.1f})")

    def save_results(self, results: Dict[str, Any]) -> str:
        """Save benchmark results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n Results saved to: {filename}")
        return filename


async def main():
    """Run the benchmark"""
    benchmark = ModelBenchmark()
    
    print("Starting Model Benchmark")
    print("Comparing Claude 4.1 Opus vs Claude Sonnet 4 across all query types")
    
    # Run the benchmark
    results = await benchmark.run_benchmark()
    
    # Print comprehensive results
    benchmark.print_comprehensive_results(results)
    
    # Save results
    filename = benchmark.save_results(results)
    
    print(f"\n Benchmark completed!")
    print(f"Models tested: {', '.join(results['models_tested'])}")
    print(f"Queries per model: {results['total_queries_per_model']}")
    print(f"Detailed results: {filename}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())
    