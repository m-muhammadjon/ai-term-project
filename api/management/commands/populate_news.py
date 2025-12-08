"""
Management command to fetch news for all stocks
Usage: python manage.py populate_news
"""
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from api.models import Stock, News
from api.services.news_service import NewsService


class Command(BaseCommand):
    help = 'Fetch news articles for all stocks from external APIs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--delay',
            type=float,
            default=2.0,
            help='Delay between API calls in seconds (default: 2.0)',
        )
        parser.add_argument(
            '--retry',
            type=int,
            default=3,
            help='Number of retries for failed API calls (default: 3)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of news articles to fetch per stock (default: 10)',
        )
        parser.add_argument(
            '--time-period',
            type=str,
            default='7d',
            choices=['1d', '7d', '30d'],
            help='Time period for news: 1d, 7d, or 30d (default: 7d)',
        )
        parser.add_argument(
            '--ticker',
            type=str,
            help='Fetch news for a specific ticker only (optional)',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip stocks that already have recent news (within last 24 hours)',
        )

    def handle(self, *args, **options):
        delay = options['delay']
        max_retries = options['retry']
        limit = options['limit']
        time_period = options['time_period']
        specific_ticker = options.get('ticker')
        skip_existing = options['skip_existing']
        
        news_service = NewsService()
        
        self.stdout.write('Starting to fetch news for stocks...')
        self.stdout.write(f'Using {delay}s delay between API calls to respect rate limits')
        self.stdout.write(f'Time period: {time_period}, Limit per stock: {limit}')
        
        # Check which API is being used
        if news_service.news_api_key:
            self.stdout.write('Using NewsAPI')
        elif news_service.alpha_vantage_key != 'demo':
            self.stdout.write('Using Alpha Vantage News API')
        elif news_service.twitter_bearer_token:
            self.stdout.write('Using Twitter API')
        else:
            self.stdout.write(self.style.WARNING('No API keys found. News fetching may be limited.'))
        
        # Get stocks to process
        if specific_ticker:
            stocks = Stock.objects.filter(ticker=specific_ticker.upper())
            if not stocks.exists():
                self.stdout.write(self.style.ERROR(f'Stock {specific_ticker} not found in database'))
                return
        else:
            stocks = Stock.objects.all().order_by('ticker')
        
        if not stocks.exists():
            self.stdout.write(self.style.WARNING('No stocks found in database. Run populate_stocks first.'))
            return
        
        total_stocks = stocks.count()
        self.stdout.write(f'Found {total_stocks} stock(s) to process')
        self.stdout.write('')
        
        total_news_fetched = 0
        total_news_saved = 0
        failed_count = 0
        skipped_count = 0
        
        # Calculate date threshold for skip_existing
        if skip_existing:
            recent_threshold = timezone.now() - timedelta(hours=24)
        
        for i, stock in enumerate(stocks):
            try:
                self.stdout.write(
                    f'Processing {stock.ticker} ({i+1}/{total_stocks})...', 
                    ending=' '
                )
                
                # Check if we should skip this stock
                if skip_existing:
                    recent_news_count = News.objects.filter(
                        ticker=stock.ticker,
                        date__gte=recent_threshold
                    ).count()
                    if recent_news_count > 0:
                        skipped_count += 1
                        self.stdout.write(self.style.WARNING(f'⏭ Skipped (has recent news)'))
                        continue
                
                # Retry logic for API calls
                news_articles = []
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        news_articles = news_service.get_news_for_ticker(
                            stock.ticker,
                            limit=limit,
                            time_period=time_period
                        )
                        if news_articles:
                            break
                    except Exception as e:
                        last_error = str(e)
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2  # Exponential backoff
                            self.stdout.write(f'Retry {attempt + 1}/{max_retries} in {wait_time}s...', ending=' ')
                            time.sleep(wait_time)
                        else:
                            self.stdout.write(self.style.ERROR(f'Failed after {max_retries} attempts'))
                
                if news_articles:
                    saved_count = 0
                    for article in news_articles:
                        try:
                            # Save news to database (avoid duplicates by link)
                            news, created = News.objects.update_or_create(
                                link=article['link'],
                                defaults={
                                    'ticker': article['ticker'],
                                    'title': article['title'],
                                    'content': article['content'],
                                    'source': article['source'],
                                    'author': article.get('author'),
                                    'date': article['date'],
                                    'sentiment': article.get('sentiment'),
                                    'sentiment_analyzed': article.get('sentiment') is not None
                                }
                            )
                            if created:
                                saved_count += 1
                        except Exception as e:
                            # Skip duplicate or invalid entries
                            continue
                    
                    total_news_fetched += len(news_articles)
                    total_news_saved += saved_count
                    
                    if saved_count > 0:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Fetched {len(news_articles)}, Saved {saved_count} new'
                            )
                        )
                    else:
                        self.stdout.write(
                            f'✓ Fetched {len(news_articles)}, All already exist'
                        )
                else:
                    failed_count += 1
                    error_msg = last_error if last_error else 'No news found'
                    self.stdout.write(self.style.WARNING(f'✗ {error_msg}'))
                
                # Delay between API calls to respect rate limits
                if i < total_stocks - 1:  # Don't delay after the last stock
                    time.sleep(delay)
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
                time.sleep(delay)  # Still delay even on error
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Completed!'))
        self.stdout.write(f'  Stocks processed: {total_stocks}')
        self.stdout.write(f'  Stocks skipped: {skipped_count}')
        self.stdout.write(f'  Stocks failed: {failed_count}')
        self.stdout.write(f'  News articles fetched: {total_news_fetched}')
        self.stdout.write(f'  News articles saved: {total_news_saved}')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        if failed_count > 0:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'Some stocks failed to fetch news. This might be due to:'
            ))
            self.stdout.write('  - API rate limits (try running again with --delay 3.0)')
            self.stdout.write('  - Network issues')
            self.stdout.write('  - No news available for those stocks')
            self.stdout.write('  - API service temporarily unavailable')
        
        if total_news_saved > 0:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'Successfully saved {total_news_saved} new news articles to database!'
            ))

