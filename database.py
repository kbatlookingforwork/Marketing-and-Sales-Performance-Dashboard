import os
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, text

def get_db_connection():
    """
    Create a database connection using environment variables.
    
    Returns:
    - A SQLAlchemy database connection
    """
    try:
        # Get database connection details from environment variables
        db_host = os.getenv("PGHOST")
        db_port = os.getenv("PGPORT", "5432")
        db_name = os.getenv("PGDATABASE")
        db_user = os.getenv("PGUSER")
        db_password = os.getenv("PGPASSWORD")
        
        # Alternative way using DATABASE_URL if available
        database_url = os.getenv("DATABASE_URL")
        
        if database_url:
            # Use the full database URL if provided
            engine = create_engine(database_url)
        elif all([db_host, db_port, db_name, db_user, db_password]):
            # Construct connection string from individual parameters
            connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            engine = create_engine(connection_string)
        else:
            raise ValueError("Database connection parameters not found in environment variables")
        
        # Test the connection
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        
        return engine
    
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        raise

def execute_query(engine, query):
    """
    Execute a SQL query and return results as a DataFrame
    
    Parameters:
    - engine: SQLAlchemy database engine
    - query: SQL query string
    
    Returns:
    - DataFrame containing query results
    """
    try:
        return pd.read_sql_query(query, engine)
    except Exception as e:
        st.error(f"Error executing query: {str(e)}")
        raise

def get_campaign_data(engine, start_date, end_date):
    """
    Get campaign performance data from the database
    
    Parameters:
    - engine: SQLAlchemy database engine
    - start_date: Filter start date
    - end_date: Filter end date
    
    Returns:
    - DataFrame with campaign data
    """
    query = f"""
    SELECT 
        c.campaign_id, 
        c.campaign_name, 
        c.date, 
        c.platform, 
        c.region, 
        c.impressions, 
        c.clicks, 
        c.installs, 
        c.spend, 
        c.revenue
    FROM 
        marketing_campaigns c
    WHERE 
        c.date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY 
        c.date
    """
    
    return execute_query(engine, query)

def get_sales_data(engine, start_date, end_date):
    """
    Get sales performance data from the database
    
    Parameters:
    - engine: SQLAlchemy database engine
    - start_date: Filter start date
    - end_date: Filter end date
    
    Returns:
    - DataFrame with sales data
    """
    query = f"""
    SELECT 
        s.campaign_id, 
        s.date, 
        s.platform, 
        s.region, 
        s.purchases, 
        s.revenue, 
        s.users, 
        s.retention, 
        s.lifetime_value
    FROM 
        sales_performance s
    WHERE 
        s.date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY 
        s.date
    """
    
    return execute_query(engine, query)

def get_combined_data(engine, start_date, end_date):
    """
    Get combined marketing and sales data
    
    Parameters:
    - engine: SQLAlchemy database engine
    - start_date: Filter start date
    - end_date: Filter end date
    
    Returns:
    - DataFrame with combined data
    """
    query = f"""
    SELECT 
        c.campaign_id, 
        c.campaign_name, 
        c.date, 
        c.platform, 
        c.region, 
        c.impressions, 
        c.clicks, 
        c.installs, 
        c.spend as campaign_spend,
        c.revenue as campaign_revenue,
        s.purchases, 
        s.revenue as sales_revenue, 
        s.users, 
        s.retention, 
        s.lifetime_value,
        c.clicks::float / NULLIF(c.impressions, 0) * 100 as ctr,
        c.installs::float / NULLIF(c.clicks, 0) * 100 as conversion_rate,
        c.spend::float / NULLIF(c.installs, 0) as cpa,
        s.revenue::float / NULLIF(s.users, 0) as arpu,
        (c.revenue - c.spend)::float / NULLIF(c.spend, 0) * 100 as roi
    FROM 
        marketing_campaigns c
    JOIN 
        sales_performance s ON c.campaign_id = s.campaign_id 
                            AND c.date = s.date 
                            AND c.platform = s.platform 
                            AND c.region = s.region
    WHERE 
        c.date BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY 
        c.date
    """
    
    return execute_query(engine, query)
