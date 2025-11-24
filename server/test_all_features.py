#!/usr/bin/env python3
"""
Comprehensive Test Suite for Stock Analysis Features
Tests all functionality including news integration, config management, and recommendations
"""
import asyncio
import sys
from pathlib import Path

# Ensure we can import from server directory
sys.path.insert(0, str(Path(__file__).parent))

from features.stock_analyzer import (
    analyze_stock_with_recommendation,
    analyze_multiple_stocks,
    get_top_recommendations
)
from features.historical_analyzer import analyze_3month_performance, get_3month_recommendations
from features.news_analyzer import NewsAnalyzer
from config_manager import get_config


def print_section(title):
    """Print a section header"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")


async def test_single_stock_analysis():
    """Test 1: Single stock analysis with news"""
    print_section("TEST 1: Single Stock Analysis with News Integration")
    
    ticker = "AAPL"
    print(f"Analyzing {ticker}...\n")
    
    result = await analyze_stock_with_recommendation(ticker, include_news=True)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✓ Ticker: {result['ticker']}")
    print(f"✓ Company: {result.get('company', 'N/A')}")
    print(f"✓ Price: ${result['current_price']:.2f} ({result.get('day_change_percent', 0):+.2f}%)")
    print(f"✓ Recommendation: {result['recommendation']}")
    print(f"✓ Risk Level: {result['risk_level']}")
    
    if 'news' in result and result['news'].get('news_available'):
        news = result['news']
        print(f"\n✓ News Sentiment: {news['overall_sentiment']} (Score: {news['sentiment_score']:.2f})")
        print(f"✓ Articles Analyzed: {news['articles_analyzed']}")
    
    if 'trajectory' in result:
        traj = result['trajectory']
        print(f"\n✓ Trajectory: {traj['trajectory']}")
        print(f"✓ Action: {traj['action']}")
        print(f"✓ 7-Day Target: ${traj['targets']['7_day']}")
    
    return True


async def test_multiple_stocks_analysis():
    """Test 2: Multiple stocks analysis"""
    print_section("TEST 2: Multiple Stocks Analysis")
    
    tickers = ["AAPL", "MSFT", "TSLA"]
    print(f"Analyzing {len(tickers)} stocks: {', '.join(tickers)}\n")
    
    results = await analyze_multiple_stocks(tickers, min_price=0, max_price=500, include_news=False)
    
    if not results:
        print("❌ No results returned")
        return False
    
    print(f"✓ Analyzed {len(results)} stocks successfully\n")
    
    for stock in results:
        print(f"  • {stock['ticker']}: ${stock['current_price']:.2f} - {stock['recommendation']}")
    
    return True


async def test_top_recommendations():
    """Test 3: Top recommendations with scoring"""
    print_section("TEST 3: Top Recommendations with Scoring")
    
    config = get_config()
    tickers = config.get_stock_list('penny')[:8]
    
    print(f"Finding top 5 from {len(tickers)} stocks...\n")
    
    top_stocks = await get_top_recommendations(
        tickers=tickers,
        min_price=1.0,
        max_price=10.0,
        top_n=5,
        include_news=True
    )
    
    if not top_stocks:
        print("❌ No recommendations returned")
        return False
    
    print(f"\n✓ Top {len(top_stocks)} recommendations:\n")
    
    for i, item in enumerate(top_stocks, 1):
        stock = item['stock_data']
        score = item['score']
        print(f"  {i}. {stock['ticker']}: Score {score}/50 - {stock['recommendation']}")
    
    return True


async def test_historical_analysis():
    """Test 4: Historical performance analysis"""
    print_section("TEST 4: 3-Month Historical Analysis")
    
    ticker = "AAPL"
    print(f"Analyzing 3-month performance for {ticker}...\n")
    
    result = await analyze_3month_performance(ticker)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return False
    
    print(f"✓ Ticker: {result['ticker']}")
    print(f"✓ Current Price: ${result['current_price']:.2f}")
    print(f"✓ 3-Month Change: {result['performance_3m']['change_percent']:+.2f}%")
    print(f"✓ Trend: {result['trend']}")
    print(f"✓ Recommendation: {result['recommendation']}")
    
    return True


async def test_config_manager():
    """Test 5: Configuration manager"""
    print_section("TEST 5: Configuration Manager")
    
    config = get_config()
    
    print("✓ Available stock lists:")
    lists = config.list_available_watchlists()
    for list_name in lists:
        stocks = config.get_stock_list(list_name)
        print(f"    • {list_name}: {len(stocks)} stocks")
    
    print(f"\n✓ Price Filters:")
    print(f"    • Min: ${config.get_min_price()}")
    print(f"    • Max: ${config.get_max_price()}")
    
    print(f"\n✓ News Settings:")
    print(f"    • Enabled: {config.is_news_enabled()}")
    print(f"    • Max Articles: {config.get_max_news_articles()}")
    
    return True


async def test_news_analyzer():
    """Test 6: News analyzer standalone"""
    print_section("TEST 6: News Analyzer")
    
    ticker = "TSLA"
    print(f"Fetching and analyzing news for {ticker}...\n")
    
    analyzer = NewsAnalyzer()
    news_data = analyzer.analyze_stock_news(ticker, max_articles=3)
    
    if not news_data.get('news_available'):
        print(f"⚠ No news available for {ticker}")
        return True
    
    print(f"✓ News Sentiment: {news_data['overall_sentiment']}")
    print(f"✓ Sentiment Score: {news_data['sentiment_score']:.2f}")
    print(f"✓ Articles Analyzed: {news_data['articles_analyzed']}")
    
    if news_data.get('news'):
        print(f"\n✓ Recent Headlines:")
        for i, article in enumerate(news_data['news'][:3], 1):
            print(f"    {i}. {article['title'][:60]}...")
            print(f"       Sentiment: {article['sentiment']}")
    
    return True


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("STOCK ANALYSIS SYSTEM - COMPREHENSIVE TEST SUITE")
    print("="*70)
    
    tests = [
        ("Single Stock Analysis", test_single_stock_analysis),
        ("Multiple Stocks Analysis", test_multiple_stocks_analysis),
        ("Top Recommendations", test_top_recommendations),
        ("Historical Analysis", test_historical_analysis),
        ("Configuration Manager", test_config_manager),
        ("News Analyzer", test_news_analyzer),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\n{'='*70}")
    print(f"TOTAL: {passed}/{total} tests passed")
    print(f"{'='*70}\n")
    
    return passed == total


async def quick_test():
    """Quick smoke test"""
    print("\n" + "="*70)
    print("QUICK SMOKE TEST")
    print("="*70 + "\n")
    
    print("Testing basic functionality...\n")
    
    # Test config
    config = get_config()
    print(f"✓ Config loaded: {len(config.list_available_watchlists())} watchlists")
    
    # Test single stock
    result = await analyze_stock_with_recommendation("AAPL", include_news=False)
    if "error" not in result:
        print(f"✓ Stock analysis works: AAPL at ${result['current_price']:.2f}")
    else:
        print(f"❌ Stock analysis failed")
        return False
    
    print("\n✓ All basic functionality working!\n")
    return True


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        # Quick test
        result = asyncio.run(quick_test())
    else:
        # Full test suite
        result = asyncio.run(run_all_tests())
    
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
