import streamlit as st
import json
from datetime import datetime

def render_query_history(protocol):
    """Render query history with enhanced functionality."""
    if hasattr(st.session_state, 'query_history') and st.session_state.query_history:
        if protocol == "RESO Web API":
            queries = [q for q in st.session_state.query_history if q.get('protocol') == 'RESO Web API']
            protocol_name = "RESO"
        else:
            queries = [q for q in st.session_state.query_history if q.get('protocol') == 'RETS']
            protocol_name = "RETS"
        
        if queries:
            st.subheader(f"📋 Recent {protocol_name} Queries")
            
            # Export/Import functionality in expander
            with st.expander("📁 Query Management", expanded=False):
                # Export and Clear buttons in a row
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📥 Export Queries", use_container_width=True, help=f"Download all {protocol_name} queries as JSON", key=f"export_{protocol_name}"):
                        # Export current query history
                        export_data = {
                            'exported_at': datetime.now().isoformat(),
                            'protocol': protocol_name,
                            'queries': queries
                        }
                        export_json = json.dumps(export_data, indent=2)
                        st.download_button(
                            label="Download Queries JSON",
                            data=export_json,
                            file_name=f"{protocol_name.lower()}_queries_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True
                        )
                
                with col2:
                    if st.button("🗑️ Clear All History", use_container_width=True, help=f"Remove all {protocol_name} queries from history", key=f"clear_{protocol_name}"):
                        # Remove all queries of this protocol from history
                        st.session_state.query_history = [
                            q for q in st.session_state.query_history 
                            if q.get('protocol') != protocol_name
                        ]
                        st.success(f"All {protocol_name} query history cleared!")
                        st.rerun()
                
                # Import section with better styling
                st.markdown("**📤 Import Queries:**")
                uploaded_file = st.file_uploader(
                    "Choose a JSON file to import queries",
                    type="json",
                    key=f"{protocol_name.lower()}_import_queries",
                    help="Upload a previously exported query file"
                )
                if uploaded_file is not None:
                    try:
                        imported_data = json.load(uploaded_file)
                        if 'queries' in imported_data:
                            # Merge imported queries with existing history
                            imported_count = 0
                            for query in imported_data['queries']:
                                if query not in st.session_state.query_history:
                                    st.session_state.query_history.append(query)
                                    imported_count += 1
                            if imported_count > 0:
                                st.success(f"✅ Successfully imported {imported_count} queries!")
                            else:
                                st.info("ℹ️ No new queries to import (all queries already exist)")
                            st.rerun()
                        else:
                            st.error("❌ Invalid query file format")
                    except Exception as e:
                        st.error(f"❌ Import error: {str(e)}")
            
            # Display recent queries with re-enter functionality
            for i, query in enumerate(reversed(queries[-5:])):  # Show last 5 instead of 3
                with st.expander(f"{protocol_name} Query {len(queries) - i} - {query['timestamp']}", expanded=i==0):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.text(f"⏰ Time: {query['timestamp']}")
                        st.text(f"📊 Resource: {query['resource']}")
                        if protocol == "RETS":
                            st.text(f"🏷️ Class: {query['class']}")
                            st.text(f"🔍 Query: {query['query']}")
                        else:
                            st.text(f"🔍 Filter: {query['filter']}")
                        st.text(f"📈 Results: {query['results_count']}")
                    
                    with col2:
                        if st.button(f"🔄 Re-enter", key=f"{protocol_name.lower()}_reenter_{i}", use_container_width=True):
                            # Set flag to apply the query
                            if protocol == "RESO Web API":
                                st.session_state.apply_reso_query = {
                                    'resource': query['resource'],
                                    'filter': query['filter']
                                }
                            else:
                                st.session_state.apply_rets_query = {
                                    'resource': query['resource'],
                                    'class': query['class'],
                                    'query': query['query']
                                }
                            st.success("Query loaded! Scroll up to see it in the form.")
                            st.rerun()
                        
                        if st.button(f"🗑️ Delete", key=f"{protocol_name.lower()}_delete_{i}", use_container_width=True):
                            # Remove from history
                            st.session_state.query_history.remove(query)
                            st.success("Query removed from history!")
                            st.rerun()
        else:
            st.info(f"No {protocol_name} queries executed yet.")
    else:
        st.info("No queries executed yet.")

def render_reso_query_history():
    """Render RESO Web API query history."""
    render_query_history("RESO Web API")

def render_rets_query_history():
    """Render RETS query history."""
    render_query_history("RETS") 