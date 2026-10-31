
from pathlib import Path
import json
import joblib
import pandas as pd
import numpy as np

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
from sklearn.metrics.pairwise import cosine_similarity
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "it_support_tickets_cleaned.csv"
MODEL_DIR = ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)

print("Loading cleaned dataset...")
df = pd.read_csv(DATA_PATH)
df = df.dropna(subset=["ticket_text", "category"]).copy()
df["ticket_text"] = df["ticket_text"].astype(str).str.strip()
df = df[df["ticket_text"] != ""]

X = df["ticket_text"]
y = df["category"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42, stratify=y
)

model = Pipeline([
    ("tfidf", TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        max_features=20000,
        sublinear_tf=True
    )),
    ("classifier", LogisticRegression(
        max_iter=2000,
        random_state=42
    ))
])

print("Training classifier...")
model.fit(X_train, y_train)

predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)

print("\nAccuracy:", round(accuracy, 4))
print(classification_report(y_test, predictions, zero_division=0))

# Save the complete classification pipeline
joblib.dump(model, MODEL_DIR / "ticket_classifier.joblib")

# Build reference vectors using training tickets only
vectorizer = model.named_steps["tfidf"]
reference_vectors = vectorizer.transform(X_train)

# Calibrate similarity using held-out, known IT tickets.
# For each test ticket, find its closest training ticket.
test_vectors = vectorizer.transform(X_test)
similarities = cosine_similarity(test_vectors, reference_vectors)
nearest_similarities = similarities.max(axis=1)

# Conservative lower-bound threshold from known validation examples.
# This is an initial calibration, not a guarantee of unknown detection.
similarity_threshold = float(
    np.percentile(nearest_similarities, 5)
)

open_set_artifacts = {
    "reference_vectors": reference_vectors,
    "similarity_threshold": similarity_threshold,
    "calibration_percentile": 5
}

joblib.dump(
    open_set_artifacts,
    MODEL_DIR / "open_set_artifacts.joblib"
)

# Save evaluation report
report = classification_report(
    y_test, predictions, output_dict=True, zero_division=0
)

with open(MODEL_DIR / "evaluation_report.json", "w") as f:
    json.dump({
        "accuracy": accuracy,
        "classification_report": report,
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "similarity_threshold": similarity_threshold
    }, f, indent=4)

# Save confusion matrix
labels = sorted(y.unique())
cm = confusion_matrix(y_test, predictions, labels=labels)

display = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=labels
)

fig, ax = plt.subplots(figsize=(10, 8))
display.plot(ax=ax, xticks_rotation=45, cmap="Blues", colorbar=False)
plt.title("IT Support Classification Confusion Matrix")
plt.tight_layout()
plt.savefig(MODEL_DIR / "confusion_matrix.png", dpi=300)
plt.close()

# Save test predictions
pd.DataFrame({
    "ticket_text": X_test.values,
    "actual_category": y_test.values,
    "predicted_category": predictions,
    "nearest_training_similarity": nearest_similarities
}).to_csv(MODEL_DIR / "test_predictions.csv", index=False)

print("\nOpen-set calibration completed.")
print("Similarity threshold:", round(similarity_threshold, 4))
print("Saved model and open-set artifacts in:", MODEL_DIR)

