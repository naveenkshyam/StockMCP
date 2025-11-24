"""
Feature: Stock Analysis with Recommendations
Provides detailed analysis and buying recommendations for stocks
Enhanced with news sentiment analysis for better trajectory predictions
"""
import yfinance as yf
import numpy as np
from datetime import datetime
from features.news_analyzer import NewsAnalyzer


async def analyze_stock_with_recommendation(ticker: str, include_news: bool = True, max_news: int = 5) -> dict:
    """
    Analyze a stock and provide detailed buying recommendation
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        dict: Complete analysis with recommendation
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="3mo")
        
        if hist.empty or not info:
            return {"error": f"Unable to fetch data for {ticker}"}
        
        current_price = info.get('currentPrice', hist['Close'].iloc[-1])
        previous_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
        day_change_pct = ((current_price - previous_close) / previous_close * 100) if previous_close else 0
        
        # Technical analysis
        ma_20 = hist['Close'].tail(20).mean() if len(hist) >= 20 else current_price
        ma_50 = hist['Close'].tail(50).mean() if len(hist) >= 50 else current_price
        recent_high = hist['High'].tail(20).max()
        recent_low = hist['Low'].tail(20).min()
        
        # Volume analysis
        avg_volume = hist['Volume'].mean()
        current_volume = info.get('volume', hist['Volume'].iloc[-1])
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Risk assessment
        volatility = hist['Close'].pct_change().std() * 100
        market_cap = info.get('marketCap', 0)
        
        risk_level = "Low"
        if volatility > 5 or market_cap < 100_000_000:
            risk_level = "High"
        elif volatility > 3 or market_cap < 1_000_000_000:
            risk_level = "Medium"
        
        # Entry points
        conservative_entry = round(ma_20 * 0.95, 2)
        moderate_entry = round(current_price * 0.97, 2)
        aggressive_entry = round(current_price * 1.02, 2)
        
        # Stop loss
        stop_loss_pct = 0.10 if risk_level == "High" else 0.07 if risk_level == "Medium" else 0.05
        stop_loss = round(current_price * (1 - stop_loss_pct), 2)
        
        # Recommendation
        recommendation = "Hold"
        if current_price < ma_20 * 0.95 and day_change_pct < 0:
            recommendation = "Strong Buy"
        elif current_price < ma_20:
            recommendation = "Buy"
        elif day_change_pct > 15:
            recommendation = "Wait for Pullback"
        elif current_price > ma_20 * 1.1:
            recommendation = "Overextended - Wait"
        
        # Analysis points
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
        
        # News analysis integration
        news_data = None
        final_recommendation = recommendation
        trajectory_data = None
        
        if include_news:
            try:
                news_analyzer = NewsAnalyzer()
                news_data = news_analyzer.analyze_stock_news(ticker, max_news)
                
                if news_data.get('news_available'):
                    # Adjust recommendation based on news
                    final_recommendation, news_reason = news_analyzer.get_trajectory_adjustment(
                        recommendation,
                        news_data['sentiment_score'],
                        sentiment_weight=0.3
                    )
                    
                    # Get trajectory prediction
                    trajectory_data = news_analyzer.get_buy_sell_trajectory(
                        ticker,
                        current_price,
                        news_data['sentiment_score']
                    )
                    
                    # Add news insight to analysis points
                    analysis_points.append(f"News: {news_data['summary']}")
                    if final_recommendation != recommendation:
                        analysis_points.append(f"Recommendation adjusted: {news_reason}")
            except Exception as e:
                # News analysis failed, use base recommendation
                pass
        
        result = {
            "ticker": ticker,
            "company": info.get('shortName', ticker),
            "current_price": current_price,
            "previous_close": previous_close,
            "day_change_percent": round(day_change_pct, 2),
            "recommendation": final_recommendation,
            "original_recommendation": recommendation,
            "risk_level": risk_level,
            "entry_points": {
                "conservative": f"${conservative_entry}",
                "moderate": f"${moderate_entry}",
                "aggressive": f"${aggressive_entry}"
            },
            "stop_loss": f"${stop_loss}",
            "key_levels": {
                "support": f"${recent_low:.2f}",
                "resistance": f"${recent_high:.2f}",
                "ma_20": f"${ma_20:.2f}",
                "ma_50": f"${ma_50:.2f}"
            },
            "analysis": analysis_points,
            "volatility": f"{volatility:.2f}%",
            "volume_ratio": f"{volume_ratio:.2f}x average",
            "sector": info.get('sector', 'N/A'),
            "market_cap": info.get('marketCap', 0)
        }
        
        # Add news and trajectory data if available
        if news_data:
            result['news'] = news_data
        if trajectory_data:
            result['trajectory'] = trajectory_data
        
        return result
    
    except Exception as e:
        return {"error": str(e)}


async def analyze_multiple_stocks(
    tickers: list,
    min_price: float = 1.0,
    max_price: float = 10.0,
    include_news: bool = True
) -> list:
    """
    Analyze multiple stocks and return recommendations
    
    Args:
        tickers: List of ticker symbols
        min_price: Minimum price filter
        max_price: Maximum price filter
        include_news: Whether to include news analysis
        
    Returns:
        list: List of analyzed stocks with recommendations
    """
    results = []
    
    for ticker in tickers:
        try:
            analysis = await analyze_stock_with_recommendation(ticker, include_news=include_news)
            
            if "error" not in analysis:
                # Filter by price range
                if min_price <= analysis['current_price'] <= max_price:
                    results.append(analysis)
        except Exception as e:
            continue
    
    return results


async def get_top_recommendations(
    tickers: list,
    min_price: float = 1.0,
    max_price: float = 10.0,
    top_n: int = 20,
    include_news: bool = True
) -> list:
    """
    Get top N stock recommendations based on scoring system
    
    Args:
        tickers: List of ticker symbols to analyze
        min_price: Minimum price filter
        max_price: Maximum price filter
        top_n: Number of top recommendations to return
        include_news: Whether to include news analysis
        
    Returns:
        list: Top N stocks sorted by recommendation score
    """
    print(f"\n🔍 Analyzing {len(tickers)} stocks between ${min_price} and ${max_price}...")
    
    # Analyze all stocks
    analyzed_stocks = await analyze_multiple_stocks(tickers, min_price, max_price, include_news)
    
    if not analyzed_stocks:
        return []
    
    print(f"✓ Found {len(analyzed_stocks)} stocks in price range")
    
    # Calculate score for each stock
    scored_stocks = []
    for stock in analyzed_stocks:
        score = calculate_stock_score(stock)
        scored_stocks.append({
            'stock_data': stock,
            'score': score
        })
    
    # Sort by score and return top N
    scored_stocks.sort(key=lambda x: x['score'], reverse=True)
    top_stocks = scored_stocks[:top_n]
    
    print(f"✓ Top {len(top_stocks)} recommendations selected")
    
    return top_stocks


def calculate_stock_score(stock_data: dict) -> int:
    """
    Calculate recommendation score based on multiple factors
    Score range: 0-50 points
    
    Args:
        stock_data: Stock analysis data
        
    Returns:
        int: Total score
    """
    score = 0
    
    # Factor 1: Recommendation quality (0-10 points)
    rec_scores = {
        'Strong Buy': 10,
        'Buy': 8,
        'Hold': 5,
        'Wait for Pullback': 3,
        'Wait': 2,
        'Overextended - Wait': 2,
        'Sell': 0
    }
    score += rec_scores.get(stock_data.get('recommendation', 'Hold'), 5)
    
    # Factor 2: Risk level - lower is better (0-10 points)
    risk_scores = {'Low': 10, 'Medium': 6, 'High': 3}
    score += risk_scores.get(stock_data.get('risk_level', 'Medium'), 6)
    
    # Factor 3: Day change momentum (0-5 points)
    day_change = stock_data.get('day_change_percent', 0)
    if day_change > 10:
        score += 5
    elif day_change > 5:
        score += 4
    elif day_change > 0:
        score += 3
    elif day_change > -5:
        score += 1
    
    # Factor 4: Volume ratio (0-5 points)
    volume_str = stock_data.get('volume_ratio', '1.0x average')
    try:
        volume_ratio = float(volume_str.replace('x average', ''))
        if volume_ratio > 2.0:
            score += 5
        elif volume_ratio > 1.5:
            score += 4
        elif volume_ratio > 1.0:
            score += 3
        else:
            score += 1
    except:
        score += 2
    
    # Factor 5: News sentiment (0-10 points) - if available
    if 'news' in stock_data and stock_data['news'].get('news_available'):
        sentiment_score = stock_data['news'].get('sentiment_score', 0)
        if sentiment_score > 0.4:
            score += 10
        elif sentiment_score > 0.2:
            score += 8
        elif sentiment_score > 0:
            score += 6
        elif sentiment_score > -0.2:
            score += 4
        else:
            score += 2
    else:
        score += 5  # Neutral if no news
    
    # Factor 6: Trajectory prediction (0-10 points) - if available
    if 'trajectory' in stock_data:
        trajectory = stock_data['trajectory'].get('trajectory', 'Sideways')
        trajectory_scores = {
            'Strong Upward': 10,
            'Moderate Upward': 8,
            'Sideways': 5,
            'Moderate Downward': 2,
            'Strong Downward': 0
        }
        score += trajectory_scores.get(trajectory, 5)
    else:
        score += 5  # Neutral if no trajectory
    
    return score


def format_top_recommendations_report(top_stocks: list, min_price: float, max_price: float) -> str:
    """
    Format top recommendations into a readable text report
    
    Args:
        top_stocks: List of top stock recommendations with scores
        min_price: Minimum price filter used
        max_price: Maximum price filter used
        
    Returns:
        str: Formatted report
    """
    report = f"""
{'='*80}
TOP {len(top_stocks)} STOCK BUYING RECOMMENDATIONS
Stocks Between ${min_price} and ${max_price} | {datetime.now().strftime('%B %d, %Y')}
{'='*80}

Total Stocks Analyzed: {len(top_stocks)}
Report Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}

"""
    
    for i, item in enumerate(top_stocks, 1):
        stock = item['stock_data']
        score = item['score']
        
        emoji = "🟢" if stock.get('day_change_percent', 0) >= 0 else "🔴"
        
        report += f"""
{'-'*80}
#{i} - {stock['ticker']} - {stock.get('company', 'N/A')}
{'-'*80}
Price: ${stock['current_price']:.2f} {emoji} {stock.get('day_change_percent', 0):+.2f}% (Today)
Score: {score}/50 | Sector: {stock.get('sector', 'N/A')}

RECOMMENDATION: {stock.get('recommendation', 'N/A')}
Risk Level: {stock.get('risk_level', 'N/A')}

Entry Points:
  • Conservative: {stock.get('entry_points', {}).get('conservative', 'N/A')}
  • Moderate: {stock.get('entry_points', {}).get('moderate', 'N/A')}
  • Aggressive: {stock.get('entry_points', {}).get('aggressive', 'N/A')}

Stop Loss: {stock.get('stop_loss', 'N/A')}

"""
        
        # Add trajectory if available
        if 'trajectory' in stock:
            traj = stock['trajectory']
            report += f"""Trajectory Analysis:
  • Direction: {traj.get('trajectory', 'N/A')}
  • Action: {traj.get('action', 'N/A')}
  • Confidence: {traj.get('confidence', 'N/A')}
  • 7-Day Target: ${traj.get('targets', {}).get('7_day', 'N/A')}
  • 30-Day Target: ${traj.get('targets', {}).get('30_day', 'N/A')}

"""
        
        # Add news sentiment if available
        if 'news' in stock and stock['news'].get('news_available'):
            news = stock['news']
            report += f"""News Sentiment:
  • Overall: {news.get('overall_sentiment', 'N/A')} (Score: {news.get('sentiment_score', 0):.2f})
  • Articles Analyzed: {news.get('articles_analyzed', 0)}
  • Summary: {news.get('summary', 'N/A')}

"""
            
            # Add top news headlines
            if news.get('news'):
                report += "  Recent Headlines:\n"
                for article in news['news'][:3]:
                    report += f"    • {article['title']} ({article['sentiment']})\n"
                report += "\n"
        
        # Add key levels
        report += f"""Key Levels:
  • Support: {stock.get('key_levels', {}).get('support', 'N/A')}
  • Resistance: {stock.get('key_levels', {}).get('resistance', 'N/A')}
  • 20-Day MA: {stock.get('key_levels', {}).get('ma_20', 'N/A')}
  • 50-Day MA: {stock.get('key_levels', {}).get('ma_50', 'N/A')}

Volatility: {stock.get('volatility', 'N/A')}
Volume: {stock.get('volume_ratio', 'N/A')}

"""
    
    report += f"""
{'='*80}
⚠️  IMPORTANT DISCLAIMER
{'='*80}
This analysis is for informational purposes only and should not be considered
as financial advice. Stock investments carry risks and past performance does
not guarantee future results. Always conduct your own research and consult
with a qualified financial advisor before making investment decisions.

Analysis includes news sentiment and trajectory predictions to enhance
buy/sell recommendations. News data is analyzed for sentiment using keyword
matching and may not reflect complete market conditions.

Generated by Enhanced Stock Analysis System with News Integration
Data Sources: Yahoo Finance (15-20 minute delay), yfinance news feeds
{'='*80}
"""
    
    return report
