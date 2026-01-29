import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_loader import load_all_data
import os

# --- Page Config ---
st.set_page_config(
    page_title="Executive Project Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Styling ---
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stApp { background-color: #f9f9f9; color: #333333; }
    h1, h2, h3 { color: #2c3e50; font-family: 'Helvetica Neue', sans-serif; }
    .metric-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 5px solid #27ae60;
        text-align: center;
    }
    .metric-value { font-size: 24px; font-weight: bold; color: #27ae60; }
    .metric-label { font-size: 14px; color: #7f8c8d; }
    /* Hide sidebar since we aren't using it for filters anymore */
    [data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# --- Data Loading ---
FILE_PATH = "ProjectListingExport-29-01-26-16-32-58.xlsx"
if not os.path.exists(FILE_PATH):
    st.error(f"Data file not found at: {FILE_PATH}")
    st.stop()

# Basic cache check is handled by data_loader, but we cleared it once.
dfs = load_all_data(FILE_PATH)
if not dfs:
    st.stop()

df_projects = dfs.get('Projects')
df_roles = dfs.get('Roles')
df_events = dfs.get('Events')
df_products = dfs.get('Products')

# --- Header & Filters ---
st.title("Executive Project Intelligence Dashboard")

# Create Filter Container
with st.container():
    st.subheader("Filters")
    
    # 0. Global Search
    search_term = st.text_input("🔍 Search Projects", placeholder="Search by Project Name, ID, or Keywords...")

    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    
    # 1. Country
    with col_f1:
        countries = sorted(df_projects['Country'].dropna().unique())
        selected_countries = st.multiselect("Country", options=countries, default=[])

    # 2. Sector
    with col_f2:
        sectors = sorted(df_projects['Sector'].dropna().unique())
        selected_sectors = st.multiselect("Sector", options=sectors, default=[])

    # 3. Project Status
    with col_f3:
        statuses = sorted(df_projects['ProjectStatus'].dropna().unique())
        selected_status = st.multiselect("Project Status", options=statuses, default=[])

    # 4. Award Year
    with col_f4:
        # Get unique years, filter out 0 or weird values
        years = sorted([int(y) for y in df_projects['AwardYear'].dropna().unique() if y > 1900], reverse=True)
        selected_years = st.multiselect("Award Year", options=years, default=[])

    # 5. Client (Owner)
    with col_f5:
        # Prepare Client list: Roles where Role == 'Owner'
        # Check if df_roles exists
        if df_roles is not None:
            # Filter for Owners
            owners_df = df_roles[df_roles['Role'] == 'Owner']
            clients = sorted(owners_df['CompanyName'].dropna().unique())
            selected_clients = st.multiselect("Client", options=clients, default=[])
        else:
            selected_clients = []

# --- Apply Filters ---
df_filtered = df_projects.copy()

# Apply Search Term
if search_term:
    search_term = search_term.lower()
    # Search in Project Name or ID (convert ID to string)
    df_filtered = df_filtered[
        df_filtered['Project'].str.lower().str.contains(search_term, na=False) | 
        df_filtered['New_ProjectId'].astype(str).str.contains(search_term, na=False)
    ]

if selected_countries:
    df_filtered = df_filtered[df_filtered['Country'].isin(selected_countries)]
if selected_sectors:
    df_filtered = df_filtered[df_filtered['Sector'].isin(selected_sectors)]
if selected_status:
    df_filtered = df_filtered[df_filtered['ProjectStatus'].isin(selected_status)]
if selected_years:
    df_filtered = df_filtered[df_filtered['AwardYear'].isin(selected_years)]

# Client Filter Logic (Complex: Filter Projects by ensuring their ID is in the selected Owner's project list)
if selected_clients and df_roles is not None:
    # Get ProjectIds for the selected clients (Owners)
    client_project_ids = df_roles[
        (df_roles['Role'] == 'Owner') & 
        (df_roles['CompanyName'].isin(selected_clients))
    ]['New_ProjectId'].unique()
    
    df_filtered = df_filtered[df_filtered['New_ProjectId'].isin(client_project_ids)]


st.markdown("---")

# --- Dashboard Body ---

# 1. KPI Row
total_value = df_filtered['Net Project Value ($m)'].sum()
total_count = len(df_filtered)
avg_value = df_filtered['Net Project Value ($m)'].mean() if total_count > 0 else 0
top_sector = df_filtered['Sector'].mode()[0] if not df_filtered.empty else "N/A"

col1, col2, col3, col4 = st.columns(4)

def metric_card(label, value, prefix="", suffix=""):
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{prefix}{value}{suffix}</div>
    </div>
    """

with col1:
    st.markdown(metric_card("Total Project Value", f"{total_value:,.0f}", prefix="$", suffix="m"), unsafe_allow_html=True)
with col2:
    st.markdown(metric_card("Total Projects", f"{total_count:,.0f}"), unsafe_allow_html=True)
with col3:
    st.markdown(metric_card("Avg. Project Value", f"{avg_value:,.1f}", prefix="$", suffix="m"), unsafe_allow_html=True)
with col4:
    st.markdown(metric_card("Top Sector", str(top_sector)), unsafe_allow_html=True)

st.markdown("###") 

# 2. Charts Row 1
c1, c2 = st.columns(2)

with c1:
    st.subheader("Geographic Distribution")
    country_stats = df_filtered.groupby('Country')['Net Project Value ($m)'].sum().reset_index()
    fig_map = px.choropleth(
        country_stats, 
        locations='Country', 
        locationmode='country names',
        color='Net Project Value ($m)',
        color_continuous_scale='Greens',
        title="Project Value by Country"
    )
    fig_map.update_layout(geo=dict(showframe=False, showcoastlines=False, projection_type='equirectangular'))
    st.plotly_chart(fig_map, width="stretch") 

with c2:
    st.subheader("Sector Breakdown")
    sector_stats = df_filtered.groupby('Sector')['Net Project Value ($m)'].sum().reset_index()
    fig_pie = px.pie(
        sector_stats, 
        values='Net Project Value ($m)', 
        names='Sector', 
        title="Project Value by Sector",
        color_discrete_sequence=px.colors.sequential.Greens_r
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, width="stretch")

# 3. Charts Row 2
st.subheader("Value Timeline (by Award Year)")
year_stats = df_filtered.groupby(['AwardYear', 'ProjectStatus'])['Net Project Value ($m)'].sum().reset_index()
year_stats = year_stats[year_stats['AwardYear'] > 2000]
fig_bar = px.bar(
    year_stats, 
    x='AwardYear', 
    y='Net Project Value ($m)', 
    color='ProjectStatus',
    title="Project Awards Over Time",
    color_discrete_sequence=px.colors.qualitative.Prism
)
st.plotly_chart(fig_bar, width="stretch")

# --- Dialog Function ---
@st.dialog("Project Details")
def show_project_details(project_id):
    # 1. Project Info
    proj = df_projects[df_projects['New_ProjectId'] == project_id].iloc[0]
    st.markdown(f"### {proj['Project']}")
    
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.markdown(f"**Country:** {proj.get('Country', 'N/A')}")
        st.markdown(f"**Sector:** {proj.get('Sector', 'N/A')}")
        st.markdown(f"**Status:** {proj.get('ProjectStatus', 'N/A')}")
    with col_d2:
        st.markdown(f"**Value:** ${proj.get('Net Project Value ($m)', 0):,.1f}m")
        st.markdown(f"**Award Year:** {proj.get('AwardYear', 'N/A')}")
        st.markdown(f"**Completion:** {proj.get('CompletionYear', 'N/A')}")
    
    st.divider()
    
    # 2. Roles
    st.markdown("#### Stakeholders")
    if df_roles is not None:
        roles = df_roles[df_roles['New_ProjectId'] == project_id][['Role', 'CompanyName', 'Contact Name']]
        if not roles.empty:
            st.dataframe(roles, hide_index=True, use_container_width=True)
        else:
            st.info("No stakeholder data available.")
    
    # 3. Products
    st.markdown("#### Products & Quantities")
    if df_products is not None:
        prods = df_products[df_products['New_ProjectId'] == project_id][['Product', 'Quantity']]
        if not prods.empty:
            st.dataframe(prods, hide_index=True, use_container_width=True)
        else:
            st.info("No product data available.")

    # 4. Events
    st.markdown("#### Project Timeline")
    if df_events is not None:
        evts = df_events[df_events['New_ProjectId'] == project_id][['EventDate', 'EventType']].sort_values('EventDate')
        if not evts.empty:
             st.dataframe(evts, hide_index=True, use_container_width=True)
        else:
             st.info("No event data available.")

# 4. Detailed View Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 Project List", "🏗️ Roles & Stakeholders", "📦 Key Products", "📅 Event Calendar"])

with tab1:
    # Ensure index is reset for correct selection mapping
    df_display = df_filtered[['New_ProjectId', 'Project', 'Country', 'Sector', 'ProjectStatus', 'Net Project Value ($m)', 'AwardYear', 'CompletionYear']].reset_index(drop=True)
    
    event = st.dataframe(
        df_display,
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row"
    )
    
    if len(event.selection.rows) > 0:
        idx = event.selection.rows[0]
        # Get ID from the DISPLAY dataframe using the selected index
        selected_id = df_display.iloc[idx]['New_ProjectId']
        show_project_details(selected_id)


with tab2:
    if df_roles is not None:
        filtered_ids = df_filtered['New_ProjectId'].unique()
        roles_filtered = df_roles[df_roles['New_ProjectId'].isin(filtered_ids)]
        
        col_r1, col_r2 = st.columns([1, 2])
        
        with col_r1:
             st.markdown("**Top Roles**")
             role_counts = roles_filtered['Role'].value_counts().head(10)
             st.bar_chart(role_counts)
        
        with col_r2:
            st.markdown("**Top Companies Involved**")
            company_counts = roles_filtered['CompanyName'].value_counts().head(10).reset_index()
            company_counts.columns = ['Company', 'Involvement Count']
            st.dataframe(company_counts, hide_index=True, use_container_width=True)

with tab3:
    if df_products is not None:
        filtered_ids = df_filtered['New_ProjectId'].unique()
        products_filtered = df_products[df_products['New_ProjectId'].isin(filtered_ids)]
        
        prod_stats = products_filtered.groupby('Product')['Quantity'].sum().sort_values(ascending=False).head(15).reset_index()
        
        st.bar_chart(data=prod_stats, x='Product', y='Quantity')
        st.dataframe(products_filtered[['ProjectName', 'Product', 'Quantity']], use_container_width=True)

with tab4:
    if df_events is not None:
        filtered_ids = df_filtered['New_ProjectId'].unique()
        events_filtered = df_events[df_events['New_ProjectId'].isin(filtered_ids)]
        events_filtered = events_filtered.sort_values('EventDate', ascending=True)
        st.dataframe(events_filtered[['EventDate', 'EventType', 'ProjectName']], hide_index=True, use_container_width=True)

st.markdown("---")
st.caption("Generated by Executive Project Intelligence System")
