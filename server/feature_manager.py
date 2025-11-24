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


# Default watchlist (can be customized)
DEFAULT_WATCHLIST = [
    "AAPL", "MSFT", "F", "NOK", "AMC", "ABEV", "PLUG", "NIO", "SOFI", "RIVN",
    "LCID", "BAC", "WFC", "INTC", "AMD", "TSLA", "NVDA", "PYPL", "SQ", "SNAP",
    "UBER", "LYFT", "AAL", "DAL", "CCL", "NCLH", "MGM", "WYNN", "GPRO", "PTON",
    "BBBY", "BBY", "TGT", "WMT", "COST", "HD", "LOW", "DIS", "NFLX", "PARA",
    "ABTS", "GSAT", "TLRY", "CGC", "SNDL", "ACB", "CRON", "OGI", "KERN", "HIMS",
    "HYZN", "EVGO", "BLNK", "CHPT", "GOEV", "WKHS", "XL", "ARVL", "ENVX", "QS"
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


async def feature_historical_analysis(args):
    """Feature: 3-Month Historical Analysis"""
    print(f"\n{'='*60}")
    print("Feature: 3-Month Historical Performance Analysis")
    print(f"{'='*60}\n")
    
    tickers = args.tickers.split(',') if args.tickers else DEFAULT_WATCHLIST
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
  # Analyze stocks with recommendations
  python feature_manager.py analyze --tickers AAPL,MSFT,TSLA
  
  # 3-month historical analysis
  python feature_manager.py historical --min-performance 10
  
  # Send immediate email report
  python feature_manager.py email --email-from you@gmail.com --email-password xxx --email-to recipient@gmail.com
  
  # Schedule daily email at 9:00 AM
  python feature_manager.py schedule --schedule-type daily --schedule-time 09:00 --email-from you@gmail.com --email-password xxx --email-to recipient@gmail.com
        """
    )
    
    subparsers = parser.add_subparsers(dest='feature', help='Feature to run')
    
    # Analyze feature
    analyze_parser = subparsers.add_parser('analyze', help='Analyze stocks with recommendations')
    analyze_parser.add_argument('--tickers', type=str, help='Comma-separated ticker symbols')
    analyze_parser.add_argument('--list', type=str, help='Use stock list from config (e.g., tech, penny, finance, ev_clean, custom)')
    analyze_parser.add_argument('--min-price', type=float, help='Minimum price (uses config default if not specified)')
    analyze_parser.add_argument('--max-price', type=float, help='Maximum price (uses config default if not specified)')
    analyze_parser.add_argument('--top', type=int, help='Get top N recommendations with scoring (e.g., --top 20)')
    analyze_parser.add_argument('--no-news', action='store_true', help='Disable news analysis')
    analyze_parser.add_argument('--save', type=str, help='Save results to file (provide filename suffix)')
    
    # Historical analysis feature
    historical_parser = subparsers.add_parser('historical', help='3-month historical analysis')
    historical_parser.add_argument('--tickers', type=str, help='Comma-separated ticker symbols')
    historical_parser.add_argument('--min-price', type=float, default=1.0, help='Minimum price (default: 1.0)')
    historical_parser.add_argument('--max-price', type=float, default=10.0, help='Maximum price (default: 10.0)')
    historical_parser.add_argument('--min-performance', type=float, default=0.0, help='Minimum 3-month performance % (default: 0.0)')
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
    if args.feature == 'analyze':
        asyncio.run(feature_analyze_stocks(args))
    elif args.feature == 'historical':
        asyncio.run(feature_historical_analysis(args))
    elif args.feature == 'email':
        asyncio.run(feature_send_email(args))
    elif args.feature == 'schedule':
        feature_schedule_email(args)


if __name__ == "__main__":
    main()
