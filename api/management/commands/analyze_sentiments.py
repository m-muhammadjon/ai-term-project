"""
Management command to analyze sentiment for all unchecked news articles
Usage: python manage.py analyze_sentiments
"""
import time
from django.core.management.base import BaseCommand
from django.db.models import Q, Count
from api.models import News
from api.services.sentiment_service import SentimentService


class Command(BaseCommand):
    help = 'Analyze sentiment for all news articles that have not been analyzed yet'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of news articles to process in each batch (default: 100)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of news articles to process (optional)',
        )
        parser.add_argument(
            '--ticker',
            type=str,
            help='Analyze sentiment for a specific ticker only (optional)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-analyze all news articles, even if already analyzed',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=0.1,
            help='Delay between processing each article in seconds (default: 0.1)',
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        limit = options.get('limit')
        specific_ticker = options.get('ticker')
        force = options['force']
        delay = options['delay']
        
        self.stdout.write('Starting sentiment analysis for news articles...')
        
        # Initialize sentiment service (will use FinBERT by default)
        sentiment_service = SentimentService()
        
        if sentiment_service.finbert_available:
            self.stdout.write(self.style.SUCCESS('✓ Using FinBERT model for sentiment analysis'))
        else:
            self.stdout.write(self.style.WARNING('⚠ FinBERT not available, using fallback method'))
        
        # Build query for unchecked news
        if force:
            query = Q()
            self.stdout.write('Mode: Re-analyzing all news articles')
        else:
            query = Q(sentiment_analyzed=False) | Q(sentiment__isnull=True)
            self.stdout.write('Mode: Analyzing only unchecked news articles')
        
        if specific_ticker:
            query &= Q(ticker=specific_ticker.upper())
            self.stdout.write(f'Filtering by ticker: {specific_ticker.upper()}')
        
        # Get news articles to process
        news_queryset = News.objects.filter(query).order_by('-date')
        
        if limit:
            news_queryset = news_queryset[:limit]
        
        total_count = news_queryset.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No news articles to analyze!'))
            return
        
        self.stdout.write(f'Found {total_count} news article(s) to analyze')
        self.stdout.write('')
        
        processed_count = 0
        success_count = 0
        error_count = 0
        updated_count = 0
        
        # Process in batches
        for i in range(0, total_count, batch_size):
            batch = news_queryset[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_count + batch_size - 1) // batch_size
            
            self.stdout.write(
                f'Processing batch {batch_num}/{total_batches} '
                f'({len(batch)} articles)...'
            )
            
            for news in batch:
                try:
                    processed_count += 1
                    
                    # Skip if already analyzed and not forcing
                    if not force and news.sentiment_analyzed and news.sentiment:
                        continue
                    
                    # Prepare text for analysis
                    text_to_analyze = f"{news.title} {news.content}".strip()
                    
                    if not text_to_analyze:
                        self.stdout.write(
                            self.style.WARNING(
                                f'  [{processed_count}/{total_count}] {news.ticker} - '
                                f'Empty content, skipping'
                            )
                        )
                        continue
                    
                    # Analyze sentiment
                    sentiment_result = sentiment_service.analyze_sentiment(text_to_analyze)
                    sentiment = sentiment_result.get('sentiment', 'Neutral')
                    
                    # Check if sentiment changed
                    sentiment_changed = news.sentiment != sentiment
                    
                    # Update news article
                    news.sentiment = sentiment
                    news.sentiment_analyzed = True
                    news.save(update_fields=['sentiment', 'sentiment_analyzed'])
                    
                    success_count += 1
                    if sentiment_changed or not news.sentiment_analyzed:
                        updated_count += 1
                    
                    # Progress indicator
                    if processed_count % 10 == 0 or processed_count == total_count:
                        self.stdout.write(
                            f'  Progress: {processed_count}/{total_count} '
                            f'({success_count} success, {error_count} errors)',
                            ending='\r'
                        )
                        self.stdout.flush()
                    
                    # Small delay to avoid overwhelming the system
                    if delay > 0:
                        time.sleep(delay)
                    
                except Exception as e:
                    error_count += 1
                    self.stdout.write('')
                    self.stdout.write(
                        self.style.ERROR(
                            f'  [{processed_count}/{total_count}] Error analyzing '
                            f'{news.ticker} (ID: {news.id}): {str(e)}'
                        )
                    )
            
            # Summary after each batch
            self.stdout.write('')
            self.stdout.write(
                f'  Batch {batch_num} complete: '
                f'{success_count} analyzed, {error_count} errors'
            )
            self.stdout.write('')
        
        # Final summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('Analysis Complete!'))
        self.stdout.write(f'  Total processed: {processed_count}')
        self.stdout.write(f'  Successfully analyzed: {success_count}')
        self.stdout.write(f'  Updated: {updated_count}')
        self.stdout.write(f'  Errors: {error_count}')
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Statistics by sentiment
        if success_count > 0:
            self.stdout.write('')
            self.stdout.write('Sentiment distribution:')
            sentiment_stats = News.objects.filter(
                sentiment_analyzed=True
            ).values('sentiment').annotate(
                count=Count('id')
            ).order_by('-count')
            
            for stat in sentiment_stats:
                sentiment = stat['sentiment'] or 'Unknown'
                count = stat['count']
                self.stdout.write(f'  {sentiment}: {count}')
        
        if error_count > 0:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                'Some articles failed to analyze. Check the error messages above.'
            ))

