# AWS Bedrock Claude Integration

**Primary and exclusive LLM integration** - streamlined for optimal performance  
**No additional API keys needed** - uses AWS credentials  
**Already in your account** - leverages existing AWS infrastructure
**Lower latency** - stays within AWS infrastructure  
**Cost tracking** - appears in your AWS billing
**Enhanced intelligence** - powers smart query understanding and natural language explanations  


## **Auto-Detection**

The application now **automatically detects and uses AWS Bedrock Claude** when you start the server:

```bash
./start_official_mcp.sh
```

You'll see this message:
```
AWS Bedrock Claude Query Processor initialized
   Using your existing AWS credentials - no additional API keys needed!
```

## **Available Models**

Based on comprehensive parameter quality benchmarking, the integration uses two Claude models:

| Model | Bedrock ID | Quality Score | Avg Response Time | Success Rate | Best For |
|-------|------------|--------------|-------------------|--------------|----------|
| **Claude Sonnet 4** | `anthropic.claude-sonnet-4-20250514-v1:0` | **98.1%** | **4.6s** | **100%** | **All queries (recommended)** |
| **Claude 4.1 Opus** | `anthropic.claude-opus-4-1-20250805-v1:0` | 98.1% | 16.3s | 100% | Alternative |

**Default Model**: Claude Sonnet 4 *(Updated October 2025 based on benchmark results)*
- 98.1% parameter quality score (equal to Opus)
- 3.6x faster than Opus (4.6s vs 16.3s average)
- 100% success rate across all query types
- Consistently generates correct AWS service names
- Proper filter expression construction
- Accurate purchase type terminology
- Reliable across all query complexity levels (EASY, MEDIUM, HARD, EXPERT)

**Why Sonnet 4?** October 2025 benchmarking revealed that Sonnet 4 achieves **equal parameter quality** to Opus while being **significantly faster**. For cost analysis, we can now have both accuracy AND performance.

**Claude 3.5 Haiku**: Removed from production due to 0% parameter quality accuracy. Cannot reliably generate correct filter expressions.

## **Model Selection & Quality**

### **Parameter Quality Testing**

The application uses a comprehensive benchmark to validate model selection:

**What's Tested:**
- AWS service name accuracy (full names vs shortcuts)
- Filter expression correctness
- Purchase type terminology precision
- Parameter structure and validation

**Scoring:** Each query scored on 100-point scale
- Base Success (20 pts): Query executes without errors
- Filter Presence (30 pts): Correct filtering applied
- Service Names (10 pts): Full AWS names used
- Purchase Types (10 pts): Correct terminology
- Expected Match (30 pts): Returns expected results

**Results (October 2025):** Both Claude Sonnet 4 and Opus achieve ~98.1% parameter quality, with Sonnet 4 being 3.6x faster (4.6s vs 16.3s average).

## **Cost & Performance Benefits**

| Benefit | AWS Bedrock Claude | External APIs |
|---------|-------------------|---------------|
| **Setup** | Zero configuration needed | Requires API keys |
| **Latency** | Low (within AWS network) | Higher (internet roundtrip) |
| **Cost Tracking** | Integrated with AWS billing | Separate billing systems |
| **Security** | Uses existing AWS credentials | Additional API key management |
| **Infrastructure** | Leverages existing AWS footprint | External dependencies |
| **Quality** | Benchmark-validated accuracy | Unvalidated performance |

**Result**: Streamlined integration with existing AWS infrastructure, validated accuracy, and no additional authentication complexity

## **Enhanced Query Examples**

With Bedrock Claude, these queries become much smarter:

### **Before (Keywords)**
```
Query: "EC2 costs last quarter"
Generic date parsing, basic SERVICE filter
```

### **After (Bedrock Claude)**
```
Query: "EC2 costs last quarter"
Intelligent Q3 2024 identification
Includes EC2, EBS, data transfer costs
Suggests appropriate visualizations
Natural language explanation
```

### **Complex Queries Now Work:**
```
"Why did my storage costs spike 40% in September?"
Compares Aug vs Sep, identifies S3/EBS drivers, provides AI explanation

"Show me a breakdown of compute vs storage vs networking costs"
Groups related services intelligently, recommends optimal visualization

"Forecast my AWS costs for next month"
Creates sparkline forecast by default with confidence intervals

"What will my database costs be if usage grows 20%?"
Analyzes historical patterns and provides intelligent projections

"Show me net amortized costs for EC2 in Q3"
Automatically detects metric type and time period, ensures complete months
```

## **IAM Permissions**

Make sure your AWS role has Bedrock permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": [
                "arn:aws:bedrock:*::foundation-model/anthropic.claude*"
            ]
        }
    ]
}
```

## **Test Your Integration**

1. **Restart your server**:
   ```bash
   ./start_official_mcp.sh
   ```

2. **Look for this message**:
   ```
   AWS Bedrock Claude Query Processor initialized
   ```

3. **Test complex queries in your dashboard**:
   - `"Compare my EC2 costs in Q2 vs Q3 2024"`
   - `"Why did my AWS bill increase 15% last month?"`
   - `"What storage services am I using and how much do they cost?"`
   - `"Forecast my database costs for next quarter"`

## **Intelligent Processing & Fallbacks**

The system uses a robust processing pipeline:

1. **Meta Query Pre-processing**: Catches system queries like "what can you do?" before LLM processing
2. **Primary Processing**: AWS Bedrock Claude for natural language understanding
3. **Error Handling**: Graceful fallback with user-friendly error messages
4. **Final Fallback**: Keyword-based processing for basic queries if Bedrock is unavailable

**Enhanced Features:**
- **Smart Metric Detection**: Recognizes "net amortized costs", "unblended costs", etc.
- **Complete Month Validation**: Ensures comparison queries use only complete months
- **Dynamic Date Templates**: All date examples are dynamically generated (no hardcoded dates)
- **Query Context Preservation**: Unique query IDs prevent caching issues

## **Pro Tips**

### **Query Optimization**
- **Forecasts**: Default to sparklines for quick insights, request "detailed cards" for comprehensive analysis
- **Metrics**: Use "net amortized costs" (default) for accurate cost attribution 
- **Comparisons**: Use complete months (e.g., "July vs August") for accurate comparisons
- **Visualizations**: Request specific chart types like "sparkline", "timeline", or "bar chart"

### **Advanced Features**
- **Natural Language**: Ask complex questions like "Why did my bill increase?" for AI-powered analysis
- **Capabilities Modal**: Click "Capabilities" button for comprehensive feature guide and examples
- **Error Recovery**: System gracefully handles Bedrock errors with informative fallbacks

### **Performance & Cost**
- **Processing Speed**: Claude Sonnet 4 recommended (4.6s average, ~3.6x faster than Opus)
- **Cost Efficiency**: Sonnet 4 provides best cost-per-query value with equal quality
- **Best of Both**: Sonnet 4 delivers both speed AND accuracy (98.1% quality score)
- **User Choice**: Opus available for scenarios requiring maximum model capability

## **Ready to Use!**

The enhanced AWS Cost Explorer dashboard is now a fully-featured, cost analysis platform:

**Key Achievements:**
- **Benchmark-Validated Model Selection**: Claude Sonnet 4 recommended (Oct 2025) - 98.1% quality, 3.6x faster than Opus
- **AWS Bedrock Integration**: Streamlined, no external dependencies
- **Accurate Parameter Generation**: 100% success rate with consistently correct AWS service names and filters
- **Enhanced Query Processing**: Auto-correction for common terminology mistakes
- **Comprehensive Testing**: 16-query benchmark validates equal quality with superior performance
- **Production Quality**: Clean codebase with comprehensive documentation

**Perfect for:**
- Accurate financial cost analysis with reliable parameters
- Complex queries requiring proper AWS terminology
- Tag-based cost filtering and organization
- Cost optimization research with intelligent comparisons
- Executive reporting requiring data accuracy

The system leverages your existing AWS infrastructure while providing benchmark-validated, enterprise-grade cost analysis capabilities.
