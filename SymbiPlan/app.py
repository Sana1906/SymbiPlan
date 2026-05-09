import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import folium
from streamlit_folium import st_folium

# --- 1. CORE LOGIC ---

def get_ai_recommendation(df, selected_location):
    try:
        # Clean columns to remove leading/trailing spaces
        df.columns = df.columns.str.strip()
        location_col = [c for c in df.columns if '70%' in c or 'Location' in c][0]
        operator_col = [c for c in df.columns if 'Operator' in c][0]
        signal_col = [c for c in df.columns if 'Signal Strength' in c][0]
        
        subset = df[df[location_col] == selected_location]
        if subset.empty: return f"No data for {selected_location} yet."
        
        # Ensure signal strength is treated as a number
        subset[signal_col] = pd.to_numeric(subset[signal_col], errors='coerce')
        avg_signals = subset.groupby(operator_col)[signal_col].mean()
        best_op, strength = avg_signals.idxmax(), round(avg_signals.max(), 1)
        return f"AI Analysis: **{best_op}** is strongest at {selected_location} ({strength}/5)."
    except Exception:
        return "Signal data analysis error. Please check your signal sheet headers."

def recommend_data_pack(pricing_df, budget, operator):
    try:
        # 1. CLEANING: Remove extra spaces and make a lowercase map of columns
        pricing_df.columns = pricing_df.columns.str.strip()
        col_map = {c.lower(): c for c in pricing_df.columns}
        
        # 2. FIND RELEVANT COLUMNS (Price, Operator, Plan Name, Data, Validity)
        p_col = col_map.get('price')
        o_col = col_map.get('operator')
        n_col = col_map.get('plan name')
        d_col = col_map.get('data')
        v_col = col_map.get('validity')

        if not all([p_col, o_col, n_col]):
            return f"Missing required columns. Found: {list(pricing_df.columns)}"

        # 3. FILTERING
        # Convert Price to numbers in case they are stored as text
        pricing_df[p_col] = pd.to_numeric(pricing_df[p_col], errors='coerce')
        
        filtered = pricing_df[
            (pricing_df[p_col] <= budget) & 
            (pricing_df[o_col].str.contains(operator, case=False, na=False))
        ]
        
        if filtered.empty: return None
        
        # Return the most expensive plan that is still under budget
        best_row = filtered.sort_values(by=p_col, ascending=False).iloc[0]
        
        return {
            "name": best_row[n_col],
            "price": best_row[p_col],
            "data": best_row[d_col] if d_col else "N/A",
            "validity": best_row[v_col] if v_col else "N/A"
        }
    except Exception as e:
        return f"Error processing: {str(e)}"

def display_geospatial_map(df):
    st.write("### 📍 Live Campus Signal Hotspots")
    coords = {"Engineering Block": [18.6611, 73.7176], "Management Block": [18.6612, 73.7181], "Admin Block":[18.6606, 73.7182], "Library":[18.6618, 73.7183], "Open Cafeteria": [18.6615, 73.7183], "Nescafe":[18.6609, 73.7183], "Hostel":[18.6616, 73.7162], "Amphitheatre":[18.6608, 73.7179], "Canteen": [18.6605, 73.7175], "Skill Center": [18.6607, 73.7190]}
    m = folium.Map(location=[18.6611, 73.7176], zoom_start=18)
    try:
        df.columns = df.columns.str.strip()
        l_col = [c for c in df.columns if '70%' in c or 'Location' in c][0]
        s_col = [c for c in df.columns if 'Signal Strength' in c][0]
        df[s_col] = pd.to_numeric(df[s_col], errors='coerce')
        avg = df.groupby(l_col)[s_col].mean().reset_index()
        for _, r in avg.iterrows():
            if r[l_col] in coords:
                c = "red" if r[s_col] < 2.5 else "orange" if r[s_col] < 3.8 else "green"
                folium.Circle(location=coords[r[l_col]], radius=15, color=c, fill=True).add_to(m)
        st_folium(m, width=700, height=400)
    except: st.warning("Mapping data unavailable...")

# --- 2. THEME & STYLING ---
st.set_page_config(page_title="SymbiPlan", page_icon="📶", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important; }
    div.stButton > button {
        width: 100% !important; height: 80px !important;
        background: rgba(255, 255, 255, 0.7) !important;
        border-radius: 15px !important; color: #1E3A8A !important;
        font-weight: 700 !important; border: 1px solid rgba(255,255,255,0.8) !important;
        transition: 0.3s;
    }
    div.stButton > button:hover { background: white !important; transform: scale(1.02); }
    h2 { color: #1E3A8A !important; text-align: center; margin-bottom: 25px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA & NAVIGATION ---
SIGNAL_URL = "https://docs.google.com/spreadsheets/d/1FVhzop8SMzmLylTPeqtm2PW2GxNbO1eTas4j7nYD__M/edit?usp=sharing"
TELECOM_URL = "https://docs.google.com/spreadsheets/d/1CaBmy4zwDnW4DkL72Jx8Tjxn3PgPYfN0KCNL-3rS2po/edit?usp=sharing"

conn = st.connection("gsheets", type=GSheetsConnection)

if 'page' not in st.session_state: st.session_state.page = 'Home'

# --- 4. HOME PAGE ---

if st.session_state.page == 'Home':
    st.markdown("<h2 style='margin-top: 0px;'>SymbiPlan</h2>", unsafe_allow_html=True)
    if st.button("🔍 SIGNAL FINDER", use_container_width=True): 
        st.session_state.page = 'Signal Finder'
    if st.button("📊 LIVE HEATMAP", use_container_width=True): 
        st.session_state.page = 'Heatmap'
    if st.button("💰 SMART RECHARGE", use_container_width=True): 
        st.session_state.page = 'Recharge'
    if st.button("📢 REPORT SIGNAL", use_container_width=True): 
        st.session_state.page = 'Report'
        
# --- 5. SUB PAGES ---
elif st.session_state.page == 'Signal Finder':
    if st.button("⬅️ Back"): st.session_state.page = 'Home'
    st.header("🔍 Signal Finder")
    try:
        df_sig = conn.read(spreadsheet=SIGNAL_URL, ttl=60)
        loc = st.selectbox("Where are you?", ["Admin Block", "Management Block", "Engineering Block", "Skill Center", "Library", "Canteen", "Open Cafeteria", "Nescafe", "Hostel Wings", "Parking", "Amphitheater"])
        if st.button("Check Strength"): st.info(get_ai_recommendation(df_sig, loc))
    except: st.error("Failed to load signal data.")

elif st.session_state.page == 'Heatmap':
    if st.button("⬅️ Back"): st.session_state.page = 'Home'
    try:
        df_sig = conn.read(spreadsheet=SIGNAL_URL, ttl=60)
        display_geospatial_map(df_sig)
    except: st.error("Failed to load map data.")

elif st.session_state.page == 'Recharge':
    if st.button("⬅️ Back"): st.session_state.page = 'Home'
    st.header("💰 Smart Recharge")
    st.write("Find the best telecom plan within your budget.")
    
    try:
        df_plans = conn.read(spreadsheet=TELECOM_URL, ttl=300)
        df_plans.columns = df_plans.columns.str.strip()
        
        budget = st.number_input("Max Budget (₹)", min_value=10, value=250, step=10)
        
        # Dynamically find the Operator column
        op_col = [c for c in df_plans.columns if c.lower() == 'operator'][0]
        operator = st.selectbox("Your Operator", df_plans[op_col].unique())
        
        if st.button("Recommend Best Plan"):
            result = recommend_data_pack(df_plans, budget, operator)
            if result is None:
                st.warning("No plans found for this budget.")
            elif isinstance(result, str):
                st.error(result)
            else:
                st.success(f"### Recommended: {result['name']}")
                st.write(f"**Price:** ₹{result['price']} | **Data:** {result['data']} | **Validity:** {result['validity']}")
    except Exception as e:
        st.error(f"Connection Error: Check spreadsheet and column names. (Error: {e})")

elif st.session_state.page == 'Report':
    if st.button("⬅️ Back"): st.session_state.page = 'Home'
    st.link_button("Open Signal Form", "https://docs.google.com/forms/d/e/1FAIpQLSfmsDX0Oo2nWGt6xScoIV-X0_UPHV_qLCsYDnKQ4P07ZN5CYg/viewform")
