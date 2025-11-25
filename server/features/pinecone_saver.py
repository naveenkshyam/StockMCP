"""
Pinecone Vector Database Integration
Save stock recommendations to Pinecone for historical tracking and comparison
Uses HYBRID embeddings: Numeric features + Text embeddings for semantic search
"""
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
from pinecone import Pinecone, ServerlessSpec
import hashlib
import numpy as np

# Pinecone Configuration
PINECONE_API_KEY = "<REPLACE_WITH_YOUR_PINECONE_API_KEY>"  # Change for production
PINECONE_INDEX_NAME = "stock-recommendations"
PINECONE_DIMENSION = 768  # Dimension for embeddings


class PineconeStockSaver:
    """Save and retrieve stock recommendations from Pinecone vector database with hybrid embeddings"""
    
    def __init__(self, api_key: str = PINECONE_API_KEY, use_text_embeddings: bool = True):
        """
        Initialize Pinecone client
        
        Args:
            api_key: Pinecone API key
            use_text_embeddings: If True, uses hybrid (numeric + text) embeddings.
                                If False, uses only numeric embeddings (faster, no model download)
        """
        self.api_key = api_key
        self.pc = Pinecone(api_key=api_key)
        self.index_name = PINECONE_INDEX_NAME
        self.index = None
        self.use_text_embeddings = use_text_embeddings
        self.text_model = None
        
        # Initialize text embedding model if needed
        if use_text_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                print("Loading text embedding model (first time: ~500MB download)...")
                # Using lightweight model: all-MiniLM-L6-v2 (384 dimensions, 80MB)
                self.text_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                print("✓ Text embedding model loaded")
            except Exception as e:
                print(f"⚠ Could not load text model: {e}")
                print("  Falling back to numeric-only embeddings")
                self.use_text_embeddings = False
        
    def initialize_index(self):
        """Create or connect to Pinecone index"""
        try:
            # Check if index exists
            existing_indexes = self.pc.list_indexes()
            index_names = [idx['name'] for idx in existing_indexes]
            
            if self.index_name not in index_names:
                print(f"Creating new Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=PINECONE_DIMENSION,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                print(f"✓ Index '{self.index_name}' created successfully")
            else:
                print(f"✓ Using existing index: {self.index_name}")
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            return True
            
        except Exception as e:
            print(f"✗ Error initializing Pinecone index: {str(e)}")
            return False
    
    def create_embedding(self, stock_data: Dict[str, Any]) -> List[float]:
        """
        Create HYBRID vector embedding from stock data
        
        Combines:
        1. Numeric features (price, volume, scores) - for exact comparisons
        2. Text embeddings (company, sector, news) - for semantic similarity
        
        This allows both:
        - Tracking: "Show me AAPL's recommendation yesterday"
        - Discovery: "Find stocks similar to Tesla in EV sector"
        """
        
        # ============================================
        # PART 1: NUMERIC FEATURES (Critical for tracking)
        # ============================================
        numeric_features = [
            # Price data (normalized to 0-1 range for stability)
            float(stock_data.get('current_price', 0)) / 1000.0,  # Max $1000
            float(stock_data.get('day_change_percent', 0)) / 100.0,  # -100% to +100%
            float(stock_data.get('volume', 0)) / 100_000_000.0,  # Max 100M volume
            
            # Recommendation encoding (0-1 scale)
            float({'Strong Buy': 1.0, 'Buy': 0.8, 'Hold': 0.6, 
                   'Wait for Pullback': 0.4, 'Overextended - Wait': 0.2, 'Sell': 0.0}
            .get(stock_data.get('recommendation', 'Hold'), 0.6)),
            
            # Risk encoding (0-1 scale)
            float({'Low': 0.3, 'Medium': 0.6, 'High': 1.0}
            .get(stock_data.get('risk_level', 'Medium'), 0.6)),
            
            # Score (already 0-1 normalized)
            float(stock_data.get('score', 0)) / 50.0,
        ]
        
        # Add trajectory features if available
        if 'trajectory' in stock_data:
            traj = stock_data['trajectory']
            
            # Trend encoding (-1 to +1)
            trend_map = {'Uptrend': 1.0, 'Downtrend': -1.0, 'Sideways': 0.0}
            trend_val = trend_map.get(traj.get('trajectory', 'Sideways'), 0.0)
            numeric_features.append(float(trend_val))
            
            # Momentum percentage
            if isinstance(traj.get('momentum'), dict):
                momentum_pct = float(traj['momentum'].get('percent_change', 0)) / 100.0
                numeric_features.append(momentum_pct)
            else:
                numeric_features.append(0.0)
        else:
            numeric_features.extend([0.0, 0.0])
        
        # Add news sentiment if available
        if 'news' in stock_data and stock_data['news'].get('news_available'):
            sentiment_score = float(stock_data['news'].get('sentiment_score', 0))
            numeric_features.append(sentiment_score)
        else:
            numeric_features.append(0.0)
        
        # ============================================
        # PART 2: TEXT EMBEDDINGS (Semantic similarity)
        # ============================================
        if self.use_text_embeddings and self.text_model:
            try:
                # Create rich text description
                text_parts = []
                
                # Company and ticker
                if stock_data.get('company'):
                    text_parts.append(stock_data['company'])
                
                # Sector and industry for similarity
                if stock_data.get('sector'):
                    text_parts.append(f"Sector: {stock_data['sector']}")
                if stock_data.get('industry'):
                    text_parts.append(f"Industry: {stock_data['industry']}")
                
                # Recommendation context
                text_parts.append(f"Recommendation: {stock_data.get('recommendation', 'Hold')}")
                
                # News headline if available
                if 'news' in stock_data and stock_data['news'].get('news_available'):
                    headline = stock_data['news'].get('top_headline', '')
                    if headline:
                        text_parts.append(f"News: {headline[:100]}")
                
                # Trajectory context
                if 'trajectory' in stock_data:
                    traj_text = stock_data['trajectory'].get('trajectory', 'Unknown')
                    text_parts.append(f"Trend: {traj_text}")
                
                # Combine all text
                full_text = " | ".join(text_parts)
                
                # Generate embedding (384 dimensions from all-MiniLM-L6-v2)
                text_embedding = self.text_model.encode(full_text, convert_to_numpy=True)
                text_embedding = text_embedding.astype(float).tolist()
                
            except Exception as e:
                print(f"⚠ Text embedding failed: {e}, using zeros")
                text_embedding = [0.0] * 384
        else:
            # No text embeddings - use zeros
            text_embedding = [0.0] * 384
        
        # ============================================
        # PART 3: COMBINE & PAD TO 768 DIMENSIONS
        # ============================================
        
        # Combine: [numeric features] + [text embedding] + [padding]
        combined = numeric_features + text_embedding
        
        # Ensure all values are float
        combined = [float(x) for x in combined]
        
        # Pad or truncate to exactly 768 dimensions
        if len(combined) < PINECONE_DIMENSION:
            # Pad with zeros
            combined.extend([0.0] * (PINECONE_DIMENSION - len(combined)))
        elif len(combined) > PINECONE_DIMENSION:
            # Truncate
            combined = combined[:PINECONE_DIMENSION]
        
        return combined
    
    def save_recommendations(
        self,
        recommendations: List[Dict[str, Any]],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        Save stock recommendations to Pinecone (skips duplicates for today)
        
        Args:
            recommendations: List of stock recommendation dictionaries
            metadata: Additional metadata (search params, timestamp, etc.)
        
        Returns:
            bool: Success status
        """
        if not self.index:
            if not self.initialize_index():
                return False
        
        try:
            timestamp = datetime.now().isoformat()
            date_str = datetime.now().strftime('%Y-%m-%d')
            
            # Check for existing recommendations today
            print(f"\nChecking for existing recommendations from {date_str}...")
            existing_recs = self.get_recommendations_by_date(date_str)
            existing_tickers = {rec['ticker'] for rec in existing_recs}
            
            if existing_tickers:
                print(f"✓ Found {len(existing_tickers)} existing recommendations: {', '.join(sorted(existing_tickers))}")
            
            vectors_to_upsert = []
            skipped_count = 0
            
            print(f"\nPreparing {len(recommendations)} recommendations for Pinecone...")
            
            for i, stock in enumerate(recommendations):
                ticker = stock.get('ticker', 'UNKNOWN')
                company = stock.get('company', 'N/A')
                price = stock.get('current_price', 0)
                recommendation = stock.get('recommendation', 'Hold')
                
                # Skip if already saved today
                if ticker in existing_tickers:
                    print(f"  {i+1}. {ticker} ({company}) - ${price:.2f} - {recommendation} [SKIPPED - Already saved today]")
                    skipped_count += 1
                    continue
                
                print(f"  {i+1}. {ticker} ({company}) - ${price:.2f} - {recommendation}")
                
                # Create unique ID for this recommendation
                id_str = f"{ticker}_{date_str}_{i}"
                vector_id = hashlib.md5(id_str.encode()).hexdigest()[:16]
                
                # Create embedding
                embedding = self.create_embedding(stock)
                
                # Prepare metadata (Pinecone has limits on metadata size)
                stock_metadata = {
                    'ticker': ticker,
                    'company': stock.get('company', 'N/A')[:100],  # Limit length
                    'date': date_str,
                    'timestamp': timestamp,
                    'current_price': float(stock.get('current_price', 0)),
                    'day_change_percent': float(stock.get('day_change_percent', 0)),
                    'recommendation': stock.get('recommendation', 'Hold'),
                    'risk_level': stock.get('risk_level', 'Medium'),
                    'score': float(stock.get('score', 0)),
                    'volume': int(stock.get('volume', 0)),
                }
                
                # Add trajectory if available
                if 'trajectory' in stock:
                    stock_metadata['trajectory_trend'] = stock['trajectory'].get('trajectory', 'Unknown')
                    stock_metadata['trajectory_action'] = stock['trajectory'].get('action', 'Unknown')
                
                # Add news sentiment if available
                if 'news' in stock and stock['news'].get('news_available'):
                    stock_metadata['news_sentiment'] = stock['news'].get('overall_sentiment', 'Neutral')
                    stock_metadata['news_score'] = float(stock['news'].get('sentiment_score', 0))
                
                # Add search metadata
                if metadata:
                    stock_metadata['search_mode'] = metadata.get('mode', 'unknown')
                    stock_metadata['price_range'] = f"${metadata.get('min_price', 0)}-${metadata.get('max_price', 0)}"
                
                vectors_to_upsert.append({
                    'id': vector_id,
                    'values': embedding,
                    'metadata': stock_metadata
                })
            
            # Upsert to Pinecone (batch upsert)
            if vectors_to_upsert:
                self.index.upsert(vectors=vectors_to_upsert)
                print(f"\n✓ Saved {len(vectors_to_upsert)} NEW recommendations to Pinecone")
                if skipped_count > 0:
                    print(f"  Skipped {skipped_count} stocks (already saved today)")
                print(f"  Index: {self.index_name}")
                print(f"  Date: {date_str}")
                return True
            else:
                if skipped_count > 0:
                    print(f"\nℹ All {skipped_count} recommendations already saved today")
                else:
                    print("✗ No recommendations to save")
                return False
                
        except Exception as e:
            print(f"✗ Error saving to Pinecone: {str(e)}")
            return False
    
    def query_similar_recommendations(
        self,
        ticker: str,
        top_k: int = 5,
        date_filter: str = None
    ) -> List[Dict[str, Any]]:
        """
        Query similar recommendations for a ticker
        
        Args:
            ticker: Stock ticker symbol
            top_k: Number of similar results to return
            date_filter: Optional date filter (YYYY-MM-DD)
        
        Returns:
            List of similar recommendations
        """
        if not self.index:
            if not self.initialize_index():
                return []
        
        try:
            # Query by metadata filter
            filter_dict = {'ticker': ticker}
            if date_filter:
                filter_dict['date'] = date_filter
            
            # Query the index
            results = self.index.query(
                vector=[0.0] * PINECONE_DIMENSION,  # Dummy vector
                filter=filter_dict,
                top_k=top_k,
                include_metadata=True
            )
            
            return [match['metadata'] for match in results.get('matches', [])]
            
        except Exception as e:
            print(f"✗ Error querying Pinecone: {str(e)}")
            return []
    
    def get_recommendations_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """
        Get all recommendations for a specific date
        
        Args:
            date_str: Date in YYYY-MM-DD format
        
        Returns:
            List of recommendations
        """
        if not self.index:
            if not self.initialize_index():
                return []
        
        try:
            # Query by date
            results = self.index.query(
                vector=[0.0] * PINECONE_DIMENSION,
                filter={'date': date_str},
                top_k=100,  # Get up to 100 recommendations
                include_metadata=True
            )
            
            return [match['metadata'] for match in results.get('matches', [])]
            
        except Exception as e:
            print(f"✗ Error querying by date: {str(e)}")
            return []
    
    def compare_recommendations(self, ticker: str, date1: str, date2: str) -> Dict[str, Any]:
        """
        Compare recommendations for a ticker between two dates
        
        Args:
            ticker: Stock ticker symbol
            date1: First date (YYYY-MM-DD)
            date2: Second date (YYYY-MM-DD)
        
        Returns:
            Comparison dictionary
        """
        recs1 = self.query_similar_recommendations(ticker, top_k=1, date_filter=date1)
        recs2 = self.query_similar_recommendations(ticker, top_k=1, date_filter=date2)
        
        if not recs1 or not recs2:
            return {
                'ticker': ticker,
                'comparison': 'unavailable',
                'message': 'Recommendations not found for one or both dates'
            }
        
        rec1 = recs1[0]
        rec2 = recs2[0]
        
        return {
            'ticker': ticker,
            'date1': date1,
            'date2': date2,
            'price_change': rec2['current_price'] - rec1['current_price'],
            'price_change_percent': ((rec2['current_price'] - rec1['current_price']) / rec1['current_price'] * 100),
            'recommendation_change': f"{rec1['recommendation']} → {rec2['recommendation']}",
            'rec1': rec1,
            'rec2': rec2
        }
    
    def get_index_stats(self) -> Dict[str, Any]:
        """Get statistics about the Pinecone index"""
        if not self.index:
            if not self.initialize_index():
                return {}
        
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.get('total_vector_count', 0),
                'dimension': stats.get('dimension', 0),
                'index_fullness': stats.get('index_fullness', 0),
                'namespaces': stats.get('namespaces', {})
            }
        except Exception as e:
            print(f"✗ Error getting stats: {str(e)}")
            return {}


def save_to_pinecone(recommendations: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> bool:
    """
    Convenience function to save recommendations to Pinecone
    
    Args:
        recommendations: List of stock recommendations
        metadata: Optional metadata about the search
    
    Returns:
        bool: Success status
    """
    saver = PineconeStockSaver()
    return saver.save_recommendations(recommendations, metadata)


def compare_with_yesterday(ticker: str) -> Dict[str, Any]:
    """
    Compare today's recommendation with yesterday's
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Comparison dictionary
    """
    from datetime import timedelta
    
    today = datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    saver = PineconeStockSaver()
    return saver.compare_recommendations(ticker, yesterday, today)


if __name__ == "__main__":
    # Test connection
    print("Testing Pinecone connection...")
    saver = PineconeStockSaver()
    
    if saver.initialize_index():
        print("\n✓ Pinecone connection successful!")
        stats = saver.get_index_stats()
        print(f"  Total vectors: {stats.get('total_vectors', 0)}")
        print(f"  Dimension: {stats.get('dimension', 0)}")
    else:
        print("\n✗ Pinecone connection failed")
