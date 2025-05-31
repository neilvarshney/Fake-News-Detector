import pandas as pd
import numpy as np
import torch
import time
from tqdm import tqdm  # For progress bars
from transformers import BertTokenizer, BertModel
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib

# Initialize BERT
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
bert_model = BertModel.from_pretrained('bert-base-uncased').to('cuda')  # GPU acceleration

def get_bert_embeddings(texts, batch_size=16):
    """Optimized embedding generator with progress tracking"""
    embeddings = []
    
    # Warm-up GPU
    dummy_input = tokenizer("warmup", return_tensors="pt").to('cuda')
    _ = bert_model(**dummy_input)
    
    print(f"\nGenerating embeddings for {len(texts)} articles (batch_size={batch_size})...")
    start_time = time.time()
    
    for i in tqdm(range(0, len(texts), batch_size), desc="Processing"):
        batch = texts[i:i+batch_size].tolist()
        
        # Tokenize on CPU -> Move to GPU
        inputs = tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=256,  # Optimal for RTX 2060 VRAM
            return_tensors="pt"
        ).to('cuda')
        
        with torch.no_grad(), torch.cuda.amp.autocast():  # Mixed precision
            outputs = bert_model(**inputs)
        
        # Move embeddings back to CPU to save VRAM
        batch_emb = outputs.last_hidden_state[:,0,:].cpu().numpy()
        embeddings.append(batch_emb)
    
    total_time = time.time() - start_time
    print(f"Embedding generation completed in {total_time/60:.1f} minutes")
    return np.vstack(embeddings)

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
X_train_emb = get_bert_embeddings(X_train)
X_test_emb = get_bert_embeddings(X_test)

# Train classifier -----------------------------------------------------
print("\nTraining classifier...")
clf = LogisticRegression(max_iter=1000, n_jobs=-1)  # Use all CPU cores
clf.fit(X_train_emb, y_train)

print(f"Test Accuracy: {clf.score(X_test_emb, y_test):.2%}")

# Save artifacts -------------------------------------------------------
joblib.dump(clf, "bert_fake_news_model.pkl")