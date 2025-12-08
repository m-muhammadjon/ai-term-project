# API Keys Setup Guide

This guide provides step-by-step instructions for obtaining API keys for the Market Research Analysis backend.

## Stock Market Data APIs

### 1. Alpha Vantage API (Primary - Recommended)

**What it provides:**
- Real-time stock quotes
- Historical price data
- Company information
- Market data

**How to get API key:**

1. **Visit Alpha Vantage website:**
   - Go to: https://www.alphavantage.co/support/#api-key

2. **Sign up for free account:**
   - Click on "Get Free API Key"
   - Fill in the registration form:
     - First Name
     - Last Name
     - Email Address
     - Organization (optional)
   - Accept the terms and conditions
   - Click "GET FREE API KEY"

3. **Get your API key:**
   - After registration, you'll receive an email with your API key
   - Or log in to your account dashboard to view your API key
   - Your API key will look like: `ABC123XYZ456`

4. **API Limits (Free Tier):**
   - 5 API calls per minute
   - 500 API calls per day
   - For higher limits, consider upgrading to a premium plan

5. **Add to your `.env` file:**
   ```bash
   ALPHA_VANTAGE_API_KEY=your_api_key_here
   ```

**Alternative: Yahoo Finance API (No Key Required)**
- The backend automatically falls back to Yahoo Finance API if Alpha Vantage key is not provided
- No registration needed
- Free and unlimited (but may have rate limits)
- Less reliable than Alpha Vantage for production use

---

## News APIs

### 2. NewsAPI (Recommended for News)

**What it provides:**
- Financial news articles
- News from multiple sources
- News filtering and search

**How to get API key:**

1. **Visit NewsAPI website:**
   - Go to: https://newsapi.org/

2. **Sign up for free account:**
   - Click "Get API Key" button
   - Fill in the registration form:
     - Email address
     - Password
     - Name
   - Verify your email address

3. **Get your API key:**
   - After email verification, log in to your account
   - Navigate to "API Keys" section
   - Copy your API key
   - Your API key will look like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

4. **API Limits (Free Tier):**
   - 100 requests per day
   - Development use only (not for commercial use)
   - For commercial use, upgrade to a paid plan

5. **Add to your `.env` file:**
   ```bash
   NEWS_API_KEY=your_api_key_here
   ```

---

### 3. Twitter API (Optional - for Twitter news)

**What it provides:**
- Real-time tweets about stocks
- Social sentiment data
- Trending topics

**How to get Bearer Token:**

1. **Visit Twitter Developer Portal:**
   - Go to: https://developer.twitter.com/

2. **Apply for Developer Account:**
   - Click "Sign up" or "Apply"
   - Log in with your Twitter account
   - Fill out the developer application:
     - Explain your use case (e.g., "Building a financial news aggregation app")
     - Accept terms and conditions
   - Wait for approval (usually takes a few hours to a few days)

3. **Create a Project and App:**
   - Once approved, go to the Developer Portal
   - Click "Create Project"
   - Fill in project details
   - Create an App within the project

4. **Get Bearer Token:**
   - Go to your App settings
   - Navigate to "Keys and Tokens" tab
   - Under "Bearer Token", click "Generate"
   - Copy the Bearer Token (starts with `AAAAAAAAAAAAAAAAAAAAA...`)

5. **API Limits:**
   - Free tier: 1,500 tweets per month
   - Rate limits apply (varies by endpoint)
   - For higher limits, upgrade to paid tier

6. **Add to your `.env` file:**
   ```bash
   TWITTER_BEARER_TOKEN=your_bearer_token_here
   ```

**Note:** Twitter API access can be restricted. If you don't have access, the backend will work without it using other news sources.

---

## Sentiment Analysis API

### 4. OpenAI API (Optional - for Advanced Sentiment Analysis)

**What it provides:**
- Advanced AI-powered sentiment analysis
- More accurate than keyword-based analysis
- Context-aware sentiment detection

**How to get API key:**

1. **Visit OpenAI website:**
   - Go to: https://platform.openai.com/

2. **Sign up for account:**
   - Click "Sign up"
   - Create an account with email or Google/Microsoft account
   - Verify your email

3. **Add payment method:**
   - OpenAI requires a payment method (even for free tier)
   - Go to "Billing" → "Payment methods"
   - Add a credit card (you'll get $5 free credit to start)

4. **Get API key:**
   - Go to "API Keys" section
   - Click "Create new secret key"
   - Give it a name (e.g., "Market Research API")
   - Copy the API key immediately (you won't be able to see it again)
   - Your API key will look like: `sk-...`

5. **API Pricing:**
   - Pay-as-you-go pricing
   - GPT-3.5-turbo: ~$0.001 per request
   - Free $5 credit to start

6. **Add to your `.env` file:**
   ```bash
   OPENAI_API_KEY=your_api_key_here
   USE_EXTERNAL_SENTIMENT_API=true
   ```

**Alternative: Built-in Keyword Analysis (No Key Required)**
- The backend includes a simple keyword-based sentiment analyzer
- Works without any API key
- Less accurate but free and unlimited
- Set `USE_EXTERNAL_SENTIMENT_API=false` or leave it unset

---

## Complete .env File Example

Create a `.env` file in your project root with all your API keys:

```bash
# Stock Market API
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here

# News API
NEWS_API_KEY=your_news_api_key_here

# Twitter API (Optional)
TWITTER_BEARER_TOKEN=your_twitter_bearer_token_here

# OpenAI API (Optional - for advanced sentiment analysis)
OPENAI_API_KEY=your_openai_api_key_here
USE_EXTERNAL_SENTIMENT_API=false
```

---

## Testing Your API Keys

After setting up your API keys, test them:

1. **Start the Django server:**
   ```bash
   python manage.py runserver
   ```

2. **Test endpoints:**
   - Visit: http://localhost:8000/api/docs/ to see the API documentation
   - Try the `/topMovers` endpoint to test stock API
   - Try the `/news` endpoint to test news API

3. **Check logs:**
   - If API calls fail, check the console output for error messages
   - Common issues:
     - Invalid API key
     - Rate limit exceeded
     - Network connectivity issues

---

## Important Notes

1. **Never commit your `.env` file to version control**
   - The `.gitignore` file already excludes `.env`
   - Keep your API keys secret

2. **API Rate Limits:**
   - Be aware of rate limits for each service
   - The backend caches data in the database to reduce API calls
   - Consider implementing additional caching for production

3. **Free Tier Limitations:**
   - Most free tiers have daily/monthly limits
   - For production use, consider upgrading to paid plans
   - Monitor your API usage

4. **Fallback Mechanisms:**
   - The backend works without API keys using free alternatives
   - Yahoo Finance for stocks (no key needed)
   - Keyword-based sentiment analysis (no key needed)
   - Some features may be limited without API keys

---

## Troubleshooting

**Problem: API key not working**
- Verify the key is correct (no extra spaces)
- Check if the key is active in the provider's dashboard
- Ensure you're using the correct environment variable name

**Problem: Rate limit exceeded**
- Wait for the rate limit window to reset
- Implement caching to reduce API calls
- Consider upgrading to a paid plan

**Problem: API service unavailable**
- Check the provider's status page
- Verify your internet connection
- The backend will fall back to alternative services when possible

---

## Support

For issues with:
- **Alpha Vantage**: https://www.alphavantage.co/support/
- **NewsAPI**: https://newsapi.org/docs
- **Twitter API**: https://developer.twitter.com/en/docs
- **OpenAI API**: https://platform.openai.com/docs

