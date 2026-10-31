
from pathlib import Path

project = Path(__file__).resolve().parent
routing_file = project / "backend" / "routing.py"

code = r'''
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "it_support_tickets_v2.csv"

# Build routing rules from the approved dataset mapping
df = pd.read_csv(DATA_PATH)

required = {"category", "assigned_group"}
if not required.issubset(df.columns):
    raise ValueError("Dataset must contain category and assigned_group.")

mapping_df = df.dropna(
    subset=["category", "assigned_group"]
)

mapping_counts = mapping_df.groupby(
    "category"
)["assigned_group"].nunique()

if (mapping_counts > 1).any():
    raise ValueError(
        "Some categories map to multiple support groups. "
        "Please define routing rules manually."
    )

CATEGORY_TO_TEAM = (
    mapping_df.groupby("category")["assigned_group"]
    .first()
    .to_dict()
)


def route_ticket(category):
    if category not in CATEGORY_TO_TEAM:
        return {
            "assigned_group": "Manual Review",
            "routing_status": "MANUAL_REVIEW"
        }

    return {
        "assigned_group": CATEGORY_TO_TEAM[category],
        "routing_status": "ROUTED"
    }


if __name__ == "__main__":
    print("\nCATEGORY TO SUPPORT TEAM MAPPING")
    print("=" * 45)

    for category, team in CATEGORY_TO_TEAM.items():
        print(f"{category} --> {team}")

    print("\nRouting test:")
    print(route_ticket("Network"))
'''

routing_file.write_text(code, encoding="utf-8")

print("Created:", routing_file)
print("Support team routing module is ready.")
