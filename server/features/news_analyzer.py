"""
News Analyzer - Fetches and analyzes news for stock recommendations
Uses news sentiment to enhance buy/sell trajectory predictions
"""
import yfinance as yf
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import re


class NewsAnalyzer:
    """Analyzes news sentiment for stock recommendations"""
    
    def __init__(self, positive_keywords: List[str] = None, negative_keywords: List[str] = None):
        self.positive_keywords = positive_keywords or [
            "earnings beat", "revenue growth", "partnership", "acquisition",
            "innovation", "breakthrough", "expansion", "profit", "upgrade", "bullish",
            "strong results", "exceed expectations", "record high", "growth",
            "success", "win", "approval", "deal", "buy rating", "outperform"
        ]
        
        self.negative_keywords = negative_keywords or [
            "lawsuit", "loss", "decline", "warning", "investigation",
            "downgrade", "bearish", "debt", "scandal", "layoffs",
            "miss", "disappointing", "concern", "risk", "fall", "drop",
            "sell rating", "underperform", "trouble", "issue"
        ]
    
    def fetch_news(self, ticker: str, max_articles: int = 5) -> List[Dict]:
        """
        Fetch recent news for a stock
        
        Args:
            ticker: Stock ticker symbol
            max_articles: Maximum number of articles to fetch
            
        Returns:
            List of news articles with title, publisher, link
        """
        try:
            stock = yf.Ticker(ticker)
            news = stock.news if hasattr(stock, 'news') else []
            
            # Limit to max_articles
            news = news[:max_articles] if news else []
            
            # Format news articles
            formatted_news = []
            for article in news:
                formatted_news.append({
                    'title': article.get('title', ''),
                    'publisher': article.get('publisher', ''),
                    'link': article.get('link', ''),
                    'published': datetime.fromtimestamp(article.get('providerPublishTime', 0)),
                    'type': article.get('type', 'news')
                })
            
            return formatted_news
            
        except Exception as e:
            print(f"Error fetching news for {ticker}: {e}")
            return []
    
    def analyze_sentiment(self, text: str) -> Dict:
        """
        Analyze sentiment of text based on keywords
        
        Args:
            text: Text to analyze (news title, summary)
            
        Returns:
            Dict with sentiment score and breakdown
        """
        text_lower = text.lower()
        
        positive_count = sum(1 for keyword in self.positive_keywords if keyword in text_lower)
        negative_count = sum(1 for keyword in self.negative_keywords if keyword in text_lower)
        
        # Calculate sentiment score (-1 to +1)
        total_keywords = positive_count + negative_count
        if total_keywords == 0:
            sentiment_score = 0  # Neutral
        else:
            sentiment_score = (positive_count - negative_count) / total_keywords
        
        # Classify sentiment
        if sentiment_score > 0.3:
            sentiment = "Positive"
        elif sentiment_score < -0.3:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"
        
        return {
            'score': sentiment_score,
            'sentiment': sentiment,
            'positive_signals': positive_count,
            'negative_signals': negative_count
        }
    
    def analyze_stock_news(self, ticker: str, max_articles: int = 5) -> Dict:
        """
        Fetch and analyze news for a stock
        
        Args:
            ticker: Stock ticker symbol
            max_articles: Maximum number of articles to analyze
            
        Returns:
            Dict with overall sentiment and news details
        """
        news_articles = self.fetch_news(ticker, max_articles)
        
        if not news_articles:
            return {
                'ticker': ticker,
                'news_available': False,
                'overall_sentiment': 'Neutral',
                'sentiment_score': 0,
                'articles_analyzed': 0,
                'news': []
            }
        
        # Analyze each article
        article_sentiments = []
        analyzed_articles = []
        
        for article in news_articles:
            sentiment = self.analyze_sentiment(article['title'])
            article_sentiments.append(sentiment['score'])
            
            analyzed_articles.append({
                'title': article['title'],
                'publisher': article['publisher'],
                'published': article['published'].strftime('%Y-%m-%d %H:%M'),
                'sentiment': sentiment['sentiment'],
                'sentiment_score': round(sentiment['score'], 2)
            })
        
        # Calculate overall sentiment
        avg_sentiment = sum(article_sentiments) / len(article_sentiments) if article_sentiments else 0
        
        if avg_sentiment > 0.2:
            overall_sentiment = "Positive"
        elif avg_sentiment < -0.2:
            overall_sentiment = "Negative"
        else:
            overall_sentiment = "Neutral"
        
        return {
            'ticker': ticker,
            'news_available': True,
            'overall_sentiment': overall_sentiment,
            'sentiment_score': round(avg_sentiment, 2),
            'articles_analyzed': len(analyzed_articles),
            'news': analyzed_articles,
            'summary': self._generate_news_summary(overall_sentiment, avg_sentiment, len(analyzed_articles))
        }
    
    def _generate_news_summary(self, sentiment: str, score: float, count: int) -> str:
        """Generate human-readable news summary"""
        if sentiment == "Positive":
            return f"Recent news is {sentiment.lower()} ({count} articles analyzed). Good momentum with positive developments."
        elif sentiment == "Negative":
            return f"Recent news is {sentiment.lower()} ({count} articles analyzed). Caution advised due to negative headlines."
        else:
            return f"Recent news is {sentiment.lower()} ({count} articles analyzed). No significant sentiment detected."
    
    def get_trajectory_adjustment(
        self,
        base_recommendation: str,
        sentiment_score: float,
        sentiment_weight: float = 0.3
    ) -> Tuple[str, str]:
        """
        Adjust recommendation based on news sentiment
        
        Args:
            base_recommendation: Original recommendation (Buy, Hold, Sell, etc.)
            sentiment_score: News sentiment score (-1 to +1)
            sentiment_weight: How much news affects decision (0-1)
            
        Returns:
            Tuple of (adjusted_recommendation, reasoning)
        """
        # Normalize sentiment impact
        sentiment_impact = sentiment_score * sentiment_weight
        
        # Recommendation adjustment logic
        if base_recommendation in ["Strong Buy", "Buy"]:
            if sentiment_score > 0.3:
                adjusted = "Strong Buy"
                reason = "Positive technical indicators + positive news momentum"
            elif sentiment_score < -0.3:
                adjusted = "Hold"
                reason = "Good technicals but negative news suggests caution"
            else:
                adjusted = base_recommendation
                reason = "Technical analysis supported by neutral news sentiment"
        
        elif base_recommendation == "Hold":
            if sentiment_score > 0.4:
                adjusted = "Buy"
                reason = "Strong positive news may drive upward momentum"
            elif sentiment_score < -0.4:
                adjusted = "Wait"
                reason = "Negative news suggests waiting for better entry"
            else:
                adjusted = "Hold"
                reason = "Neutral technical and news outlook"
        
        elif base_recommendation in ["Wait", "Sell", "Overextended - Wait"]:
            if sentiment_score > 0.3:
                adjusted = "Hold"
                reason = "Negative technicals offset by positive news"
            else:
                adjusted = base_recommendation
                reason = "Both technical and news sentiment suggest caution"
        
        else:
            adjusted = base_recommendation
            reason = "News sentiment neutral or not applicable"
        
        return adjusted, reason
    
    def get_buy_sell_trajectory(self, ticker: str, current_price: float, news_sentiment: float) -> Dict:
        """
        Generate buy/sell trajectory based on news sentiment
        
        Args:
            ticker: Stock ticker
            current_price: Current stock price
            news_sentiment: Overall news sentiment score (-1 to +1)
            
        Returns:
            Dict with trajectory prediction and target prices
        """
        # Calculate trajectory based on sentiment
        if news_sentiment > 0.4:
            trajectory = "Strong Upward"
            target_7d = current_price * 1.05  # 5% gain expected
            target_30d = current_price * 1.15  # 15% gain expected
            action = "Buy on dips"
            confidence = "High"
        elif news_sentiment > 0.2:
            trajectory = "Moderate Upward"
            target_7d = current_price * 1.03
            target_30d = current_price * 1.10
            action = "Buy"
            confidence = "Medium"
        elif news_sentiment > -0.2:
            trajectory = "Sideways"
            target_7d = current_price * 1.01
            target_30d = current_price * 1.03
            action = "Hold"
            confidence = "Medium"
        elif news_sentiment > -0.4:
            trajectory = "Moderate Downward"
            target_7d = current_price * 0.97
            target_30d = current_price * 0.90
            action = "Wait or Trim"
            confidence = "Medium"
        else:
            trajectory = "Strong Downward"
            target_7d = current_price * 0.95
            target_30d = current_price * 0.85
            action = "Avoid or Sell"
            confidence = "High"
        
        return {
            'trajectory': trajectory,
            'action': action,
            'confidence': confidence,
            'targets': {
                '7_day': round(target_7d, 2),
                '30_day': round(target_30d, 2)
            },
            'sentiment_based': True
        }


# Convenience function
async def analyze_with_news(ticker: str, max_articles: int = 5) -> Dict:
    """Analyze stock with news sentiment"""
    analyzer = NewsAnalyzer()
    return analyzer.analyze_stock_news(ticker, max_articles)
