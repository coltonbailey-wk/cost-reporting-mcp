# AWS Cost Explorer Official MCP - Management Dashboard

A powerful web application that integrates with the **official AWS Cost Explorer MCP server** from [AWS Labs](https://github.com/awslabs/mcp/tree/main/src/cost-explorer-mcp-server) to provide comprehensive AWS cost analysis and management insights.

### **Official AWS Support**
- **Maintained by AWS Labs**: Official AWS support and updates
- **Standard MCP Protocol**: Full MCP specification compliance
- **Cost Explorer Integration**: Direct integration with AWS Cost Explorer API

### **Official MCP Tools Available**

The official AWS Cost Explorer MCP server provides these tools:

1. **get_today_date** - Get current date for time-based queries
2. **get_dimension_values** - Get available values for dimensions (SERVICE, REGION)
3. **get_tag_values** - Get available values for tag keys
4. **get_cost_and_usage** - Retrieve AWS cost and usage data
5. **get_cost_and_usage_comparisons** - Compare costs between time periods
6. **get_cost_comparison_drivers** - Analyze cost change drivers (top 10 most significant)
7. **get_cost_forecast** - Generate cost forecasts with confidence intervals

## **Quick Start**

### **Option 1: Easy Start**
```bash
cd cost-explorer-official-mcp
./start_official_mcp.sh
```

### **Option 2: Manual Start**
```bash
cd cost-explorer-official-mcp
pip3 install -r requirements.txt
python3 web_app.py
```

### **Access the Dashboard**
Open your browser and go to: **http://localhost:8002**

### **Quick Test Queries**
Try these queries immediately to see the enhanced features:

1. **Account Info**: `"Which AWS account is this getting data from?"`
2. **Help**: `"What can you do?"`
3. **Sparkline**: `"Give me a sparkline graph of monthly AWS charges this year"`
4. **Timeline**: `"Show me a timeline of costs for the last 6 months"`
5. **Bar Chart**: `"Create a bar chart of my AWS service costs"`

## **Smart Natural Language Understanding**

This dashboard features **basic query classification** that distinguishes between different types of questions and provides appropriate responses.
This is a work in progress, so it will not be able to answer all NLP queries.

### ** Account & System Information**
Get information about your AWS setup and dashboard capabilities:
- `"Which AWS account is this getting data from?"`
- `"What AWS account am I connected to?"`
- `"What region is this data from?"`
- `"Where is this data coming from?"`

### ** Help & Capabilities**
Learn what the dashboard can do:
- `"Help"`
- `"What can you do?"`
- `"What are your capabilities?"`
- `"What tools do you have?"`

### **Cost Analysis Queries**

#### **Basic Cost Analysis**
- `"Show me my AWS costs for the last 3 months grouped by service"`
- `"Break down my S3 costs by storage class for Q1 2025"`
- `"What were my costs for reserved instances vs on-demand in May?"`

#### **Cost Comparison**
- `"Compare my AWS costs between April and May 2025"`
- `"How did my EC2 costs change from last month to this month?"`
- `"Why did my AWS bill increase in June compared to May?"`

#### **Forecasting**
- `"Forecast my AWS costs for next month"`
- `"Predict my EC2 spending for the next quarter"`
- `"What will my total AWS bill be for the rest of 2025?"`

## **Enhanced Visualizations**

The dashboard supports **multiple chart types** with detection based on your query:

### ** Sparkline Charts**
Compact trend visualizations showing costs over time:
- `"Can you give me a sparkline graph of monthly AWS charges for each service this year?"`
- `"Show me sparklines for my top AWS services"`
- `"Create sparkline trends for my costs"`

### **Timeline Charts**
Multi-line time series charts for detailed trend analysis:
- `"Show me a timeline of AWS costs for the last 6 months"`
- `"Create a timeline chart of my EC2 costs"`
- `"Give me a line graph of daily AWS charges for the last 30 days"`

### **Bar Charts**
Service comparison with colorful bar visualizations:
- `"Create a bar chart of my AWS service costs"`
- `"Show me a bar graph of my top spending categories"`
- `"Give me bar charts for my monthly expenses"`

### ** Pie Charts & Tables**
Default comprehensive cost breakdowns (automatically chosen):
- `"Show me my AWS costs for the last 3 months"`
- `"What are my current AWS expenses?"`
- `"Break down my costs by service"`

## **Smart Date & Time Parsing**

The system parses time periods from your queries:

### **Time Periods**
- **"this year"** → January to current date
- **"last 6 months"** → 180 days of data
- **"last 3 months"** → 90 days of data  
- **"last 30 days"** → Daily granularity
- **"monthly"** → Monthly granularity
- **"daily"** → Daily granularity

### **Example Queries with Smart Parsing**
- `"Give me a sparkline of monthly AWS charges for each service this year"` 
  → **Sparklines + This Year + Monthly data**
- `"Show me a timeline of daily costs for the last 30 days"`
  → **Timeline + 30 days + Daily data**

## **Official MCP Features**

### **Cost Analysis**
- **Detailed breakdowns** by service, region, and other dimensions
- **Historical cost data** for specific time periods
- **Flexible filtering** by dimensions, tags, and cost categories
- **Multiple chart types**: Sparklines, timelines, bar charts, pie charts
- **Interactive visualizations** with hover tooltips and zoom

### **Cost Comparison (NEW AWS Feature)**
- **Leverage AWS Cost Explorer's new Cost Comparison feature**
- **Compare costs between two time periods** to identify changes and trends
- **Analyze cost drivers** to understand what caused cost increases or decreases
- **Get detailed insights** into the top 10 most significant cost change drivers automatically
- **Visual comparison charts** showing changes over time

### **Forecasting**
- **Generate cost forecasts** based on historical usage patterns
- **Get predictions with confidence intervals** (80% or 95%)
- **Support for daily and monthly** forecast granularity
- **Plan budgets** and anticipate future AWS spending
- **Interactive forecast charts** with trend lines

### **Smart Query Processing**
- **Intelligent query classification** (Cost Analysis vs Meta Questions)
- **Natural language date parsing** ("this year", "last 6 months", etc.)
- **Chart type detection** from keywords (sparkline, timeline, bar chart)
- **Account information queries** for system details
- **Context-aware responses** with appropriate visualizations

### **Easy User Interface**
- **Side-by-side panels**: Visual Analysis & Raw Data
- **Expandable sections** with toggle functionality
- **Real-time chart rendering** with Chart.js v4.4.0
- **Responsive design** that works on all devices
- **Color-coded information cards** for different query types

## **Architecture**

```
Web Browser → FastAPI App → Official AWS MCP Server → AWS Cost Explorer API
                ↓
            Natural Language Processing
                ↓
            Official AWS Analysis & Insights
```

## **Files Structure**

```
cost-explorer-official-mcp/
├── web_app.py                    # FastAPI web application
├── templates/
│   └── official_mcp_dashboard.html # Enhanced frontend
├── requirements.txt              # Dependencies
├── start_official_mcp.sh        # Easy startup script
└── README.md                    # This documentation
```

## **Security & Permissions**

### **Required IAM Permissions**
The official MCP server requires these IAM permissions:
- `ce:GetCostAndUsage`
- `ce:GetDimensionValues`
- `ce:GetTags`
- `ce:GetCostForecast`
- `ce:GetCostAndUsageComparisons`
- `ce:GetCostComparisonDrivers`

### **AWS Authentication**
The MCP server uses the AWS profile specified in the `AWS_PROFILE` environment variable:
```json
"env": {
  "AWS_PROFILE": "your-aws-profile",
  "AWS_REGION": "us-east-1"
}
```

## **Cost Considerations**

**Important:** AWS Cost Explorer API incurs charges on a per-request basis:
- **Cost Explorer API Pricing:** $0.01 per request
- Each tool invocation that queries Cost Explorer will generate at least one billable API request
- Complex queries with multiple filters or large date ranges may result in multiple API calls

For current pricing information, refer to the [AWS Cost Explorer Pricing page](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/).

## **Key Benefits of Official MCP**

| Feature | Custom MCP | Official AWS MCP |
|---------|------------|------------------|
| **Maintenance** | Custom implementation | Official AWS support |
| **Updates** | Manual updates needed | Automatic updates from AWS |
| **Features** | Basic cost analysis | Full Cost Explorer capabilities |
| **Cost Comparison** | Not available | NEW AWS feature |
| **Cost Drivers** | Not available | Top 10 drivers analysis |
| **Forecasting** | Basic | Advanced with confidence intervals |
| **Chart Types** | Basic tables | Sparklines, timelines, bar charts, pie charts |
| **Query Intelligence** | Simple keyword matching | Smart classification & date parsing |
| **Account Info** | Not available | AWS account & region details |
| **Help System** | Not available | Interactive capabilities guide |
| **Production Ready** | Custom | Battle-tested by AWS |

## **Advanced Usage**

### **Integration with Cursor**
You can also integrate the official MCP server directly with Cursor:

```json
{
  "mcpServers": {
    "awslabs.cost-explorer-mcp-server": {
      "command": "uvx",
      "args": ["awslabs.cost-explorer-mcp-server@latest"],
      "env": {
        "FASTMCP_LOG_LEVEL": "ERROR",
        "AWS_PROFILE": "your-aws-profile",
        "AWS_REGION": "us-east-1"
      },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

### **Docker Support**
The official MCP server also supports Docker deployment:

```json
{
  "mcpServers": {
    "awslabs.cost-explorer-mcp-server": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "--interactive",
        "--env",
        "FASTMCP_LOG_LEVEL=ERROR",
        "--env-file",
        "/path/to/.env",
        "awslabs/cost-explorer-mcp-server:latest"
      ],
      "env": {},
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

## **References**

- [Official AWS Cost Explorer MCP Server](https://github.com/awslabs/mcp/tree/main/src/cost-explorer-mcp-server)
- [AWS Cost Explorer Pricing](https://aws.amazon.com/aws-cost-management/aws-cost-explorer/pricing/)
- [AWS Cost Comparison Feature](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-cost-comparison.html)
