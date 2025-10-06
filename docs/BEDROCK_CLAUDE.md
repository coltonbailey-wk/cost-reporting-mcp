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

| Model | Bedrock ID | Parameter Quality | Speed | Best For |
|-------|------------|------------------|-------|----------|
| **Claude 4.1 Opus** | `anthropic.claude-opus-4-1-20250805-v1:0` | Highest accuracy | Slower | **All queries (default)** |
| **Claude 3.5 Sonnet** | `anthropic.claude-3-5-sonnet-20240620-v1:0` | Inconsistent | Faster | Optional for simple queries |

**Default Model**: Claude 4.1 Opus
- Consistently generates correct AWS service names
- Proper filter expression construction
- Accurate purchase type terminology
- Reliable across all query complexity levels

**Why Opus?** For financial cost analysis, parameter accuracy is more important than response speed. Incorrect parameters can lead to wrong cost insights, which is unacceptable for financial tooling.

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

**Results:** Claude 4.1 Opus demonstrates consistently superior parameter quality across all query types.

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
- **Processing Speed**: Claude 4.1 Opus is slower but prioritizes accuracy for financial data
- **Cost Efficiency**: Higher token cost justified by superior parameter quality
- **Quality First**: For cost analysis, accurate parameters matter more than response speed
- **User Choice**: Sonnet available as faster option with lower accuracy

## **Ready to Use!**

The enhanced AWS Cost Explorer dashboard is now a fully-featured, cost analysis platform:

**Key Achievements:**
- **Benchmark-Validated Model Selection**: Claude 4.1 Opus default based on parameter quality testing
- **AWS Bedrock Integration**: Streamlined, no external dependencies
- **Accurate Parameter Generation**: Consistently correct AWS service names and filters
- **Enhanced Query Processing**: Auto-correction for common terminology mistakes
- **Comprehensive Testing**: 100-point quality scoring validates all queries
- **Production Quality**: Clean codebase with comprehensive documentation

**Perfect for:**
- Accurate financial cost analysis with reliable parameters
- Complex queries requiring proper AWS terminology
- Tag-based cost filtering and organization
- Cost optimization research with intelligent comparisons
- Executive reporting requiring data accuracy

The system leverages your existing AWS infrastructure while providing benchmark-validated, enterprise-grade cost analysis capabilities.
