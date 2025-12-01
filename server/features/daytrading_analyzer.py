"""
Day Trading Analyzer - Identifies best stocks for day trading
Analyzes volatility, volume, news sentiment, and price momentum
Focuses on liquid stocks with high trading potential
"""
import yfinance as yf
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
from features.news_analyzer import NewsAnalyzer


async def analyze_daytrading_stock(ticker: str) -> Dict:
    """
    Analyze a stock for day trading potential
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        dict: Day trading analysis with scores and recommendations
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # Get recent historical data (30 days for pattern analysis)
        hist = stock.history(period="30d")
        
        if hist.empty or not info:
            return None
        
        current_price = info.get('currentPrice', hist['Close'].iloc[-1])
        
        # Skip if price > $20
        if current_price > 20:
            return None
        
        # Market cap check - prefer liquid stocks
        market_cap = info.get('marketCap', 0)
        if market_cap < 100_000_000:  # Less than $100M - too risky
            return None
        
        # Calculate key day trading metrics
        
        # 1. Volatility (critical for day trading)
        daily_returns = hist['Close'].pct_change()
        volatility = daily_returns.std() * 100
        avg_daily_range = ((hist['High'] - hist['Low']) / hist['Low'] * 100).mean()
        
        # 2. Volume analysis (liquidity is key)
        avg_volume = hist['Volume'].mean()
        recent_volume = hist['Volume'].tail(5).mean()
        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
        
        # Volume must be significant for day trading
        if avg_volume < 500_000:  # Less than 500k shares/day
            return None
        
        # 3. Price momentum (intraday opportunities)
        ma_5 = hist['Close'].tail(5).mean()
        ma_10 = hist['Close'].tail(10).mean()
        ma_20 = hist['Close'].tail(20).mean()
        
        momentum_score = 0
        if ma_5 > ma_10:
            momentum_score += 1
        if ma_10 > ma_20:
            momentum_score += 1
        if current_price > ma_5:
            momentum_score += 1
        
        # 4. Recent price action (last 5 days)
        recent_change = ((current_price - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5] * 100) if len(hist) >= 5 else 0
        
        # 5. Intraday volatility pattern
        intraday_ranges = []
        for i in range(min(10, len(hist))):
            idx = -(i+1)
            day_range = ((hist['High'].iloc[idx] - hist['Low'].iloc[idx]) / hist['Low'].iloc[idx] * 100)
            intraday_ranges.append(day_range)
        
        avg_intraday_range = np.mean(intraday_ranges) if intraday_ranges else 0
        
        # 6. Gap analysis (gaps create trading opportunities)
        gaps = []
        for i in range(1, min(10, len(hist))):
            prev_close = hist['Close'].iloc[-(i+1)]
            curr_open = hist['Open'].iloc[-i]
            gap = ((curr_open - prev_close) / prev_close * 100)
            gaps.append(abs(gap))
        
        avg_gap = np.mean(gaps) if gaps else 0
        
        # 7. News sentiment analysis
        news_analyzer = NewsAnalyzer()
        news_data = news_analyzer.analyze_stock_news(ticker, max_articles=10)
        
        news_score = 0
        news_summary = "No recent news"
        
        if news_data.get('news_available'):
            sentiment_score = news_data['sentiment_score']
            news_summary = news_data['overall_sentiment']
            
            # Strong news creates volatility and trading opportunities
            if abs(sentiment_score) > 0.5:
                news_score = 10  # Strong sentiment
            elif abs(sentiment_score) > 0.3:
                news_score = 7   # Moderate sentiment
            elif abs(sentiment_score) > 0.1:
                news_score = 4   # Weak sentiment
            else:
                news_score = 2   # Neutral
        
        # 8. Technical price trajectory
        closes = hist['Close'].values
        x = np.arange(len(closes))
        slope, _ = np.polyfit(x, closes, 1)
        
        # Trend determination
        if slope > closes[-1] * 0.002:
            trend = "Strong Uptrend"
            trend_score = 10
        elif slope > closes[-1] * 0.001:
            trend = "Uptrend"
            trend_score = 8
        elif slope < -closes[-1] * 0.002:
            trend = "Strong Downtrend"
            trend_score = 6  # Can still trade downtrends
        elif slope < -closes[-1] * 0.001:
            trend = "Downtrend"
            trend_score = 5
        else:
            trend = "Sideways"
            trend_score = 7  # Sideways can be good for range trading
        
        # Calculate day trading score (0-100)
        score = 0
        
        # Volatility score (0-30 points) - Higher volatility = more opportunities
        if avg_intraday_range > 5:
            score += 30
        elif avg_intraday_range > 3:
            score += 25
        elif avg_intraday_range > 2:
            score += 20
        elif avg_intraday_range > 1:
            score += 15
        else:
            score += 10
        
        # Volume score (0-20 points)
        if volume_ratio > 2:
            score += 20
        elif volume_ratio > 1.5:
            score += 17
        elif volume_ratio > 1.2:
            score += 14
        elif volume_ratio > 1:
            score += 12
        else:
            score += 8
        
        # Momentum score (0-15 points)
        score += momentum_score * 5
        
        # News score (0-10 points)
        score += news_score
        
        # Trend score (0-10 points)
        score += trend_score
        
        # Gap score (0-10 points) - Gaps create opportunities
        if avg_gap > 2:
            score += 10
        elif avg_gap > 1:
            score += 7
        elif avg_gap > 0.5:
            score += 5
        else:
            score += 3
        
        # Liquidity bonus (0-5 points)
        if avg_volume > 5_000_000:
            score += 5
        elif avg_volume > 2_000_000:
            score += 4
        elif avg_volume > 1_000_000:
            score += 3
        else:
            score += 2
        
        # Determine day trading recommendation
        if score >= 85:
            recommendation = "Excellent Day Trade"
            action = "Strong Buy for Day Trading"
        elif score >= 75:
            recommendation = "Very Good Day Trade"
            action = "Buy for Day Trading"
        elif score >= 65:
            recommendation = "Good Day Trade"
            action = "Consider for Day Trading"
        elif score >= 55:
            recommendation = "Moderate Day Trade"
            action = "Watch for Entry"
        else:
            recommendation = "Poor Day Trade"
            action = "Skip"
        
        # Calculate profit targets for day trading
        target_low = current_price * 1.02   # 2% gain
        target_medium = current_price * 1.03  # 3% gain
        target_high = current_price * 1.05   # 5% gain
        stop_loss = current_price * 0.98    # 2% loss
        
        return {
            'ticker': ticker,
            'company': info.get('shortName', ticker),
            'current_price': round(current_price, 2),
            'market_cap': market_cap,
            'score': score,
            'recommendation': recommendation,
            'action': action,
            'metrics': {
                'volatility': round(volatility, 2),
                'avg_intraday_range': round(avg_intraday_range, 2),
                'volume_ratio': round(volume_ratio, 2),
                'avg_volume': int(avg_volume),
                'momentum_score': momentum_score,
                'recent_change_5d': round(recent_change, 2),
                'avg_gap': round(avg_gap, 2)
            },
            'news': {
                'sentiment': news_summary,
                'impact': 'High' if news_score >= 7 else 'Medium' if news_score >= 4 else 'Low',
                'articles_count': len(news_data.get('news', []))
            },
            'trend': trend,
            'targets': {
                'low': round(target_low, 2),
                'medium': round(target_medium, 2),
                'high': round(target_high, 2),
                'stop_loss': round(stop_loss, 2)
            },
            'key_levels': {
                'support': round(hist['Low'].tail(10).min(), 2),
                'resistance': round(hist['High'].tail(10).max(), 2),
                'ma_5': round(ma_5, 2),
                'ma_10': round(ma_10, 2)
            }
        }
        
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None


async def get_daytrading_recommendations(
    tickers: List[str],
    max_price: float = 20.0,
    min_score: int = 55,
    top_n: int = 10
) -> List[Dict]:
    """
    Get top day trading recommendations from a list of tickers
    
    Args:
        tickers: List of ticker symbols to analyze
        max_price: Maximum stock price (default: $20)
        min_score: Minimum day trading score (default: 55)
        top_n: Number of top stocks to return (default: 10)
        
    Returns:
        List of top day trading stocks with analysis
    """
    recommendations = []
    
    print(f"Analyzing {len(tickers)} stocks for day trading opportunities...")
    
    for ticker in tickers:
        try:
            analysis = await analyze_daytrading_stock(ticker)
            
            if analysis and analysis['score'] >= min_score:
                recommendations.append(analysis)
                
        except Exception as e:
            continue
    
    # Sort by score
    recommendations.sort(key=lambda x: x['score'], reverse=True)
    
    return recommendations[:top_n]


def format_daytrading_report(recommendations: List[Dict]) -> str:
    """
    Format day trading recommendations into a readable report
    
    Args:
        recommendations: List of day trading recommendations
        
    Returns:
        Formatted text report
    """
    report = []
    report.append("="*80)
    report.append("DAY TRADING RECOMMENDATIONS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("="*80)
    report.append("")
    report.append(f"Found {len(recommendations)} day trading opportunities")
    report.append("")
    
    for i, stock in enumerate(recommendations, 1):
        report.append(f"{i}. {stock['ticker']} - {stock['company']}")
        report.append(f"   Price: ${stock['current_price']:.2f}")
        report.append(f"   Day Trading Score: {stock['score']}/100")
        report.append(f"   Recommendation: {stock['recommendation']}")
        report.append(f"   Action: {stock['action']}")
        report.append("")
        
        metrics = stock['metrics']
        report.append(f"   Trading Metrics:")
        report.append(f"      • Avg Intraday Range: {metrics['avg_intraday_range']:.2f}%")
        report.append(f"      • Volume Ratio: {metrics['volume_ratio']:.2f}x average")
        report.append(f"      • Avg Volume: {metrics['avg_volume']:,} shares")
        report.append(f"      • 5-Day Change: {metrics['recent_change_5d']:+.2f}%")
        report.append(f"      • Avg Gap: {metrics['avg_gap']:.2f}%")
        report.append("")
        
        report.append(f"   News Impact: {stock['news']['impact']} ({stock['news']['sentiment']})")
        report.append(f"   Trend: {stock['trend']}")
        report.append("")
        
        targets = stock['targets']
        report.append(f"   Day Trading Targets:")
        report.append(f"      • Entry: ${stock['current_price']:.2f}")
        report.append(f"      • Target Low (2%): ${targets['low']:.2f}")
        report.append(f"      • Target Medium (3%): ${targets['medium']:.2f}")
        report.append(f"      • Target High (5%): ${targets['high']:.2f}")
        report.append(f"      • Stop Loss: ${targets['stop_loss']:.2f}")
        report.append("")
        
        levels = stock['key_levels']
        report.append(f"   Key Levels:")
        report.append(f"      • Support: ${levels['support']:.2f}")
        report.append(f"      • Resistance: ${levels['resistance']:.2f}")
        report.append(f"      • 5-day MA: ${levels['ma_5']:.2f}")
        report.append("")
        report.append("-"*80)
        report.append("")
    
    return "\n".join(report)


# Day trading focused watchlist (liquid, volatile stocks under $20)
DAYTRADING_WATCHLIST = [
    # Tech & Growth
    'PLTR', 'SOFI', 'NIO', 'LCID', 'RIVN', 'GRAB', 'NU',
    
    # Financial
    'BAC', 'WFC', 'C', 'ALLY', 'SCHW',
    
    # Energy & Commodities  
    'F', 'PLUG', 'FCEL', 'VALE', 'ABEV', 'X', 'CLF',
    
    # Cannabis
    'TLRY', 'CGC', 'SNDL', 'ACB', 'CRON', 'OGI',
    
    # Entertainment & Media
    'SNAP', 'PINS', 'PARA', 'DKNG',
    
    # Airlines & Travel
    'AAL', 'UAL', 'CCL', 'NCLH', 'RCL',
    
    # Retail
    'BBY', 'BBBY', 'EXPR', 'KOSS',
    
    # Telecom
    'NOK', 'T', 'VZ',
    
    # Biotech (volatile)
    'OCGN', 'SENS', 'INO', 'BNGO',
    
    # EV & Clean Energy
    'BLNK', 'CHPT', 'EVGO', 'WKHS', 'GOEV',
    
    # Meme Stocks (high volatility)
    'AMC', 'GME', 'BB',
    
    # Crypto-related
    'MARA', 'RIOT', 'COIN',
    
    # Real Estate
    'AGNC', 'NLY', 'ARR',
    
    # Other high-volume stocks
    'INTC', 'AMD', 'PYPL', 'UBER', 'LYFT', 'ZM',
    'SQ', 'HOOD', 'UPST', 'AFRM'
]
