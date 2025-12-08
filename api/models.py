import uuid
from django.db import models
from django.utils import timezone


class Stock(models.Model):
    """Model to store stock information"""
    ticker = models.CharField(max_length=10, unique=True, db_index=True)
    company_full_name = models.CharField(max_length=255)
    current_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    change_in_day = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sentiment_score = models.IntegerField(null=True, blank=True)
    market_cap = models.BigIntegerField(null=True, blank=True)
    volume = models.BigIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['ticker']

    def __str__(self):
        return f"{self.ticker} - {self.company_full_name}"


class News(models.Model):
    """Model to store news articles"""
    SENTIMENT_CHOICES = [
        ('Bullish', 'Bullish'),
        ('Bearish', 'Bearish'),
        ('Neutral', 'Neutral'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticker = models.CharField(max_length=10, db_index=True)
    title = models.CharField(max_length=500)
    content = models.TextField()
    source = models.CharField(max_length=255)
    author = models.CharField(max_length=255, null=True, blank=True)
    date = models.DateTimeField()
    link = models.URLField(max_length=500, unique=True, db_index=True)
    sentiment = models.CharField(max_length=10, choices=SENTIMENT_CHOICES, null=True, blank=True)
    sentiment_analyzed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['ticker', '-date']),
            models.Index(fields=['sentiment']),
        ]

    def __str__(self):
        return f"{self.ticker} - {self.title[:50]}"


class PriceHistory(models.Model):
    """Model to store historical price data for stocks"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='price_history')
    date = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ['-date']
        unique_together = ['stock', 'date']
        indexes = [
            models.Index(fields=['stock', '-date']),
        ]

    def __str__(self):
        return f"{self.stock.ticker} - {self.date} - ${self.price}"


class NewsSentimentHistory(models.Model):
    """Model to store sentiment history for stocks"""
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='sentiment_history')
    date = models.DateField()
    bullish_count = models.IntegerField(default=0)
    bearish_count = models.IntegerField(default=0)
    neutral_count = models.IntegerField(default=0)
    total_news = models.IntegerField(default=0)

    class Meta:
        ordering = ['-date']
        unique_together = ['stock', 'date']
        indexes = [
            models.Index(fields=['stock', '-date']),
        ]

    def __str__(self):
        return f"{self.stock.ticker} - {self.date} - Bullish: {self.bullish_count}, Bearish: {self.bearish_count}"

