import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils import filter_data_by_date, filter_data_by_platform, filter_data_by_region, filter_data_by_campaign, get_color_scale

st.set_page_config(
    page_title="Geo & Platform Insights | Marketing Dashboard",
    page_icon="🌍",
    layout="wide"
)

# Title
st.title("🌍 Geo & Platform Intelligence")

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

# Apply filters
filtered_data = combined_data.copy()
filtered_data = filter_data_by_date(filtered_data, start_date, end_date)
if selected_campaigns:
    filtered_data = filter_data_by_campaign(filtered_data, selected_campaigns)
if selected_platforms:
    filtered_data = filter_data_by_platform(filtered_data, selected_platforms)

# Check if we have data after filtering
if filtered_data.empty:
    st.warning("No data available with the current filter settings.")
    st.stop()

# Geo Intelligence Section
st.subheader("Geographic Performance Insights")

# Select metric for geo analysis
geo_metric = st.selectbox(
    "Select Geographic Analysis Metric",
    ["conversion_rate", "cpa", "cltv", "roi", "arpu"],
    format_func=lambda x: {
        "conversion_rate": "Conversion Rate (%)",
        "cpa": "Cost Per Acquisition ($)",
        "cltv": "Customer Lifetime Value ($)",
        "roi": "Return on Investment (%)",
        "arpu": "Average Revenue Per User ($)"
    }.get(x, x.replace('_', ' ').title())
)

# Prepare data for map visualization
if 'region' in filtered_data.columns:
    # Map general regions to country codes for visualization
    region_mapping = {
        'North America': ['USA', 'CAN', 'MEX'],
        'South America': ['BRA', 'ARG', 'COL', 'PER', 'CHL'],
        'Europe': ['GBR', 'DEU', 'FRA', 'ITA', 'ESP', 'NLD', 'PRT', 'POL'],
        'Asia Pacific': ['JPN', 'CHN', 'IND', 'AUS', 'KOR', 'IDN', 'SGP', 'MYS', 'PHL', 'THA'],
        'Middle East': ['SAU', 'ARE', 'ISR', 'QAT', 'TUR'],
        'Africa': ['ZAF', 'EGY', 'NGA', 'KEN', 'MAR']
    }
    
    # Region-specific data
    region_data = filtered_data.groupby('region').agg({
        'conversion_rate': 'mean',
        'cpa': 'mean',
        'cltv': 'mean',
        'roi': 'mean',
        'arpu': 'mean',
        'spend': 'sum',
        'revenue': 'sum',
        'installs': 'sum',
        'purchases': 'sum'
    }).reset_index()
    
    # Create country-level data for choropleth map
    country_rows = []
    
    for _, row in region_data.iterrows():
        region = row['region']
        for country_code in region_mapping.get(region, []):
            country_rows.append({
                'iso_alpha': country_code,
                'region': region,
                'conversion_rate': row['conversion_rate'],
                'cpa': row['cpa'],
                'cltv': row['cltv'],
                'roi': row['roi'],
                'arpu': row['arpu'],
                'spend': row['spend'],
                'revenue': row['revenue'],
                'installs': row['installs'],
                'purchases': row['purchases']
            })
    
    geo_data = pd.DataFrame(country_rows)
    
    # Create choropleth map
    reversed_color_scale = True if geo_metric == 'cpa' else False
    
    if geo_metric in ['cpa', 'cltv', 'arpu']:
        hover_data = {
            'iso_alpha': False,
            'region': True,
            geo_metric: ':$.2f',
            'spend': ':$.2f',
            'revenue': ':$.2f'
        }
        color_bar_title = f"{geo_metric.replace('_', ' ').title()} ($)"
    else:
        hover_data = {
            'iso_alpha': False,
            'region': True,
            geo_metric: ':.2f%',
            'spend': ':$.2f',
            'revenue': ':$.2f'
        }
        color_bar_title = f"{geo_metric.replace('_', ' ').title()} (%)"
    
    fig = px.choropleth(
        geo_data,
        locations='iso_alpha',
        color=geo_metric,
        hover_name='region',
        hover_data=hover_data,
        color_continuous_scale=px.colors.sequential.Bluered_r if reversed_color_scale else px.colors.sequential.Bluered,
        projection='natural earth',
        title=f"{geo_metric.replace('_', ' ').title()} by Region"
    )
    
    fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        coloraxis_colorbar=dict(
            title=color_bar_title
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Top/Bottom 5 regions table
    st.subheader("Top and Bottom Performing Regions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # For CPA, lower is better so we sort ascending
        ascending = True if geo_metric == 'cpa' else False
        
        top_regions = region_data.sort_values(geo_metric, ascending=ascending).head(5)
        st.write(f"Top 5 Regions by {geo_metric.replace('_', ' ').title()}")
        
        # Format for display
        display_top = top_regions[['region', geo_metric, 'spend', 'revenue']].copy()
        
        if geo_metric in ['conversion_rate', 'roi']:
            display_top[geo_metric] = display_top[geo_metric].apply(lambda x: f"{x:.2f}%")
        elif geo_metric in ['cpa', 'cltv', 'arpu']:
            display_top[geo_metric] = display_top[geo_metric].apply(lambda x: f"${x:.2f}")
        
        display_top['spend'] = display_top['spend'].apply(lambda x: f"${x:.2f}")
        display_top['revenue'] = display_top['revenue'].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(display_top, use_container_width=True)
    
    with col2:
        # For CPA, higher is worse so we sort descending
        ascending = False if geo_metric == 'cpa' else True
        
        bottom_regions = region_data.sort_values(geo_metric, ascending=ascending).head(5)
        st.write(f"Bottom 5 Regions by {geo_metric.replace('_', ' ').title()}")
        
        # Format for display
        display_bottom = bottom_regions[['region', geo_metric, 'spend', 'revenue']].copy()
        
        if geo_metric in ['conversion_rate', 'roi']:
            display_bottom[geo_metric] = display_bottom[geo_metric].apply(lambda x: f"{x:.2f}%")
        elif geo_metric in ['cpa', 'cltv', 'arpu']:
            display_bottom[geo_metric] = display_bottom[geo_metric].apply(lambda x: f"${x:.2f}")
        
        display_bottom['spend'] = display_bottom['spend'].apply(lambda x: f"${x:.2f}")
        display_bottom['revenue'] = display_bottom['revenue'].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(display_bottom, use_container_width=True)

# Platform Intelligence Section
st.subheader("Platform Performance Insights")

# Get platform data
platform_data = filtered_data.groupby('platform').agg({
    'conversion_rate': 'mean',
    'cpa': 'mean',
    'cltv': 'mean',
    'roi': 'mean',
    'arpu': 'mean',
    'spend': 'sum',
    'revenue': 'sum',
    'impressions': 'sum',
    'clicks': 'sum',
    'installs': 'sum',
    'purchases': 'sum'
}).reset_index()

# Platform comparison metrics
platform_metrics = st.multiselect(
    "Select Platform Comparison Metrics",
    ["conversion_rate", "cpa", "cltv", "roi", "arpu"],
    default=["conversion_rate", "cpa", "roi"]
)

if platform_metrics:
    # Create a radar chart for comprehensive platform comparison
    categories = [metric.replace('_', ' ').title() for metric in platform_metrics]
    
    fig = go.Figure()
    
    for platform in platform_data['platform'].unique():
        platform_row = platform_data[platform_data['platform'] == platform]
        
        # Normalize values for radar chart (0-1 scale)
        values = []
        for metric in platform_metrics:
            min_val = platform_data[metric].min()
            max_val = platform_data[metric].max()
            val = platform_row[metric].values[0]
            
            # For metrics where lower is better (like CPA), invert normalization
            if metric in ['cpa']:
                if max_val > min_val:
                    norm_val = 1 - ((val - min_val) / (max_val - min_val))
                else:
                    norm_val = 0.5
            else:
                if max_val > min_val:
                    norm_val = (val - min_val) / (max_val - min_val)
                else:
                    norm_val = 0.5
            
            values.append(norm_val)
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself',
            name=platform
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        title="Platform Performance Comparison",
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Platform-specific metrics
st.subheader("Key Metrics by Platform")

# Create comparison bar charts
fig = go.Figure()
metric_units = {
    'conversion_rate': '%',
    'cpa': '$',
    'cltv': '$',
    'roi': '%',
    'arpu': '$'
}

for metric in platform_metrics:
    # For better visualization, format hover text based on metric type
    if metric in ['conversion_rate', 'roi']:
        hovertemplate = f"{metric.replace('_', ' ').title()}: %{{y:.2f}}%<extra></extra>"
    else:
        hovertemplate = f"{metric.replace('_', ' ').title()}: ${{'y:.2f}}<extra></extra>"
    
    fig.add_trace(go.Bar(
        x=platform_data['platform'],
        y=platform_data[metric],
        name=metric.replace('_', ' ').title(),
        hovertemplate=hovertemplate
    ))

fig.update_layout(
    title="Platform Comparison by Key Metrics",
    xaxis=dict(title="Platform"),
    yaxis=dict(title="Value"),
    barmode='group',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1
    )
)

st.plotly_chart(fig, use_container_width=True)

# Platform performance details table
st.subheader("Detailed Platform Performance")

# Format for display
display_platform = platform_data.copy()

# Format percentages and currency
percentage_cols = ['conversion_rate', 'roi']
currency_cols = ['cpa', 'cltv', 'arpu', 'spend', 'revenue']
count_cols = ['impressions', 'clicks', 'installs', 'purchases']

for col in percentage_cols:
    if col in display_platform.columns:
        display_platform[col] = display_platform[col].apply(lambda x: f"{x:.2f}%")

for col in currency_cols:
    if col in display_platform.columns:
        display_platform[col] = display_platform[col].apply(lambda x: f"${x:.2f}")

for col in count_cols:
    if col in display_platform.columns:
        display_platform[col] = display_platform[col].apply(lambda x: f"{x:,.0f}")

# Select columns to display
display_cols = ['platform']
display_cols.extend([col for col in platform_metrics if col in display_platform.columns])
display_cols.extend(['spend', 'revenue'])
display_cols.extend([col for col in count_cols if col in display_platform.columns])

st.dataframe(display_platform[display_cols], use_container_width=True)

# Cross-analysis: Platform performance by region
st.subheader("Cross-Analysis: Platform Performance by Region")

# Group by platform and region
platform_region_data = filtered_data.groupby(['platform', 'region']).agg({
    'conversion_rate': 'mean',
    'cpa': 'mean',
    'cltv': 'mean',
    'roi': 'mean',
    'spend': 'sum',
    'revenue': 'sum'
}).reset_index()

# Select metric for heatmap
heatmap_metric = st.selectbox(
    "Select Metric for Platform-Region Analysis",
    ["conversion_rate", "cpa", "cltv", "roi"],
    format_func=lambda x: {
        "conversion_rate": "Conversion Rate (%)",
        "cpa": "Cost Per Acquisition ($)",
        "cltv": "Customer Lifetime Value ($)",
        "roi": "Return on Investment (%)"
    }.get(x, x.replace('_', ' ').title())
)

# Create pivot table for heatmap
pivot_data = platform_region_data.pivot(index="platform", columns="region", values=heatmap_metric)

# Create heatmap
reversed_colorscale = True if heatmap_metric == 'cpa' else False

fig = px.imshow(
    pivot_data,
    labels=dict(
        x="Region", 
        y="Platform", 
        color=heatmap_metric.replace('_', ' ').title()
    ),
    color_continuous_scale='RdBu_r' if reversed_colorscale else 'RdBu',
    title=f"{heatmap_metric.replace('_', ' ').title()} by Platform and Region"
)

# Add text annotations
for i in range(len(pivot_data.index)):
    for j in range(len(pivot_data.columns)):
        value = pivot_data.iloc[i, j]
        if not pd.isna(value):
            if heatmap_metric in ['conversion_rate', 'roi']:
                text = f"{value:.2f}%"
            else:
                text = f"${value:.2f}"
            
            fig.add_annotation(
                x=j,
                y=i,
                text=text,
                showarrow=False,
                font=dict(color="black")
            )

fig.update_layout(
    xaxis=dict(title="Region"),
    yaxis=dict(title="Platform")
)

st.plotly_chart(fig, use_container_width=True)

# Budget Allocation Recommendations
st.subheader("Budget Allocation Recommendations")

# Create budget allocation recommendations based on performance
if 'spend' in filtered_data.columns and 'revenue' in filtered_data.columns:
    # Group by platform and region
    allocation_data = filtered_data.groupby(['platform', 'region']).agg({
        'spend': 'sum',
        'revenue': 'sum',
        'roi': 'mean',
        'conversion_rate': 'mean'
    }).reset_index()
    
    # Calculate ROI and revenue metrics
    allocation_data['roi'] = ((allocation_data['revenue'] - allocation_data['spend']) / allocation_data['spend'] * 100).round(2)
    allocation_data['revenue_per_dollar'] = (allocation_data['revenue'] / allocation_data['spend']).round(2)
    
    # Calculate allocation score (weighted combination of ROI and conversion rate)
    allocation_data['allocation_score'] = (
        0.7 * (allocation_data['roi'] / allocation_data['roi'].max() if allocation_data['roi'].max() > 0 else 0) +
        0.3 * (allocation_data['conversion_rate'] / allocation_data['conversion_rate'].max() if allocation_data['conversion_rate'].max() > 0 else 0)
    ).round(2)
    
    # Sort by allocation score
    top_allocations = allocation_data.sort_values('allocation_score', ascending=False).head(10)
    
    # Create recommendations table
    recommendations = top_allocations[['platform', 'region', 'roi', 'conversion_rate', 'revenue_per_dollar', 'allocation_score']].copy()
    
    # Format for display
    recommendations['roi'] = recommendations['roi'].apply(lambda x: f"{x:.2f}%")
    recommendations['conversion_rate'] = recommendations['conversion_rate'].apply(lambda x: f"{x:.2f}%")
    recommendations['revenue_per_dollar'] = recommendations['revenue_per_dollar'].apply(lambda x: f"${x:.2f}")
    
    st.write("Top 10 Platform-Region Combinations for Budget Allocation")
    st.dataframe(recommendations, use_container_width=True)
    
    # Create a bubble chart showing allocation recommendations
    fig = px.scatter(
        top_allocations,
        x='roi',
        y='conversion_rate',
        size='revenue',
        color='platform',
        hover_name='region',
        hover_data={
            'roi': ':.2f%',
            'conversion_rate': ':.2f%',
            'revenue': ':$.2f',
            'spend': ':$.2f',
            'allocation_score': ':.2f'
        },
        size_max=60,
        title="Budget Allocation Recommendations (Bubble Size = Revenue)"
    )
    
    fig.update_layout(
        xaxis=dict(title="ROI (%)"),
        yaxis=dict(title="Conversion Rate (%)"),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Budget allocation by platform
    st.subheader("Recommended Budget Distribution by Platform")
    
    # Calculate optimal budget allocation by platform based on performance
    platform_allocation = allocation_data.groupby('platform').agg({
        'allocation_score': 'mean',
        'spend': 'sum',
        'revenue': 'sum'
    }).reset_index()
    
    # Calculate recommended allocation percentage
    total_score = platform_allocation['allocation_score'].sum()
    platform_allocation['recommended_percentage'] = (platform_allocation['allocation_score'] / total_score * 100).round(2)
    platform_allocation['current_percentage'] = (platform_allocation['spend'] / platform_allocation['spend'].sum() * 100).round(2)
    platform_allocation['adjustment'] = (platform_allocation['recommended_percentage'] - platform_allocation['current_percentage']).round(2)
    
    # Sort by recommended percentage
    platform_allocation = platform_allocation.sort_values('recommended_percentage', ascending=False)
    
    # Create comparison chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=platform_allocation['platform'],
        y=platform_allocation['current_percentage'],
        name='Current Budget %',
        marker_color='lightblue'
    ))
    
    fig.add_trace(go.Bar(
        x=platform_allocation['platform'],
        y=platform_allocation['recommended_percentage'],
        name='Recommended Budget %',
        marker_color='darkblue'
    ))
    
    # Add adjustment arrows
    for i, row in platform_allocation.iterrows():
        adjustment = row['adjustment']
        color = 'green' if adjustment > 0 else 'red'
        arrow = '↑' if adjustment > 0 else '↓'
        
        fig.add_annotation(
            x=row['platform'],
            y=max(row['current_percentage'], row['recommended_percentage']) + 5,
            text=f"{arrow} {abs(adjustment):.1f}%",
            showarrow=False,
            font=dict(color=color, size=14)
        )
    
    fig.update_layout(
        title="Current vs. Recommended Budget Allocation by Platform",
        xaxis=dict(title="Platform"),
        yaxis=dict(title="Budget Allocation (%)"),
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Return to Main Dashboard
st.sidebar.markdown("---")
st.sidebar.markdown("[Return to Main Dashboard](/)")
