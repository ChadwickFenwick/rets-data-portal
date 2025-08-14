import streamlit as st
import pandas as pd
import io
from datetime import datetime

def render_data_visualization():
    """Render comprehensive data visualization for query results."""
    if not st.session_state.query_results:
        st.info("No query results available for visualization. Please execute a query first.")
        return
    
    results_df = pd.DataFrame(st.session_state.query_results)
    
    # Show results summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Records", len(results_df))
    with col2:
        st.metric("Total Columns", len(results_df.columns))
    with col3:
        st.metric("Data Size", f"{results_df.memory_usage(deep=True).sum() / 1024:.1f} KB")
    
    # Data table with toggle
    st.subheader("📊 Data Table")
    show_visuals = st.checkbox("Show Visualizations", value=True, help="Toggle to show/hide charts and graphs")
    
    # Display the results table
    st.dataframe(results_df, use_container_width=True, height=400)
    
    if show_visuals:
        render_charts_and_analytics(results_df)

def render_charts_and_analytics(df):
    """Render various charts and analytics for the data."""
    st.subheader("📈 Data Visualizations")
    
    # Get numeric and categorical columns
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Price distribution (if price-related columns exist)
    price_cols = [col for col in numeric_cols if 'price' in col.lower() or 'list' in col.lower()]
    if price_cols:
        st.write("**💰 Price Distribution**")
        price_col = st.selectbox("Select Price Column:", price_cols, key="price_chart")
        
        if price_col and df[price_col].notna().sum() > 0:
            # Create price ranges manually to avoid pandas Interval issues
            price_data = df[price_col].dropna()
            if len(price_data) > 0:
                min_price = price_data.min()
                max_price = price_data.max()
                
                # Create custom bins
                if max_price > min_price:
                    bin_edges = pd.linspace(min_price, max_price, 11)
                    bin_labels = [f"${int(bin_edges[i]):,}-${int(bin_edges[i+1]):,}" for i in range(len(bin_edges)-1)]
                    
                    # Create histogram data
                    hist_data = pd.cut(price_data, bins=bin_edges, labels=bin_labels, include_lowest=True)
                    hist_counts = hist_data.value_counts().sort_index()
                    
                    # Create chart data
                    chart_data = pd.DataFrame({
                        'Price Range': hist_counts.index.astype(str),
                        'Count': hist_counts.values
                    })
                    
                    st.bar_chart(chart_data.set_index('Price Range'))
                else:
                    st.info("Not enough price variation for histogram")
    
    # Property type distribution (if property type columns exist)
    property_cols = [col for col in categorical_cols if 'type' in col.lower() or 'property' in col.lower()]
    if property_cols:
        st.write("**🏠 Property Type Distribution**")
        property_col = st.selectbox("Select Property Type Column:", property_cols, key="property_chart")
        
        if property_col and df[property_col].notna().sum() > 0:
            property_counts = df[property_col].value_counts().head(10)  # Top 10 types
            
            if len(property_counts) > 0:
                chart_data = pd.DataFrame({
                    'Property Type': property_counts.index,
                    'Count': property_counts.values
                })
                
                st.bar_chart(chart_data.set_index('Property Type'))
    
    # Bedrooms and bathrooms (if they exist)
    bedroom_cols = [col for col in numeric_cols if 'bedroom' in col.lower() or 'bed' in col.lower()]
    bathroom_cols = [col for col in numeric_cols if 'bathroom' in col.lower() or 'bath' in col.lower()]
    
    if bedroom_cols or bathroom_cols:
        col1, col2 = st.columns(2)
        
        with col1:
            if bedroom_cols:
                st.write("**🛏️ Bedrooms Distribution**")
                bedroom_col = st.selectbox("Select Bedroom Column:", bedroom_cols, key="bedroom_chart")
                
                if bedroom_col and df[bedroom_col].notna().sum() > 0:
                    bedroom_counts = df[bedroom_col].value_counts().sort_index()
                    chart_data = pd.DataFrame({
                        'Bedrooms': bedroom_counts.index,
                        'Count': bedroom_counts.values
                    })
                    st.bar_chart(chart_data.set_index('Bedrooms'))
        
        with col2:
            if bathroom_cols:
                st.write("**🛁 Bathrooms Distribution**")
                bathroom_col = st.selectbox("Select Bathroom Column:", bathroom_cols, key="bathroom_chart")
                
                if bathroom_col and df[bathroom_col].notna().sum() > 0:
                    bathroom_counts = df[bathroom_col].value_counts().sort_index()
                    chart_data = pd.DataFrame({
                        'Bathrooms': bathroom_counts.index,
                        'Count': bathroom_counts.values
                    })
                    st.bar_chart(chart_data.set_index('Bathrooms'))
    
    # Geographic visualization (if coordinates exist)
    lat_cols = [col for col in numeric_cols if 'lat' in col.lower() or 'latitude' in col.lower()]
    lon_cols = [col for col in numeric_cols if 'lon' in col.lower() or 'longitude' in col.lower()]
    
    if lat_cols and lon_cols:
        st.write("**📍 Geographic Distribution**")
        lat_col = st.selectbox("Select Latitude Column:", lat_cols, key="lat_chart")
        lon_col = st.selectbox("Select Longitude Column:", lon_cols, key="lon_chart")
        
        if lat_col and lon_col:
            # Filter out invalid coordinates
            valid_coords = df[(df[lat_col].notna()) & (df[lon_col].notna()) & 
                            (df[lat_col] != 0) & (df[lon_col] != 0)]
            
            if len(valid_coords) > 0:
                # Create scatter plot data
                chart_data = pd.DataFrame({
                    'Latitude': valid_coords[lat_col],
                    'Longitude': valid_coords[lon_col]
                })
                
                st.scatter_chart(chart_data, x='Longitude', y='Latitude')
            else:
                st.info("No valid coordinates found for mapping")
    
    # Time series analysis (if date columns exist)
    date_cols = []
    for col in df.columns:
        try:
            pd.to_datetime(df[col].head(10))
            date_cols.append(col)
        except:
            continue
    
    if date_cols:
        st.write("**📅 Time Series Analysis**")
        date_col = st.selectbox("Select Date Column:", date_cols, key="date_chart")
        
        if date_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                date_counts = df[date_col].dt.date.value_counts().sort_index()
                
                if len(date_counts) > 0:
                    chart_data = pd.DataFrame({
                        'Date': date_counts.index,
                        'Count': date_counts.values
                    })
                    
                    st.line_chart(chart_data.set_index('Date'))
            except:
                st.info("Could not parse date column for time series analysis")

def render_export_section():
    """Render the export functionality."""
    if not st.session_state.query_results:
        st.info("No query results available for export. Please execute a query first.")
        return
    
    st.header("📁 Export Results")
    
    results_df = pd.DataFrame(st.session_state.query_results)
    
    # Export options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Export Configuration")
        
        # File name
        filename = st.text_input(
            "File Name:",
            value=f"rets_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            help="Enter the filename for the export"
        )
        
        # Export options
        include_index = st.checkbox("Include row index", value=False)
        
        # Column selection
        selected_columns = st.multiselect(
            "Select columns to export:",
            options=results_df.columns.tolist(),
            default=results_df.columns.tolist(),
            help="Choose which columns to include in the export"
        )
    
    with col2:
        st.subheader("Export Summary")
        st.info(f"**Total Records:** {len(results_df)}")
        st.info(f"**Total Columns:** {len(results_df.columns)}")
        st.info(f"**Selected Columns:** {len(selected_columns)}")
    
    # Preview
    if selected_columns:
        st.subheader("Export Preview")
        preview_df = results_df[selected_columns].head(10)
        st.dataframe(preview_df, use_container_width=True)
        
        # Generate CSV
        csv_buffer = io.StringIO()
        results_df[selected_columns].to_csv(csv_buffer, index=include_index)
        csv_data = csv_buffer.getvalue()
        
        # Download button
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.warning("Please select at least one column to export.") 