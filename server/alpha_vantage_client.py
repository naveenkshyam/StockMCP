"""
Alpha Vantage API Client
Shared module for accessing Alpha Vantage stock data and technical indicators
"""
import requests
import os

# Alpha Vantage API configuration
ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
ALPHA_VANTAGE_BASE_URL = 'https://www.alphavantage.co/query'


def fetch_alpha_vantage_quote(ticker: str) -> dict:
    """Fetch real-time quote data from Alpha Vantage API."""
    try:
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': ticker,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if 'Global Quote' in data and data['Global Quote']:
            quote = data['Global Quote']
            return {
                'symbol': quote.get('01. symbol'),
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                'volume': int(quote.get('06. volume', 0)),
                'latest_trading_day': quote.get('07. latest trading day'),
                'previous_close': float(quote.get('08. previous close', 0)),
                'source': 'Alpha Vantage'
            }
        else:
            return {'error': 'No data returned from Alpha Vantage', 'details': data}
    except Exception as e:
        return {'error': str(e)}


def fetch_alpha_vantage_overview(ticker: str) -> dict:
    """Fetch company overview data from Alpha Vantage API."""
    try:
        params = {
            'function': 'OVERVIEW',
            'symbol': ticker,
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if data and 'Symbol' in data:
            return {
                'symbol': data.get('Symbol'),
                'name': data.get('Name'),
                'sector': data.get('Sector'),
                'industry': data.get('Industry'),
                'market_cap': int(data.get('MarketCapitalization', 0)),
                'pe_ratio': float(data.get('PERatio', 0)) if data.get('PERatio') != 'None' else None,
                'dividend_yield': float(data.get('DividendYield', 0)) if data.get('DividendYield') != 'None' else None,
                '52_week_high': float(data.get('52WeekHigh', 0)),
                '52_week_low': float(data.get('52WeekLow', 0)),
                'analyst_rating': data.get('AnalystTargetPrice'),
                'source': 'Alpha Vantage'
            }
        else:
            return {'error': 'No overview data available', 'details': data}
    except Exception as e:
        return {'error': str(e)}


def fetch_alpha_vantage_technical(ticker: str) -> dict:
    """Fetch technical indicators (RSI) from Alpha Vantage API."""
    try:
        params = {
            'function': 'RSI',
            'symbol': ticker,
            'interval': 'daily',
            'time_period': 14,
            'series_type': 'close',
            'apikey': ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(ALPHA_VANTAGE_BASE_URL, params=params, timeout=10)
        data = response.json()
        
        rsi_value = None
        if 'Technical Analysis: RSI' in data:
            latest_date = list(data['Technical Analysis: RSI'].keys())[0]
            rsi_value = float(data['Technical Analysis: RSI'][latest_date]['RSI'])
        
        return {
            'rsi': rsi_value,
            'rsi_signal': 'Oversold' if rsi_value and rsi_value < 30 else 'Overbought' if rsi_value and rsi_value > 70 else 'Neutral',
            'source': 'Alpha Vantage'
        }
    except Exception as e:
        return {'error': str(e), 'rsi': None, 'rsi_signal': 'Unavailable'}
