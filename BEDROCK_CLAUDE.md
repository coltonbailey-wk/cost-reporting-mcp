# AWS Bedrock Claude Integration

**No additional API keys needed** - uses AWS credentials  
**Already in your account** - already in use at Workiva
**Lower latency** - stays within AWS infrastructure  
**Cost tracking** - appears in your AWS billing  


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

The integration supports these Claude models in Bedrock:
TODO: Allow user to choose which model best suits their needs through UI

| Model | Bedrock ID | Best For |
|-------|------------|----------|
| **Claude 3.5 Sonnet** | `anthropic.claude-3-5-sonnet-20241022-v2:0` | General queries (recommended) |
| **Claude 3.5 Haiku** | `anthropic.claude-3-5-haiku-20241022-v1:0` | Fast, simple queries |
| **Claude 3 Opus** | `anthropic.claude-3-opus-20240229-v1:0` | Complex analysis |
| **Claude 3 Sonnet** | `anthropic.claude-3-sonnet-20240229-v1:0` | Balanced performance |
| **Claude 3 Haiku** | `anthropic.claude-3-haiku-20240307-v1:0` | Quick responses |

## **Cost Comparison**

| Option | Cost | Setup | Latency |
|--------|------|-------|---------|
| **AWS Bedrock Claude** | Already paying ~$643/month | Zero setup | Low (in AWS) |
| Direct Anthropic API | $3/1M tokens (~$0.003/query) | Requires API key | Higher |
| Google Gemini | $1/1M tokens (~$0.001/query) | Requires API key | Higher |

**Recommendation**: Stick with Bedrock since we're already using it heavily

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
→ Compares Aug vs Sep, identifies S3/EBS drivers, suggests optimizations

"Show me a breakdown of compute vs storage vs networking costs"
→ Groups related services intelligently, recommends pie chart

"What will my database costs be if usage grows 20%?"
→ Creates forecast with growth assumptions
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

## **Fallback Behavior**

The system has intelligent fallbacks:
1. **First choice**: AWS Bedrock Claude (using your AWS creds)
2. **Second choice**: Direct Anthropic API (if `ANTHROPIC_API_KEY` set)
3. **Third choice**: Google Gemini (if `GOOGLE_API_KEY` set)  
4. **Final fallback**: Keyword-based processing

## **Pro Tips**

### **Model Selection**
- **Default**: Claude 3.5 Sonnet (best balance)
- **Fast queries**: Switch to Claude 3.5 Haiku for speed
- **Complex analysis**: Use Claude 3 Opus for detailed insights

### **Cost Optimization**
- Adding query processing will be minimal additional cost
- Much cheaper than direct API calls at expected usage level

### **Performance**
- **Bedrock**: ~1-2 seconds (in AWS network)
- **External APIs**: ~2-4 seconds (internet roundtrip)

## **Ready to Use!**

The enhanced AWS Cost Explorer dashboard is now powered by the same Claude models we're already using.
