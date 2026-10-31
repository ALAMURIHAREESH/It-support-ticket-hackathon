
from pathlib import Path
import joblib
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent.parent

MODEL_PATH = ROOT / "models" / "ticket_classifier.joblib"
OPEN_SET_PATH = ROOT / "models" / "open_set_artifacts.joblib"

CONFIDENCE_THRESHOLD = 0.70

if not MODEL_PATH.exists() or not OPEN_SET_PATH.exists():
    raise FileNotFoundError(
        "Model or open-set artifacts missing. Run ml_engine/train.py first."
    )

model = joblib.load(MODEL_PATH)
open_set = joblib.load(OPEN_SET_PATH)

reference_vectors = open_set["reference_vectors"]
SIMILARITY_THRESHOLD = open_set["similarity_threshold"]

vectorizer = model.named_steps["tfidf"]

IT_KEYWORDS = {
    "laptop", "computer", "desktop", "pc", "monitor",
    "keyboard", "mouse", "printer", "print", "camera",
    "microphone", "speaker", "hardware", "wifi", "wireless",
    "network", "internet", "vpn", "router", "server",
    "connection", "email", "outlook", "teams", "software",
    "application", "app", "windows", "linux", "mac",
    "password", "login", "signin", "account", "access",
    "permission", "database", "file", "folder", "drive",
    "cloud", "browser", "website", "system", "storage",
    "disk", "usb", "screen", "display", "boot", "crash",
    "error", "update", "install", "installation", "malware",
    "security", "antivirus", "slow", "hang", "freeze",
    "restart", "shutdown", "power", "charger", "battery",
    "backup", "sharepoint", "office", "excel", "word",
    "cannot", "unable", "failed", "failure", "not working",
    "issue", "problem", "broken", "disconnect", "disconnecting"
}

GENERIC_GREETINGS = {
    "hi", "hello", "hey", "good morning",
    "good afternoon", "good evening",
    "how are you", "how are you doing",
    "thank you", "thanks", "ok", "okay"
}


def validate_ticket(ticket_text):
    if not isinstance(ticket_text, str):
        raise ValueError("Please enter a valid IT support description.")

    text = " ".join(ticket_text.strip().lower().split())

    if not text:
        raise ValueError("Ticket description cannot be empty.")

    if text.strip(" .,!?") in GENERIC_GREETINGS:
        raise ValueError(
            "This is a greeting, not an IT support ticket. "
            "Please describe your technical issue."
        )

    words = re.findall(r"[a-zA-Z0-9]+", text)

    if len(words) < 3:
        raise ValueError(
            "Please provide at least three words describing your IT issue."
        )

    # Basic relevance check. This is a guardrail, not a perfect IT detector.
    has_it_keyword = any(
        keyword in text for keyword in IT_KEYWORDS
    )

    if not has_it_keyword:
        raise ValueError(
            "We could not identify an IT-related issue. "
            "Please describe a hardware, software, network, "
            "email, access, database or security problem."
        )

    return text


def predict_ticket(ticket_text):
    clean_text = validate_ticket(ticket_text)

    # Classification
    probabilities = model.predict_proba([clean_text])[0]
    classes = model.classes_
    best_index = int(np.argmax(probabilities))

    predicted_category = str(classes[best_index])
    confidence = float(probabilities[best_index])

    # Similarity to the training examples
    query_vector = vectorizer.transform([clean_text])
    similarities = cosine_similarity(
        query_vector, reference_vectors
    )[0]

    max_similarity = float(similarities.max())

    # Detect potentially unfamiliar IT tickets
    if max_similarity < SIMILARITY_THRESHOLD:
        decision = "MANUAL_REVIEW"
        issue_status = "POTENTIALLY_UNSEEN_IT_ISSUE"
        explanation = (
            "This appears to be an IT-related ticket, but it differs "
            "from the training examples. Human review is required."
        )

    elif confidence < CONFIDENCE_THRESHOLD:
        decision = "MANUAL_REVIEW"
        issue_status = "KNOWN_DOMAIN_UNCERTAIN_CATEGORY"
        explanation = (
            "The ticket resembles known IT examples, but the model "
            "is not sufficiently confident about its category."
        )

    else:
        decision = "AUTO_CLASSIFY"
        issue_status = "KNOWN_ISSUE_CANDIDATE"
        explanation = (
            "The ticket resembles training examples and has sufficient "
            "classification confidence."
        )

    category_probabilities = {
        str(category): round(float(probability), 4)
        for category, probability in zip(classes, probabilities)
    }

    return {
        "ticket_text": clean_text,
        "predicted_category": predicted_category,
        "confidence": round(confidence, 4),
        "confidence_percentage": round(confidence * 100, 2),
        "similarity": round(max_similarity, 4),
        "similarity_threshold": round(
            float(SIMILARITY_THRESHOLD), 4
        ),
        "decision": decision,
        "issue_status": issue_status,
        "explanation": explanation,
        "category_probabilities": category_probabilities
    }


if __name__ == "__main__":
    print("\nOPEN-SET IT SUPPORT CLASSIFIER")
    print("Similarity threshold:", round(SIMILARITY_THRESHOLD, 4))

    while True:
        ticket = input("\nEnter ticket (or exit): ")

        if ticket.strip().lower() == "exit":
            break

        try:
            result = predict_ticket(ticket)

            print("\nPredicted category:", result["predicted_category"])
            print("Confidence:", result["confidence_percentage"], "%")
            print("Similarity:", result["similarity"])
            print("Decision:", result["decision"])
            print("Issue status:", result["issue_status"])
            print("Explanation:", result["explanation"])

        except ValueError as error:
            print("\nINVALID INPUT:", error)
