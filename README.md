# Stock Analysis MCP Server

Advanced stock analysis system with **Pinecone vector database tracking**, AI-powered recommendations, news sentiment analysis, and automated reporting. Built for Python 3.13 with FastMCP.

## 🚀 Features

### Core Capabilities
- ✅ **Real-time Stock Analysis** - Buy/sell recommendations with risk assessment
- ✅ **Pinecone Vector Database** - Track recommendations day-to-day with hybrid embeddings
- ✅ **News Sentiment Analysis** - AI-powered news analysis for trajectory prediction
- ✅ **Smart Recommendations** - 50-point scoring system with multiple factors
- ✅ **Historical Tracking** - Compare today vs yesterday, track changes over time
- ✅ **Automated Reports** - Email notifications with HTML formatting
- ✅ **FastMCP Server** - 11 MCP tools for AI assistant integration
- ✅ **Configurable Watchlists** - Tech, penny stocks, finance, EV, custom lists

### What Makes This Unique
**Pinecone Integration**: Unlike traditional stock trackers, this system saves recommendations to a vector database so you can:
- Compare today's recommendations with yesterday's
- Track how recommendations evolve over time
- Filter out stocks with no significant changes
- Prevent duplicate saves for same-day analysis
- Build historical patterns of recommendation accuracy

## 📋 Requirements

- **Python 3.13+** (optimized for latest Python features)
- **Pinecone Account** (free tier: 2M vectors, sufficient for daily tracking)
- **Gmail** (optional, for email reports)

## 🔧 Installation

### 1. Clone & Setup
```bash
cd StockMCP/server
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate  # Windows
```

### 2. Install Dependencies
```bash
pip install -e .
```

This installs:
- `mcp[cli]>=1.8.1` - FastMCP server framework
- `yfinance>=0.2.61` - Yahoo Finance API
- `pandas>=2.2.0` - Data processing
- `numpy>=2.0.0` - Numerical computations
- `pinecone>=8.0.0` - Vector database
- `sentence-transformers>=5.0.0` - Text embeddings (80MB model)
- `schedule>=1.2.0` - Task scheduling
- `pyyaml>=6.0` - Configuration management

### 3. Configure (Optional)
Edit `server/config.yaml`:
```yaml
email:
  enabled: true
  from: "your-email@gmail.com"
  password: "your-gmail-app-password"
  to: "recipient@example.com"

price_filters:
  min_price: 1.0
  max_price: 10.0

stock_lists:
  custom: [YOUR, TICKERS, HERE]
```

## 🎯 Quick Start

### Interactive Menu (Easiest)
```bash
cd server
python3 run.py
```

**Menu Options:**
1. **Search ALL Stocks ($1-$10)** - Analyzes 60+ stocks, returns top 10 with comparisons
2. **Search Configured Stocks** - Uses your config.yaml watchlist
3. Historical Performance (3-Month)
4. Send Email Report
5. Schedule Automatic Reports
6. Configure Settings
7. Run Tests
8. **Save to Pinecone** - Save today's recommendations for tracking ⭐

### Command Line
```bash
# Search all 60+ stocks and save top 10 to Pinecone
python3 features/feature_manager.py search-all --top 10 --min-price 1.0 --max-price 10.0

# Save recommendations to Pinecone
python3 features/feature_manager.py save-pinecone --mode all --top 10

# Analyze configured stocks
python3 features/feature_manager.py analyze --list penny --top 20

# Historical analysis
python3 features/feature_manager.py historical --min-performance 15

# Email report
python3 features/feature_manager.py email --list tech
```

## 🗄️ Pinecone Vector Database

### What Gets Saved?
Each stock recommendation becomes a **768-dimensional hybrid embedding**:
- **Numeric features (9 dims)**: Price, volume, risk, score, trend, momentum, sentiment
- **Text embeddings (384 dims)**: Company, sector, industry, news (via all-MiniLM-L6-v2)
- **Padding (375 dims)**: Zeros to reach 768 total

### Metadata Tracked
```python
{
    'ticker': 'AAPL',
    'company': 'Apple Inc.',
    'date': '2025-11-25',
    'current_price': 189.50,
    'day_change_percent': 2.3,
    'recommendation': 'Buy',
    'risk_level': 'Low',
    'score': 42,
    'trajectory_trend': 'Uptrend',
    'news_sentiment': 'Positive',
    'search_mode': 'extended_watchlist',
    'price_range': '$1-$10'
}
```

### Smart Features
1. **Duplicate Detection** - Skips stocks already saved today
2. **Change Filtering** - Only displays stocks with >1% price change OR recommendation change
3. **Historical Comparison** - Compares today vs yesterday automatically
4. **Cost**: $0/month on free tier (10 stocks/day = ~3,650/year << 2M limit)

### Daily Workflow
**Day 1:**
```bash
python3 run.py
# Select: 1 (Search ALL stocks)
# Select: 8 (Save to Pinecone)
```

**Day 2:**
```bash
python3 run.py
# Select: 1 (Search ALL stocks)
# Automatically shows: 📊 Yesterday's data, 🔄 Changes, price movements
# Select: 8 (Save new recommendations only - duplicates auto-skipped)
```

## 📊 Recommendation Scoring (50 Points)

| Factor | Points | Description |
|--------|--------|-------------|
| **Recommendation** | 10 | Strong Buy (10), Buy (7), Hold (5), Wait (2) |
| **Risk Level** | 10 | Low (10), Medium (6), High (3) |
| **Day Momentum** | 5 | Daily % change |
| **Volume Ratio** | 5 | Current vs average volume |
| **News Sentiment** | 10 | Positive (10), Neutral (5), Negative (0) |
| **Trajectory** | 10 | Uptrend (10), Sideways (5), Downtrend (0) |

**Example Output:**
```
📈 Top 10 Stock Recommendations (Score: 0-50)

1. AAPL - Apple Inc. - $189.50 (+2.3%)
   Score: 42/50 | Recommendation: Buy | Risk: Low
   📊 Yesterday: $185.20 | 🔄 CHANGED (Hold → Buy)
   Entry: $187.50 | Stop Loss: $180.00
   News: Positive (8.5/10) | Trajectory: Uptrend
```

## 🔌 FastMCP Server (11 Tools)

### Core Analysis Tools
1. **get_stock_info** - Real-time data from Yahoo Finance
2. **get_buying_recommendation** - Entry points, stop loss, risk analysis
3. **get_top_performers** - Best gainers from watchlist
4. **get_price_trajectory** - 30-day trend prediction
5. **get_stocks_under_price** - Filter by price range ($1-$10)

### Advanced Tools
6. **get_top_stock_recommendations_in_range** - Top N with full analysis
7. **generate_daily_analysis_email** - HTML email content
8. **send_email_notification** - SMTP email delivery
9. **save_daily_analysis_to_file** - Export HTML report

### Custom Search
10. **Extended watchlist search** - 60+ stocks from tech, finance, EV sectors
11. **Configurable watchlist search** - Your custom config.yaml lists

### Running MCP Server
```bash
cd server
python3 main.py
```

Connect with MCP-compatible clients (Claude Desktop, etc.)

## 📁 Project Structure

```
StockMCP/
├── README.md                    # This file
├── .gitignore                   # Python 3.13 optimized
├── server/
│   ├── main.py                  # FastMCP server (11 tools)
│   ├── run.py                   # Interactive menu ⭐ START HERE
│   ├── config_manager.py        # Configuration loader
│   ├── config.yaml              # User settings
│   ├── pyproject.toml           # Python 3.13+ dependencies
│   ├── start.sh                 # Quick start script
│   └── features/
│       ├── feature_manager.py   # CLI commands
│       ├── pinecone_saver.py    # Vector database integration
│       ├── email_notifier.py    # Email functionality
│       ├── stock_analyzer.py    # Core analysis + news
│       ├── news_analyzer.py     # Sentiment analysis
│       ├── historical_analyzer.py # 3-month tracking
│       └── auto_scheduler.py    # Automated scheduling
```

## 🎓 Examples

### Example 1: Daily Stock Tracking
```bash
# Morning routine (Day 1)
python3 run.py
# 1 → Search ALL stocks → Top 10 displayed
# 8 → Save to Pinecone

# Morning routine (Day 2)
python3 run.py
# 1 → Search ALL stocks → Shows changes from yesterday!
# Output: "🔄 CHANGED: Hold → Buy (+3.2%)"
# 8 → Save only NEW recommendations (duplicates skipped)
```

### Example 2: Find Best Penny Stocks
```bash
python3 features/feature_manager.py search-all --top 10 --min-price 1.0 --max-price 5.0
```

### Example 3: Email Daily Report
```bash
# Configure email in config.yaml first
python3 features/feature_manager.py email --list tech

# Or schedule daily at 8 AM
python3 features/feature_manager.py schedule --schedule-type daily --schedule-time 08:00 --list penny
```

### Example 4: Historical Analysis
```bash
# Find stocks with 20%+ gains in last 3 months
python3 features/feature_manager.py historical --min-performance 20 --list default
```


## ⚙️ Configuration

### Stock Lists (config.yaml)
- **default** - Mixed portfolio (7 stocks)
- **tech** - AAPL, MSFT, NVDA, GOOGL, META, AMD, etc.
- **penny** - Low-price, high-volume stocks
- **finance** - Banks: JPM, BAC, WFC, C, etc.
- **ev_clean** - TSLA, RIVN, LCID, NIO, etc.
- **custom** - Your watchlist

### Extended Watchlist (60+ Stocks)
Auto-included in "Search ALL" mode:
- Major tech (AAPL, MSFT, GOOGL, AMZN, etc.)
- Affordable stocks (F, NOK, BB, AMC, SNDL, etc.)
- EV sector (TSLA, NIO, RIVN, LCID, etc.)
- Cannabis (ACB, CGC, TLRY, SNDL, etc.)
- Meme stocks (AMC, GME, BB, EXPR, etc.)

### Price Filters
```yaml
price_filters:
  min_price: 1.0   # $1 minimum
  max_price: 10.0  # $10 maximum
```

### Email Setup (Gmail)
1. Enable 2-Step Verification: https://myaccount.google.com/security
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Add to `config.yaml`:
```yaml
email:
  enabled: true
  from: "your-email@gmail.com"
  password: "16-char-app-password"  # NOT your Gmail password!
  to: "recipient@example.com"
```

## 🐛 Troubleshooting

### No Stocks Found
- Adjust price range: `--min-price 0 --max-price 100`
- Try different watchlist: `--list tech`

### Pinecone Errors
- Check API key in `pinecone_saver.py` (line 14)
- Verify index exists: https://app.pinecone.io
- Free tier limits: 2M vectors

### Text Model Download
- First run downloads ~80MB model (all-MiniLM-L6-v2)
- Cached after first download
- Disable with `use_text_embeddings=False` in code

### Email Failures
- Use Gmail App Password (not regular password)
- Check 2-step verification enabled
- Test with: `python3 feature_manager.py email --list default`

### Import Errors
- Ensure virtual environment active: `source .venv/bin/activate`
- Reinstall: `pip install -e .`
- Check Python version: `python3 --version` (must be 3.13+)

## 📚 Command Reference

| Command | Description |
|---------|-------------|
| `python3 run.py` | Interactive menu (recommended) |
| `python3 features/feature_manager.py search-all --top 10` | Search 60+ stocks |
| `python3 features/feature_manager.py analyze --list penny` | Analyze configured list |
| `python3 features/feature_manager.py save-pinecone --mode all` | Save to Pinecone |
| `python3 features/feature_manager.py historical --min-performance 15` | 15%+ gainers |
| `python3 features/feature_manager.py email --list tech` | Send email report |
| `python3 features/feature_manager.py schedule --schedule-type daily --schedule-time 09:00` | Daily automation |
| `python3 main.py` | Start MCP server |

### Common Flags
- `--tickers AAPL,MSFT,TSLA` - Specific stocks
- `--list penny` - Use watchlist
- `--top 20` - Top N recommendations
- `--min-price 1.0` - Minimum price
- `--max-price 10.0` - Maximum price
- `--no-news` - Disable news (faster)
- `--save filename` - Export results

## 🔐 Privacy & Security

- **API Keys**: Pinecone API key hardcoded in `features/pinecone_saver.py` (line 14) - change for production
- **Email**: Uses Gmail App Passwords (not stored in repo)
- **Data**: All stock data from public APIs (Yahoo Finance)
- **Storage**: Pinecone vectors stored in AWS us-east-1
- **No PII**: System doesn't collect personal information

## 📈 Performance

- **Analysis Speed**: ~2-5 seconds per stock (with news)
- **Batch Analysis**: 60+ stocks in ~2 minutes
- **Pinecone Save**: ~1 second per 10 stocks
- **Email Send**: ~2-3 seconds
- **Memory Usage**: ~200-500MB (with text model loaded)

## 🤝 Contributing

This is a personal project. For suggestions:
1. Fork the repository
2. Create feature branch
3. Submit pull request

## ⚠️ Disclaimer

**NOT FINANCIAL ADVICE**

This tool is for educational and informational purposes only. It does not constitute financial advice, investment recommendations, or solicitations to buy/sell securities.

**Key Points:**
- Stock market involves risk of loss
- Past performance ≠ future results
- Always do your own research
- Consult licensed financial advisors
- Use at your own risk

**Data Sources:**
- Yahoo Finance (15-20 min delay)
- News sentiment from public sources
- Technical indicators calculated from historical data

**No Guarantees:**
- Recommendations may be wrong
- Prices may differ from real-time
- System errors possible
- News sentiment subjective

## 📄 License

MIT License - Use at your own risk

## 🔄 Version History

**v1.0.0** (2025-11-25)
- Python 3.13 optimization
- Pinecone vector database integration
- Hybrid embeddings (numeric + text)
- Duplicate detection & change filtering
- Extended watchlist (60+ stocks)
- Removed Alpha Vantage (unused)
- FastMCP server with 11 tools
- Cleaned up codebase

---

**Ready to start?**
```bash
cd server
python3 run.py
```

Select Option 1 to search stocks, Option 8 to save to Pinecone, and start tracking your recommendations! 🚀
