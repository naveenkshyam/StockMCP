# Stock Analysis System

Advanced stock analysis system with news sentiment integration, smart recommendations, and automated reporting.

## Features

✅ **Real-time Stock Analysis** - Buy/sell recommendations with entry/exit points  
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
```

### 2. Configure Settings
Edit `server/config.yaml`:
```yaml
email:
  from: "your-email@gmail.com"
  password: "your-gmail-app-password"
  to: "recipient@example.com"

stock_lists:
  custom: [YOUR, STOCKS, HERE]
```

### 3. Run the System

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

### 2. Top Recommendations (50-Point Scoring)
Stocks scored based on:
- Recommendation quality (10 pts)
- Risk level (10 pts)
- Day momentum (5 pts)
- Volume ratio (5 pts)
- **News sentiment** (10 pts)
- **Trajectory prediction** (10 pts)

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

The MCP server provides 8 tools:
- `get_stock_info` - Real-time stock data
- `get_buying_recommendation` - Buy/sell advice
- `get_top_performers` - Best performing stocks
- `get_price_trajectory` - Price predictions
- `get_stocks_under_price` - Filter by price
- `generate_daily_analysis_email` - Email reports
- `send_email_notification` - Send emails
- `save_daily_analysis_to_file` - Save reports

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
- yfinance - Stock data
- pandas, numpy - Data processing
- pyyaml - Configuration
- schedule - Task scheduling
- mcp - Model Context Protocol

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

## Disclaimer

This tool is for informational purposes only. Not financial advice. Always do your own research and consult with qualified financial advisors before making investment decisions.

Data sources: Yahoo Finance (15-20 minute delay), yfinance news feeds.
