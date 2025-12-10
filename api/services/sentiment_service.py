"""
Service for sentiment analysis of news articles
"""
import os
import requests
from typing import Dict, Optional
from django.conf import settings


class SentimentService:
    """Service to analyze sentiment of news articles"""
    
    def __init__(self):
        # Priority order:
        # 1. FinBERT model (local, best for financial text)
        # 2. OpenAI API (if enabled and key provided)
        # 3. Simple keyword-based algorithm (fallback)
        
        self.use_external_api = os.getenv('USE_EXTERNAL_SENTIMENT_API', 'false').lower() == 'true'
        self.use_finbert = os.getenv('USE_FINBERT', 'true').lower() == 'true'
        
        # OpenAI API for advanced sentiment analysis (optional)
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
        self.openai_base_url = 'https://api.openai.com/v1'
        
        # Try to load FinBERT model
        self.finbert_available = False
        if self.use_finbert:
            try:
                from api.ai_model import predict_sentiment as finbert_predict
                self._finbert_predict = finbert_predict
                self.finbert_available = True
            except Exception as e:
                print(f"FinBERT model not available: {str(e)}")
                self.finbert_available = False
    
    def analyze_sentiment(self, text: str) -> Dict[str, str]:
        """
        Analyze sentiment of text
        Returns: {'sentiment': 'Bullish' | 'Bearish' | 'Neutral'}
        """
        if not text:
            return {'sentiment': 'Neutral'}
        
        try:
            # Try FinBERT first (best for financial text)
            if self.finbert_available:
                sentiment = self._finbert_predict(text)
                return {'sentiment': sentiment}
            
            # Fallback to OpenAI if enabled
            if self.use_external_api and self.openai_api_key:
                return self._analyze_with_openai(text)
            
            # Fallback to simple keyword-based algorithm
            return self._analyze_with_simple_algorithm(text)
            
        except Exception as e:
            print(f"Error analyzing sentiment: {str(e)}")
            # Try fallback methods
            try:
                if self.use_external_api and self.openai_api_key:
                    return self._analyze_with_openai(text)
            except:
                pass
            return self._analyze_with_simple_algorithm(text)
    
    def _analyze_with_openai(self, text: str) -> Dict[str, str]:
        """Analyze sentiment using OpenAI API"""
        headers = {
            'Authorization': f'Bearer {self.openai_api_key}',
            'Content-Type': 'application/json'
        }
        
        prompt = f"""Analyze the sentiment of this financial news text and classify it as Bullish, Bearish, or Neutral.
        
Text: {text[:1000]}
        
Respond with only one word: Bullish, Bearish, or Neutral."""
        
        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are a financial sentiment analyzer. Respond with only one word: Bullish, Bearish, or Neutral.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 10,
            'temperature': 0.3
        }
        
        response = requests.post(
            f"{self.openai_base_url}/chat/completions",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            sentiment_text = result['choices'][0]['message']['content'].strip()
            sentiment = sentiment_text.split()[0] if sentiment_text else 'Neutral'
            
            if sentiment in ['Bullish', 'Bearish', 'Neutral']:
                return {'sentiment': sentiment}
        
        return {'sentiment': 'Neutral'}
    
    def _analyze_with_simple_algorithm(self, text: str) -> Dict[str, str]:
        """
        Simple keyword-based sentiment analysis
        For production, consider using NLTK, TextBlob, or VADER
        """
        text_lower = text.lower()
        
        # Bullish keywords
        bullish_keywords = [
            'surge', 'rally', 'gain', 'rise', 'up', 'bullish', 'buy', 'outperform',
            'growth', 'profit', 'earnings beat', 'upgrade', 'positive', 'strong',
            'momentum', 'breakthrough', 'success', 'win', 'soar', 'jump', 'climb',
            'increase', 'expand', 'boom', 'thrive', 'excel', 'outperform'
        ]
        
        # Bearish keywords
        bearish_keywords = [
            'drop', 'fall', 'decline', 'down', 'bearish', 'sell', 'underperform',
            'loss', 'earnings miss', 'downgrade', 'negative', 'weak', 'crash',
            'plunge', 'tumble', 'slump', 'decrease', 'shrink', 'struggle', 'fail',
            'concern', 'risk', 'worry', 'fear', 'uncertainty', 'volatility'
        ]
        
        bullish_count = sum(1 for keyword in bullish_keywords if keyword in text_lower)
        bearish_count = sum(1 for keyword in bearish_keywords if keyword in text_lower)
        
        # Determine sentiment
        if bullish_count > bearish_count + 1:
            return {'sentiment': 'Bullish'}
        elif bearish_count > bullish_count + 1:
            return {'sentiment': 'Bearish'}
        else:
            return {'sentiment': 'Neutral'}

