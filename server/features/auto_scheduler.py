"""
Feature: Auto Scheduler for Stock Reports
Automatically sends daily/weekly stock analysis emails
"""
import asyncio
import smtplib
from datetime import datetime, time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time as time_module


class StockScheduler:
    """Automated scheduler for stock reports"""
    
    def __init__(
        self,
        email_from: str,
        email_password: str,
        email_to: str,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587
    ):
        self.email_from = email_from
        self.email_password = email_password
        self.email_to = email_to
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.is_running = False
    
    async def send_scheduled_report(
        self,
        watchlist: list,
        min_price: float = 1.0,
        max_price: float = 10.0
    ):
        """Send scheduled stock analysis report"""
        from features.stock_analyzer import analyze_multiple_stocks
        
        try:
            # Analyze stocks
            stocks = await analyze_multiple_stocks(watchlist, min_price, max_price)
            
            # Generate email
            html_content = self._generate_html_report(stocks)
            text_content = self._generate_text_report(stocks)
            
            # Send email
            await self._send_email(
                subject=f"Daily Stock Analysis - {datetime.now().strftime('%Y-%m-%d')}",
                html_content=html_content,
                text_content=text_content
            )
            
            print(f"[{datetime.now()}] Successfully sent scheduled report with {len(stocks)} stocks")
            
        except Exception as e:
            print(f"[{datetime.now()}] Error sending scheduled report: {e}")
    
    async def _send_email(self, subject: str, html_content: str, text_content: str):
        """Send email notification"""
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = self.email_from
        msg['To'] = self.email_to
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.email_from, self.email_password)
            server.sendmail(self.email_from, self.email_to, msg.as_string())
    
    def _generate_html_report(self, stocks: list) -> str:
        """Generate HTML email report"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; }
                h1 { color: #2c3e50; }
                table { border-collapse: collapse; width: 100%; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #3498db; color: white; }
                .buy { color: green; font-weight: bold; }
                .sell { color: red; font-weight: bold; }
            </style>
        </head>
        <body>
            <h1>Daily Stock Analysis Report</h1>
            <p>Generated: {date}</p>
            <p>Analyzed {count} stocks in range ${min_price}-${max_price}</p>
            <table>
                <tr>
                    <th>Ticker</th>
                    <th>Price</th>
                    <th>Change %</th>
                    <th>Recommendation</th>
                    <th>Risk</th>
                </tr>
        """.format(
            date=datetime.now().strftime('%Y-%m-%d %H:%M'),
            count=len(stocks),
            min_price=1.0,
            max_price=10.0
        )
        
        for stock in stocks:
            rec_class = "buy" if "Buy" in stock.get('recommendation', '') else ""
            html += f"""
                <tr>
                    <td>{stock.get('ticker', 'N/A')}</td>
                    <td>${stock.get('current_price', 0):.2f}</td>
                    <td>{stock.get('change_percent', 0):+.2f}%</td>
                    <td class="{rec_class}">{stock.get('recommendation', 'N/A')}</td>
                    <td>{stock.get('risk_level', 'N/A')}</td>
                </tr>
            """
        
        html += """
            </table>
        </body>
        </html>
        """
        return html
    
    def _generate_text_report(self, stocks: list) -> str:
        """Generate plain text email report"""
        report = f"Daily Stock Analysis Report\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += f"Analyzed {len(stocks)} stocks\n\n"
        
        for stock in stocks:
            report += f"Ticker: {stock.get('ticker', 'N/A')}\n"
            report += f"  Price: ${stock.get('current_price', 0):.2f}\n"
            report += f"  Change: {stock.get('change_percent', 0):+.2f}%\n"
            report += f"  Recommendation: {stock.get('recommendation', 'N/A')}\n"
            report += f"  Risk: {stock.get('risk_level', 'N/A')}\n\n"
        
        return report
    
    def schedule_daily(
        self,
        hour: int,
        minute: int,
        watchlist: list,
        min_price: float = 1.0,
        max_price: float = 10.0
    ):
        """
        Schedule daily reports at specific time
        
        Args:
            hour: Hour (0-23)
            minute: Minute (0-59)
            watchlist: List of tickers to analyze
            min_price: Minimum price filter
            max_price: Maximum price filter
        """
        schedule_time = f"{hour:02d}:{minute:02d}"
        
        schedule.every().day.at(schedule_time).do(
            lambda: asyncio.run(
                self.send_scheduled_report(watchlist, min_price, max_price)
            )
        )
        
        print(f"Scheduled daily report at {schedule_time}")
    
    def schedule_weekly(
        self,
        day: str,
        hour: int,
        minute: int,
        watchlist: list,
        min_price: float = 1.0,
        max_price: float = 10.0
    ):
        """
        Schedule weekly reports on specific day
        
        Args:
            day: Day of week (monday, tuesday, etc.)
            hour: Hour (0-23)
            minute: Minute (0-59)
            watchlist: List of tickers to analyze
            min_price: Minimum price filter
            max_price: Maximum price filter
        """
        schedule_time = f"{hour:02d}:{minute:02d}"
        
        getattr(schedule.every(), day.lower()).at(schedule_time).do(
            lambda: asyncio.run(
                self.send_scheduled_report(watchlist, min_price, max_price)
            )
        )
        
        print(f"Scheduled weekly report on {day} at {schedule_time}")
    
    def run(self):
        """Start the scheduler (blocking call)"""
        self.is_running = True
        print("Scheduler started. Press Ctrl+C to stop.")
        
        try:
            while self.is_running:
                schedule.run_pending()
                time_module.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nScheduler stopped by user")
            self.is_running = False


# Convenience functions
def create_scheduler(
    email_from: str,
    email_password: str,
    email_to: str
) -> StockScheduler:
    """Create a new scheduler instance"""
    return StockScheduler(email_from, email_password, email_to)


async def send_immediate_report(
    email_from: str,
    email_password: str,
    email_to: str,
    watchlist: list,
    min_price: float = 1.0,
    max_price: float = 10.0
):
    """Send an immediate report without scheduling"""
    scheduler = StockScheduler(email_from, email_password, email_to)
    await scheduler.send_scheduled_report(watchlist, min_price, max_price)
