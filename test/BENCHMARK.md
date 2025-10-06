# Test Suite

This directory contains all testing and benchmarking tools for the AWS Cost Explorer MCP server.

## Test Files

### Benchmarking
- `benchmark.py` - **Main benchmark script** for Claude 4.1 Opus vs Claude 3.5 Sonnet

## Running the Benchmark

### Benchmark
```bash
cd test/
python benchmark.py
```

This comprehensive benchmark tests both Claude 4.1 Opus and Claude 3.5 Sonnet across all query difficulties:
- **EASY**: Basic service cost queries (EC2, RDS, S3, Lambda)
- **MEDIUM**: Time-based and grouped requests (last month, current month)
- **HARD**: Comparisons and complex analysis (cost differences, aggregations)
- **EXPERT**: Purchase types and advanced scenarios (Reserved vs On-Demand)

### Output
The benchmark generates:
- JSON results file with detailed metrics
- Comprehensive performance comparison
- Quality analysis for each query
- Response time statistics
- Accuracy scoring and recommendations

## Test Query Types

The benchmark includes 12 test queries across four difficulty levels:

### EASY (Basic Service Queries)
- EC2, RDS, S3, Lambda cost queries
- Tests basic service name recognition

### MEDIUM (Time-Based Queries)
- Last month and current month analysis
- Tests date range handling and grouping

### HARD (Complex Analysis)
- Cost comparisons and differences
- Tests complex filter combinations

### EXPERT (Advanced Scenarios)
- Reserved vs On-Demand instance comparisons
- Tests purchase type terminology and advanced filtering

## Validation Approach

### What This Benchmark Tests

This benchmark is a **parameter quality test** that evaluates how well each model generates AWS Cost Explorer API parameters. It focuses on:

- **Parameter Generation Quality**: Does the model create valid, well-formed API parameters?
- **Service Name Accuracy**: Does it use full AWS service names instead of shortcuts?
- **Filter Correctness**: Does it apply appropriate filters for the query?
- **Terminology Precision**: Does it use correct AWS terminology (e.g., "Standard Reserved Instances")?

### What This Benchmark Does NOT Test

This benchmark does **not** validate the actual cost data returned by AWS. It does not:

- Make boto3 calls to compare actual AWS cost data
- Verify that the numeric costs returned are accurate
- Validate that filtered results match expected real-world data
- Test end-to-end data accuracy against AWS Cost Explorer

The benchmark assumes that if the LLM generates correct parameters (proper service names, filters, and structure), the AWS Cost Explorer API will return accurate data. This is a reasonable assumption since AWS APIs are deterministic.

TODO: create test suite to compare returned results from MCP against boto calls

## Scoring System

Each query is evaluated on a 100-point scale:

- **Base Success** (20 points): Query executes without errors
- **Filter Presence** (30 points): Correct filtering applied for specific services
- **Service Names** (10 points): Uses full AWS service names (e.g., "Amazon Elastic Compute Cloud - Compute" not "EC2")
- **Purchase Types** (10 points): Correct terminology (e.g., "Standard Reserved Instances" not "Reserved")
- **Expected Match** (30 points): Returns expected service or purchase type in results

## Requirements

- Python 3.8+
- AWS credentials configured
- Access to AWS Bedrock Claude models
- boto3 installed

## Results Location

Benchmark results are saved as JSON files with timestamps:
- Format: `benchmark_results_YYYYMMDD_HHMMSS.json`
- Contains detailed metrics for each model and query
- Includes quality scores, response times, and validation results
