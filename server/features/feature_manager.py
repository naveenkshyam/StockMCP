"""
Feature Manager - Command-line interface for stock analysis features
Allows selecting and running different analysis features
"""
import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add server directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from features.stock_analyzer import (
    analyze_stock_with_recommendation,
    analyze_multiple_stocks,
    get_top_recommendations,
    format_top_recommendations_report
)
from features.historical_analyzer import analyze_3month_performance, get_3month_recommendations
from features.auto_scheduler import StockScheduler, send_immediate_report
from config_manager import get_config
from features.pinecone_saver import PineconeStockSaver, save_to_pinecone
from features.pinecone_historical import (
    PineconeHistoricalAnalyzer,
    analyze_pinecone_historical,
    format_historical_report
)


# Default watchlist (can be customized)
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "F", "NOK", "AMC", "ABEV", "PLUG", "NIO", "SOFI", "RIVN",
    "LCID", "BAC", "WFC", "INTC", "AMD", "TSLA", "NVDA", "PYPL", "SQ", "SNAP",
    "UBER", "LYFT", "AAL", "DAL", "CCL", "NCLH", "MGM", "WYNN", "GPRO", "PTON",
    "BBBY", "BBY", "TGT", "WMT", "COST", "HD", "LOW", "DIS", "NFLX", "PARA",
    "ABTS", "GSAT", "TLRY", "CGC", "SNDL", "ACB", "CRON", "OGI", "KERN", "HIMS",
    "HYZN", "EVGO", "BLNK", "CHPT", "GOEV", "WKHS", "XL", "ARVL", "ENVX", "QS"
]

# Extended watchlist for comprehensive search (60+ stocks)
EXTENDED_WATCHLIST = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AMD', 
    'NFLX', 'DIS', 'PYPL', 'INTC', 'CSCO', 'ADBE', 'CRM', 'ORCL',
    'BABA', 'V', 'MA', 'JPM', 'BAC', 'WMT', 'PFE', 'KO', 'PEP',
    'NKE', 'MCD', 'SBUX', 'COST', 'HD', 
    'F', 'AAL', 'CCL', 'PLUG', 'SOFI', 'NIO', 'LCID', 'RIVN', 
    'UBER', 'LYFT', 'SNAP', 'PINS', 'ZM', 'DKNG', 'PLTR', 'BB', 
    'NOK', 'AMC', 'GME', 'WKHS', 'SIRI', 'VALE', 'GOLD', 'ABEV',
    'GNUS', 'IDEX', 'BNGO', 'SNDL', 'CLVS', 'INO', 'NKLA',
    'TOPS', 'SHIP', 'CLOV', 'WISH', 'RIDE', 'MULN',
    'EXPR', 'KOSS', 'SENS', 'OCGN', 'GEVO', 'FCEL', 'MARA', 'RIOT',
    'ACB', 'CGC', 'TLRY', 'HEXO', 'OGI', 'CRON'
]


async def feature_analyze_stocks(args):
    """Feature: Analyze stocks with recommendations"""
    print(f"\n{'='*60}")
    print("Feature: Stock Analysis with Recommendations")
    print(f"{'='*60}\n")
    
    config = get_config()
    
    # Get stock list from config or command line
    if args.tickers:
        tickers = args.tickers.split(',')
    elif args.list:
        tickers = config.get_stock_list(args.list)
        print(f"Using watchlist '{args.list}' from config")
    else:
        tickers = config.get_stock_list('default')
        print(f"Using default watchlist from config")
    
    min_price = args.min_price if args.min_price else config.get_min_price()
    max_price = args.max_price if args.max_price else config.get_max_price()
    
    print(f"Analyzing {len(tickers)} stocks in price range ${min_price}-${max_price}...\n")
    
    # Check if top recommendations requested
    if args.top:
        top_stocks = await get_top_recommendations(
            tickers=tickers,
            min_price=min_price,
            max_price=max_price,
            top_n=args.top,
            include_news=not args.no_news
        )
        
        if not top_stocks:
            print("No stocks found matching criteria.")
            return
        
        print(f"\nTop {len(top_stocks)} Recommendations:\n")
        
        for i, item in enumerate(top_stocks, 1):
            stock = item['stock_data']
            score = item['score']
            print(f"{i}. {stock['ticker']} - {stock.get('company', 'N/A')}")
            print(f"   Price: ${stock['current_price']:.2f} ({stock.get('day_change_percent', 0):+.2f}%)")
            print(f"   Score: {score}/50")
            print(f"   Recommendation: {stock['recommendation']}")
            print(f"   Risk Level: {stock['risk_level']}")
            
            if 'news' in stock and stock['news'].get('news_available'):
                print(f"   News Sentiment: {stock['news']['overall_sentiment']} ({stock['news']['sentiment_score']:.2f})")
            
            if 'trajectory' in stock:
                print(f"   Trajectory: {stock['trajectory']['trajectory']} - {stock['trajectory']['action']}")
            
            print()
        
        # Save if requested
        if args.save:
            report = format_top_recommendations_report(top_stocks, min_price, max_price)
            filename = f"top_{args.top}_stocks_{args.save}.txt"
            with open(filename, 'w') as f:
                f.write(report)
            print(f"Report saved to {filename}")
    
    else:
        # Regular analysis
        stocks = await analyze_multiple_stocks(
            tickers=tickers,
            min_price=min_price,
            max_price=max_price,
            include_news=not args.no_news
        )
        
        print(f"Found {len(stocks)} stocks matching criteria:\n")
        
        for i, stock in enumerate(stocks, 1):
            print(f"{i}. {stock['ticker']} - {stock.get('company', 'N/A')}")
            print(f"   Price: ${stock['current_price']:.2f} ({stock.get('day_change_percent', 0):+.2f}%)")
            print(f"   Recommendation: {stock['recommendation']}")
            print(f"   Risk Level: {stock['risk_level']}")
            if 'entry_points' in stock:
                print(f"   Entry Points: {stock['entry_points'].get('conservative', 'N/A')} (conservative)")
            if 'stop_loss' in stock:
                print(f"   Stop Loss: {stock['stop_loss']}")
            
            if 'news' in stock and stock['news'].get('news_available'):
                print(f"   News: {stock['news']['overall_sentiment']} sentiment")
            
            print()
        
        if args.save:
            filename = f"stock_analysis_{args.save}.txt"
            with open(filename, 'w') as f:
                f.write(f"Stock Analysis Report\n")
                f.write(f"Generated: {datetime.now().isoformat()}\n\n")
                for stock in stocks:
                    f.write(f"{stock['ticker']}: ${stock['current_price']:.2f} - {stock['recommendation']}\n")
            print(f"Results saved to {filename}")


async def feature_search_all_stocks(args):
    """Feature: Search ALL 60+ stocks in extended watchlist"""
    print(f"\n{'='*60}")
    print("Feature: Search ALL Stocks ($1-$10) - Top Recommendations")
    print(f"{'='*60}\n")
    
    min_price = args.min_price if args.min_price else 1.0
    max_price = args.max_price if args.max_price else 10.0
    top_n = args.top if args.top else 10
    
    print(f"Searching {len(EXTENDED_WATCHLIST)} stocks in extended watchlist...")
    print(f"Price range: ${min_price} - ${max_price}")
    print(f"Top recommendations: {top_n}\n")
    
    # Get top recommendations from extended watchlist
    top_stocks = await get_top_recommendations(
        tickers=EXTENDED_WATCHLIST,
        min_price=min_price,
        max_price=max_price,
        top_n=top_n,
        include_news=not args.no_news
    )
    
    if not top_stocks:
        print("No stocks found matching criteria.")
        return
    
    # Get yesterday's data from Pinecone for comparison
    from datetime import datetime, timedelta
    yesterday_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    print("Checking Pinecone for yesterday's recommendations...")
    saver = PineconeStockSaver()
    saver.initialize_index()
    
    yesterday_recs = saver.get_recommendations_by_date(yesterday_date)
    yesterday_map = {rec['ticker']: rec for rec in yesterday_recs} if yesterday_recs else {}
    
    if yesterday_map:
        print(f"✓ Found {len(yesterday_map)} recommendations from {yesterday_date}\n")
    else:
        print(f"ℹ No data from yesterday ({yesterday_date}) - this is your first run\n")
    
    print(f"Top {len(top_stocks)} Recommendations from Extended Watchlist:\n")
    
    changes_detected = 0
    no_change_count = 0
    
    for i, item in enumerate(top_stocks, 1):
        stock = item['stock_data']
        score = item['score']
        ticker = stock['ticker']
        
        # Compare with yesterday's data first
        has_change = False
        if ticker in yesterday_map:
            yesterday_rec = yesterday_map[ticker]
            yesterday_price = yesterday_rec.get('current_price', 0)
            yesterday_recommendation = yesterday_rec.get('recommendation', 'Unknown')
            
            price_change = stock['current_price'] - yesterday_price
            price_change_pct = (price_change / yesterday_price * 100) if yesterday_price > 0 else 0
            
            # Check if there are any significant changes
            rec_changed = stock['recommendation'] != yesterday_recommendation
            price_changed = abs(price_change_pct) > 1.0  # More than 1% change
            
            if rec_changed or price_changed:
                has_change = True
                changes_detected += 1
            else:
                no_change_count += 1
                continue  # Skip stocks with no significant changes
        
        # Only display stocks with changes or new stocks
        print(f"{changes_detected}. {ticker} - {stock.get('company', 'N/A')}")
        print(f"   Price: ${stock['current_price']:.2f} ({stock.get('day_change_percent', 0):+.2f}%)")
        print(f"   Score: {score}/50")
        print(f"   Recommendation: {stock['recommendation']}")
        print(f"   Risk Level: {stock['risk_level']}")
        
        # Show comparison with yesterday's data
        if ticker in yesterday_map:
            yesterday_rec = yesterday_map[ticker]
            yesterday_price = yesterday_rec.get('current_price', 0)
            yesterday_recommendation = yesterday_rec.get('recommendation', 'Unknown')
            
            price_change = stock['current_price'] - yesterday_price
            price_change_pct = (price_change / yesterday_price * 100) if yesterday_price > 0 else 0
            
            print(f"   📊 Yesterday: {yesterday_recommendation} @ ${yesterday_price:.2f}")
            
            if stock['recommendation'] != yesterday_recommendation:
                print(f"   🔄 CHANGED: {yesterday_recommendation} → {stock['recommendation']}")
            
            if abs(price_change_pct) > 5:
                direction = "↗" if price_change > 0 else "↘"
                print(f"   {direction} Price Change: {price_change_pct:+.2f}% since yesterday")
            elif abs(price_change_pct) > 1:
                direction = "↗" if price_change > 0 else "↘"
                print(f"   {direction} Price Change: {price_change_pct:+.2f}% since yesterday")
        
        if 'news' in stock and stock['news'].get('news_available'):
            print(f"   News Sentiment: {stock['news']['overall_sentiment']} ({stock['news']['sentiment_score']:.2f})")
        
        if 'trajectory' in stock:
            print(f"   Trajectory: {stock['trajectory']['trajectory']} - {stock['trajectory']['action']}")
        
        print()
    
    # Summary
    if no_change_count > 0:
        print(f"ℹ Filtered out {no_change_count} stocks with no significant changes (< 1% price change and same recommendation)")
    
    print(f"\n✓ Showing {changes_detected} stocks with changes")
    
    # Save if requested
    if args.save:
        report = format_top_recommendations_report(top_stocks, min_price, max_price)
        filename = f"all_stocks_top_{top_n}_{args.save}.txt"
        with open(filename, 'w') as f:
            f.write(report)
        print(f"Report saved to {filename}")
    
    return top_stocks  # Return for potential use by save-pinecone


async def feature_save_to_pinecone(args):
    """Feature: Save recommendations to Pinecone vector database"""
    print(f"\n{'='*60}")
    print("Feature: Save Recommendations to Pinecone")
    print(f"{'='*60}\n")
    
    config = get_config()
    
    # Determine search mode
    if args.mode == 'all':
        print("Mode: ALL stocks search (extended watchlist)")
        min_price = args.min_price if args.min_price else 1.0
        max_price = args.max_price if args.max_price else 10.0
        top_n = args.top if args.top else 10
        
        print(f"Searching {len(EXTENDED_WATCHLIST)} stocks...")
        print(f"Price range: ${min_price} - ${max_price}")
        print(f"Top N: {top_n}\n")
        
        top_stocks = await get_top_recommendations(
            tickers=EXTENDED_WATCHLIST,
            min_price=min_price,
            max_price=max_price,
            top_n=top_n,
            include_news=True
        )
        
        metadata = {
            'mode': 'extended_watchlist',
            'min_price': min_price,
            'max_price': max_price,
            'total_searched': len(EXTENDED_WATCHLIST)
        }
        
    elif args.mode == 'config':
        print("Mode: Configured stocks search (config.yaml)")
        list_name = args.list if args.list else 'default'
        tickers = config.get_stock_list(list_name)
        min_price = args.min_price if args.min_price else config.get_min_price()
        max_price = args.max_price if args.max_price else config.get_max_price()
        top_n = args.top if args.top else 20
        
        print(f"Using watchlist '{list_name}' from config")
        print(f"Analyzing {len(tickers)} stocks...")
        print(f"Top N: {top_n}\n")
        
        top_stocks = await get_top_recommendations(
            tickers=tickers,
            min_price=min_price,
            max_price=max_price,
            top_n=top_n,
            include_news=True
        )
        
        metadata = {
            'mode': 'config',
            'list_name': list_name,
            'min_price': min_price,
            'max_price': max_price,
            'total_searched': len(tickers)
        }
    else:
        print(f"✗ Invalid mode: {args.mode}")
        print("Valid modes: 'all' or 'config'")
        return
    
    if not top_stocks:
        print("✗ No stocks found matching criteria. Nothing to save.")
        return
    
    print(f"\nFound {len(top_stocks)} recommendations to save\n")
    
    # Extract stock data from top_stocks
    recommendations = [item['stock_data'] for item in top_stocks]
    
    # Save to Pinecone
    print("Saving to Pinecone vector database...")
    success = save_to_pinecone(recommendations, metadata)
    
    if success:
        print("\n" + "="*60)
        print("✓ SUCCESS: Recommendations saved to Pinecone!")
        print("="*60)
        print("\nYou can now:")
        print("  • Run this again tomorrow to track changes")
        print("  • Compare today's vs tomorrow's recommendations")
        print("  • Analyze how recommendations evolved over time")
        print()
    else:
        print("\n✗ Failed to save recommendations to Pinecone")


async def feature_pinecone_historical(args):
    """Feature: Analyze historical performance of stocks in Pinecone (3-month comparison)"""
    print(f"\n{'='*60}")
    print("Feature: Pinecone Historical Analysis (3-Month Comparison)")
    print(f"{'='*60}\n")
    
    analyzer = PineconeHistoricalAnalyzer()
    
    if args.ticker:
        # Analyze single stock
        print(f"Analyzing {args.ticker} with 3-month historical comparison...\n")
        
        analysis = await analyzer.analyze_with_news_and_recommendation(
            ticker=args.ticker,
            current_date=args.date
        )
        
        if "error" in analysis:
            print(f"✗ Error: {analysis['error']}")
            return
        
        # Display results
        print(f"{'='*70}")
        print(f"{analysis['ticker']} - {analysis['company']}")
        print(f"{'='*70}\n")
        
        # Price comparison
        current = analysis['current_data']
        old = analysis['three_months_ago']
        perf = analysis['performance']
        
        print(f"PRICE COMPARISON:")
        print(f"  Current ({analysis['current_date']}): ${current['price']:.2f}")
        print(f"  3 Months Ago ({analysis['comparison_date']}): ${old['price']:.2f}")
        print(f"  Change: {perf['price_change']:+.2f} ({perf['price_change_percent']:+.2f}%)")
        print(f"  Performance Rating: {perf['performance_rating']}\n")
        
        # Recommendation comparison
        print(f"RECOMMENDATION CHANGE:")
        print(f"  3 Months Ago: {old['recommendation']} (Risk: {old['risk_level']})")
        print(f"  Current: {current['recommendation']} (Risk: {current['risk_level']})\n")
        
        # Technical analysis
        tech = analysis['technical_analysis']
        print(f"TECHNICAL ANALYSIS:")
        print(f"  Trend: {tech['trend']}")
        print(f"  Volatility: {tech['volatility']}")
        print(f"  Price vs MA20: {tech['price_vs_ma20']}")
        print(f"  Price vs MA50: {tech['price_vs_ma50']}\n")
        
        # News analysis
        news = analysis['news_analysis']
        print(f"NEWS ANALYSIS:")
        if news.get('news_available'):
            print(f"  Overall Sentiment: {news['overall_sentiment']}")
            print(f"  Sentiment Score: {news['sentiment_score']:.2f}")
            print(f"  Articles Analyzed: {news['articles_analyzed']}")
            print(f"\n  Recent Headlines:")
            for article in news['news'][:3]:
                print(f"    • {article['title'][:80]}...")
                print(f"      Sentiment: {article['sentiment']} ({article['sentiment_score']:+.2f})")
        else:
            print(f"  No recent news available\n")
        
        # Final recommendation
        rec = analysis['recommendation']
        print(f"\n{'='*70}")
        print(f"RECOMMENDATION: {rec['recommendation']} (Score: {rec['score']}/100)")
        print(f"{'='*70}")
        print(f"Action: {rec['action']}")
        print(f"Confidence: {rec['confidence']}\n")
        
        print(f"Key Factors:")
        for factor in rec['factors']:
            print(f"  {factor}")
        
        print(f"\nReasoning:")
        print(f"  {rec['reasoning']}\n")
        
        # Save if requested
        if args.save:
            filename = f"pinecone_historical_{args.ticker}_{args.save}.txt"
            with open(filename, 'w') as f:
                f.write(format_historical_report([analysis]))
            print(f"Report saved to {filename}")
    
    else:
        # Analyze all stocks from Pinecone
        print(f"Analyzing ALL stocks from Pinecone for date: {args.date or 'today'}...")
        print(f"Minimum score filter: {args.min_score}")
        print(f"Sort by: {args.sort_by}\n")
        
        analyses = await analyzer.analyze_all_pinecone_stocks(
            date=args.date,
            min_score=args.min_score,
            sort_by=args.sort_by
        )
        
        if not analyses:
            print("✗ No stocks found for analysis")
            return
        
        print(f"\n{'='*70}")
        print(f"Found {len(analyses)} stocks meeting criteria (score >= {args.min_score})")
        print(f"{'='*70}\n")
        
        # Display top stocks
        for i, analysis in enumerate(analyses[:args.display_limit], 1):
            current = analysis['current_data']
            perf = analysis['performance']
            rec = analysis['recommendation']
            news = analysis['news_analysis']
            
            print(f"{i}. {analysis['ticker']} - {analysis['company']}")
            print(f"   Price: ${current['price']:.2f} | 3M Change: {perf['price_change_percent']:+.2f}% ({perf['performance_rating']})")
            print(f"   Recommendation: {rec['recommendation']} (Score: {rec['score']}/100)")
            print(f"   News: {news.get('overall_sentiment', 'N/A')} ({news.get('sentiment_score', 0):.2f})")
            print(f"   Action: {rec['action']}")
            print()
        
        if len(analyses) > args.display_limit:
            print(f"... and {len(analyses) - args.display_limit} more stocks")
        
        # Save if requested
        if args.save:
            filename = f"pinecone_historical_all_{args.save}.txt"
            with open(filename, 'w') as f:
                f.write(format_historical_report(analyses))
            print(f"\nFull report saved to {filename}")


async def feature_historical_analysis(args):
    """Feature: 3-Month Historical Analysis"""
    print(f"\n{'='*60}")
    print("Feature: 3-Month Historical Performance Analysis")
    print(f"{'='*60}\n")
    
    config = get_config()
    
    # Get stock list from config or command line
    if args.tickers:
        tickers = args.tickers.split(',')
    elif args.list:
        tickers = config.get_stock_list(args.list)
        print(f"Using watchlist '{args.list}' from config")
    else:
        tickers = DEFAULT_WATCHLIST
        print("Using default watchlist")
    
    print(f"Analyzing 3-month performance for {len(tickers)} stocks...\n")
    
    recommendations = await get_3month_recommendations(
        tickers=tickers,
        min_price=args.min_price,
        max_price=args.max_price,
        min_performance=args.min_performance
    )
    
    print(f"Found {len(recommendations)} stocks with {args.min_performance}%+ 3-month performance:\n")
    
    for i, stock in enumerate(recommendations, 1):
        print(f"{i}. {stock['ticker']} - {stock.get('company', 'N/A')}")
        print(f"   Current Price: ${stock['current_price']:.2f}")
        print(f"   3-Month Performance: {stock['performance_3m']['change_percent']:+.2f}%")
        print(f"   Trend: {stock['trend']}")
        print(f"   Recommendation: {stock['recommendation']}")
        print(f"   Volatility: {stock['volatility_3m']}")
        print()
    
    if args.save:
        filename = f"historical_analysis_{args.save}.txt"
        with open(filename, 'w') as f:
            f.write(f"3-Month Historical Analysis Report\n\n")
            for stock in recommendations:
                f.write(f"{stock['ticker']}: {stock['performance_3m']['change_percent']:+.2f}% - {stock['recommendation']}\n")
        print(f"Results saved to {filename}")


async def feature_send_email(args):
    """Feature: Send email report"""
    print(f"\n{'='*60}")
    print("Feature: Email Report")
    print(f"{'='*60}\n")
    
    if not all([args.email_from, args.email_password, args.email_to]):
        print("Error: Email credentials required!")
        print("Use --email-from, --email-password, --email-to")
        return
    
    tickers = args.tickers.split(',') if args.tickers else DEFAULT_WATCHLIST
    print(f"Sending email report for {len(tickers)} stocks...\n")
    
    await send_immediate_report(
        email_from=args.email_from,
        email_password=args.email_password,
        email_to=args.email_to,
        watchlist=tickers,
        min_price=args.min_price,
        max_price=args.max_price
    )
    
    print("Email sent successfully!")


def feature_schedule_email(args):
    """Feature: Schedule automatic email reports"""
    print(f"\n{'='*60}")
    print("Feature: Auto-Scheduled Email Reports")
    print(f"{'='*60}\n")
    
    if not all([args.email_from, args.email_password, args.email_to]):
        print("Error: Email credentials required!")
        print("Use --email-from, --email-password, --email-to")
        return
    
    tickers = args.tickers.split(',') if args.tickers else DEFAULT_WATCHLIST
    
    scheduler = StockScheduler(
        email_from=args.email_from,
        email_password=args.email_password,
        email_to=args.email_to
    )
    
    if args.schedule_type == 'daily':
        hour, minute = map(int, args.schedule_time.split(':'))
        scheduler.schedule_daily(
            hour=hour,
            minute=minute,
            watchlist=tickers,
            min_price=args.min_price,
            max_price=args.max_price
        )
        print(f"Scheduled daily reports at {args.schedule_time}")
    
    elif args.schedule_type == 'weekly':
        hour, minute = map(int, args.schedule_time.split(':'))
        scheduler.schedule_weekly(
            day=args.schedule_day,
            hour=hour,
            minute=minute,
            watchlist=tickers,
            min_price=args.min_price,
            max_price=args.max_price
        )
        print(f"Scheduled weekly reports on {args.schedule_day} at {args.schedule_time}")
    
    print("\nScheduler is running...")
    scheduler.run()


def main():
    parser = argparse.ArgumentParser(
        description="Stock Analysis Feature Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search ALL 60+ stocks for top 10 recommendations
  python feature_manager.py search-all --top 10 --min-price 1.0 --max-price 10.0
  
  # Analyze configured stocks with recommendations
  python feature_manager.py analyze --list default --top 20
  
  # Save recommendations to Pinecone (all stocks mode)
  python feature_manager.py save-pinecone --mode all --top 10
  
  # Save recommendations to Pinecone (config mode)
  python feature_manager.py save-pinecone --mode config --list default --top 20
  
  # Analyze historical performance of single stock (3-month comparison)
  python feature_manager.py pinecone-historical --ticker AAPL
  
  # Analyze ALL stocks in Pinecone with 3-month comparison
  python feature_manager.py pinecone-historical --min-score 60 --sort-by performance
  
  # Analyze historical for specific date
  python feature_manager.py pinecone-historical --date 2024-11-01 --sort-by news
  
  # 3-month historical analysis (Yahoo Finance data)
  python feature_manager.py historical --min-performance 10
  
  # Send immediate email report
  python feature_manager.py email --email-from you@gmail.com --email-password xxx --email-to recipient@gmail.com
  
  # Schedule daily email at 9:00 AM
  python feature_manager.py schedule --schedule-type daily --schedule-time 09:00 --email-from you@gmail.com --email-password xxx --email-to recipient@gmail.com
        """
    )
    
    subparsers = parser.add_subparsers(dest='feature', help='Feature to run')
    
    # Search ALL stocks feature (NEW)
    search_all_parser = subparsers.add_parser('search-all', help='Search ALL 60+ stocks for top recommendations')
    search_all_parser.add_argument('--top', type=int, default=10, help='Number of top recommendations (default: 10)')
    search_all_parser.add_argument('--min-price', type=float, default=1.0, help='Minimum price (default: 1.0)')
    search_all_parser.add_argument('--max-price', type=float, default=10.0, help='Maximum price (default: 10.0)')
    search_all_parser.add_argument('--no-news', action='store_true', help='Disable news analysis')
    search_all_parser.add_argument('--save', type=str, help='Save results to file (provide filename suffix)')
    
    # Analyze feature (configured stocks)
    analyze_parser = subparsers.add_parser('analyze', help='Analyze configured stocks with recommendations')
    analyze_parser.add_argument('--tickers', type=str, help='Comma-separated ticker symbols')
    analyze_parser.add_argument('--list', type=str, help='Use stock list from config (e.g., tech, penny, finance, ev_clean, custom)')
    analyze_parser.add_argument('--min-price', type=float, help='Minimum price (uses config default if not specified)')
    analyze_parser.add_argument('--max-price', type=float, help='Maximum price (uses config default if not specified)')
    analyze_parser.add_argument('--top', type=int, help='Get top N recommendations with scoring (e.g., --top 20)')
    analyze_parser.add_argument('--no-news', action='store_true', help='Disable news analysis')
    analyze_parser.add_argument('--save', type=str, help='Save results to file (provide filename suffix)')
    
    # Save to Pinecone feature (NEW)
    pinecone_parser = subparsers.add_parser('save-pinecone', help='Save recommendations to Pinecone vector database')
    pinecone_parser.add_argument('--mode', type=str, required=True, choices=['all', 'config'], 
                                 help='Search mode: "all" for 60+ stocks, "config" for configured stocks')
    pinecone_parser.add_argument('--list', type=str, help='Stock list name (for config mode)')
    pinecone_parser.add_argument('--top', type=int, help='Number of top recommendations to save')
    pinecone_parser.add_argument('--min-price', type=float, help='Minimum price')
    pinecone_parser.add_argument('--max-price', type=float, help='Maximum price')
    
    # Pinecone Historical Analysis feature (NEW)
    pinecone_hist_parser = subparsers.add_parser('pinecone-historical', 
                                                   help='Analyze 3-month historical performance of stocks in Pinecone')
    pinecone_hist_parser.add_argument('--ticker', type=str, help='Single ticker to analyze')
    pinecone_hist_parser.add_argument('--date', type=str, help='Date to analyze (YYYY-MM-DD), defaults to today')
    pinecone_hist_parser.add_argument('--min-score', type=int, default=50, 
                                      help='Minimum recommendation score (0-100, default: 50)')
    pinecone_hist_parser.add_argument('--sort-by', type=str, default='performance', 
                                      choices=['performance', 'score', 'news'],
                                      help='Sort results by performance, score, or news sentiment')
    pinecone_hist_parser.add_argument('--display-limit', type=int, default=20,
                                      help='Number of stocks to display (default: 20)')
    pinecone_hist_parser.add_argument('--save', type=str, help='Save results to file (provide filename suffix)')
    
    # Historical analysis feature
    historical_parser = subparsers.add_parser('historical', help='3-month historical analysis')
    historical_parser.add_argument('--tickers', type=str, help='Comma-separated ticker symbols')
    historical_parser.add_argument('--list', type=str, help='Use stock list from config (e.g., default, tech, penny, finance, ev_clean, custom)')
    historical_parser.add_argument('--min-price', type=float, default=1.0, help='Minimum price (default: 1.0)')
    historical_parser.add_argument('--max-price', type=float, default=10.0, help='Maximum price (default: 10.0)')
    historical_parser.add_argument('--min-performance', type=float, default=0.0, help='Minimum 3-month performance percent (default: 0.0)')
    historical_parser.add_argument('--save', type=str, help='Save results to file (provide filename suffix)')
    
    # Email feature
    email_parser = subparsers.add_parser('email', help='Send email report')
    email_parser.add_argument('--tickers', type=str, help='Comma-separated ticker symbols')
    email_parser.add_argument('--min-price', type=float, default=1.0, help='Minimum price (default: 1.0)')
    email_parser.add_argument('--max-price', type=float, default=10.0, help='Maximum price (default: 10.0)')
    email_parser.add_argument('--email-from', type=str, required=True, help='Sender email address')
    email_parser.add_argument('--email-password', type=str, required=True, help='Sender email password (Gmail App Password)')
    email_parser.add_argument('--email-to', type=str, required=True, help='Recipient email address')
    
    # Schedule feature
    schedule_parser = subparsers.add_parser('schedule', help='Schedule automatic email reports')
    schedule_parser.add_argument('--tickers', type=str, help='Comma-separated ticker symbols')
    schedule_parser.add_argument('--min-price', type=float, default=1.0, help='Minimum price (default: 1.0)')
    schedule_parser.add_argument('--max-price', type=float, default=10.0, help='Maximum price (default: 10.0)')
    schedule_parser.add_argument('--schedule-type', type=str, choices=['daily', 'weekly'], required=True, help='Schedule type')
    schedule_parser.add_argument('--schedule-time', type=str, required=True, help='Time in HH:MM format (e.g., 09:00)')
    schedule_parser.add_argument('--schedule-day', type=str, choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'], help='Day of week for weekly schedule')
    schedule_parser.add_argument('--email-from', type=str, required=True, help='Sender email address')
    schedule_parser.add_argument('--email-password', type=str, required=True, help='Sender email password (Gmail App Password)')
    schedule_parser.add_argument('--email-to', type=str, required=True, help='Recipient email address')
    
    args = parser.parse_args()
    
    if not args.feature:
        parser.print_help()
        return
    
    # Run selected feature
    if args.feature == 'search-all':
        asyncio.run(feature_search_all_stocks(args))
    elif args.feature == 'analyze':
        asyncio.run(feature_analyze_stocks(args))
    elif args.feature == 'save-pinecone':
        asyncio.run(feature_save_to_pinecone(args))
    elif args.feature == 'pinecone-historical':
        asyncio.run(feature_pinecone_historical(args))
    elif args.feature == 'historical':
        asyncio.run(feature_historical_analysis(args))
    elif args.feature == 'email':
        asyncio.run(feature_send_email(args))
    elif args.feature == 'schedule':
        feature_schedule_email(args)


if __name__ == "__main__":
    main()
