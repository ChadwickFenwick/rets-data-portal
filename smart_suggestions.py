import streamlit as st
import re
from datetime import datetime, timedelta
# import google.generativeai as genai  # Commented out - AI features disabled
import json

# Configure Gemini API (commented out - AI features disabled)
# def configure_gemini(api_key):
#     """Configure the Gemini API with the provided key."""
#     try:
#         genai.configure(api_key=api_key)
#         return True
#     except Exception as e:
#         st.error(f"Failed to configure Gemini API: {str(e)}")
#         return False

def render_intelligent_query_generator(metadata, protocol="RETS"):
    """
    Render an intelligent query generator that uses Gemini AI to analyze metadata and generate queries
    based on what's actually available in the feed.
    """
    # AI Query Generation (Hidden for now)
    # Uncomment the section below to re-enable AI-powered query generation
    """
    st.subheader("🤖 AI-Powered Query Generator")
    
    # API Key input
    api_key = st.text_input(
        "Google Gemini API Key:",
        type="password",
        help="Enter your Google Gemini API key to enable AI-powered query generation",
        placeholder="Enter your API key here..."
    )
    
    if not api_key:
        st.info("🔑 Please enter your Google Gemini API key to use the AI-powered query generator.")
        return
    
    # Configure Gemini
    if not configure_gemini(api_key):
        return
    
    # Natural language input
    user_request = st.text_area(
        "Describe what you're looking for:",
        placeholder="e.g., 'Show me active listings under $500k with 3+ bedrooms in Austin'",
        help="Describe your search in natural language. The AI will analyze your metadata to find matching fields and values."
    )
    
    # Generate button (always visible)
    generate_button = st.button("🤖 Generate AI Query", use_container_width=True, disabled=not user_request.strip())
    
    if user_request and generate_button:
        with st.spinner("🤖 AI is analyzing your metadata and generating query..."):
            generated_query = _generate_ai_query(user_request, metadata, protocol, api_key)
            
            if generated_query:
                st.success("✅ AI-generated query based on your metadata analysis:")
                
                # Display the generated query
                st.code(generated_query['query'], language="sql")
                st.write(f"**AI Explanation:** {generated_query['explanation']}")
                
                # Show field mapping
                if generated_query.get('field_mapping'):
                    st.write("**Field Mapping:**")
                    for original, mapped in generated_query['field_mapping'].items():
                        st.write(f"- '{original}' → {mapped}")
                
                # Instructions for manual copying
                st.info("💡 **To use this query:**\n1. Select the query text above\n2. Copy it (Ctrl+C)\n3. Paste it into the query builder form")
                
                # Show AI analysis
                with st.expander("🤖 AI Analysis Details", expanded=False):
                    _show_ai_analysis(generated_query.get('ai_analysis', {}))
            else:
                st.warning("Could not generate a query. The AI may need more specific information or the metadata structure may be different than expected.")
                
                # Show debugging information
                with st.expander("🔍 Debug Information", expanded=True):
                    _show_debug_info(user_request, metadata, protocol)
    """
    
    # AI features completely hidden - no UI elements shown

# def _generate_ai_query(request, metadata, protocol, api_key):
#     """
#     Generate a query using Google Gemini AI by analyzing the actual metadata.
#     """
#     try:
#         # Prepare metadata summary for AI
#         metadata_summary = _prepare_metadata_summary(metadata, protocol)
#         
#         # Create the prompt for Gemini
#         prompt = _create_ai_prompt(request, metadata_summary, protocol)
#         
#         # Generate response using Gemini
#         try:
#             # Try different model names that might be available
#             model_names = ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro']
#             model = None
#             
#             for model_name in model_names:
#                 try:
#                     model = genai.GenerativeModel(model_name)
#                     # Test if the model works by making a simple call
#                     test_response = model.generate_content("Hello")
#                     break
#                 except Exception as model_error:
#                     continue
#             
#             if model is None:
#                 st.error("No available Gemini models found. Please check your API key and try again.")
#                 return None
#             
#             response = model.generate_content(prompt)
#         except Exception as model_error:
#             st.error(f"Failed to initialize Gemini model: {str(model_error)}")
#             return None
#         
#         # Parse the AI response
#         initial_result = _parse_ai_response(response.text, request, protocol)
#         
#         if initial_result and initial_result.get('query'):
#             # Now fetch lookup values only for the fields used in the query
#             enhanced_result = _enhance_query_with_lookup_values(initial_result, metadata, protocol)
#             return enhanced_result
#         
#         return initial_result
#         
#     except Exception as e:
#         st.error(f"AI query generation failed: {str(e)}")
#         return None

def _prepare_metadata_summary(metadata, protocol):
    """
    Prepare a comprehensive summary of the metadata for the AI to analyze.
    """
    summary = {
        'protocol': protocol,
        'resources': [],
        'common_fields': {},
        'field_examples': [],
        'all_fields': [],
        'field_statistics': {},
        'lookup_values': {}
    }
    
    if protocol == "RESO Web API":
        # Comprehensive RESO metadata analysis
        for resource_name, resource_data in metadata.items():
            if isinstance(resource_data, dict):
                properties = resource_data.get('properties', [])
                if properties:
                    resource_summary = {
                        'name': resource_name,
                        'field_count': len(properties),
                        'all_fields': [prop.get('name', '') for prop in properties if prop.get('name')],
                        'sample_fields': [prop.get('name', '') for prop in properties[:10]]
                    }
                    summary['resources'].append(resource_summary)
                    
                    # Collect ALL field examples (not just first 20)
                    for prop in properties:
                        field_name = prop.get('name', '')
                        field_type = prop.get('type', '')
                        if field_name:
                            field_info = {
                                'name': field_name,
                                'type': field_type,
                                'resource': resource_name
                            }
                            summary['field_examples'].append(field_info)
                            summary['all_fields'].append(field_name)
    else:
        # Comprehensive RETS metadata analysis
        for metadata_type, metadata_content in metadata.items():
            if metadata_type.startswith('TABLE_') and metadata_content:
                if isinstance(metadata_content, dict) and 'fields' in metadata_content:
                    table_name = metadata_type.replace('TABLE_', '')
                    fields = metadata_content['fields']
                    
                    table_summary = {
                        'name': table_name,
                        'field_count': len(fields),
                        'all_fields': [field.get('SystemName', field.get('StandardName', '')) for field in fields if field.get('SystemName') or field.get('StandardName')],
                        'sample_fields': [field.get('SystemName', field.get('StandardName', '')) for field in fields[:10]]
                    }
                    summary['resources'].append(table_summary)
                    
                    # Collect ALL field examples (not just first 20)
                    for field in fields:
                        field_name = field.get('SystemName', field.get('StandardName', ''))
                        data_type = field.get('DataType', '')
                        if field_name:
                            field_info = {
                                'name': field_name,
                                'type': data_type,
                                'table': table_name
                            }
                            summary['field_examples'].append(field_info)
                            summary['all_fields'].append(field_name)
    
    # Generate comprehensive field statistics
    summary['field_statistics'] = _generate_field_statistics(summary['all_fields'])
    
    # Identify common field patterns from ALL fields
    summary['common_fields'] = _identify_common_field_patterns(summary['field_examples'])
    
    # Don't fetch lookup values here - we'll do it on-demand when we know which fields are needed
    summary['lookup_values'] = {}
    
    return summary

def _identify_common_field_patterns(field_examples):
    """
    Identify common field patterns in the metadata.
    """
    patterns = {
        'price_fields': [],
        'status_fields': [],
        'bedroom_fields': [],
        'bathroom_fields': [],
        'location_fields': [],
        'date_fields': [],
        'property_type_fields': []
    }
    
    for field in field_examples:
        field_lower = field['name'].lower()
        
        # Price fields
        if any(term in field_lower for term in ['price', 'list', 'sale', 'value', 'cost']):
            patterns['price_fields'].append(field['name'])
        
        # Status fields
        if any(term in field_lower for term in ['status', 'state', 'condition', 'listing']):
            patterns['status_fields'].append(field['name'])
        
        # Bedroom fields
        if any(term in field_lower for term in ['bedroom', 'bed', 'br']):
            patterns['bedroom_fields'].append(field['name'])
        
        # Bathroom fields
        if any(term in field_lower for term in ['bathroom', 'bath', 'ba']):
            patterns['bathroom_fields'].append(field['name'])
        
        # Location fields
        if any(term in field_lower for term in ['city', 'state', 'zip', 'county', 'address', 'location']):
            patterns['location_fields'].append(field['name'])
        
        # Date fields
        if any(term in field_lower for term in ['date', 'modified', 'created', 'updated', 'timestamp']):
            patterns['date_fields'].append(field['name'])
        
        # Property type fields
        if any(term in field_lower for term in ['property', 'type', 'category', 'class']):
            patterns['property_type_fields'].append(field['name'])
    
    return patterns

def _generate_field_statistics(all_fields):
    """
    Generate comprehensive statistics about all available fields.
    """
    stats = {
        'total_fields': len(all_fields),
        'field_patterns': {},
        'common_prefixes': {},
        'common_suffixes': {},
        'field_categories': {}
    }
    
    # Analyze field patterns
    for field in all_fields:
        field_lower = field.lower()
        
        # Common prefixes
        for prefix in ['list', 'sale', 'rent', 'prop', 'property', 'res', 'residential', 'com', 'commercial']:
            if field_lower.startswith(prefix):
                if prefix not in stats['common_prefixes']:
                    stats['common_prefixes'][prefix] = []
                stats['common_prefixes'][prefix].append(field)
        
        # Common suffixes
        for suffix in ['price', 'date', 'id', 'name', 'type', 'status', 'count', 'total']:
            if field_lower.endswith(suffix):
                if suffix not in stats['common_suffixes']:
                    stats['common_suffixes'][suffix] = []
                stats['common_suffixes'][suffix].append(field)
        
        # Field categories
        if any(term in field_lower for term in ['price', 'list', 'sale', 'value', 'cost']):
            if 'price' not in stats['field_categories']:
                stats['field_categories']['price'] = []
            stats['field_categories']['price'].append(field)
        
        if any(term in field_lower for term in ['bedroom', 'bed', 'br']):
            if 'bedrooms' not in stats['field_categories']:
                stats['field_categories']['bedrooms'] = []
            stats['field_categories']['bedrooms'].append(field)
        
        if any(term in field_lower for term in ['bathroom', 'bath', 'ba']):
            if 'bathrooms' not in stats['field_categories']:
                stats['field_categories']['bathrooms'] = []
            stats['field_categories']['bathrooms'].append(field)
        
        if any(term in field_lower for term in ['city', 'state', 'zip', 'county', 'address', 'location']):
            if 'location' not in stats['field_categories']:
                stats['field_categories']['location'] = []
            stats['field_categories']['location'].append(field)
        
        if any(term in field_lower for term in ['status', 'state', 'condition']):
            if 'status' not in stats['field_categories']:
                stats['field_categories']['status'] = []
            stats['field_categories']['status'].append(field)
    
    return stats

def _fetch_lookup_values_for_important_fields(metadata, protocol):
    """
    Fetch lookup values for important fields to help the AI use correct values.
    """
    lookup_data = {}
    
    try:
        # Get the client from session state
        if hasattr(st.session_state, 'rets_client') and st.session_state.rets_client:
            client = st.session_state.rets_client
            
            # Define important field patterns to look for
            important_patterns = {
                'status': ['status', 'state', 'condition', 'listing'],
                'property_type': ['property', 'type', 'category', 'class'],
                'transaction_type': ['transaction', 'sale', 'rent', 'lease'],
                'listing_type': ['listing', 'type', 'category']
            }
            
            # Find fields that match these patterns
            all_fields = []
            if protocol == "RESO Web API":
                for resource_name, resource_data in metadata.items():
                    if isinstance(resource_data, dict):
                        properties = resource_data.get('properties', [])
                        for prop in properties:
                            field_name = prop.get('name', '')
                            if field_name:
                                all_fields.append((field_name, resource_name))
            else:
                for metadata_type, metadata_content in metadata.items():
                    if metadata_type.startswith('TABLE_') and metadata_content:
                        if isinstance(metadata_content, dict) and 'fields' in metadata_content:
                            table_name = metadata_type.replace('TABLE_', '')
                            fields = metadata_content['fields']
                            for field in fields:
                                field_name = field.get('SystemName', field.get('StandardName', ''))
                                if field_name:
                                    all_fields.append((field_name, table_name))
            
            # Find important fields and fetch their lookup values
            for pattern_name, search_terms in important_patterns.items():
                matching_fields = []
                
                for field_name, resource_name in all_fields:
                    field_lower = field_name.lower()
                    if any(term in field_lower for term in search_terms):
                        matching_fields.append((field_name, resource_name))
                
                # Fetch lookup values for the first few matching fields
                for field_name, resource_name in matching_fields[:3]:  # Limit to 3 fields per pattern
                    try:
                        if hasattr(client, 'get_lookup_values'):
                            lookup_result = client.get_lookup_values(resource_name, field_name)
                            if lookup_result and 'values' in lookup_result:
                                values = lookup_result['values']
                                if values:
                                    lookup_data[f"{field_name} ({resource_name})"] = {
                                        'field': field_name,
                                        'resource': resource_name,
                                        'values': list(values.keys())[:20],  # Limit to first 20 values
                                        'total_count': len(values)
                                    }
                    except Exception as e:
                        # Silently continue if lookup fails for this field
                        continue
            
            # Also fetch lookup values for fields that have lookup names in RETS metadata
            if protocol == "RETS":
                for metadata_type, metadata_content in metadata.items():
                    if metadata_type.startswith('TABLE_') and metadata_content:
                        if isinstance(metadata_content, dict) and 'fields' in metadata_content:
                            table_name = metadata_type.replace('TABLE_', '')
                            fields = metadata_content['fields']
                            for field in fields:
                                field_name = field.get('SystemName', field.get('StandardName', ''))
                                lookup_name = field.get('LookupName', '')
                                
                                if field_name and lookup_name:
                                    try:
                                        lookup_result = client.get_lookup_values(table_name, field_name)
                                        if lookup_result and 'values' in lookup_result:
                                            values = lookup_result['values']
                                            if values:
                                                lookup_data[f"{field_name} ({table_name})"] = {
                                                    'field': field_name,
                                                    'resource': table_name,
                                                    'lookup_name': lookup_name,
                                                    'values': list(values.keys())[:20],
                                                    'total_count': len(values)
                                                }
                                    except Exception as e:
                                        continue
                        
    except Exception as e:
        # If lookup fetching fails, continue without lookup data
        st.warning(f"Could not fetch lookup values: {str(e)}")
    
    return lookup_data

def _enhance_query_with_lookup_values(query_result, metadata, protocol):
    """
    Enhance the AI-generated query by fetching lookup values only for the fields actually used.
    """
    try:
        query = query_result.get('query', '')
        if not query:
            return query_result
        
        # Extract field names from the query
        used_fields = _extract_fields_from_query(query, protocol)
        
        if not used_fields:
            return query_result
        
        # Fetch lookup values only for the fields used in the query
        lookup_values = _fetch_lookup_values_for_specific_fields(used_fields, metadata, protocol)
        
        if lookup_values:
            # Create enhanced explanation
            enhanced_explanation = query_result.get('explanation', '')
            enhanced_explanation += "\n\n**Lookup Values Used:**"
            
            # Update the query to use actual lookup values
            updated_query = query_result.get('query', '')
            
            for field_name, lookup_info in lookup_values.items():
                values = lookup_info.get('values', [])
                if values:
                    enhanced_explanation += f"\n- {field_name}: {', '.join(values[:5])}"
                    if len(values) > 5:
                        enhanced_explanation += f" (and {len(values) - 5} more)"
                    
                    # Update the query to use the correct lookup value
                    if protocol == "RETS":
                        # For RETS, replace generic values with actual lookup values
                        # Look for patterns like (FieldName=GenericValue) and replace with actual values
                        import re
                        
                        # Common value mappings
                        value_mappings = {
                            'active': ['ACT', 'A', '1'],
                            'pending': ['PEND', 'P', '2'],
                            'sold': ['SOLD', 'S', '3'],
                            'expired': ['EXP', 'E', '4'],
                            'withdrawn': ['WITH', 'W', '5'],
                            'residential': ['RES', 'R', '1'],
                            'commercial': ['COM', 'C', '2'],
                            'land': ['LAND', 'L', '3']
                        }
                        
                        # Find the best matching lookup value
                        best_match = None
                        for generic_term, possible_values in value_mappings.items():
                            if generic_term in updated_query.lower():
                                # Find which of the possible values exists in our lookup values
                                for possible_value in possible_values:
                                    if possible_value in values:
                                        best_match = possible_value
                                        break
                                if best_match:
                                    break
                        
                        if best_match:
                            # Replace the generic value with the actual lookup value
                            pattern = rf'\({field_name}=[^)]+\)'
                            replacement = f'({field_name}={best_match})'
                            updated_query = re.sub(pattern, replacement, updated_query)
                            enhanced_explanation += f"\n  → Updated query to use '{best_match}' instead of generic value"
                    
                    elif protocol == "RESO Web API":
                        # For RESO, similar logic but with OData format
                        import re
                        
                        # Common value mappings for RESO
                        value_mappings = {
                            'active': ['ACT', 'A', '1'],
                            'pending': ['PEND', 'P', '2'],
                            'sold': ['SOLD', 'S', '3'],
                            'expired': ['EXP', 'E', '4'],
                            'withdrawn': ['WITH', 'W', '5']
                        }
                        
                        # Find the best matching lookup value
                        best_match = None
                        for generic_term, possible_values in value_mappings.items():
                            if generic_term in updated_query.lower():
                                for possible_value in possible_values:
                                    if possible_value in values:
                                        best_match = possible_value
                                        break
                                if best_match:
                                    break
                        
                        if best_match:
                            # Replace the generic value with the actual lookup value
                            pattern = rf'{field_name}\s+eq\s+[\'"]?[^\'"]+[\'"]?'
                            replacement = f"{field_name} eq '{best_match}'"
                            updated_query = re.sub(pattern, replacement, updated_query)
                            enhanced_explanation += f"\n  → Updated query to use '{best_match}' instead of generic value"
            
            # Update the result with the corrected query
            query_result['query'] = updated_query
            query_result['explanation'] = enhanced_explanation
            query_result['lookup_values_used'] = lookup_values
            
            # Show success message
            st.success("✅ Query enhanced with actual lookup values from your feed!")
        
        return query_result
        
    except Exception as e:
        st.warning(f"Could not enhance query with lookup values: {str(e)}")
        return query_result

def _extract_fields_from_query(query, protocol):
    """
    Extract field names from the generated query.
    """
    fields = []
    
    if protocol == "RETS":
        # Extract field names from DMQL format like (FieldName=Value) or (FieldName>Value) or (FieldName<Value)
        import re
        field_matches = re.findall(r'\(([^=><]+)[=><]', query)
        fields.extend(field_matches)
    else:  # RESO Web API
        # Extract field names from OData format like FieldName eq 'Value'
        import re
        field_matches = re.findall(r'([A-Za-z_][A-Za-z0-9_]*)\s+(eq|ne|gt|ge|lt|le)', query)
        fields.extend([match[0] for match in field_matches])
    
    unique_fields = list(set(fields))  # Remove duplicates
    return unique_fields

def _fetch_lookup_values_for_specific_fields(field_names, metadata, protocol):
    """
    Fetch lookup values only for the specific fields used in the query.
    """
    lookup_data = {}
    
    try:
        # Get the client from session state
        if hasattr(st.session_state, 'rets_client') and st.session_state.rets_client:
            client = st.session_state.rets_client
            
            # Find the resource/table for each field
            field_locations = _find_field_locations(field_names, metadata, protocol)
            
            # Fetch lookup values only for the fields we need
            for field_name, location_info in field_locations.items():
                resource_name = location_info.get('resource')
                class_name = location_info.get('class')
                
                if resource_name:
                    try:
                        if hasattr(client, 'get_lookup_values'):
                            lookup_result = client.get_lookup_values(resource_name, field_name)
                            
                            if lookup_result and 'values' in lookup_result:
                                values = lookup_result['values']
                                if values:
                                    lookup_data[field_name] = {
                                        'field': field_name,
                                        'resource': resource_name,
                                        'class': class_name,
                                        'values': list(values.keys())[:10],  # Limit to first 10 values
                                        'total_count': len(values)
                                    }
                    except Exception as e:
                        # Silently continue if lookup fails for this field
                        continue
                        
    except Exception as e:
        # If lookup fetching fails, continue without lookup data
        pass
    
    return lookup_data

def _find_field_locations(field_names, metadata, protocol):
    """
    Find which resource/table each field belongs to.
    """
    field_locations = {}
    
    if protocol == "RESO Web API":
        for resource_name, resource_data in metadata.items():
            if isinstance(resource_data, dict):
                properties = resource_data.get('properties', [])
                for prop in properties:
                    field_name = prop.get('name', '')
                    if field_name in field_names:
                        field_locations[field_name] = {'resource': resource_name}
    else:
        # For RETS, we need to find the resource and class
        # First, find which resource/class combinations contain our fields
        for metadata_type, metadata_content in metadata.items():
            if metadata_type.startswith('TABLE_') and metadata_content:
                if isinstance(metadata_content, dict) and 'fields' in metadata_content:
                    table_name = metadata_type.replace('TABLE_', '')
                    fields = metadata_content['fields']
                    for field in fields:
                        field_name = field.get('SystemName', field.get('StandardName', ''))
                        if field_name in field_names:
                            # Parse the table name to get resource and class
                            # Format is typically "Resource_Class" or just "Resource"
                            if '_' in table_name:
                                resource, class_name = table_name.split('_', 1)
                            else:
                                resource = table_name
                                class_name = None
                            
                            field_locations[field_name] = {
                                'resource': resource,
                                'class': class_name,
                                'full_table': table_name
                            }
    
    return field_locations

def _create_ai_prompt(request, metadata_summary, protocol):
    """
    Create a comprehensive prompt for the AI to generate a query using ALL available fields.
    """
    # Prepare comprehensive field information
    total_fields = metadata_summary['field_statistics']['total_fields']
    
    # Get all available fields for the AI to search through
    all_fields_list = metadata_summary['all_fields']
    
    # Create field categories for better matching
    field_categories = metadata_summary['field_statistics']['field_categories']
    
    prompt = f"""
You are an expert in {protocol} query generation. You have access to ALL {total_fields} fields from the metadata. 
Analyze the user's request and find the EXACT field names that match their requirements.

USER REQUEST: "{request}"

METADATA SUMMARY:
Protocol: {metadata_summary['protocol']}
Total Available Fields: {total_fields}
Available Resources: {len(metadata_summary['resources'])}

RESOURCE DETAILS:
{chr(10).join([f"• {r['name']}: {r['field_count']} fields" for r in metadata_summary['resources'][:10]])}

COMPREHENSIVE FIELD CATEGORIES:
"""
    
    # Add field categories with actual field names
    for category, fields in field_categories.items():
        if fields:
            prompt += f"\n{category.upper()} FIELDS ({len(fields)} available):\n"
            # Show all fields in this category, not just first 5
            for field in fields:
                prompt += f"  - {field}\n"
    
    # Add common field patterns
    prompt += f"""
COMMON FIELD PATTERNS:
- Price Fields: {', '.join(metadata_summary['common_fields']['price_fields'][:10])}
- Status Fields: {', '.join(metadata_summary['common_fields']['status_fields'][:10])}
- Bedroom Fields: {', '.join(metadata_summary['common_fields']['bedroom_fields'][:10])}
- Bathroom Fields: {', '.join(metadata_summary['common_fields']['bathroom_fields'][:10])}
- Location Fields: {', '.join(metadata_summary['common_fields']['location_fields'][:10])}
- Date Fields: {', '.join(metadata_summary['common_fields']['date_fields'][:10])}
- Property Type Fields: {', '.join(metadata_summary['common_fields']['property_type_fields'][:10])}

LOOKUP VALUES FOR IMPORTANT FIELDS (use these exact values):
"""
    
    prompt += f"""

ALL AVAILABLE FIELDS (search through these for exact matches):
"""
    
    # Add all fields in a searchable format
    for i, field in enumerate(all_fields_list):
        prompt += f"{field}"
        if (i + 1) % 10 == 0:  # New line every 10 fields
            prompt += "\n"
        else:
            prompt += ", "
    
    prompt += f"""

CRITICAL INSTRUCTIONS:
1. Search through ALL {total_fields} available fields above to find EXACT field names
2. Do NOT use generic field names like "ListPrice" or "Status" unless they actually exist in the field list
3. Match user terms to actual field names in the metadata
4. If you can't find an exact match, look for similar field names or explain what's available
5. Use the most specific field names available for the user's request
6. **CRITICAL**: Use generic values like "Active", "Residential", "Sale" for now - the system will enhance the query with actual lookup values afterward
7. Focus on finding the correct field names first, then use appropriate generic values
8. The system will automatically fetch and show you the actual lookup values for the fields you use

TASK:
1. Analyze the user's request to understand what they're looking for
2. Search through ALL available fields to find exact matches
3. Generate a valid {protocol} query using ONLY field names that exist in the metadata
4. Provide a clear explanation of what the query does

QUERY FORMAT:
"""
    
    if protocol == "RETS":
        prompt += """- For RETS: Use DMQL format with these EXACT operators:
  * Equals: (FieldName=Value)
  * Greater than: (FieldName=Value+)  (use + after the value)
  * Greater than or equal: (FieldName=Value+)  (use + after the value)
  * Less than: (FieldName=-Value)  (use - before the value)
  * Less than or equal: (FieldName=-Value)  (use - before the value)
  * Range: (FieldName=MinValue-MaxValue)  (use - between values)
  * Multiple conditions: (Field1=Value1),(Field2=Value2+)  (use commas for AND)
  * Wildcard: (FieldName=*Value*)  (use * for LIKE)
  
  Examples:
  - Active listings: (Status=Active)
  - Price above $500k: (ListPrice=500000+)
  - 3+ bedrooms: (BedroomsTotal=3+)
  - Price range: (ListPrice=300000-800000)
  - Multiple conditions: (Status=Active),(ListPrice=500000+),(BedroomsTotal=3+)"""
    else:
        prompt += """- For RESO Web API: Use OData format like "FieldName eq 'Value' and FieldName2 gt 100"
  * Equals: FieldName eq 'Value'
  * Greater than: FieldName gt Value
  * Greater than or equal: FieldName ge Value
  * Less than: FieldName lt Value
  * Less than or equal: FieldName le Value
  * AND: FieldName1 eq 'Value1' and FieldName2 gt Value2
  * OR: FieldName1 eq 'Value1' or FieldName2 eq 'Value2'"""
    
    prompt += f"""

RESPONSE FORMAT (JSON):
{{
    "query": "the generated query string using actual field names",
    "explanation": "clear explanation of what the query does",
    "field_mapping": {{
        "user_request_term": "actual_field_name_used"
    }},
    "ai_analysis": {{
        "identified_requirements": ["list of requirements identified"],
        "selected_fields": ["list of exact field names selected"],
        "reasoning": "explanation of why these specific fields were chosen",
        "field_search_results": "summary of field matching process"
    }}
}}

Generate the query now, using ONLY field names that exist in the metadata above:
"""
    return prompt

def _parse_ai_response(response_text, request, protocol):
    """
    Parse the AI response and extract the query information.
    """
    try:
        # Try to extract JSON from the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end != 0:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            
            # Post-process the query to fix any incorrect operators
            if protocol == "RETS" and result.get('query'):
                result['query'] = _fix_rets_operators(result['query'])
            
            return {
                'query': result.get('query', ''),
                'explanation': result.get('explanation', ''),
                'field_mapping': result.get('field_mapping', {}),
                'ai_analysis': result.get('ai_analysis', {})
            }
        else:
            # Fallback: try to extract query from text
            return _extract_query_from_text(response_text, request, protocol)
            
    except json.JSONDecodeError:
        # Fallback: try to extract query from text
        return _extract_query_from_text(response_text, request, protocol)

def _fix_rets_operators(query):
    """
    Fix common operator mistakes in RETS DMQL queries.
    Converts standard comparison operators to proper RETS syntax.
    """
    import re
    
    # Fix greater than operators: (Field>Value) -> (Field=Value+)
    query = re.sub(r'\(([^=]+)>([^)]+)\)', r'(\1=\2+)', query)
    
    # Fix greater than or equal operators: (Field>=Value) -> (Field=Value+)
    query = re.sub(r'\(([^=]+)>=([^)]+)\)', r'(\1=\2+)', query)
    
    # Fix less than operators: (Field<Value) -> (Field=-Value)
    query = re.sub(r'\(([^=]+)<([^)]+)\)', r'(\1=-\2)', query)
    
    # Fix less than or equal operators: (Field<=Value) -> (Field=-Value)
    query = re.sub(r'\(([^=]+)<=([^)]+)\)', r'(\1=-\2)', query)
    
    # Fix not equal operators: (Field!=Value) -> (Field!Value)
    query = re.sub(r'\(([^=]+)!=([^)]+)\)', r'(\1!\2)', query)
    
    # Fix AND operators: (Field1=Value1) AND (Field2=Value2) -> (Field1=Value1),(Field2=Value2)
    query = re.sub(r'\)\s+AND\s+\(', r'),(', query)
    
    # Fix OR operators: (Field1=Value1) OR (Field2=Value2) -> (Field1=Value1)|(Field2=Value2)
    query = re.sub(r'\)\s+OR\s+\(', r')|(', query)
    
    return query

def _extract_query_from_text(text, request, protocol):
    """
    Extract query information from AI text response when JSON parsing fails.
    """
    # Look for query patterns in the text
    if protocol == "RETS":
        # Look for DMQL patterns
        query_match = re.search(r'\([^)]+\)(?:,\([^)]+\))*', text)
    else:
        # Look for OData patterns
        query_match = re.search(r'[A-Za-z]+\s+(eq|ne|gt|ge|lt|le)\s+[\'"]?[^\'"]+[\'"]?(?:\s+and\s+[A-Za-z]+\s+(eq|ne|gt|ge|lt|le)\s+[\'"]?[^\'"]+[\'"]?)*', text)
    
    if query_match:
        query = query_match.group(0)
        
        # Post-process RETS queries to fix operators
        if protocol == "RETS":
            query = _fix_rets_operators(query)
        
        return {
            'query': query,
            'explanation': f"AI-generated query based on: {request}",
            'field_mapping': {},
            'ai_analysis': {
                'reasoning': "Query extracted from AI response"
            }
        }
    
    return None

def _show_ai_analysis(ai_analysis):
    """
    Show detailed AI analysis to the user.
    """
    if not ai_analysis:
        return
    
    st.write("**🤖 AI Analysis:**")
    
    if ai_analysis.get('identified_requirements'):
        st.write("**Requirements Identified:**")
        for req in ai_analysis['identified_requirements']:
            st.write(f"- {req}")
    
    if ai_analysis.get('selected_fields'):
        st.write("**Fields Selected:**")
        for field in ai_analysis['selected_fields']:
            st.write(f"- {field}")
    
    if ai_analysis.get('reasoning'):
        st.write("**AI Reasoning:**")
        st.write(ai_analysis['reasoning'])



def _show_debug_info(request, metadata, protocol):
    """
    Show comprehensive debugging information when AI query generation fails.
    """
    st.write("**🔍 Comprehensive Debug Information:**")
    
    # Show the user request
    st.write(f"**User Request:** {request}")
    
    # Generate comprehensive metadata summary for debugging
    metadata_summary = _prepare_metadata_summary(metadata, protocol)
    
    # Show comprehensive metadata summary
    st.write("**📊 Complete Metadata Analysis:**")
    st.write(f"- Total Available Fields: {metadata_summary['field_statistics']['total_fields']}")
    st.write(f"- Available Resources: {len(metadata_summary['resources'])}")
    
    # Show all resources with field counts
    st.write("**📋 All Resources:**")
    for resource in metadata_summary['resources'][:10]:  # Show first 10
        st.write(f"- {resource['name']}: {resource['field_count']} fields")
    
    # Show comprehensive field categories
    field_categories = metadata_summary['field_statistics']['field_categories']
    st.write("**🏷️ Field Categories Found:**")
    for category, fields in field_categories.items():
        if fields:
            st.write(f"- {category.title()} ({len(fields)} fields): {', '.join(fields[:10])}")
            if len(fields) > 10:
                st.write(f"  ... and {len(fields) - 10} more {category} fields")
    
    # Show lookup values found
    lookup_values = metadata_summary.get('lookup_values', {})
    if lookup_values:
        st.write("**📋 Lookup Values Found:**")
        for field_key, lookup_info in lookup_values.items():
            values = lookup_info.get('values', [])
            if values:
                st.write(f"- {field_key}: {', '.join(values[:10])}")
                if len(values) > 10:
                    st.write(f"  ... and {len(values) - 10} more values")
    else:
        st.write("**📋 Lookup Values:** No lookup values found - AI will use generic values")
    
    # Show common field patterns
    st.write("**🔍 Common Field Patterns:**")
    common_fields = metadata_summary['common_fields']
    for pattern, fields in common_fields.items():
        if fields:
            st.write(f"- {pattern.replace('_', ' ').title()}: {', '.join(fields[:10])}")
            if len(fields) > 10:
                st.write(f"  ... and {len(fields) - 10} more")
    
    # Show field search suggestions based on user request
    st.write("**🎯 Field Search Suggestions:**")
    request_lower = request.lower()
    
    # Extract potential search terms from user request
    search_terms = []
    if any(term in request_lower for term in ['price', 'cost', 'value', 'list']):
        search_terms.extend(['price', 'list', 'sale', 'value'])
    if any(term in request_lower for term in ['bedroom', 'bed', 'br']):
        search_terms.extend(['bedroom', 'bed', 'br'])
    if any(term in request_lower for term in ['bathroom', 'bath', 'ba']):
        search_terms.extend(['bathroom', 'bath', 'ba'])
    if any(term in request_lower for term in ['city', 'state', 'zip', 'county', 'address']):
        search_terms.extend(['city', 'state', 'zip', 'county', 'address'])
    if any(term in request_lower for term in ['status', 'active', 'sold', 'pending']):
        search_terms.extend(['status', 'state', 'condition'])
    
    # Find matching fields for each search term
    all_fields = metadata_summary['all_fields']
    for term in search_terms:
        matching_fields = [f for f in all_fields if term.lower() in f.lower()]
        if matching_fields:
            st.write(f"- Fields matching '{term}': {', '.join(matching_fields[:10])}")
            if len(matching_fields) > 10:
                st.write(f"  ... and {len(matching_fields) - 10} more")
    
    # Show all available fields in a searchable format
    with st.expander("📋 All Available Fields (Click to View)", expanded=False):
        st.write("**Complete Field List:**")
        # Display fields in columns for better readability
        col1, col2, col3 = st.columns(3)
        fields_per_col = len(all_fields) // 3 + 1
        
        for i, field in enumerate(all_fields):
            col_idx = i // fields_per_col
            if col_idx == 0:
                with col1:
                    st.write(f"• {field}")
            elif col_idx == 1:
                with col2:
                    st.write(f"• {field}")
            else:
                with col3:
                    st.write(f"• {field}")
    
    st.write("**💡 Suggestions:**")
    st.write("- The AI now has access to ALL available fields in your feed")
    st.write("- Try being more specific about what you're looking for")
    st.write("- Use the field search suggestions above to find exact field names")
    st.write("- Check the 'All Available Fields' expander to see what's actually available")
    st.write("- Make sure your API key is valid and has access to Gemini models") 