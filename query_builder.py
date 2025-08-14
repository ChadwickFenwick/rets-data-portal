import streamlit as st
import pandas as pd
from datetime import datetime
from clients.rets_client import RESOWebAPIClient
from history import render_reso_query_history, render_rets_query_history
from smart_suggestions import render_intelligent_query_generator

# Cache helper functions (import from app_new.py)
def get_cached_resources():
    """Get resources from cache or fetch if not cached."""
    if not st.session_state.cache_resources:
        if st.session_state.rets_client:
            st.session_state.cache_resources = st.session_state.rets_client.get_resources()
    return st.session_state.cache_resources

def initialize_query_session_state():
    """Initialize query-related session state variables."""
    # Initialize query form fields for re-entering queries
    if 'reso_query_resource' not in st.session_state:
        st.session_state.reso_query_resource = ""
    if 'odata_filter' not in st.session_state:
        st.session_state.odata_filter = ""
    if 'query_resource' not in st.session_state:
        st.session_state.query_resource = ""
    if 'query_class' not in st.session_state:
        st.session_state.query_class = ""
    if 'query_params' not in st.session_state:
        st.session_state.query_params = ""

    # Initialize flags for applying queries
    if 'apply_reso_query' not in st.session_state:
        st.session_state.apply_reso_query = None
    if 'apply_rets_query' not in st.session_state:
        st.session_state.apply_rets_query = None

def apply_query_values_from_flags():
    """Apply query values from flags (this runs before widgets are created)."""
    if st.session_state.apply_reso_query:
        st.session_state.reso_query_resource = st.session_state.apply_reso_query['resource']
        st.session_state.odata_filter = st.session_state.apply_reso_query['filter']

    if st.session_state.apply_rets_query:
        st.session_state.query_resource = st.session_state.apply_rets_query['resource']
        st.session_state.query_class = st.session_state.apply_rets_query['class']
        st.session_state.query_params = st.session_state.apply_rets_query['query']

def render_reso_query_editor():
    """Render the RESO Web API query editor interface."""
    resources_list = get_cached_resources()
    
    if resources_list:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🔧 Build Your RESO Query")
            
            # Resource selection
            query_resource = st.selectbox(
                "RESO Resource:",
                options=[''] + resources_list,
                help="Select the RESO resource to query",
                key="reso_query_resource"
            )
            
            # Apply query from history if flag is set
            if st.session_state.apply_reso_query:
                # This will be handled by the form fields using the session state values
                st.info(f"📋 Query loaded: {st.session_state.apply_reso_query['resource']} - {st.session_state.apply_reso_query['filter'][:50]}...")
                # Clear the flag after showing the info
                st.session_state.apply_reso_query = None
            
            # Show current selection
            if query_resource:
                st.success(f"📊 Selected RESO Resource: {query_resource}")
            else:
                st.warning("📊 Select a RESO resource to build queries")
            
            # Apply generated query if available (outside form)
            if hasattr(st.session_state, 'generated_odata_filter') and st.session_state.generated_odata_filter:
                st.info(f"💡 Generated query available: `{st.session_state.generated_odata_filter}`")
                if st.button("📋 Apply Generated Query", use_container_width=True):
                    st.session_state.odata_filter = st.session_state.generated_odata_filter
                    st.success("Generated query applied!")
                    st.rerun()
            
            # Query parameters form
            with st.form("reso_query_form", clear_on_submit=False):
                
                # OData filter input
                odata_filter = st.text_area(
                    "OData $filter:",
                    placeholder="e.g., StandardStatus eq 'Active' and ListPrice gt 100000",
                    help="Enter OData $filter expression",
                    height=120,
                    key="odata_filter"
                )
                
                # Display constructed query
                if odata_filter:
                    st.text_area("OData Filter:", value=odata_filter, height=68, disabled=True)
                
                # Optional parameters
                st.write("**Query Options:**")
                opt_col1, opt_col2, opt_col3 = st.columns(3)
                with opt_col1:
                    limit = st.number_input("$top (Limit):", min_value=1, max_value=10000, value=25)
                with opt_col2:
                    skip = st.number_input("$skip (Offset):", min_value=0, max_value=100000, value=0)
                with opt_col3:
                    select_fields = st.text_input(
                        "$select (Fields):", 
                        placeholder="Field1,Field2,Field3",
                        help="Comma-separated field names, or leave empty for all"
                    )
                
                # Validation and submit button
                query_btn = st.form_submit_button("🚀 Execute RESO Query", use_container_width=True)
                
                # Show validation status
                if not query_resource:
                    st.warning("⚠️ Please select a RESO resource")
                elif not odata_filter or odata_filter.strip() == "":
                    st.warning("⚠️ Please enter an OData $filter expression")
                else:
                    st.success(f"✅ Ready: {odata_filter}")
                
                if query_btn and query_resource and odata_filter and odata_filter.strip():
                    with st.spinner("Querying RESO Web API..."):
                        try:
                            # RESO Web API uses different method signature
                            if hasattr(st.session_state.rets_client, 'execute_query'):
                                # Check if this is a RESO client by checking the class type
                                if isinstance(st.session_state.rets_client, RESOWebAPIClient):
                                    # This is a RESO client
                                    results = st.session_state.rets_client.execute_query(
                                        resource=query_resource,
                                        odata_filter=odata_filter.strip(),
                                        limit=limit,
                                        select=select_fields,
                                        skip=skip
                                    )
                                else:
                                    # This is a RETS client - shouldn't happen in RESO section
                                    st.error("Wrong client type for RESO query")
                                    results = None
                            else:
                                st.error("RESO client does not support execute_query method")
                                results = None
                            
                            if results:
                                st.session_state.query_results = results
                                
                                # Update query history
                                if not hasattr(st.session_state, 'query_history'):
                                    st.session_state.query_history = []
                                
                                st.session_state.query_history.append({
                                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'protocol': 'RESO Web API',
                                    'resource': query_resource,
                                    'filter': odata_filter,
                                    'results_count': len(results)
                                })
                                
                                st.success(f"✅ Query successful! Found {len(results)} results.")
                            else:
                                st.warning("No results found for this RESO query.")
                                
                        except Exception as e:
                            st.error(f"RESO query execution error: {str(e)}")
                            st.text(f"Debug details: {e}")
        
        with col2:
            # OData query help and examples
            st.subheader("📚 OData Query Help")
            
            with st.expander("OData $filter Examples"):
                st.markdown("""
                **Basic Examples:**
                - `StandardStatus eq 'Active'` - Active listings
                - `ListPrice gt 100000` - Price above $100,000
                - `ListPrice ge 50000 and ListPrice le 250000` - Price range
                - `PropertyType eq 'Residential'` - Property type filter
                - `ModificationTimestamp gt 2024-01-01T00:00:00Z` - Recent updates
                
                **Operators:**
                - `eq` - equals
                - `ne` - not equals
                - `gt` - greater than
                - `ge` - greater than or equal
                - `lt` - less than
                - `le` - less than or equal
                - `and` - logical AND
                - `or` - logical OR
                """)
            # Move recent queries section here
            render_reso_query_history()
    else:
        st.info("No RESO resources found.")

def render_rets_query_editor():
    """Render the RETS query editor interface."""
    resources_data = []
    classes_data = []
    
    # Parse comprehensive metadata structure
    for metadata_type, metadata_content in st.session_state.metadata.items():
        if metadata_type == 'RESOURCE' and metadata_content:
            if isinstance(metadata_content, dict) and 'resources' in metadata_content:
                resources_data = metadata_content['resources']
        elif metadata_type.startswith('CLASS_') and metadata_content:
            resource_name = metadata_type.replace('CLASS_', '')
            if isinstance(metadata_content, dict) and 'classes' in metadata_content:
                for class_info in metadata_content['classes']:
                    class_info['resource'] = resource_name
                    classes_data.append(class_info)
    
    if resources_data:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🔧 Build Your RETS Query")
            
            # Resource selection
            resource_options = [r.get('ResourceID', r.get('StandardName', 'Unknown')) for r in resources_data]
            query_resource = st.selectbox(
                "Resource:",
                options=[''] + resource_options,
                help="Select the resource to query",
                key="query_resource"
            )
            
            # Class selection
            query_class = ''
            if query_resource:
                resource_classes = [c for c in classes_data if c.get('resource') == query_resource]
                if resource_classes:
                    class_options = [c.get('ClassName', c.get('StandardName', 'Unknown')) for c in resource_classes]
                    query_class = st.selectbox(
                        "Class:",
                        options=[''] + class_options,
                        help="Select the class within the chosen resource",
                        key="query_class"
                    )
            
            # Apply query from history if flag is set
            if st.session_state.apply_rets_query:
                # This will be handled by the form fields using the session state values
                st.info(f"📋 Query loaded: {st.session_state.apply_rets_query['resource']}:{st.session_state.apply_rets_query['class']} - {st.session_state.apply_rets_query['query'][:50]}...")
                # Clear the flag after showing the info
                st.session_state.apply_rets_query = None
            
            # Show current selection
            if query_resource and query_class:
                st.success(f"📊 Selected: {query_resource}:{query_class}")
            elif query_resource:
                st.warning("📊 Select a class to build queries")
            else:
                st.warning("📊 Select a resource to build queries")
            
            # Apply generated query if available (outside form)
            if hasattr(st.session_state, 'generated_dmql_query') and st.session_state.generated_dmql_query:
                st.info(f"💡 Generated query available: `{st.session_state.generated_dmql_query}`")
                if st.button("📋 Apply Generated Query", use_container_width=True):
                    st.session_state.query_params = st.session_state.generated_dmql_query
                    st.success("Generated query applied!")
                    st.rerun()
            
            # Query parameters form
            with st.form("rets_query_form", clear_on_submit=False):
                
                # DMQL query input
                query_params = st.text_area(
                    "DMQL Query:",
                    placeholder="e.g., (Status=Active),(ListPrice=100000+)",
                    help="Enter DMQL query parameters",
                    height=120,
                    key="query_params"
                )
                
                # Display constructed query
                if query_params:
                    st.text_area("Full Query:", value=f"{query_resource}:{query_class}:*", height=68, disabled=True)
                
                # Optional parameters
                st.write("**Query Options:**")
                opt_col1, opt_col2 = st.columns(2)
                with opt_col1:
                    limit = st.number_input("Limit:", min_value=1, max_value=10000, value=25)
                with opt_col2:
                    select_fields = st.text_input(
                        "Select Fields:", 
                        placeholder="Field1,Field2,Field3",
                        help="Comma-separated field names, or leave empty for all"
                    )
                
                # Validation and submit button
                query_btn = st.form_submit_button("🚀 Execute RETS Query", use_container_width=True)
                
                # Show validation status
                if not query_resource:
                    st.warning("⚠️ Please select a resource")
                elif not query_class:
                    st.warning("⚠️ Please select a class")
                elif not query_params or query_params.strip() == "":
                    st.warning("⚠️ Please enter DMQL query parameters")
                else:
                    st.success(f"✅ Ready: {query_params}")
                
                if query_btn and query_resource and query_class and query_params and query_params.strip():
                    with st.spinner("Querying RETS server..."):
                        try:
                            results = st.session_state.rets_client.execute_query(
                                query_resource, 
                                query_class, 
                                query_params.strip(),
                                limit,
                                select_fields
                            )
                            
                            if results:
                                st.session_state.query_results = results
                                
                                # Update query history
                                if not hasattr(st.session_state, 'query_history'):
                                    st.session_state.query_history = []
                                
                                st.session_state.query_history.append({
                                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'protocol': 'RETS',
                                    'resource': query_resource,
                                    'class': query_class,
                                    'query': query_params,
                                    'results_count': len(results)
                                })
                                
                                st.success(f"✅ Query successful! Found {len(results)} results.")
                            else:
                                st.warning("No results found for this RETS query.")
                        
                        except Exception as e:
                            st.error(f"RETS query execution error: {str(e)}")
        
        with col2:
            # DMQL query help and examples
            st.subheader("📚 DMQL Query Help")
            
            with st.expander("DMQL Examples"):
                st.markdown("""
                **Basic Examples:**
                - `(Status=Active)` - Active listings
                - `(ListPrice=100000+)` - Price above $100,000
                - `(ListPrice=100000-500000)` - Price range
                - `(City=Austin)` - City search
                - `(Status=Active),(ListPrice=200000+)` - Multiple conditions
                
                **Operators:**
                - `=` - equals
                - `+` - greater than
                - `-` - range (e.g., 100000-500000)
                - `*` - wildcard
                - `,` - AND operator
                """)
            # Move recent queries section here
            render_rets_query_history()
    else:
        st.info("No RETS resources found in metadata.")

def render_query_results():
    """Render query results if available."""
    if st.session_state.query_results:
        st.markdown("---")
        st.subheader("📊 Query Results")
        
        results_df = pd.DataFrame(st.session_state.query_results)
        
        # Show results summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(results_df))
        with col2:
            st.metric("Total Columns", len(results_df.columns))
        with col3:
            st.metric("Data Size", f"{results_df.memory_usage(deep=True).sum() / 1024:.1f} KB")
        
        # Display the results table
        st.dataframe(results_df, use_container_width=True, height=400)
        
        # Quick export button
        if st.button("📥 Quick Export to CSV", use_container_width=True):
            csv_data = results_df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

def render_query_builder():
    """Main function to render the query builder interface."""
    st.header("🔍 Query Builder")
    
    if st.session_state.connected and st.session_state.metadata:
        protocol = st.session_state.get('protocol', 'RETS')
        
        # Initialize query session state
        initialize_query_session_state()
        
        # Apply query values from flags
        apply_query_values_from_flags()
        
        # Intelligent query generator
        with st.expander("🤖 Intelligent Query Generator", expanded=True):
            render_intelligent_query_generator(st.session_state.metadata, protocol)
        
        st.markdown("---")
        
        # Render appropriate query editor based on protocol
        if protocol == "RESO Web API":
            render_reso_query_editor()
        else:
            render_rets_query_editor()
        
        # Display query results if available
        render_query_results()
    else:
        st.info("Please connect to a server and load metadata to use the query builder.") 