Setup Backend:

cd path\to\fake-news-detector\backend

Install Dependencies:
pip install -r requirements.txt

Train the Model:
python model.py
(This will generate fake_news_model.pkl and tfidf_vectorizer.pkl)

Start Flask Server:
python app.py

Expected Output:
* Running on http://127.0.0.1:5000/

Setup Frontend:

Open a New Command Prompt:
cd path\to\fake-news-detector\frontend

Install Dependencies:
npm install

Start React App:
npm start

Expected Output:
Local: http://localhost:3000

Use:
https://theonion.com/ for fake news to test the program. TheOnion is a popular satirical news publication that creates humorously exaggerated and outlandish news stories. It's known 
for its dry, sarcastic tone and often features stories about current events, pop culture, and political issues, presented in a way that's both absurd and self-aware

https://www.reuters.com/ for real news to test the program.

trained it on the Kaggle Fake and Real News Dataset, it works best for short-form news articles similar to those in the dataset (e.g., political/news content from 2015–2018)