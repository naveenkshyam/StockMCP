from mcp.server.fastmcp import FastMCP
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import Optional
from email_notifier import StockEmailNotifier, create_and_send_email, create_and_save_email

# Initialize FastMCP server
mcp = FastMCP("stock-api")

@mcp.tool()
async def get_stock_info(ticker: str) -> dict:
    """
    Get the information of a stock using its ticker symbol.
    Args:
        ticker (str): The stock ticker symbol.
    Returns:
        dict: A dictionary containing the following stock information:
            - symbol: Stock ticker symbol
            - shortName: Company's short name 
            - currentPrice: Current stock price
            - regularMarketChange: Price change from previous close
            - regularMarketChangePercent: Percentage change from previous close
            - regularMarketDayRange: Today's price range (low-high)
            - volume: Today's trading volume
            - marketCap: Company's market capitalization
            - fiftyTwoWeekRange: 52-week price range (low-high)
            - trailingPE: Price-to-earnings ratio (trailing 12 months)
            - dividendYield: Dividend yield as a percentage
            - sector: Company's sector
            - industry: Company's industry
            - recommendationKey: Analyst recommendations
    """
    try:
        # Fetch the stock price from yahoo finance
        dat = yf.Ticker(ticker)
        response = dat.info

        if response:
            # Extract only the important fields
            important_fields = [
                'symbol', 
                'shortName', 
                'currentPrice',
                'regularMarketChange',
                'regularMarketChangePercent',
                'regularMarketDayRange',
                'volume',
                'marketCap',
                'fiftyTwoWeekRange',
                'trailingPE',
                'dividendYield',
                'sector',
                'industry',
                'recommendationKey'
            ]
            
            # Create a filtered response with only the important fields
            filtered_data = {field: response.get(field) for field in important_fields if field in response}
            
            return {
                "ticker": ticker,
                "data": filtered_data
            }
        else:
            return {"error": "Stock not found"}
    
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_buying_recommendation(ticker: str) -> dict:
    """
    Get detailed buying recommendation for a stock including entry points, stop-loss, and risk analysis.
    Args:
        ticker (str): The stock ticker symbol.
    Returns:
        dict: Buying recommendations including:
            - current_price: Current stock price
            - recommendation: Overall recommendation (Strong Buy, Buy, Hold, Sell, etc.)
            - entry_points: Suggested buy price ranges (conservative, moderate, aggressive)
            - stop_loss: Recommended stop-loss level
            - risk_level: Risk assessment (Low, Medium, High)
            - key_levels: Important support and resistance levels
            - analysis: Detailed analysis text
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get historical data for analysis
        hist = stock.history(period="3mo")
        
        if hist.empty or not info:
            return {"error": "Unable to fetch stock data"}
        
        current_price = info.get('currentPrice', hist['Close'].iloc[-1])
        previous_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
        day_change_pct = ((current_price - previous_close) / previous_close * 100) if previous_close else 0
        
        # Calculate key technical levels
        high_52w = info.get('fiftyTwoWeekHigh', hist['High'].max())
        low_52w = info.get('fiftyTwoWeekLow', hist['Low'].min())
        
        # Calculate moving averages
        ma_20 = hist['Close'].tail(20).mean() if len(hist) >= 20 else current_price
        ma_50 = hist['Close'].tail(50).mean() if len(hist) >= 50 else current_price
        
        # Calculate support and resistance
        recent_high = hist['High'].tail(20).max()
        recent_low = hist['Low'].tail(20).min()
        
        # Volume analysis
        avg_volume = hist['Volume'].mean()
        current_volume = info.get('volume', hist['Volume'].iloc[-1])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Risk assessment
        volatility = hist['Close'].pct_change().std() * 100
        market_cap = info.get('marketCap', 0)
        
        # Determine risk level
        risk_level = "Low"
        if volatility > 5 or market_cap < 100_000_000:
            risk_level = "High"
        elif volatility > 3 or market_cap < 1_000_000_000:
            risk_level = "Medium"
        
        # Calculate entry points
        conservative_entry = round(ma_20 * 0.95, 2)
        moderate_entry = round(current_price * 0.97, 2)
        aggressive_entry = round(current_price * 1.02, 2)
        
        # Calculate stop loss (5-10% below entry depending on volatility)
        stop_loss_pct = 0.10 if risk_level == "High" else 0.07 if risk_level == "Medium" else 0.05
        stop_loss = round(current_price * (1 - stop_loss_pct), 2)
        
        # Generate recommendation
        recommendation = "Hold"
        if current_price < ma_20 * 0.95 and day_change_pct < 0:
            recommendation = "Strong Buy"
        elif current_price < ma_20:
            recommendation = "Buy"
        elif day_change_pct > 15:
            recommendation = "Wait for Pullback"
        elif current_price > ma_20 * 1.1:
            recommendation = "Overextended - Wait"
        
        # Analysis text
        analysis_points = []
        
        if day_change_pct > 10:
            analysis_points.append(f"Stock surged {day_change_pct:.1f}% today - consider waiting for consolidation")
        elif day_change_pct < -5:
            analysis_points.append(f"Stock down {abs(day_change_pct):.1f}% - potential buying opportunity")
        
        if volume_ratio > 2:
            analysis_points.append(f"High volume ({volume_ratio:.1f}x average) - strong interest")
        elif volume_ratio < 0.5:
            analysis_points.append(f"Low volume ({volume_ratio:.1f}x average) - limited liquidity")
        
        if current_price > ma_50:
            analysis_points.append(f"Price above 50-day MA (${ma_50:.2f}) - bullish trend")
        else:
            analysis_points.append(f"Price below 50-day MA (${ma_50:.2f}) - bearish trend")
        
        return {
            "ticker": ticker,
            "current_price": current_price,
            "previous_close": previous_close,
            "day_change_percent": round(day_change_pct, 2),
            "recommendation": recommendation,
            "risk_level": risk_level,
            "entry_points": {
                "conservative": f"${conservative_entry} (wait for dip to 20-day MA)",
                "moderate": f"${moderate_entry} (slight pullback from current)",
                "aggressive": f"${current_price} - ${aggressive_entry} (current levels)"
            },
            "stop_loss": f"${stop_loss}",
            "key_levels": {
                "support": f"${recent_low:.2f}",
                "resistance": f"${recent_high:.2f}",
                "ma_20": f"${ma_20:.2f}",
                "ma_50": f"${ma_50:.2f}",
                "52_week_high": f"${high_52w:.2f}",
                "52_week_low": f"${low_52w:.2f}"
            },
            "analysis": analysis_points,
            "volatility": f"{volatility:.2f}%",
            "volume_ratio": f"{volume_ratio:.2f}x average"
        }
    
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_top_performers(days: int = 7, limit: int = 10) -> dict:
    """
    Get list of top performing stocks from a predefined watchlist over the specified period.
    Args:
        days (int): Number of days to analyze (default: 7)
        limit (int): Maximum number of stocks to return (default: 10)
    Returns:
        dict: List of top performing stocks with performance metrics
    """
    try:
        # Predefined watchlist - you can customize this list
        watchlist = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AMD', 
            'NFLX', 'DIS', 'PYPL', 'INTC', 'CSCO', 'ADBE', 'CRM', 'ORCL',
            'BABA', 'V', 'MA', 'JPM', 'BAC', 'WMT', 'PFE', 'KO', 'PEP',
            'NKE', 'MCD', 'SBUX', 'COST', 'HD'
        ]
        
        performers = []
        
        for ticker in watchlist:
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period=f"{days+5}d")
                
                if len(hist) < days:
                    continue
                
                start_price = hist['Close'].iloc[-days-1]
                current_price = hist['Close'].iloc[-1]
                change_pct = ((current_price - start_price) / start_price * 100)
                
                # Get additional info
                info = stock.info
                volume_avg = hist['Volume'].mean()
                
                performers.append({
                    'ticker': ticker,
                    'company': info.get('shortName', ticker),
                    'current_price': round(current_price, 2),
                    'change_percent': round(change_pct, 2),
                    'change_amount': round(current_price - start_price, 2),
                    'volume': int(hist['Volume'].iloc[-1]),
                    'avg_volume': int(volume_avg),
                    'market_cap': info.get('marketCap', 0),
                    'sector': info.get('sector', 'N/A')
                })
            except Exception as e:
                continue
        
        # Sort by performance
        performers.sort(key=lambda x: x['change_percent'], reverse=True)
        top_performers = performers[:limit]
        
        return {
            "period_days": days,
            "total_analyzed": len(performers),
            "top_performers": top_performers,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_price_trajectory(ticker: str, days: int = 30) -> dict:
    """
    Analyze price trajectory and predict potential direction based on historical patterns.
    Args:
        ticker (str): The stock ticker symbol
        days (int): Number of days to analyze (default: 30)
    Returns:
        dict: Trajectory analysis including:
            - trend: Overall trend (Uptrend, Downtrend, Sideways)
            - momentum: Price momentum indicator
            - prediction: Short-term direction prediction
            - confidence: Confidence level of prediction
            - historical_data: Recent price data points
            - key_metrics: Important trajectory metrics
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=f"{days+10}d")
        
        if hist.empty:
            return {"error": "Unable to fetch historical data"}
        
        # Calculate trend indicators
        closes = hist['Close'].values
        dates = hist.index.tolist()
        
        # Linear regression for trend
        x = np.arange(len(closes))
        slope, intercept = np.polyfit(x, closes, 1)
        
        # Determine trend
        trend = "Sideways"
        if slope > closes[-1] * 0.001:
            trend = "Uptrend"
        elif slope < -closes[-1] * 0.001:
            trend = "Downtrend"
        
        # Calculate momentum
        momentum = ((closes[-1] - closes[0]) / closes[0] * 100)
        
        # Calculate moving averages for crossover signals
        if len(closes) >= 20:
            ma_5 = closes[-5:].mean()
            ma_20 = closes[-20:].mean()
            
            # Momentum indicator
            if ma_5 > ma_20 and closes[-1] > ma_5:
                momentum_signal = "Strong Bullish"
            elif ma_5 > ma_20:
                momentum_signal = "Bullish"
            elif ma_5 < ma_20 and closes[-1] < ma_5:
                momentum_signal = "Strong Bearish"
            elif ma_5 < ma_20:
                momentum_signal = "Bearish"
            else:
                momentum_signal = "Neutral"
        else:
            momentum_signal = "Insufficient data"
        
        # Calculate volatility
        returns = np.diff(closes) / closes[:-1]
        volatility = np.std(returns) * 100
        
        # Predict direction
        recent_slope = (closes[-5:].mean() - closes[-10:-5].mean()) / closes[-10:-5].mean() * 100
        
        prediction = "Neutral"
        confidence = "Low"
        
        if abs(recent_slope) > 5:
            confidence = "High"
        elif abs(recent_slope) > 2:
            confidence = "Medium"
        
        if recent_slope > 2:
            prediction = "Upward"
        elif recent_slope < -2:
            prediction = "Downward"
        
        # Calculate support and resistance
        recent_prices = closes[-days:]
        support = np.percentile(recent_prices, 25)
        resistance = np.percentile(recent_prices, 75)
        
        # Format historical data (last 10 days)
        historical_data = []
        for i in range(min(10, len(hist))):
            idx = -10 + i
            if abs(idx) <= len(hist):
                historical_data.append({
                    'date': dates[idx].strftime('%Y-%m-%d'),
                    'close': round(hist['Close'].iloc[idx], 2),
                    'volume': int(hist['Volume'].iloc[idx])
                })
        
        return {
            "ticker": ticker,
            "analysis_period": f"{days} days",
            "current_price": round(closes[-1], 2),
            "trend": trend,
            "momentum": {
                "percent_change": round(momentum, 2),
                "signal": momentum_signal
            },
            "prediction": {
                "direction": prediction,
                "confidence": confidence,
                "rationale": f"Based on recent {days}-day trend analysis and momentum indicators"
            },
            "key_metrics": {
                "volatility": f"{volatility:.2f}%",
                "avg_price": round(closes.mean(), 2),
                "price_range": f"${closes.min():.2f} - ${closes.max():.2f}",
                "support_level": f"${support:.2f}",
                "resistance_level": f"${resistance:.2f}",
                "trend_slope": f"{slope:.4f}"
            },
            "historical_data": historical_data,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def get_stocks_under_price(max_price: float = 10.0, min_price: float = 1.0, limit: int = 20) -> dict:
    """
    Get list of stocks trading within a specified price range from the watchlist.
    Args:
        max_price (float): Maximum stock price to filter (default: $10.00)
        min_price (float): Minimum stock price to filter (default: $1.00)
        limit (int): Maximum number of stocks to return (default: 20)
    Returns:
        dict: List of affordable stocks with their current prices and daily changes
    """
    try:
        # Extended watchlist for affordable stocks (60+ tickers)
        watchlist = [
            # Major stocks that sometimes dip
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AMD', 
            'NFLX', 'DIS', 'PYPL', 'INTC', 'CSCO', 'ADBE', 'CRM', 'ORCL',
            'BABA', 'V', 'MA', 'JPM', 'BAC', 'WMT', 'PFE', 'KO', 'PEP',
            'NKE', 'MCD', 'SBUX', 'COST', 'HD', 
            # Affordable stocks typically under $10
            'F', 'AAL', 'CCL', 'PLUG', 'SOFI', 'NIO', 'LCID', 'RIVN', 
            'UBER', 'LYFT', 'SNAP', 'PINS', 'ZM', 'DKNG', 'PLTR', 'BB', 
            'NOK', 'AMC', 'GME', 'WKHS', 'SIRI', 'VALE', 'GOLD', 'ABEV',
            'GNUS', 'IDEX', 'BNGO', 'SNDL', 'CLVS', 'INO', 'NKLA',
            'TOPS', 'SHIP', 'CLOV', 'WISH', 'RIDE', 'MULN',
            'EXPR', 'KOSS', 'SENS', 'OCGN', 'GEVO', 'FCEL', 'MARA', 'RIOT',
            'ACB', 'CGC', 'TLRY', 'HEXO', 'OGI', 'CRON'
        ]
        
        affordable_stocks = []
        
        for ticker in watchlist:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                hist = stock.history(period="5d")
                
                if hist.empty:
                    continue
                
                current_price = info.get('currentPrice', hist['Close'].iloc[-1])
                
                # Filter by price range (min and max)
                if min_price <= current_price <= max_price:
                    previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                    day_change = current_price - previous_close
                    day_change_pct = (day_change / previous_close * 100) if previous_close else 0
                    
                    affordable_stocks.append({
                        'ticker': ticker,
                        'company': info.get('shortName', ticker),
                        'current_price': round(current_price, 2),
                        'previous_close': round(previous_close, 2),
                        'day_change': round(day_change, 2),
                        'day_change_percent': round(day_change_pct, 2),
                        'volume': int(hist['Volume'].iloc[-1]),
                        'market_cap': info.get('marketCap', 0),
                        'sector': info.get('sector', 'N/A'),
                        'industry': info.get('industry', 'N/A')
                    })
            except Exception as e:
                continue
        
        # Sort by price (lowest first)
        affordable_stocks.sort(key=lambda x: x['current_price'])
        
        return {
            "max_price": max_price,
            "min_price": min_price,
            "price_range": f"${min_price} - ${max_price}",
            "total_found": len(affordable_stocks),
            "stocks": affordable_stocks[:limit],
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def generate_daily_analysis_email(
    max_price: float = 10.0,
    min_price: float = 1.0,
    recipient_email: str = "",
    include_recommendations: bool = True
) -> dict:
    """
    Generate a formatted daily analysis email content for stocks within specified price range.
    Args:
        max_price (float): Maximum stock price to include (default: $10.00)
        min_price (float): Minimum stock price to include (default: $1.00)
        recipient_email (str): Email address to send to (required)
        include_recommendations (bool): Include buying recommendations (default: True)
    Returns:
        dict: Email content and metadata ready to send
    """
    try:
        if not recipient_email:
            return {"error": "Recipient email address is required"}
        
        # Get stocks within price range
        stocks_data = await get_stocks_under_price(max_price=max_price, min_price=min_price, limit=20)
        
        if "error" in stocks_data:
            return stocks_data
        
        stocks = stocks_data['stocks']
        
        if not stocks:
            return {
                "error": f"No stocks found between ${min_price} and ${max_price}",
                "message": "Try adjusting the price range"
            }
        
        # Prepare top movers data if recommendations are included
        top_movers_data = []
        if include_recommendations:
            # Get top 3 gainers and losers
            sorted_by_change = sorted(stocks, key=lambda x: x['day_change_percent'], reverse=True)
            top_gainers = sorted_by_change[:3]
            top_losers = sorted_by_change[-3:] if len(sorted_by_change) >= 3 else []
            
            for stock in top_gainers + top_losers:
                rec = await get_buying_recommendation(stock['ticker'])
                top_movers_data.append({
                    'stock': stock,
                    'recommendation': rec if "error" not in rec else {}
                })
        
        # Use email notifier to generate content
        notifier = StockEmailNotifier()
        html_content = notifier.generate_html_email(
            stocks=stocks,
            max_price=max_price,
            include_recommendations=include_recommendations,
            top_movers_data=top_movers_data if top_movers_data else None
        )
        text_content = notifier.generate_text_email(stocks, max_price)
        
        return {
            "subject": f"Daily Stock Analysis - Stocks ${min_price}-${max_price} ({datetime.now().strftime('%Y-%m-%d')})",
            "recipient": recipient_email,
            "html_content": html_content,
            "text_content": text_content,
            "total_stocks": len(stocks),
            "price_range": f"${min_price} - ${max_price}",
            "generated_at": datetime.now().isoformat(),
            "ready_to_send": True,
            "message": "Email content generated successfully. Use send_email_notification to send."
        }
    
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def send_email_notification(
    recipient_email: str,
    subject: str,
    html_content: str,
    text_content: str,
    smtp_server: str = "smtp.gmail.com",
    smtp_port: int = 587,
    sender_email: Optional[str] = None,
    sender_password: Optional[str] = None
) -> dict:
    """
    Send email notification with daily stock analysis.
    Args:
        recipient_email (str): Email address to send to
        subject (str): Email subject line
        html_content (str): HTML formatted email body
        text_content (str): Plain text email body
        smtp_server (str): SMTP server address (default: smtp.gmail.com)
        smtp_port (int): SMTP port (default: 587)
        sender_email (str): Sender's email address (optional)
        sender_password (str): Sender's email password or app password (optional)
    Returns:
        dict: Status of email sending operation
    """
    try:
        if not sender_email or not sender_password:
            return {
                "error": "Email credentials required",
                "message": "Please provide sender_email and sender_password",
                "instructions": """
To send emails, you need to:
1. Provide sender_email (your Gmail address)
2. Provide sender_password (use Gmail App Password, not regular password)
3. To create App Password: 
   - Go to Google Account Settings
   - Security > 2-Step Verification > App Passwords
   - Generate password for 'Mail' application
                """,
                "alternative": "You can also save email content to a file using the generated html_content"
            }
        
        # Use email notifier to send
        notifier = StockEmailNotifier(smtp_server=smtp_server, smtp_port=smtp_port)
        result = notifier.send_email(
            recipient_email=recipient_email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
            sender_email=sender_email,
            sender_password=sender_password
        )
        
        return result
    
    except Exception as e:
        return {
            "error": str(e),
            "message": "Failed to send email. Check your credentials and network connection."
        }

@mcp.tool()
async def save_daily_analysis_to_file(
    max_price: float = 10.0,
    filename: Optional[str] = None
) -> dict:
    """
    Save daily analysis to an HTML file instead of emailing.
    Args:
        max_price (float): Maximum stock price to include (default: $10.00)
        filename (str): Output filename (optional, auto-generated if not provided)
    Returns:
        dict: File path and status
    """
    try:
        # Generate email content (without sending)
        email_data = await generate_daily_analysis_email(
            max_price=max_price,
            recipient_email="none@example.com",
            include_recommendations=True
        )
        
        if "error" in email_data:
            return email_data
        
        # Use email notifier to save to file
        notifier = StockEmailNotifier()
        result = notifier.save_to_file(email_data['html_content'], filename)
        
        if result['status'] == 'success':
            result['total_stocks'] = email_data['total_stocks']
        
        return result
    
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
