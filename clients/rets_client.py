import requests
from requests.auth import HTTPDigestAuth
from requests_oauthlib import OAuth2Session
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET
import pandas as pd
from urllib.parse import urljoin, urlparse
import re
import json

class RESOWebAPIClient:
    """
    A client for connecting to and interacting with RESO Web API servers using OAuth2.
    """
    
    def __init__(self, base_url: str, token_url: str = "", client_id: str = "", client_secret: str = "", 
                 username: str = "", password: str = "", scope: str = "odata_api", access_token: str = ""):
        """
        Initialize the RESO Web API client.
        
        Args:
            base_url: RESO API base URL (e.g., https://api.example.com/reso/odata)
            token_url: OAuth2 token endpoint URL (for OAuth2 flow)
            client_id: OAuth2 client ID (for OAuth2 flow)
            client_secret: OAuth2 client secret (for OAuth2 flow)
            username: Username for authentication (for password grant)
            password: Password for authentication (for password grant)
            scope: OAuth2 scope for API access
            access_token: Direct access token (if already obtained)
        """
        self.base_url = base_url.rstrip('/')
        self.token_url = token_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.scope = scope
        self.access_token = access_token  # Can be provided directly
        self.connected = False
        self.metadata = {}
        self.auth_method = "token" if access_token else "oauth2"
        
    def connect(self) -> bool:
        """
        Connect to the RESO Web API server using either direct token or OAuth2 flow.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            if self.auth_method == "token" and self.access_token:
                # Direct token authentication
                print("Using direct access token for RESO Web API authentication...")
                # Test the token by making a simple API call
                test_response = self._make_api_request('')
                if test_response is not None:
                    print("RESO Web API direct token authentication successful")
                    self.connected = True
                    return True
                else:
                    print("Direct access token appears to be invalid or expired")
                    return False
            else:
                # OAuth2 flow authentication
                print("Attempting RESO Web API OAuth2 authentication...")
                
                if not self.token_url or not self.client_id:
                    print("Missing required OAuth2 parameters (token_url, client_id)")
                    return False
                
                # Request access token using password grant
                data = {
                    'grant_type': 'password',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'username': self.username,
                    'password': self.password,
                    'scope': self.scope
                }
                
                headers = {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
                
                response = requests.post(self.token_url, data=data, headers=headers)
                print(f"Token request status: {response.status_code}")
                
                if response.status_code == 200:
                    token_data = response.json()
                    self.access_token = token_data.get('access_token')
                    if self.access_token:
                        print("RESO Web API OAuth2 authentication successful")
                        self.connected = True
                        return True
                    else:
                        print("No access token received")
                        return False
                else:
                    print(f"Token request failed: {response.status_code} - {response.text}")
                    return False
                
        except Exception as e:
            print(f"RESO Web API connection error: {str(e)}")
            return False
    
    def _make_api_request(self, endpoint: str, params: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
        """
        Make authenticated API request to RESO endpoint.
        
        Args:
            endpoint: API endpoint (e.g., 'Property', '$metadata')
            params: OData query parameters
            
        Returns:
            Response JSON data or None if error
        """
        if not self.access_token:
            print("No access token available")
            return None
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/json',
            'OData-Version': '4.0'
        }
        
        # Clean up URL formatting
        base_clean = self.base_url.rstrip('/')
        endpoint_clean = endpoint.lstrip('/')
        url = f"{base_clean}/{endpoint_clean}" if endpoint_clean else base_clean
        
        print(f"Making RESO API request to: {url}")
        print(f"Authorization header: Bearer {self.access_token[:10]}...{self.access_token[-10:] if len(self.access_token) > 20 else self.access_token}")
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            print(f"API request to {endpoint}: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                print(f"Content type: {content_type}")
                
                if 'application/json' in content_type:
                    return response.json()
                else:
                    # Return text content for metadata endpoints
                    return {'content': response.text}
            elif response.status_code == 401:
                print(f"Access token expired or invalid. Response body: {response.text}")
                print("Suggestions:")
                print("1. Check if the access token is still valid")
                print("2. Verify the token has proper permissions")
                print("3. Try generating a new access token")
                return None
            elif response.status_code == 403:
                print(f"Access forbidden. Response body: {response.text}")
                print("Suggestions:")
                print("1. Check if your token has permission to access this endpoint")
                print("2. Verify your account has access to the RESO API")
                return None
            elif response.status_code == 404:
                print(f"Endpoint not found. Response body: {response.text}")
                print(f"Attempted URL: {url}")
                print("Suggestions:")
                print("1. Verify the base URL is correct")
                print("2. Check if the API supports OData endpoints")
                return None
            else:
                print(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"API request error: {str(e)}")
            return None
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve OData metadata from the RESO server.
        
        Returns:
            Dict containing metadata information
        """
        # For metadata requests, we need to use a different approach
        # The 415 error suggests we need to accept XML format for metadata
        if not self.access_token:
            print("No access token available")
            return None
            
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Accept': 'application/xml, text/xml, */*',  # Accept XML for metadata
            'OData-Version': '4.0'
        }
        
        url = f"{self.base_url.rstrip('/')}/$metadata"
        
        try:
            print(f"Making RESO metadata request to: {url}")
            response = requests.get(url, headers=headers, timeout=30)
            print(f"Metadata request: {response.status_code}")
            
            if response.status_code == 200:
                # Parse metadata and get available resources
                resources_response = self._make_api_request('')
                if resources_response:
                    # Extract available resources from the service document
                    resources = []
                    if 'value' in resources_response:
                        for item in resources_response['value']:
                            if 'name' in item:
                                resources.append(item['name'])
                    
                    self.metadata = {
                        'resources': resources,
                        'metadata_content': response.text,
                        'service_document': resources_response
                    }
                    return self.metadata
                else:
                    print("Failed to get service document")
                    return None
            else:
                print(f"Metadata request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Metadata request error: {str(e)}")
            return None
    
    def get_resources(self) -> List[str]:
        """
        Get list of available resources.
        
        Returns:
            List of resource names
        """
        if not self.metadata:
            self.get_metadata()
        return self.metadata.get('resources', [])
    
    def get_resource_details(self, resource_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific RESO resource.
        
        Args:
            resource_name: Name of the resource
            
        Returns:
            Dict containing resource details
        """
        # For RESO, we get resource details from the metadata XML
        if not self.metadata or 'metadata_content' not in self.metadata:
            return {}
        
        # Parse XML metadata to extract resource information
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(self.metadata['metadata_content'])
            
            # Look for EntitySet with the given name
            for entity_set in root.iter():
                if entity_set.tag.endswith('EntitySet') and entity_set.get('Name') == resource_name:
                    entity_type = entity_set.get('EntityType', '')
                    
                    # Find the corresponding EntityType
                    for entity_type_elem in root.iter():
                        if entity_type_elem.tag.endswith('EntityType') and entity_type_elem.get('Name') == entity_type.split('.')[-1]:
                            properties = []
                            for prop in entity_type_elem.iter():
                                if prop.tag.endswith('Property'):
                                    prop_info = {
                                        'name': prop.get('Name', ''),
                                        'type': prop.get('Type', ''),
                                        'nullable': prop.get('Nullable', 'true'),
                                        'max_length': prop.get('MaxLength', ''),
                                    }
                                    properties.append(prop_info)
                            
                            return {
                                'resource_name': resource_name,
                                'entity_type': entity_type,
                                'properties': properties,
                                'property_count': len(properties)
                            }
        except Exception as e:
            print(f"Error parsing RESO metadata for resource {resource_name}: {e}")
        
        return {'resource_name': resource_name, 'properties': [], 'property_count': 0}
    
    def get_all_lookup_fields(self, resource: str, class_name: str = None) -> List[str]:
        """
        Get list of fields that have lookup values for RESO resources.
        
        Args:
            resource: Resource name
            class_name: Not used in RESO (for compatibility with RETS interface)
            
        Returns:
            List of field names with lookup values
        """
        # For RESO, lookup fields are typically enum types in the metadata
        if not self.metadata or 'metadata_content' not in self.metadata:
            print(f"No metadata available for lookup fields in {resource}")
            return []
        
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(self.metadata['metadata_content'])
            lookup_fields = []
            
            # Find the EntityType for this resource
            entity_type_name = None
            for entity_set in root.iter():
                if entity_set.tag.endswith('EntitySet') and entity_set.get('Name') == resource:
                    entity_type_full = entity_set.get('EntityType', '')
                    entity_type_name = entity_type_full.split('.')[-1]
                    break
            
            if not entity_type_name:
                return []
            
            # Find properties with enum types
            for entity_type_elem in root.iter():
                if entity_type_elem.tag.endswith('EntityType') and entity_type_elem.get('Name') == entity_type_name:
                    for prop in entity_type_elem.iter():
                        if prop.tag.endswith('Property'):
                            prop_name = prop.get('Name', 'Unknown')
                            prop_type = prop.get('Type', '')
                            
                            # Check if it's an enum type (typically contains namespace)
                            if '.' in prop_type and not prop_type.startswith('Edm.'):
                                lookup_fields.append(prop_name)
                    break
            return lookup_fields
            
        except Exception as e:
            return []
    
    def get_lookup_values(self, resource: str, field_name: str) -> Optional[Dict[str, Any]]:
        """
        Get lookup values for a specific RESO field.
        
        Args:
            resource: Resource name
            field_name: Field name to get lookup values for
            
        Returns:
            Dict containing lookup values
        """
        # For RESO, we need to extract enum values from metadata
        if not self.metadata or 'metadata_content' not in self.metadata:
            return None
        
        import xml.etree.ElementTree as ET
        try:
            root = ET.fromstring(self.metadata['metadata_content'])
            
            # First, find the property type
            property_type = None
            entity_type_name = None
            
            for entity_set in root.iter():
                if entity_set.tag.endswith('EntitySet') and entity_set.get('Name') == resource:
                    entity_type_full = entity_set.get('EntityType', '')
                    entity_type_name = entity_type_full.split('.')[-1]
                    
                    for entity_type_elem in root.iter():
                        if entity_type_elem.tag.endswith('EntityType') and entity_type_elem.get('Name') == entity_type_name:
                            for prop in entity_type_elem.iter():
                                if prop.tag.endswith('Property') and prop.get('Name') == field_name:
                                    property_type = prop.get('Type', '')
                                    break
                            break
                    break
            
            if not property_type:
                return None
            
            # Handle different property type patterns
            lookup_values = {}
            
            # Pattern 1: Collection(Edm.String) - these are standard RESO lookup fields
            if property_type == 'Collection(Edm.String)':
                # For Collection(Edm.String) fields, RESO typically defines the valid values
                # in the RESO Data Dictionary. Since we can't access that dynamically,
                # we'll query the actual data to get sample values
                try:
                    # Query for unique values of this field
                    sample_data = self.execute_query(
                        resource=resource,
                        odata_filter="",
                        select=field_name,
                        limit=1000
                    )
                    
                    if sample_data:
                        unique_values = set()
                        for record in sample_data:
                            field_value = record.get(field_name)
                            if field_value:
                                if isinstance(field_value, list):
                                    # Handle array values
                                    for val in field_value:
                                        if val and val.strip():
                                            unique_values.add(val.strip())
                                elif isinstance(field_value, str) and field_value.strip():
                                    unique_values.add(field_value.strip())
                        
                        # Convert to lookup format
                        for value in sorted(unique_values):
                            lookup_values[value] = value
                        
                except Exception as e:
                    pass  # Ignore errors during data sampling
            
            # Pattern 2: Direct enum type reference
            elif '.' in property_type and not property_type.startswith('Edm.'):
                enum_type_name = property_type.split('.')[-1]
                
                for enum_type in root.iter():
                    if enum_type.tag.endswith('EnumType') and enum_type.get('Name') == enum_type_name:
                        for member in enum_type.iter():
                            if member.tag.endswith('Member'):
                                name = member.get('Name', '')
                                value = member.get('Value', name)
                                if name:
                                    lookup_values[value] = name
                        break
            
            if lookup_values:
                return {
                    'field_name': field_name,
                    'lookup_type': property_type,
                    'values': lookup_values,
                    'count': len(lookup_values)
                }
            else:
                return None
                
        except Exception as e:
            return None
    
    def execute_query(self, resource: str, odata_filter: str = "", 
                     limit: int = 100, select: str = "", skip: int = 0) -> Optional[List[Dict[str, Any]]]:
        """
        Execute an OData query against the RESO server.
        
        Args:
            resource: Resource name (e.g., 'Property', 'Member')
            odata_filter: OData $filter expression
            limit: Maximum number of results ($top)
            select: Comma-separated list of fields to select
            skip: Number of records to skip ($skip)
            
        Returns:
            List of dictionaries containing query results
        """
        params = {}
        
        if odata_filter:
            params['$filter'] = odata_filter
        if select:
            params['$select'] = select
        if limit:
            params['$top'] = str(limit)
        if skip:
            params['$skip'] = str(skip)
        
        print(f"Executing RESO query on {resource} with params: {params}")
        
        response = self._make_api_request(resource, params)
        if response and 'value' in response:
            results = response['value']
            print(f"RESO query returned {len(results)} results")
            return results
        
        return []
    
    def disconnect(self):
        """
        Disconnect from the RESO server.
        """
        self.access_token = None
        self.connected = False
        print("RESO Web API disconnected")

class RETSClient:
    """
    A client for connecting to and interacting with RETs servers.
    """
    
    def __init__(self, url: str, username: str, password: str, user_agent: str = "RETS-Dashboard/1.0", 
                 user_agent_password: str = "", rets_version: str = "1.7.2"):
        """
        Initialize the RETs client.
        
        Args:
            url: RETs server URL
            username: Username for authentication
            password: Password for authentication
            user_agent: User Agent string for RETs server
            user_agent_password: User Agent password (if required)
            rets_version: RETs protocol version
        """
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.user_agent = user_agent
        self.user_agent_password = user_agent_password
        self.rets_version = rets_version
        self.session = None
        self.login_url = None
        self.metadata_url = None
        self.search_url = None
        self.connected = False
        
    def connect(self) -> bool:
        """
        Connect to the RETs server and authenticate.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Create session
            self.session = requests.Session()
            
            # Set required headers
            headers = {
                'User-Agent': self.user_agent,
                'RETS-Version': self.rets_version,
                'Accept': 'text/xml, application/xml, text/plain, */*'
            }
            
            # Add User Agent password if provided (Matrix servers often require this)
            if self.user_agent_password:
                # For Matrix servers, the format might just be the password itself
                headers['RETS-UA-Authorization'] = self.user_agent_password
            
            self.session.headers.update(headers)
            
            # Try both Basic and Digest authentication
            auth_methods = [
                ('Basic', (self.username, self.password)),
                ('Digest', HTTPDigestAuth(self.username, self.password))
            ]
            
            for auth_name, auth_method in auth_methods:
                print(f"Trying {auth_name} authentication...")
                self.session.auth = auth_method
                
                success = False
                
                # For Matrix servers, try the base URL first as it might be the login endpoint
                if 'matrix' in self.url.lower():
                    try:
                        login_response = self.session.get(self.url, timeout=30)
                        print(f"Matrix base URL response status: {login_response.status_code}")
                        
                        if login_response.status_code == 200:
                            print(f"Login successful with {auth_name} auth for {self.url}")
                            self._parse_login_response(login_response.text)
                            self.connected = True
                            return True
                        elif login_response.status_code == 401:
                            print(f"{auth_name} authentication failed for base URL: {self.url}")
                    except requests.exceptions.RequestException as e:
                        print(f"Request error for base URL {self.url}: {str(e)}")
                
                # Try multiple common RETs endpoints
                login_endpoints = ['/login', '/Login', '/RETS/Login', '/rets/login', '/Login.ashx', '/login.ashx']
                
                for endpoint in login_endpoints:
                    try:
                        login_url = self.url + endpoint
                        
                        # For .ashx endpoints, don't append additional paths
                        if self.url.endswith('.ashx'):
                            login_url = self.url
                            if endpoint != login_endpoints[0]:  # Skip other endpoints for .ashx
                                break
                        
                        print(f"Trying login URL: {login_url} with {auth_name}")
                        login_response = self.session.get(login_url, timeout=30)
                        
                        print(f"Response status: {login_response.status_code}")
                        
                        if login_response.status_code == 200:
                            print(f"Login successful with {auth_name} auth for {login_url}")
                            # Parse login response to get URLs
                            self._parse_login_response(login_response.text)
                            self.connected = True
                            return True
                        elif login_response.status_code == 401:
                            # Authentication failed
                            print(f"{auth_name} authentication failed for {login_url}")
                            if self.url.endswith('.ashx'):
                                break  # Don't try other endpoints for .ashx URLs
                            continue
                        else:
                            print(f"Login failed with status {login_response.status_code} for {login_url}")
                            if self.url.endswith('.ashx'):
                                break  # Don't try other endpoints for .ashx URLs
                            continue
                            
                    except requests.exceptions.RequestException as e:
                        print(f"Request error for {login_url}: {str(e)}")
                        if self.url.endswith('.ashx'):
                            break  # Don't try other endpoints for .ashx URLs
                        continue
                
                # For .ashx URLs, break after trying both auth methods on the same URL
                if self.url.endswith('.ashx'):
                    continue  # Try next auth method instead of breaking
            
            return False
                
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return False
    
    def _parse_login_response(self, response_text: str):
        """
        Parse the login response to extract service URLs.
        
        Args:
            response_text: Raw login response text
        """
        print(f"Parsing login response (first 500 chars): {response_text[:500]}...")
        
        try:
            # Parse XML response
            root = ET.fromstring(response_text)
            
            # Extract service URLs - look for standard RETS response format
            for elem in root.iter():
                tag_lower = elem.tag.lower()
                if 'metadata' in tag_lower or elem.get('Action') == 'GetMetadata':
                    if elem.text:
                        self.metadata_url = elem.text
                        print(f"Found metadata URL: {self.metadata_url}")
                elif 'search' in tag_lower or elem.get('Action') == 'Search':
                    if elem.text:
                        self.search_url = elem.text
                        print(f"Found search URL: {self.search_url}")
                elif 'getmetadata' in tag_lower:
                    if elem.text:
                        self.metadata_url = elem.text
                        print(f"Found GetMetadata URL: {self.metadata_url}")
                    
        except ET.ParseError as e:
            print(f"XML parsing failed: {e}")
            # If not XML, try to extract URLs from text - Matrix servers often use this format
            lines = response_text.split('\n')
            for line in lines:
                line_stripped = line.strip()
                if line_stripped.startswith('GetMetadata='):
                    self.metadata_url = line_stripped.replace('GetMetadata=', '')
                    print(f"Found GetMetadata URL: {self.metadata_url}")
                elif line_stripped.startswith('Search='):
                    self.search_url = line_stripped.replace('Search=', '')
                    print(f"Found Search URL: {self.search_url}")
                elif 'getmetadata' in line.lower():
                    # Extract URL from line
                    url_match = re.search(r'https?://[^\s<>"\']+', line)
                    if url_match:
                        self.metadata_url = url_match.group()
                        print(f"Found metadata URL in text: {self.metadata_url}")
                elif 'search=' in line.lower():
                    url_match = re.search(r'https?://[^\s<>"\']+', line)
                    if url_match:
                        self.search_url = url_match.group()
                        print(f"Found search URL in text: {self.search_url}")
        
        # Only use fallback URLs if we didn't find them in the response
        if not self.metadata_url:
            # For Matrix servers, construct standard URLs if not found
            base_url = self.url.replace('/login.ashx', '').replace('/rets/login.ashx', '')
            
            # Try common Matrix metadata endpoints
            possible_metadata = [
                f"{base_url}/rets/GetMetadata.ashx",
                f"{base_url}/GetMetadata.ashx", 
                f"{self.url.replace('login.ashx', 'GetMetadata.ashx')}",
                f"{base_url}/metadata"
            ]
            self.metadata_url = possible_metadata[0]  # Use the most common one
            print(f"Using fallback metadata URL: {self.metadata_url}")
            
        if not self.search_url:
            # For Matrix servers, construct standard URLs if not found
            base_url = self.url.replace('/login.ashx', '').replace('/rets/login.ashx', '')
            
            # Try common Matrix search endpoints
            possible_search = [
                f"{base_url}/rets/Search.ashx",
                f"{base_url}/Search.ashx",
                f"{self.url.replace('login.ashx', 'Search.ashx')}",
                f"{base_url}/search"
            ]
            self.search_url = possible_search[0]  # Use the most common one
            print(f"Using fallback search URL: {self.search_url}")
            
        print(f"Final URLs - Metadata: {self.metadata_url}, Search: {self.search_url}")
    
    def get_metadata(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve comprehensive metadata from the RETs server.
        
        Returns:
            Dict containing metadata information
        """
        if not self.connected or not self.session:
            print("Not connected or no session available")
            return None
            
        try:
            metadata_result = {}
            
            # 1. Get system metadata first
            print(f"Requesting system metadata from: {self.metadata_url}")
            params = {
                'Type': 'METADATA-SYSTEM',
                'ID': '*'
            }
            
            response = self.session.get(self.metadata_url, params=params, timeout=30)
            print(f"System metadata response status: {response.status_code}")
            
            if response.status_code == 200:
                system_metadata = self._parse_metadata_response(response.text)
                metadata_result['SYSTEM'] = system_metadata
                
                # 2. Get resource metadata
                print("Requesting resource metadata...")
                resource_params = {
                    'Type': 'METADATA-RESOURCE',
                    'ID': '0'
                }
                
                resource_response = self.session.get(self.metadata_url, params=resource_params, timeout=30)
                print(f"Resource metadata response status: {resource_response.status_code}")
                
                if resource_response.status_code == 200:
                    resource_metadata = self._parse_metadata_response(resource_response.text)
                    metadata_result['RESOURCE'] = resource_metadata
                    
                    # 3. Get class metadata for each resource
                    if resource_metadata and 'resources' in resource_metadata:
                        for resource in resource_metadata['resources']:
                            resource_name = resource.get('ResourceID', '')
                            if resource_name:
                                print(f"Requesting class metadata for resource: {resource_name}")
                                class_params = {
                                    'Type': 'METADATA-CLASS',
                                    'ID': resource_name
                                }
                                
                                class_response = self.session.get(self.metadata_url, params=class_params, timeout=30)
                                print(f"Class metadata for {resource_name} response status: {class_response.status_code}")
                                
                                if class_response.status_code == 200:
                                    class_metadata = self._parse_metadata_response(class_response.text)
                                    metadata_result[f'CLASS_{resource_name}'] = class_metadata
                                    
                                    # 4. Get table metadata (fields) for each class
                                    if class_metadata and 'classes' in class_metadata:
                                        for class_info in class_metadata['classes']:
                                            class_name = class_info.get('ClassName', '')
                                            if class_name:
                                                print(f"Requesting table metadata for {resource_name}:{class_name}")
                                                table_params = {
                                                    'Type': 'METADATA-TABLE',
                                                    'ID': f'{resource_name}:{class_name}'
                                                }
                                                
                                                table_response = self.session.get(self.metadata_url, params=table_params, timeout=30)
                                                print(f"Table metadata for {resource_name}:{class_name} response status: {table_response.status_code}")
                                                
                                                if table_response.status_code == 200:
                                                    table_metadata = self._parse_metadata_response(table_response.text)
                                                    metadata_result[f'TABLE_{resource_name}_{class_name}'] = table_metadata
                
                return metadata_result
            else:
                print(f"System metadata request failed with status: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Metadata retrieval error: {str(e)}")
            return None
    
    def _parse_metadata_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse metadata response.
        
        Args:
            response_text: Raw metadata response text
            
        Returns:
            Dict containing parsed metadata
        """
        metadata = {
            'system': {},
            'resources': [],
            'classes': [],
            'fields': []
        }
        
        try:
            # Try to parse as XML
            root = ET.fromstring(response_text)
            
            # Extract all elements with attributes (common RETS pattern)
            for elem in root.iter():
                tag_lower = elem.tag.lower()
                
                # Extract system information
                if 'system' in tag_lower:
                    if elem.attrib:
                        metadata['system'].update(elem.attrib)
                    for child in elem:
                        if child.attrib:
                            metadata['system'][child.tag] = child.attrib
                        elif child.text:
                            metadata['system'][child.tag] = child.text
                
                # Extract resources - check both child elements and attributes
                elif 'resource' in tag_lower:
                    if elem.attrib:
                        resource_info = dict(elem.attrib)
                        metadata['resources'].append(resource_info)
                    else:
                        resource_info = {}
                        for child in elem:
                            if child.attrib:
                                resource_info.update(child.attrib)
                            elif child.text:
                                resource_info[child.tag] = child.text
                        if resource_info:
                            metadata['resources'].append(resource_info)
                
                # Extract classes
                elif 'class' in tag_lower:
                    if elem.attrib:
                        class_info = dict(elem.attrib)
                        metadata['classes'].append(class_info)
                    else:
                        class_info = {}
                        for child in elem:
                            if child.attrib:
                                class_info.update(child.attrib)
                            elif child.text:
                                class_info[child.tag] = child.text
                        if class_info:
                            metadata['classes'].append(class_info)
                
                # Extract fields/tables
                elif any(field_tag in tag_lower for field_tag in ['field', 'table', 'column']):
                    if elem.attrib:
                        field_info = dict(elem.attrib)
                        metadata['fields'].append(field_info)
                    else:
                        field_info = {}
                        for child in elem:
                            if child.attrib:
                                field_info.update(child.attrib)
                            elif child.text:
                                field_info[child.tag] = child.text
                        if field_info:
                            metadata['fields'].append(field_info)
                        
        except ET.ParseError:
            # If not XML, create basic structure
            metadata = {
                'system': {'raw_response': response_text[:500]},
                'resources': [],
                'classes': [],
                'fields': []
            }
        
        return metadata
    
    def get_resources(self) -> List[str]:
        """
        Get list of available resources.
        
        Returns:
            List of resource names
        """
        metadata = self.get_metadata()
        if not metadata:
            return []
        
        resources = []
        
        # Extract resource names from metadata
        if 'resources' in metadata:
            for resource in metadata['resources']:
                if isinstance(resource, dict):
                    name = resource.get('name') or resource.get('ResourceID') or resource.get('resource_name')
                    if name:
                        resources.append(name)
                elif isinstance(resource, str):
                    resources.append(resource)
        
        # If no resources found, provide common defaults
        if not resources:
            resources = ['Property', 'Agent', 'Office', 'Media', 'Tour']
        
        return resources
    
    def get_resource_details(self, resource_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific resource.
        
        Args:
            resource_name: Name of the resource
            
        Returns:
            Dict containing resource details
        """
        metadata = self.get_metadata()
        if not metadata:
            return {}
        
        details = {
            'classes': [],
            'fields': []
        }
        
        # Extract classes for this resource
        for class_info in metadata.get('classes', []):
            if isinstance(class_info, dict):
                if class_info.get('resource') == resource_name:
                    details['classes'].append(class_info)
        
        # Extract fields for this resource
        for field_info in metadata.get('fields', []):
            if isinstance(field_info, dict):
                if field_info.get('resource') == resource_name:
                    details['fields'].append(field_info)
        
        # If no specific details found, provide basic structure
        if not details['classes'] and not details['fields']:
            details = {
                'classes': [{'name': resource_name, 'description': f'{resource_name} class'}],
                'fields': [
                    {'name': 'ID', 'type': 'Character', 'description': 'Unique identifier'},
                    {'name': 'Status', 'type': 'Character', 'description': 'Status field'},
                    {'name': 'ModificationTimestamp', 'type': 'DateTime', 'description': 'Last modified'}
                ]
            }
        
        return details
    
    def execute_query(self, resource: str, class_name: str, query: str = "", 
                     limit: int = 100, select: str = "") -> Optional[List[Dict[str, Any]]]:
        """
        Execute a query against the RETs server.
        
        Args:
            resource: Resource name
            class_name: Class name
            query: DMQL query string
            limit: Maximum number of results
            select: Comma-separated list of fields to select
            
        Returns:
            List of dictionaries containing query results
        """
        if not self.connected or not self.session:
            print("Not connected or no session available for query")
            return None
            
        try:
            # Build query parameters for Matrix RETS
            params = {
                'SearchType': resource,
                'Class': class_name,
                'Query': query.strip() if query and query.strip() else '(ListingId=*)',  # Default query that should work with most RETS servers
                'QueryType': 'DMQL2',
                'Count': '1',  # Include count
                'Format': 'COMPACT-DECODED',
                'Limit': str(limit)
            }
            
            if select:
                params['Select'] = select
            
            print(f"Executing search query:")
            print(f"URL: {self.search_url}")
            print(f"Params: {params}")
            
            # Execute search
            response = self.session.get(self.search_url, params=params, timeout=30)
            
            print(f"Search response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response content length: {len(response.text)}")
            print(f"First 500 chars of response: {response.text[:500]}")
            
            if response.status_code == 200:
                results = self._parse_search_response(response.text)
                print(f"Parsed {len(results) if results else 0} results from response")
                return results
            else:
                print(f"Search failed with status {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            print(f"Query execution error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _parse_search_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse search response and return results.
        
        Args:
            response_text: Raw search response text
            
        Returns:
            List of dictionaries containing search results
        """
        results = []
        
        try:
            print("Attempting to parse search response as XML...")
            # Try to parse as XML
            root = ET.fromstring(response_text)
            
            print(f"Root element: {root.tag}")
            print(f"Root attributes: {root.attrib}")
            
            # Check for Matrix RETS tab-delimited format
            columns_elem = root.find('.//COLUMNS')
            delimiter_elem = root.find('.//DELIMITER')
            
            if columns_elem is not None and columns_elem.text:
                print("Found Matrix RETS tab-delimited format")
                
                # Get delimiter (usually tab = ASCII 09)
                delimiter = '\t'  # default
                if delimiter_elem is not None and 'value' in delimiter_elem.attrib:
                    delim_value = delimiter_elem.attrib['value']
                    if delim_value == '09':
                        delimiter = '\t'
                    elif delim_value == '2C':
                        delimiter = ','
                    else:
                        delimiter = chr(int(delim_value))
                
                # Parse column headers
                headers = columns_elem.text.strip().split(delimiter)
                print(f"Found {len(headers)} columns: {headers[:5]}...")  # Show first 5
                
                # Find and parse data rows - look for DATA elements with text content
                data_elements = root.findall('.//DATA')
                print(f"Found {len(data_elements)} DATA elements in Matrix format")
                
                for i, data_elem in enumerate(data_elements):
                    # Debug: check what's actually in DATA elements
                    if i < 3:  # Log first 3 DATA elements
                        print(f"DATA element {i}: text='{data_elem.text[:100] if data_elem.text else None}', attrib={data_elem.attrib}")
                    
                    # Try text content first
                    if data_elem.text:
                        data_text = data_elem.text  # Don't strip - tabs are important
                        values = data_text.split(delimiter)
                        
                        print(f"DATA element {i}: {len(values)} values vs {len(headers)} headers")
                        
                        # Handle column alignment - Matrix RETS often has mismatched columns
                        if len(values) > len(headers):
                            # More values than headers - likely extra columns at start/end
                            # Try different alignment strategies
                            
                            # Strategy 1: Skip first column if it's empty (common issue)
                            if values[0] == '' or values[0].strip() == '':
                                values = values[1:]  # Remove first empty column
                            
                            # Strategy 2: Truncate to header count if still too many
                            if len(values) > len(headers):
                                values = values[:len(headers)]
                                
                        row_data = {}
                        for j, header in enumerate(headers):
                            if j < len(values):
                                value = values[j].strip() if values[j] else ""
                                row_data[header] = value if value else None
                            else:
                                row_data[header] = None
                        results.append(row_data)
                        
                        if len(results) == 1:
                            print(f"After alignment - values: {len(values)}, headers: {len(headers)}")
                            print(f"First row sample: {[(k, v) for k, v in list(row_data.items())[:5]]}")
                            
                            if len(results) >= 25:  # Get 25 records for testing
                                print(f"Parsed {len(results)} rows, stopping for performance")
                                break
                    
                    # Try attributes if no text content
                    elif data_elem.attrib:
                        # DATA element might have attributes instead of text
                        row_data = dict(data_elem.attrib)
                        if row_data:
                            results.append(row_data)
                            if len(results) == 1:
                                print(f"First row from attributes: {list(row_data.keys())[:5]}...")
                            
                            if len(results) >= 50:
                                break
                
                # If no DATA elements with content, try a more detailed approach
                if not results:
                    print("No data in DATA elements, examining raw response...")
                    
                    # Log a sample of the response to see the structure
                    response_lines = response_text.split('\n')
                    print(f"Response has {len(response_lines)} lines")
                    
                    # Look for lines that might contain data
                    for i, line in enumerate(response_lines):
                        line = line.strip()
                        
                        # Skip empty lines
                        if not line:
                            continue
                            
                        # Check if this is a data line (has right number of tabs)
                        if delimiter in line:
                            tab_count = line.count(delimiter)
                            # Expected tab count is headers-1
                            if tab_count == len(headers) - 1:
                                print(f"Found potential data line {i}: {line[:100]}...")
                                values = line.split(delimiter)
                                
                                if len(values) == len(headers):
                                    row_data = {}
                                    for j, header in enumerate(headers):
                                        if j < len(values):
                                            value = values[j].strip()
                                            row_data[header] = value if value else None
                                    results.append(row_data)
                                    
                                    if len(results) == 1:
                                        print(f"First parsed row: {[(k, v) for k, v in list(row_data.items())[:3]]}")
                                    
                                    if len(results) >= 50:
                                        print(f"Parsed {len(results)} rows from raw text")
                                        break
                
                print(f"Parsed {len(results)} data rows from Matrix RETS format")
                if results:
                    return results
            
            # Look for RETS-DATA or DATA elements
            data_elements = root.findall('.//DATA') or root.findall('.//RETS-DATA') or root.findall('.//data')
            
            if data_elements:
                print(f"Found {len(data_elements)} DATA elements")
                for data_elem in data_elements:
                    row_data = {}
                    # Get data from attributes or text
                    if data_elem.attrib:
                        row_data.update(data_elem.attrib)
                    
                    # Also check child elements
                    for child in data_elem:
                        if child.text and child.text.strip():
                            row_data[child.tag] = child.text.strip()
                        elif child.attrib:
                            row_data.update(child.attrib)
                    
                    if row_data:
                        results.append(row_data)
                        print(f"Added row with {len(row_data)} fields")
            else:
                # Look for any elements that might contain data
                print("No DATA elements found, searching for other data containers...")
                for elem in root.iter():
                    if elem.attrib and len(elem.attrib) > 2:  # Has multiple attributes (likely data)
                        row_data = dict(elem.attrib)
                        if any(key.lower() in ['listingid', 'mlsnumber', 'status', 'listprice'] for key in row_data.keys()):
                            results.append(row_data)
                            print(f"Found data in {elem.tag} element with {len(row_data)} fields")
                        
        except ET.ParseError as e:
            print(f"XML parsing failed: {e}")
            # If not XML, try to parse as delimited text (tab or comma)
            lines = response_text.strip().split('\n')
            if len(lines) > 1:
                print(f"Trying to parse as delimited text with {len(lines)} lines")
                
                # Try tab-delimited first
                headers = lines[0].split('\t')
                if len(headers) == 1:
                    # Try comma-delimited
                    headers = lines[0].split(',')
                
                print(f"Found {len(headers)} headers: {headers[:5]}...")  # Show first 5 headers
                
                for i, line in enumerate(lines[1:]):
                    if line.strip():
                        values = line.split('\t') if '\t' in line else line.split(',')
                        if len(values) == len(headers):
                            row_data = dict(zip(headers, values))
                            results.append(row_data)
                            if i < 3:  # Log first few rows
                                print(f"Row {i+1}: {len(row_data)} fields")
        
        print(f"Final parsed results count: {len(results)}")
        if results and len(results) > 0:
            print(f"Sample result keys: {list(results[0].keys())[:10]}")  # Show first 10 keys
        
        return results
    
    def get_lookup_values(self, resource: str, field_name: str) -> Optional[Dict[str, Any]]:
        """
        Get lookup values for a specific field.
        
        Args:
            resource: Resource name
            field_name: Field name to get lookup values for
            
        Returns:
            Dict containing lookup values
        """
        if not self.connected or not self.session:
            print("Not connected or no session available for lookup")
            return None
            
        try:
            print(f"Requesting lookup values for {resource}:{field_name}")
            
            # First, try to get the lookup name from field metadata
            lookup_name = self._get_lookup_name_for_field(resource, field_name)
            if not lookup_name:
                print(f"No lookup name found for field {field_name}")
                # Try using the field name as lookup name
                lookup_name = field_name
            
            print(f"Using lookup name: {lookup_name}")
            
            # Try multiple lookup metadata request formats
            lookup_attempts = [
                # Standard RETS lookup format
                {'Type': 'METADATA-LOOKUP_TYPE', 'ID': f"{resource}:{lookup_name}"},
                # Alternative format with lookup name
                {'Type': 'METADATA-LOOKUP_TYPE', 'ID': lookup_name},
                # Matrix specific format
                {'Type': 'METADATA-LOOKUP', 'ID': f"{resource}:{lookup_name}"},
                {'Type': 'METADATA-LOOKUP', 'ID': lookup_name},
                # Try with original field name
                {'Type': 'METADATA-LOOKUP_TYPE', 'ID': f"{resource}:{field_name}"},
                {'Type': 'METADATA-LOOKUP', 'ID': f"{resource}:{field_name}"}
            ]
            
            for attempt_params in lookup_attempts:
                try:
                    print(f"Trying lookup with params: {attempt_params}")
                    response = self.session.get(self.metadata_url, params=attempt_params, timeout=30)
                    print(f"Lookup response status: {response.status_code}")
                    print(f"Response content preview: {response.text[:500]}")
                    
                    if response.status_code == 200:
                        result = self._parse_lookup_response(response.text, field_name)
                        if result and result.get('values'):
                            print(f"Successfully found {len(result['values'])} lookup values")
                            return result
                        else:
                            print("Response parsed but no values found")
                    
                except Exception as e:
                    print(f"Lookup attempt failed: {str(e)}")
                    continue
            
            print("All lookup attempts failed")
            return None
                
        except Exception as e:
            print(f"Lookup request error: {str(e)}")
            return None
    
    def _parse_lookup_response(self, response_text: str, field_name: str) -> Dict[str, Any]:
        """
        Parse lookup response and return lookup values.
        
        Args:
            response_text: Raw lookup response text
            field_name: Field name for context
            
        Returns:
            Dict containing lookup values
        """
        lookup_values = {}
        
        try:
            print("Parsing lookup response as XML...")
            root = ET.fromstring(response_text)
            print(f"Root element: {root.tag}")
            print(f"Root attributes: {root.attrib}")
            
            # Check for RETS reply code first
            reply_code = root.attrib.get('ReplyCode', '0')
            if reply_code != '0':
                print(f"RETS error code {reply_code}: {root.attrib.get('ReplyText', 'Unknown error')}")
                return {
                    'field_name': field_name,
                    'values': {},
                    'count': 0,
                    'error': root.attrib.get('ReplyText', 'Unknown error')
                }
            
            # Try multiple patterns for lookup values
            # First try looking for LookupType elements with child text elements
            lookup_type_elements = root.findall('.//LookupType')
            print(f"Found {len(lookup_type_elements)} LookupType elements")
            
            for lookup_elem in lookup_type_elements:
                print(f"LookupType element children: {[child.tag for child in lookup_elem]}")
                
                # Extract value and names from child elements
                value = None
                long_value = None
                short_value = None
                
                for child in lookup_elem:
                    print(f"Child element {child.tag}: {child.text}")
                    if child.tag == 'Value':
                        value = child.text
                    elif child.tag == 'LongValue':
                        long_value = child.text
                    elif child.tag == 'ShortValue':
                        short_value = child.text
                
                if value:
                    display_name = long_value or short_value or value
                    lookup_values[value] = display_name
                    print(f"Added lookup: {value} = {display_name}")
            
            # If no LookupType elements found, try attribute-based patterns
            if not lookup_values:
                patterns_to_try = [
                    # Standard RETS patterns
                    ('.//LOOKUP_TYPE', ['Value', 'LookupValue'], ['LongValue', 'ShortValue', 'LookupName']),
                    ('.//LOOKUP', ['Value', 'LookupValue'], ['LongValue', 'ShortValue', 'LookupName']),
                    # Matrix specific patterns
                    ('.//DATA', ['Value', 'LookupValue'], ['LongValue', 'ShortValue', 'LookupName']),
                    # Generic element patterns
                    ('.//*[@Value]', ['Value'], ['LongValue', 'ShortValue', 'LookupName']),
                    ('.//*[@LookupValue]', ['LookupValue'], ['LongValue', 'ShortValue', 'LookupName'])
                ]
                
                for xpath, value_attrs, name_attrs in patterns_to_try:
                    elements = root.findall(xpath)
                    print(f"Found {len(elements)} elements with pattern {xpath}")
                    
                    for elem in elements:
                        print(f"Element {elem.tag} attributes: {elem.attrib}")
                        
                        # Get the value
                        value = None
                        for attr in value_attrs:
                            if attr in elem.attrib:
                                value = elem.attrib[attr]
                                break
                        
                        if not value:
                            continue
                        
                        # Get the display name
                        name = value  # Default to value
                        for attr in name_attrs:
                            if attr in elem.attrib and elem.attrib[attr]:
                                name = elem.attrib[attr]
                                break
                        
                        lookup_values[value] = name
                        print(f"Added lookup: {value} = {name}")
                    
                    if lookup_values:
                        break  # Stop if we found values
            
            # If still no values, try to parse any elements with useful attributes
            if not lookup_values:
                print("Trying to parse all elements with attributes...")
                for elem in root.iter():
                    if elem.attrib:
                        print(f"Element {elem.tag}: {elem.attrib}")
                        # Look for any pattern that might be lookup values
                        possible_values = []
                        possible_names = []
                        
                        for key, val in elem.attrib.items():
                            if any(keyword in key.lower() for keyword in ['value', 'code', 'id']):
                                possible_values.append(val)
                            elif any(keyword in key.lower() for keyword in ['name', 'long', 'short', 'desc']):
                                possible_names.append(val)
                        
                        if possible_values:
                            value = possible_values[0]
                            name = possible_names[0] if possible_names else value
                            lookup_values[value] = name
                            
            print(f"Found {len(lookup_values)} lookup values for {field_name}")
            
        except ET.ParseError as e:
            print(f"Failed to parse lookup response as XML: {str(e)}")
            print(f"Response content: {response_text[:1000]}")
            
        return {
            'field_name': field_name,
            'values': lookup_values,
            'count': len(lookup_values)
        }
    
    def _get_lookup_name_for_field(self, resource: str, field_name: str) -> Optional[str]:
        """
        Get the lookup name for a specific field from metadata.
        
        Args:
            resource: Resource name
            field_name: Field name
            
        Returns:
            Lookup name if found, None otherwise
        """
        metadata = self.get_metadata()
        if not metadata:
            return None
            
        # Look for the field in table metadata
        for metadata_type, metadata_content in metadata.items():
            if metadata_type.startswith('TABLE_') and resource in metadata_type:
                if isinstance(metadata_content, dict) and 'fields' in metadata_content:
                    for field in metadata_content['fields']:
                        if isinstance(field, dict):
                            field_system_name = field.get('SystemName', '')
                            field_standard_name = field.get('StandardName', '')
                            
                            if field_system_name == field_name or field_standard_name == field_name:
                                lookup_name = field.get('LookupName', '')
                                if lookup_name:
                                    return lookup_name
        
        return None
    
    def get_all_lookup_fields(self, resource: str, class_name: str) -> List[str]:
        """
        Get list of fields that have lookup values.
        
        Args:
            resource: Resource name
            class_name: Class name
            
        Returns:
            List of field names with lookup values
        """
        lookup_fields = []
        
        # Get table metadata to find lookup fields
        metadata = self.get_metadata()
        if not metadata:
            return lookup_fields
            
        # Look for fields with lookup types in the comprehensive metadata
        table_key = f"TABLE_{resource}_{class_name}"
        if table_key in metadata:
            table_metadata = metadata[table_key]
            if isinstance(table_metadata, dict) and 'fields' in table_metadata:
                for field in table_metadata['fields']:
                    if isinstance(field, dict):
                        # Check if field has lookup information
                        lookup_name = field.get('LookupName', '')
                        interpretation = field.get('Interpretation', '')
                        data_type = field.get('DataType', '')
                        
                        if lookup_name or 'lookup' in interpretation.lower() or data_type == 'Character':
                            field_name = field.get('SystemName', field.get('StandardName', ''))
                            if field_name:
                                lookup_fields.append(field_name)
        
        print(f"Found {len(lookup_fields)} fields with potential lookup values")
        return lookup_fields
    
    def disconnect(self):
        """
        Disconnect from the RETs server.
        """
        if self.session:
            try:
                # Attempt logout
                self.session.get(self.url + '/logout')
            except:
                pass
            finally:
                self.session.close()
                self.session = None
                self.connected = False
