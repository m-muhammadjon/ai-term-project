import os
import time
import requests
from decimal import Decimal
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from django.conf import settings
from django.utils import timezone


class StockAPIService:
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.alpha_vantage_base_url = 'https://www.alphavantage.co/query'
        
        self.yahoo_finance_base_url = 'https://query1.finance.yahoo.com/v8/finance/chart'
    
    def get_stock_quote(self, ticker: str) -> Optional[Dict]:
        try:
            if self.alpha_vantage_key != 'demo':
                return self._get_alpha_vantage_quote(ticker)
            else:
                return self._get_yahoo_finance_quote(ticker)
        except Exception as e:
            raise
    
    def _get_alpha_vantage_quote(self, ticker: str) -> Optional[Dict]:
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': ticker,
            'apikey': self.alpha_vantage_key
        }
        
        try:
            response = requests.get(self.alpha_vantage_base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
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
                    'market_cap': None
                }
            else:
                raise Exception("No quote data in response")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {str(e)}")
        except (KeyError, ValueError, TypeError) as e:
            raise Exception(f"Data parsing error: {str(e)}")
    
    def _get_yahoo_finance_quote(self, ticker: str) -> Optional[Dict]:
        url = f"{self.yahoo_finance_base_url}/{ticker}"
        params = {
            'interval': '1d',
            'range': '1d'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart'] and len(data['chart']['result']) > 0:
                result = data['chart']['result'][0]
                
                if 'error' in result:
                    error_msg = result.get('error', {}).get('description', 'Unknown error')
                    raise Exception(f"Yahoo Finance API error: {error_msg}")
                
                meta = result.get('meta', {})
                
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
        try:
            if self.alpha_vantage_key != 'demo':
                return self._get_alpha_vantage_history(ticker, days)
            else:
                return self._get_yahoo_finance_history(ticker, days)
        except Exception as e:
            print(f"Error fetching price history for {ticker}: {str(e)}")
            return []
    
    def _get_alpha_vantage_history(self, ticker: str, days: int) -> List[Dict]:
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
        from api.models import Stock
        
        popular_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 
                          'NFLX', 'DIS', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 
                          'PYPL', 'BAC', 'INTC', 'CMCSA', 'XOM', 'VZ', 'ADBE', 'CSCO', 'NKE', 
                          'MRVL', 'AVGO', 'QCOM']
        
        tickers_to_check = popular_tickers[:limit * 3] if limit * 3 <= len(popular_tickers) else popular_tickers
        
        now = timezone.now()
        cache_duration = timedelta(hours=1)
        
        db_stocks = Stock.objects.filter(ticker__in=tickers_to_check)
        db_stock_dict = {stock.ticker: stock for stock in db_stocks}
        
        movers = []
        stocks_to_update = []
        
        for ticker in tickers_to_check:
            stock = db_stock_dict.get(ticker)
            
            if stock and stock.current_price and stock.change_in_day is not None:
                if stock.updated_at:
                    time_since_update = now - stock.updated_at
                    if time_since_update < cache_duration:
                        absolute_change = (stock.change_in_day / 100) * stock.current_price
                        movers.append({
                            'ticker': ticker,
                            'change': absolute_change,
                            'current_price': stock.current_price
                        })
                        continue
            
            stocks_to_update.append(ticker)
        
        if stocks_to_update:
            max_concurrent = 5
            delay_between_batches = 12
            
            for i, ticker in enumerate(stocks_to_update):
                try:
                    quote = self.get_stock_quote(ticker)
                    
                    if quote and quote.get('current_price') and quote['current_price'] > 0:
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
                        
                        movers.append({
                            'ticker': ticker,
                            'change': quote['change'],
                            'current_price': quote['current_price']
                        })
                    
                    if (i + 1) % max_concurrent == 0 and i < len(stocks_to_update) - 1:
                        time.sleep(delay_between_batches)
                    elif i < len(stocks_to_update) - 1:
                        time.sleep(0.5)
                        
                except Exception as e:
                    stock = db_stock_dict.get(ticker)
                    if stock and stock.current_price and stock.change_in_day is not None:
                        movers.append({
                            'ticker': ticker,
                            'change': stock.change_in_day,
                            'current_price': stock.current_price
                        })
                    continue
        
        movers.sort(key=lambda x: abs(x['change']), reverse=True)
        return movers[:limit]

