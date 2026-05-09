import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- 1. LOGIC FUNCTIONS ---

def get_ai_recommendation(df, selected_location):
    try:
        location_col = [c for c in df.columns if '70%' in c][0]
        operator_col = [c for c in df.columns if 'Operator' in c][0]
        signal_col = [c for c in df.columns if 'Signal Strength' in c][0]
        subset = df[df[location_col] == selected_location]
        if subset.empty: return f"No data for {selected_location} yet."
        avg_signals = subset.groupby(operator_col)[signal_col].mean()
        best_op, strength = avg_signals.idxmax(), round(avg_signals.max(), 1)
        return f"AI Analysis: **{best_op}** is strongest at {selected_location} ({strength}/5)."
    except: return "Data error. Check headers!"

def recommend_data_pack(pricing_df, budget, operator):
    try:
        # Assuming sheet has columns: 'Operator', 'Price', 'Data', 'Validity', 'Plan Name'
        filtered = pricing_df[(pricing_df['Price'] <= budget) & (pricing_df['Operator'] == operator)]
        if filtered.empty:
            return None
        # Sort by Price (Descending) to get the best possible plan within budget
        return filtered.sort_values(by='Price', ascending=False).iloc[0]
    except:
        return "Error reading pricing data."

def display_geospatial_map(df):
    st.write("### 📍 Live Campus Signal Hotspots")
    coords = {"Engineering Block": [18.6611, 73.7176], "Management Block": [18.6612, 73.7181], "Admin Block":[18.6606, 73.7182], "Library":[18.6618, 73.7183], "Open Cafeteria": [18.6615, 73.7183], "Nescafe":[18.6609, 73.7183], "Hostel":[18.6616, 73.7162], "Amphitheatre":[18.6608, 73.7179], "Canteen": [18.6605, 73.7175], "Skill Center": [18.6607, 73.7190]}
    m = folium.Map(location=[18.6611, 73.7176], zoom_start=18)
    try:
        l_col = [c for c in df.columns if '70%' in c][0]
        s_col = [c for c in df.columns if 'Signal Strength' in c][0]
        avg = df.groupby(l_col)[s_col].mean().reset_index()
        for _, r in avg.iterrows():
            if r[l_col] in coords:
                c = "red" if r[s_col] < 2.5 else "orange" if r[s_col] < 3.8 else "green"
                folium.Circle(location=coords[r[l_col]], radius=15, color=c, fill=True).add_to(m)
        st_folium(m, width=700, height=400)
    except: st.warning("Waiting for data...")

# --- 2. WEBSITE SETTINGS & THEME ---
st.set_page_config(page_title="SymbiPlan", page_icon="📶", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; }
    div.stButton > button {
        width: 100% !important;
        height: 70px !important;
        background: rgba(255, 255, 255, 0.6) !important;
        border-radius: 15px !important;
        color: #1E3A8A !important;
        font-weight: 700 !important;
        border: 1px solid rgba(255,255,255,0.8) !important;
        margin-bottom: 10px;
    }
    div.stButton > button:hover { background: white !important; transform: scale(1.01); }
    .main .block-container { padding-top: 2rem !important; }
    h2 { margin: 0 !important; padding: 10px 0 !important; color: #1E3A8A !important; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA CONNECTIONS ---
SIGNAL_SHEET_URL = "https://docs.google.com/spreadsheets/d/1FVhzop8SMzmLylTPeqtm2PW2GxNbO1eTas4j7nYD__M/edit?usp=sharing"
# Add your Pricing Sheet URL here
PRICING_SHEET_URL = "https://docs.google.com/spreadsheets/d/1CaBmy4zwDnW4DkL72Jx8Tjxn3PgPYfN0KCNL-3rS2po/edit?usp=sharing" 

conn = st.connection("gsheets", type=GSheetsConnection)

try:
    df = conn.read(spreadsheet=SIGNAL_SHEET_URL, ttl=60)
except:
    df = pd.read_csv(SIGNAL_SHEET_URL.split('/edit')[0] + '/export?format=csv')

# --- 4. NAVIGATION STATE ---
if 'page' not in st.session_state: st.session_state.page = 'Home'

# --- 5. THE HOME PAGE ---
if st.session_state.page == 'Home':
    st.markdown("<h2>SymbiPlan</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 SIGNAL FINDER"): st.session_state.page = 'Signal Finder'
        if st.button("📊 LIVE HEATMAP"): st.session_state.page = 'Heatmap'
    with col2:
        if st.button("💰 SMART RECHARGE"): st.session_state.page = 'Recharge'
        if st.button("📢 REPORT SIGNAL"): st.session_state.page = 'Report'

# --- 6. INDIVIDUAL PAGES ---
elif st.session_state.page == 'Signal Finder':
    if st.button("⬅️ Back"): st.session_state.page = 'Home'
    st.header("🔍 Signal Finder")
    loc = st.selectbox("Where are you?", ["Admin Block", "Management Block", "Engineering Block", "Skill Center", "Library", "Canteen", "Open Cafeteria", "Nescafe", "Hostel Wings", "Parking", "Amphitheater"])
    if st.button("Check"): st.info(get_ai_recommendation(df, loc))

elif st.session_state.page == 'Heatmap':
    if st.button("⬅️ Back"): st.session_state.page = 'Home'
    display_geospatial_map(df)

elif st.session_state.page == 'Recharge':
    if st.button("⬅️ Back"): st.session_state.page = 'Home'
    st.header("💰 Data Pack Recommender")
    st.write("Find the best plan based on your budget.")
    
    # Try fetching pricing data
    try:
        pricing_df = conn.read(spreadsheet=PRICING_SHEET_URL, ttl=300)
        budget = st.number_input("Enter your maximum budget (₹)", min_value=10, value=299, step=10)
        op_choice = st.selectbox("Select Operator", pricing_df['Operator'].unique())
        
        if st.button("Find Best Plan"):
            plan = recommend_data_pack(pricing_df, budget, op_choice)
            if plan is not None:
                st.success(f"### Recommended: {plan['Plan Name']}")
                st.metric("Price", f"₹{plan['Price']}")
                st.write(f"**Data:** {plan['Data']} | **Validity:** {plan['Validity']}")
            else:
                st.error("No plans found within this budget for the selected operator.")
    except:
        st.warning("Pricing sheet not connected. Please ensure the URL is correct and the sheet has 'Operator', 'Price', 'Data', and 'Plan Name' columns.")

elif st.session_state.page == 'Report':
    if st.button("⬅️ Back"): st.session_state.page = 'Home'
    st.link_button("Open Signal Form", "https://docs.google.com/forms/d/e/1FAIpQLSfmsDX0Oo2nWGt6xScoIV-X0_UPHV_qLCsYDnKQ4P07ZN5CYg/viewform")
