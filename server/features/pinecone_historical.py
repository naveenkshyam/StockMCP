"""
Pinecone Historical Analysis Feature
Analyzes stocks saved in Pinecone: compares current performance with 3 months ago
Provides recommendations based on historical trends, news, and performance metrics
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import numpy as np
from features.pinecone_saver import PineconeStockSaver
from features.news_analyzer import NewsAnalyzer


class PineconeHistoricalAnalyzer:
    """Analyze historical performance of stocks saved in Pinecone"""
    
    def __init__(self):
        self.pinecone_saver = PineconeStockSaver()
        self.pinecone_saver.initialize_index()
        self.news_analyzer = NewsAnalyzer()
    
    async def get_3month_comparison(self, ticker: str, current_date: str = None) -> Dict[str, Any]:
        """
        Compare stock's current state with 3 months ago from Pinecone
        
        Args:
            ticker: Stock ticker symbol
            current_date: Current date (YYYY-MM-DD), defaults to today
            
        Returns:
            Dict with comparison data
        """
        if not current_date:
            current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Calculate 3 months ago date
        three_months_ago = (datetime.strptime(current_date, '%Y-%m-%d') - timedelta(days=90)).strftime('%Y-%m-%d')
        
        # Get recommendations from Pinecone
        current_recs = self.pinecone_saver.query_similar_recommendations(ticker, top_k=1, date_filter=current_date)
        old_recs = self.pinecone_saver.query_similar_recommendations(ticker, top_k=1, date_filter=three_months_ago)
        
        # Get current live data
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="3mo")
            
            current_price = info.get('currentPrice', hist['Close'].iloc[-1] if not hist.empty else 0)
            
            # If no Pinecone data, use live historical data
            if not old_recs and not hist.empty:
                three_month_old_price = hist['Close'].iloc[0]
            else:
                three_month_old_price = old_recs[0].get('current_price', 0) if old_recs else 0
            
        except Exception as e:
            return {"error": f"Failed to fetch data for {ticker}: {str(e)}"}
        
        # Calculate performance metrics
        if three_month_old_price > 0:
            price_change = current_price - three_month_old_price
            price_change_pct = (price_change / three_month_old_price) * 100
        else:
            price_change = 0
            price_change_pct = 0
        
        # Analyze the comparison
        comparison = {
            'ticker': ticker,
            'company': info.get('shortName', ticker),
            'current_date': current_date,
            'comparison_date': three_months_ago,
            'current_data': {
                'price': round(current_price, 2),
                'recommendation': current_recs[0].get('recommendation', 'Unknown') if current_recs else 'No data',
                'risk_level': current_recs[0].get('risk_level', 'Unknown') if current_recs else 'Unknown',
                'day_change_percent': current_recs[0].get('day_change_percent', 0) if current_recs else 0,
                'data_source': 'Pinecone' if current_recs else 'Live'
            },
            'three_months_ago': {
                'price': round(three_month_old_price, 2),
                'recommendation': old_recs[0].get('recommendation', 'Unknown') if old_recs else 'No data',
                'risk_level': old_recs[0].get('risk_level', 'Unknown') if old_recs else 'Unknown',
                'data_source': 'Pinecone' if old_recs else 'Historical'
            },
            'performance': {
                'price_change': round(price_change, 2),
                'price_change_percent': round(price_change_pct, 2),
                'performance_rating': self._rate_performance(price_change_pct)
            }
        }
        
        return comparison
    
    def _rate_performance(self, change_pct: float) -> str:
        """Rate stock performance based on percentage change"""
        if change_pct >= 30:
            return "Excellent (30%+)"
        elif change_pct >= 20:
            return "Very Good (20-30%)"
        elif change_pct >= 10:
            return "Good (10-20%)"
        elif change_pct >= 5:
            return "Moderate (5-10%)"
        elif change_pct >= 0:
            return "Slight Gain (0-5%)"
        elif change_pct >= -5:
            return "Slight Loss (0-5%)"
        elif change_pct >= -10:
            return "Moderate Loss (5-10%)"
        elif change_pct >= -20:
            return "Poor (-10 to -20%)"
        else:
            return "Very Poor (-20%+)"
    
    async def analyze_with_news_and_recommendation(
        self,
        ticker: str,
        current_date: str = None
    ) -> Dict[str, Any]:
        """
        Full analysis: 3-month comparison + news sentiment + recommendation
        
        Args:
            ticker: Stock ticker symbol
            current_date: Current date (YYYY-MM-DD), defaults to today
            
        Returns:
            Complete analysis with recommendations
        """
        # Get 3-month comparison
        comparison = await self.get_3month_comparison(ticker, current_date)
        
        if "error" in comparison:
            return comparison
        
        # Fetch news sentiment
        news_analysis = self.news_analyzer.analyze_stock_news(ticker, max_articles=5)
        
        # Get current stock data for trajectory
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            hist = stock.history(period="3mo")
            
            current_price = comparison['current_data']['price']
            
            # Calculate trend
            if not hist.empty:
                closes = hist['Close'].values
                x = np.arange(len(closes))
                slope, _ = np.polyfit(x, closes, 1)
                
                if slope > current_price * 0.001:
                    trend = "Uptrend"
                elif slope < -current_price * 0.001:
                    trend = "Downtrend"
                else:
                    trend = "Sideways"
                
                # Calculate volatility
                returns = hist['Close'].pct_change()
                volatility = returns.std() * np.sqrt(63) * 100  # Annualized
            else:
                trend = "Unknown"
                volatility = 0
            
            # Moving averages
            ma_20 = hist['Close'].tail(20).mean() if len(hist) >= 20 else current_price
            ma_50 = hist['Close'].tail(50).mean() if len(hist) >= 50 else current_price
            
        except Exception as e:
            trend = "Unknown"
            volatility = 0
            ma_20 = current_price
            ma_50 = current_price
        
        # Generate recommendation based on all factors
        recommendation_result = self._generate_comprehensive_recommendation(
            comparison,
            news_analysis,
            trend,
            volatility,
            ma_20,
            ma_50,
            current_price
        )
        
        # Combine all data
        full_analysis = {
            **comparison,
            'news_analysis': news_analysis,
            'technical_analysis': {
                'trend': trend,
                'volatility': f"{volatility:.2f}%",
                'ma_20': round(ma_20, 2),
                'ma_50': round(ma_50, 2),
                'price_vs_ma20': f"{((current_price - ma_20) / ma_20 * 100):+.2f}%",
                'price_vs_ma50': f"{((current_price - ma_50) / ma_50 * 100):+.2f}%"
            },
            'recommendation': recommendation_result,
            'analyzed_at': datetime.now().isoformat()
        }
        
        return full_analysis
    
    def _generate_comprehensive_recommendation(
        self,
        comparison: Dict,
        news: Dict,
        trend: str,
        volatility: float,
        ma_20: float,
        ma_50: float,
        current_price: float
    ) -> Dict[str, Any]:
        """
        Generate comprehensive recommendation based on all factors
        
        Considers:
        - 3-month performance
        - Current trend
        - News sentiment
        - Technical indicators
        """
        # Scoring system (0-100)
        score = 50  # Start neutral
        factors = []
        
        # Factor 1: 3-Month Performance (weight: 30 points)
        perf_pct = comparison['performance']['price_change_percent']
        if perf_pct >= 20:
            score += 15
            factors.append(f"✓ Excellent 3-month gain: {perf_pct:+.1f}%")
        elif perf_pct >= 10:
            score += 10
            factors.append(f"✓ Strong 3-month gain: {perf_pct:+.1f}%")
        elif perf_pct >= 5:
            score += 5
            factors.append(f"✓ Moderate 3-month gain: {perf_pct:+.1f}%")
        elif perf_pct >= 0:
            factors.append(f"○ Slight 3-month gain: {perf_pct:+.1f}%")
        elif perf_pct >= -5:
            score -= 5
            factors.append(f"✗ Slight 3-month loss: {perf_pct:+.1f}%")
        elif perf_pct >= -10:
            score -= 10
            factors.append(f"✗ Moderate 3-month loss: {perf_pct:+.1f}%")
        else:
            score -= 15
            factors.append(f"✗ Significant 3-month loss: {perf_pct:+.1f}%")
        
        # Factor 2: Trend (weight: 20 points)
        if trend == "Uptrend":
            score += 10
            factors.append("✓ Stock in uptrend")
        elif trend == "Downtrend":
            score -= 10
            factors.append("✗ Stock in downtrend")
        else:
            factors.append("○ Stock consolidating sideways")
        
        # Factor 3: News Sentiment (weight: 20 points)
        if news.get('news_available'):
            sentiment_score = news.get('sentiment_score', 0)
            if sentiment_score > 0.3:
                score += 10
                factors.append(f"✓ Positive news sentiment ({sentiment_score:.2f})")
            elif sentiment_score < -0.3:
                score -= 10
                factors.append(f"✗ Negative news sentiment ({sentiment_score:.2f})")
            else:
                factors.append(f"○ Neutral news sentiment ({sentiment_score:.2f})")
        else:
            factors.append("○ No recent news available")
        
        # Factor 4: Technical Position (weight: 15 points)
        if current_price > ma_50:
            score += 8
            factors.append("✓ Trading above 50-day MA")
        else:
            score -= 5
            factors.append("✗ Trading below 50-day MA")
        
        if current_price > ma_20:
            score += 5
            factors.append("✓ Trading above 20-day MA")
        else:
            factors.append("✗ Trading below 20-day MA")
        
        # Factor 5: Volatility (weight: 10 points)
        if volatility < 30:
            score += 5
            factors.append(f"✓ Low volatility ({volatility:.1f}%)")
        elif volatility > 50:
            score -= 5
            factors.append(f"✗ High volatility ({volatility:.1f}%)")
        else:
            factors.append(f"○ Moderate volatility ({volatility:.1f}%)")
        
        # Factor 6: Recommendation Change (weight: 5 points)
        old_rec = comparison['three_months_ago']['recommendation']
        current_rec = comparison['current_data']['recommendation']
        if old_rec != 'No data' and current_rec != 'No data':
            if 'Buy' in current_rec and 'Buy' not in old_rec:
                score += 5
                factors.append("✓ Recommendation upgraded to Buy")
            elif 'Buy' not in current_rec and 'Buy' in old_rec:
                score -= 5
                factors.append("✗ Recommendation downgraded from Buy")
        
        # Generate final recommendation
        if score >= 75:
            recommendation = "Strong Buy"
            action = "Excellent opportunity - consider increasing position"
            confidence = "High"
        elif score >= 60:
            recommendation = "Buy"
            action = "Good entry point for long-term holders"
            confidence = "Medium-High"
        elif score >= 45:
            recommendation = "Hold/Accumulate"
            action = "Maintain position, consider adding on dips"
            confidence = "Medium"
        elif score >= 30:
            recommendation = "Hold"
            action = "Wait for clearer signals before action"
            confidence = "Medium"
        elif score >= 20:
            recommendation = "Caution"
            action = "Consider trimming position or tightening stop-loss"
            confidence = "Medium"
        else:
            recommendation = "Avoid/Sell"
            action = "Exit position or avoid entering"
            confidence = "Medium-High"
        
        # Generate detailed reasoning
        reasoning = self._generate_reasoning(
            recommendation,
            comparison,
            news,
            trend,
            perf_pct
        )
        
        return {
            'recommendation': recommendation,
            'action': action,
            'confidence': confidence,
            'score': score,
            'max_score': 100,
            'factors': factors,
            'reasoning': reasoning
        }
    
    def _generate_reasoning(
        self,
        recommendation: str,
        comparison: Dict,
        news: Dict,
        trend: str,
        perf_pct: float
    ) -> str:
        """Generate human-readable reasoning for recommendation"""
        ticker = comparison['ticker']
        current_price = comparison['current_data']['price']
        
        reasoning_parts = []
        
        # Opening statement
        reasoning_parts.append(
            f"{recommendation} recommendation for {ticker} at ${current_price:.2f}."
        )
        
        # Performance analysis
        if perf_pct > 20:
            reasoning_parts.append(
                f"Stock has gained {perf_pct:.1f}% over 3 months, showing strong momentum."
            )
        elif perf_pct > 10:
            reasoning_parts.append(
                f"Stock up {perf_pct:.1f}% in 3 months with positive momentum."
            )
        elif perf_pct > 0:
            reasoning_parts.append(
                f"Stock gained {perf_pct:.1f}% in 3 months, showing modest progress."
            )
        else:
            reasoning_parts.append(
                f"Stock declined {abs(perf_pct):.1f}% over 3 months, requiring caution."
            )
        
        # Trend analysis
        if trend == "Uptrend":
            reasoning_parts.append("Technical trend is bullish with higher highs.")
        elif trend == "Downtrend":
            reasoning_parts.append("Technical trend is bearish with lower lows.")
        else:
            reasoning_parts.append("Stock is consolidating without clear direction.")
        
        # News impact
        if news.get('news_available'):
            sentiment = news.get('overall_sentiment', 'Neutral')
            if sentiment == "Positive":
                reasoning_parts.append("Recent news is positive, supporting upward potential.")
            elif sentiment == "Negative":
                reasoning_parts.append("Recent news is negative, adding downside risk.")
            else:
                reasoning_parts.append("News sentiment is neutral.")
        
        # Action advice
        if recommendation in ["Strong Buy", "Buy"]:
            reasoning_parts.append(
                "Consider this as a buying opportunity with favorable risk-reward."
            )
        elif recommendation == "Hold/Accumulate":
            reasoning_parts.append(
                "Current position holders should maintain, with potential to add on weakness."
            )
        elif recommendation == "Hold":
            reasoning_parts.append(
                "Wait for more decisive signals before making changes."
            )
        else:
            reasoning_parts.append(
                "Risk outweighs reward at current levels - exercise caution."
            )
        
        return " ".join(reasoning_parts)
    
    async def analyze_all_pinecone_stocks(
        self,
        date: str = None,
        min_score: int = 50,
        sort_by: str = "performance"
    ) -> List[Dict[str, Any]]:
        """
        Analyze all stocks saved in Pinecone for a given date
        
        Args:
            date: Date to analyze (YYYY-MM-DD), defaults to today
            min_score: Minimum recommendation score to include
            sort_by: Sort results by 'performance', 'score', or 'news'
            
        Returns:
            List of analyzed stocks with recommendations
        """
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # Get all recommendations for the date
        recommendations = self.pinecone_saver.get_recommendations_by_date(date)
        
        if not recommendations:
            print(f"No recommendations found for {date}")
            return []
        
        print(f"Found {len(recommendations)} stocks in Pinecone for {date}")
        print("Analyzing historical performance...\n")
        
        analyzed_stocks = []
        
        for i, rec in enumerate(recommendations, 1):
            ticker = rec.get('ticker')
            print(f"{i}/{len(recommendations)}: Analyzing {ticker}...")
            
            try:
                analysis = await self.analyze_with_news_and_recommendation(ticker, date)
                
                # Filter by minimum score
                if analysis['recommendation']['score'] >= min_score:
                    analyzed_stocks.append(analysis)
            
            except Exception as e:
                print(f"  ✗ Error analyzing {ticker}: {str(e)}")
                continue
        
        # Sort results
        if sort_by == "performance":
            analyzed_stocks.sort(
                key=lambda x: x['performance']['price_change_percent'],
                reverse=True
            )
        elif sort_by == "score":
            analyzed_stocks.sort(
                key=lambda x: x['recommendation']['score'],
                reverse=True
            )
        elif sort_by == "news":
            analyzed_stocks.sort(
                key=lambda x: x['news_analysis'].get('sentiment_score', 0),
                reverse=True
            )
        
        return analyzed_stocks


async def analyze_pinecone_historical(
    ticker: str = None,
    date: str = None,
    analyze_all: bool = False,
    min_score: int = 50,
    sort_by: str = "performance"
) -> Dict[str, Any]:
    """
    Convenience function to analyze historical performance
    
    Args:
        ticker: Single ticker to analyze (optional)
        date: Date to analyze (YYYY-MM-DD), defaults to today
        analyze_all: If True, analyze all stocks in Pinecone for the date
        min_score: Minimum recommendation score (for analyze_all)
        sort_by: Sort method (for analyze_all)
        
    Returns:
        Analysis results
    """
    analyzer = PineconeHistoricalAnalyzer()
    
    if analyze_all:
        return await analyzer.analyze_all_pinecone_stocks(date, min_score, sort_by)
    elif ticker:
        return await analyzer.analyze_with_news_and_recommendation(ticker, date)
    else:
        return {"error": "Provide either ticker or set analyze_all=True"}


def format_historical_report(analyses: List[Dict[str, Any]]) -> str:
    """Format historical analysis results as a readable report"""
    if not analyses:
        return "No analysis results to display."
    
    report = []
    report.append("="*80)
    report.append("PINECONE HISTORICAL ANALYSIS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"Total Stocks Analyzed: {len(analyses)}")
    report.append("="*80)
    report.append("")
    
    for i, analysis in enumerate(analyses, 1):
        report.append(f"{i}. {analysis['ticker']} - {analysis['company']}")
        report.append(f"   {'='*70}")
        
        # Current vs 3 months ago
        current = analysis['current_data']
        old = analysis['three_months_ago']
        perf = analysis['performance']
        
        report.append(f"   Current Price: ${current['price']:.2f} (Rec: {current['recommendation']})")
        report.append(f"   3 Months Ago:  ${old['price']:.2f} (Rec: {old['recommendation']})")
        report.append(f"   Performance:   {perf['price_change']:+.2f} ({perf['price_change_percent']:+.2f}%) - {perf['performance_rating']}")
        
        # Technical analysis
        tech = analysis['technical_analysis']
        report.append(f"   Trend: {tech['trend']} | Volatility: {tech['volatility']}")
        report.append(f"   vs MA20: {tech['price_vs_ma20']} | vs MA50: {tech['price_vs_ma50']}")
        
        # News
        news = analysis['news_analysis']
        if news.get('news_available'):
            report.append(f"   News: {news['overall_sentiment']} (Score: {news['sentiment_score']:.2f})")
        else:
            report.append(f"   News: No recent news")
        
        # Recommendation
        rec = analysis['recommendation']
        report.append(f"   \n   RECOMMENDATION: {rec['recommendation']} (Score: {rec['score']}/100)")
        report.append(f"   Action: {rec['action']}")
        report.append(f"   Confidence: {rec['confidence']}")
        
        # Key factors
        report.append(f"   \n   Key Factors:")
        for factor in rec['factors'][:5]:  # Top 5 factors
            report.append(f"     • {factor}")
        
        report.append("")
    
    return "\n".join(report)
