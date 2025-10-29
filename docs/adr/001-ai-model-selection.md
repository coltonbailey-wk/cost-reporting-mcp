# ADR-001: AI Model Selection for Cost Explorer Application

## Status
**Updated** - October 27, 2025 (Benchmark results changed recommendation to Claude Sonnet 4)  
**Originally Accepted** - October 6, 2025

## Context

The AWS Cost Explorer Official MCP application requires AI models to provide intelligent natural language processing for cost analysis queries. The application must reliably convert natural language into accurate AWS Cost Explorer API parameters.

The application integrates with AWS Bedrock Claude models to provide:
- Natural language query understanding
- Intelligent parameter extraction and AWS Cost Explorer API call generation
- Service name recognition and proper terminology usage
- Filter construction for specific services and purchase types
- Date range interpretation and granularity selection

## Decision

Based on comprehensive parameter quality and performance testing (October 2025), we have updated our model recommendation:

### 1. Claude 4.1 Opus (Alternative/High-Complexity)
**Model ID:** `anthropic.claude-opus-4-1-20250805-v1:0`

**Strengths:**
- Excellent parameter quality and accuracy (98.1% quality score)
- Correctly uses full AWS service names (not shortcuts)
- Proper purchase type terminology
- Reliable filter generation for complex queries
- 100% success rate across all query types

**Performance Profile:**
- EASY queries: 15.9s average
- MEDIUM queries: 15.3s average
- HARD queries: 16.1s average
- EXPERT queries: 17.8s average

**Trade-off:** Equal quality to Sonnet but **3.6x slower** (16.3s vs 4.6s average)

**Recommendation:** Available for scenarios where maximum model capability is prioritized over response time


### 2. Claude Sonnet 4 (Secondary)
**Model ID:** `anthropic.claude-sonnet-4-20250514-v1:0`

**Strengths:**
- Significantly faster response times (4.6s vs 16.3s average) - **3.6x faster than Opus**
- Equal parameter quality to Opus (98.1% quality score)
- 100% success rate across all query types
- Excellent performance on complex queries

**Performance Profile:**
- EASY queries: 3.8s average
- MEDIUM queries: 4.0s average  
- HARD queries: 3.9s average
- EXPERT queries: 6.6s average

**Recommendation:** **Recommended as primary model** for most use cases given equal quality with significantly better performance


### 3. Claude 3.5 Haiku (Removed)
**Model ID:** `anthropic.claude-3-5-haiku-20241022-v1:0`

**Status:** Removed from production

**Critical Issues:**
- Consistently fails to generate correct filter expressions
- Ignores user filtering intent
- Returns unfiltered results for all AWS services regardless of query
- 0% accuracy on parameter quality tests

**Recommendation:** Not suitable for cost analysis use cases


## Supporting Evidence

### Benchmark Methodology

**Test Type:** Parameter Quality Benchmark

The benchmark evaluates how well each model generates AWS Cost Explorer API parameters, not the accuracy of returned cost data. This is a reasonable approach because AWS APIs are deterministic - correct parameters will yield accurate data.

**What the Benchmark Tests:**
- Parameter generation quality and structure
- AWS service name accuracy (full names vs shortcuts)
- Filter expression correctness
- Purchase type terminology precision
- Expected service/type matching in results

**What the Benchmark Does NOT Test:**
- Actual AWS cost data validation via boto3 calls
- Numeric accuracy of returned costs
- End-to-end data correctness against AWS Cost Explorer

**Test Queries:** 12 queries across 4 difficulty levels
- **EASY**: Basic service queries (EC2, RDS, S3, Lambda)
- **MEDIUM**: Time-based analysis (last month, current month)
- **HARD**: Complex analysis (cost comparisons, differences)
- **EXPERT**: Advanced scenarios (Reserved vs On-Demand)

**Scoring System:** 100-point scale per query
- Base Success (20 points): Query executes without errors
- Filter Presence (30 points): Correct filtering applied
- Service Names (10 points): Uses full AWS names
- Purchase Types (10 points): Correct terminology
- Expected Match (30 points): Returns expected service/type

### Benchmark Results Summary

**Model Performance Comparison (October 2025 Benchmark):**

| Model | Quality Score | Avg Response Time | Speed vs Opus | Success Rate | Recommendation |
|-------|--------------|-------------------|---------------|--------------|----------------|
| **Claude Sonnet 4** | 98.1% | 4.6 seconds | **Baseline** | 100% | **Primary/Recommended** |
| **Claude 4.1 Opus** | 98.1% | 16.3 seconds | 3.6x slower | 100% | Alternative option |
| **Claude 3.5 Haiku** | 0% | N/A | N/A | 0% | **Removed** |

**Key Findings (October 2025 Benchmark):**

1. **Claude Sonnet 4** demonstrates excellent parameter quality AND speed
   - 98.1% quality score (equal to Opus)
   - 100% success rate across all 16 test queries
   - 3.6x faster than Opus (4.6s vs 16.3s average)
   - Consistently generates correct AWS service names
   - Properly constructs filter expressions
   - Reliable across all query difficulty levels (EASY, MEDIUM, HARD, EXPERT)

2. **Claude 4.1 Opus** achieves equal quality but slower performance
   - 98.1% quality score (equal to Sonnet)
   - 100% success rate across all 16 test queries
   - Significantly slower responses (16.3s average)
   - Excellent parameter generation quality
   - No meaningful quality advantage over Sonnet in current testing

3. **Claude 3.5 Haiku** fails parameter quality requirements
   - Does not generate filter expressions correctly
   - Returns unfiltered results regardless of query intent
   - Not suitable for production cost analysis

### Cost Analysis

**AWS Bedrock Pricing (per 1K tokens):**
- **Claude 3.5 Haiku**: $0.00025 input / $0.00125 output (Removed from use)
- **Claude Sonnet 4**: $0.003 input / $0.015 output
- **Claude 4.1 Opus**: $0.015 input / $0.075 output

**Cost-Quality Analysis:**
- **Claude 4.1 Opus**: Higher cost per token, but superior accuracy justifies the expense for cost analysis
- **Claude Sonnet 4**: Lower cost, but inconsistent parameter quality may lead to incorrect results
- **Claude 3.5 Haiku**: Cheapest option, but 0% accuracy makes it unusable regardless of price

**Decision:** Accuracy is more important than cost for financial analysis tooling. Using an incorrect model that generates wrong parameters could lead to incorrect cost insights, which is unacceptable.

### Integration Benefits

**AWS Bedrock Advantages:**
- **Zero Configuration**: Uses existing AWS credentials
- **Low Latency**: Stays within AWS network infrastructure
- **Cost Tracking**: Integrated with existing AWS billing
- **Security**: No additional API key management required
- **Reliability**: AWS-managed service with high availability

## Alternative Considered: Google Gemini

### Why Gemini Was Not Selected

**Technical Limitations:**
1. **External API Dependency**: Requires separate API keys and external network calls
2. **Latency Impact**: Additional network hops outside AWS infrastructure
3. **Cost Tracking Complexity**: Separate billing system outside AWS ecosystem
4. **Security Concerns**: Additional API key management and rotation requirements

**Integration Challenges:**
1. **Authentication Complexity**: Would require Google Cloud credentials alongside AWS
2. **Network Latency**: External API calls add 200-500ms overhead
3. **Reliability**: Additional external dependency point of failure
4. **Maintenance**: Separate SDK and authentication management

**Cost Analysis:**
- **Gemini Pro**: $0.0005 input / $0.0015 output per 1K tokens
- While potentially cheaper per token, the operational overhead and latency costs outweigh savings
- External billing adds administrative complexity

**Performance Comparison:**
- **Query Understanding**: Claude Sonnet 4 achieves 98.1% accuracy in benchmark testing
- **AWS-Specific Context**: Claude models show better understanding of AWS cost terminology
- **Response Time**: External APIs add 2-4s overhead vs 4.6s for Claude Sonnet 4 (measured)

### Response Time Considerations

**Measured Response Times (October 2025 Benchmark):**
- **Claude Sonnet 4**: 4.6s average (3.8-6.6s range) - **Recommended**
- **Claude 4.1 Opus**: 16.3s average (13.4-22.4s range) - 3.6x slower
- **Claude 3.5 Haiku**: Not tested (removed due to quality issues)

**Performance AND Accuracy Achievement:**
- October 2025 testing shows **no tradeoff needed** - Sonnet 4 delivers both
- Both models achieve 98.1% quality score with 100% success rate
- Sonnet 4 is 3.6x faster while maintaining equal quality
- For cost analysis, we can have both speed AND accuracy

### Usage Pattern

**Default Behavior (Updated October 2025):**
- **Claude Sonnet 4 is now the recommended default** for all queries
- Delivers equal quality (98.1%) with significantly better performance (3.6x faster)

**User Options:**
- Users can optionally select Claude 4.1 Opus if maximum model capability is desired
- Both models achieve 100% success rate and equal parameter quality
- No option for Haiku due to reliability issues

## Consequences

### Positive
1. **Optimal Performance**: Claude Sonnet 4 as default delivers both speed AND accuracy
2. **No Trade-offs**: 98.1% quality with 3.6x better performance than Opus
3. **100% Success Rate**: Both models achieve perfect reliability across all query types
4. **User Choice**: Opus available for users who prefer maximum model capability
5. **AWS Integration**: Seamless integration with existing AWS infrastructure
6. **Validated Selection**: Comprehensive benchmark (16 queries) validates recommendation
7. **Security**: No additional credential management required

### Negative
1. **AWS Vendor Lock-in**: Tied to AWS Bedrock service availability
2. **Reduced Options**: Haiku removed due to quality issues
3. **Token Costs**: Both models have associated per-token costs (Sonnet more cost-effective)

### Mitigation Strategies
1. **Cost Efficiency**: Sonnet 4 as default provides best cost-per-query value
2. **Optional Opus**: Available for scenarios requiring maximum capability
3. **Enhanced Processor**: Auto-correction ensures high quality across both models
4. **Clear Documentation**: Users understand both models deliver equal quality

## Stakeholder Alignment

### Business Stakeholders
- **Data Accuracy**: Prioritizes correct cost analysis over speed or cost
- **Risk Mitigation**: Reliable parameter generation prevents incorrect financial insights
- **AWS Integration**: Leverages existing AWS infrastructure and billing

### Technical Stakeholders
- **Quality Metrics**: Benchmark provides quantitative validation of model selection
- **Maintainability**: AWS Bedrock simplifies model deployment and updates
- **Scalability**: AWS-managed service handles scaling automatically
- **Error Handling**: Enhanced processor provides auto-correction for common mistakes

### End Users
- **Reliability**: Default model prioritizes accurate results
- **Flexibility**: Option to choose faster model if acceptable
- **Trust**: Parameter quality testing validates model capabilities

## Future Improvements

### Benchmark Enhancements
Current benchmarks test parameter quality. Future enhancements could include:

1. **Data Validation Testing**
   - Compare model-generated results against direct boto3 AWS Cost Explorer calls
   - Validate numeric accuracy of returned cost data
   - Ensure filtered results match expected real-world data
   - Test end-to-end data accuracy

2. **Expanded Test Coverage**
   - Increase test suite to 50+ queries
   - Add edge cases and error scenarios
   - Test tag-based filtering extensively
   - Include Workiva-specific use cases

3. **Performance Monitoring**
   - Track response times in production
   - Monitor user model selection patterns
   - Measure actual AWS Bedrock costs by model
   - Document user satisfaction by model choice

### Monitoring and Metrics
Production monitoring should track:
- Parameter quality scores by model
- Query success/failure rates
- Response time distributions (p50, p95, p99)
- Cost per query by model
- User model selection preferences

## Review Date
This decision should be reviewed by **April 2026** or when:
- New Claude models become available in AWS Bedrock
- Significant changes in model performance or quality observed
- Changes in AWS Bedrock pricing significantly alter cost-performance tradeoffs
- Production data indicates different usage patterns than benchmarks predict
- User feedback suggests different model preferences

## Revision History

### October 27, 2025 - Model Recommendation Update
**Changed recommendation from Claude 4.1 Opus to Claude Sonnet 4 based on benchmark results**

**Benchmark Details:**
- Test Date: October 27, 2025
- Test Queries: 16 queries across 4 difficulty levels (EASY, MEDIUM, HARD, EXPERT)
- Success Rate: Both models 100%
- Quality Score: Both models 98.1%
- Performance: Sonnet 4 is 3.6x faster (4.6s vs 16.3s average)

**Key Finding:** Sonnet 4 achieves equal parameter quality to Opus while being significantly faster, eliminating the need for a quality vs. speed trade-off.

**Results File:** `test/benchmark_results_20251027_134514.json`
