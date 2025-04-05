import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import streamlit as st
from database import execute_query
from appsflyer_integration import get_appsflyer_data

def load_and_process_data(source_type, **kwargs):
    """
    Load data from the specified source and preprocess it
    
    Parameters:
    - source_type: 'database', 'excel', 'appsflyer', or 'sample'
    - kwargs: Additional parameters based on source_type
    
    Returns:
    - success: Boolean indicating if data loading was successful
    - campaign_data: DataFrame with campaign data
    - sales_data: DataFrame with sales data
    - combined_data: DataFrame with combined campaign and sales data
    """
    try:
        if source_type == 'database':
            connection = kwargs.get('connection')
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            # Load campaign data
            campaign_query = f"""
            SELECT 
                campaign_id, 
                campaign_name, 
                date, 
                platform, 
                region, 
                impressions, 
                clicks, 
                installs, 
                spend, 
                revenue
            FROM 
                marketing_campaigns 
            WHERE 
                date BETWEEN '{start_date}' AND '{end_date}'
            """
            campaign_data = execute_query(connection, campaign_query)
            
            # Load sales data
            sales_query = f"""
            SELECT 
                campaign_id, 
                date, 
                platform, 
                region, 
                purchases, 
                revenue, 
                users, 
                retention, 
                lifetime_value
            FROM 
                sales_performance 
            WHERE 
                date BETWEEN '{start_date}' AND '{end_date}'
            """
            sales_data = execute_query(connection, sales_query)
        
        elif source_type == 'excel':
            campaign_file = kwargs.get('campaign_file')
            sales_file = kwargs.get('sales_file')
            
            # Determine file type and read accordingly
            if campaign_file.name.endswith('.csv'):
                campaign_data = pd.read_csv(campaign_file)
            else:
                campaign_data = pd.read_excel(campaign_file)
                
            if sales_file.name.endswith('.csv'):
                sales_data = pd.read_csv(sales_file)
            else:
                sales_data = pd.read_excel(sales_file)
            
            # Filter by date if provided
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            if 'date' in campaign_data.columns:
                campaign_data['date'] = pd.to_datetime(campaign_data['date'])
                campaign_data = campaign_data[(campaign_data['date'] >= start_date) & 
                                             (campaign_data['date'] <= end_date)]
            
            if 'date' in sales_data.columns:
                sales_data['date'] = pd.to_datetime(sales_data['date'])
                sales_data = sales_data[(sales_data['date'] >= start_date) & 
                                       (sales_data['date'] <= end_date)]
        
        elif source_type == 'appsflyer':
            api_key = kwargs.get('api_key')
            app_id = kwargs.get('app_id')
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            # Call the function to get data from Appsflyer API
            campaign_data, sales_data = get_appsflyer_data(api_key, app_id, start_date, end_date)
        
        elif source_type == 'sample':
            # Generate sample data for demonstration
            start_date = kwargs.get('start_date')
            end_date = kwargs.get('end_date')
            
            campaign_data, sales_data = generate_sample_data(start_date, end_date)
        
        else:
            raise ValueError(f"Unknown source type: {source_type}")
        
        # Process and combine the data
        campaign_data, sales_data, combined_data = process_data(campaign_data, sales_data)
        
        return True, campaign_data, sales_data, combined_data
    
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return False, None, None, None

def process_data(campaign_data, sales_data):
    """
    Process and combine campaign and sales data
    
    Parameters:
    - campaign_data: DataFrame with campaign data
    - sales_data: DataFrame with sales data
    
    Returns:
    - processed_campaign_data: Processed campaign data
    - processed_sales_data: Processed sales data
    - combined_data: Combined data from both sources
    """
    # Ensure date columns are datetime
    if 'date' in campaign_data.columns:
        campaign_data['date'] = pd.to_datetime(campaign_data['date'])
    
    if 'date' in sales_data.columns:
        sales_data['date'] = pd.to_datetime(sales_data['date'])
    
    # Calculate additional metrics for campaign data
    if all(col in campaign_data.columns for col in ['clicks', 'impressions']):
        campaign_data['ctr'] = (campaign_data['clicks'] / campaign_data['impressions'] * 100).round(2)
    
    if all(col in campaign_data.columns for col in ['installs', 'clicks']):
        campaign_data['conversion_rate'] = (campaign_data['installs'] / campaign_data['clicks'] * 100).round(2)
    
    if all(col in campaign_data.columns for col in ['spend', 'installs']):
        campaign_data['cpa'] = (campaign_data['spend'] / campaign_data['installs']).round(2)
    
    if all(col in campaign_data.columns for col in ['revenue', 'spend']):
        campaign_data['roi'] = ((campaign_data['revenue'] - campaign_data['spend']) / campaign_data['spend'] * 100).round(2)
    
    # Calculate additional metrics for sales data
    if all(col in sales_data.columns for col in ['revenue', 'users']):
        sales_data['arpu'] = (sales_data['revenue'] / sales_data['users']).round(2)
    
    if 'lifetime_value' in sales_data.columns:
        sales_data['cltv'] = sales_data['lifetime_value'].round(2)
    
    # Combine the data
    if 'campaign_id' in campaign_data.columns and 'campaign_id' in sales_data.columns:
        # Merge on campaign_id, date, platform, and region if available
        merge_columns = ['campaign_id']
        if all(col in campaign_data.columns and col in sales_data.columns for col in ['date', 'platform', 'region']):
            merge_columns.extend(['date', 'platform', 'region'])
        
        combined_data = pd.merge(
            campaign_data, 
            sales_data,
            on=merge_columns,
            how='outer',
            suffixes=('_campaign', '_sales')
        )
    else:
        # If no common campaign_id, create a combined dataset with empty values
        combined_data = pd.concat([campaign_data, sales_data], axis=1)
    
    # Rename columns to avoid confusion with suffixes
    for col in combined_data.columns:
        if col.endswith('_campaign') or col.endswith('_sales'):
            # Get the base column name without suffix
            base_name = col.rsplit('_', 1)[0]
            
            # If the base column doesn't exist in the combined data, rename it
            if base_name not in combined_data.columns:
                combined_data.rename(columns={col: base_name}, inplace=True)
    
    # Calculate additional combined metrics
    if all(col in combined_data.columns for col in ['spend', 'purchases']):
        combined_data['cost_per_purchase'] = (combined_data['spend'] / combined_data['purchases']).round(2)
    
    # Add bounce rate if not present (for demonstration)
    if 'bounce_rate' not in combined_data.columns:
        combined_data['bounce_rate'] = np.random.uniform(20, 60, size=len(combined_data)).round(2)
    
    # Ensure values are valid numbers
    for df in [campaign_data, sales_data, combined_data]:
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return campaign_data, sales_data, combined_data

def generate_sample_data(start_date, end_date):
    """
    Generate sample data for demonstration purposes.
    This is used only when no real data sources are available.
    
    Parameters:
    - start_date: Start date for the sample data
    - end_date: End date for the sample data
    
    Returns:
    - campaign_data: Sample campaign performance data
    - sales_data: Sample sales performance data
    """
    # Convert to datetime if they're not already
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Create date range
    date_range = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Campaign names
    campaign_names = [
        'Summer Sale 2023', 
        'Back to School', 
        'Holiday Special', 
        'New Year Promotion',
        'Spring Collection'
    ]
    
    # Platform types
    platforms = ['iOS', 'Android', 'Web']
    
    # Regions
    regions = [
        'North America', 'Europe', 'Asia Pacific', 
        'South America', 'Middle East', 'Africa'
    ]
    
    # Generate campaign data
    campaign_rows = []
    
    # Create a unique seed to ensure consistent results
    np.random.seed(42)
    
    for campaign_id, campaign_name in enumerate(campaign_names, 1):
        for date in date_range:
            for platform in platforms:
                for region in regions:
                    # Create base values with some randomness
                    impressions = int(np.random.normal(10000, 2000))
                    ctr = np.random.uniform(1.5, 4.5)
                    clicks = int(impressions * ctr / 100)
                    conversion_rate = np.random.uniform(3, 15)
                    installs = int(clicks * conversion_rate / 100)
                    spend = np.random.uniform(500, 2000)
                    revenue = spend * np.random.uniform(0.8, 2.5)
                    
                    # Adjust values based on platform and region for more realistic variation
                    if platform == 'iOS':
                        spend *= 1.2
                        revenue *= 1.3
                    elif platform == 'Android':
                        installs *= 1.3
                    
                    if region == 'North America':
                        spend *= 1.4
                        revenue *= 1.5
                    elif region == 'Europe':
                        spend *= 1.2
                        revenue *= 1.3
                    
                    campaign_rows.append({
                        'campaign_id': campaign_id,
                        'campaign_name': campaign_name,
                        'date': date,
                        'platform': platform,
                        'region': region,
                        'impressions': impressions,
                        'clicks': clicks,
                        'installs': installs,
                        'spend': round(spend, 2),
                        'revenue': round(revenue, 2),
                        'ctr': round(ctr, 2),
                        'conversion_rate': round(conversion_rate, 2),
                        'cpa': round(spend / max(installs, 1), 2),
                        'roi': round((revenue - spend) / spend * 100, 2)
                    })
    
    # Create campaign dataframe
    campaign_data = pd.DataFrame(campaign_rows)
    
    # Generate sales data
    sales_rows = []
    
    for campaign_id, campaign_name in enumerate(campaign_names, 1):
        for date in date_range:
            for platform in platforms:
                for region in regions:
                    # Get corresponding campaign row to ensure consistency
                    campaign_row = campaign_data[
                        (campaign_data['campaign_id'] == campaign_id) &
                        (campaign_data['date'] == date) &
                        (campaign_data['platform'] == platform) &
                        (campaign_data['region'] == region)
                    ]
                    
                    if len(campaign_row) == 1:
                        installs = campaign_row['installs'].values[0]
                        
                        # Calculate sales metrics based on campaign metrics
                        purchase_rate = np.random.uniform(0.1, 0.4)
                        purchases = int(installs * purchase_rate)
                        revenue = purchases * np.random.uniform(30, 80)
                        users = installs
                        retention = np.random.uniform(40, 80)
                        lifetime_value = revenue / max(purchases, 1) * np.random.uniform(2, 5)
                        
                        sales_rows.append({
                            'campaign_id': campaign_id,
                            'date': date,
                            'platform': platform,
                            'region': region,
                            'purchases': purchases,
                            'revenue': round(revenue, 2),
                            'users': users,
                            'retention': round(retention, 2),
                            'lifetime_value': round(lifetime_value, 2)
                        })
    
    # Create sales dataframe
    sales_data = pd.DataFrame(sales_rows)
    
    return campaign_data, sales_data
