import pandas as pd
import numpy as np
import torch
from transformers import BertTokenizer, BertModel
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib

# Initialize BERT
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
bert_model = BertModel.from_pretrained('bert-base-uncased').to('cuda')  # GPU acceleration

def get_bert_embeddings(texts, batch_size=32):
    """Generate BERT embeddings for text analysis"""
    # Convert pandas Series to list if necessary
    if isinstance(texts, pd.Series):
        texts = texts.tolist()
    elif isinstance(texts, str):
        texts = [texts]
    
    all_embeddings = []
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i + batch_size]
        
        inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=256,
            return_tensors="pt"
        ).to('cuda')
        
        with torch.no_grad(), torch.amp.autocast('cuda'):  # Updated autocast syntax
            outputs = bert_model(**inputs)
            batch_embeddings = outputs.last_hidden_state[:,0,:].cpu().numpy()
            all_embeddings.append(batch_embeddings)
            
        # Clear CUDA cache after each batch
        torch.cuda.empty_cache()
    
    return np.vstack(all_embeddings)

# Load data ------------------------------------------------------------
real = pd.read_csv("True.csv")
fake = pd.read_csv("Fake.csv")
df = pd.concat([real.assign(label=1), fake.assign(label=0)])
df['text'] = df['text'].str.replace(r'http\S+|[^a-zA-Z\s]', '', regex=True)

# Train-test split -----------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    df['text'], df['label'], test_size=0.2, random_state=42
)

# Generate embeddings --------------------------------------------------
print("Generating embeddings for training data...")
X_train_emb = get_bert_embeddings(X_train)
print("Generating embeddings for test data...")
X_test_emb = get_bert_embeddings(X_test)

# Train classifier -----------------------------------------------------
print("Training classifier...")
clf = LogisticRegression(max_iter=1000, n_jobs=-1)  # Use all CPU cores
clf.fit(X_train_emb, y_train)

# Save artifacts -------------------------------------------------------
joblib.dump(clf, "bert_fake_news_model.pkl")