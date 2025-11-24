"""
Feature: Historical Performance Tracker
Analyzes stocks over the past 3 months and provides recommendations
"""
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta


async def analyze_3month_performance(ticker: str) -> dict:
    """
    Analyze stock performance over the past 3 months
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        dict: 3-month performance analysis
    """
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="3mo")
        info = stock.info
        
        if hist.empty:
            return {"error": f"No historical data for {ticker}"}
        
        # Calculate performance metrics
        start_price = hist['Close'].iloc[0]
        end_price = hist['Close'].iloc[-1]
        change_3m = ((end_price - start_price) / start_price * 100)
        
        # Price statistics
        high_3m = hist['High'].max()
        low_3m = hist['Low'].min()
        avg_price_3m = hist['Close'].mean()
        
        # Volume analysis
        avg_volume_3m = hist['Volume'].mean()
        recent_volume = hist['Volume'].tail(5).mean()
        volume_trend = "Increasing" if recent_volume > avg_volume_3m else "Decreasing"
        
        # Volatility
        returns = hist['Close'].pct_change()
        volatility_3m = returns.std() * np.sqrt(63) * 100  # Annualized
        
        # Trend analysis
        closes = hist['Close'].values
        x = np.arange(len(closes))
        slope, _ = np.polyfit(x, closes, 1)
        
        trend = "Sideways"
        if slope > closes[-1] * 0.001:
            trend = "Uptrend"
        elif slope < -closes[-1] * 0.001:
            trend = "Downtrend"
        
        # Moving averages
        ma_20 = hist['Close'].tail(20).mean()
        ma_50 = hist['Close'].tail(50).mean()
        
        # Recommendation based on 3-month analysis
        recommendation_score = 0
        
        # Positive performance
        if change_3m > 20:
            recommendation_score += 3
        elif change_3m > 10:
            recommendation_score += 2
        elif change_3m > 0:
            recommendation_score += 1
        
        # Trend alignment
        if trend == "Uptrend" and end_price > ma_20:
            recommendation_score += 2
        
        # Volume confirmation
        if volume_trend == "Increasing":
            recommendation_score += 1
        
        # Generate recommendation
        if recommendation_score >= 5:
            recommendation = "Strong Buy"
        elif recommendation_score >= 3:
            recommendation = "Buy"
        elif recommendation_score >= 1:
            recommendation = "Hold"
        else:
            recommendation = "Cautious - Monitor"
        
        return {
            "ticker": ticker,
            "company": info.get('shortName', ticker),
            "current_price": round(end_price, 2),
            "performance_3m": {
                "start_price": round(start_price, 2),
                "end_price": round(end_price, 2),
                "change_percent": round(change_3m, 2),
                "change_amount": round(end_price - start_price, 2)
            },
            "price_stats": {
                "high_3m": round(high_3m, 2),
                "low_3m": round(low_3m, 2),
                "avg_price_3m": round(avg_price_3m, 2)
            },
            "trend": trend,
            "volatility_3m": f"{volatility_3m:.2f}%",
            "volume_trend": volume_trend,
            "moving_averages": {
                "ma_20": round(ma_20, 2),
                "ma_50": round(ma_50, 2)
            },
            "recommendation": recommendation,
            "recommendation_score": recommendation_score,
            "sector": info.get('sector', 'N/A'),
            "analyzed_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {"error": str(e)}


async def get_3month_recommendations(
    tickers: list,
    min_price: float = 1.0,
    max_price: float = 10.0,
    min_performance: float = 0.0
) -> list:
    """
    Get stocks with positive 3-month performance and recommendations
    
    Args:
        tickers: List of ticker symbols to analyze
        min_price: Minimum price filter
        max_price: Maximum price filter
        min_performance: Minimum 3-month performance (%)
        
    Returns:
        list: Filtered and sorted recommendations
    """
    recommendations = []
    
    for ticker in tickers:
        try:
            analysis = await analyze_3month_performance(ticker)
            
            if "error" not in analysis:
                # Apply filters
                if (min_price <= analysis['current_price'] <= max_price and
                    analysis['performance_3m']['change_percent'] >= min_performance):
                    recommendations.append(analysis)
        except Exception as e:
            continue
    
    # Sort by 3-month performance
    recommendations.sort(key=lambda x: x['performance_3m']['change_percent'], reverse=True)
    
    return recommendations
