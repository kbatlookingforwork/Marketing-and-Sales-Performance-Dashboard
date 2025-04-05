import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_db_connection, get_campaign_data, get_sales_data, get_combined_data
from data_processing import load_and_process_data
from visualization import create_map_visualization, create_platform_chart, create_kpi_metric
import os
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(page_title="Marketing & Sales Performance Dashboard",
                   page_icon="📊",
                   layout="wide",
                   initial_sidebar_state="expanded")

# Title and introduction
st.title("📊 Marketing & Sales Performance Dashboard")
st.markdown("""
    <div style="display: flex; align-items: center; gap: 10px; margin-top: 20px;">
        <p style="font-weight: bold; color: green;">Created by:</p>
        <a href="https://www.linkedin.com/in/danyyudha" target="_blank">
            <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" 
                 style="width: 20px; height: 20px;">
        </a>
        <p><b>Dany Yudha Putra Haque</b></p>
    </div>
""",
            unsafe_allow_html=True)
st.write(
    "A data-driven dashboard for marketing campaigns and sales funnel analysis with geo & platform intelligence"
)

# Initialize session state for data
if "data_loaded" not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.campaign_data = None
    st.session_state.sales_data = None
    st.session_state.combined_data = None

# Sidebar - Data Source Selection
st.sidebar.title("Data Sources")

data_source = st.sidebar.selectbox(
    "Select Data Source",
    ["Sample Data", "Database", "Excel Upload", "Appsflyer API"],
    help="Choose the source of data for analysis")

# Date range filter
st.sidebar.title("Date Range")
start_date = st.sidebar.date_input("Start Date",
                                   pd.to_datetime("2023-01-01").date())
end_date = st.sidebar.date_input("End Date",
                                 pd.to_datetime("2023-06-30").date())

# Load data based on selected source
if data_source == "Database":
    try:
        if st.sidebar.button("Load Database Data"):
            db_connection = get_db_connection()

            # Get data from database
            campaign_data = get_campaign_data(db_connection, start_date,
                                              end_date)
            sales_data = get_sales_data(db_connection, start_date, end_date)
            combined_data = get_combined_data(db_connection, start_date,
                                              end_date)

            # Store in session state
            st.session_state.campaign_data = campaign_data
            st.session_state.sales_data = sales_data
            st.session_state.combined_data = combined_data
            st.session_state.data_loaded = True

            st.sidebar.success("Database data loaded successfully!")
    except Exception as e:
        st.error(f"Error connecting to database: {e}")
        st.session_state.data_loaded = False

elif data_source == "Excel Upload":
    campaign_file = st.sidebar.file_uploader(
        "Upload Campaign Data (Excel/CSV)", type=["xlsx", "csv"])
    sales_file = st.sidebar.file_uploader("Upload Sales Data (Excel/CSV)",
                                          type=["xlsx", "csv"])

    if campaign_file and sales_file and st.sidebar.button("Load Excel Data"):
        success, campaign_data, sales_data, combined_data = load_and_process_data(
            "excel",
            campaign_file=campaign_file,
            sales_file=sales_file,
            start_date=start_date,
            end_date=end_date)

        if success:
            st.session_state.campaign_data = campaign_data
            st.session_state.sales_data = sales_data
            st.session_state.combined_data = combined_data
            st.session_state.data_loaded = True
            st.sidebar.success("Excel data loaded successfully!")
        else:
            st.error(
                "Failed to load Excel data. Please check the file format.")

elif data_source == "Appsflyer API":
    api_key = os.getenv("APPSFLYER_API_KEY", "")
    if not api_key:
        st.sidebar.warning(
            "Appsflyer API key not found in environment variables.")
        api_key = st.sidebar.text_input("Enter Appsflyer API Key",
                                        type="password")

    app_id = st.sidebar.text_input("App ID")

    if api_key and app_id and st.sidebar.button("Load Appsflyer Data"):
        success, campaign_data, sales_data, combined_data = load_and_process_data(
            "appsflyer",
            api_key=api_key,
            app_id=app_id,
            start_date=start_date,
            end_date=end_date)

        if success:
            st.session_state.campaign_data = campaign_data
            st.session_state.sales_data = sales_data
            st.session_state.combined_data = combined_data
            st.session_state.data_loaded = True
            st.sidebar.success("Appsflyer data loaded successfully!")
        else:
            st.error(
                "Failed to load Appsflyer data. Please check your API key and App ID."
            )

else:  # Sample Data
    if st.sidebar.button("Load Sample Data"):
        success, campaign_data, sales_data, combined_data = load_and_process_data(
            "sample", start_date=start_date, end_date=end_date)

        if success:
            st.session_state.campaign_data = campaign_data
            st.session_state.sales_data = sales_data
            st.session_state.combined_data = combined_data
            st.session_state.data_loaded = True
            st.sidebar.success("Sample data loaded successfully!")
        else:
            st.error("Failed to load sample data.")

# Navigation to other pages
st.sidebar.title("Navigation")
st.sidebar.info("""
- 📈 [Campaign Performance](/campaign_performance)
- 🛒 [Sales Funnel](/sales_funnel)
- 🌍 [Geo & Platform Insights](/geo_platform_insights)
- 📊 [Metrics Dashboard](/metrics_dashboard)
""")

# Main dashboard content
if st.session_state.data_loaded and st.session_state.combined_data is not None:
    # Top-level metrics
    st.subheader("Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        conversion_rate = st.session_state.combined_data[
            "conversion_rate"].mean()
        st.metric("Conversion Rate",
                  f"{conversion_rate:.2f}%",
                  help="Average conversion rate across all campaigns")

    with col2:
        cpa = st.session_state.combined_data["cpa"].mean()
        st.metric("Cost Per Acquisition",
                  f"${cpa:.2f}",
                  help="Average cost to acquire a customer")

    with col3:
        # Use "spend" instead of "campaign_spend" for sample data compatibility
        roi = ((st.session_state.combined_data["revenue"].sum() -
                st.session_state.combined_data["spend"].sum()) /
               st.session_state.combined_data["spend"].sum() * 100)
        st.metric("ROI",
                  f"{roi:.2f}%",
                  help="Return on investment for marketing campaigns")

    with col4:
        total_revenue = st.session_state.combined_data["revenue"].sum()
        st.metric("Total Revenue",
                  f"${total_revenue:,.2f}",
                  help="Total revenue from all campaigns")

    # Quick Insights - Campaign Performance
    st.subheader("Campaign Performance Overview")

    # Create two columns
    col1, col2 = st.columns(2)

    with col1:
        # Campaign metrics chart
        campaign_metrics = st.session_state.combined_data.groupby(
            "campaign_name").agg({
                "conversion_rate": "mean",
                "cpa": "mean",
                "roi": "mean"
            }).reset_index()

        # Create horizontal bar chart for conversion rates by campaign
        fig = px.bar(campaign_metrics.sort_values("conversion_rate",
                                                  ascending=False),
                     y="campaign_name",
                     x="conversion_rate",
                     title="Conversion Rate by Campaign",
                     labels={
                         "campaign_name": "Campaign",
                         "conversion_rate": "Conversion Rate (%)"
                     },
                     color="conversion_rate",
                     color_continuous_scale=px.colors.sequential.Blues,
                     text=campaign_metrics["conversion_rate"].apply(
                         lambda x: f"{x:.2f}%"))

        fig.update_layout(xaxis_title="Conversion Rate (%)",
                          yaxis_title="Campaign",
                          height=300)

        # Make text labels visible
        fig.update_traces(textposition="outside")

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Platform distribution chart
        platform_data = st.session_state.combined_data.groupby("platform").agg(
            {
                "spend": "sum",
                "revenue": "sum",
                "conversion_rate": "mean"
            }).reset_index()

        # Calculate ROI
        platform_data["roi"] = (
            (platform_data["revenue"] - platform_data["spend"]) /
            platform_data["spend"] * 100).round(2)

        # Create bubble chart for platform performance
        fig = px.scatter(platform_data,
                         x="spend",
                         y="revenue",
                         size="conversion_rate",
                         color="platform",
                         hover_name="platform",
                         text="platform",
                         title="Platform Performance",
                         labels={
                             "spend": "Marketing Spend ($)",
                             "revenue": "Revenue ($)",
                             "conversion_rate": "Conversion Rate (%)"
                         },
                         height=300)

        fig.update_traces(
            textposition="top center",
            marker=dict(sizemode="diameter", sizeref=0.1),
        )

        fig.update_layout(xaxis_title="Marketing Spend ($)",
                          yaxis_title="Revenue ($)")

        st.plotly_chart(fig, use_container_width=True)

    # Geographic insights
    st.subheader("Geographic Performance")

    geo_data = st.session_state.combined_data.groupby("region").agg({
        "conversion_rate":
        "mean",
        "cpa":
        "mean",
        "roi":
        "mean",
        "spend":
        "sum",
        "revenue":
        "sum"
    }).reset_index()

    # Create geo performance table
    st.dataframe(geo_data.style.format({
        "conversion_rate": "{:.2f}%",
        "cpa": "${:.2f}",
        "roi": "{:.2f}%",
        "spend": "${:,.2f}",
        "revenue": "${:,.2f}"
    }),
                 use_container_width=True)

    # Call to action for detailed reports
    st.info(
        "👆 Use the navigation links in the sidebar to explore detailed reports and insights."
    )

else:
    # Show welcome screen when no data is loaded
    st.info(
        "👈 Please select a data source and load data using the sidebar options."
    )

    # Placeholder images
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Campaign Performance Analysis")
        st.markdown("""
        Analyze your marketing campaign performance with detailed metrics:
        - Conversion rates by campaign
        - Cost per acquisition (CPA) analysis
        - Click-through rates (CTR)
        - Return on investment (ROI)
        """)

    with col2:
        st.subheader("Geo & Platform Intelligence")
        st.markdown("""
        Gain insights based on geography and platform:
        - Performance breakdown by region
        - Platform-specific metrics (iOS, Android, Web)
        - Cross-platform comparison
        - Budget allocation recommendations
        """)

# Footer with version info
st.sidebar.markdown("---")
st.sidebar.caption("Marketing & Sales Dashboard v1.0")
st.sidebar.caption(f"Last Updated: {datetime.now().strftime('%Y-%m-%d')}")
