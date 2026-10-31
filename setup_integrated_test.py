
from pathlib import Path

project = Path(__file__).resolve().parent
test_file = project / "ml_engine" / "test_system.py"

code = r'''
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
        routing = route_ticket(
            prediction["predicted_category"]
        )

        print("\nPREDICTION")
        print("-" * 30)
        print("Category:", prediction["predicted_category"])
        print("Confidence:", prediction["confidence_percentage"], "%")
        print("Decision:", prediction["decision"])

        print("\nROUTING")
        print("-" * 30)
        print("Assigned group:", routing["assigned_group"])
        print("Routing status:", routing["routing_status"])

        if prediction["decision"] == "MANUAL_REVIEW":
            print("\nAction: Send ticket for manual review.")

    except ValueError as error:
        print("Error:", error)
'''

test_file.write_text(code, encoding="utf-8")
print("Created:", test_file)


test_file.write_text(code, encoding="utf-8")
print("Created:", test_file)

