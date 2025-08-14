import pandas as pd
import streamlit as st
from typing import Dict, List, Any, Optional
import re
from urllib.parse import urlparse
import base64
from datetime import datetime, timedelta
import json
import time
from typing import Any, Dict, Optional, Union

def validate_connection_params(url: str, username: str, password: str) -> bool:
    """
    Validate RETs connection parameters.
    
    Args:
        url: RETs server URL
        username: Username
        password: Password
        
    Returns:
        bool: True if parameters are valid, False otherwise
    """
    # Check if all fields are provided
    if not url or not username or not password:
        return False
    
    # Basic URL validation
    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return False
    except:
        return False
    
    # Check for minimum length requirements
    if len(username) < 1 or len(password) < 1:
        return False
    
    return True

def format_metadata(metadata: Dict[str, Any], search_term: str = "", protocol: str = "RETS") -> Optional[pd.DataFrame]:
    """
    Format metadata for display in Streamlit.
    
    Args:
        metadata: Metadata dictionary
        search_term: Optional search term to filter results
        protocol: Protocol type ("RETS" or "RESO Web API")
        
    Returns:
        Formatted DataFrame or None if no data
    """
    if not metadata:
        return None
    
    formatted_data = []
    
    # Handle RESO Web API metadata format
    if protocol == "RESO Web API":
        if 'resources' in metadata:
            for resource in metadata['resources']:
                formatted_data.append({
                    'Category': 'Resource',
                    'Type': 'EntitySet',
                    'Name': resource,
                    'Description': f'RESO {resource} resource',
                    'Value': '',
                    'Details': f'OData EntitySet for {resource}'
                })
        
        # Parse XML metadata content if available
        if 'metadata_content' in metadata:
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(metadata['metadata_content'])
                
                # Extract schema information
                for schema in root.iter():
                    if schema.tag.endswith('Schema'):
                        namespace = schema.get('Namespace', 'Unknown')
                        formatted_data.append({
                            'Category': 'Schema',
                            'Type': 'Namespace', 
                            'Name': namespace,
                            'Description': 'RESO OData Schema',
                            'Value': schema.get('Alias', ''),
                            'Details': f'OData Schema: {namespace}'
                        })
                
                # Extract entity types
                for entity_type in root.iter():
                    if entity_type.tag.endswith('EntityType'):
                        name = entity_type.get('Name', '')
                        key_props = []
                        for key in entity_type.iter():
                            if key.tag.endswith('Key'):
                                for prop_ref in key.iter():
                                    if prop_ref.tag.endswith('PropertyRef'):
                                        key_props.append(prop_ref.get('Name', ''))
                        
                        formatted_data.append({
                            'Category': 'EntityType',
                            'Type': 'Definition',
                            'Name': name,
                            'Description': f'Entity type definition for {name}',
                            'Value': ', '.join(key_props) if key_props else '',
                            'Details': f'Key Properties: {", ".join(key_props) if key_props else "None"}'
                        })
                
                # Extract enum types (lookup values)
                for enum_type in root.iter():
                    if enum_type.tag.endswith('EnumType'):
                        name = enum_type.get('Name', '')
                        member_count = len([m for m in enum_type.iter() if m.tag.endswith('Member')])
                        formatted_data.append({
                            'Category': 'EnumType',
                            'Type': 'Lookup',
                            'Name': name,
                            'Description': f'Enumeration type with {member_count} values',
                            'Value': str(member_count),
                            'Details': f'Lookup values for {name} field'
                        })
                        
            except Exception as e:
                formatted_data.append({
                    'Category': 'Error',
                    'Type': 'XML Parse',
                    'Name': 'Metadata Parse Error',
                    'Description': str(e),
                    'Value': '',
                    'Details': 'Failed to parse RESO metadata XML'
                })
    
    # Handle RETS metadata format (existing logic)
    elif isinstance(metadata, dict):
        for metadata_type, metadata_content in metadata.items():
            if metadata_type == 'SYSTEM' and metadata_content:
                if isinstance(metadata_content, dict) and 'system' in metadata_content:
                    for key, value in metadata_content['system'].items():
                        formatted_data.append({
                            'Category': 'System',
                            'Type': 'System Info',
                            'Name': key,
                            'Value': str(value)[:100],
                            'Description': f'System {key}'
                        })
            
            elif metadata_type == 'RESOURCE' and metadata_content:
                if isinstance(metadata_content, dict) and 'resources' in metadata_content:
                    for resource in metadata_content['resources']:
                        if isinstance(resource, dict):
                            name = resource.get('ResourceID') or resource.get('StandardName') or 'Unknown'
                            description = resource.get('Description') or resource.get('LongName') or 'Resource'
                            formatted_data.append({
                                'Category': 'Resource',
                                'Type': 'Resource',
                                'Name': name,
                                'Value': name,
                                'Description': description[:100]
                            })
            
            elif metadata_type.startswith('CLASS_') and metadata_content:
                resource_name = metadata_type.replace('CLASS_', '')
                if isinstance(metadata_content, dict) and 'classes' in metadata_content:
                    for class_info in metadata_content['classes']:
                        if isinstance(class_info, dict):
                            name = class_info.get('ClassName') or class_info.get('StandardName') or 'Unknown'
                            description = class_info.get('Description') or class_info.get('LongName') or 'Class'
                            formatted_data.append({
                                'Category': 'Class',
                                'Type': f'Class ({resource_name})',
                                'Name': name,
                                'Value': name,
                                'Description': description[:100]
                            })
            
            elif metadata_type.startswith('TABLE_') and metadata_content:
                resource_class = metadata_type.replace('TABLE_', '').replace('_', ':')
                if isinstance(metadata_content, dict) and 'fields' in metadata_content:
                    for field in metadata_content['fields']:
                        if isinstance(field, dict):
                            name = field.get('SystemName') or field.get('StandardName') or field.get('LongName') or 'Unknown'
                            field_type = field.get('DataType') or field.get('Interpretation') or 'Unknown'
                            description = field.get('LongName') or field.get('ShortName') or 'Field'
                            formatted_data.append({
                                'Category': 'Field',
                                'Type': f'Field ({resource_class}) - {field_type}',
                                'Name': name,
                                'Value': name,
                                'Description': description[:100]
                            })
    
    # Handle simple metadata structure (legacy/fallback)
    if not formatted_data:
        # Process system information
        if 'system' in metadata:
            for key, value in metadata['system'].items():
                formatted_data.append({
                    'Category': 'System',
                    'Type': key,
                    'Name': key,
                    'Value': str(value)[:100],  # Truncate long values
                    'Description': f'System {key}'
                })
        
        # Process resources
        if 'resources' in metadata:
            for resource in metadata['resources']:
                if isinstance(resource, dict):
                    name = resource.get('name') or resource.get('ResourceID') or 'Unknown'
                    description = resource.get('description') or resource.get('desc') or 'Resource'
                    formatted_data.append({
                        'Category': 'Resource',
                        'Type': 'Resource',
                        'Name': name,
                        'Value': name,
                        'Description': description
                    })
        
        # Process classes
        if 'classes' in metadata:
            for class_info in metadata['classes']:
                if isinstance(class_info, dict):
                    name = class_info.get('name') or class_info.get('ClassName') or 'Unknown'
                    description = class_info.get('description') or class_info.get('desc') or 'Class'
                    resource = class_info.get('resource') or 'Unknown'
                    formatted_data.append({
                        'Category': 'Class',
                        'Type': f'Class ({resource})',
                        'Name': name,
                        'Value': name,
                        'Description': description
                    })
        
        # Process fields
        if 'fields' in metadata:
            for field_info in metadata['fields']:
                if isinstance(field_info, dict):
                    name = field_info.get('name') or field_info.get('FieldName') or 'Unknown'
                    field_type = field_info.get('type') or field_info.get('DataType') or 'Unknown'
                    description = field_info.get('description') or field_info.get('desc') or 'Field'
                    resource = field_info.get('resource') or 'Unknown'
                    formatted_data.append({
                        'Category': 'Field',
                        'Type': f'Field ({resource}) - {field_type}',
                        'Name': name,
                        'Value': name,
                        'Description': description
                    })
    
    if not formatted_data:
        return None
    
    # Create DataFrame
    df = pd.DataFrame(formatted_data)
    
    # Apply search filter if provided
    if search_term:
        search_term = search_term.lower()
        mask = (
            df['Name'].str.lower().str.contains(search_term, na=False) |
            df['Description'].str.lower().str.contains(search_term, na=False) |
            df['Type'].str.lower().str.contains(search_term, na=False) |
            df['Value'].str.lower().str.contains(search_term, na=False)
        )
        df = df[mask]
    
    if df.empty:
        return None
    return df.copy()  # Ensure we return a DataFrame, not a Series

def create_download_link(df: pd.DataFrame, filename: str) -> str:
    """
    Create a download link for a DataFrame.
    
    Args:
        df: DataFrame to download
        filename: Name of the file
        
    Returns:
        HTML download link
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV</a>'
    return href

def format_query_results(results: List[Dict[str, Any]]) -> pd.DataFrame:
    """
    Format query results for display.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        Formatted DataFrame
    """
    if not results:
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    
    # Clean up column names
    df.columns = [col.replace('_', ' ').title() for col in df.columns]
    
    # Handle common data types
    for col in df.columns:
        if 'price' in col.lower():
            # Try to convert price columns to numeric
            try:
                df[col] = pd.to_numeric(df[col], errors='ignore')
            except:
                pass
        elif 'date' in col.lower() or 'timestamp' in col.lower():
            # Try to convert date columns
            try:
                df[col] = pd.to_datetime(df[col], errors='ignore')
            except:
                pass
    
    return df

def validate_query_params(resource: str, class_name: str, query: str) -> tuple[bool, str]:
    """
    Validate query parameters.
    
    Args:
        resource: Resource name
        class_name: Class name
        query: Query string
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not resource:
        return False, "Resource name is required"
    
    if not class_name:
        return False, "Class name is required"
    
    # Basic query validation
    if query and not re.match(r'^[\w\s\(\),=\+\-\*\.<>]*$', query):
        return False, "Query contains invalid characters"
    
    return True, ""

def get_sample_queries() -> List[Dict[str, str]]:
    """
    Get sample queries for demonstration.
    
    Returns:
        List of sample query dictionaries
    """
    return [
        {
            'name': 'Active Listings',
            'resource': 'Property',
            'class': 'ResidentialProperty',
            'query': '(Status=Active)',
            'description': 'Find all active property listings'
        },
        {
            'name': 'Price Range',
            'resource': 'Property',
            'class': 'ResidentialProperty',
            'query': '(ListPrice=100000-500000)',
            'description': 'Properties between $100k and $500k'
        },
        {
            'name': 'Recently Modified',
            'resource': 'Property',
            'class': 'ResidentialProperty',
            'query': '(ModificationTimestamp=2024-01-01T00:00:00+)',
            'description': 'Properties modified since January 1, 2024'
        },
        {
            'name': 'Specific City',
            'resource': 'Property',
            'class': 'ResidentialProperty',
            'query': '(City=Austin)',
            'description': 'Properties in Austin'
        },
        {
            'name': 'Bedrooms and Bathrooms',
            'resource': 'Property',
            'class': 'ResidentialProperty',
            'query': '(Bedrooms=3+),(Bathrooms=2+)',
            'description': 'Properties with 3+ bedrooms and 2+ bathrooms'
        }
    ]

def format_field_info(field_info: Dict[str, Any]) -> str:
    """
    Format field information for display.
    
    Args:
        field_info: Field information dictionary
        
    Returns:
        Formatted field information string
    """
    parts = []
    
    if 'name' in field_info:
        parts.append(f"**{field_info['name']}**")
    
    if 'type' in field_info:
        parts.append(f"Type: {field_info['type']}")
    
    if 'description' in field_info:
        parts.append(f"Description: {field_info['description']}")
    
    if 'required' in field_info:
        parts.append(f"Required: {field_info['required']}")
    
    if 'max_length' in field_info:
        parts.append(f"Max Length: {field_info['max_length']}")
    
    return " | ".join(parts)

def clean_data_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean DataFrame for CSV export.
    
    Args:
        df: DataFrame to clean
        
    Returns:
        Cleaned DataFrame
    """
    # Create a copy to avoid modifying original
    cleaned_df = df.copy()
    
    # Remove or replace problematic characters
    for col in cleaned_df.select_dtypes(include=['object']).columns:
        cleaned_df[col] = cleaned_df[col].astype(str).str.replace('\n', ' ').str.replace('\r', ' ')
    
    # Handle missing values
    cleaned_df = cleaned_df.fillna('')
    
    return cleaned_df

def get_connection_tips() -> List[str]:
    """
    Get tips for RETs connection.
    
    Returns:
        List of connection tips
    """
    return [
        "Ensure your RETs URL includes the protocol (http:// or https://)",
        "Check that your username and password are correct",
        "Some RETs servers require specific User-Agent headers",
        "Verify that your IP address is whitelisted with the RETs provider",
        "Try connecting during off-peak hours if experiencing timeouts",
        "Contact your RETs provider if authentication continues to fail"
    ]

def analyze_metadata_for_suggestions(metadata, protocol="RETS"):
    """
    Analyze metadata to generate intelligent query suggestions.
    Returns categorized suggestions with explanations.
    """
    suggestions = {
        'basic_queries': [],
        'price_queries': [],
        'location_queries': [],
        'property_queries': [],
        'date_queries': [],
        'status_queries': [],
        'advanced_queries': []
    }
    
    if protocol == "RESO Web API":
        # Analyze RESO metadata
        for resource_name, resource_data in metadata.items():
            if isinstance(resource_data, dict):
                properties = resource_data.get('properties', [])
                
                # Extract field information
                fields = {}
                for prop in properties:
                    if isinstance(prop, dict):
                        field_name = prop.get('name', '')
                        field_type = prop.get('type', '').lower()
                        fields[field_name] = field_type
                
                # Generate suggestions based on field patterns
                suggestions = _generate_reso_suggestions(fields, resource_name, suggestions)
    
    else:
        # Analyze RETS metadata
        for metadata_type, metadata_content in metadata.items():
            if metadata_type.startswith('TABLE_') and metadata_content:
                if isinstance(metadata_content, dict) and 'fields' in metadata_content:
                    fields = {}
                    for field in metadata_content['fields']:
                        if isinstance(field, dict):
                            field_name = field.get('SystemName', field.get('StandardName', ''))
                            data_type = field.get('DataType', '').lower()
                            fields[field_name] = data_type
                    
                    # Generate suggestions based on field patterns
                    suggestions = _generate_rets_suggestions(fields, metadata_type.replace('TABLE_', ''), suggestions)
    
    return suggestions

def _generate_reso_suggestions(fields, resource_name, suggestions):
    """Generate RESO-specific query suggestions."""
    
    # Price-related fields
    price_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['price', 'listprice', 'saleprice', 'value'])]
    if price_fields:
        suggestions['price_queries'].extend([
            {
                'name': f'Active Listings Under $500k',
                'query': f"{price_fields[0]} lt 500000 and StandardStatus eq 'Active'",
                'description': f'Find active listings priced under $500,000 using {price_fields[0]}',
                'resource': resource_name
            },
            {
                'name': f'Price Range $200k-$400k',
                'query': f"{price_fields[0]} ge 200000 and {price_fields[0]} le 400000",
                'description': f'Properties in the $200k-$400k range using {price_fields[0]}',
                'resource': resource_name
            }
        ])
    
    # Status fields
    status_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['status', 'standardstatus', 'listingstatus'])]
    if status_fields:
        suggestions['status_queries'].extend([
            {
                'name': 'Active Listings Only',
                'query': f"{status_fields[0]} eq 'Active'",
                'description': f'Show only active listings using {status_fields[0]}',
                'resource': resource_name
            },
            {
                'name': 'Recently Sold',
                'query': f"{status_fields[0]} eq 'Closed'",
                'description': f'Show recently sold properties using {status_fields[0]}',
                'resource': resource_name
            }
        ])
    
    # Location fields
    location_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['city', 'state', 'zip', 'county', 'address'])]
    if location_fields:
        suggestions['location_queries'].extend([
            {
                'name': 'Properties in Specific City',
                'query': f"{location_fields[0]} eq 'Austin'",
                'description': f'Filter by city using {location_fields[0]} (replace Austin with your city)',
                'resource': resource_name
            }
        ])
    
    # Property type fields
    property_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['propertytype', 'type', 'category'])]
    if property_fields:
        suggestions['property_queries'].extend([
            {
                'name': 'Residential Properties Only',
                'query': f"{property_fields[0]} eq 'Residential'",
                'description': f'Filter for residential properties using {property_fields[0]}',
                'resource': resource_name
            }
        ])
    
    # Date fields
    date_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['date', 'timestamp', 'modified', 'created'])]
    if date_fields:
        current_date = datetime.now().strftime('%Y-%m-%d')
        suggestions['date_queries'].extend([
            {
                'name': 'Listings Updated This Month',
                'query': f"{date_fields[0]} ge {current_date[:7]}-01",
                'description': f'Properties updated this month using {date_fields[0]}',
                'resource': resource_name
            }
        ])
    
    # Bedroom/Bathroom fields
    bedroom_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['bedroom', 'beds'])]
    bathroom_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['bathroom', 'baths'])]
    
    if bedroom_fields and bathroom_fields:
        suggestions['property_queries'].extend([
            {
                'name': '3+ Bedrooms, 2+ Bathrooms',
                'query': f"{bedroom_fields[0]} ge 3 and {bathroom_fields[0]} ge 2",
                'description': f'Properties with 3+ bedrooms and 2+ bathrooms',
                'resource': resource_name
            }
        ])
    
    return suggestions

def _generate_rets_suggestions(fields, table_name, suggestions):
    """Generate RETS-specific query suggestions."""
    
    # Price-related fields
    price_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['price', 'listprice', 'saleprice', 'value'])]
    if price_fields:
        suggestions['price_queries'].extend([
            {
                'name': f'Active Listings Under $500k',
                'query': f"(Status=Active),({price_fields[0]}=-500000)",
                'description': f'Find active listings priced under $500,000 using {price_fields[0]}',
                'table': table_name
            },
            {
                'name': f'Price Range $200k-$400k',
                'query': f"({price_fields[0]}=200000-400000)",
                'description': f'Properties in the $200k-$400k range using {price_fields[0]}',
                'table': table_name
            }
        ])
    
    # Status fields
    status_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['status', 'listingstatus'])]
    if status_fields:
        suggestions['status_queries'].extend([
            {
                'name': 'Active Listings Only',
                'query': f"({status_fields[0]}=Active)",
                'description': f'Show only active listings using {status_fields[0]}',
                'table': table_name
            },
            {
                'name': 'Recently Sold',
                'query': f"({status_fields[0]}=Closed)",
                'description': f'Show recently sold properties using {status_fields[0]}',
                'table': table_name
            }
        ])
    
    # Location fields
    location_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['city', 'state', 'zip', 'county', 'address'])]
    if location_fields:
        suggestions['location_queries'].extend([
            {
                'name': 'Properties in Specific City',
                'query': f"({location_fields[0]}=Austin)",
                'description': f'Filter by city using {location_fields[0]} (replace Austin with your city)',
                'table': table_name
            }
        ])
    
    # Property type fields
    property_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['propertytype', 'type', 'category'])]
    if property_fields:
        suggestions['property_queries'].extend([
            {
                'name': 'Residential Properties Only',
                'query': f"({property_fields[0]}=Residential)",
                'description': f'Filter for residential properties using {property_fields[0]}',
                'table': table_name
            }
        ])
    
    # Date fields
    date_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['date', 'timestamp', 'modified', 'created'])]
    if date_fields:
        current_date = datetime.now().strftime('%Y-%m-%d')
        suggestions['date_queries'].extend([
            {
                'name': 'Listings Updated This Month',
                'query': f"({date_fields[0]}={current_date[:7]}-01+)",
                'description': f'Properties updated this month using {date_fields[0]}',
                'table': table_name
            }
        ])
    
    # Bedroom/Bathroom fields
    bedroom_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['bedroom', 'beds'])]
    bathroom_fields = [f for f in fields.keys() if any(term in f.lower() for term in ['bathroom', 'baths'])]
    
    if bedroom_fields and bathroom_fields:
        suggestions['property_queries'].extend([
            {
                'name': '3+ Bedrooms, 2+ Bathrooms',
                'query': f"({bedroom_fields[0]}=3+),({bathroom_fields[0]}=2+)",
                'description': f'Properties with 3+ bedrooms and 2+ bathrooms',
                'table': table_name
            }
        ])
    
    return suggestions

def get_smart_suggestions(metadata, protocol="RETS", user_context=None):
    """
    Get intelligent query suggestions based on metadata analysis and user context.
    
    Args:
        metadata: The metadata from the RETS/RESO server
        protocol: "RETS" or "RESO Web API"
        user_context: Optional dict with user preferences/history
    
    Returns:
        dict: Categorized query suggestions
    """
    # Analyze metadata for field patterns
    suggestions = analyze_metadata_for_suggestions(metadata, protocol)
    
    # Add context-aware suggestions
    if user_context:
        suggestions = _add_contextual_suggestions(suggestions, user_context, protocol)
    
    # Add common patterns that work across most systems
    suggestions = _add_common_patterns(suggestions, protocol)
    
    return suggestions

def _add_contextual_suggestions(suggestions, user_context, protocol):
    """Add suggestions based on user context and history."""
    
    # If user has recent queries, suggest variations
    if 'recent_queries' in user_context:
        recent_queries = user_context['recent_queries']
        
        # Analyze recent query patterns
        price_patterns = [q for q in recent_queries if any(term in q.lower() for term in ['price', 'listprice'])]
        if price_patterns:
            suggestions['advanced_queries'].append({
                'name': 'Similar Price Range (Based on History)',
                'query': _generate_similar_price_query(price_patterns[0], protocol),
                'description': 'Query similar to your recent price-based searches',
                'context': 'Based on your recent queries'
            })
    
    # If user has preferred locations
    if 'preferred_locations' in user_context:
        locations = user_context['preferred_locations']
        for location in locations[:3]:  # Limit to first 3
            if protocol == "RESO Web API":
                suggestions['location_queries'].append({
                    'name': f'Properties in {location}',
                    'query': f"City eq '{location}'",
                    'description': f'Properties in your preferred location: {location}',
                    'context': 'Based on your preferences'
                })
            else:
                suggestions['location_queries'].append({
                    'name': f'Properties in {location}',
                    'query': f"(City={location})",
                    'description': f'Properties in your preferred location: {location}',
                    'context': 'Based on your preferences'
                })
    
    return suggestions

def _add_common_patterns(suggestions, protocol):
    """Add common query patterns that work across most systems."""
    
    if protocol == "RESO Web API":
        suggestions['basic_queries'].extend([
            {
                'name': 'All Active Listings',
                'query': "StandardStatus eq 'Active'",
                'description': 'Basic query to get all active listings',
                'context': 'Common pattern'
            },
            {
                'name': 'Recent Listings (Last 30 Days)',
                'query': f"ModificationTimestamp ge {datetime.now().strftime('%Y-%m-%d')}",
                'description': 'Listings modified in the last 30 days',
                'context': 'Common pattern'
            }
        ])
        
        suggestions['advanced_queries'].extend([
            {
                'name': 'Luxury Properties ($1M+)',
                'query': "ListPrice ge 1000000 and StandardStatus eq 'Active'",
                'description': 'High-end properties over $1 million',
                'context': 'Common pattern'
            },
            {
                'name': 'New Construction',
                'query': "PropertyType eq 'New Construction' or PropertyType eq 'New'",
                'description': 'New construction properties',
                'context': 'Common pattern'
            }
        ])
    
    else:  # RETS
        suggestions['basic_queries'].extend([
            {
                'name': 'All Active Listings',
                'query': "(Status=Active)",
                'description': 'Basic query to get all active listings',
                'context': 'Common pattern'
            },
            {
                'name': 'Recent Listings (Last 30 Days)',
                'query': f"(ModificationTimestamp={datetime.now().strftime('%Y-%m-%d')}+)",
                'description': 'Listings modified in the last 30 days',
                'context': 'Common pattern'
            }
        ])
        
        suggestions['advanced_queries'].extend([
            {
                'name': 'Luxury Properties ($1M+)',
                'query': "(Status=Active),(ListPrice=1000000+)",
                'description': 'High-end properties over $1 million',
                'context': 'Common pattern'
            },
            {
                'name': 'New Construction',
                'query': "(PropertyType=New Construction)",
                'description': 'New construction properties',
                'context': 'Common pattern'
            }
        ])
    
    return suggestions

def _generate_similar_price_query(price_query, protocol):
    """Generate a similar price query based on an existing one."""
    # Extract price range from existing query
    if protocol == "RESO Web API":
        # Look for price patterns like "ListPrice ge 200000 and ListPrice le 400000"
        price_match = re.search(r'ListPrice\s+(ge|gt)\s+(\d+)', price_query)
        if price_match:
            min_price = int(price_match.group(2))
            max_price = min_price * 2  # Double the range
            return f"ListPrice ge {min_price} and ListPrice le {max_price}"
    else:
        # Look for price patterns like "(ListPrice=200000-400000)"
        price_match = re.search(r'ListPrice=(\d+)-(\d+)', price_query)
        if price_match:
            min_price = int(price_match.group(1))
            max_price = int(price_match.group(2))
            new_min = int(min_price * 0.8)  # 20% lower
            new_max = int(max_price * 1.2)  # 20% higher
            return f"(ListPrice={new_min}-{new_max})"
    
    # Fallback to a generic price query
    return "ListPrice ge 200000 and ListPrice le 500000" if protocol == "RESO Web API" else "(ListPrice=200000-500000)"

def get_field_recommendations(metadata, protocol="RETS", search_term=""):
    """
    Get field recommendations based on search term and metadata analysis.
    
    Args:
        metadata: The metadata from the RETS/RESO server
        protocol: "RETS" or "RESO Web API"
        search_term: User's search term
    
    Returns:
        list: Recommended fields with relevance scores
    """
    recommendations = []
    
    if protocol == "RESO Web API":
        for resource_name, resource_data in metadata.items():
            if isinstance(resource_data, dict):
                properties = resource_data.get('properties', [])
                
                for prop in properties:
                    if isinstance(prop, dict):
                        field_name = prop.get('name', '')
                        field_type = prop.get('type', '')
                        description = prop.get('description', '')
                        
                        # Calculate relevance score
                        relevance = _calculate_field_relevance(field_name, field_type, description, search_term)
                        
                        if relevance > 0:
                            recommendations.append({
                                'field_name': field_name,
                                'resource': resource_name,
                                'type': field_type,
                                'description': description,
                                'relevance': relevance
                            })
    
    else:  # RETS
        for metadata_type, metadata_content in metadata.items():
            if metadata_type.startswith('TABLE_') and metadata_content:
                if isinstance(metadata_content, dict) and 'fields' in metadata_content:
                    for field in metadata_content['fields']:
                        if isinstance(field, dict):
                            field_name = field.get('SystemName', field.get('StandardName', ''))
                            data_type = field.get('DataType', '')
                            long_name = field.get('LongName', '')
                            
                            # Calculate relevance score
                            relevance = _calculate_field_relevance(field_name, data_type, long_name, search_term)
                            
                            if relevance > 0:
                                recommendations.append({
                                    'field_name': field_name,
                                    'table': metadata_type.replace('TABLE_', ''),
                                    'type': data_type,
                                    'description': long_name,
                                    'relevance': relevance
                                })
    
    # Sort by relevance and return top recommendations
    recommendations.sort(key=lambda x: x['relevance'], reverse=True)
    return recommendations[:10]  # Return top 10

def _calculate_field_relevance(field_name, field_type, description, search_term):
    """Calculate relevance score for a field based on search term."""
    if not search_term:
        return 0
    
    search_lower = search_term.lower()
    field_lower = field_name.lower()
    type_lower = field_type.lower()
    desc_lower = description.lower()
    
    relevance = 0
    
    # Exact match gets highest score
    if search_lower == field_lower:
        relevance += 100
    elif search_lower in field_lower:
        relevance += 50
    elif field_lower in search_lower:
        relevance += 30
    
    # Partial matches
    if any(word in field_lower for word in search_lower.split()):
        relevance += 20
    
    # Type matching
    if search_lower in type_lower:
        relevance += 15
    
    # Description matching
    if search_lower in desc_lower:
        relevance += 10
    
    # Boost common field types
    common_patterns = {
        'price': ['price', 'listprice', 'saleprice', 'value'],
        'status': ['status', 'listingstatus'],
        'location': ['city', 'state', 'zip', 'county', 'address'],
        'property': ['propertytype', 'type', 'category'],
        'date': ['date', 'timestamp', 'modified', 'created'],
        'bedroom': ['bedroom', 'beds', 'bed'],
        'bathroom': ['bathroom', 'baths', 'bath']
    }
    
    for pattern, keywords in common_patterns.items():
        if pattern in search_lower:
            if any(keyword in field_lower for keyword in keywords):
                relevance += 25
    
    return relevance

class CacheEntry:
    """A cache entry with TTL (Time To Live) support."""
    
    def __init__(self, data: Any, ttl_seconds: int = 3600):
        """
        Initialize a cache entry.
        
        Args:
            data: The data to cache
            ttl_seconds: Time to live in seconds (default: 1 hour)
        """
        self.data = data
        self.created_at = time.time()
        self.ttl_seconds = ttl_seconds
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired."""
        return time.time() - self.created_at > self.ttl_seconds
    
    def get_age_seconds(self) -> float:
        """Get the age of the cache entry in seconds."""
        return time.time() - self.created_at
    
    def get_remaining_ttl_seconds(self) -> float:
        """Get the remaining TTL in seconds."""
        return max(0, self.ttl_seconds - self.get_age_seconds())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary for serialization."""
        return {
            'data': self.data,
            'created_at': self.created_at,
            'ttl_seconds': self.ttl_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CacheEntry':
        """Create cache entry from dictionary."""
        entry = cls(data['data'], data['ttl_seconds'])
        entry.created_at = data['created_at']
        return entry

class TTLCache:
    """A TTL-based cache system with automatic expiration."""
    
    def __init__(self, default_ttl_seconds: int = 3600, max_size: int = 1000):
        """
        Initialize the TTL cache.
        
        Args:
            default_ttl_seconds: Default TTL in seconds (default: 1 hour)
            max_size: Maximum number of cache entries (default: 1000)
        """
        self.cache: Dict[str, CacheEntry] = {}
        self.default_ttl_seconds = default_ttl_seconds
        self.max_size = max_size
        self.access_times: Dict[str, float] = {}  # For LRU eviction
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from cache.
        
        Args:
            key: Cache key
            default: Default value if key not found or expired
            
        Returns:
            Cached value or default
        """
        if key in self.cache:
            entry = self.cache[key]
            if not entry.is_expired():
                # Update access time for LRU
                self.access_times[key] = time.time()
                return entry.data
            else:
                # Remove expired entry
                self._remove_entry(key)
        
        return default
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set a value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: TTL in seconds (uses default if None)
        """
        if ttl_seconds is None:
            ttl_seconds = self.default_ttl_seconds
        
        # Check if we need to evict entries
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        self.cache[key] = CacheEntry(value, ttl_seconds)
        self.access_times[key] = time.time()
    
    def delete(self, key: str) -> bool:
        """
        Delete a key from cache.
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        return self._remove_entry(key)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()
        self.access_times.clear()
    
    def clear_expired(self) -> int:
        """
        Clear all expired entries.
        
        Returns:
            Number of entries cleared
        """
        expired_keys = [
            key for key, entry in self.cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            self._remove_entry(key)
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_entries = len(self.cache)
        expired_entries = sum(1 for entry in self.cache.values() if entry.is_expired())
        valid_entries = total_entries - expired_entries
        
        # Calculate average age and TTL
        ages = [entry.get_age_seconds() for entry in self.cache.values()]
        ttls = [entry.ttl_seconds for entry in self.cache.values()]
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': expired_entries,
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'utilization_percent': (len(self.cache) / self.max_size) * 100 if self.max_size > 0 else 0,
            'avg_age_seconds': sum(ages) / len(ages) if ages else 0,
            'avg_ttl_seconds': sum(ttls) / len(ttls) if ttls else 0
        }
    
    def _remove_entry(self, key: str) -> bool:
        """Remove an entry from cache."""
        if key in self.cache:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
            return True
        return False
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self.access_times:
            return
        
        # Find LRU key
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        self._remove_entry(lru_key)

# Cache configuration constants
CACHE_TTL_CONFIG = {
    'metadata': 3600,        # 1 hour - metadata rarely changes
    'resources': 1800,       # 30 minutes - resources may change occasionally
    'resource_details': 900, # 15 minutes - resource details may change
    'lookup_fields': 7200,   # 2 hours - lookup fields rarely change
    'lookup_values': 3600,   # 1 hour - lookup values may change occasionally
    'query_results': 300,    # 5 minutes - query results change frequently
}

def initialize_ttl_cache():
    """Initialize TTL cache in session state."""
    if 'ttl_cache' not in st.session_state:
        st.session_state.ttl_cache = TTLCache(default_ttl_seconds=3600, max_size=1000)
    
    # Clear expired entries on initialization
    expired_count = st.session_state.ttl_cache.clear_expired()
    if expired_count > 0:
        st.sidebar.info(f"🧹 Cleared {expired_count} expired cache entries")

def get_cached_data(cache_type: str, key: str, fetch_func, ttl_seconds: Optional[int] = None) -> Any:
    """
    Get data from TTL cache or fetch if not cached/expired.
    
    Args:
        cache_type: Type of cache (e.g., 'metadata', 'resources')
        key: Cache key
        fetch_func: Function to call if data not cached
        ttl_seconds: TTL in seconds (uses default from config if None)
        
    Returns:
        Cached or freshly fetched data
    """
    if 'ttl_cache' not in st.session_state:
        initialize_ttl_cache()
    
    cache = st.session_state.ttl_cache
    cache_key = f"{cache_type}:{key}"
    
    # Try to get from cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Fetch fresh data
    try:
        fresh_data = fetch_func()
        if fresh_data is not None:
            # Use configured TTL or provided TTL
            if ttl_seconds is None:
                ttl_seconds = CACHE_TTL_CONFIG.get(cache_type, 3600)
            
            cache.set(cache_key, fresh_data, ttl_seconds)
            return fresh_data
    except Exception as e:
        st.error(f"Error fetching {cache_type} data: {str(e)}")
        return None
    
    return None

def clear_cache_by_type(cache_type: str) -> int:
    """
    Clear all cache entries of a specific type.
    
    Args:
        cache_type: Type of cache to clear
        
    Returns:
        Number of entries cleared
    """
    if 'ttl_cache' not in st.session_state:
        return 0
    
    cache = st.session_state.ttl_cache
    keys_to_remove = [
        key for key in cache.cache.keys()
        if key.startswith(f"{cache_type}:")
    ]
    
    for key in keys_to_remove:
        cache.delete(key)
    
    return len(keys_to_remove)

def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    if 'ttl_cache' not in st.session_state:
        return {'error': 'Cache not initialized'}
    
    return st.session_state.ttl_cache.get_stats()

def render_cache_controls():
    """Render cache control UI in sidebar."""
    if 'ttl_cache' not in st.session_state:
        return
    
    cache = st.session_state.ttl_cache
    
    with st.sidebar.expander("💾 Cache Management", expanded=False):
        # Cache statistics
        stats = cache.get_stats()
        
        st.metric("Total Entries", stats['total_entries'])
        st.metric("Valid Entries", stats['valid_entries'])
        st.metric("Cache Usage", f"{stats['utilization_percent']:.1f}%")
        
        # Cache actions
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Clear Expired", use_container_width=True):
                cleared = cache.clear_expired()
                st.success(f"Cleared {cleared} expired entries")
                st.rerun()
        
        with col2:
            if st.button("Clear All", use_container_width=True):
                cache.clear()
                st.success("Cache cleared")
                st.rerun()
        
        # Clear by type
        st.subheader("Clear by Type")
        
        cache_types = list(CACHE_TTL_CONFIG.keys())
        selected_type = st.selectbox("Select cache type:", cache_types)
        
        if st.button(f"Clear {selected_type}", use_container_width=True):
            cleared = clear_cache_by_type(selected_type)
            st.success(f"Cleared {cleared} {selected_type} entries")
            st.rerun()
        
        # TTL configuration
        st.subheader("TTL Configuration")
        for cache_type, ttl in CACHE_TTL_CONFIG.items():
            new_ttl = st.number_input(
                f"{cache_type} (seconds)",
                value=ttl,
                min_value=60,
                max_value=86400,
                step=300,
                help=f"TTL for {cache_type} cache entries"
            )
            if new_ttl != ttl:
                CACHE_TTL_CONFIG[cache_type] = new_ttl
