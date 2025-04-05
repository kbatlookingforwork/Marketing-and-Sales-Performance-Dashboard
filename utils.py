import pandas as pd
import numpy as np
import streamlit as st
import io
import base64

def filter_data_by_date(data, start_date, end_date, date_column='date'):
    """
    Filter a DataFrame by date range
    
    Parameters:
    - data: DataFrame to filter
    - start_date: Start date for filtering
    - end_date: End date for filtering
    - date_column: Name of the date column
    
    Returns:
    - Filtered DataFrame
    """
    if date_column not in data.columns:
        return data
    
    # Ensure date column is datetime
    data[date_column] = pd.to_datetime(data[date_column])
    
    # Convert filter dates to datetime if they're not already
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Apply filter
    return data[(data[date_column] >= start_date) & (data[date_column] <= end_date)]

def filter_data_by_platform(data, platforms, platform_column='platform'):
    """
    Filter a DataFrame by platforms
    
    Parameters:
    - data: DataFrame to filter
    - platforms: List of platforms to include
    - platform_column: Name of the platform column
    
    Returns:
    - Filtered DataFrame
    """
    if platform_column not in data.columns or not platforms:
        return data
    
    return data[data[platform_column].isin(platforms)]

def filter_data_by_region(data, regions, region_column='region'):
    """
    Filter a DataFrame by regions
    
    Parameters:
    - data: DataFrame to filter
    - regions: List of regions to include
    - region_column: Name of the region column
    
    Returns:
    - Filtered DataFrame
    """
    if region_column not in data.columns or not regions:
        return data
    
    return data[data[region_column].isin(regions)]

def filter_data_by_campaign(data, campaigns, campaign_column='campaign_name'):
    """
    Filter a DataFrame by campaign names
    
    Parameters:
    - data: DataFrame to filter
    - campaigns: List of campaign names to include
    - campaign_column: Name of the campaign column
    
    Returns:
    - Filtered DataFrame
    """
    if campaign_column not in data.columns or not campaigns:
        return data
    
    return data[data[campaign_column].isin(campaigns)]

def calculate_conversion_metrics(data):
    """
    Calculate conversion metrics for marketing funnel
    
    Parameters:
    - data: DataFrame with marketing data
    
    Returns:
    - DataFrame with additional conversion metrics
    """
    df = data.copy()
    
    # Calculate Click-Through Rate (CTR)
    if all(col in df.columns for col in ['clicks', 'impressions']):
        df['ctr'] = (df['clicks'] / df['impressions'] * 100).round(2)
    
    # Calculate Conversion Rate
    if all(col in df.columns for col in ['installs', 'clicks']):
        df['conversion_rate'] = (df['installs'] / df['clicks'] * 100).round(2)
    
    # Calculate Cost Per Install (CPI)
    if all(col in df.columns for col in ['spend', 'installs']):
        df['cpi'] = (df['spend'] / df['installs']).round(2)
    
    # Calculate Cost Per Acquisition (CPA)
    if all(col in df.columns for col in ['spend', 'purchases']):
        df['cpa'] = (df['spend'] / df['purchases']).round(2)
    
    return df

def calculate_revenue_metrics(data):
    """
    Calculate revenue metrics for marketing campaigns
    
    Parameters:
    - data: DataFrame with marketing and sales data
    
    Returns:
    - DataFrame with additional revenue metrics
    """
    df = data.copy()
    
    # Calculate Return on Investment (ROI)
    if all(col in df.columns for col in ['revenue', 'spend']):
        df['roi'] = ((df['revenue'] - df['spend']) / df['spend'] * 100).round(2)
    
    # Calculate Average Revenue Per User (ARPU)
    if all(col in df.columns for col in ['revenue', 'users']):
        df['arpu'] = (df['revenue'] / df['users']).round(2)
    
    return df

def download_dataframe_as_csv(df, label="Download CSV"):
    """
    Create a download link for a DataFrame
    
    Parameters:
    - df: DataFrame to download
    - label: Text for the download button
    
    Returns:
    - Download link HTML
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="data.csv">{label}</a>'
    return href

def format_number(number, prefix="", suffix="", decimal_places=0):
    """
    Format a number with prefix, suffix and proper formatting
    
    Parameters:
    - number: Number to format
    - prefix: String prefix (e.g., '$')
    - suffix: String suffix (e.g., '%')
    - decimal_places: Number of decimal places to show
    
    Returns:
    - Formatted number string
    """
    if pd.isna(number):
        return "N/A"
    
    if isinstance(number, (int, float)):
        if abs(number) >= 1_000_000:
            return f"{prefix}{number/1_000_000:.{decimal_places}f}M{suffix}"
        elif abs(number) >= 1_000:
            return f"{prefix}{number/1_000:.{decimal_places}f}K{suffix}"
        else:
            return f"{prefix}{number:.{decimal_places}f}{suffix}"
    else:
        return str(number)

def get_color_scale(values, colorscale='RdYlGn', reverse=False):
    """
    Get a color scale for a series of values
    
    Parameters:
    - values: Series of values to create a color scale for
    - colorscale: Name of colorscale to use
    - reverse: Whether to reverse the colorscale
    
    Returns:
    - List of hex color codes
    """
    import plotly.colors as pc
    
    # Get min and max values
    min_val = min(values)
    max_val = max(values)
    
    # Create a normalized scale from 0-1
    normalized = [(val - min_val) / (max_val - min_val) if max_val > min_val else 0.5 for val in values]
    
    # Get color scale
    if reverse:
        normalized = [1 - val for val in normalized]
    
    # Use Plotly's color scale function
    colors = pc.sample_colorscale(
        pc.get_colorscale(colorscale), 
        normalized
    )
    
    return colors
