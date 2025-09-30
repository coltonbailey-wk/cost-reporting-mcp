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

The integration uses stable, production-tested Claude models in Bedrock:

| Model | Bedrock ID | Best For | Status |
|-------|------------|----------|---------|
| **Claude 3.5 Sonnet** | `anthropic.claude-3-5-sonnet-20240620-v1:0` | General queries (default) |
| **Claude 3 Opus** | `anthropic.claude-3-opus-20240229-v1:0` | Complex analysis |
| **Claude 3 Sonnet** | `anthropic.claude-3-sonnet-20240229-v1:0` | Balanced performance |
| **Claude 3 Haiku** | `anthropic.claude-3-haiku-20240307-v1:0` | Quick responses |

**Note**: The system automatically uses Claude 3.5 Sonnet as the default model, optimized for cost analysis queries and natural language explanations.

## **Cost & Performance Benefits**

| Benefit | AWS Bedrock Claude | External APIs |
|---------|-------------------|---------------|
| **Setup** | Zero configuration needed | Requires API keys |
| **Latency** | Low (within AWS network) | Higher (internet roundtrip) |
| **Cost Tracking** | Integrated with AWS billing | Separate billing systems |
| **Security** | Uses existing AWS credentials | Additional API key management |
| **Infrastructure** | Leverages existing AWS footprint | External dependencies |

**Result**: Streamlined integration with existing AWS infrastructure and no additional authentication complexity

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
→ Compares Aug vs Sep, identifies S3/EBS drivers, provides AI explanation

"Show me a breakdown of compute vs storage vs networking costs"
→ Groups related services intelligently, recommends optimal visualization

"Forecast my AWS costs for next month"
→ Creates sparkline forecast by default with confidence intervals

"What will my database costs be if usage grows 20%?"
→ Analyzes historical patterns and provides intelligent projections

"Show me net amortized costs for EC2 in Q3"
→ Automatically detects metric type and time period, ensures complete months
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
- **Processing Speed**: ~1-2 seconds for most queries within AWS network
- **Cost Efficiency**: Leverages existing AWS Bedrock usage with minimal incremental cost
- **Smart Caching**: Unique query IDs prevent stale data issues

## **Ready to Use!**

The enhanced AWS Cost Explorer dashboard is now a fully-featured, production-ready cost analysis platform:

**Key Achievements:**
- **Exclusive AWS Bedrock Claude Integration**: Streamlined, no external dependencies
- **Forecast Sparklines**: Default compact visualization with detailed cards on request  
- **Comprehensive UI**: Professional interface with capabilities modal and optimized layout
- **Smart Query Processing**: Context-aware understanding with intelligent fallbacks
- **Production Quality**: Linted, formatted code with comprehensive documentation

**Perfect for:**
- Quick daily cost insights with sparkline trends
- Deep-dive analysis with AI-powered explanations  
- Executive reporting with professional visualizations
- Cost optimization research with intelligent comparisons

The system leverages your existing AWS infrastructure while providing enterprise-grade cost analysis capabilities.
