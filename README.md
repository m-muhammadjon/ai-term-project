# AI Project - Market Research Analysis Backend

Django REST API backend for Market Research Analysis application.

## Features

- **Stock Market Data**: Real-time stock quotes, price history, and market data
- **News Aggregation**: Fetch news from multiple sources (Twitter, NewsAPI, Alpha Vantage)
- **Sentiment Analysis**: Analyze sentiment of news articles (Bullish, Bearish, Neutral)
- **Top Movers**: Get stocks with highest price changes
- **News Buzz**: Track most mentioned stocks in news
- **Sentiment Movers**: Stocks with significant sentiment changes

## API Endpoints

### GET /topMovers
Get top movers (stocks with highest price changes)
- Query params: `limit` (optional, default: 10)

### GET /newsBuzz
Get most mentioned stocks in news
- Query params: `limit` (optional, default: 10)

### GET /sentimentMovers
Get sentiment movers
- Query params: `limit` (optional, default: 10)

### GET /stocks
Get all stocks
- Query params: `limit` (optional, default: 50)

### GET /news
Get news articles
- Query params:
  - `limit` (optional, default: 20)
  - `sentiment` (optional: Bullish, Bearish, Neutral)
  - `stocks` (optional: comma-separated tickers, e.g., "AAPL,MSFT")
  - `timePeriod` (optional: 1d, 7d, 30d)

### GET /sentiment/:id
Get sentiment analysis for a specific news article
- Path param: `id` (UUID of news article)

### GET /stock-details
Get detailed information about a stock
- Query params: `ticker` (required)

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
Create a `.env` file in the project root with the following variables:
```bash
# Stock Market API
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Twitter API (v2)
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# News API
NEWS_API_KEY=your_news_api_key_here

# OpenAI API (optional, for advanced sentiment analysis)
OPENAI_API_KEY=your_openai_api_key_here
USE_EXTERNAL_SENTIMENT_API=false
```

Note: The backend will work without API keys using free alternatives (Yahoo Finance for stocks, simple keyword-based sentiment analysis).

3. **Run migrations:**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Create superuser (optional):**
```bash
python manage.py createsuperuser
```

5. **Populate initial stock data (optional):**
```bash
python manage.py populate_stocks
```

6. **Fetch news for all stocks (optional):**
```bash
# Fetch news for all stocks (last 7 days)
python manage.py populate_news

# Fetch news for a specific stock
python manage.py populate_news --ticker AAPL

# Fetch news with custom settings
python manage.py populate_news --time-period 30d --limit 20 --delay 3.0

# Skip stocks that already have recent news (within 24 hours)
python manage.py populate_news --skip-existing
```

7. **Analyze sentiment for news articles (optional):**
```bash
# Analyze sentiment for all unchecked news articles using FinBERT
python manage.py analyze_sentiments

# Analyze with custom batch size
python manage.py analyze_sentiments --batch-size 50

# Analyze for a specific ticker
python manage.py analyze_sentiments --ticker AAPL

# Re-analyze all news articles (force update)
python manage.py analyze_sentiments --force

# Limit number of articles to process
python manage.py analyze_sentiments --limit 1000
```

8. **Run development server:**
```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/`

## API Documentation

Once the server is running, you can access the interactive API documentation:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

The documentation is automatically generated using `drf-spectacular` and includes:
- All available endpoints
- Request/response schemas
- Query parameters
- Try-it-out functionality

## API Keys

**📖 For detailed step-by-step instructions on getting API keys, see [API_KEYS_GUIDE.md](API_KEYS_GUIDE.md)**

You'll need API keys for the following services:

1. **Alpha Vantage** (Stock Market Data) - **Primary**
   - Sign up at: https://www.alphavantage.co/support/#api-key
   - Free tier: 5 API calls per minute, 500 calls per day
   - **Alternative**: Yahoo Finance (no key required, automatic fallback)

2. **NewsAPI** (News Articles) - **Recommended**
   - Sign up at: https://newsapi.org/
   - Free tier: 100 requests per day

3. **Twitter API** (Optional - for Twitter news)
   - Sign up at: https://developer.twitter.com/
   - Requires Twitter Developer account approval

4. **OpenAI API** (Optional - for advanced sentiment analysis)
   - Sign up at: https://platform.openai.com/
   - Pay-as-you-go pricing (starts with $5 free credit)
   - **Alternative**: Built-in keyword-based analysis (no key required)

## Alternative APIs

The backend includes fallback mechanisms:
- **Yahoo Finance API**: Free alternative for stock data (no API key required)
- **Simple Sentiment Analysis**: Keyword-based analysis (no external API required)

## Project Structure

```
api/
├── models.py              # Database models
├── serializers/           # DRF serializers
│   └── stock_serializers.py
├── views/                 # API views
│   ├── top_movers_view.py
│   ├── news_buzz_view.py
│   ├── sentiment_movers_view.py
│   ├── stocks_view.py
│   ├── news_view.py
│   ├── sentiment_view.py
│   └── stock_details_view.py
└── services/              # External API services
    ├── stock_api_service.py
    ├── news_service.py
    └── sentiment_service.py
```

## Development Notes

- The backend uses SQLite by default (suitable for development)
- For production, consider using PostgreSQL
- CORS is enabled for all origins in development (configure properly for production)
- Sentiment analysis can be done with simple keyword matching or OpenAI API
- News articles are cached in the database to reduce API calls

## License

MIT

