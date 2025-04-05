import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils import filter_data_by_date, filter_data_by_platform, filter_data_by_region, filter_data_by_campaign

st.set_page_config(
    page_title="Sales Funnel | Marketing Dashboard",
    page_icon="🛒",
    layout="wide"
)

# Title
st.title("🛒 Sales Funnel Analysis")

# Check if data is loaded in session state
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.warning("Please load data from the main dashboard first.")
    st.stop()

# Get data from session state
combined_data = st.session_state.combined_data

# Sidebar filters
st.sidebar.title("Filters")

# Date range filter
st.sidebar.subheader("Date Range")
min_date = combined_data['date'].min().date()
max_date = combined_data['date'].max().date()
start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

# Campaign filter
campaigns = combined_data['campaign_name'].unique().tolist()
selected_campaigns = st.sidebar.multiselect(
    "Select Campaigns",
    campaigns,
    default=campaigns[:3] if len(campaigns) > 3 else campaigns
)

# Platform filter
platforms = combined_data['platform'].unique().tolist()
selected_platforms = st.sidebar.multiselect(
    "Select Platforms",
    platforms,
    default=platforms
)

# Region filter
regions = combined_data['region'].unique().tolist()
selected_regions = st.sidebar.multiselect(
    "Select Regions",
    regions,
    default=regions[:3] if len(regions) > 3 else regions
)

# Apply filters
filtered_data = combined_data.copy()
filtered_data = filter_data_by_date(filtered_data, start_date, end_date)
if selected_campaigns:
    filtered_data = filter_data_by_campaign(filtered_data, selected_campaigns)
if selected_platforms:
    filtered_data = filter_data_by_platform(filtered_data, selected_platforms)
if selected_regions:
    filtered_data = filter_data_by_region(filtered_data, selected_regions)

# Check if we have data after filtering
if filtered_data.empty:
    st.warning("No data available with the current filter settings.")
    st.stop()

# Overall Funnel
st.subheader("Overall Sales Funnel")

# Create funnel data based on available columns
funnel_stages = []
funnel_values = []

if 'impressions' in filtered_data.columns:
    funnel_stages.append('Impressions')
    funnel_values.append(filtered_data['impressions'].sum())

if 'clicks' in filtered_data.columns:
    funnel_stages.append('Clicks')
    funnel_values.append(filtered_data['clicks'].sum())

if 'installs' in filtered_data.columns:
    funnel_stages.append('Installs')
    funnel_values.append(filtered_data['installs'].sum())

if 'users' in filtered_data.columns:
    funnel_stages.append('Active Users')
    funnel_values.append(filtered_data['users'].sum())

if 'purchases' in filtered_data.columns:
    funnel_stages.append('Purchases')
    funnel_values.append(filtered_data['purchases'].sum())

# Create the funnel DataFrame
funnel_df = pd.DataFrame({
    'Stage': funnel_stages,
    'Value': funnel_values
})

# Create funnel chart
fig = px.funnel(
    funnel_df,
    x='Value',
    y='Stage',
    title="Marketing and Sales Funnel"
)

# Add percentage labels
for i in range(len(funnel_df) - 1):
    current_value = funnel_df['Value'].iloc[i]
    next_value = funnel_df['Value'].iloc[i + 1]
    
    if current_value > 0:
        conversion_rate = next_value / current_value * 100
        fig.add_annotation(
            x=next_value,
            y=funnel_df['Stage'].iloc[i + 1],
            text=f"{conversion_rate:.2f}% from previous",
            showarrow=True,
            arrowhead=1,
            ax=50,
            ay=0
        )

st.plotly_chart(fig, use_container_width=True)

# Conversion rates
st.subheader("Conversion Rates")
col1, col2, col3, col4 = st.columns(4)

# Click-through rate (CTR)
with col1:
    if all(col in filtered_data.columns for col in ['clicks', 'impressions']):
        ctr = filtered_data['clicks'].sum() / filtered_data['impressions'].sum() * 100 if filtered_data['impressions'].sum() > 0 else 0
        st.metric("Click-Through Rate (CTR)", f"{ctr:.2f}%", help="Percentage of impressions that resulted in clicks")

# Install rate
with col2:
    if all(col in filtered_data.columns for col in ['installs', 'clicks']):
        install_rate = filtered_data['installs'].sum() / filtered_data['clicks'].sum() * 100 if filtered_data['clicks'].sum() > 0 else 0
        st.metric("Install Conversion Rate", f"{install_rate:.2f}%", help="Percentage of clicks that resulted in app installs")

# Purchase rate
with col3:
    if all(col in filtered_data.columns for col in ['purchases', 'installs']):
        purchase_rate = filtered_data['purchases'].sum() / filtered_data['installs'].sum() * 100 if filtered_data['installs'].sum() > 0 else 0
        st.metric("Purchase Conversion Rate", f"{purchase_rate:.2f}%", help="Percentage of installs that resulted in purchases")

# Overall conversion
with col4:
    if all(col in filtered_data.columns for col in ['purchases', 'impressions']):
        overall_rate = filtered_data['purchases'].sum() / filtered_data['impressions'].sum() * 100 if filtered_data['impressions'].sum() > 0 else 0
        st.metric("Overall Conversion Rate", f"{overall_rate:.2f}%", help="Percentage of impressions that resulted in purchases")

# Funnel by Platform
st.subheader("Funnel Analysis by Platform")

# Group data by platform
platform_funnel_data = filtered_data.groupby('platform').agg({
    'impressions': 'sum',
    'clicks': 'sum',
    'installs': 'sum',
    'purchases': 'sum'
}).reset_index()

# Calculate conversion rates
platform_funnel_data['CTR'] = (platform_funnel_data['clicks'] / platform_funnel_data['impressions'] * 100).round(2)
platform_funnel_data['Install Rate'] = (platform_funnel_data['installs'] / platform_funnel_data['clicks'] * 100).round(2)
platform_funnel_data['Purchase Rate'] = (platform_funnel_data['purchases'] / platform_funnel_data['installs'] * 100).round(2)
platform_funnel_data['Overall Rate'] = (platform_funnel_data['purchases'] / platform_funnel_data['impressions'] * 100).round(2)

# Create a grouped bar chart
fig = go.Figure()

for platform in platform_funnel_data['platform']:
    platform_data = platform_funnel_data[platform_funnel_data['platform'] == platform]
    
    # Create data for this platform's funnel
    funnel_values = [
        platform_data['impressions'].values[0],
        platform_data['clicks'].values[0],
        platform_data['installs'].values[0],
        platform_data['purchases'].values[0]
    ]
    
    fig.add_trace(go.Funnel(
        name=platform,
        y=['Impressions', 'Clicks', 'Installs', 'Purchases'],
        x=funnel_values,
        textinfo="value+percent initial"
    ))

fig.update_layout(
    title="Funnel Analysis by Platform",
    funnelmode="stack",
    showlegend=True
)

st.plotly_chart(fig, use_container_width=True)

# Conversion rate comparison by platform
st.subheader("Conversion Rate Comparison by Platform")

# Create comparison chart
fig = px.bar(
    platform_funnel_data,
    x='platform',
    y=['CTR', 'Install Rate', 'Purchase Rate', 'Overall Rate'],
    barmode='group',
    title="Conversion Rates by Platform",
    labels={'platform': 'Platform', 'value': 'Conversion Rate (%)', 'variable': 'Metric'}
)

st.plotly_chart(fig, use_container_width=True)

# Funnel by Region
st.subheader("Funnel Analysis by Region")

# Group data by region
region_funnel_data = filtered_data.groupby('region').agg({
    'impressions': 'sum',
    'clicks': 'sum',
    'installs': 'sum',
    'purchases': 'sum'
}).reset_index()

# Calculate conversion rates
region_funnel_data['CTR'] = (region_funnel_data['clicks'] / region_funnel_data['impressions'] * 100).round(2)
region_funnel_data['Install Rate'] = (region_funnel_data['installs'] / region_funnel_data['clicks'] * 100).round(2)
region_funnel_data['Purchase Rate'] = (region_funnel_data['purchases'] / region_funnel_data['installs'] * 100).round(2)
region_funnel_data['Overall Rate'] = (region_funnel_data['purchases'] / region_funnel_data['impressions'] * 100).round(2)

# Sort by overall conversion rate
top_regions = region_funnel_data.sort_values('Overall Rate', ascending=False).head(5)

# Create a heatmap
fig = px.imshow(
    top_regions[['CTR', 'Install Rate', 'Purchase Rate', 'Overall Rate']].values,
    x=['CTR', 'Install Rate', 'Purchase Rate', 'Overall Rate'],
    y=top_regions['region'],
    color_continuous_scale='Blues',
    labels=dict(x="Conversion Metric", y="Region", color="Rate (%)"),
    title="Top Regions by Conversion Rate"
)

fig.update_layout(
    xaxis=dict(side="top"),
    coloraxis_colorbar=dict(
        title="Rate (%)",
        ticksuffix="%"
    )
)

# Add text annotations
for i in range(len(top_regions)):
    for j, col in enumerate(['CTR', 'Install Rate', 'Purchase Rate', 'Overall Rate']):
        fig.add_annotation(
            x=j,
            y=i,
            text=f"{top_regions[col].iloc[i]:.2f}%",
            showarrow=False,
            font=dict(color="black" if top_regions[col].iloc[i] < 50 else "white")
        )

st.plotly_chart(fig, use_container_width=True)

# Dropoff Analysis
st.subheader("Funnel Dropoff Analysis")

# Calculate overall dropoff rates
dropoff_data = pd.DataFrame({
    'Stage': ['Impression to Click', 'Click to Install', 'Install to Purchase'],
    'Conversion': [
        filtered_data['clicks'].sum() / filtered_data['impressions'].sum() * 100 if filtered_data['impressions'].sum() > 0 else 0,
        filtered_data['installs'].sum() / filtered_data['clicks'].sum() * 100 if filtered_data['clicks'].sum() > 0 else 0,
        filtered_data['purchases'].sum() / filtered_data['installs'].sum() * 100 if filtered_data['installs'].sum() > 0 else 0
    ],
    'Dropoff': [
        100 - (filtered_data['clicks'].sum() / filtered_data['impressions'].sum() * 100) if filtered_data['impressions'].sum() > 0 else 0,
        100 - (filtered_data['installs'].sum() / filtered_data['clicks'].sum() * 100) if filtered_data['clicks'].sum() > 0 else 0,
        100 - (filtered_data['purchases'].sum() / filtered_data['installs'].sum() * 100) if filtered_data['installs'].sum() > 0 else 0
    ]
})

# Create stacked bar chart for conversion vs dropoff
fig = go.Figure()

fig.add_trace(go.Bar(
    x=dropoff_data['Stage'],
    y=dropoff_data['Conversion'],
    name='Conversion Rate',
    marker_color='green',
    text=[f"{val:.2f}%" for val in dropoff_data['Conversion']],
    textposition='auto'
))

fig.add_trace(go.Bar(
    x=dropoff_data['Stage'],
    y=dropoff_data['Dropoff'],
    name='Dropoff Rate',
    marker_color='red',
    text=[f"{val:.2f}%" for val in dropoff_data['Dropoff']],
    textposition='auto'
))

fig.update_layout(
    barmode='stack',
    title="Conversion vs Dropoff Rates at Each Funnel Stage",
    yaxis=dict(
        title="Percentage",
        ticksuffix="%"
    ),
    xaxis=dict(
        title="Funnel Stage"
    ),
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

st.plotly_chart(fig, use_container_width=True)

# Funnel Table Data
st.subheader("Funnel Metrics by Campaign")

# Group by campaign
campaign_funnel = filtered_data.groupby('campaign_name').agg({
    'impressions': 'sum',
    'clicks': 'sum',
    'installs': 'sum',
    'purchases': 'sum',
    'spend': 'sum',
    'revenue': 'sum'
}).reset_index()

# Calculate metrics
campaign_funnel['CTR'] = (campaign_funnel['clicks'] / campaign_funnel['impressions'] * 100).round(2)
campaign_funnel['Install Rate'] = (campaign_funnel['installs'] / campaign_funnel['clicks'] * 100).round(2)
campaign_funnel['Purchase Rate'] = (campaign_funnel['purchases'] / campaign_funnel['installs'] * 100).round(2)
campaign_funnel['Overall Rate'] = (campaign_funnel['purchases'] / campaign_funnel['impressions'] * 100).round(2)
campaign_funnel['Cost per Purchase'] = (campaign_funnel['spend'] / campaign_funnel['purchases']).round(2)
campaign_funnel['Revenue per Purchase'] = (campaign_funnel['revenue'] / campaign_funnel['purchases']).round(2)
campaign_funnel['ROI'] = ((campaign_funnel['revenue'] - campaign_funnel['spend']) / campaign_funnel['spend'] * 100).round(2)

# Format for display
display_funnel = campaign_funnel[['campaign_name', 'CTR', 'Install Rate', 'Purchase Rate', 'Overall Rate', 'Cost per Purchase', 'Revenue per Purchase', 'ROI']]
display_funnel = display_funnel.sort_values('Overall Rate', ascending=False)

# Format percentages and currency
formatted_funnel = display_funnel.copy()
percentage_cols = ['CTR', 'Install Rate', 'Purchase Rate', 'Overall Rate', 'ROI']
currency_cols = ['Cost per Purchase', 'Revenue per Purchase']

for col in percentage_cols:
    formatted_funnel[col] = formatted_funnel[col].apply(lambda x: f"{x:.2f}%")

for col in currency_cols:
    formatted_funnel[col] = formatted_funnel[col].apply(lambda x: f"${x:.2f}")

st.dataframe(formatted_funnel, use_container_width=True)

# Return to Main Dashboard
st.sidebar.markdown("---")
st.sidebar.markdown("[Return to Main Dashboard](/)")
