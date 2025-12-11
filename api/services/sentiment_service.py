import os
from typing import Dict


class SentimentService:
    
    def __init__(self):
        self.use_finbert = os.getenv('USE_FINBERT', 'true').lower() == 'true'
        
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
        if not text:
            return {'sentiment': 'Neutral'}
        
        if not self.finbert_available:
            return {'sentiment': 'Neutral'}
        
        try:
            sentiment = self._finbert_predict(text)
            return {'sentiment': sentiment}
        except Exception as e:
            print(f"Error analyzing sentiment: {str(e)}")
            return {'sentiment': 'Neutral'}

