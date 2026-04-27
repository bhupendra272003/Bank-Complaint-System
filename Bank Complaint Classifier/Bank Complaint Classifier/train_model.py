import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle

# Sample banking complaints data
data = {
    "complaint": [
        "mera card block karo transaction unauthorized hai",
        "loan interest bahut zyada hai",
        "ATM se paise nahi nikle",
        "maine paise transfer kiye lekin nahi pahunche",
        "credit card bill galat aaya hai",
        "fraud transaction hui mere account se",
        "personal loan chahiye",
        "account mein paise deduct hue lekin transaction fail"
    ],
    "category": [
        "fraud",
        "loan",
        "atm",
        "transfer",
        "billing",
        "fraud",
        "loan",
        "transfer"
    ]
}

df = pd.DataFrame(data)

# Convert text to numbers (TF-IDF)
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df["complaint"])
y = df["category"]

# Train model
model = MultinomialNB()
model.fit(X, y)

# Save model and vectorizer
pickle.dump(model, open("model.pkl", "wb"))
pickle.dump(vectorizer, open("vectorizer.pkl", "wb"))

print("✅ Model trained and saved successfully!")