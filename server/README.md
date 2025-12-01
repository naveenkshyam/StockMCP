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
✅ **3-Month Historical Analysis** - Compare current vs 3 months ago with news & recommendations  
✅ **NEW: Day Trading Analyzer** - Find best day trading stocks with volatility, volume, and news analysis 🔥  

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
# Use configured stocks only (any stocks from config.yaml)
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
- **Pinecone Historical Analysis (3-Month Comparison)** - Compare current vs 3 months ago 🔥 NEW!
- **Day Trading Recommendations** - Find volatile, liquid stocks perfect for day trading 🔥 NEW!

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

### Day Trading Recommendations (NEW! 🔥)
```bash
# Find top 10 day trading stocks (under $20)
python features/feature_manager.py daytrading --top 10

# Analyze ALL 75+ day trading stocks
python features/feature_manager.py daytrading --all --top 15 --min-score 65

# Custom tickers for day trading analysis
python features/feature_manager.py daytrading --tickers PLTR,SOFI,NIO --max-price 20

# Save detailed day trading report
python features/feature_manager.py daytrading --top 10 --save daytrading_report
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
python features/feature_manager.py save-pinecone --mode all --top 10 --min-price 1.0 --max-price 10.0

# Save configured stocks results to Pinecone
python features/feature_manager.py save-pinecone --mode config --list default --top 20
```

**Why use Pinecone?**
- Track how recommendations change day-to-day
- Compare today's "Strong Buy" with yesterday's "Hold"
- Identify stocks with improving or declining signals
- Historical analysis of recommendation accuracy

### Pinecone Historical Analysis (NEW! 🔥)
```bash
# Analyze single stock with 3-month comparison
python features/feature_manager.py pinecone-historical --ticker AAPL

# Analyze ALL stocks saved in Pinecone (score >= 60)
python features/feature_manager.py pinecone-historical --min-score 60 --sort-by performance

# Sort by news sentiment
python features/feature_manager.py pinecone-historical --sort-by news --display-limit 10

# Save detailed report
python features/feature_manager.py pinecone-historical --min-score 70 --save report_20241126
```

**Using the Interactive Menu (run.py):**

Select **option 9** from the main menu:

**Option 1 - Single Stock Analysis:**
- Enter ticker (e.g., NVDA, AAPL)
- Get detailed 3-month comparison with:
  - Price change percentage and rating
  - Recommendation evolution (then vs now)
  - Technical analysis (trend, volatility, moving averages)
  - News sentiment with recent headlines
  - 100-point recommendation score with reasoning

**Option 2 - Bulk Analysis:**
- Set minimum score filter (0-100, default: 50)
- Choose sort method:
  - `performance` - Best 3-month price gains
  - `score` - Highest recommendation scores
  - `news` - Most positive sentiment
- Set display limit (default: 20 stocks)
- Optionally save full report

**Prerequisites:**
- Must have saved data to Pinecone first (run option 8 or save-pinecone command)
- Works best with data from 3 months ago for full comparison

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
├── main.py                   # MCP server (advanced)
├── config.yaml               # Configuration file
├── config_manager.py         # Config loader
├── test_all_features.py      # Comprehensive test suite
├── features/
│   ├── feature_manager.py        # Command-line interface
│   ├── stock_analyzer.py         # Stock analysis + news integration
│   ├── historical_analyzer.py    # 3-month performance
│   ├── news_analyzer.py          # News sentiment analysis
│   ├── daytrading_analyzer.py    # Day trading recommendations 🆕
│   ├── pinecone_saver.py         # Pinecone vector DB integration
│   ├── pinecone_historical.py    # 3-month historical comparison
│   ├── email_notifier.py         # Email functionality
│   └── auto_scheduler.py         # Automated scheduling
└── .venv/                        # Virtual environment
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
python features/feature_manager.py search-all --top 10
```

### Example 2: Track Recommendation Changes (NEW!)
```bash
# Day 1: Save today's recommendations
python features/feature_manager.py save-pinecone --mode all --top 10

# Day 2: Search again and see what changed
python features/feature_manager.py search-all --top 10
# Output will show: "Yesterday: Hold → Today: Buy" for changed recommendations
```

### Example 3: 3-Month Historical Analysis (NEW! 🔥)

**Via Interactive Menu (Recommended):**
```bash
python run.py
# Select option 9: Pinecone Historical Analysis

# For single stock:
# Choose option 1, enter ticker (e.g., AAPL)
# Optionally save detailed report

# For bulk analysis:
# Choose option 2
# Set min score (e.g., 60)
# Choose sort method (performance/score/news)
# Set display limit (e.g., 10)
```

**Via Command Line:**
```bash
# Analyze single stock with 3-month comparison, news, and recommendations
python features/feature_manager.py pinecone-historical --ticker AAPL

# Analyze ALL stocks saved in Pinecone (score >= 60)
python features/feature_manager.py pinecone-historical --min-score 60 --sort-by performance

# Sort by news sentiment
python features/feature_manager.py pinecone-historical --sort-by news --display-limit 10

# Save detailed report
python features/feature_manager.py pinecone-historical --min-score 70 --save report_20241126
```

**What You Get:**
- Current price vs 3 months ago comparison
- Percentage change with performance rating
- Recommendation evolution tracking
- Technical analysis (trend, volatility, MA20/MA50)
- News sentiment with recent headlines
- 100-point recommendation score
- Detailed action plan with confidence level

### Example 4: Find Top 10 Penny Stocks from Config
```bash
python features/feature_manager.py analyze --list penny --top 10
```

### Example 5: Stocks with 20%+ 3-Month Gains
```bash
python features/feature_manager.py historical --list default --min-performance 20
```

### Example 6: Daily Morning Report
```bash
python features/feature_manager.py schedule \
  --schedule-type daily \
  --schedule-time 08:00 \
  --list default
```

### Example 7: Day Trading Morning Scan (NEW! 🔥)
```bash
# Quick morning scan for day trading opportunities
python features/feature_manager.py daytrading --top 10 --min-score 65

# Comprehensive scan of all 75+ day trading stocks
python features/feature_manager.py daytrading --all --top 15 --min-score 70 --save morning_scan

# Focus on specific volatile stocks
python features/feature_manager.py daytrading --tickers RIVN,NIO,PLTR,SOFI,LCID --max-price 20
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

### 6. 3-Month Historical Analysis (NEW! 🔥)
Compare stocks' current performance with 3 months ago from Pinecone data, combining:
- **Price Performance**: Current price vs 3 months ago (gain/loss %)
- **Recommendation Evolution**: How recommendations changed over time
- **Technical Analysis**: Trend, volatility, MA20/MA50 comparison
- **News Sentiment**: Current headlines and sentiment scoring
- **Smart Recommendations**: 100-point scoring system considering all factors

#### Comprehensive Scoring (100 points):
- **3-Month Performance** (30 pts): >20%: +15, >10%: +10, >5%: +5
- **Trend Analysis** (20 pts): Uptrend: +10, Downtrend: -10
- **News Sentiment** (20 pts): Positive: +10, Negative: -10
- **Technical Position** (15 pts): Above MA50: +8, Above MA20: +5
- **Volatility** (10 pts): Low <30%: +5, High >50%: -5
- **Recommendation Change** (5 pts): Upgraded: +5, Downgraded: -5

#### Recommendation Levels:
- **Strong Buy (75-100)**: Excellent opportunity
- **Buy (60-74)**: Good entry point
- **Hold/Accumulate (45-59)**: Maintain, add on dips
- **Hold (30-44)**: Wait for clearer signals
- **Caution (20-29)**: Consider trimming position
- **Avoid/Sell (<20)**: Exit or avoid

### 7. Day Trading Analyzer (NEW! 🔥)
Specialized tool for identifying high-potential day trading opportunities with comprehensive analysis:

#### Key Features:
- **Volatility Analysis**: Average intraday range (optimal: 3-7%)
- **Volume Metrics**: Liquidity checks and recent activity
- **Price Momentum**: MA crossovers and trend strength
- **Gap Analysis**: Opening gaps create trading opportunities
- **News Impact**: Sentiment-driven volatility detection
- **Technical Trajectory**: Price trend using linear regression
- **Market Cap Filter**: Excludes illiquid penny stocks (<$100M)

#### Scoring System (0-100):
- **Volatility** (30 pts): Higher intraday range = more opportunities
- **Volume** (20 pts): High volume ratio indicates strong liquidity
- **Momentum** (15 pts): MA crossovers and price position
- **News** (10 pts): Strong sentiment creates volatility
- **Trend** (10 pts): Identifies directional opportunities
- **Gaps** (10 pts): Morning gaps = trading opportunities
- **Liquidity** (5 pts): Volume > 500k shares minimum

#### Day Trading Recommendations:
- **Excellent (85-100)**: Strong Buy for Day Trading
- **Very Good (75-84)**: Buy for Day Trading
- **Good (65-74)**: Consider for Day Trading
- **Moderate (55-64)**: Watch for Entry
- **Poor (<55)**: Skip

#### What You Get:
- **Trading Metrics**: Volatility, volume ratio, 5-day momentum
- **News Impact**: Sentiment analysis with impact level
- **Price Targets**: 2%, 3%, and 5% gain targets
- **Stop Loss**: Automatic 2% stop loss calculation
- **Key Levels**: Support, resistance, and moving averages
- **Trend Analysis**: Current price trajectory

#### Day Trading Watchlist (75+ Stocks):
- **Tech & Growth**: PLTR, SOFI, NIO, LCID, RIVN, GRAB, NU
- **Financial**: BAC, WFC, C, ALLY, SCHW
- **Energy**: F, PLUG, FCEL, VALE, X, CLF
- **Cannabis**: TLRY, CGC, SNDL, ACB, CRON
- **Crypto-Related**: MARA, RIOT, COIN
- **High Volatility**: AMC, GME, BB (meme stocks)
- And 50+ more liquid, volatile stocks

#### Usage Examples:
```bash
# Quick scan: Top 10 day trading opportunities
python features/feature_manager.py daytrading --top 10

# Comprehensive: All 75+ stocks, minimum score 65
python features/feature_manager.py daytrading --all --top 15 --min-score 65

# Custom analysis with specific stocks
python features/feature_manager.py daytrading --tickers PLTR,SOFI,NIO,RIVN

# Save detailed report
python features/feature_manager.py daytrading --top 10 --save today
```

#### Best Practices:
1. **Morning Scan**: Run at market open to identify opportunities
2. **Min Score**: Use 65+ for quality trades, 75+ for best setups
3. **Volume Check**: Ensure avg volume > 1M shares for good fills
4. **News Impact**: High news impact = increased volatility/opportunity
5. **Risk Management**: Always use provided stop loss levels
6. **Target Selection**: Start with 2% targets, scale to 3-5% as momentum builds

See `features/PINECONE_HISTORICAL_README.md` for detailed documentation.

## Tips

1. **Use Config Lists**: Define your watchlists in `config.yaml` for quick access
2. **News Analysis**: Provides better insights but takes longer (can disable with `--no-news`)
3. **Save Reports**: Use `--save filename` to keep records
4. **Price Range**: Adjust in config.yaml or use `--min-price` and `--max-price`
5. **Scheduler**: Run in `screen` or `tmux` for 24/7 operation
6. **Pinecone Workflow**: Save data daily (option 8), analyze weekly (option 9) for best results

## Complete Workflow Example

### Daily Trading Workflow with Pinecone Tracking

**Day 1 - Initial Setup:**
```bash
python run.py
# Select option 8: Save to Pinecone
# Choose mode 1 (ALL stocks) or 2 (configured)
# This saves today's recommendations as baseline
```

**Day 2-89 - Daily Tracking:**
```bash
python run.py
# Select option 1: Search ALL Stocks
# Review today's top recommendations
# Compare with yesterday's data (automatic)
# Select option 8 again to save today's data
```

**Day 90+ - Historical Analysis:**
```bash
python run.py
# Select option 9: Pinecone Historical Analysis
# Choose option 2 for bulk analysis
# Set min-score: 60 (quality stocks)
# Sort by: performance (top movers)
# Review which stocks improved over 3 months
```

### Best Practices

1. **First Time Setup:**
   - Configure `config.yaml` with your email and stock lists
   - Run option 8 to save initial data to Pinecone
   - Wait 3+ months for meaningful historical comparisons

2. **Daily Routine:**
   - Morning: Run option 1 (Search ALL stocks) for quick scan
   - Review recommendation changes from yesterday
   - Save to Pinecone (option 8) to track changes

3. **Weekly Analysis:**
   - Run option 9 (Historical Analysis) to see 3-month trends
   - Filter by min-score 70+ for best opportunities
   - Save reports for record keeping

4. **Monthly Review:**
   - Analyze all Pinecone data with sort-by performance
   - Identify consistently strong stocks
   - Review news sentiment patterns

## Support

For issues or questions:
1. Run tests: `python test_all_features.py`
2. Check config: `python run.py` → option 6
3. Review logs in terminal output

## Disclaimer

This tool is for informational purposes only. Not financial advice. Always do your own research and consult with qualified financial advisors before making investment decisions.

Data sources: Yahoo Finance (15-20 minute delay), yfinance news feeds.
