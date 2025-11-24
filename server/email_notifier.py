#!/usr/bin/env python3
"""
Email Notification Module for Stock Analysis
Handles email generation and sending for daily stock reports
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional, List, Dict
import asyncio


class StockEmailNotifier:
    """Handle email notifications for stock analysis"""
    
    def __init__(self, smtp_server: str = "smtp.gmail.com", smtp_port: int = 587):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
    
    def generate_html_email(
        self, 
        stocks: List[Dict], 
        max_price: float,
        include_recommendations: bool = True,
        top_movers_data: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate HTML email content for stock analysis
        
        Args:
            stocks: List of stock data dictionaries
            max_price: Maximum price filter used
            include_recommendations: Include recommendation details
            top_movers_data: Optional list of stocks with recommendations
            
        Returns:
            HTML formatted string
        """
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    line-height: 1.6; 
                    color: #333; 
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{ 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; 
                    padding: 30px; 
                    text-align: center; 
                    border-radius: 10px;
                    margin-bottom: 30px;
                }}
                .summary {{ 
                    background: #f4f4f4; 
                    padding: 20px; 
                    margin: 20px 0; 
                    border-radius: 8px;
                    border-left: 5px solid #667eea;
                }}
                .stock-card {{ 
                    border: 1px solid #ddd; 
                    margin: 15px 0; 
                    padding: 20px; 
                    border-radius: 8px;
                    background: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .positive {{ color: #10b981; font-weight: bold; }}
                .negative {{ color: #ef4444; font-weight: bold; }}
                .neutral {{ color: #6b7280; }}
                table {{ 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 20px 0;
                    background: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                th {{ 
                    background: #667eea; 
                    color: white; 
                    padding: 12px; 
                    text-align: left;
                    font-weight: 600;
                }}
                td {{ 
                    padding: 12px; 
                    border-bottom: 1px solid #e5e7eb;
                }}
                tr:hover {{ background: #f9fafb; }}
                .footer {{ 
                    text-align: center; 
                    color: #666; 
                    font-size: 12px; 
                    margin-top: 40px; 
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                }}
                .recommendation {{ 
                    background: #fef3c7; 
                    padding: 15px; 
                    border-left: 4px solid #f59e0b; 
                    margin: 10px 0;
                    border-radius: 4px;
                }}
                .badge {{
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                }}
                .badge-high {{ background: #fee2e2; color: #991b1b; }}
                .badge-medium {{ background: #fef3c7; color: #92400e; }}
                .badge-low {{ background: #d1fae5; color: #065f46; }}
                h2 {{ color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                h3 {{ color: #764ba2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Daily Stock Analysis Report</h1>
                <p style="font-size: 18px;">Stocks Under ${max_price}</p>
                <p style="font-size: 14px; opacity: 0.9;">{datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}</p>
            </div>
            
            <div class="summary">
                <h2 style="margin-top: 0; color: #667eea; border: none;">📈 Executive Summary</h2>
                <ul style="margin: 10px 0;">
                    <li><strong>Total Stocks Analyzed:</strong> {len(stocks)}</li>
                    <li><strong>Price Filter:</strong> Under ${max_price}</li>
                    <li><strong>Report Generated:</strong> {datetime.now().strftime('%Y-%m-%d %I:%M %p')}</li>
                    <li><strong>Data Source:</strong> Yahoo Finance (15-20 min delay)</li>
                </ul>
            </div>
            
            <h2>🎯 All Stocks Under ${max_price}</h2>
            <table>
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Ticker</th>
                        <th>Company</th>
                        <th>Current Price</th>
                        <th>Daily Change</th>
                        <th>Change %</th>
                        <th>Volume</th>
                        <th>Sector</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add stock rows
        for i, stock in enumerate(stocks, 1):
            change_class = "positive" if stock['day_change'] >= 0 else "negative"
            arrow = "↑" if stock['day_change'] >= 0 else "↓"
            
            html_content += f"""
                    <tr>
                        <td>{i}</td>
                        <td><strong>{stock['ticker']}</strong></td>
                        <td>{stock['company']}</td>
                        <td style="font-weight: 600;">${stock['current_price']}</td>
                        <td class="{change_class}">{arrow} ${abs(stock['day_change']):.2f}</td>
                        <td class="{change_class}">{stock['day_change_percent']:+.2f}%</td>
                        <td>{stock['volume']:,}</td>
                        <td style="font-size: 12px;">{stock['sector']}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
        """
        
        # Add detailed analysis for top movers if provided
        if include_recommendations and top_movers_data:
            html_content += """
            <h2>🔍 Detailed Analysis - Top Movers</h2>
            <p>In-depth analysis of the most significant price movements today:</p>
            """
            
            for stock_data in top_movers_data:
                stock = stock_data['stock']
                rec = stock_data.get('recommendation', {})
                
                change_emoji = "📈" if stock['day_change'] >= 0 else "📉"
                
                html_content += f"""
                <div class="stock-card">
                    <h3>{change_emoji} {stock['ticker']} - {stock['company']}</h3>
                    <p style="font-size: 16px;">
                        <strong>Current Price:</strong> ${stock['current_price']} 
                        <span class="{'positive' if stock['day_change'] >= 0 else 'negative'}">
                            ({stock['day_change_percent']:+.2f}%)
                        </span>
                    </p>
                    <p><strong>Sector:</strong> {stock['sector']} | <strong>Industry:</strong> {stock['industry']}</p>
                    <p><strong>Volume:</strong> {stock['volume']:,}</p>
                """
                
                if rec and "error" not in rec:
                    risk_badge_class = {
                        'High': 'badge-high',
                        'Medium': 'badge-medium',
                        'Low': 'badge-low'
                    }.get(rec.get('risk_level', 'Medium'), 'badge-medium')
                    
                    html_content += f"""
                    <div class="recommendation">
                        <p style="margin-top: 0;">
                            <strong>💡 Investment Recommendation:</strong> {rec.get('recommendation', 'N/A')} 
                            <span class="badge {risk_badge_class}">{rec.get('risk_level', 'N/A')} Risk</span>
                        </p>
                        <p><strong>Entry Points:</strong></p>
                        <ul style="margin: 5px 0;">
                            <li>Conservative: {rec.get('entry_points', {}).get('conservative', 'N/A')}</li>
                            <li>Moderate: {rec.get('entry_points', {}).get('moderate', 'N/A')}</li>
                            <li>Aggressive: {rec.get('entry_points', {}).get('aggressive', 'N/A')}</li>
                        </ul>
                        <p><strong>Suggested Stop Loss:</strong> {rec.get('stop_loss', 'N/A')}</p>
                        <p><strong>Key Levels:</strong></p>
                        <ul style="margin: 5px 0;">
                            <li>Support: {rec.get('key_levels', {}).get('support', 'N/A')}</li>
                            <li>Resistance: {rec.get('key_levels', {}).get('resistance', 'N/A')}</li>
                        </ul>
                    </div>
                    """
                
                html_content += "</div>"
        
        html_content += """
            <div class="footer">
                <p><strong>⚠️ Important Disclaimer:</strong></p>
                <p>This analysis is provided for informational purposes only and should not be considered 
                as financial advice. Stock prices are subject to market volatility and past performance 
                does not guarantee future results. Always conduct your own research and consult with a 
                qualified financial advisor before making investment decisions.</p>
                <p style="margin-top: 15px;">
                    <strong>Generated by Enhanced Stock MCP Server</strong><br>
                    Data Source: Yahoo Finance | Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
                </p>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def generate_text_email(self, stocks: List[Dict], max_price: float) -> str:
        """
        Generate plain text email content for stock analysis
        
        Args:
            stocks: List of stock data dictionaries
            max_price: Maximum price filter used
            
        Returns:
            Plain text formatted string
        """
        text_content = f"""
{'='*80}
DAILY STOCK ANALYSIS REPORT
Stocks Under ${max_price} | {datetime.now().strftime('%B %d, %Y')}
{'='*80}

SUMMARY:
--------
- Total Stocks Analyzed: {len(stocks)}
- Price Filter: Under ${max_price}
- Report Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
- Data Source: Yahoo Finance

STOCKS UNDER ${max_price}:
{'='*80}
{'#':<4} {'Ticker':<8} {'Company':<30} {'Price':<10} {'Change':<15} {'Volume':<15}
{'-'*80}
"""
        
        for i, stock in enumerate(stocks, 1):
            arrow = "↑" if stock['day_change'] >= 0 else "↓"
            text_content += f"{i:<4} {stock['ticker']:<8} {stock['company'][:29]:<30} ${stock['current_price']:<9.2f} {arrow}${abs(stock['day_change']):.2f} ({stock['day_change_percent']:+.2f}%)  {stock['volume']:<14,}\n"
        
        text_content += f"""
{'='*80}

DISCLAIMER:
-----------
This analysis is for informational purposes only. Always do your own research 
before making investment decisions. Stock prices are subject to market volatility.

Generated by Enhanced Stock MCP Server
Data Source: Yahoo Finance | {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
{'='*80}
"""
        
        return text_content
    
    def send_email(
        self,
        recipient_email: str,
        subject: str,
        html_content: str,
        text_content: str,
        sender_email: str,
        sender_password: str
    ) -> Dict:
        """
        Send email via SMTP
        
        Args:
            recipient_email: Recipient's email address
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            sender_email: Sender's email address
            sender_password: Sender's email password (app password for Gmail)
            
        Returns:
            Dictionary with status and message
        """
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Date'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
            
            # Attach both text and HTML parts
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            
            return {
                "status": "success",
                "message": f"Email sent successfully to {recipient_email}",
                "sent_at": datetime.now().isoformat(),
                "subject": subject
            }
        
        except smtplib.SMTPAuthenticationError:
            return {
                "status": "error",
                "error": "Authentication failed",
                "message": "Invalid email or password. For Gmail, use App Password instead of regular password.",
                "help": "Visit: https://myaccount.google.com/apppasswords"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to send email. Check your credentials and network connection."
            }
    
    def save_to_file(self, html_content: str, filename: Optional[str] = None) -> Dict:
        """
        Save HTML email content to a file
        
        Args:
            html_content: HTML content to save
            filename: Output filename (auto-generated if not provided)
            
        Returns:
            Dictionary with status and filename
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"stock_analysis_{timestamp}.html"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return {
                "status": "success",
                "message": f"Analysis saved to {filename}",
                "filename": filename,
                "saved_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to save file"
            }


# Convenience functions for direct use
def create_and_send_email(
    stocks: List[Dict],
    max_price: float,
    recipient_email: str,
    sender_email: str,
    sender_password: str,
    include_recommendations: bool = True,
    top_movers_data: Optional[List[Dict]] = None
) -> Dict:
    """
    Create and send stock analysis email
    
    Args:
        stocks: List of stock data dictionaries
        max_price: Maximum price filter
        recipient_email: Recipient's email
        sender_email: Sender's email
        sender_password: Sender's password (app password for Gmail)
        include_recommendations: Include detailed recommendations
        top_movers_data: Optional list of stocks with recommendations
        
    Returns:
        Dictionary with send status
    """
    notifier = StockEmailNotifier()
    
    subject = f"Daily Stock Analysis - Stocks Under ${max_price} ({datetime.now().strftime('%Y-%m-%d')})"
    html_content = notifier.generate_html_email(stocks, max_price, include_recommendations, top_movers_data)
    text_content = notifier.generate_text_email(stocks, max_price)
    
    return notifier.send_email(
        recipient_email=recipient_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
        sender_email=sender_email,
        sender_password=sender_password
    )


def create_and_save_email(
    stocks: List[Dict],
    max_price: float,
    filename: Optional[str] = None,
    include_recommendations: bool = True,
    top_movers_data: Optional[List[Dict]] = None
) -> Dict:
    """
    Create and save stock analysis to HTML file
    
    Args:
        stocks: List of stock data dictionaries
        max_price: Maximum price filter
        filename: Output filename (auto-generated if not provided)
        include_recommendations: Include detailed recommendations
        top_movers_data: Optional list of stocks with recommendations
        
    Returns:
        Dictionary with save status
    """
    notifier = StockEmailNotifier()
    
    html_content = notifier.generate_html_email(stocks, max_price, include_recommendations, top_movers_data)
    
    return notifier.save_to_file(html_content, filename)


if __name__ == "__main__":
    # Example usage
    print("Stock Email Notifier Module")
    print("="*80)
    print("\nThis module provides email notification functionality for stock analysis.")
    print("\nExample Usage:")
    print("""
from email_notifier import StockEmailNotifier, create_and_send_email

# Sample stock data
stocks = [
    {
        'ticker': 'AAPL',
        'company': 'Apple Inc.',
        'current_price': 175.50,
        'day_change': 2.30,
        'day_change_percent': 1.33,
        'volume': 50000000,
        'sector': 'Technology'
    }
]

# Send email
result = create_and_send_email(
    stocks=stocks,
    max_price=10.0,
    recipient_email='user@example.com',
    sender_email='sender@gmail.com',
    sender_password='your_app_password'
)

print(result)
    """)
