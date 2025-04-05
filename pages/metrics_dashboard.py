import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils import filter_data_by_date, filter_data_by_platform, filter_data_by_region, filter_data_by_campaign
from visualization import create_time_series_chart, create_kpi_metric

st.set_page_config(
    page_title="Key Metrics | Marketing Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("📊 Key Performance Metrics Dashboard")

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

# Time period comparison toggle
compare_periods = st.sidebar.checkbox("Compare Time Periods", value=False)
if compare_periods:
    comparison_period = st.sidebar.selectbox(
        "Comparison Period",
        ["Previous Period", "Same Period Last Year", "Custom Period"]
    )
    
    if comparison_period == "Custom Period":
        comparison_start = st.sidebar.date_input("Comparison Start Date", 
                                               min_date, 
                                               min_value=min_date, 
                                               max_value=max_date)
        comparison_end = st.sidebar.date_input("Comparison End Date", 
                                             min_date + (max_date - min_date)//2, 
                                             min_value=min_date, 
                                             max_value=max_date)
    else:
        # Automatically calculate comparison period
        current_range = (end_date - start_date).days
        if comparison_period == "Previous Period":
            comparison_start = start_date - pd.Timedelta(days=current_range)
            comparison_end = start_date - pd.Timedelta(days=1)
        else:  # Same Period Last Year
            comparison_start = start_date - pd.Timedelta(days=365)
            comparison_end = end_date - pd.Timedelta(days=365)

# Apply filters
filtered_data = combined_data.copy()
filtered_data = filter_data_by_date(filtered_data, start_date, end_date)
if selected_campaigns:
    filtered_data = filter_data_by_campaign(filtered_data, selected_campaigns)
if selected_platforms:
    filtered_data = filter_data_by_platform(filtered_data, selected_platforms)
if selected_regions:
    filtered_data = filter_data_by_region(filtered_data, selected_regions)

# If comparing periods, prepare comparison data
if compare_periods:
    comparison_data = combined_data.copy()
    comparison_data = filter_data_by_date(comparison_data, comparison_start, comparison_end)
    if selected_campaigns:
        comparison_data = filter_data_by_campaign(comparison_data, selected_campaigns)
    if selected_platforms:
        comparison_data = filter_data_by_platform(comparison_data, selected_platforms)
    if selected_regions:
        comparison_data = filter_data_by_region(comparison_data, selected_regions)

# Check if we have data after filtering
if filtered_data.empty:
    st.warning("No data available with the current filter settings.")
    st.stop()

# Main metrics section
st.subheader("Key Performance Indicators")

# Create metrics row
col1, col2, col3, col4 = st.columns(4)

# Function to calculate and display metric with comparison
def display_metric(col_obj, title, value, unit="", help_text=""):
    if compare_periods and not comparison_data.empty:
        current_value = value
        comparison_value = comparison_data[column].mean() if column in comparison_data.columns else 0
        
        if comparison_value != 0:
            change_pct = ((current_value - comparison_value) / comparison_value) * 100
            
            # Format display values
            if unit == "%":
                current_formatted = f"{current_value:.2f}%"
                delta_formatted = f"{change_pct:.1f}%"
            elif unit == "$":
                current_formatted = f"${current_value:.2f}"
                delta_formatted = f"{change_pct:.1f}%"
            else:
                current_formatted = f"{current_value:.2f}{unit}"
                delta_formatted = f"{change_pct:.1f}%"
            
            col_obj.metric(
                title,
                current_formatted,
                delta_formatted,
                help=help_text
            )
        else:
            # Format without comparison
            if unit == "%":
                current_formatted = f"{current_value:.2f}%"
            elif unit == "$":
                current_formatted = f"${current_value:.2f}"
            else:
                current_formatted = f"{current_value:.2f}{unit}"
            
            col_obj.metric(title, current_formatted, help=help_text)
    else:
        # No comparison, just display the current value
        if unit == "%":
            current_formatted = f"{value:.2f}%"
        elif unit == "$":
            current_formatted = f"${value:.2f}"
        else:
            current_formatted = f"{value:.2f}{unit}"
        
        col_obj.metric(title, current_formatted, help=help_text)

# Calculate and display key metrics
with col1:
    if 'conversion_rate' in filtered_data.columns:
        conversion_rate = filtered_data['conversion_rate'].mean()
        display_metric(
            col1,
            "Conversion Rate",
            conversion_rate,
            "%",
            "Average conversion rate across all campaigns"
        )
    else:
        st.metric("Conversion Rate", "N/A")

with col2:
    if 'cpa' in filtered_data.columns:
        cpa = filtered_data['cpa'].mean()
        display_metric(
            col2,
            "Cost Per Acquisition",
            cpa,
            "$",
            "Average cost to acquire a customer"
        )
    else:
        st.metric("Cost Per Acquisition", "N/A")

with col3:
    if 'cltv' in filtered_data.columns:
        cltv = filtered_data['cltv'].mean()
        display_metric(
            col3,
            "Customer Lifetime Value",
            cltv,
            "$",
            "Average revenue generated per customer over their lifetime"
        )
    else:
        st.metric("Customer Lifetime Value", "N/A")

with col4:
    if 'roi' in filtered_data.columns:
        roi = filtered_data['roi'].mean()
        display_metric(
            col4,
            "Return on Investment",
            roi,
            "%",
            "Average return on investment across all campaigns"
        )
    else:
        st.metric("Return on Investment", "N/A")

# Secondary metrics row
col1, col2, col3, col4 = st.columns(4)

with col1:
    if 'ctr' in filtered_data.columns:
        ctr = filtered_data['ctr'].mean()
        display_metric(
            col1,
            "Click-Through Rate",
            ctr,
            "%",
            "Percentage of impressions that resulted in clicks"
        )
    elif all(col in filtered_data.columns for col in ['clicks', 'impressions']):
        ctr = (filtered_data['clicks'].sum() / filtered_data['impressions'].sum() * 100)
        display_metric(
            col1,
            "Click-Through Rate",
            ctr,
            "%",
            "Percentage of impressions that resulted in clicks"
        )
    else:
        st.metric("Click-Through Rate", "N/A")

with col2:
    if 'bounce_rate' in filtered_data.columns:
        bounce_rate = filtered_data['bounce_rate'].mean()
        display_metric(
            col2,
            "Bounce Rate",
            bounce_rate,
            "%",
            "Percentage of visitors who navigate away after viewing only one page"
        )
    else:
        st.metric("Bounce Rate", "N/A")

with col3:
    if all(col in filtered_data.columns for col in ['revenue', 'users']):
        arpu = filtered_data['revenue'].sum() / filtered_data['users'].sum() if filtered_data['users'].sum() > 0 else 0
        display_metric(
            col3,
            "Avg. Revenue Per User",
            arpu,
            "$",
            "Average revenue generated per user"
        )
    elif 'arpu' in filtered_data.columns:
        arpu = filtered_data['arpu'].mean()
        display_metric(
            col3,
            "Avg. Revenue Per User",
            arpu,
            "$",
            "Average revenue generated per user"
        )
    else:
        st.metric("Avg. Revenue Per User", "N/A")

with col4:
    if all(col in filtered_data.columns for col in ['spend', 'clicks']):
        cpc = filtered_data['spend'].sum() / filtered_data['clicks'].sum() if filtered_data['clicks'].sum() > 0 else 0
        display_metric(
            col4,
            "Cost Per Click",
            cpc,
            "$",
            "Average cost per click across all campaigns"
        )
    else:
        st.metric("Cost Per Click", "N/A")

# Metrics Over Time
st.subheader("Metrics Trends Over Time")

# Select metrics for time series
time_series_metrics = st.multiselect(
    "Select Metrics to Visualize",
    ["conversion_rate", "cpa", "cltv", "roi", "ctr", "bounce_rate", "arpu"],
    default=["conversion_rate", "cpa", "roi"]
)

if time_series_metrics:
    # Group data by date
    time_series_data = filtered_data.groupby('date').agg({
        metric: 'mean' for metric in time_series_metrics if metric in filtered_data.columns
    }).reset_index()
    
    # If comparing periods, prepare comparison time series
    if compare_periods and not comparison_data.empty:
        comparison_time_series = comparison_data.groupby('date').agg({
            metric: 'mean' for metric in time_series_metrics if metric in comparison_data.columns
        }).reset_index()
        
        # Align dates for comparison (shift comparison dates to align with current period)
        time_diff = (filtered_data['date'].min() - comparison_data['date'].min()).days
        comparison_time_series['aligned_date'] = comparison_time_series['date'] + pd.Timedelta(days=time_diff)
    
    # Create time series visualization
    fig = go.Figure()
    
    for metric in time_series_metrics:
        if metric in time_series_data.columns:
            # Format based on metric type
            if metric in ['conversion_rate', 'ctr', 'bounce_rate', 'roi']:
                hovertemplate = f"{metric.replace('_', ' ').title()}: %{{y:.2f}}%<extra></extra>"
            elif metric in ['cpa', 'cltv', 'arpu']:
                hovertemplate = f"{metric.replace('_', ' ').title()}: ${{'y:.2f}}<extra></extra>"
            else:
                hovertemplate = f"{metric.replace('_', ' ').title()}: %{{y:.2f}}<extra></extra>"
            
            # Add current period line
            fig.add_trace(go.Scatter(
                x=time_series_data['date'],
                y=time_series_data[metric],
                mode='lines+markers',
                name=f"{metric.replace('_', ' ').title()} (Current)",
                hovertemplate=hovertemplate
            ))
            
            # Add comparison period line if applicable
            if compare_periods and not comparison_data.empty and metric in comparison_time_series.columns:
                fig.add_trace(go.Scatter(
                    x=comparison_time_series['aligned_date'],
                    y=comparison_time_series[metric],
                    mode='lines+markers',
                    name=f"{metric.replace('_', ' ').title()} (Comparison)",
                    line=dict(dash='dash'),
                    opacity=0.7,
                    hovertemplate=hovertemplate
                ))
    
    fig.update_layout(
        title="Metrics Trends Over Time",
        xaxis_title="Date",
        yaxis_title="Value",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode="x unified"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Metrics breakdown
st.subheader("Metrics Breakdown by Dimension")

# Select dimension and metric for breakdown
col1, col2 = st.columns(2)

with col1:
    breakdown_dimension = st.selectbox(
        "Select Dimension",
        ["platform", "region", "campaign_name"],
        format_func=lambda x: {
            "platform": "Platform",
            "region": "Region",
            "campaign_name": "Campaign"
        }.get(x, x.replace('_', ' ').title())
    )

with col2:
    breakdown_metric = st.selectbox(
        "Select Metric",
        ["conversion_rate", "cpa", "cltv", "roi", "ctr", "bounce_rate", "arpu"],
        format_func=lambda x: {
            "conversion_rate": "Conversion Rate (%)",
            "cpa": "Cost Per Acquisition ($)",
            "cltv": "Customer Lifetime Value ($)",
            "roi": "Return on Investment (%)",
            "ctr": "Click-Through Rate (%)",
            "bounce_rate": "Bounce Rate (%)",
            "arpu": "Average Revenue Per User ($)"
        }.get(x, x.replace('_', ' ').title())
    )

# Check if selected metric exists in data
if breakdown_metric not in filtered_data.columns:
    st.warning(f"The selected metric '{breakdown_metric}' is not available in the current dataset.")
else:
    # Group by selected dimension
    dimension_breakdown = filtered_data.groupby(breakdown_dimension).agg({
        breakdown_metric: 'mean',
        'spend': 'sum',
        'revenue': 'sum'
    }).reset_index()
    
    # Sort by the metric
    if breakdown_metric == 'cpa':
        # For CPA, lower is better
        dimension_breakdown = dimension_breakdown.sort_values(breakdown_metric)
    else:
        # For other metrics, higher is better
        dimension_breakdown = dimension_breakdown.sort_values(breakdown_metric, ascending=False)
    
    # Create visualization
    if breakdown_metric in ['conversion_rate', 'ctr', 'bounce_rate', 'roi']:
        # Percentage metrics
        format_str = '.2f%'
        title_suffix = "(%)"
    elif breakdown_metric in ['cpa', 'cltv', 'arpu']:
        # Currency metrics
        format_str = '$.2f'
        title_suffix = "($)"
    else:
        format_str = '.2f'
        title_suffix = ""
    
    fig = px.bar(
        dimension_breakdown,
        x=breakdown_dimension,
        y=breakdown_metric,
        color=breakdown_metric,
        color_continuous_scale='RdBu_r' if breakdown_metric == 'cpa' else 'RdBu',
        hover_data=['spend', 'revenue'],
        labels={
            breakdown_dimension: breakdown_dimension.replace('_', ' ').title(),
            breakdown_metric: breakdown_metric.replace('_', ' ').title(),
            'spend': 'Total Spend ($)',
            'revenue': 'Total Revenue ($)'
        },
        title=f"{breakdown_metric.replace('_', ' ').title()} by {breakdown_dimension.replace('_', ' ').title()} {title_suffix}"
    )
    
    # Format hover data
    fig.update_traces(
        hovertemplate=(
            f"<b>%{{x}}</b><br>" +
            f"{breakdown_metric.replace('_', ' ').title()}: %{{y:{format_str}}}<br>" +
            "Total Spend: $%{customdata[0]:.2f}<br>" +
            "Total Revenue: $%{customdata[1]:.2f}<br>" +
            "<extra></extra>"
        )
    )
    
    fig.update_layout(
        xaxis_title=breakdown_dimension.replace('_', ' ').title(),
        yaxis_title=breakdown_metric.replace('_', ' ').title()
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Correlation Analysis
st.subheader("Metric Correlation Analysis")

# Select metrics for correlation
correlation_metrics = st.multiselect(
    "Select Metrics for Correlation Analysis",
    ["conversion_rate", "cpa", "cltv", "roi", "ctr", "bounce_rate", "arpu", "spend", "revenue"],
    default=["conversion_rate", "cpa", "roi", "spend", "revenue"]
)

if len(correlation_metrics) >= 2:
    # Get only the selected metrics
    correlation_data = filtered_data[correlation_metrics].copy()
    
    # Calculate correlation matrix
    corr_matrix = correlation_data.corr()
    
    # Create heatmap
    fig = px.imshow(
        corr_matrix,
        x=correlation_metrics,
        y=correlation_metrics,
        color_continuous_scale='RdBu_r',
        labels=dict(color="Correlation"),
        title="Correlation Between Metrics"
    )
    
    # Add text annotations
    for i in range(len(correlation_metrics)):
        for j in range(len(correlation_metrics)):
            fig.add_annotation(
                x=j,
                y=i,
                text=f"{corr_matrix.iloc[i, j]:.2f}",
                showarrow=False,
                font=dict(color="white" if abs(corr_matrix.iloc[i, j]) > 0.5 else "black")
            )
    
    fig.update_layout(
        xaxis=dict(title=""),
        yaxis=dict(title="")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Key insights based on correlations
    st.subheader("Key Correlation Insights")
    
    # Find strong correlations (positive and negative)
    strong_positive = []
    strong_negative = []
    
    for i in range(len(correlation_metrics)):
        for j in range(i+1, len(correlation_metrics)):
            metric1 = correlation_metrics[i]
            metric2 = correlation_metrics[j]
            corr_value = corr_matrix.loc[metric1, metric2]
            
            if corr_value > 0.7:
                strong_positive.append((metric1, metric2, corr_value))
            elif corr_value < -0.7:
                strong_negative.append((metric1, metric2, corr_value))
    
    # Display insights
    if strong_positive:
        st.write("Strong Positive Correlations:")
        for metric1, metric2, corr in strong_positive:
            st.write(f"• **{metric1.replace('_', ' ').title()}** and **{metric2.replace('_', ' ').title()}** have a strong positive correlation ({corr:.2f}), meaning they tend to increase together.")
    
    if strong_negative:
        st.write("Strong Negative Correlations:")
        for metric1, metric2, corr in strong_negative:
            st.write(f"• **{metric1.replace('_', ' ').title()}** and **{metric2.replace('_', ' ').title()}** have a strong negative correlation ({corr:.2f}), meaning as one increases, the other tends to decrease.")
    
    if not strong_positive and not strong_negative:
        st.write("No strong correlations (above 0.7 or below -0.7) were found between the selected metrics.")

# ROI Analysis
st.subheader("Return on Investment (ROI) Analysis")

if all(col in filtered_data.columns for col in ['spend', 'revenue']):
    # Calculate total ROI
    total_spend = filtered_data['spend'].sum()
    total_revenue = filtered_data['revenue'].sum()
    total_roi = ((total_revenue - total_spend) / total_spend * 100) if total_spend > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Spend", f"${total_spend:,.2f}")
    
    with col2:
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
    
    with col3:
        st.metric("Overall ROI", f"{total_roi:.2f}%")
    
    # ROI by dimension (campaign, platform, region)
    roi_dimension = st.selectbox(
        "Analyze ROI by",
        ["campaign_name", "platform", "region"],
        format_func=lambda x: x.replace('_', ' ').title()
    )
    
    # Group by selected dimension
    roi_breakdown = filtered_data.groupby(roi_dimension).agg({
        'spend': 'sum',
        'revenue': 'sum'
    }).reset_index()
    
    # Calculate ROI
    roi_breakdown['roi'] = ((roi_breakdown['revenue'] - roi_breakdown['spend']) / roi_breakdown['spend'] * 100).round(2)
    roi_breakdown['profit'] = (roi_breakdown['revenue'] - roi_breakdown['spend']).round(2)
    
    # Sort by ROI
    roi_breakdown = roi_breakdown.sort_values('roi', ascending=False)
    
    # Create visualization
    fig = px.bar(
        roi_breakdown,
        x=roi_dimension,
        y='roi',
        color='roi',
        color_continuous_scale='RdYlGn',
        hover_data=['spend', 'revenue', 'profit'],
        labels={
            roi_dimension: roi_dimension.replace('_', ' ').title(),
            'roi': 'ROI (%)',
            'spend': 'Total Spend ($)',
            'revenue': 'Total Revenue ($)',
            'profit': 'Profit ($)'
        },
        title=f"ROI by {roi_dimension.replace('_', ' ').title()}"
    )
    
    # Add a reference line at 0% ROI
    fig.add_hline(
        y=0, 
        line_dash="dash", 
        line_color="red",
        annotation_text="Break-even point",
        annotation_position="top right"
    )
    
    # Format hover data
    fig.update_traces(
        hovertemplate=(
            f"<b>%{{x}}</b><br>" +
            "ROI: %{y:.2f}%<br>" +
            "Spend: $%{customdata[0]:,.2f}<br>" +
            "Revenue: $%{customdata[1]:,.2f}<br>" +
            "Profit: $%{customdata[2]:,.2f}<br>" +
            "<extra></extra>"
        )
    )
    
    fig.update_layout(
        xaxis_title=roi_dimension.replace('_', ' ').title(),
        yaxis_title="ROI (%)"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ROI distribution
    st.subheader("ROI Distribution Analysis")
    
    # Create a histogram of ROI values
    fig = px.histogram(
        roi_breakdown,
        x='roi',
        nbins=20,
        marginal="box",
        title="ROI Distribution",
        labels={'roi': 'ROI (%)'},
        color_discrete_sequence=['#3366CC']
    )
    
    # Add a reference line at 0% ROI
    fig.add_vline(
        x=0, 
        line_dash="dash", 
        line_color="red",
        annotation_text="Break-even",
        annotation_position="top"
    )
    
    # Add a reference line at average ROI
    avg_roi = roi_breakdown['roi'].mean()
    fig.add_vline(
        x=avg_roi, 
        line_dash="dash", 
        line_color="green",
        annotation_text=f"Avg: {avg_roi:.2f}%",
        annotation_position="top"
    )
    
    fig.update_layout(
        xaxis_title="ROI (%)",
        yaxis_title="Count"
    )
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("Spend and/or revenue data is not available for ROI analysis.")

# Advanced Metrics
st.subheader("Advanced Marketing Metrics")

# Calculate advanced metrics if data is available
advanced_metrics = {}

# Customer Acquisition Cost (CAC)
if all(col in filtered_data.columns for col in ['spend', 'users']):
    cac = filtered_data['spend'].sum() / filtered_data['users'].sum() if filtered_data['users'].sum() > 0 else 0
    advanced_metrics['Customer Acquisition Cost (CAC)'] = f"${cac:.2f}"

# CLTV to CAC Ratio
if all(col in filtered_data.columns for col in ['spend', 'users', 'cltv']):
    cac = filtered_data['spend'].sum() / filtered_data['users'].sum() if filtered_data['users'].sum() > 0 else 0
    cltv = filtered_data['cltv'].mean()
    cltv_cac_ratio = cltv / cac if cac > 0 else 0
    advanced_metrics['CLTV to CAC Ratio'] = f"{cltv_cac_ratio:.2f}"

# Conversion Rate by Stage
if all(col in filtered_data.columns for col in ['impressions', 'clicks', 'installs', 'purchases']):
    impression_to_click = filtered_data['clicks'].sum() / filtered_data['impressions'].sum() * 100 if filtered_data['impressions'].sum() > 0 else 0
    click_to_install = filtered_data['installs'].sum() / filtered_data['clicks'].sum() * 100 if filtered_data['clicks'].sum() > 0 else 0
    install_to_purchase = filtered_data['purchases'].sum() / filtered_data['installs'].sum() * 100 if filtered_data['installs'].sum() > 0 else 0
    
    advanced_metrics['Impression → Click Rate'] = f"{impression_to_click:.2f}%"
    advanced_metrics['Click → Install Rate'] = f"{click_to_install:.2f}%"
    advanced_metrics['Install → Purchase Rate'] = f"{install_to_purchase:.2f}%"

# Payback Period (if we have retention data)
if all(col in filtered_data.columns for col in ['cpa', 'arpu']):
    avg_cpa = filtered_data['cpa'].mean()
    avg_arpu = filtered_data['arpu'].mean()
    payback_period = avg_cpa / avg_arpu if avg_arpu > 0 else 0
    advanced_metrics['Payback Period'] = f"{payback_period:.2f} months"

# Display advanced metrics in a nice format
if advanced_metrics:
    cols = st.columns(3)
    for i, (metric, value) in enumerate(advanced_metrics.items()):
        cols[i % 3].metric(metric, value)
else:
    st.info("Advanced metrics could not be calculated with the available data.")

# Custom Date Range Comparison (side by side)
if compare_periods and not comparison_data.empty:
    st.subheader("Period Comparison Analysis")
    
    # Selected periods
    st.write(f"Current Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    st.write(f"Comparison Period: {comparison_start.strftime('%Y-%m-%d')} to {comparison_end.strftime('%Y-%m-%d')}")
    
    # Calculate key metrics for both periods
    metric_columns = ['conversion_rate', 'cpa', 'cltv', 'roi', 'ctr', 'arpu', 'spend', 'revenue']
    current_metrics = {}
    comparison_metrics = {}
    
    for metric in metric_columns:
        if metric in filtered_data.columns:
            if metric in ['spend', 'revenue']:
                current_metrics[metric] = filtered_data[metric].sum()
            else:
                current_metrics[metric] = filtered_data[metric].mean()
        
        if metric in comparison_data.columns:
            if metric in ['spend', 'revenue']:
                comparison_metrics[metric] = comparison_data[metric].sum()
            else:
                comparison_metrics[metric] = comparison_data[metric].mean()
    
    # Create a comparison table
    comparison_table = pd.DataFrame({
        'Metric': [metric.replace('_', ' ').title() for metric in current_metrics.keys()],
        'Current Period': current_metrics.values(),
        'Comparison Period': [comparison_metrics.get(metric, 0) for metric in current_metrics.keys()]
    })
    
    # Calculate change and percent change
    comparison_table['Absolute Change'] = comparison_table['Current Period'] - comparison_table['Comparison Period']
    comparison_table['Percent Change'] = ((comparison_table['Current Period'] - comparison_table['Comparison Period']) / 
                                         comparison_table['Comparison Period'] * 100)
    
    # Format metrics
    for i, metric in enumerate(current_metrics.keys()):
        if metric in ['conversion_rate', 'roi', 'ctr']:
            # Percentage metrics
            comparison_table.loc[i, 'Current Period'] = f"{comparison_table.loc[i, 'Current Period']:.2f}%"
            comparison_table.loc[i, 'Comparison Period'] = f"{comparison_table.loc[i, 'Comparison Period']:.2f}%"
            comparison_table.loc[i, 'Absolute Change'] = f"{comparison_table.loc[i, 'Absolute Change']:.2f}%"
        elif metric in ['cpa', 'cltv', 'arpu', 'spend', 'revenue']:
            # Currency metrics
            comparison_table.loc[i, 'Current Period'] = f"${comparison_table.loc[i, 'Current Period']:.2f}"
            comparison_table.loc[i, 'Comparison Period'] = f"${comparison_table.loc[i, 'Comparison Period']:.2f}"
            comparison_table.loc[i, 'Absolute Change'] = f"${comparison_table.loc[i, 'Absolute Change']:.2f}"
        
        # Format percent change
        comparison_table.loc[i, 'Percent Change'] = f"{comparison_table.loc[i, 'Percent Change']:.2f}%"
    
    st.dataframe(comparison_table, use_container_width=True)
    
    # Create a bar chart comparing key metrics
    st.subheader("Visual Period Comparison")
    
    # Select metrics for visual comparison
    visual_comparison_metrics = st.multiselect(
        "Select Metrics for Visual Comparison",
        list(current_metrics.keys()),
        default=['conversion_rate', 'roi']
    )
    
    if visual_comparison_metrics:
        # Prepare data for visualization
        comparison_viz_data = []
        
        for metric in visual_comparison_metrics:
            if metric in current_metrics and metric in comparison_metrics:
                comparison_viz_data.append({
                    'Metric': metric.replace('_', ' ').title(),
                    'Period': 'Current',
                    'Value': current_metrics[metric]
                })
                comparison_viz_data.append({
                    'Metric': metric.replace('_', ' ').title(),
                    'Period': 'Comparison',
                    'Value': comparison_metrics[metric]
                })
        
        comparison_viz_df = pd.DataFrame(comparison_viz_data)
        
        # Create grouped bar chart
        fig = px.bar(
            comparison_viz_df,
            x='Metric',
            y='Value',
            color='Period',
            barmode='group',
            title="Period Comparison by Metric",
            color_discrete_map={'Current': '#3366CC', 'Comparison': '#99B3E6'}
        )
        
        # Set y-axis to start at zero for fair comparison
        fig.update_layout(yaxis_range=[0, comparison_viz_df['Value'].max() * 1.2])
        
        # Add percentage change annotations
        for metric in visual_comparison_metrics:
            if metric in current_metrics and metric in comparison_metrics:
                current_val = current_metrics[metric]
                comparison_val = comparison_metrics[metric]
                
                if comparison_val != 0:
                    percent_change = ((current_val - comparison_val) / comparison_val) * 100
                    change_text = f"{percent_change:.1f}%"
                    color = "green" if percent_change > 0 else "red"
                    
                    fig.add_annotation(
                        x=metric.replace('_', ' ').title(),
                        y=max(current_val, comparison_val) * 1.05,
                        text=change_text,
                        showarrow=False,
                        font=dict(color=color, size=14)
                    )
        
        st.plotly_chart(fig, use_container_width=True)

# Return to Main Dashboard
st.sidebar.markdown("---")
st.sidebar.markdown("[Return to Main Dashboard](/)")
