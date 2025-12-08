"""
Service for interacting with stock market APIs
Using Alpha Vantage as primary source, with fallback to Yahoo Finance
"""
import os
import time
import requests
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from django.conf import settings
from django.utils import timezone


class StockAPIService:
    """Service to fetch stock data from external APIs"""
    
    def __init__(self):
        # Alpha Vantage API key (set in environment variables)
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.alpha_vantage_base_url = 'https://www.alphavantage.co/query'
        
        # Alternative: Yahoo Finance API (free, no key required)
        self.yahoo_finance_base_url = 'https://query1.finance.yahoo.com/v8/finance/chart'
    
    def get_stock_quote(self, ticker: str) -> Optional[Dict]:
        """
        Get current stock quote
        Returns: {
            'ticker': str,
            'current_price': Decimal,
            'change': Decimal,
            'change_percent': Decimal,
            'volume': int,
            'market_cap': int
        }
        """
        try:
            # Try Alpha Vantage first
            if self.alpha_vantage_key != 'demo':
                return self._get_alpha_vantage_quote(ticker)
            else:
                # Fallback to Yahoo Finance
                return self._get_yahoo_finance_quote(ticker)
        except Exception as e:
            # Re-raise the exception so callers can handle it
            raise
    
    def _get_alpha_vantage_quote(self, ticker: str) -> Optional[Dict]:
        """Get quote from Alpha Vantage API"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': ticker,
            'apikey': self.alpha_vantage_key
        }
        
        try:
            response = requests.get(self.alpha_vantage_base_url, params=params, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                raise Exception(f"Alpha Vantage API error: {data['Error Message']}")
            if 'Note' in data:
                raise Exception(f"Alpha Vantage rate limit: {data['Note']}")
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                price_str = quote.get('05. price', '0')
                
                if not price_str or price_str == '0':
                    raise Exception("No price data in quote")
                
                return {
                    'ticker': ticker,
                    'current_price': Decimal(price_str),
                    'change': Decimal(quote.get('09. change', 0)),
                    'change_percent': Decimal(quote.get('10. change percent', '0%').rstrip('%')),
                    'volume': int(quote.get('06. volume', 0)),
                    'market_cap': None  # Alpha Vantage doesn't provide this in quote
                }
            else:
                raise Exception("No quote data in response")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except (KeyError, ValueError, TypeError) as e:
            raise Exception(f"Data parsing error: {str(e)}")
    
    def _get_yahoo_finance_quote(self, ticker: str) -> Optional[Dict]:
        """Get quote from Yahoo Finance API (free alternative)"""
        url = f"{self.yahoo_finance_base_url}/{ticker}"
        params = {
            'interval': '1d',
            'range': '1d'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and len(data['chart']['result']) > 0:
                result = data['chart']['result'][0]
                
                # Check for errors in the result
                if 'error' in result:
                    error_msg = result.get('error', {}).get('description', 'Unknown error')
                    raise Exception(f"Yahoo Finance API error: {error_msg}")
                
                meta = result.get('meta', {})
                
                # Check if we have valid price data
                if not meta.get('regularMarketPrice'):
                    raise Exception("No price data available")
                
                current_price = Decimal(str(meta.get('regularMarketPrice', 0)))
                previous_close = Decimal(str(meta.get('previousClose', current_price)))
                change = current_price - previous_close
                change_percent = (change / previous_close * 100) if previous_close > 0 else Decimal(0)
                
                return {
                    'ticker': ticker,
                    'current_price': current_price,
                    'change': change,
                    'change_percent': change_percent,
                    'volume': meta.get('regularMarketVolume', 0),
                    'market_cap': meta.get('marketCap', None)
                }
            else:
                raise Exception("No chart data in response")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except (KeyError, ValueError, TypeError) as e:
            raise Exception(f"Data parsing error: {str(e)}")
    
    def get_price_history(self, ticker: str, days: int = 30) -> List[Dict]:
        """
        Get historical price data
        Returns: List of {'date': date, 'price': Decimal, 'volume': int}
        """
        try:
            if self.alpha_vantage_key != 'demo':
                return self._get_alpha_vantage_history(ticker, days)
            else:
                return self._get_yahoo_finance_history(ticker, days)
        except Exception as e:
            print(f"Error fetching price history for {ticker}: {str(e)}")
            return []
    
    def _get_alpha_vantage_history(self, ticker: str, days: int) -> List[Dict]:
        """Get historical data from Alpha Vantage"""
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': ticker,
            'apikey': self.alpha_vantage_key,
            'outputsize': 'compact' if days <= 100 else 'full'
        }
        
        response = requests.get(self.alpha_vantage_base_url, params=params, timeout=10)
        data = response.json()
        
        history = []
        if 'Time Series (Daily)' in data:
            time_series = data['Time Series (Daily)']
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            for date_str, values in time_series.items():
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
                if date >= start_date:
                    history.append({
                        'date': date,
                        'price': Decimal(values['4. close']),
                        'volume': int(values['5. volume'])
                    })
            
            history.sort(key=lambda x: x['date'])
        return history
    
    def _get_yahoo_finance_history(self, ticker: str, days: int) -> List[Dict]:
        """Get historical data from Yahoo Finance"""
        url = f"{self.yahoo_finance_base_url}/{ticker}"
        params = {
            'interval': '1d',
            'range': f'{days}d'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        history = []
        if 'chart' in data and 'result' in data['chart'] and len(data['chart']['result']) > 0:
            result = data['chart']['result'][0]
            timestamps = result.get('timestamp', [])
            closes = result.get('indicators', {}).get('quote', [{}])[0].get('close', [])
            volumes = result.get('indicators', {}).get('quote', [{}])[0].get('volume', [])
            
            for i, timestamp in enumerate(timestamps):
                if closes[i] is not None:
                    date = datetime.fromtimestamp(timestamp).date()
                    history.append({
                        'date': date,
                        'price': Decimal(str(closes[i])),
                        'volume': int(volumes[i]) if volumes[i] else 0
                    })
        
        return history
    
    def get_top_movers(self, limit: int = 10) -> List[Dict]:
        """
        Get top movers (stocks with highest price changes)
        Optimized to use database first, only makes API calls for missing/outdated data.
        Returns: List of {'ticker': str, 'change': Decimal, 'current_price': Decimal}
        """
        from api.models import Stock
        
        # Common stock tickers to check
        popular_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 
                          'NFLX', 'DIS', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 
                          'PYPL', 'BAC', 'INTC', 'CMCSA', 'XOM', 'VZ', 'ADBE', 'CSCO', 'NKE', 
                          'MRVL', 'AVGO', 'QCOM']
        
        # Check more tickers to get best movers (need more data to find top movers)
        tickers_to_check = popular_tickers[:limit * 3] if limit * 3 <= len(popular_tickers) else popular_tickers
        
        now = timezone.now()
        cache_duration = timedelta(hours=1)  # Cache for 1 hour
        
        # Get stocks from database
        db_stocks = Stock.objects.filter(ticker__in=tickers_to_check)
        db_stock_dict = {stock.ticker: stock for stock in db_stocks}
        
        movers = []
        stocks_to_update = []
        
        # First, collect data from database and identify which stocks need updating
        for ticker in tickers_to_check:
            stock = db_stock_dict.get(ticker)
            
            if stock and stock.current_price and stock.change_in_day is not None:
                # Check if data is fresh enough
                if stock.updated_at:
                    time_since_update = now - stock.updated_at
                    if time_since_update < cache_duration:
                        # Use database data
                        # Calculate absolute change from percentage change
                        # change_in_day is percentage, so: absolute_change = (percentage / 100) * price
                        absolute_change = (stock.change_in_day / 100) * stock.current_price
                        movers.append({
                            'ticker': ticker,
                            'change': absolute_change,
                            'current_price': stock.current_price
                        })
                        continue
            
            # Stock needs updating (missing or outdated)
            stocks_to_update.append(ticker)
        
        # Update stocks that need fresh data (with rate limiting)
        if stocks_to_update:
            # Limit concurrent API calls to respect rate limits
            # Alpha Vantage: 5 calls/min, so we'll do max 5 at a time with delays
            max_concurrent = 5
            delay_between_batches = 12  # 12 seconds for Alpha Vantage rate limit
            
            for i, ticker in enumerate(stocks_to_update):
                try:
                    quote = self.get_stock_quote(ticker)
                    
                    if quote and quote.get('current_price') and quote['current_price'] > 0:
                        # Update database
                        stock, created = Stock.objects.get_or_create(
                            ticker=ticker,
                            defaults={'company_full_name': f'{ticker} Corporation'}
                        )
                        stock.current_price = quote['current_price']
                        stock.change_in_day = quote['change_percent']
                        if quote.get('volume'):
                            stock.volume = quote['volume']
                        if quote.get('market_cap'):
                            stock.market_cap = quote['market_cap']
                        stock.save()
                        
                        # Add to movers list
                        # Use 'change' (absolute dollar change) for top movers sorting
                        movers.append({
                            'ticker': ticker,
                            'change': quote['change'],  # Absolute dollar change
                            'current_price': quote['current_price']
                        })
                    
                    # Rate limiting: delay after every 5 calls (for Alpha Vantage)
                    if (i + 1) % max_concurrent == 0 and i < len(stocks_to_update) - 1:
                        time.sleep(delay_between_batches)
                    elif i < len(stocks_to_update) - 1:
                        # Small delay between calls
                        time.sleep(0.5)
                        
                except Exception as e:
                    # If API call fails, try to use stale database data if available
                    stock = db_stock_dict.get(ticker)
                    if stock and stock.current_price and stock.change_in_day is not None:
                        movers.append({
                            'ticker': ticker,
                            'change': stock.change_in_day,
                            'current_price': stock.current_price
                        })
                    # Continue with next ticker
                    continue
        
        # Sort by absolute change and return top movers
        movers.sort(key=lambda x: abs(x['change']), reverse=True)
        return movers[:limit]

