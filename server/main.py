from mcp.server.fastmcp import FastMCP
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
from typing import Optional
from email_notifier import StockEmailNotifier, create_and_send_email, create_and_save_email
from alpha_vantage_client import (
    fetch_alpha_vantage_quote,
    fetch_alpha_vantage_overview,
    fetch_alpha_vantage_technical
)

# Initialize FastMCP server
mcp = FastMCP("stock-api")

# Helper function for generating recommendation reasoning
def generate_recommendation_reasoning(stock: dict, recommendation: dict, trajectory: dict = None) -> dict:
    """
    Generate detailed reasoning for why a stock is recommended for buy/sell
    based on price movements, technical indicators, and trajectory
    """
    reasoning = {
        'summary': '',
        'key_factors': [],
        'price_analysis': '',
        'trajectory_insight': '',
        'action_rationale': ''
    }
    
    rec_type = recommendation.get('recommendation', 'Hold')
    day_change = stock.get('day_change_percent', 0)
    current_price = stock.get('current_price', 0)
    risk = recommendation.get('risk_level', 'Medium')
    
    # Price Movement Analysis
    if day_change > 5:
        reasoning['price_analysis'] = f"Stock surged {day_change:.1f}% today, showing strong upward momentum. "
        if rec_type in ['Wait for Pullback', 'Overextended - Wait']:
            reasoning['price_analysis'] += "However, this rapid increase suggests overbought conditions. Consider waiting for a pullback to enter at better prices."
        else:
            reasoning['price_analysis'] += "This momentum could continue if supported by strong fundamentals."
    elif day_change > 2:
        reasoning['price_analysis'] = f"Stock gained {day_change:.1f}% today, indicating positive sentiment. "
        reasoning['price_analysis'] += "Moderate upward movement suggests healthy price action without being overextended."
    elif day_change < -5:
        reasoning['price_analysis'] = f"Stock dropped {abs(day_change):.1f}% today, creating a potential buying opportunity. "
        if rec_type in ['Strong Buy', 'Buy']:
            reasoning['price_analysis'] += "This dip could be an excellent entry point for long-term holders."
    elif day_change < -2:
        reasoning['price_analysis'] = f"Stock declined {abs(day_change):.1f}% today. "
        reasoning['price_analysis'] += "Minor pullback may present a better entry point than previous levels."
    else:
        reasoning['price_analysis'] = f"Stock moved {day_change:+.1f}% today, showing relatively stable price action. "
        reasoning['price_analysis'] += "Low volatility suggests consolidation phase."
    
    # Trajectory Insight
    if trajectory and trajectory.get('trend'):
        trend = trajectory.get('trend', 'Unknown')
        momentum = trajectory.get('momentum', {})
        prediction = trajectory.get('prediction', {})
        
        momentum_signal = momentum.get('signal', 'Neutral')
        predicted_direction = prediction.get('direction', 'Neutral')
        confidence = prediction.get('confidence', 'Low')
        
        reasoning['trajectory_insight'] = f"30-day trajectory shows {trend} pattern with {momentum_signal} momentum. "
        reasoning['trajectory_insight'] += f"Prediction: {predicted_direction} movement with {confidence} confidence. "
        
        if trend == 'Uptrend' and predicted_direction == 'Upward':
            reasoning['trajectory_insight'] += "Strong technical setup favors continued upside."
        elif trend == 'Downtrend' and predicted_direction == 'Downward':
            reasoning['trajectory_insight'] += "Bearish technical pattern suggests caution."
        elif trend == 'Sideways':
            reasoning['trajectory_insight'] += "Consolidation phase - waiting for breakout direction."
    
    # Action Rationale
    if rec_type == 'Strong Buy':
        reasoning['action_rationale'] = f"STRONG BUY: Stock is trading below key support levels at ${current_price}. "
        if day_change < 0:
            reasoning['action_rationale'] += f"Today's {abs(day_change):.1f}% dip presents an excellent entry opportunity. "
        reasoning['action_rationale'] += f"Risk level is {risk}. Consider position sizing accordingly."
        reasoning['key_factors'] = [
            'Trading below 20-day moving average',
            'Recent price decline creates value opportunity',
            'Technical indicators suggest oversold conditions',
            'Strong upside potential from current levels'
        ]
        
    elif rec_type == 'Buy':
        reasoning['action_rationale'] = f"BUY: Stock shows positive signals at ${current_price}. "
        if day_change > 0:
            reasoning['action_rationale'] += f"Today's {day_change:.1f}% gain confirms positive momentum. "
        reasoning['action_rationale'] += f"Risk level is {risk}. Good entry point for building position."
        reasoning['key_factors'] = [
            'Favorable technical setup',
            'Trading near support levels',
            'Positive momentum indicators',
            'Acceptable risk-reward ratio'
        ]
        
    elif rec_type == 'Hold':
        reasoning['action_rationale'] = f"HOLD: Stock at ${current_price} doesn't present clear entry opportunity. "
        reasoning['action_rationale'] += "Wait for more definitive signals before taking action. "
        reasoning['key_factors'] = [
            'Neutral technical indicators',
            'Waiting for trend confirmation',
            'No urgent catalysts',
            'Better opportunities may emerge'
        ]
        
    elif rec_type == 'Wait for Pullback':
        reasoning['action_rationale'] = f"WAIT: Stock surged {day_change:.1f}% to ${current_price}. "
        reasoning['action_rationale'] += "Overbought conditions suggest waiting for consolidation before entry. "
        reasoning['key_factors'] = [
            f'Rapid {day_change:.1f}% increase indicates overbought',
            'High risk of short-term pullback',
            'Better entry prices likely after consolidation',
            'Wait for 3-5% retracement'
        ]
        
    elif rec_type == 'Overextended - Wait':
        reasoning['action_rationale'] = f"OVEREXTENDED: Stock at ${current_price} has risen too far too fast. "
        reasoning['action_rationale'] += "Wait for significant pullback before considering entry. "
        reasoning['key_factors'] = [
            'Trading far above moving averages',
            'Momentum unsustainable at current levels',
            'High probability of correction',
            'Wait for 10%+ pullback'
        ]
    
    # Generate summary
    reasoning['summary'] = f"{rec_type} recommendation for {stock.get('company', stock.get('ticker'))} "
    reasoning['summary'] += f"at ${current_price} (${day_change:+.2f}% today). "
    reasoning['summary'] += f"{risk} risk. " + reasoning['action_rationale'][:100] + "..."
    
    return reasoning

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
async def get_top_stock_recommendations_in_range(
    max_price: float = 10.0,
    min_price: float = 1.0,
    top_n: int = 10,
    use_extended_watchlist: bool = True
) -> dict:
    """
    Get top N stock recommendations within a specified price range with detailed analysis.
    Args:
        max_price (float): Maximum stock price to filter (default: $10.00)
        min_price (float): Minimum stock price to filter (default: $1.00)
        top_n (int): Number of top recommendations to return (default: 10)
        use_extended_watchlist (bool): If True, searches 60+ stocks from extended watchlist. 
                                       If False, only uses configured stocks from config.yaml (default: True)
    Returns:
        dict: Top N stock recommendations with buying recommendations, entry points, and analysis
    """
    try:
        # Determine which stocks to analyze
        if use_extended_watchlist:
            # Get stocks from extended watchlist (60+ stocks)
            stocks_data = await get_stocks_under_price(max_price=max_price, min_price=min_price, limit=50)
        else:
            # Use only configured stocks from config.yaml (7 default stocks)
            from config_manager import ConfigManager
            config = ConfigManager()
            config_stocks = config.get_stock_list('default')
            
            # Manually filter configured stocks by price
            affordable_stocks = []
            for ticker in config_stocks:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    hist = stock.history(period="5d")
                    
                    if hist.empty:
                        continue
                    
                    current_price = info.get('currentPrice', hist['Close'].iloc[-1])
                    
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
            
            stocks_data = {
                "stocks": affordable_stocks,
                "total_found": len(affordable_stocks),
                "source": "config.yaml default list"
            }
        
        if "error" in stocks_data:
            return stocks_data
        
        stocks = stocks_data['stocks']
        
        if not stocks:
            return {
                "error": f"No stocks found between ${min_price} and ${max_price}",
                "message": "Try adjusting the price range"
            }
        
        # Sort by daily change percentage (top performers)
        sorted_stocks = sorted(stocks, key=lambda x: x['day_change_percent'], reverse=True)
        
        # Get top N stocks
        top_stocks = sorted_stocks[:min(top_n, len(sorted_stocks))]
        
        # Get detailed recommendations for each
        recommendations = []
        for stock in top_stocks:
            try:
                # Get buying recommendation
                rec = await get_buying_recommendation(stock['ticker'])
                if "error" in rec:
                    continue
                
                # Get price trajectory prediction
                trajectory = await get_price_trajectory(stock['ticker'], days=30)
                
                # Generate detailed reasoning for recommendation
                reasoning = generate_recommendation_reasoning(
                    stock=stock,
                    recommendation=rec,
                    trajectory=trajectory if "error" not in trajectory else None
                )
                
                recommendations.append({
                    'ticker': stock['ticker'],
                    'company': stock['company'],
                    'current_price': stock['current_price'],
                    'day_change_percent': stock['day_change_percent'],
                    'volume': stock['volume'],
                    'recommendation': rec['recommendation'],
                    'risk_level': rec['risk_level'],
                    'entry_points': rec['entry_points'],
                    'stop_loss': rec['stop_loss'],
                    'key_levels': rec['key_levels'],
                    'analysis': rec['analysis'],
                    'trajectory': {
                        'trend': trajectory.get('trend', 'Unknown') if trajectory and "error" not in trajectory else 'Unknown',
                        'prediction': trajectory.get('prediction', {}) if trajectory and "error" not in trajectory else {},
                        'momentum': trajectory.get('momentum', {}) if trajectory and "error" not in trajectory else {}
                    },
                    'recommendation_reasoning': reasoning
                })
            except Exception as e:
                continue
        
        return {
            "price_range": f"${min_price} - ${max_price}",
            "requested_count": top_n,
            "returned_count": len(recommendations),
            "stock_source": "Extended watchlist (60+ stocks)" if use_extended_watchlist else "Config default list (7 stocks)",
            "total_stocks_analyzed": stocks_data.get('total_found', len(stocks)),
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat(),
            "note": f"Top {len(recommendations)} stock recommendations based on daily performance within your price range"
        }
    
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
async def generate_daily_analysis_email(
    max_price: float = 10.0,
    min_price: float = 1.0,
    recipient_email: str = "",
    include_recommendations: bool = True,
    top_n_recommendations: int = 10
) -> dict:
    """
    Generate a formatted daily analysis email content for stocks within specified price range.
    Args:
        max_price (float): Maximum stock price to include (default: $10.00)
        min_price (float): Minimum stock price to include (default: $1.00)
        recipient_email (str): Email address to send to (required)
        include_recommendations (bool): Include buying recommendations (default: True)
        top_n_recommendations (int): Number of top stock recommendations to include (default: 10)
    Returns:
        dict: Email content and metadata ready to send
    """
    try:
        if not recipient_email:
            return {"error": "Recipient email address is required"}
        
        # Get stocks within price range (fetch more to have options)
        stocks_data = await get_stocks_under_price(max_price=max_price, min_price=min_price, limit=50)
        
        if "error" in stocks_data:
            return stocks_data
        
        stocks = stocks_data['stocks']
        
        if not stocks:
            return {
                "error": f"No stocks found between ${min_price} and ${max_price}",
                "message": "Try adjusting the price range"
            }
        
        # Prepare top N recommendations if included
        top_movers_data = []
        if include_recommendations:
            # Get top N stocks by daily change (both gainers and some interesting movers)
            sorted_by_change = sorted(stocks, key=lambda x: x['day_change_percent'], reverse=True)
            
            # Get top N stocks to analyze
            stocks_to_analyze = sorted_by_change[:top_n_recommendations]
            
            for stock in stocks_to_analyze:
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

@mcp.tool()
async def get_multi_source_stock_data(ticker: str) -> dict:
    """
    Fetch stock data from multiple sources (Yahoo Finance + Alpha Vantage) for comparison.
    Args:
        ticker (str): The stock ticker symbol
    Returns:
        dict: Combined data from both sources with comparison metrics
    """
    try:
        # Fetch from Yahoo Finance
        yf_stock = yf.Ticker(ticker)
        yf_info = yf_stock.info
        yf_hist = yf_stock.history(period="5d")
        
        yf_data = {
            'source': 'Yahoo Finance',
            'current_price': yf_info.get('currentPrice', yf_hist['Close'].iloc[-1] if not yf_hist.empty else None),
            'previous_close': yf_info.get('previousClose'),
            'volume': yf_info.get('volume'),
            'market_cap': yf_info.get('marketCap'),
            'pe_ratio': yf_info.get('trailingPE'),
            'dividend_yield': yf_info.get('dividendYield'),
            '52_week_high': yf_info.get('fiftyTwoWeekHigh'),
            '52_week_low': yf_info.get('fiftyTwoWeekLow'),
            'sector': yf_info.get('sector'),
            'industry': yf_info.get('industry'),
            'company_name': yf_info.get('shortName')
        }
        
        # Fetch from Alpha Vantage
        av_quote = fetch_alpha_vantage_quote(ticker)
        av_overview = fetch_alpha_vantage_overview(ticker)
        av_technical = fetch_alpha_vantage_technical(ticker)
        
        av_data = {
            'source': 'Alpha Vantage',
            'current_price': av_quote.get('price') if 'error' not in av_quote else None,
            'previous_close': av_quote.get('previous_close') if 'error' not in av_quote else None,
            'volume': av_quote.get('volume') if 'error' not in av_quote else None,
            'market_cap': av_overview.get('market_cap') if 'error' not in av_overview else None,
            'pe_ratio': av_overview.get('pe_ratio') if 'error' not in av_overview else None,
            'dividend_yield': av_overview.get('dividend_yield') if 'error' not in av_overview else None,
            '52_week_high': av_overview.get('52_week_high') if 'error' not in av_overview else None,
            '52_week_low': av_overview.get('52_week_low') if 'error' not in av_overview else None,
            'sector': av_overview.get('sector') if 'error' not in av_overview else None,
            'industry': av_overview.get('industry') if 'error' not in av_overview else None,
            'company_name': av_overview.get('name') if 'error' not in av_overview else None,
            'rsi': av_technical.get('rsi'),
            'rsi_signal': av_technical.get('rsi_signal'),
            'latest_trading_day': av_quote.get('latest_trading_day') if 'error' not in av_quote else None
        }
        
        # Calculate discrepancies
        price_diff = None
        price_diff_pct = None
        if yf_data['current_price'] and av_data['current_price']:
            price_diff = abs(yf_data['current_price'] - av_data['current_price'])
            price_diff_pct = (price_diff / yf_data['current_price'] * 100)
        
        return {
            'ticker': ticker,
            'yahoo_finance': yf_data,
            'alpha_vantage': av_data,
            'comparison': {
                'price_difference': round(price_diff, 2) if price_diff else None,
                'price_difference_percent': round(price_diff_pct, 2) if price_diff_pct else None,
                'data_consistency': 'High' if price_diff_pct and price_diff_pct < 0.5 else 'Medium' if price_diff_pct and price_diff_pct < 2 else 'Low',
                'note': 'Prices may differ due to update timing and data source delays'
            },
            'generated_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {'error': str(e)}

@mcp.tool()
async def get_comprehensive_recommendation(ticker: str, use_alpha_vantage: bool = True) -> dict:
    """
    Get comprehensive buying recommendation combining data from multiple sources.
    Args:
        ticker (str): The stock ticker symbol
        use_alpha_vantage (bool): Whether to include Alpha Vantage data (default: True)
    Returns:
        dict: Enhanced recommendations with multi-source analysis
    """
    try:
        # Get Yahoo Finance recommendation (existing function)
        yf_recommendation = await get_buying_recommendation(ticker)
        
        if 'error' in yf_recommendation:
            return yf_recommendation
        
        # Initialize result with Yahoo Finance data
        result = {
            'ticker': ticker,
            'primary_source': 'Yahoo Finance',
            'yf_recommendation': yf_recommendation,
            'generated_at': datetime.now().isoformat()
        }
        
        # Add Alpha Vantage data if requested
        if use_alpha_vantage:
            av_quote = fetch_alpha_vantage_quote(ticker)
            av_overview = fetch_alpha_vantage_overview(ticker)
            av_technical = fetch_alpha_vantage_technical(ticker)
            
            av_insights = {
                'source': 'Alpha Vantage',
                'current_price': av_quote.get('price') if 'error' not in av_quote else None,
                'change_percent': av_quote.get('change_percent') if 'error' not in av_quote else None,
                'rsi': av_technical.get('rsi'),
                'rsi_signal': av_technical.get('rsi_signal'),
                'analyst_target_price': av_overview.get('analyst_rating') if 'error' not in av_overview else None
            }
            
            result['av_insights'] = av_insights
            
            # Generate combined recommendation
            combined_signals = []
            
            # RSI-based signal
            if av_technical.get('rsi'):
                rsi = av_technical['rsi']
                if rsi < 30:
                    combined_signals.append('RSI indicates oversold condition - potential buying opportunity')
                elif rsi > 70:
                    combined_signals.append('RSI indicates overbought condition - consider waiting')
                else:
                    combined_signals.append(f'RSI at {rsi:.1f} - neutral territory')
            
            # Price comparison
            yf_price = yf_recommendation.get('current_price')
            av_price = av_quote.get('price') if 'error' not in av_quote else None
            
            if yf_price and av_price:
                price_diff_pct = abs(yf_price - av_price) / yf_price * 100
                if price_diff_pct > 2:
                    combined_signals.append(f'Warning: Price discrepancy of {price_diff_pct:.2f}% between sources')
                else:
                    combined_signals.append('Price data consistent across sources')
            
            # Generate consensus recommendation
            yf_rec = yf_recommendation.get('recommendation', 'Hold')
            rsi_signal = av_technical.get('rsi_signal', 'Neutral')
            
            if 'Buy' in yf_rec and rsi_signal == 'Oversold':
                consensus = 'Strong Buy - Confirmed by multiple indicators'
            elif 'Buy' in yf_rec or rsi_signal == 'Oversold':
                consensus = 'Buy - Positive signals from analysis'
            elif yf_rec == 'Hold' and rsi_signal == 'Neutral':
                consensus = 'Hold - Wait for clearer signals'
            elif 'Wait' in yf_rec or rsi_signal == 'Overbought':
                consensus = 'Wait - Overbought conditions detected'
            else:
                consensus = 'Hold - Mixed signals'
            
            result['consensus_recommendation'] = {
                'overall': consensus,
                'signals': combined_signals,
                'confidence': 'High' if len(combined_signals) >= 3 else 'Medium'
            }
        
        return result
    
    except Exception as e:
        return {'error': str(e)}

@mcp.tool()
async def compare_stock_sources(ticker: str) -> dict:
    """
    Detailed comparison of stock data from Yahoo Finance vs Alpha Vantage.
    Args:
        ticker (str): The stock ticker symbol
    Returns:
        dict: Side-by-side comparison with discrepancy analysis
    """
    try:
        multi_source_data = await get_multi_source_stock_data(ticker)
        
        if 'error' in multi_source_data:
            return multi_source_data
        
        yf = multi_source_data['yahoo_finance']
        av = multi_source_data['alpha_vantage']
        
        # Calculate field-by-field comparisons
        comparisons = []
        
        fields_to_compare = [
            ('current_price', 'Current Price', '$'),
            ('previous_close', 'Previous Close', '$'),
            ('volume', 'Volume', ''),
            ('market_cap', 'Market Cap', '$'),
            ('pe_ratio', 'P/E Ratio', ''),
            ('52_week_high', '52 Week High', '$'),
            ('52_week_low', '52 Week Low', '$')
        ]
        
        for field, label, prefix in fields_to_compare:
            yf_val = yf.get(field)
            av_val = av.get(field)
            
            if yf_val is not None and av_val is not None:
                diff = abs(yf_val - av_val)
                diff_pct = (diff / yf_val * 100) if yf_val != 0 else 0
                
                comparisons.append({
                    'field': label,
                    'yahoo_finance': f"{prefix}{yf_val:,.2f}" if prefix == '$' else f"{yf_val:,.0f}",
                    'alpha_vantage': f"{prefix}{av_val:,.2f}" if prefix == '$' else f"{av_val:,.0f}",
                    'difference': f"{prefix}{diff:,.2f}" if prefix == '$' else f"{diff:,.0f}",
                    'difference_percent': f"{diff_pct:.2f}%",
                    'status': 'Match' if diff_pct < 0.5 else 'Minor Variance' if diff_pct < 2 else 'Significant Variance'
                })
            else:
                comparisons.append({
                    'field': label,
                    'yahoo_finance': str(yf_val) if yf_val is not None else 'N/A',
                    'alpha_vantage': str(av_val) if av_val is not None else 'N/A',
                    'difference': 'N/A',
                    'difference_percent': 'N/A',
                    'status': 'Incomplete Data'
                })
        
        # Add unique Alpha Vantage metrics
        if av.get('rsi'):
            comparisons.append({
                'field': 'RSI (14-day)',
                'yahoo_finance': 'Not Available',
                'alpha_vantage': f"{av['rsi']:.2f}",
                'difference': 'N/A',
                'difference_percent': 'N/A',
                'status': f"Alpha Vantage Only - {av['rsi_signal']}"
            })
        
        return {
            'ticker': ticker,
            'comparison_table': comparisons,
            'summary': {
                'total_fields_compared': len([c for c in comparisons if c['status'] != 'Incomplete Data']),
                'matching_fields': len([c for c in comparisons if c['status'] == 'Match']),
                'variance_fields': len([c for c in comparisons if 'Variance' in c['status']]),
                'overall_reliability': multi_source_data['comparison']['data_consistency']
            },
            'recommendation': 'Data appears reliable' if multi_source_data['comparison']['data_consistency'] in ['High', 'Medium'] else 'Verify data before trading',
            'generated_at': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {'error': str(e)}

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
