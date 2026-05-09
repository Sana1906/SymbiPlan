import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import folium
from streamlit_folium import st_folium

# ML Libraries
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# =====================================================
# 1. SIGNAL AI RECOMMENDATION FUNCTION
# =====================================================

def get_ai_recommendation(df, selected_location):

    try:
        location_col = [c for c in df.columns if '70%' in c][0]
        operator_col = [c for c in df.columns if 'Operator' in c][0]
        signal_col = [c for c in df.columns if 'Signal Strength' in c][0]

        subset = df[df[location_col] == selected_location]

        if subset.empty:
            return f"No data for {selected_location} yet."

        avg_signals = subset.groupby(operator_col)[signal_col].mean()

        best_op = avg_signals.idxmax()
        strength = round(avg_signals.max(), 1)

        return f"AI Analysis: {best_op} is strongest at {selected_location} ({strength}/5)."

    except:
        return "Data error. Check headers!"


# =====================================================
# 2. HEATMAP FUNCTION
# =====================================================

def display_geospatial_map(df):

    st.write("### 📍 Live Campus Signal Hotspots")

    coords = {
        "Engineering Block": [18.6611, 73.7176],
        "Management Block": [18.6612, 73.7181],
        "Admin Block": [18.6606, 73.7182],
        "Library": [18.6618, 73.7183],
        "Open Cafeteria": [18.6615, 73.7183],
        "Nescafe": [18.6609, 73.7183],
        "Hostel": [18.6616, 73.7162],
        "Amphitheatre": [18.6608, 73.7179],
        "Canteen": [18.6605, 73.7175],
        "Skill Center": [18.6607, 73.7190]
    }

    m = folium.Map(location=[18.6611, 73.7176], zoom_start=18)

    try:
        l_col = [c for c in df.columns if '70%' in c][0]
        s_col = [c for c in df.columns if 'Signal Strength' in c][0]

        avg = df.groupby(l_col)[s_col].mean().reset_index()

        for _, r in avg.iterrows():

            if r[l_col] in coords:

                color = (
                    "red" if r[s_col] < 2.5
                    else "orange" if r[s_col] < 3.8
                    else "green"
                )

                folium.Circle(
                    location=coords[r[l_col]],
                    radius=15,
                    color=color,
                    fill=True
                ).add_to(m)

        st_folium(m, width=700, height=400)

    except:
        st.warning("Waiting for data...")


# =====================================================
# 3. STREAMLIT SETTINGS
# =====================================================

st.set_page_config(
    page_title="SymbiPlan",
    page_icon="📶",
    layout="wide"
)

# =====================================================
# 4. CUSTOM CSS
# =====================================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
}

div.stButton > button {

    width: 100% !important;
    height: 80px !important;

    background: rgba(255,255,255,0.6) !important;

    border-radius: 15px !important;

    color: #1E3A8A !important;

    font-weight: 700 !important;

    border: 1px solid rgba(255,255,255,0.8) !important;

    transition: 0.3s;
}

div.stButton > button:hover {

    background: white !important;

    transform: scale(1.01);
}

.main .block-container {

    padding-top: 2rem !important;
}

h2 {

    margin: 0 !important;

    padding: 10px 0 !important;

    color: #1E3A8A !important;

    text-align: center;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# 5. LOAD SIGNAL DATA FROM GOOGLE SHEETS
# =====================================================

SHEET_URL = "https://docs.google.com/spreadsheets/d/1FVhzop8SMzmLylTPeqtm2PW2GxNbO1eTas4j7nYD__M/edit?usp=sharing"

try:

    conn = st.connection("gsheets", type=GSheetsConnection)

    df = conn.read(
        spreadsheet=SHEET_URL,
        ttl=60
    )

except:

    csv_url = SHEET_URL.split('/edit')[0] + '/export?format=csv'

    df = pd.read_csv(csv_url)

# =====================================================
# 6. LOAD TELECOM PACK DATASET
# =====================================================

PACK_SHEET_URL = "https://docs.google.com/spreadsheets/d/1CaBmy4zwDnW4DkL72Jx8Tjxn3PgPYfN0KCNL-3rS2po/edit?usp=sharing"

try:

    telecom_csv = PACK_SHEET_URL.split('/edit')[0] + '/export?format=csv'

    telecom_df = pd.read_csv(telecom_csv)

    # CLEAN COLUMN NAMES
    telecom_df.columns = telecom_df.columns.str.strip().str.lower()

    # FEATURE ENGINEERING
    telecom_df['cost_per_gb'] = telecom_df['price'] / telecom_df['data_gb']

    features = telecom_df[
        ['price', 'data_gb', 'validity', 'cost_per_gb']
    ]

    # SCALING
    scaler = StandardScaler()

    scaled_features = scaler.fit_transform(features)

    # KMEANS
    kmeans = KMeans(
        n_clusters=3,
        random_state=42
    )

    telecom_df['cluster'] = kmeans.fit_predict(
        scaled_features
    )

except Exception as e:

    st.error(f"Telecom Dataset Error: {e}")

# =====================================================
# 7. PLAN RECOMMENDATION FUNCTION
# =====================================================

def recommend_plan(budget, data_need, provider):

    filtered = telecom_df[
        (telecom_df['price'] <= budget) &
        (telecom_df['data_gb'] >= data_need)
    ]

    # FILTER BY PROVIDER
    if provider != "All":
        filtered = filtered[
            filtered['provider'] == provider
        ]

    if filtered.empty:
        return None

    best = filtered.sort_values(
        by='cost_per_gb'
    ).iloc[0]

    return best

# =====================================================
# 8. SESSION STATE
# =====================================================

if 'page' not in st.session_state:
    st.session_state.page = 'Home'

# =====================================================
# 9. HOME PAGE
# =====================================================

if st.session_state.page == 'Home':

    st.markdown(
        "<h2>SymbiPlan</h2>",
        unsafe_allow_html=True
    )

    if st.button(
        "🔍 SIGNAL FINDER",
        use_container_width=True
    ):
        st.session_state.page = 'Signal Finder'

    if st.button(
        "📊 LIVE HEATMAP",
        use_container_width=True
    ):
        st.session_state.page = 'Heatmap'

    if st.button(
        "📦 DATA PACK RECOMMENDER",
        use_container_width=True
    ):
        st.session_state.page = 'Plans'

    if st.button(
        "📢 REPORT SIGNAL",
        use_container_width=True
    ):
        st.session_state.page = 'Report'

# =====================================================
# 10. SIGNAL FINDER PAGE
# =====================================================

elif st.session_state.page == 'Signal Finder':

    if st.button("⬅️ Back"):
        st.session_state.page = 'Home'

    st.header("🔍 Signal Finder")

    loc = st.selectbox(
        "Where are you?",
        [
            "Admin Block",
            "Management Block",
            "Engineering Block",
            "Skill Center",
            "Library",
            "Canteen",
            "Open Cafeteria",
            "Nescafe",
            "Hostel",
            "Amphitheatre"
        ]
    )

    if st.button("Check"):

        st.info(
            get_ai_recommendation(df, loc)
        )

# =====================================================
# 11. HEATMAP PAGE
# =====================================================

elif st.session_state.page == 'Heatmap':

    if st.button("⬅️ Back"):
        st.session_state.page = 'Home'

    display_geospatial_map(df)

# =====================================================
# 12. DATA PACK RECOMMENDER PAGE
# =====================================================

elif st.session_state.page == 'Plans':

    if st.button("⬅️ Back"):
        st.session_state.page = 'Home'

    st.header("📦 AI Data Pack Recommendation")

    provider_options = ["All"] + list(
        telecom_df['provider'].unique()
    )

    provider = st.selectbox(
        "Select Provider",
        provider_options
    )

    budget = st.slider(
        "Select Budget (₹)",
        50,
        5000,
        500
    )

    data_need = st.slider(
        "Required Data (GB)",
        1,
        500,
        50
    )

    if st.button("Find Best Plan"):

        result = recommend_plan(
            budget,
            data_need,
            provider
        )

        if result is not None:

            st.success(
                "✅ Best Recommended Plan"
            )

            st.write(
                f"### 📡 Provider: {result['provider']}"
            )

            st.write(
                f"💰 Price: ₹{result['price']}"
            )

            st.write(
                f"📶 Data: {result['data_gb']} GB"
            )

            st.write(
                f"📅 Validity: {result['validity']} Days"
            )

            st.write(
                f"⚡ Cost per GB: ₹{round(result['cost_per_gb'],2)}"
            )

            st.write(
                f"🤖 Cluster Group: {result['cluster']}"
            )

        else:

            st.warning(
                "No suitable plan found."
            )

# =====================================================
# 13. REPORT PAGE
# =====================================================

elif st.session_state.page == 'Report':

    if st.button("⬅️ Back"):
        st.session_state.page = 'Home'

    st.link_button(
        "Open Signal Form",
        "https://docs.google.com/forms/d/e/1FAIpQLSfmsDX0Oo2nWGt6xScoIV-X0_UPHV_qLCsYDnKQ4P07ZN5CYg/viewform"
    )
