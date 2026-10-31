
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ml_engine.predict import predict_ticket
from backend.routing import route_ticket

print("\nIT SUPPORT INTELLIGENCE SYSTEM")
print("=" * 45)

while True:
    ticket = input("\nEnter ticket description (or exit): ")

    if ticket.strip().lower() == "exit":
        break

    try:
        prediction = predict_ticket(ticket)

        print("\nPREDICTION")
        print("-" * 30)
        print("Category:", prediction["predicted_category"])
        print("Confidence:", prediction["confidence_percentage"], "%")
        print("Decision:", prediction["decision"])

        if prediction["decision"] == "AUTO_CLASSIFY":

            routing = route_ticket(
                prediction["predicted_category"]
            )

            print("\nROUTING")
            print("-" * 30)
            print("Assigned group:", routing["assigned_group"])
            print("Routing status:", routing["routing_status"])

        else:
            print("\nMANUAL REVIEW")
            print("-" * 30)
            print("Assigned group: Pending human review")
            print("Routing status: NOT_ROUTED")
            print("Action: Human verification required.")

    except ValueError as error:
        print("Error:", error)

