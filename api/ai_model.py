from transformers import BertForSequenceClassification, AutoTokenizer
import torch
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR / "my_finbert"
MODEL_DIR_STR = str(MODEL_DIR)

_tokenizer = None
_model = None

LABEL_MAP = {0: "Bearish", 1: "Neutral", 2: "Bullish"}


def _load_model():
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR_STR, local_files_only=True)
        _model = BertForSequenceClassification.from_pretrained(MODEL_DIR_STR, local_files_only=True)
        _model.eval()
    return _tokenizer, _model


def predict_sentiment(text, max_length=512):
    if not text or not text.strip():
        return "Neutral"
    
    try:
        tokenizer, model = _load_model()
        
        inputs = tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            max_length=max_length
        )
        
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            predicted_class = torch.argmax(logits, dim=1).item()
        
        return LABEL_MAP.get(predicted_class, "Neutral")
    
    except Exception as e:
        print(f"Error in sentiment prediction: {str(e)}")
        return "Neutral"


if __name__ == "__main__":
    test_headlines = [
        "Apple reports strong Q4 revenue beating expectations",
        "Stock market crashes as investors panic",
        "Company announces quarterly earnings report"
    ]
    
    for headline in test_headlines:
        sentiment = predict_sentiment(headline)
        print(f"'{headline}' -> {sentiment}")