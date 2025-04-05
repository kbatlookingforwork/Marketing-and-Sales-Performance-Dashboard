import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from visualization import create_time_series_chart
from data_processing import load_and_process_data
from utils import filter_data_by_date, filter_data_by_platform, filter_data_by_region, filter_data_by_campaign

st.set_page_config(
    page_title="Campaign Performance | Marketing Dashboard",
    page_icon="📈",
    layout="wide"
)

# Title
st.title("📈 Campaign Performance Analysis")

# Check if data is loaded in session state
if 'data_loaded' not in st.session_state or not st.session_state.data_loaded:
    st.warning("Please load data from the main dashboard first.")
    st.stop()

# Get data from session state
campaign_data = st.session_state.campaign_data
combined_data = st.session_state.combined_data

# Sidebar filters
st.sidebar.title("Filters")

# Date range filter
st.sidebar.subheader("Date Range")
min_date = campaign_data['date'].min().date()
max_date = campaign_data['date'].max().date()
start_date = st.sidebar.date_input("Start Date", min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", max_date, min_value=min_date, max_value=max_date)

# Campaign filter
campaigns = campaign_data['campaign_name'].unique().tolist()
selected_campaigns = st.sidebar.multiselect(
    "Select Campaigns",
    campaigns,
    default=campaigns[:3] if len(campaigns) > 3 else campaigns
)

# Platform filter
platforms = campaign_data['platform'].unique().tolist()
selected_platforms = st.sidebar.multiselect(
    "Select Platforms",
    platforms,
    default=platforms
)

# Region filter
regions = campaign_data['region'].unique().tolist()
selected_regions = st.sidebar.multiselect(
    "Select Regions",
    regions,
    default=regions[:3] if len(regions) > 3 else regions
)

# Apply filters
filtered_data = campaign_data.copy()
filtered_data = filter_data_by_date(filtered_data, start_date, end_date)
if selected_campaigns:
    filtered_data = filter_data_by_campaign(filtered_data, selected_campaigns)
if selected_platforms:
    filtered_data = filter_data_by_platform(filtered_data, selected_platforms)
if selected_regions:
    filtered_data = filter_data_by_region(filtered_data, selected_regions)

# Also filter combined data
filtered_combined = combined_data.copy()
filtered_combined = filter_data_by_date(filtered_combined, start_date, end_date)
if selected_campaigns:
    filtered_combined = filter_data_by_campaign(filtered_combined, selected_campaigns)
if selected_platforms:
    filtered_combined = filter_data_by_platform(filtered_combined, selected_platforms)
if selected_regions:
    filtered_combined = filter_data_by_region(filtered_combined, selected_regions)

# Check if we have data after filtering
if filtered_data.empty:
    st.warning("No data available with the current filter settings.")
    st.stop()

# Campaign Performance Overview
st.subheader("Campaign Performance Overview")

# Summary metrics in columns
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_impressions = filtered_data['impressions'].sum()
    st.metric("Total Impressions", f"{total_impressions:,.0f}")

with col2:
    total_clicks = filtered_data['clicks'].sum()
    st.metric("Total Clicks", f"{total_clicks:,.0f}")

with col3:
    total_installs = filtered_data['installs'].sum()
    st.metric("Total Installs", f"{total_installs:,.0f}")

with col4:
    total_spend = filtered_data['spend'].sum()
    st.metric("Total Spend", f"${total_spend:,.2f}")

# Time series trends
st.subheader("Campaign Trends Over Time")

# Metric selector for time series
metric_options = {
    "Impressions": "impressions",
    "Clicks": "clicks", 
    "Installs": "installs",
    "Spend": "spend",
    "CTR (%)": "ctr",
    "Conversion Rate (%)": "conversion_rate",
    "CPA ($)": "cpa"
}

selected_metrics = st.multiselect(
    "Select Metrics to Display",
    options=list(metric_options.keys()),
    default=["Impressions", "Clicks", "Installs"]
)

if selected_metrics:
    # Group by date
    daily_data = filtered_data.groupby('date').agg({
        'impressions': 'sum',
        'clicks': 'sum',
        'installs': 'sum',
        'spend': 'sum',
    }).reset_index()
    
    # Calculate derived metrics
    daily_data['ctr'] = (daily_data['clicks'] / daily_data['impressions'] * 100).round(2)
    daily_data['conversion_rate'] = (daily_data['installs'] / daily_data['clicks'] * 100).round(2)
    daily_data['cpa'] = (daily_data['spend'] / daily_data['installs']).round(2)
    
    # Create figure
    fig = go.Figure()
    
    for metric_name in selected_metrics:
        metric_col = metric_options[metric_name]
        fig.add_trace(go.Scatter(
            x=daily_data['date'],
            y=daily_data[metric_col],
            mode='lines+markers',
            name=metric_name
        ))
    
    fig.update_layout(
        title="Campaign Metrics Over Time",
        xaxis_title="Date",
        yaxis_title="Value",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Campaign Comparison
st.subheader("Campaign Performance Comparison")

# Metric for comparison
comparison_metric = st.selectbox(
    "Select Comparison Metric",
    ["conversion_rate", "cpa", "ctr", "roi", "impressions", "clicks", "installs", "spend"],
    format_func=lambda x: x.replace('_', ' ').title()
)

# Group by campaign
campaign_comparison = filtered_data.groupby('campaign_name').agg({
    'impressions': 'sum',
    'clicks': 'sum',
    'installs': 'sum',
    'spend': 'sum',
    'revenue': 'sum'
}).reset_index()

# Calculate metrics
campaign_comparison['ctr'] = (campaign_comparison['clicks'] / campaign_comparison['impressions'] * 100).round(2)
campaign_comparison['conversion_rate'] = (campaign_comparison['installs'] / campaign_comparison['clicks'] * 100).round(2)
campaign_comparison['cpa'] = (campaign_comparison['spend'] / campaign_comparison['installs']).round(2)
campaign_comparison['roi'] = ((campaign_comparison['revenue'] - campaign_comparison['spend']) / campaign_comparison['spend'] * 100).round(2)

# Sort by the selected metric
campaign_comparison = campaign_comparison.sort_values(by=comparison_metric, ascending=False)

# Create bar chart
fig = px.bar(
    campaign_comparison,
    x='campaign_name',
    y=comparison_metric,
    title=f"Campaign Comparison by {comparison_metric.replace('_', ' ').title()}",
    labels={'campaign_name': 'Campaign', comparison_metric: comparison_metric.replace('_', ' ').title()}
)

st.plotly_chart(fig, use_container_width=True)

# Platform analysis
st.subheader("Performance by Platform")

# Group by platform
platform_comparison = filtered_data.groupby('platform').agg({
    'impressions': 'sum',
    'clicks': 'sum',
    'installs': 'sum',
    'spend': 'sum',
    'revenue': 'sum'
}).reset_index()

# Calculate metrics
platform_comparison['ctr'] = (platform_comparison['clicks'] / platform_comparison['impressions'] * 100).round(2)
platform_comparison['conversion_rate'] = (platform_comparison['installs'] / platform_comparison['clicks'] * 100).round(2)
platform_comparison['cpa'] = (platform_comparison['spend'] / platform_comparison['installs']).round(2)
platform_comparison['roi'] = ((platform_comparison['revenue'] - platform_comparison['spend']) / platform_comparison['spend'] * 100).round(2)

# Multiple metric comparison by platform
platform_metrics = st.multiselect(
    "Select Platform Metrics to Display",
    ["conversion_rate", "cpa", "ctr", "roi"],
    default=["conversion_rate", "cpa"]
)

if platform_metrics:
    # Create bar charts for each metric
    fig = px.bar(
        platform_comparison, 
        x='platform', 
        y=platform_metrics,
        barmode='group',
        title="Platform Performance Comparison",
        labels={
            'platform': 'Platform',
            'value': 'Value',
            'variable': 'Metric'
        }
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Tabular data
st.subheader("Campaign Performance Data")

# Get metrics for display
display_columns = ['campaign_name', 'impressions', 'clicks', 'installs', 'spend', 'revenue', 'ctr', 'conversion_rate', 'cpa', 'roi']

# Group by campaign
campaign_table = filtered_data.groupby('campaign_name').agg({
    'impressions': 'sum',
    'clicks': 'sum',
    'installs': 'sum',
    'spend': 'sum',
    'revenue': 'sum'
}).reset_index()

# Calculate metrics
campaign_table['ctr'] = (campaign_table['clicks'] / campaign_table['impressions'] * 100).round(2)
campaign_table['conversion_rate'] = (campaign_table['installs'] / campaign_table['clicks'] * 100).round(2)
campaign_table['cpa'] = (campaign_table['spend'] / campaign_table['installs']).round(2)
campaign_table['roi'] = ((campaign_table['revenue'] - campaign_table['spend']) / campaign_table['spend'] * 100).round(2)

# Format numeric columns
formatted_table = campaign_table.copy()
formatted_table['impressions'] = formatted_table['impressions'].apply(lambda x: f"{x:,.0f}")
formatted_table['clicks'] = formatted_table['clicks'].apply(lambda x: f"{x:,.0f}")
formatted_table['installs'] = formatted_table['installs'].apply(lambda x: f"{x:,.0f}")
formatted_table['spend'] = formatted_table['spend'].apply(lambda x: f"${x:,.2f}")
formatted_table['revenue'] = formatted_table['revenue'].apply(lambda x: f"${x:,.2f}")
formatted_table['ctr'] = formatted_table['ctr'].apply(lambda x: f"{x:.2f}%")
formatted_table['conversion_rate'] = formatted_table['conversion_rate'].apply(lambda x: f"{x:.2f}%")
formatted_table['cpa'] = formatted_table['cpa'].apply(lambda x: f"${x:.2f}")
formatted_table['roi'] = formatted_table['roi'].apply(lambda x: f"{x:.2f}%")

# Display the table
st.dataframe(formatted_table[display_columns], use_container_width=True)

# Return to Main Dashboard
st.sidebar.markdown("---")
st.sidebar.markdown("[Return to Main Dashboard](/)")
