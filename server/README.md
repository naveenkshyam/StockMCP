# Stock Analysis System - Quick Start Guide

## Overview
Advanced stock analysis system with news sentiment integration, smart recommendations, automated reporting, **multi-source data validation** (Yahoo Finance + Alpha Vantage), and **Pinecone vector database** for historical comparison.

## Features
✅ Real-time stock analysis with buy/sell recommendations  
✅ News sentiment analysis for trajectory predictions  
✅ Top N recommendations with multi-factor scoring (50-point scale)  
✅ 3-month historical performance tracking  
✅ Email notifications (HTML & text)  
✅ Automated daily/weekly reports  
✅ Configurable stock lists and settings  
✅ **Multi-source data validation** (Yahoo Finance + Alpha Vantage)  
✅ **Flexible stock source options** (configured lists vs extended watchlist)  
✅ **Pinecone vector database** for tracking recommendation changes  
✅ **Historical comparison** - see how recommendations changed from yesterday  

## Stock Source Options

### Three Ways to Search for Stocks:

#### 1. **Search ALL Stocks** ($1-$10 Price Range) 🆕
- Searches 60+ stocks from extended watchlist
- Price range: $1.00 - $10.00 (customizable)
- Returns top 10 recommendations with full analysis
- **Compares with yesterday's data from Pinecone** to show recommendation changes
- Best for: Comprehensive market scan to find the best opportunities
- Example: Find top 10 affordable stocks with strong buy signals

#### 2. **Search Configured Stocks** (Focused Analysis)
- Uses only stocks defined in your `config.yaml` file
- Default: 7 carefully selected stocks (NVDA, AMD, INTC, F, NOK, BAC, WFC)
- Best for: Tracking specific stocks you care about
- Faster execution, focused results

#### 3. **Custom Ticker Search**
- Enter specific ticker symbols (e.g., AAPL, MSFT, TSLA)
- Best for: Analyzing specific stocks of interest

### Using in MCP Server
```python
# Use configured stocks only (7 stocks from config.yaml)
result = await get_top_stock_recommendations_in_range(
    max_price=10.0,
    min_price=1.0,
    top_n=10,
    use_extended_watchlist=False  # Configured stocks only
)

# Use extended watchlist (60+ stocks)
result = await get_top_stock_recommendations_in_range(
    max_price=10.0,
    min_price=1.0,
    top_n=10,
    use_extended_watchlist=True  # Extended watchlist (default)
)
```

## Quick Start

### 1. Activate Environment
```bash
cd /home/nshyam/lambda-examples/ML_Python_examples/StockMCP/server
source .venv/bin/activate
```

### 2. Run the System
```bash
python run.py
```

This launches an interactive menu where you can:
- **Search ALL stocks ($1-$10)** - Top 10 with historical comparison 🆕
- Search configured stocks - Top N recommendations
- View 3-month historical performance
- Send email reports
- Schedule automatic reports
- Configure settings
- Run tests
- **Save recommendations to Pinecone** - Track changes over time 🆕

## Alternative: Command Line Interface

### Search ALL Stocks (NEW!)
```bash
# Search 60+ stocks for top 10 recommendations ($1-$10 range)
python feature_manager.py search-all --top 10 --min-price 1.0 --max-price 10.0

# Without news analysis (faster)
python feature_manager.py search-all --top 10 --no-news

# Save results
python feature_manager.py search-all --top 10 --save all_stocks_report
```

### Analyze Stocks
```bash
# Analyze specific stocks
python feature_manager.py analyze --tickers AAPL,MSFT,TSLA

# Use predefined list from config
python feature_manager.py analyze --list penny

# Get top 20 recommendations with news
python feature_manager.py analyze --list tech --top 20

# Without news analysis (faster)
python feature_manager.py analyze --list default --no-news
```

### Historical Analysis
```bash
# 3-month performance
python feature_manager.py historical --list penny --min-performance 10

# Save results
python feature_manager.py historical --list tech --save tech_historical
```

### Email Reports
```bash
# Using config.yaml settings
python feature_manager.py email --list default

# Manual email settings
python feature_manager.py email \
  --list penny \
  --email-from your@gmail.com \
  --email-password your-app-password \
  --email-to recipient@example.com
```

### Schedule Automatic Reports
```bash
# Daily at 9:00 AM
python feature_manager.py schedule \
  --schedule-type daily \
  --schedule-time 09:00 \
  --list default

# Weekly on Monday at 8:00 AM
python feature_manager.py schedule \
  --schedule-type weekly \
  --schedule-day monday \
  --schedule-time 08:00 \
  --list tech
```

### Save to Pinecone (NEW!)
```bash
# Save ALL stocks search results to Pinecone
python feature_manager.py save-pinecone --mode all --top 10 --min-price 1.0 --max-price 10.0

# Save configured stocks results to Pinecone
python feature_manager.py save-pinecone --mode config --list default --top 20
```

**Why use Pinecone?**
- Track how recommendations change day-to-day
- Compare today's "Strong Buy" with yesterday's "Hold"
- Identify stocks with improving or declining signals
- Historical analysis of recommendation accuracy

## Configuration

Edit `config.yaml` to customize:

### Email Settings
```yaml
email:
  from: "your-email@gmail.com"
  password: "your-gmail-app-password"
  to: "recipient@example.com"
```

### Stock Lists
```yaml
stock_lists:
  default: [AAPL, MSFT, TSLA, ...]
  tech: [AAPL, MSFT, GOOGL, ...]
  penny: [ABTS, PLUG, NIO, ...]
  custom: [YOUR, STOCKS, HERE]
```

### Price Filters
```yaml
analysis:
  price_filter:
    min_price: 1.0
    max_price: 10.0
```

### News Analysis
```yaml
analysis:
  news:
    enabled: true
    max_articles: 5
    sentiment_weight: 0.3
```

## File Structure

```
server/
├── run.py                    # Interactive main menu (START HERE)
├── feature_manager.py        # Command-line interface
├── test_all_features.py      # Comprehensive test suite
├── config.yaml               # Configuration file
├── config_manager.py         # Config loader
├── email_notifier.py         # Email functionality
├── main.py                   # MCP server (advanced)
├── pinecone_saver.py         # Pinecone vector DB integration 🆕
├── features/
│   ├── stock_analyzer.py     # Stock analysis + news integration
│   ├── historical_analyzer.py # 3-month performance
│   ├── news_analyzer.py      # News sentiment analysis
│   └── auto_scheduler.py     # Automated scheduling
└── .venv/                    # Virtual environment
```

## Testing

### Quick Test
```bash
python test_all_features.py --quick
```

### Full Test Suite
```bash
python test_all_features.py
```

Tests include:
- Single stock analysis
- Multiple stocks analysis
- Top recommendations with scoring
- Historical performance
- Configuration manager
- News analyzer

## Gmail Setup (For Email Features)

1. Enable 2-Step Verification in Google Account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Add to `config.yaml`:
   ```yaml
   email:
     from: "your-email@gmail.com"
     password: "generated-app-password"
     to: "recipient@example.com"
   ```

## Examples

### Example 1: Find Top 10 Affordable Stocks (NEW!)
```bash
# Search ALL 60+ stocks for best opportunities
python feature_manager.py search-all --top 10
```

### Example 2: Track Recommendation Changes (NEW!)
```bash
# Day 1: Save today's recommendations
python feature_manager.py save-pinecone --mode all --top 10

# Day 2: Search again and see what changed
python feature_manager.py search-all --top 10
# Output will show: "Yesterday: Hold → Today: Buy" for changed recommendations
```

### Example 3: Find Top 10 Penny Stocks from Config
```bash
python feature_manager.py analyze --list penny --top 10
```

### Example 4: Stocks with 20%+ 3-Month Gains
```bash
python feature_manager.py historical --list default --min-performance 20
```

### Example 5: Daily Morning Report
```bash
python feature_manager.py schedule \
  --schedule-type daily \
  --schedule-time 08:00 \
  --list default
```

## Features in Detail

### 1. Stock Analysis
- Current price and day change
- Buy/sell recommendations
- Entry points (conservative, moderate, aggressive)
- Stop loss calculations
- Risk assessment (Low/Medium/High)
- Technical indicators (MA20, MA50)
- Volume analysis
- **News sentiment** (positive/negative/neutral)
- **Trajectory prediction** (7-day and 30-day targets)

### 2. Top Recommendations (Scoring System)
Stocks are scored on 50 points based on:
- Recommendation quality (0-10 points)
- Risk level (0-10 points)
- Day momentum (0-5 points)
- Volume ratio (0-5 points)
- **News sentiment** (0-10 points)
- **Trajectory prediction** (0-10 points)

### 3. News Integration
- Fetches recent news articles for each stock
- Analyzes sentiment using keyword matching
- Adjusts recommendations based on news
- Predicts price trajectory
- Shows confidence level

### 4. Historical Analysis
- 3-month price performance
- Trend analysis (uptrend/downtrend/sideways)
- Volatility metrics
- Volume trends
- Performance-based filtering

### 5. Pinecone Vector Database (NEW!)
- **Store daily recommendations** as vector embeddings
- **Track changes** in recommendations over time
- **Compare today vs yesterday**: See if a stock went from "Hold" to "Buy"
- **Historical accuracy**: Analyze how recommendations performed
- **768-dimensional vectors** encoding price, recommendation, risk, sentiment, trajectory
- **Automatic comparison** when searching ALL stocks

#### How It Works:
1. **Save Today's Data**: Recommendations stored with metadata (price, ticker, recommendation, sentiment)
2. **Vector Embeddings**: Each stock encoded as 768-dimensional vector
3. **Tomorrow's Search**: Automatically queries Pinecone for yesterday's data
4. **Change Detection**: Shows recommendation evolution (e.g., "Hold → Strong Buy")
5. **Track Accuracy**: See if "Buy" recommendations actually went up in price

## Tips

1. **Use Config Lists**: Define your watchlists in `config.yaml` for quick access
2. **News Analysis**: Provides better insights but takes longer (can disable with `--no-news`)
3. **Save Reports**: Use `--save filename` to keep records
4. **Price Range**: Adjust in config.yaml or use `--min-price` and `--max-price`
5. **Scheduler**: Run in `screen` or `tmux` for 24/7 operation

## Support

For issues or questions:
1. Run tests: `python test_all_features.py`
2. Check config: `python run.py` → option 6
3. Review logs in terminal output

## Disclaimer

This tool is for informational purposes only. Not financial advice. Always do your own research and consult with qualified financial advisors before making investment decisions.

Data sources: Yahoo Finance (15-20 minute delay), yfinance news feeds.
