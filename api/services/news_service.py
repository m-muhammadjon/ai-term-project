import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from django.conf import settings


class NewsService:
    
    def __init__(self):
        self.twitter_bearer_token = os.getenv('TWITTER_BEARER_TOKEN', '')
        self.twitter_base_url = 'https://api.twitter.com/2'
        
        self.news_api_key = os.getenv('NEWS_API_KEY', '')
        self.news_api_base_url = 'https://newsapi.org/v2'
        
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.alpha_vantage_base_url = 'https://www.alphavantage.co/query'
    
    def get_news_for_ticker(self, ticker: str, limit: int = 10, 
                           sentiment: Optional[str] = None,
                           time_period: Optional[str] = None) -> List[Dict]:
        try:
            news = []
            
            if self.news_api_key:
                news.extend(self._get_newsapi_news(ticker, limit, time_period))
            
            if self.alpha_vantage_key != 'demo':
                news.extend(self._get_alpha_vantage_news(ticker, limit))
            
            if not news and self.twitter_bearer_token:
                news.extend(self._get_twitter_news(ticker, limit))
            
            if sentiment:
                news = [n for n in news if n.get('sentiment') == sentiment]
            
            seen_titles = set()
            unique_news = []
            for article in news:
                if article['title'] not in seen_titles:
                    seen_titles.add(article['title'])
                    unique_news.append(article)
                    if len(unique_news) >= limit:
                        break
            
            return unique_news[:limit]
        except Exception as e:
            print(f"Error fetching news for {ticker}: {str(e)}")
            return []
    
    def _get_newsapi_news(self, ticker: str, limit: int, time_period: Optional[str] = None) -> List[Dict]:
        url = f"{self.news_api_base_url}/everything"
        
        to_date = datetime.now()
        if time_period == '1d':
            from_date = to_date - timedelta(days=1)
        elif time_period == '7d':
            from_date = to_date - timedelta(days=7)
        elif time_period == '30d':
            from_date = to_date - timedelta(days=30)
        else:
            from_date = to_date - timedelta(days=7)
        
        params = {
            'q': ticker,
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': limit,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'apiKey': self.news_api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        news = []
        if 'articles' in data:
            for article in data['articles']:
                try:
                    published_date = datetime.strptime(
                        article['publishedAt'], 
                        '%Y-%m-%dT%H:%M:%SZ'
                    )
                except:
                    published_date = datetime.now()
                
                news.append({
                    'ticker': ticker,
                    'title': article.get('title', ''),
                    'content': article.get('description', '') or article.get('content', ''),
                    'source': article.get('source', {}).get('name', 'Unknown'),
                    'author': article.get('author'),
                    'date': published_date,
                    'link': article.get('url', ''),
                    'sentiment': None
                })
        
        return news
    
    def _get_alpha_vantage_news(self, ticker: str, limit: int) -> List[Dict]:
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': ticker,
            'apikey': self.alpha_vantage_key,
            'limit': limit
        }
        
        response = requests.get(self.alpha_vantage_base_url, params=params, timeout=10)
        data = response.json()
        
        news = []
        if 'feed' in data:
            for item in data['feed']:
                try:
                    published_date = datetime.strptime(
                        item['time_published'],
                        '%Y%m%dT%H%M%S'
                    )
                except:
                    published_date = datetime.now()
                
                sentiment_score = item.get('overall_sentiment_score', 0)
                if sentiment_score > 0.35:
                    sentiment = 'Bullish'
                elif sentiment_score < -0.35:
                    sentiment = 'Bearish'
                else:
                    sentiment = 'Neutral'
                
                news.append({
                    'ticker': ticker,
                    'title': item.get('title', ''),
                    'content': item.get('summary', ''),
                    'source': item.get('source', 'Unknown'),
                    'author': None,
                    'date': published_date,
                    'link': item.get('url', ''),
                    'sentiment': sentiment
                })
        
        return news
    
    def _get_twitter_news(self, ticker: str, limit: int) -> List[Dict]:
        if not self.twitter_bearer_token:
            return []
        
        url = f"{self.twitter_base_url}/tweets/search/recent"
        headers = {
            'Authorization': f'Bearer {self.twitter_bearer_token}'
        }
        
        query = f"${ticker} -is:retweet lang:en"
        params = {
            'query': query,
            'max_results': min(limit, 100),
            'tweet.fields': 'created_at,author_id,public_metrics',
            'expansions': 'author_id'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            data = response.json()
            
            news = []
            if 'data' in data:
                users = {u['id']: u for u in data.get('includes', {}).get('users', [])}
                
                for tweet in data['data']:
                    author = users.get(tweet.get('author_id', ''), {})
                    try:
                        created_at = datetime.strptime(
                            tweet['created_at'],
                            '%Y-%m-%dT%H:%M:%S.%fZ'
                        )
                    except:
                        created_at = datetime.now()
                    
                    news.append({
                        'ticker': ticker,
                        'title': tweet['text'][:200],
                        'content': tweet['text'],
                        'source': 'Twitter',
                        'author': author.get('name', 'Unknown'),
                        'date': created_at,
                        'link': f"https://twitter.com/{author.get('username', '')}/status/{tweet['id']}",
                        'sentiment': None
                    })
            
            return news
        except Exception as e:
            print(f"Error fetching Twitter news: {str(e)}")
            return []
    
    def get_news_buzz(self, limit: int = 10) -> List[Dict]:
        popular_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD', 
                          'NFLX', 'DIS', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD', 
                          'PYPL', 'BAC', 'INTC', 'CMCSA', 'XOM', 'VZ', 'ADBE', 'CSCO', 'NKE', 
                          'MRVL', 'AVGO', 'QCOM']
        
        buzz_scores = []
        for ticker in popular_tickers:
            news = self.get_news_for_ticker(ticker, limit=5)
            if news:
                score = min(len(news) / 10.0, 0.999999)
                buzz_scores.append({
                    'ticker': ticker,
                    'score': round(score, 6),
                    'company_full_name': self._get_company_name(ticker)
                })
        
        buzz_scores.sort(key=lambda x: x['score'], reverse=True)
        return buzz_scores[:limit]
    
    def _get_company_name(self, ticker: str) -> str:
        company_names = {
            'AAPL': 'Apple Inc.',
            'MSFT': 'Microsoft Corporation',
            'GOOGL': 'Alphabet Inc.',
            'AMZN': 'Amazon.com Inc.',
            'META': 'Meta Platforms Inc.',
            'TSLA': 'Tesla Inc.',
            'NVDA': 'NVIDIA Corporation',
            'AMD': 'Advanced Micro Devices Inc.',
            'NFLX': 'Netflix Inc.',
            'DIS': 'The Walt Disney Company',
            'JPM': 'JPMorgan Chase & Co.',
            'V': 'Visa Inc.',
            'JNJ': 'Johnson & Johnson',
            'WMT': 'Walmart Inc.',
            'PG': 'The Procter & Gamble Company',
            'MA': 'Mastercard Incorporated',
            'UNH': 'UnitedHealth Group Inc.',
            'HD': 'The Home Depot Inc.',
            'PYPL': 'PayPal Holdings Inc.',
            'BAC': 'Bank of America Corp.',
            'INTC': 'Intel Corporation',
            'CMCSA': 'Comcast Corporation',
            'XOM': 'Exxon Mobil Corporation',
            'VZ': 'Verizon Communications Inc.',
            'ADBE': 'Adobe Inc.',
            'CSCO': 'Cisco Systems Inc.',
            'NKE': 'Nike Inc.',
            'MRVL': 'Marvell Technology Inc.',
            'AVGO': 'Broadcom Inc.',
            'QCOM': 'QUALCOMM Incorporated'
        }
        return company_names.get(ticker, f'{ticker} Corporation')

