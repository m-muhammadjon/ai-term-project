"""
Management command to populate initial stock data
Usage: python manage.py populate_stocks
"""
import time
from django.core.management.base import BaseCommand
from api.models import Stock
from api.services.stock_api_service import StockAPIService
from api.services.news_service import NewsService


class Command(BaseCommand):
    help = 'Populate initial stock data from external APIs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Delay between API calls in seconds (default: 1.0)',
        )
        parser.add_argument(
            '--retry',
            type=int,
            default=3,
            help='Number of retries for failed API calls (default: 3)',
        )

    def handle(self, *args, **options):
        delay = options['delay']
        max_retries = options['retry']
        
        stock_service = StockAPIService()
        
        self.stdout.write('Starting to populate stock data...')
        self.stdout.write(f'Using {delay}s delay between API calls to respect rate limits')
        
        # Check which API is being used
        if stock_service.alpha_vantage_key != 'demo':
            self.stdout.write(self.style.WARNING(
                'Using Alpha Vantage API (5 calls/min limit). '
                'Recommended delay: 12-15 seconds. Current delay: {:.1f}s'.format(delay)
            ))
            if delay < 12:
                self.stdout.write(self.style.WARNING(
                    '⚠ Warning: Delay is less than 12s. You may hit rate limits. '
                    'Use --delay 12 or higher for Alpha Vantage.'
                ))
        else:
            self.stdout.write('Using Yahoo Finance API (no key required)')
        
        # Common stock tickers
        tickers = [
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'AMD',
            'NFLX', 'DIS', 'JPM', 'V', 'JNJ', 'WMT', 'PG', 'MA', 'UNH', 'HD',
            'PYPL', 'BAC', 'INTC', 'CMCSA', 'XOM', 'VZ', 'ADBE', 'CSCO', 'NKE',
            'MRVL', 'AVGO', 'QCOM'
        ]
        
        news_service = NewsService()
        
        created_count = 0
        updated_count = 0
        failed_count = 0
        
        for i, ticker in enumerate(tickers):
            try:
                self.stdout.write(f'Processing {ticker} ({i+1}/{len(tickers)})...', ending=' ')
                
                # Retry logic for API calls
                quote = None
                last_error = None
                
                for attempt in range(max_retries):
                    try:
                        quote = stock_service.get_stock_quote(ticker)
                        if quote:
                            break
                    except Exception as e:
                        last_error = str(e)
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2  # Exponential backoff: 2s, 4s, 6s
                            self.stdout.write(f'Retry {attempt + 1}/{max_retries} in {wait_time}s...', ending=' ')
                            time.sleep(wait_time)
                        else:
                            self.stdout.write(self.style.ERROR(f'Failed after {max_retries} attempts'))
                
                if quote and quote.get('current_price') and quote['current_price'] > 0:
                    # Get company name
                    company_name = news_service._get_company_name(ticker)
                    
                    stock, created = Stock.objects.update_or_create(
                        ticker=ticker,
                        defaults={
                            'company_full_name': company_name,
                            'current_price': quote['current_price'],
                            'change_in_day': quote['change_percent'],
                            'volume': quote.get('volume'),
                            'market_cap': quote.get('market_cap'),
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f'✓ Created'))
                    else:
                        updated_count += 1
                        self.stdout.write(self.style.SUCCESS(f'✓ Updated'))
                else:
                    failed_count += 1
                    error_msg = last_error if last_error else 'No data returned'
                    self.stdout.write(self.style.WARNING(f'✗ No data ({error_msg})'))
                
                # Delay between API calls to respect rate limits
                # Alpha Vantage: 5 calls per minute = 12 seconds between calls
                # We use a smaller delay since we might be using Yahoo Finance
                if i < len(tickers) - 1:  # Don't delay after the last ticker
                    time.sleep(delay)
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(f'✗ Error: {str(e)}'))
                time.sleep(delay)  # Still delay even on error
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        self.stdout.write(self.style.SUCCESS(f'Completed!'))
        self.stdout.write(f'  Created: {created_count}')
        self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Failed: {failed_count}')
        self.stdout.write(self.style.SUCCESS('=' * 50))
        
        if failed_count > 0:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'Some stocks failed to load. This might be due to:'
            ))
            self.stdout.write('  - API rate limits (try running again with --delay 2.0)')
            self.stdout.write('  - Network issues')
            self.stdout.write('  - Invalid ticker symbols')
            self.stdout.write('  - API service temporarily unavailable')

