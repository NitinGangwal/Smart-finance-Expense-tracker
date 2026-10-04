import html
import json
import os
import re
from datetime import date

import altair as alt
import ollama
import pandas as pd
import streamlit as st

MODEL = "gemma3:4b"
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expenses.csv")
CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Entertainment", "Education", "Health", "Other"]
COLUMNS = ["date", "item", "amount", "category"]
COLORS = {
    "Food": "#F59E0B", "Travel": "#2563EB", "Shopping": "#DB2777", "Bills": "#DC2626",
    "Entertainment": "#7C3AED", "Education": "#16A34A", "Health": "#0D9488", "Other": "#6B7280",
}


def load():
    if os.path.exists(FILE):
        return pd.read_csv(FILE)
    return pd.DataFrame(columns=COLUMNS)


def save(df):
    df.to_csv(FILE, index=False)


def parse_with_ai(text):
    prompt = f"""Extract every expense from this text: "{text}"
Return ONLY JSON in this format:
{{"expenses": [{{"item": "tea", "amount": 20, "category": "Food"}}]}}
Category must be one of: {", ".join(CATEGORIES)}. Amount is a number in rupees."""
    reply = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}], format="json")
    data = json.loads(reply["message"]["content"])
    rows = []
    for e in data.get("expenses", []):
        try:
            amount = float(e["amount"])
        except (KeyError, ValueError, TypeError):
            continue
        category = e.get("category", "Other")
        if category not in CATEGORIES:
            category = "Other"
        rows.append({"date": str(date.today()), "item": str(e.get("item", "?")).title(),
                     "amount": amount, "category": category})
    return rows


def ai_summary(df):
    by_cat = df.groupby("category")["amount"].sum().round(0).to_string()
    prompt = f"""You are a professional personal finance advisor for a college student in India.
Total spent: Rs.{df['amount'].sum():.0f}
Spending by category (Rs.):
{by_cat}
Write a short summary (3-4 lines), then give 3 practical, specific saving tips as a numbered list.
Use a clear, professional tone."""
    reply = ollama.chat(model=MODEL, messages=[{"role": "user", "content": prompt}])
    return reply["message"]["content"]


def to_html(text):
    safe = html.escape(text)
    safe = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", safe)
    safe = re.sub(r"(?m)^\s*[\*\-]\s+", "&bull; ", safe)
    return safe.replace("\n", "<br>")


st.set_page_config(page_title="Smart Expense Tracker", page_icon="💰", layout="wide")

st.markdown("""
<style>
.stApp { background: linear-gradient(180deg, #FFFBE6 0%, #EAFBEA 100%); }
.stApp, .stApp p, .stApp label, .stApp li, .stApp span, .stApp h1, .stApp h2, .stApp h3, .stApp h4,
.stMarkdown, [data-testid="stWidgetLabel"] p { color: #111111 !important; }
header[data-testid="stHeader"] { background: transparent; }

.hero {
    background: linear-gradient(120deg, #FFD814 0%, #FFB300 60%, #FF8F00 100%);
    padding: 28px 34px; border-radius: 18px; margin-bottom: 22px;
    border-bottom: 6px solid #16A34A; box-shadow: 0 8px 22px rgba(0,0,0,0.15);
}
.hero h1 { margin: 0; font-size: 2.1rem; font-weight: 800; color: #111111 !important; }
.hero p { margin: 6px 0 0 0; font-size: 1.02rem; color: #111111 !important; }

.card { border-radius: 16px; padding: 18px 22px; box-shadow: 0 6px 16px rgba(0,0,0,0.12); color: #111111; }
.card .label { font-size: 0.8rem; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; }
.card .value { font-size: 2rem; font-weight: 800; margin-top: 4px; color: #111111; }
.card.green  { background: #B9F6CA; border-left: 8px solid #16A34A; }
.card.yellow { background: #FFF59D; border-left: 8px solid #F5B301; }
.card.red    { background: #FFCDD2; border-left: 8px solid #D93025; }

.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] { background: #FFFFFF; border-radius: 10px; padding: 8px 18px; font-weight: 700; color: #111111 !important; }
.stTabs [aria-selected="true"] { background: #FFD814 !important; }

.stTextInput input { background: #FFFFFF !important; color: #111111 !important; border: 2px solid #16A34A !important; border-radius: 10px; }
.stButton > button, .stDownloadButton > button {
    background: #FFD814; color: #111111 !important; border: 1px solid #F5B301;
    border-radius: 10px; padding: 0.55rem 1.4rem; font-weight: 700;
}
.stButton > button:hover, .stDownloadButton > button:hover { background: #FFC400; border-color: #E0A800; color: #111111 !important; }

.tbl { width: 100%; border-collapse: collapse; background: #FFFFFF; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.tbl th { background: #16A34A; color: #FFFFFF !important; padding: 10px 14px; text-align: left; }
.tbl td { color: #111111 !important; padding: 9px 14px; border-bottom: 1px solid #EEEEEE; }
.tbl tr:nth-child(even) td { background: #F6FFF7; }

.tips {
    background: #FFF8CC; border-left: 10px solid #F5B301; border-radius: 16px;
    padding: 22px 28px; color: #111111; font-size: 1.02rem; line-height: 1.7;
    box-shadow: 0 8px 20px rgba(245,179,1,0.35);
}
.tips-title { font-weight: 800; font-size: 1.15rem; margin-bottom: 8px; color: #111111; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>💰 Smart Expense &amp; Finance Tracker</h1>
  <p>Record expenses in plain language and let a local, open-source AI organise them for you. Your financial data stays on your own device.</p>
</div>
""", unsafe_allow_html=True)

df = load()

total = df["amount"].sum() if not df.empty else 0
count = len(df)
top = df.groupby("category")["amount"].sum().idxmax() if not df.empty else "-"

c1, c2, c3 = st.columns(3)
c1.markdown(f'<div class="card green"><div class="label">Total Spending</div><div class="value">₹ {total:,.0f}</div></div>', unsafe_allow_html=True)
c2.markdown(f'<div class="card yellow"><div class="label">Total Transactions</div><div class="value">{count}</div></div>', unsafe_allow_html=True)
c3.markdown(f'<div class="card red"><div class="label">Top Spending Category</div><div class="value">{top}</div></div>', unsafe_allow_html=True)

st.write("")
tab1, tab2, tab3 = st.tabs(["➕ Add Expense", "📊 Analytics", "💡 AI Insights"])

with tab1:
    if "flash" in st.session_state:
        st.success(st.session_state.pop("flash"))
    text = st.text_input("Describe your expenses", placeholder="e.g. tea 20, bus 100, lunch 120")
    if st.button("Add Expense") and text.strip():
        with st.spinner("Analysing your expenses..."):
            try:
                new_rows = parse_with_ai(text)
            except Exception as err:
                new_rows = []
                st.error(f"Something went wrong: {err}")
        if new_rows:
            df = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
            save(df)
            st.session_state["flash"] = f"{len(new_rows)} expense(s) added successfully."
            st.rerun()
        else:
            st.warning("We could not understand that entry. Please try again, for example: tea 20, bus 100.")

    if not df.empty:
        st.subheader("Recent Transactions")
        show = df.tail(15).iloc[::-1].copy()
        show["amount"] = show["amount"].map(lambda v: f"₹ {v:,.0f}")
        show.columns = ["Date", "Item", "Amount", "Category"]
        st.markdown(show.to_html(index=False, classes="tbl", border=0), unsafe_allow_html=True)
        st.write("")
        st.download_button("Download CSV", df.to_csv(index=False), "expenses.csv", "text/csv")

with tab2:
    if df.empty:
        st.info("No data yet. Add a few expenses to see your analytics.")
    else:
        by_cat = df.groupby("category", as_index=False)["amount"].sum()
        scale = alt.Scale(domain=list(COLORS.keys()), range=list(COLORS.values()))
        left, right = st.columns(2)
        with left:
            st.subheader("Spending by Category")
            bar = (
                alt.Chart(by_cat)
                .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8)
                .encode(
                    x=alt.X("category:N", sort="-y", title=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("amount:Q", title="Amount (₹)"),
                    color=alt.Color("category:N", scale=scale, legend=None),
                    tooltip=["category", "amount"],
                )
                .properties(height=340, width="container")
                .configure(background="#FFFFFF")
            )
            st.altair_chart(bar, theme=None)
        with right:
            st.subheader("Share of Spending")
            donut = (
                alt.Chart(by_cat)
                .mark_arc(innerRadius=80, outerRadius=140)
                .encode(
                    theta="amount:Q",
                    color=alt.Color("category:N", scale=scale, legend=alt.Legend(title="Category")),
                    tooltip=["category", "amount"],
                )
                .properties(height=340, width="container")
                .configure(background="#FFFFFF")
            )
            st.altair_chart(donut, theme=None)

with tab3:
    if df.empty:
        st.info("Add some expenses first, then generate your personalised insights.")
    else:
        if st.button("Generate Summary & Saving Tips"):
            with st.spinner("Preparing your insights. This may take a minute..."):
                try:
                    st.session_state["tips"] = ai_summary(df)
                except Exception as err:
                    st.error(f"Something went wrong: {err}")
        if "tips" in st.session_state:
            st.markdown(
                f'<div class="tips"><div class="tips-title">💡 AI Summary &amp; Saving Tips</div>{to_html(st.session_state["tips"])}</div>',
                unsafe_allow_html=True,
            )
            
#run krne ki command => 