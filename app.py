import streamlit as st
import pandas as pd
import plotly.express as px
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="IT Support Intelligence",
    page_icon="🎫",
    layout="wide"
)

# ---------------- API HELPERS ----------------

def api_get(endpoint, params=None):
    try:
        response = requests.get(
            f"{API_URL}{endpoint}",
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        st.error(f"Backend connection error: {error}")
        return None


def api_post(endpoint, payload):
    try:
        response = requests.post(
            f"{API_URL}{endpoint}",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        try:
            detail = response.json().get("detail", str(error))
        except Exception:
            detail = str(error)
        st.error(f"Request failed: {detail}")
        return None


def api_put(endpoint, payload):
    try:
        response = requests.put(
            f"{API_URL}{endpoint}",
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as error:
        try:
            detail = response.json().get("detail", str(error))
        except Exception:
            detail = str(error)
        st.error(f"Review failed: {detail}")
        return None


# ---------------- SIDEBAR ----------------

st.sidebar.title("🎫 IT Support Intelligence")
st.sidebar.caption("AI-powered ticket classification")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Submit Ticket",
        "All Tickets",
        "Manual Review"
    ]
)

health = api_get("/health")

if health and health.get("status") == "healthy":
    st.sidebar.success("Backend connected")
else:
    st.sidebar.error("Backend unavailable")


# ---------------- DASHBOARD ----------------

if page == "Dashboard":

    st.title("📊 IT Support Analytics Dashboard")
    st.caption("Overview of IT support operations and ticket classification")

    summary = api_get("/analytics/summary")
    categories = api_get("/analytics/categories")
    trends = api_get("/analytics/trends")

    if summary:

        c1, c2, c3, c4 = st.columns(4)

        c1.metric("Total Tickets", summary["total_tickets"])
        c2.metric("Routed Tickets", summary["routed_tickets"])
        c3.metric("Pending Review", summary["pending_manual_review"])
        c4.metric("SLA Breaches", summary["sla_breached_tickets"])

    st.divider()

    left, right = st.columns(2)

    if categories and categories["categories"]:
        category_df = pd.DataFrame(categories["categories"])

        with left:
            st.subheader("Tickets by Category")
            fig = px.pie(
                category_df,
                names="category",
                values="count",
                hole=0.45
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("Category-wise Ticket Volume")
            fig = px.bar(
                category_df,
                x="category",
                y="count",
                text="count"
            )
            fig.update_layout(xaxis_title="Category",
                              yaxis_title="Number of Tickets")
            st.plotly_chart(fig, use_container_width=True)

    if trends and trends["daily_ticket_counts"]:
        st.subheader("Daily Ticket Trends")

        trend_df = pd.DataFrame(trends["daily_ticket_counts"])
        trend_df["date"] = pd.to_datetime(trend_df["date"])

        fig = px.line(
            trend_df,
            x="date",
            y="count",
            markers=True,
            title="Daily Ticket Volume"
        )
        st.plotly_chart(fig, use_container_width=True)


# ---------------- SUBMIT TICKET ----------------

elif page == "Submit Ticket":

    st.title("🎫 Submit IT Support Ticket")
    st.write("Describe your technical issue below.")

    with st.form("ticket_form"):

        subject = st.text_input("Ticket Subject")

        ticket_text = st.text_area(
            "Describe your issue",
            placeholder="Example: My laptop is not turning on..."
        )

        c1, c2 = st.columns(2)

        with c1:
            priority = st.selectbox(
                "Priority",
                ["Low", "Medium", "High", "Critical"]
            )

            impact = st.selectbox(
                "Impact",
                ["Low", "Medium", "High"]
            )

        with c2:
            urgency = st.selectbox(
                "Urgency",
                ["Low", "Medium", "High"]
            )

            channel = st.selectbox(
                "Submission Channel",
                ["Web", "Email", "Phone", "Chat"]
            )

        submitted = st.form_submit_button(
            "Submit and Classify Ticket",
            type="primary"
        )

    if submitted:

        if len(ticket_text.strip()) < 5:
            st.warning("Please enter a more detailed ticket description.")

        else:
            payload = {
                "ticket_text": ticket_text,
                "subject": subject,
                "priority": priority,
                "impact": impact,
                "urgency": urgency,
                "channel": channel
            }

            with st.spinner("AI is analyzing your ticket..."):
                result = api_post("/tickets", payload)

            if result:

                st.success("Ticket submitted successfully!")

                st.subheader("AI Classification Result")

                a, b, c = st.columns(3)

                a.metric("Ticket ID", result["ticket_id"])
                b.metric("Predicted Category",
                         result["predicted_category"])
                c.metric("Confidence",
                         f'{result["confidence"]:.2f}%')

                if result["decision"] == "AUTO_CLASSIFY":
                    st.success("Automatically classified and routed.")
                else:
                    st.warning(
                        "Low-confidence prediction. "
                        "Ticket sent for manual review."
                    )

                st.write("**Assigned Support Group:**",
                         result["assigned_group"] or "Pending review")

                st.write("**Routing Status:**",
                         result["routing_status"])

                probability_df = pd.DataFrame(
                    list(result["category_probabilities"].items()),
                    columns=["Category", "Probability"]
                )

                st.subheader("Category Prediction Probabilities")

                fig = px.bar(
                    probability_df,
                    x="Category",
                    y="Probability",
                    text="Probability"
                )
                fig.update_layout(yaxis_tickformat=".0%")
                st.plotly_chart(fig, use_container_width=True)


# ---------------- ALL TICKETS ----------------

elif page == "All Tickets":

    st.title("📋 All Support Tickets")

    result = api_get("/tickets", params={"skip": 0, "limit": 500})

    if result and result["tickets"]:

        df = pd.DataFrame(result["tickets"])

        st.metric("Tickets displayed", len(df))

        if "decision" in df.columns:
            decisions = ["All"] + sorted(
                df["decision"].dropna().unique().tolist()
            )

            selected = st.selectbox("Filter by Decision", decisions)

            if selected != "All":
                df = df[df["decision"] == selected]

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

    elif result:
        st.info("No tickets found.")


# ---------------- MANUAL REVIEW ----------------

elif page == "Manual Review":

    st.title("📝 Manual Review Queue")
    st.caption("Verify tickets with low-confidence predictions.")

    result = api_get("/tickets", params={"skip": 0, "limit": 500})

    if result:

        df = pd.DataFrame(result["tickets"])

        if not df.empty:
            pending = df[
                df["review_status"] == "PENDING"
            ]

            st.metric("Pending Reviews", len(pending))

            if pending.empty:
                st.success("No tickets are waiting for manual review.")

            else:
                for _, ticket in pending.iterrows():

                    with st.expander(
                        f'{ticket["ticket_id"]} | '
                        f'{ticket["predicted_category"]}'
                    ):

                        st.write("**Ticket Description:**")
                        st.write(ticket["ticket_text"])

                        st.write(
                            "**Model Confidence:**",
                            f'{ticket["confidence"] * 100:.2f}%'
                            if pd.notna(ticket["confidence"])
                            else "Unavailable"
                        )

                        ticket_id = ticket["ticket_id"]

                        categories = [
                            "Access",
                            "Database",
                            "Email_Collaboration",
                            "Hardware",
                            "Network",
                            "Security",
                            "Software"
                        ]

                        selected_category = st.selectbox(
                            "Confirm or correct category",
                            categories,
                            index=(
                                categories.index(ticket["predicted_category"])
                                if ticket["predicted_category"] in categories
                                else 0
                            ),
                            key=f"category_{ticket_id}"
                        )

                        if st.button(
                            "Approve and Route",
                            key=f"approve_{ticket_id}"
                        ):

                            review_result = api_put(
                                f"/tickets/{ticket_id}/review",
                                {
                                    "reviewed_category": selected_category
                                }
                            )

                            if review_result:
                                st.success(
                                    "Ticket reviewed and routed successfully."
                                )
                                st.rerun()


st.sidebar.divider()
st.sidebar.caption("IT Support Intelligence | Hackathon Prototype")
