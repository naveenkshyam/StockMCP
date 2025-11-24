# Stock Analysis System

Advanced stock analysis system with **multi-source data validation**, news sentiment integration, smart recommendations, and automated reporting.

## Features

✅ **Real-time Stock Analysis** - Buy/sell recommendations with entry/exit points  
✅ **Multi-Source Data Validation** - Cross-verify data from Yahoo Finance + Alpha Vantage  
✅ **RSI Technical Indicator** - Identify overbought/oversold conditions  
✅ **Consensus Recommendations** - Combined signals from multiple data sources  
✅ **News Sentiment Integration** - Analyzes news to predict price trajectory  
✅ **Top N Recommendations** - Multi-factor scoring system (50 points)  
✅ **Historical Analysis** - 3-month performance tracking with trends  
✅ **Email Reports** - HTML and text format notifications  
✅ **Automated Scheduling** - Daily/weekly automatic reports  
✅ **Configurable Lists** - Pre-defined watchlists (tech, penny, finance, EV, custom)  
✅ **MCP Server** - Model Context Protocol integration for AI assistants

## Quick Start

### 1. Setup Environment
```bash
cd server
source .venv/bin/activate
pip install requests  # For Alpha Vantage API
```

### 2. Get Alpha Vantage API Key (Optional but Recommended)
For multi-source data validation and RSI indicators:
1. Visit: https://www.alphavantage.co/support/#api-key
2. Sign up for free account (5 calls/min, 500/day)
3. Set environment variable:
```bash
export ALPHA_VANTAGE_API_KEY="your_api_key_here"
```

### 3. Configure Settings
Edit `server/config.yaml`:
```yaml
email:
  from: "your-email@gmail.com"
  password: "your-gmail-app-password"
  to: "recipient@example.com"

stock_lists:
  custom: [YOUR, STOCKS, HERE]
```

### 4. Run the System

**Interactive Menu (Recommended):**
```bash
./start.sh
# or
python run.py
```

**Command Line:**
```bash
# Analyze top 20 penny stocks
python feature_manager.py analyze --list penny --top 20

# Historical performance (15%+ gains)
python feature_manager.py historical --min-performance 15

# Send email report
python feature_manager.py email --list tech

# Schedule daily reports at 9 AM
python feature_manager.py schedule --schedule-type daily --schedule-time 09:00
```

**Run Tests:**
```bash
python test_all_features.py --quick
```

## File Structure

```
server/
├── run.py                    # Interactive menu - START HERE
├── feature_manager.py        # Command-line interface
├── test_all_features.py      # Test suite
├── config.yaml               # Configuration file
├── config_manager.py         # Config loader
├── email_notifier.py         # Email functionality
├── main.py                   # MCP server (advanced)
├── start.sh                  # Quick start script
└── features/
    ├── stock_analyzer.py     # Analysis + news + recommendations
    ├── news_analyzer.py      # News sentiment & trajectory
    ├── historical_analyzer.py # 3-month performance
    └── auto_scheduler.py     # Automated scheduling
```

## Key Capabilities

### 1. Stock Analysis with News
- Current price and change
- Buy/sell recommendations (Strong Buy, Buy, Hold, Wait)
- Entry points (conservative, moderate, aggressive)
- Stop loss calculations
- Risk assessment (Low/Medium/High)
- **News sentiment** (positive/negative/neutral)
- **Price trajectory** (7-day and 30-day targets)

### 2. Top Recommendations (60-Point Scoring)
Stocks scored based on:
- Recommendation quality (10 pts)
- Risk level (10 pts)
- Day momentum (5 pts)
- Volume ratio (5 pts)
- **News sentiment** (10 pts)
- **Trajectory prediction** (10 pts)
- **RSI indicator** (10 pts) - NEW with Alpha Vantage

### 3. Configuration (config.yaml)

**Stock Lists:**
- `default` - General mix
- `tech` - Technology (AAPL, MSFT, NVDA, etc.)
- `penny` - Low-price stocks ($1-$10)
- `finance` - Banks and finance (BAC, WFC, JPM, etc.)
- `ev_clean` - EV and clean energy
- `custom` - Your watchlist

**Settings:**
- Email credentials (Gmail App Password required)
- Price filters (min/max)
- News analysis (enable/disable, sentiment weight)
- Scheduler (daily/weekly times)

## Examples

### Find Best Penny Stocks
```bash
python feature_manager.py analyze --list penny --top 10
```

### Email Daily Tech Report
```bash
python feature_manager.py schedule \
  --schedule-type daily \
  --schedule-time 08:00 \
  --list tech
```

### Top Gainers (Last 3 Months)
```bash
python feature_manager.py historical \
  --list default \
  --min-performance 20 \
  --save top_gainers
```

### Analyze Specific Stocks
```bash
python feature_manager.py analyze \
  --tickers AAPL,MSFT,TSLA \
  --min-price 0 \
  --max-price 500
```

## Gmail Setup (For Email Features)

1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Add to `config.yaml`:
```yaml
email:
  from: "your-email@gmail.com"
  password: "16-char-app-password"
  to: "recipient@example.com"
```

## Testing

**Quick Test:**
```bash
python test_all_features.py --quick
```

**Full Test Suite:**
```bash
python test_all_features.py
```

Tests cover:
- Single/multiple stock analysis
- Top recommendations with scoring
- Historical performance
- Configuration manager
- News analyzer
- Email functionality

## MCP Server (Advanced)

For use with MCP-compatible AI assistants:
```bash
cd server
uv run main.py
```

### Available MCP Tools

#### Core Tools (Yahoo Finance)
- `get_stock_info` - Real-time stock data
- `get_buying_recommendation` - Buy/sell advice with technical analysis
- `get_top_performers` - Best performing stocks from watchlist
- `get_price_trajectory` - Price trend predictions
- `get_stocks_under_price` - Filter by price range
- `generate_daily_analysis_email` - Create email reports
- `send_email_notification` - Send emails via SMTP
- `save_daily_analysis_to_file` - Save reports as HTML

#### Multi-Source Tools (Yahoo Finance + Alpha Vantage)
- `get_multi_source_stock_data` - Compare data from both sources
- `get_comprehensive_recommendation` - Enhanced recommendations with RSI
- `compare_stock_sources` - Detailed side-by-side comparison

### Multi-Source Data Features

**Data Validation:**
- Cross-verify prices between Yahoo Finance and Alpha Vantage
- Detect discrepancies and data inconsistencies
- Get data consistency ratings (High/Medium/Low)

**RSI Technical Indicator:**
- 14-day Relative Strength Index from Alpha Vantage
- Automatic signals: Oversold (<30), Overbought (>70), Neutral (30-70)
- Helps identify optimal entry/exit points

**Consensus Recommendations:**
- Combines Yahoo Finance technical analysis with Alpha Vantage RSI
- Multi-signal confirmation for higher confidence
- Ratings: Strong Buy, Buy, Hold, Wait

**Example Usage:**
```python
# Compare data sources
result = await get_multi_source_stock_data("AAPL")
print(f"Price difference: {result['comparison']['price_difference_percent']}%")
print(f"Data consistency: {result['comparison']['data_consistency']}")
print(f"RSI: {result['alpha_vantage']['rsi']} ({result['alpha_vantage']['rsi_signal']})")

# Get enhanced recommendation
rec = await get_comprehensive_recommendation("TSLA", use_alpha_vantage=True)
print(f"Consensus: {rec['consensus_recommendation']['overall']}")
print(f"Confidence: {rec['consensus_recommendation']['confidence']}")

# Validate data quality
comp = await compare_stock_sources("NVDA")
print(f"Reliability: {comp['summary']['overall_reliability']}")
```

### Alpha Vantage API Setup

**Free Tier Limits:**
- 5 API calls per minute
- 500 API calls per day

**Getting Started:**
1. Sign up at https://www.alphavantage.co/support/#api-key
2. Get your free API key
3. Set environment variable: `export ALPHA_VANTAGE_API_KEY="your_key"`
4. System falls back to Yahoo Finance if Alpha Vantage unavailable

**Managing Rate Limits:**
- Use `use_alpha_vantage=False` parameter when AV data isn't needed
- Cache results for repeated queries
- Consider premium tier for production ($49.99/month = 600 calls/min)

## Command Reference

| Command | Description |
|---------|-------------|
| `python run.py` | Interactive menu |
| `python feature_manager.py analyze --list penny` | Analyze penny stocks |
| `python feature_manager.py analyze --list tech --top 20` | Top 20 tech stocks |
| `python feature_manager.py historical --min-performance 15` | 15%+ 3-month gains |
| `python feature_manager.py email --list default` | Send email report |
| `python feature_manager.py schedule --schedule-type daily --schedule-time 09:00` | Daily 9 AM reports |
| `python test_all_features.py --quick` | Quick test |
| `./start.sh` | Quick start script |

## Options

**Common Flags:**
- `--tickers AAPL,MSFT` - Specific stocks
- `--list penny` - Use config watchlist
- `--top 20` - Get top N recommendations
- `--min-price 1.0` - Minimum price filter
- `--max-price 10.0` - Maximum price filter
- `--min-performance 10` - Min 3-month % gain
- `--no-news` - Disable news analysis (faster)
- `--save filename` - Save to file

## Requirements

- Python 3.12+
- yfinance - Stock data from Yahoo Finance
- requests - Alpha Vantage API calls
- pandas, numpy - Data processing
- pyyaml - Configuration
- schedule - Task scheduling
- mcp - Model Context Protocol

## What's New

### Multi-Source Data Integration (Latest)
- **Dual Data Sources**: Yahoo Finance + Alpha Vantage for cross-validation
- **RSI Indicator**: 14-day Relative Strength Index for overbought/oversold signals
- **Consensus Recommendations**: Combined analysis from multiple sources
- **Data Validation**: Automatic discrepancy detection and consistency ratings
- **Enhanced Scoring**: 60-point system (up from 50) with RSI factor
- **CLI Integration**: All features (analyze, top N, historical) now use Alpha Vantage
- **3 New MCP Tools**: Multi-source comparison, comprehensive recommendations, source validation

### Benefits:
- **Higher Accuracy**: Cross-verify data to catch errors
- **Better Insights**: Access RSI and Alpha Vantage-exclusive metrics
- **Increased Confidence**: Recommendations backed by multiple sources
- **Reliability**: System works even if one source fails
- **Flexibility**: Choose single or multi-source analysis
- **CLI & MCP Support**: Both interfaces benefit from multi-source data

## Troubleshooting

**No stocks found:**
- Check price range (default $1-$10)
- Use `--min-price 0 --max-price 1000` for broader range

**News not working:**
- Some stocks have limited news
- Use `--no-news` flag for faster analysis

**Email fails:**
- Verify Gmail App Password (not regular password)
- Check config.yaml formatting
- Ensure 2-step verification enabled

**Alpha Vantage issues:**
- Rate limit exceeded: Wait 60 seconds (5 calls/min limit)
- "Demo key" limitations: Get your free API key
- Price discrepancies: Check `latest_trading_day` field for data freshness

## Disclaimer

This tool is for informational purposes only. Not financial advice. Always do your own research and consult with qualified financial advisors before making investment decisions.

**Data sources:** 
- Yahoo Finance (15-20 minute delay during market hours)
- Alpha Vantage API (real-time and technical indicators)
- News feeds from yfinance

**Important Notes:**
- Price discrepancies between sources may occur due to timing
- RSI and technical indicators are tools, not guarantees
- Multi-source validation increases confidence but doesn't eliminate risk
- Free API tiers have rate limits - plan usage accordingly
