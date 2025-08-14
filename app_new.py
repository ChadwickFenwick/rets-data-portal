import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

# Import our modular components
from connection import (
    initialize_connection_session_state,
    render_connection_sidebar,
    render_connection_status,
    clear_connection_state
)
from query_builder import render_query_builder
from history import render_reso_query_history, render_rets_query_history
from visualization import render_data_visualization, render_export_section
from smart_suggestions import render_intelligent_query_generator
from utils import format_metadata, create_download_link, get_cached_data, render_cache_controls
from clients.rets_client import RESOWebAPIClient

# TTL Cache helper functions
def get_cached_metadata():
    """Get metadata from TTL cache or fetch if not cached."""
    if not st.session_state.rets_client:
        return None
    
    def fetch_metadata():
        with st.spinner("🔄 Fetching metadata..."):
            return st.session_state.rets_client.get_metadata()
    
    return get_cached_data('metadata', 'main', fetch_metadata)

def get_cached_resources():
    """Get resources from TTL cache or fetch if not cached."""
    if not st.session_state.rets_client:
        return None
    
    def fetch_resources():
        with st.spinner("🔄 Fetching resources..."):
            return st.session_state.rets_client.get_resources()
    
    return get_cached_data('resources', 'main', fetch_resources)

def get_cached_resource_details(resource_name):
    """Get resource details from TTL cache or fetch if not cached."""
    if not st.session_state.rets_client:
        return {}
    
    def fetch_resource_details():
        try:
            with st.spinner(f"🔄 Fetching details for {resource_name}..."):
                return st.session_state.rets_client.get_resource_details(resource_name)
        except Exception as e:
            return {'error': str(e)}
    
    return get_cached_data('resource_details', resource_name, fetch_resource_details)

def get_cached_lookup_fields(resource_name, class_name=""):
    """Get lookup fields from TTL cache or fetch if not cached."""
    if not st.session_state.rets_client:
        return []
    
    def fetch_lookup_fields():
        try:
            if hasattr(st.session_state.rets_client, 'get_all_lookup_fields'):
                return st.session_state.rets_client.get_all_lookup_fields(resource_name, class_name)
            else:
                return []
        except Exception as e:
            return []
    
    cache_key = f"{resource_name}_{class_name}"
    return get_cached_data('lookup_fields', cache_key, fetch_lookup_fields)

def get_cached_lookup_values(resource_name, field_name, class_name=""):
    """Get lookup values from TTL cache or fetch if not cached."""
    if not st.session_state.rets_client:
        return {}
    
    def fetch_lookup_values():
        try:
            with st.spinner(f"🔄 Fetching lookup values for {field_name}..."):
                # Both RESO and RETS clients only accept resource and field_name
                return st.session_state.rets_client.get_lookup_values(resource_name, field_name)
        except Exception as e:
            return {'error': str(e)}
    
    cache_key = f"{resource_name}_{field_name}_{class_name}"
    return get_cached_data('lookup_values', cache_key, fetch_lookup_values)

def render_metadata_tab():
    """Render the metadata explorer tab."""
    st.header("Metadata Explorer")
    
    # Use cached metadata
    metadata = get_cached_metadata()
    if metadata:
        # Download metadata button
        col1, col2 = st.columns([3, 1])
        with col2:
            protocol = st.session_state.get('protocol', 'RETS')
            if protocol == "RESO Web API":
                # For RESO, download the raw OData metadata XML
                if (hasattr(st.session_state, 'rets_client') 
                    and st.session_state.rets_client 
                    and isinstance(st.session_state.rets_client, RESOWebAPIClient)
                    and hasattr(st.session_state.rets_client, 'metadata') 
                    and st.session_state.rets_client.metadata):
                    metadata_content = st.session_state.rets_client.metadata.get('metadata_content', '')
                    if metadata_content:
                        st.download_button(
                            label="📥 Download Metadata",
                            data=metadata_content,
                            file_name=f"reso_metadata_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xml",
                            mime="application/xml",
                            use_container_width=True
                        )
            else:
                # For RETS, download all metadata as JSON
                metadata_json = json.dumps(st.session_state.metadata, indent=2, default=str)
                st.download_button(
                    label="📥 Download Metadata",
                    data=metadata_json,
                    file_name=f"rets_metadata_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )
        
        with col1:
            # Search functionality
            search_term = st.text_input("🔍 Search metadata:", placeholder="Enter search term...")
        
        # Display metadata (pass protocol for proper formatting)
        if search_term:
            filtered_metadata = format_metadata(metadata, search_term, protocol)
            if filtered_metadata is not None and not filtered_metadata.empty:
                st.dataframe(filtered_metadata, use_container_width=True, height=400)
            else:
                st.info("No metadata found matching your search.")
        else:
            formatted_metadata = format_metadata(metadata, "", protocol)
            if formatted_metadata is not None and not formatted_metadata.empty:
                st.dataframe(formatted_metadata, use_container_width=True, height=400)
            else:
                st.info("No metadata available.")
    else:
        st.info("No metadata loaded. Please connect to a RETs server first.")

def render_resources_tab():
    """Render the resources browser tab."""
    st.header("📋 Resources Browser")
    
    if st.session_state.connected:
        # Use cached metadata
        metadata = get_cached_metadata()
        if metadata:
            protocol = st.session_state.get('protocol', 'RETS')
            
            if protocol == "RESO Web API":
                # Handle RESO resources (cached)
                resources_list = get_cached_resources()
                
                if resources_list:
                    st.write(f"**Available RESO Resources:** {len(resources_list)}")
                    
                    # Create comprehensive resources table
                    resources_table_data = []
                    
                    # Show loading progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    for i, resource_name in enumerate(resources_list):
                        status_text.text(f"Loading resource details: {resource_name}")
                        progress_bar.progress((i + 1) / len(resources_list))
                        
                        # Get detailed information for each resource (cached)
                        resource_details = get_cached_resource_details(resource_name)
                        
                        resources_table_data.append({
                            'Resource Name': resource_name,
                            'Entity Type': resource_details.get('entity_type', 'Unknown'),
                            'Properties Count': resource_details.get('property_count', 0),
                            'Description': resource_details.get('description', ''),
                            'Namespace': resource_details.get('namespace', ''),
                            'Key Properties': ', '.join(resource_details.get('key_properties', [])),
                            'Navigation Properties': len(resource_details.get('navigation_properties', [])),
                            'Has Enum Types': 'Yes' if resource_details.get('enum_types') else 'No'
                        })
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display the comprehensive resources table
                    if resources_table_data:
                        st.subheader("📊 RESO Resources Overview")
                        resources_df = pd.DataFrame(resources_table_data)
                        
                        # Add search functionality
                        search_term = st.text_input("🔍 Search resources:", placeholder="Enter resource name or type...")
                        
                        if search_term:
                            # Filter the dataframe based on search term
                            filtered_df = resources_df[
                                resources_df.apply(lambda row: row.astype(str).str.contains(search_term, case=False, na=False).any(), axis=1)
                            ]
                            st.info(f"Showing {len(filtered_df)} of {len(resources_df)} resources matching '{search_term}'")
                        else:
                            filtered_df = resources_df
                        
                        # Display the table
                        st.dataframe(
                            filtered_df,
                            use_container_width=True,
                            height=min(600, len(filtered_df) * 40 + 100)
                        )
                        
                        # Add export functionality
                        if st.button("📥 Export Resources Table as CSV"):
                            csv = filtered_df.to_csv(index=False)
                            st.download_button(
                                label="Download CSV",
                                data=csv,
                                file_name=f"reso_resources_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                    
                    # Detailed view for selected resource
                    st.subheader("🔍 Resource Details")
                    selected_resource = st.selectbox(
                        "Select a RESO resource for detailed view:",
                        options=[''] + resources_list,
                        key='resource_selector'
                    )
                    
                    if selected_resource:
                        # Get RESO resource details (cached)
                        resource_details = get_cached_resource_details(selected_resource)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader(f"📄 RESO Resource: {selected_resource}")
                            st.write(f"**Entity Type:** {resource_details.get('entity_type', 'Unknown')}")
                            st.write(f"**Properties Count:** {resource_details.get('property_count', 0)}")
                            st.write(f"**Description:** {resource_details.get('description', 'N/A')}")
                            st.write(f"**Namespace:** {resource_details.get('namespace', 'N/A')}")
                            
                            # Show key properties
                            key_props = resource_details.get('key_properties', [])
                            if key_props:
                                st.write(f"**Key Properties:** {', '.join(key_props)}")
                        
                        with col2:
                            st.subheader("🔧 All Properties")
                            properties = resource_details.get('properties', [])
                            if properties:
                                # Show all properties in a table
                                prop_data = []
                                for prop in properties:
                                    prop_data.append({
                                        'Name': prop.get('name', ''),
                                        'Type': prop.get('type', ''),
                                        'Nullable': prop.get('nullable', ''),
                                        'Max Length': prop.get('max_length', '')
                                    })
                                
                                if prop_data:
                                    st.dataframe(pd.DataFrame(prop_data), use_container_width=True, height=400)
                                    
                                    # Add export for properties
                                    if st.button(f"📥 Export {selected_resource} Properties"):
                                        csv = pd.DataFrame(prop_data).to_csv(index=False)
                                        st.download_button(
                                            label="Download Properties CSV",
                                            data=csv,
                                            file_name=f"reso_{selected_resource}_properties_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                            mime="text/csv"
                                        )
                            else:
                                st.info("No properties found for this resource.")
                        
                        # Full width properties table below columns
                        if selected_resource and properties:
                            st.markdown("---")
                            st.subheader(f"📊 Full Properties Table for {selected_resource}")
                            st.dataframe(pd.DataFrame(prop_data), use_container_width=True, height=400)
                else:
                    st.info("No RESO resources found.")
            
            elif protocol == "RETS":
                # Handle RETS resources (existing logic)
                resources_data = []
                classes_data = []
                
                # Parse comprehensive metadata structure
                for metadata_type, metadata_content in metadata.items():
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
                    st.write(f"**Available RETS Resources:** {len(resources_data)}")
                    
                    # Resource selector
                    resource_options = [r.get('ResourceID', r.get('StandardName', 'Unknown')) for r in resources_data]
                    selected_resource = st.selectbox(
                        "Select a RETS resource to explore:",
                        options=[''] + resource_options,
                        key='resource_selector'
                    )
                    
                    if selected_resource:
                        # Find selected resource details
                        resource_details = next((r for r in resources_data if r.get('ResourceID') == selected_resource or r.get('StandardName') == selected_resource), None)
                        
                        if resource_details:
                            # Display resource information
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.subheader(f"📄 Resource: {selected_resource}")
                                resource_info = {}
                                for key, value in resource_details.items():
                                    if key not in ['ResourceID', 'StandardName']:
                                        resource_info[key] = value
                                
                                if resource_info:
                                    st.json(resource_info)
                                else:
                                    st.info("No additional resource details available.")
                            
                            with col2:
                                # Find classes for this resource
                                resource_classes = [c for c in classes_data if c.get('resource') == selected_resource]
                                
                                if resource_classes:
                                    st.subheader(f"📊 Classes in {selected_resource}")
                                    
                                    class_options = [c.get('ClassName', c.get('StandardName', 'Unknown')) for c in resource_classes]
                                    selected_class = st.selectbox(
                                        "Select a class:",
                                        options=[''] + class_options,
                                        key='class_selector'
                                    )
                                    
                                    if selected_class:
                                        class_details = next((c for c in resource_classes if c.get('ClassName') == selected_class or c.get('StandardName') == selected_class), None)
                                        if class_details:
                                            class_info = {}
                                            for key, value in class_details.items():
                                                if key not in ['ClassName', 'StandardName', 'resource']:
                                                    class_info[key] = value
                                            
                                            if class_info:
                                                st.json(class_info)
                                else:
                                    st.info("No classes found for this resource.")
                            
                            # Display table metadata (fields/columns) - full width outside columns
                            if selected_class:
                                st.markdown("---")
                                st.subheader(f"📋 Table Fields for {selected_resource}:{selected_class}")
                                table_key = f"TABLE_{selected_resource}_{selected_class}"
                                if table_key in metadata:
                                    table_metadata = metadata[table_key]
                                    if isinstance(table_metadata, dict) and 'fields' in table_metadata:
                                        fields_data = table_metadata['fields']
                                        
                                        if fields_data:
                                            # Convert fields to DataFrame for better display
                                            fields_df = pd.DataFrame([
                                                {
                                                    'Field Name': field.get('SystemName', field.get('StandardName', '')),
                                                    'Standard Name': field.get('StandardName', ''),
                                                    'Long Name': field.get('LongName', ''),
                                                    'Data Type': field.get('DataType', ''),
                                                    'Max Length': field.get('MaximumLength', ''),
                                                    'Required': field.get('Required', ''),
                                                    'Lookup Name': field.get('LookupName', ''),
                                                    'Interpretation': field.get('Interpretation', '')
                                                }
                                                for field in fields_data
                                            ])
                                            
                                            # Add search functionality
                                            field_search = st.text_input("🔍 Search fields:", placeholder="Enter field name...")
                                            
                                            if field_search:
                                                mask = fields_df.apply(lambda x: x.astype(str).str.contains(field_search, case=False, na=False).any(axis=1))
                                                filtered_fields_df = fields_df[mask]
                                                st.info(f"Showing {len(filtered_fields_df)} of {len(fields_df)} fields matching '{field_search}'")
                                            else:
                                                filtered_fields_df = fields_df
                                            
                                            # Display the fields table (full width)
                                            st.dataframe(
                                                filtered_fields_df,
                                                use_container_width=True,
                                                height=400
                                            )
                                            
                                            # Add export functionality
                                            if st.button("📥 Export Fields CSV", use_container_width=True):
                                                csv = filtered_fields_df.to_csv(index=False)
                                                st.download_button(
                                                    label="Download Fields CSV",
                                                    data=csv,
                                                    file_name=f"rets_{selected_resource}_{selected_class}_fields_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                                    mime="text/csv",
                                                    use_container_width=True
                                                )
                                        
                                        else:
                                            st.info("No fields found for this table.")
                                    else:
                                        st.info("Table metadata not available for this resource/class combination.")
                                else:
                                    st.info("Table metadata not found. Try refreshing the connection.")
                else:
                    st.info("No RETS resources found in metadata.")
        else:
            st.info("No metadata available. Please connect to a server first.")
    else:
        st.info("Connect to a RETs server to browse available resources.")

def render_field_values_tab():
    """Render the field values and lookups tab."""
    st.header("🔎 Field Values & Lookups")
    
    if st.session_state.connected:
        # Use cached metadata
        metadata = get_cached_metadata()
        if metadata:
            protocol = st.session_state.get('protocol', 'RETS')
            
            # Initialize variables for both protocols
            resources_data = []
            classes_by_resource = {}
            
            if protocol == "RESO Web API":
                # Handle RESO field values (cached)
                resources_list = get_cached_resources()
                
                if resources_list:
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.subheader("🎯 Select RESO Resource & Field")
                        
                        # Resource selection
                        lookup_resource = st.selectbox(
                            "RESO Resource:",
                            options=[''] + resources_list,
                            help="Select the RESO resource to explore field values",
                            key='reso_lookup_resource'
                        )
                        
                        # Field selection
                        if lookup_resource:
                            # Get lookup fields for this resource (cached)
                            lookup_fields = get_cached_lookup_fields(lookup_resource)
                            
                            if lookup_fields:
                                st.info(f"Found {len(lookup_fields)} fields with lookup values")
                                selected_field = st.selectbox(
                                    "Lookup Field:",
                                    options=[''] + lookup_fields,
                                    help="Select a field with lookup values",
                                    key='reso_lookup_field'
                                )
                                
                                if selected_field:
                                    # Get lookup values button
                                    if st.button("🔍 Get RESO Lookup Values", use_container_width=True):
                                        with st.spinner("Fetching RESO lookup values..."):
                                            lookup_data = get_cached_lookup_values(lookup_resource, selected_field)
                                            if lookup_data:
                                                st.session_state.current_lookups = lookup_data
                                                st.success(f"Found {lookup_data.get('count', 0)} lookup values!")
                                            else:
                                                st.warning("No lookup values found for this RESO field.")
                            else:
                                st.info("No lookup fields found for this RESO resource.")
                                
                                # Show all properties for debugging
                                resource_details = get_cached_resource_details(lookup_resource)
                                properties = resource_details.get('properties', [])
                                if properties:
                                    st.write(f"**Debug:** All properties in {lookup_resource}:")
                                    for prop in properties[:10]:  # Show first 10
                                        st.write(f"- {prop.get('name', 'Unknown')} ({prop.get('type', 'Unknown type')})")
                                    if len(properties) > 10:
                                        st.write(f"... and {len(properties) - 10} more properties")
                
                # Display RESO lookup values if available
                if hasattr(st.session_state, 'current_lookups') and st.session_state.current_lookups:
                    st.markdown("---")
                    
                    # Show field info
                    field_name = st.session_state.current_lookups.get('field_name', 'Unknown Field')
                    st.subheader(f"📋 RESO Lookup Values for {field_name}")
                    
                    # Show any errors
                    if 'error' in st.session_state.current_lookups:
                        st.error(f"Error retrieving lookup values: {st.session_state.current_lookups['error']}")
                    
                    lookup_values = st.session_state.current_lookups.get('values', {})
                    
                    if lookup_values:
                        # Show count and field type
                        lookup_type = st.session_state.current_lookups.get('lookup_type', 'Unknown')
                        st.info(f"Found {len(lookup_values)} unique values | Field Type: {lookup_type}")
                        
                        # Convert to DataFrame for better display
                        lookup_df = pd.DataFrame([
                            {'Value': key, 'Description': value}
                            for key, value in lookup_values.items()
                        ])
                        
                        # Search lookup values
                        lookup_search = st.text_input("🔍 Search RESO values:", placeholder="Enter search term...")
                        
                        if lookup_search:
                            mask = lookup_df.apply(lambda x: x.astype(str).str.contains(lookup_search, case=False, na=False).any(axis=1))
                            filtered_lookup_df = lookup_df[mask]
                            st.info(f"Showing {len(filtered_lookup_df)} of {len(lookup_df)} values matching '{lookup_search}'")
                        else:
                            filtered_lookup_df = lookup_df
                        
                        st.dataframe(filtered_lookup_df, use_container_width=True, height=400)
                        
                        # Download lookup values
                        csv_data = filtered_lookup_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download RESO Values CSV",
                            data=csv_data,
                            file_name=f"reso_{field_name}_values_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    else:
                        st.info("No values available for this RESO field.")
            
            elif protocol == "RETS":
                # Handle RETS field values (existing logic)
                for metadata_type, metadata_content in metadata.items():
                    if metadata_type == 'RESOURCE' and metadata_content:
                        if isinstance(metadata_content, dict) and 'resources' in metadata_content:
                            resources_data = metadata_content['resources']
                    elif metadata_type.startswith('CLASS_') and metadata_content:
                        resource_name = metadata_type.replace('CLASS_', '')
                        if isinstance(metadata_content, dict) and 'classes' in metadata_content:
                            classes_by_resource[resource_name] = [
                                c.get('ClassName', c.get('StandardName', 'Unknown')) 
                                for c in metadata_content['classes']
                            ]
                
                if resources_data:
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.subheader("🎯 Select Resource & Class")
                        
                        # Resource selection
                        resource_options = [r.get('ResourceID', r.get('StandardName', 'Unknown')) for r in resources_data]
                        lookup_resource = st.selectbox(
                            "Resource:",
                            options=[''] + resource_options,
                            help="Select the resource to explore field values",
                            key='lookup_resource'
                        )
                        
                        # Class selection
                        lookup_class = ''
                        if lookup_resource and lookup_resource in classes_by_resource:
                            lookup_class = st.selectbox(
                                "Class:",
                                options=[''] + classes_by_resource[lookup_resource],
                                help="Select the class within the chosen resource",
                                key='lookup_class'
                            )
                        
                        # Get fields for this resource/class
                        if lookup_resource and lookup_class:
                            table_key = f"TABLE_{lookup_resource}_{lookup_class}"
                            if table_key in metadata:
                                table_metadata = metadata[table_key]
                                if isinstance(table_metadata, dict) and 'fields' in table_metadata:
                                    fields_data = table_metadata['fields']
                                    
                                    # Show field selector - only fields with lookup values
                                    lookup_fields = []
                                    for field in fields_data:
                                        if isinstance(field, dict):
                                            # Only include fields that have a LookupName (indicating lookup values exist)
                                            lookup_name = field.get('LookupName')
                                            if lookup_name and lookup_name.strip():
                                                field_name = field.get('SystemName', field.get('StandardName', field.get('LongName', 'Unknown')))
                                                lookup_fields.append(field_name)
                                    
                                    if lookup_fields:
                                        st.info(f"Found {len(lookup_fields)} fields with lookup values out of {len(fields_data)} total fields")
                                        field_names = lookup_fields
                                    else:
                                        st.warning("No fields with lookup values found in this resource/class")
                                        field_names = []
                                    
                                    selected_field = st.selectbox(
                                        "Field:",
                                        options=[''] + field_names,
                                        help="Select a field to view its lookup values",
                                        key='lookup_field'
                                    )
                                    
                                    if selected_field:
                                        # Get lookup values button
                                        if st.button("🔍 Get Lookup Values", use_container_width=True):
                                            with st.spinner("Fetching lookup values..."):
                                                lookup_data = get_cached_lookup_values(lookup_resource, selected_field, lookup_class)
                                                if lookup_data:
                                                    st.session_state.current_lookups = lookup_data
                                                else:
                                                    st.warning("No lookup values found or this field doesn't have lookups.")
                    
                    with col2:
                        st.subheader("💡 Field Information")
                        
                        if lookup_resource and lookup_class and 'lookup_field' in st.session_state and st.session_state.lookup_field:
                            selected_field = st.session_state.lookup_field
                            
                            # Find field details
                            table_key = f"TABLE_{lookup_resource}_{lookup_class}"
                            if table_key in metadata:
                                table_metadata = metadata[table_key]
                                if isinstance(table_metadata, dict) and 'fields' in table_metadata:
                                    field_info = next(
                                        (f for f in table_metadata['fields'] 
                                         if f.get('SystemName') == selected_field or f.get('StandardName') == selected_field),
                                        None
                                    )
                                    
                                    if field_info:
                                        st.json({
                                            'Field Name': field_info.get('SystemName', ''),
                                            'Standard Name': field_info.get('StandardName', ''),
                                            'Long Name': field_info.get('LongName', ''),
                                            'Data Type': field_info.get('DataType', ''),
                                            'Max Length': field_info.get('MaximumLength', ''),
                                            'Required': field_info.get('Required', ''),
                                            'Lookup Name': field_info.get('LookupName', ''),
                                            'Interpretation': field_info.get('Interpretation', '')
                                        })
                    
                    # Display lookup values (full width, outside columns)
                    if hasattr(st.session_state, 'current_lookups') and st.session_state.current_lookups:
                        st.markdown("---")
                        
                        # Show field info
                        field_name = st.session_state.current_lookups.get('field_name', 'Unknown Field')
                        st.subheader(f"📋 Lookup Values for {field_name}")
                        
                        # Show any errors
                        if 'error' in st.session_state.current_lookups:
                            st.error(f"Error retrieving lookup values: {st.session_state.current_lookups['error']}")
                        
                        lookup_values = st.session_state.current_lookups.get('values', {})
                        
                        if lookup_values:
                            # Show count
                            st.info(f"Found {len(lookup_values)} unique values")
                            
                            # Convert to DataFrame for better display
                            lookup_df = pd.DataFrame([
                                {'Value': key, 'Description': value}
                                for key, value in lookup_values.items()
                            ])
                            
                            # Search lookup values
                            lookup_search = st.text_input("🔍 Search values:", placeholder="Enter search term...")
                            
                            if lookup_search:
                                mask = lookup_df.apply(lambda x: x.astype(str).str.contains(lookup_search, case=False, na=False).any(axis=1))
                                filtered_lookup_df = lookup_df[mask]
                                st.info(f"Showing {len(filtered_lookup_df)} of {len(lookup_df)} values matching '{lookup_search}'")
                            else:
                                filtered_lookup_df = lookup_df
                            
                            st.dataframe(filtered_lookup_df, use_container_width=True, height=400)
                            
                            # Download lookup values
                            csv_data = filtered_lookup_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Values CSV",
                                data=csv_data,
                                file_name=f"{lookup_resource}_{lookup_class}_{field_name}_values.csv",
                                mime="text/csv"
                            )
                        else:
                            st.info("No values available for this field.")
        else:
            st.info("No metadata available. Please connect to a server first.")
    else:
        st.info("Connect to a RETs server to explore field values and lookups.")

def render_welcome_section():
    """Render the welcome section for non-connected users."""
    st.info("👈 Please connect to a RETs server using the sidebar to get started.")
    
    # Help section
    st.markdown("---")
    st.subheader("Getting Started")
    st.markdown("""
    This RETs Dashboard allows you to:
    
    1. **Connect** to RETs servers using your credentials
    2. **Browse** metadata and resources
    3. **Execute** custom queries using DMQL
    4. **Export** results to CSV format
    
    To begin, enter your RETs server URL, username, and password in the sidebar.
    """)
    
    # Troubleshooting section
    st.markdown("---")
    st.subheader("Connection Troubleshooting")
    
    with st.expander("Common Connection Issues"):
        st.markdown("""
        **Connection Failed?** Try these steps:
        
        1. **Check URL Format**: Ensure your URL includes `http://` or `https://`
           - Example: `https://your-rets-server.com/rets/`
        
        2. **Verify Credentials**: Double-check username and password
           - Some servers are case-sensitive
           - Try removing extra spaces
        
        3. **Configure User Agent**: Most RETs servers require specific User Agent strings
           - Check Advanced Settings and try different User Agent values
           - Common format: `YourAppName/1.0`
           - Some servers also need User Agent passwords
        
        4. **RETs Version**: Try different RETs protocol versions
           - Most common: 1.7.2, 1.8
           - Some older servers use 1.5 or 1.0
        
        5. **Test Different Endpoints**: The app tries multiple login paths automatically:
           - `/login`, `/Login`, `/RETS/Login`, `/rets/login`
        
        6. **Network Issues**: Check if:
           - Your IP address is whitelisted
           - The server is currently online
           - There are no firewall restrictions
        
        7. **Use Test Connection**: Click "Test Connection" to verify credentials without saving
        
        8. **Contact Provider**: If issues persist, contact your RETs data provider for:
           - Correct server URL and User Agent requirements
           - Account status verification
           - IP whitelist confirmation
        """)
    
    # Sample connection examples
    with st.expander("Sample Connection Examples"):
        st.markdown("""
        **Common RETs Server URLs:**
        
        - `https://matrix.brightmls.com/Matrix/Login.aspx`
        - `https://rets.rapattoni.com/LoginService/Login`
        - `https://rets.mlspin.com/rets/login`
        - `https://your-mls-name.rets.com/login`
        
        **Common User Agents:**
        
        - `YourAppName/1.0` (replace with your actual app name)
        - `Matrix/1.0`
        - `RETS-Connector/1.0`
        - `MyRETS/1.0`
        
        **Note:** Each MLS provider has different requirements. Always use the exact URL and User Agent provided by your data provider.
        """)
    
    # Query examples
    with st.expander("Query Examples"):
        st.markdown("""
        **Sample DMQL Queries:**
        
        - **Active Listings**: `(Status=Active)`
        - **Price Range**: `(ListPrice=100000-500000)`
        - **City Search**: `(City=Austin)`
        - **Multiple Conditions**: `(Status=Active),(ListPrice=200000+)`
        - **Date Range**: `(ModificationTimestamp=2024-01-01T00:00:00+)`
        
        **Common Resources:**
        - Property, Agent, Office, Media, Tour
        
        **Common Classes:**
        - ResidentialProperty, CommercialProperty, Land, Rental
        """)
    
    # Matrix-specific help
    with st.expander("Matrix Server Troubleshooting"):
        st.markdown("""
        **For Matrix-based RETs servers (like Canopy MLS):**
        
        1. **User Agent Requirements**: Matrix servers typically require specific User Agent strings
           - Try: `Matrix/1.0`
           - Try: `YourCompanyName/1.0`
           - Contact your MLS provider for the exact User Agent string
        
        2. **User Agent Password**: Many Matrix servers require a User Agent password
           - This is different from your login password
           - Contact your MLS provider for this credential
        
        3. **URL Format**: Matrix login URLs often end in `.ashx`
           - Example: `https://matrix.yourmls.com/Matrix/Login.ashx`
           - Don't add additional paths to .ashx URLs
        
        4. **Authentication Method**: Some Matrix servers use digest authentication
           - The app will try different authentication methods automatically
        
        5. **IP Whitelisting**: Matrix servers often require IP whitelisting
           - Contact your MLS to whitelist your IP address
           - Replit servers may have dynamic IPs
        """)
    
    # RESO Troubleshooting Guide
    with st.expander("🔧 RESO Web API Troubleshooting", expanded=False):
        st.markdown("""
        ### Common RESO Connection Issues:
        
        1. **Access Token Expired (401 Error)**
           - RESO tokens typically expire in 1 hour or less
           - Generate a new access token from your MLS provider
           - Check if your token has proper permissions
        
        2. **Wrong Base URL Format**
           - RESO URLs usually end with `/odata` or similar OData endpoint
           - Example: `https://api.yourmls.com/reso/odata`
           - Avoid trailing slashes in the base URL
        
        3. **Authentication Method Issues**
           - **Direct Access Token**: Use if you have a pre-generated token
           - **OAuth2 Flow**: Use if you have client credentials and user login
           - Check with your MLS which method they support
        
        4. **Permission Issues (403 Error)**
           - Your token may not have access to requested resources
           - Contact your MLS to verify API permissions
           - Some MLS providers require additional approvals for API access
        
        5. **API Endpoint Not Found (404 Error)**
           - Verify the base URL is correct for your MLS
           - Some providers use different paths for their RESO API
           - Check your MLS documentation for the correct endpoint
        
        6. **Token Format Issues**
           - Ensure the access token is properly formatted
           - Remove any extra spaces or characters
           - Some tokens are JWT format, others are opaque strings
        """)
    
    # Save connection info
    st.markdown("---")
    st.info("💡 **Tip:** Use the 'Save Connection' feature to store your credentials securely for future use. Your passwords are saved locally in your browser session only.")

def setup_railway_config():
    """Setup Railway-specific configuration for deployment."""
    # Set up port from environment variable (Railway provides this)
    port = int(os.environ.get('PORT', 8080))
    
    # Configure Streamlit server settings for Railway
    if 'RAILWAY_ENVIRONMENT' in os.environ or 'RAILWAY_PROJECT_ID' in os.environ:
        # We're running on Railway
        os.environ.setdefault('STREAMLIT_SERVER_PORT', str(port))
        os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
        os.environ.setdefault('STREAMLIT_SERVER_HEADLESS', 'true')
        os.environ.setdefault('STREAMLIT_SERVER_ENABLE_CORS', 'false')
        os.environ.setdefault('STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION', 'false')
        os.environ.setdefault('STREAMLIT_BROWSER_GATHER_USAGE_STATS', 'false')

def create_health_check_page():
    """Create a simple health check page for Railway monitoring."""
    # Check if health parameter is in URL
    try:
        query_params = st.query_params
        if 'health' in query_params:
            st.json({
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "service": "RETS Dashboard",
                "version": "1.0.0"
            })
            st.stop()
    except:
        # Fallback for older Streamlit versions or if query_params fails
        pass

def main():
    """Main application function."""
    # Setup Railway configuration
    setup_railway_config()
    
    # Check for health check request
    create_health_check_page()
    
    # Page configuration
    st.set_page_config(
        page_title="RETs Dashboard",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    initialize_connection_session_state()
    
    # Dynamic title based on connection status
    if st.session_state.connected and st.session_state.rets_client:
        protocol = st.session_state.get('protocol', 'RETS')
        connection_name = st.session_state.get('current_connection_name', '')
        
        if connection_name:
            if protocol == "RESO Web API":
                st.title(f"🏠 RESO Dashboard - {connection_name}")
            else:
                st.title(f"🏠 RETS Dashboard - {connection_name}")
        else:
            if protocol == "RESO Web API":
                st.title("🏠 RESO Dashboard")
            else:
                st.title("🏠 RETS Dashboard")
    else:
        st.title("🏠 RETS Dashboard")
    
    # Connection status and disconnect button next to header
    render_connection_status()
    
    st.markdown("---")
    
    # Render connection sidebar
    render_connection_sidebar()
    
    # Main content area
    if st.session_state.connected:
        # Render cache controls in sidebar
        render_cache_controls()
        
        # Tabs for different functionalities
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Metadata", "🔍 Resources", "⚡ Query Builder", "🔎 Field Values", "📁 Export"])
        
        with tab1:
            render_metadata_tab()
        
        with tab2:
            render_resources_tab()
        
        with tab3:
            render_query_builder()
        
        with tab4:
            render_field_values_tab()
        
        with tab5:
            render_export_section()
    else:
        # Welcome message for non-connected users
        render_welcome_section()

if __name__ == "__main__":
    main() 