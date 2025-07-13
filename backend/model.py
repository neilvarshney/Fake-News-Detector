# data manipulation
import pandas as pd
import numpy as np

# deep learning operations
import torch

# BERT model
from transformers import BertTokenizer, BertModel
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

# for saving the trainedmodel
import joblib

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt

# Initialize BERT. Load pre-tained BERT model that understands English text
tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
bert_model = BertModel.from_pretrained('bert-base-uncased').to('cuda')  # GPU acceleration

# Conerts text into numerical representations (embeddings) that the model can understand.
def get_bert_embeddings(texts, batch_size=32):

    # Convert pandas Series to list if necessary
    if isinstance(texts, pd.Series):
        texts = texts.tolist()
    elif isinstance(texts, str):
        texts = [texts]
    
    all_embeddings = []
    
    # Process in batches of 32
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

# combines the real and fake news dataframes and adds a label column. 1 for real, 0 for fake
df = pd.concat([real.assign(label=1), fake.assign(label=0)])

# removes URLs and non-alphabetic characters from the text
df['text'] = df['text'].str.replace(r'http\S+|[^a-zA-Z\s]', '', regex=True)

# Train-test split -----------------------------------------------------
# splits the data into training and testing sets. 20% of the data is used for testing
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


# get stats
y_pred = clf.predict(X_test_emb)
y_pred_proba = clf.predict_proba(X_test_emb)[:, 1]

# Calculate key metrics
accuracy = accuracy_score(y_test, y_pred)
precision = precision_score(y_test, y_pred)
recall = recall_score(y_test, y_pred)
f1 = f1_score(y_test, y_pred)

print(f"Accuracy: {accuracy:.3f}")
print(f"Precision: {precision:.3f}")
print(f"Recall: {recall:.3f}")
print(f"F1-Score: {f1:.3f}")

# Save artifacts -------------------------------------------------------
joblib.dump(clf, "bert_fake_news_model.pkl")