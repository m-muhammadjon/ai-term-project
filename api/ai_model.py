"""
FinBERT model for financial sentiment analysis
"""
from transformers import BertForSequenceClassification, AutoTokenizer
import torch
from pathlib import Path

# Get the absolute path to the model directory
# This file is in api/, and the model is in api/my_finbert/
BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "my_finbert"
MODEL_DIR_STR = str(MODEL_DIR)

# Lazy loading - only load model when needed
_tokenizer = None
_model = None

# Map model predictions to our sentiment labels
# FinBERT: 0=negative, 1=neutral, 2=positive
# Our labels: Bullish, Bearish, Neutral
LABEL_MAP = {0: "Bearish", 1: "Neutral", 2: "Bullish"}


def _load_model():
    """Load the model and tokenizer (lazy loading)"""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR_STR, local_files_only=True)
        _model = BertForSequenceClassification.from_pretrained(MODEL_DIR_STR, local_files_only=True)
        _model.eval()  # Set to evaluation mode
    return _tokenizer, _model


def predict_sentiment(text, max_length=512):
    """
    Predict sentiment using FinBERT model
    
    Args:
        text: Input text to analyze
        max_length: Maximum sequence length (default: 512)
    
    Returns:
        str: Sentiment label ("Bullish", "Bearish", or "Neutral")
    """
    if not text or not text.strip():
        return "Neutral"
    
    try:
        tokenizer, model = _load_model()
        
        # Tokenize input
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=max_length
        )
        
        # Predict
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            predicted_class = torch.argmax(logits, dim=1).item()
        
        # Map to our sentiment labels
        return LABEL_MAP.get(predicted_class, "Neutral")
    
    except Exception as e:
        # Fallback to Neutral on any error
        print(f"Error in sentiment prediction: {str(e)}")
        return "Neutral"


# For testing purposes
if __name__ == "__main__":
    test_headlines = [
        "Apple reports strong Q4 revenue beating expectations",
        "Stock market crashes as investors panic",
        "Company announces quarterly earnings report"
    ]
    
    for headline in test_headlines:
        sentiment = predict_sentiment(headline)
        print(f"'{headline}' -> {sentiment}")