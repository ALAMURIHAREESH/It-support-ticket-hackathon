
from pathlib import Path

project = Path(__file__).resolve().parent
predict_file = project / "ml_engine" / "predict.py"

code = r'''
from pathlib import Path
import joblib

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "models" / "ticket_classifier.joblib"

CONFIDENCE_THRESHOLD = 0.70

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        "Trained model not found. Run the training script first."
    )

model = joblib.load(MODEL_PATH)


def predict_ticket(ticket_text):
    if not isinstance(ticket_text, str) or not ticket_text.strip():
        raise ValueError("Please enter a valid ticket description.")

    probabilities = model.predict_proba([ticket_text])[0]
    classes = model.classes_

    best_index = probabilities.argmax()

    predicted_category = classes[best_index]
    confidence = float(probabilities[best_index])

    if confidence >= CONFIDENCE_THRESHOLD:
        decision = "AUTO_CLASSIFY"
    else:
        decision = "MANUAL_REVIEW"

    all_probabilities = {
        str(category): round(float(probability), 4)
        for category, probability in zip(classes, probabilities)
    }

    return {
        "ticket_text": ticket_text,
        "predicted_category": str(predicted_category),
        "confidence": round(confidence, 4),
        "confidence_percentage": round(confidence * 100, 2),
        "decision": decision,
        "category_probabilities": all_probabilities
    }


if __name__ == "__main__":

    print("\nIT SUPPORT TICKET PREDICTION SYSTEM")
    print("=" * 45)

    while True:
        ticket = input("\nEnter ticket description (or type exit): ")

        if ticket.strip().lower() == "exit":
            break

        try:
            result = predict_ticket(ticket)

            print("\nPrediction Result")
            print("-" * 35)
            print("Category:", result["predicted_category"])
            print("Confidence:", result["confidence_percentage"], "%")
            print("Decision:", result["decision"])

            print("\nCategory probabilities:")
            for category, probability in result["category_probabilities"].items():
                print(f"{category}: {probability * 100:.2f}%")

        except ValueError as error:
            print("Error:", error)
'''

predict_file.write_text(code, encoding="utf-8")

print("Created:", predict_file)
print("Prediction module is ready.")
