import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import numpy as np

def create_map_visualization(data):
    """
    Create a choropleth map visualization of performance by region
    
    Parameters:
    - data: DataFrame containing geo data
    
    Returns:
    - fig: Plotly figure object
    """
    # Check if we have standard regions or country codes
    if 'region' in data.columns:
        # Map general regions to country codes for visualization
        region_mapping = {
            'North America': ['USA', 'CAN', 'MEX'],
            'South America': ['BRA', 'ARG', 'COL', 'PER', 'CHL'],
            'Europe': ['GBR', 'DEU', 'FRA', 'ITA', 'ESP', 'NLD', 'PRT', 'POL'],
            'Asia Pacific': ['JPN', 'CHN', 'IND', 'AUS', 'KOR', 'IDN', 'SGP', 'MYS', 'PHL', 'THA'],
            'Middle East': ['SAU', 'ARE', 'ISR', 'QAT', 'TUR'],
            'Africa': ['ZAF', 'EGY', 'NGA', 'KEN', 'MAR']
        }
        
        # Create a country-level dataset from the regional data
        country_rows = []
        
        for _, row in data.groupby('region').agg({
            'conversion_rate': 'mean',
            'cpa': 'mean',
            'cltv': 'mean',
            'roi': 'mean'
        }).reset_index().iterrows():
            region = row['region']
            for country_code in region_mapping.get(region, []):
                country_rows.append({
                    'iso_alpha': country_code,
                    'region': region,
                    'conversion_rate': row['conversion_rate'],
                    'cpa': row['cpa'],
                    'cltv': row['cltv'],
                    'roi': row['roi']
                })
        
        geo_data = pd.DataFrame(country_rows)
        
    else:
        # Assuming we have country codes in the data
        geo_data = data.copy()
    
    # Create the choropleth map
    fig = px.choropleth(
        geo_data,
        locations='iso_alpha',
        color='conversion_rate',
        hover_name='region',
        hover_data={
            'iso_alpha': False,
            'conversion_rate': ':.2f%',
            'cpa': ':$.2f',
            'cltv': ':$.2f',
            'roi': ':.2f%'
        },
        color_continuous_scale=px.colors.sequential.Bluered,
        projection='natural earth',
        title='Conversion Rate by Region'
    )
    
    fig.update_layout(
        margin={"r":0,"t":30,"l":0,"b":0},
        coloraxis_colorbar=dict(
            title='Conversion Rate',
            tickformat='.1f%'
        )
    )
    
    return fig

def create_platform_chart(data):
    """
    Create a visualization comparing performance across different platforms
    
    Parameters:
    - data: DataFrame containing platform data
    
    Returns:
    - fig: Plotly figure object
    """
    if 'platform' not in data.columns:
        return px.bar(
            pd.DataFrame({
                'platform': ['No platform data available'],
                'value': [0]
            }),
            x='platform',
            y='value',
            title='Platform data not available'
        )
    
    # Group data by platform
    platform_metrics = data.groupby('platform').agg({
        'conversion_rate': 'mean',
        'cpa': 'mean',
        'cltv': 'mean',
        'roi': 'mean'
    }).reset_index()
    
    # Create a grouped bar chart
    fig = go.Figure()
    
    metrics = [
        {'name': 'Conversion Rate (%)', 'column': 'conversion_rate', 'format': '.2f'},
        {'name': 'CPA ($)', 'column': 'cpa', 'format': '.2f'},
        {'name': 'CLTV ($)', 'column': 'cltv', 'format': '.2f'},
        {'name': 'ROI (%)', 'column': 'roi', 'format': '.2f'}
    ]
    
    for metric in metrics:
        fig.add_trace(go.Bar(
            x=platform_metrics['platform'],
            y=platform_metrics[metric['column']],
            name=metric['name'],
            hovertemplate=f"{metric['name']}: %{{y:{metric['format']}}}<extra></extra>"
        ))
    
    fig.update_layout(
        title='Platform Performance Comparison',
        xaxis_title='Platform',
        yaxis_title='Value',
        barmode='group',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def create_kpi_metric(data, title, column, unit='', help_text=''):
    """
    Create a KPI metric card for the dashboard
    
    Parameters:
    - data: DataFrame containing the metric
    - title: Title of the metric
    - column: Column name in the DataFrame
    - unit: Unit symbol (%, $, etc.)
    - help_text: Help text for the metric
    """
    if column in data.columns:
        value = data[column].mean()
        
        # Format based on unit
        if unit == '%':
            formatted_value = f"{value:.2f}%"
        elif unit == '$':
            formatted_value = f"${value:.2f}"
        else:
            formatted_value = f"{value:.2f}{unit}"
        
        st.metric(title, formatted_value, help=help_text)
    else:
        st.metric(title, "N/A", help=help_text)

def create_sales_funnel(data):
    """
    Create a sales funnel visualization
    
    Parameters:
    - data: DataFrame containing funnel stage data
    
    Returns:
    - fig: Plotly figure object
    """
    # Check necessary columns exist
    required_cols = ['impressions', 'clicks', 'installs', 'purchases']
    if not all(col in data.columns for col in required_cols):
        # Create placeholder funnel with whatever data we have
        stages = []
        values = []
        
        for col in ['impressions', 'clicks', 'installs', 'users', 'purchases']:
            if col in data.columns:
                stages.append(col.title())
                values.append(data[col].sum())
        
        if not stages:
            # No funnel data available
            return px.funnel(
                pd.DataFrame({
                    'Stage': ['No funnel data available'],
                    'Value': [0]
                }),
                x='Value',
                y='Stage',
                title='Funnel data not available'
            )
    else:
        # Create funnel with all stages
        stages = ['Impressions', 'Clicks', 'Installs', 'Purchases']
        values = [
            data['impressions'].sum(),
            data['clicks'].sum(),
            data['installs'].sum(),
            data['purchases'].sum()
        ]
    
    # Create funnel dataframe
    funnel_df = pd.DataFrame({
        'Stage': stages,
        'Value': values
    })
    
    # Create funnel chart
    fig = px.funnel(
        funnel_df,
        x='Value',
        y='Stage',
        title='Marketing and Sales Funnel'
    )
    
    # Add conversion rate annotations
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
    
    return fig

def create_time_series_chart(data, metric, title=None, color_column=None):
    """
    Create a time series chart for a specific metric
    
    Parameters:
    - data: DataFrame containing time series data
    - metric: Column name of the metric to plot
    - title: Chart title (optional)
    - color_column: Column name to use for color grouping (optional)
    
    Returns:
    - fig: Plotly figure object
    """
    if 'date' not in data.columns or metric not in data.columns:
        # Return an empty chart with a message
        fig = go.Figure()
        fig.add_annotation(
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            text="Time series data not available",
            showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Group data by date and optionally by the color column
    if color_column and color_column in data.columns:
        # Group by date and the color column
        grouped_data = data.groupby(['date', color_column]).agg({
            metric: 'mean'
        }).reset_index()
        
        # Create line chart with color
        fig = px.line(
            grouped_data,
            x='date',
            y=metric,
            color=color_column,
            title=title or f"{metric.replace('_', ' ').title()} Over Time",
            labels={
                'date': 'Date',
                metric: metric.replace('_', ' ').title()
            }
        )
    else:
        # Group by date only
        grouped_data = data.groupby('date').agg({
            metric: 'mean'
        }).reset_index()
        
        # Create line chart without color
        fig = px.line(
            grouped_data,
            x='date',
            y=metric,
            title=title or f"{metric.replace('_', ' ').title()} Over Time",
            labels={
                'date': 'Date',
                metric: metric.replace('_', ' ').title()
            }
        )
    
    # Format y-axis labels based on metric type
    if metric in ['ctr', 'conversion_rate', 'roi', 'retention']:
        fig.update_layout(
            yaxis=dict(ticksuffix='%')
        )
    elif metric in ['cpa', 'spend', 'revenue', 'cltv', 'arpu']:
        fig.update_layout(
            yaxis=dict(tickprefix='$')
        )
    
    return fig
