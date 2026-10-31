
from pathlib import Path
import subprocess
import sys

project = Path(__file__).resolve().parent
data_file = project / "data" / "it_support_tickets_v2.csv"
train_file = project / "ml_engine" / "train.py"

if not data_file.exists():
    raise FileNotFoundError(
        f"Dataset not found: {data_file}\n"
        "Place it inside the project's data folder."
    )

train_code = r'''
from pathlib import Path
import json
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay
)

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "it_support_tickets_v2.csv"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)

print("Loading dataset...")
df = pd.read_csv(DATA_PATH)

# Keep only rows with valid text and category labels
df = df.dropna(subset=["ticket_text", "category"]).copy()
df["ticket_text"] = df["ticket_text"].astype(str).str.strip()
df = df[df["ticket_text"] != ""]

X = df["ticket_text"]
y = df["category"]

print("\nDataset shape:", df.shape)
print("\nCategory distribution:")
print(y.value_counts())

# Stratified split preserves category proportions
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# TF-IDF + Logistic Regression pipeline
model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=20000,
        min_df=1,
        sublinear_tf=True
    )),
    ("classifier", LogisticRegression(
        max_iter=2000,
        random_state=42
    ))
])

print("\nTraining model...")
model.fit(X_train, y_train)

print("Evaluating model...")
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)
report = classification_report(
    y_test,
    predictions,
    output_dict=True,
    zero_division=0
)

print("\n========== MODEL RESULTS ==========")
print(f"Accuracy: {accuracy:.4f}")
print("\nClassification Report:")
print(classification_report(y_test, predictions, zero_division=0))

# Save complete pipeline
joblib.dump(model, MODEL_DIR / "ticket_classifier.joblib")

# Save evaluation report
with open(MODEL_DIR / "evaluation_report.json", "w") as f:
    json.dump({
        "accuracy": accuracy,
        "classification_report": report,
        "train_samples": len(X_train),
        "test_samples": len(X_test)
    }, f, indent=4)

# Save confusion matrix image
labels = sorted(y.unique())
cm = confusion_matrix(y_test, predictions, labels=labels)

display = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=labels
)

fig, ax = plt.subplots(figsize=(10, 8))
display.plot(ax=ax, xticks_rotation=45, cmap="Blues", colorbar=False)
plt.title("IT Support Ticket Classification - Confusion Matrix")
plt.tight_layout()
plt.savefig(MODEL_DIR / "confusion_matrix.png", dpi=300)
plt.close()

# Save test predictions for inspection
results = pd.DataFrame({
    "ticket_text": X_test.values,
    "actual_category": y_test.values,
    "predicted_category": predictions
})
results.to_csv(MODEL_DIR / "test_predictions.csv", index=False)

print("\nTraining completed successfully!")
print("Saved files in:", MODEL_DIR)
print("- ticket_classifier.joblib")
print("- evaluation_report.json")
print("- confusion_matrix.png")
print("- test_predictions.csv")
'''

train_file.write_text(train_code, encoding="utf-8")
print("Created:", train_file)

print("\nStarting model training...\n")
subprocess.run([sys.executable, str(train_file)], check=True)
