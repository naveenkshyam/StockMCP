"""
Configuration Manager
Loads and provides access to configuration settings
"""
import yaml
import os
from pathlib import Path
from typing import Dict, List, Any


class ConfigManager:
    """Manages configuration settings from config.yaml"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
        
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print(f"Warning: Config file not found at {self.config_path}")
            return self._get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Return default configuration if file not found"""
        return {
            'email': {
                'from': '',
                'password': '',
                'to': '',
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587
            },
            'stock_lists': {
                'default': ['AAPL', 'MSFT', 'TSLA']
            },
            'analysis': {
                'price_filter': {
                    'min_price': 1.0,
                    'max_price': 10.0
                },
                'news': {
                    'enabled': True,
                    'max_articles': 5,
                    'sentiment_weight': 0.3
                }
            }
        }
    
    # Email settings
    def get_email_from(self) -> str:
        return self.config.get('email', {}).get('from', '')
    
    def get_email_password(self) -> str:
        return self.config.get('email', {}).get('password', '')
    
    def get_email_to(self) -> str:
        return self.config.get('email', {}).get('to', '')
    
    def get_smtp_server(self) -> str:
        return self.config.get('email', {}).get('smtp_server', 'smtp.gmail.com')
    
    def get_smtp_port(self) -> int:
        return self.config.get('email', {}).get('smtp_port', 587)
    
    # Stock lists
    def get_stock_list(self, list_name: str = 'default') -> List[str]:
        """Get a specific stock list by name"""
        return self.config.get('stock_lists', {}).get(list_name, [])
    
    def get_all_stock_lists(self) -> Dict[str, List[str]]:
        """Get all available stock lists"""
        return self.config.get('stock_lists', {})
    
    def list_available_watchlists(self) -> List[str]:
        """Get names of all available watchlists"""
        return list(self.config.get('stock_lists', {}).keys())
    
    # Analysis settings
    def get_min_price(self) -> float:
        return self.config.get('analysis', {}).get('price_filter', {}).get('min_price', 1.0)
    
    def get_max_price(self) -> float:
        return self.config.get('analysis', {}).get('price_filter', {}).get('max_price', 10.0)
    
    def get_historical_period(self) -> str:
        return self.config.get('analysis', {}).get('historical', {}).get('period', '3mo')
    
    def get_min_performance(self) -> float:
        return self.config.get('analysis', {}).get('historical', {}).get('min_performance', 0.0)
    
    # News settings
    def is_news_enabled(self) -> bool:
        return self.config.get('analysis', {}).get('news', {}).get('enabled', True)
    
    def get_max_news_articles(self) -> int:
        return self.config.get('analysis', {}).get('news', {}).get('max_articles', 5)
    
    def get_sentiment_weight(self) -> float:
        return self.config.get('analysis', {}).get('news', {}).get('sentiment_weight', 0.3)
    
    def get_positive_keywords(self) -> List[str]:
        return self.config.get('analysis', {}).get('news', {}).get('keywords', {}).get('positive', [])
    
    def get_negative_keywords(self) -> List[str]:
        return self.config.get('analysis', {}).get('news', {}).get('keywords', {}).get('negative', [])
    
    # Scheduler settings
    def is_daily_enabled(self) -> bool:
        return self.config.get('scheduler', {}).get('daily', {}).get('enabled', False)
    
    def get_daily_time(self) -> str:
        return self.config.get('scheduler', {}).get('daily', {}).get('time', '09:00')
    
    def get_daily_watchlist(self) -> str:
        return self.config.get('scheduler', {}).get('daily', {}).get('watchlist', 'default')
    
    def is_weekly_enabled(self) -> bool:
        return self.config.get('scheduler', {}).get('weekly', {}).get('enabled', False)
    
    def get_weekly_day(self) -> str:
        return self.config.get('scheduler', {}).get('weekly', {}).get('day', 'monday')
    
    def get_weekly_time(self) -> str:
        return self.config.get('scheduler', {}).get('weekly', {}).get('time', '08:00')
    
    def get_weekly_watchlist(self) -> str:
        return self.config.get('scheduler', {}).get('weekly', {}).get('watchlist', 'default')
    
    # Output settings
    def should_save_reports(self) -> bool:
        return self.config.get('output', {}).get('save_reports', True)
    
    def get_report_directory(self) -> str:
        return self.config.get('output', {}).get('report_directory', 'reports')
    
    def get_output_format(self) -> str:
        return self.config.get('output', {}).get('format', 'both')


# Global config instance
_config_instance = None

def get_config() -> ConfigManager:
    """Get or create global config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance


def reload_config():
    """Reload configuration from file"""
    global _config_instance
    _config_instance = ConfigManager()
    return _config_instance
