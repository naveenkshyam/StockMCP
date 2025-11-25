#!/usr/bin/env python
"""
Stock Analysis System - Main Runner
Provides easy access to all features with configuration support
"""
import sys
import os

# Get the Python interpreter path (works for both venv and system Python)
def get_python_path():
    """Get the correct Python interpreter path"""
    return sys.executable

def print_banner():
    """Print welcome banner"""
    print("\n" + "="*70)
    print("STOCK ANALYSIS SYSTEM")
    print("Enhanced with News Integration & Smart Recommendations")
    print("="*70 + "\n")

def print_menu():
    """Print main menu"""
    print("Available Features:")
    print()
    print("1. Search ALL Stocks ($1-$10) - Top 10 Recommendations")
    print("   • Searches 60+ stocks in extended watchlist")
    print("   • Returns top 10 with full analysis & trajectory")
    print("   • Best for comprehensive market scan")
    print()
    print("2. Search Configured Stocks - Top N Recommendations")
    print("   • Uses stock lists from config.yaml (default: 7 stocks)")
    print("   • Customizable: tech, penny, finance, ev_clean, custom")
    print("   • Faster, focused analysis")
    print()
    print("3. Historical Performance (3-Month)")
    print("   • Track stock performance over 3 months")
    print("   • Trend and momentum analysis")
    print("   • Filter by minimum performance %")
    print()
    print("4. Send Email Report")
    print("   • Email analysis to specified recipient")
    print("   • HTML and text formats")
    print("   • Uses config.yaml for email settings")
    print()
    print("5. Schedule Automatic Reports")
    print("   • Daily or weekly automatic emails")
    print("   • Background scheduler")
    print()
    print("6. Configure Settings")
    print("   • Edit config.yaml file")
    print("   • Customize stock lists, email, price filters")
    print()
    print("7. Run Tests")
    print("   • Test all features")
    print("   • Quick smoke test available")
    print()
    print("8. Save Recommendations to Pinecone")
    print("   • Store today's recommendations in vector database")
    print("   • Compare with tomorrow's recommendations")
    print("   • Track recommendation changes over time")
    print()
    print("0. Exit")
    print()

def run_analyze_all_stocks():
    """Run comprehensive search across ALL 60+ stocks"""
    print("\n" + "-"*70)
    print("SEARCH ALL STOCKS ($1-$10) - TOP 10 RECOMMENDATIONS")
    print("-"*70 + "\n")
    
    print("This will search 60+ stocks in the extended watchlist")
    print("Price range: $1.00 - $10.00")
    print()
    
    top_n = input("How many top recommendations (default 10): ").strip() or "10"
    min_price = input("Minimum price (default $1.00): ").strip() or "1.00"
    max_price = input("Maximum price (default $10.00): ").strip() or "10.00"
    
    cmd = f"{get_python_path()} features/feature_manager.py search-all --top {top_n} --min-price {min_price} --max-price {max_price}"
    
    # Ask about news
    use_news = input("\nInclude news analysis? (Y/n): ").strip().lower()
    if use_news == 'n':
        cmd += " --no-news"
    
    # Ask about saving
    save = input("Save results to file? (y/N): ").strip().lower()
    if save == 'y':
        filename = input("Enter filename suffix (e.g., 'all_stocks_report'): ").strip() or "all_stocks"
        cmd += f" --save {filename}"
    
    print(f"\nRunning: {cmd}\n")
    os.system(cmd)

def run_analyze_configured():
    """Run analysis on configured stocks from config.yaml"""
    print("\n" + "-"*70)
    print("SEARCH CONFIGURED STOCKS - TOP N RECOMMENDATIONS")
    print("-"*70 + "\n")
    
    print("Available lists: default, tech, penny, finance, ev_clean, custom")
    list_name = input("Enter list name (default): ").strip() or "default"
    top_n = input("How many top recommendations (default 20): ").strip() or "20"
    
    cmd = f"{get_python_path()} features/feature_manager.py analyze --list {list_name} --top {top_n}"
    
    # Ask about news
    use_news = input("\nInclude news analysis? (Y/n): ").strip().lower()
    if use_news == 'n':
        cmd += " --no-news"
    
    # Ask about saving
    save = input("Save results to file? (y/N): ").strip().lower()
    if save == 'y':
        filename = input("Enter filename suffix (e.g., 'report1'): ").strip() or "results"
        cmd += f" --save {filename}"
    
    print(f"\nRunning: {cmd}\n")
    os.system(cmd)

def run_historical():
    """Run historical analysis"""
    print("\n" + "-"*70)
    print("3-MONTH HISTORICAL ANALYSIS")
    print("-"*70 + "\n")
    
    print("Options:")
    print("1. Analyze specific tickers")
    print("2. Use predefined list from config")
    
    choice = input("\nSelect option (1-2): ").strip()
    
    if choice == "1":
        tickers = input("Enter tickers (comma-separated): ").strip()
        cmd = f"{get_python_path()} features/feature_manager.py historical --tickers {tickers}"
    elif choice == "2":
        list_name = input("Enter list name (default, tech, penny, etc.): ").strip() or "default"
        cmd = f"{get_python_path()} features/feature_manager.py historical --list {list_name}"
    else:
        print("Invalid option")
        return
    
    min_perf = input("\nMinimum 3-month performance % (default 0): ").strip()
    if min_perf:
        cmd += f" --min-performance {min_perf}"
    
    save = input("Save results? (y/N): ").strip().lower()
    if save == 'y':
        filename = input("Enter filename suffix: ").strip() or "historical"
        cmd += f" --save {filename}"
    
    print(f"\nRunning: {cmd}\n")
    os.system(cmd)

def run_email():
    """Send email report"""
    print("\n" + "-"*70)
    print("SEND EMAIL REPORT")
    print("-"*70 + "\n")
    
    print("Email credentials can be:")
    print("1. Read from config.yaml (recommended)")
    print("2. Entered manually")
    print()
    
    use_config = input("Use config.yaml for email settings? (Y/n): ").strip().lower() != 'n'
    
    if use_config:
        cmd = f"{get_python_path()} features/feature_manager.py email"
        from config_manager import get_config
        config = get_config()
        email_from = config.get_email_from()
        email_to = config.get_email_to()
        
        if not email_from or not email_to:
            print("\n⚠ Email settings not found in config.yaml")
            print("Please edit config.yaml or enter manually\n")
            return
        
        print(f"\n✓ Using: {email_from} → {email_to}")
    else:
        email_from = input("Your Gmail: ").strip()
        email_password = input("Gmail App Password: ").strip()
        email_to = input("Recipient email: ").strip()
        
        cmd = f"{get_python_path()} features/feature_manager.py email --email-from {email_from} --email-password {email_password} --email-to {email_to}"
    
    list_name = input("\nStock list (default, tech, penny, etc.): ").strip() or "default"
    cmd += f" --list {list_name}"
    
    print(f"\nRunning: {cmd}\n")
    os.system(cmd)

def run_schedule():
    """Schedule automatic reports"""
    print("\n" + "-"*70)
    print("SCHEDULE AUTOMATIC REPORTS")
    print("-"*70 + "\n")
    
    print("Schedule type:")
    print("1. Daily")
    print("2. Weekly")
    
    choice = input("\nSelect (1-2): ").strip()
    
    if choice == "1":
        time_str = input("Time (HH:MM, e.g., 09:00): ").strip()
        cmd = f"{get_python_path()} features/feature_manager.py schedule --schedule-type daily --schedule-time {time_str}"
    elif choice == "2":
        day = input("Day (monday-sunday): ").strip().lower()
        time_str = input("Time (HH:MM): ").strip()
        cmd = f"{get_python_path()} features/feature_manager.py schedule --schedule-type weekly --schedule-day {day} --schedule-time {time_str}"
    else:
        print("Invalid option")
        return
    
    # Email settings
    from config_manager import get_config
    config = get_config()
    
    if config.get_email_from() and config.get_email_to():
        print(f"\n✓ Using email from config: {config.get_email_from()} → {config.get_email_to()}")
        # Config will be used by scheduler
    else:
        print("\n⚠ Email settings required in config.yaml")
        print("Please edit config.yaml first")
        return
    
    list_name = input("\nStock list (default, tech, penny, etc.): ").strip() or "default"
    cmd += f" --list {list_name}"
    
    print(f"\n⚠ Scheduler will run in foreground. Use Ctrl+C to stop.")
    print(f"Running: {cmd}\n")
    
    input("Press Enter to start scheduler...")
    os.system(cmd)

def edit_config():
    """Edit configuration file"""
    print("\n" + "-"*70)
    print("EDIT CONFIGURATION")
    print("-"*70 + "\n")
    
    config_path = "config.yaml"
    
    if not os.path.exists(config_path):
        print(f"⚠ {config_path} not found!")
        return
    
    editor = os.environ.get('EDITOR', 'nano')
    print(f"Opening {config_path} with {editor}...\n")
    print("Things you can configure:")
    print("  • Email settings (Gmail credentials)")
    print("  • Stock lists (default, tech, penny, finance, ev_clean, custom)")
    print("  • Price filters (min/max price)")
    print("  • News settings (enable/disable, sentiment weight)")
    print("  • Scheduler settings")
    print()
    
    input("Press Enter to open editor...")
    os.system(f"{editor} {config_path}")

def run_save_to_pinecone():
    """Save stock recommendations to Pinecone vector database"""
    print("\n" + "-"*70)
    print("SAVE RECOMMENDATIONS TO PINECONE")
    print("-"*70 + "\n")
    
    print("This will save today's recommendations to Pinecone vector database")
    print("allowing you to compare with future recommendations.")
    print()
    
    print("Options:")
    print("1. Save ALL stocks search ($1-$10, top 10)")
    print("2. Save configured stocks search (from config.yaml)")
    
    choice = input("\nSelect option (1-2): ").strip()
    
    if choice == "1":
        top_n = input("How many top recommendations to save (default 10): ").strip() or "10"
        min_price = input("Minimum price (default $1.00): ").strip() or "1.00"
        max_price = input("Maximum price (default $10.00): ").strip() or "10.00"
        
        cmd = f"{get_python_path()} features/feature_manager.py save-pinecone --mode all --top {top_n} --min-price {min_price} --max-price {max_price}"
    
    elif choice == "2":
        print("\nAvailable lists: default, tech, penny, finance, ev_clean, custom")
        list_name = input("Enter list name (default): ").strip() or "default"
        top_n = input("How many top recommendations to save (default 20): ").strip() or "20"
        
        cmd = f"{get_python_path()} features/feature_manager.py save-pinecone --mode config --list {list_name} --top {top_n}"
    
    else:
        print("Invalid option")
        return
    
    print(f"\nRunning: {cmd}\n")
    os.system(cmd)

def run_tests():
    """Run test suite"""
    print("\n" + "-"*70)
    print("TEST SUITE")
    print("-"*70 + "\n")
    
    print("Options:")
    print("1. Quick smoke test (fast)")
    print("2. Full test suite (comprehensive)")
    
    choice = input("\nSelect (1-2): ").strip()
    
    if choice == "1":
        os.system(f"{get_python_path()} test_all_features.py --quick")
    elif choice == "2":
        os.system(f"{get_python_path()} test_all_features.py")
    else:
        print("Invalid option")

def main():
    """Main entry point"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    while True:
        print_banner()
        print_menu()
        
        choice = input("Select feature (0-8): ").strip()
        
        if choice == "0":
            print("\nGoodbye!\n")
            break
        elif choice == "1":
            run_analyze_all_stocks()
        elif choice == "2":
            run_analyze_configured()
        elif choice == "3":
            run_historical()
        elif choice == "4":
            run_email()
        elif choice == "5":
            run_schedule()
        elif choice == "6":
            edit_config()
        elif choice == "7":
            run_tests()
        elif choice == "8":
            run_save_to_pinecone()
        else:
            print("\n⚠ Invalid choice. Please select 0-8.\n")
            input("Press Enter to continue...")
        
        if choice != "0":
            print("\n" + "="*70)
            input("\nPress Enter to return to main menu...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!\n")
        sys.exit(0)
