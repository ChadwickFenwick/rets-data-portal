import streamlit as st
import json
from datetime import datetime
from clients.rets_client import RETSClient, RESOWebAPIClient
from utils import validate_connection_params, initialize_ttl_cache

def clear_connection_state():
    """Clear all connection-related session state to ensure clean interface refresh."""
    if st.session_state.rets_client:
        st.session_state.rets_client.disconnect()
    st.session_state.connected = False
    st.session_state.rets_client = None
    st.session_state.metadata = None
    st.session_state.resources = []
    st.session_state.query_results = None
    st.session_state.protocol = None
    st.session_state.current_connection_name = None
    st.session_state.auto_connect = False
    
    # Clear all cache data (legacy cache)
    st.session_state.cache_metadata = {}
    st.session_state.cache_resources = {}
    st.session_state.cache_resource_details = {}
    st.session_state.cache_lookup_values = {}
    st.session_state.cache_lookup_fields = {}
    
    # Clear TTL cache
    if 'ttl_cache' in st.session_state:
        st.session_state.ttl_cache.clear()

def initialize_connection_session_state():
    """Initialize all connection-related session state variables."""
    if 'rets_client' not in st.session_state:
        st.session_state.rets_client = None
    if 'connected' not in st.session_state:
        st.session_state.connected = False
    if 'metadata' not in st.session_state:
        st.session_state.metadata = None
    if 'resources' not in st.session_state:
        st.session_state.resources = []
    if 'query_results' not in st.session_state:
        st.session_state.query_results = None
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    if 'saved_connections' not in st.session_state:
        st.session_state.saved_connections = []
    if 'auto_connect' not in st.session_state:
        st.session_state.auto_connect = False
    if 'protocol' not in st.session_state:
        st.session_state.protocol = None
    if 'current_connection_name' not in st.session_state:
        st.session_state.current_connection_name = None
    
    # Form fields initialization
    if 'form_protocol' not in st.session_state:
        st.session_state.form_protocol = "RETS"
    if 'form_auth_method' not in st.session_state:
        st.session_state.form_auth_method = "OAuth2 Flow"
    if 'form_connection_name' not in st.session_state:
        st.session_state.form_connection_name = ""
    if 'form_url' not in st.session_state:
        st.session_state.form_url = ""
    if 'form_username' not in st.session_state:
        st.session_state.form_username = ""
    if 'form_password' not in st.session_state:
        st.session_state.form_password = ""
    if 'form_user_agent' not in st.session_state:
        st.session_state.form_user_agent = "RETS-Dashboard/1.0"
    if 'form_user_agent_password' not in st.session_state:
        st.session_state.form_user_agent_password = ""
    if 'form_rets_version' not in st.session_state:
        st.session_state.form_rets_version = "1.7.2"
    if 'form_token_url' not in st.session_state:
        st.session_state.form_token_url = ""
    if 'form_client_id' not in st.session_state:
        st.session_state.form_client_id = ""
    if 'form_client_secret' not in st.session_state:
        st.session_state.form_client_secret = ""
    if 'form_scope' not in st.session_state:
        st.session_state.form_scope = "odata_api"
    if 'form_access_token' not in st.session_state:
        st.session_state.form_access_token = ""
    if 'form_save_connection' not in st.session_state:
        st.session_state.form_save_connection = True
    if 'form_debug_mode' not in st.session_state:
        st.session_state.form_debug_mode = False
    
    # Initialize cache system (legacy cache for backward compatibility)
    if 'cache_metadata' not in st.session_state:
        st.session_state.cache_metadata = {}
    if 'cache_resources' not in st.session_state:
        st.session_state.cache_resources = {}
    if 'cache_resource_details' not in st.session_state:
        st.session_state.cache_resource_details = {}
    if 'cache_lookup_values' not in st.session_state:
        st.session_state.cache_lookup_values = {}
    if 'cache_lookup_fields' not in st.session_state:
        st.session_state.cache_lookup_fields = {}
    
    # Initialize TTL cache
    initialize_ttl_cache()

def render_saved_connections():
    """Render the saved connections section in the sidebar."""
    if st.session_state.saved_connections:
        connection_names = [f"{conn['name']}" for conn in st.session_state.saved_connections]
        selected_conn = st.selectbox(
            "Saved Connections",
            options=["New Connection"] + connection_names,
            help="Choose a saved connection or create a new one"
        )
        
        # Store the selected connection in session state for use in other functions
        st.session_state.selected_saved_connection = selected_conn
        
        if selected_conn != "New Connection":
            selected_index = connection_names.index(selected_conn)
            saved_conn = st.session_state.saved_connections[selected_index]
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Load", use_container_width=True):
                    st.session_state.auto_connect = True
                    st.rerun()
            with col2:
                if st.button("Delete", use_container_width=True):
                    st.session_state.saved_connections.pop(selected_index)
                    st.rerun()
        
        # Compact Import/Export
        with st.expander("Import/Export"):
            # Export connections
            connections_data = json.dumps(st.session_state.saved_connections, indent=2)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rets_connections_{timestamp}.json"
            
            st.download_button(
                label="Export Connections",
                data=connections_data,
                file_name=filename,
                mime="application/json",
                use_container_width=True
            )
            
            # Import connections
            uploaded_file = st.file_uploader(
                "Import Connections",
                type="json",
                label_visibility="collapsed"
            )
            
            if uploaded_file is not None:
                try:
                    imported_data = json.load(uploaded_file)
                    
                    if isinstance(imported_data, list):
                        # Validate structure
                        valid_connections = []
                        for conn in imported_data:
                            if (isinstance(conn, dict) and 
                                'name' in conn and 'url' in conn and 
                                'protocol' in conn):
                                valid_connections.append(conn)
                        
                        if valid_connections:
                            # Merge with existing connections (avoid duplicates by name)
                            existing_names = {conn['name'] for conn in st.session_state.saved_connections}
                            new_connections = []
                            updated_connections = []
                            
                            for conn in valid_connections:
                                if conn['name'] in existing_names:
                                    # Update existing connection
                                    for i, existing_conn in enumerate(st.session_state.saved_connections):
                                        if existing_conn['name'] == conn['name']:
                                            st.session_state.saved_connections[i] = conn
                                            updated_connections.append(conn['name'])
                                            break
                                else:
                                    # Add new connection
                                    st.session_state.saved_connections.append(conn)
                                    new_connections.append(conn['name'])
                            
                            # Show import results
                            success_msg = []
                            if new_connections:
                                success_msg.append(f"Added {len(new_connections)}")
                            if updated_connections:
                                success_msg.append(f"Updated {len(updated_connections)}")
                            
                            if success_msg:
                                st.success(f"Import successful! {' and '.join(success_msg)}")
                                st.rerun()
                            else:
                                st.info("No new connections to import")
                        else:
                            st.error("No valid connections found")
                    else:
                        st.error("Invalid file format")
                except json.JSONDecodeError:
                    st.error("Invalid JSON file")
                except Exception as e:
                    st.error(f"Import error: {str(e)}")
    else:
        # Import option when no connections exist
        with st.expander("Import Connections"):
            uploaded_file = st.file_uploader(
                "Upload JSON file",
                type="json"
            )
            
            if uploaded_file is not None:
                try:
                    imported_data = json.load(uploaded_file)
                    
                    if isinstance(imported_data, list):
                        # Validate structure
                        valid_connections = []
                        for conn in imported_data:
                            if (isinstance(conn, dict) and 
                                'name' in conn and 'url' in conn and 
                                'protocol' in conn):
                                valid_connections.append(conn)
                        
                        if valid_connections:
                            st.session_state.saved_connections.extend(valid_connections)
                            st.success(f"Imported {len(valid_connections)} connections!")
                            st.rerun()
                        else:
                            st.error("No valid connections found")
                    else:
                        st.error("Invalid file format")
                except json.JSONDecodeError:
                    st.error("Invalid JSON file")
                except Exception as e:
                    st.error(f"Import error: {str(e)}")

def get_connection_defaults():
    """Get default values for connection form based on selected saved connection."""
    default_protocol = "RETS"
    default_url = ""
    default_username = ""
    default_password = ""
    default_name = ""
    default_user_agent = "RETS-Dashboard/1.0"
    default_user_agent_password = ""
    default_rets_version = "1.7.2"
    default_token_url = ""
    default_client_id = ""
    default_client_secret = ""
    default_scope = "odata_api"
    default_auth_method = "OAuth2 Flow"
    default_access_token = ""
    
    if (st.session_state.saved_connections and 
        hasattr(st.session_state, 'selected_saved_connection') and 
        st.session_state.selected_saved_connection != "New Connection"):
        try:
            selected_conn = st.session_state.selected_saved_connection
            connection_names = [f"{conn['name']}" for conn in st.session_state.saved_connections]
            
            if selected_conn != "New Connection":
                selected_index = connection_names.index(selected_conn)
                saved_conn = st.session_state.saved_connections[selected_index]
                default_protocol = saved_conn.get('protocol', 'RETS')
                default_url = saved_conn['url']
                default_username = saved_conn['username']
                default_password = saved_conn['password']
                default_name = saved_conn['name']
                
                # Load protocol-specific defaults
                if default_protocol == "RETS":
                    default_user_agent = saved_conn.get('user_agent', 'RETS-Dashboard/1.0')
                    default_user_agent_password = saved_conn.get('user_agent_password', '')
                    default_rets_version = saved_conn.get('rets_version', '1.7.2')
                    # Reset RESO defaults when RETS is selected
                    default_auth_method = "OAuth2 Flow"
                    default_access_token = ""
                    default_token_url = ""
                    default_client_id = ""
                    default_client_secret = ""
                    default_scope = "odata_api"
                else:  # RESO Web API
                    default_auth_method = saved_conn.get('auth_method', 'OAuth2 Flow')
                    default_access_token = saved_conn.get('access_token', '')
                    default_token_url = saved_conn.get('token_url', '')
                    default_client_id = saved_conn.get('client_id', '')
                    default_client_secret = saved_conn.get('client_secret', '')
                    default_scope = saved_conn.get('scope', 'odata_api')
                    # Reset RETS defaults when RESO is selected
                    default_user_agent = "RETS-Dashboard/1.0"
                    default_user_agent_password = ""
                    default_rets_version = "1.7.2"
        except (ValueError, IndexError):
            pass
    
    return {
        'protocol': default_protocol,
        'url': default_url,
        'username': default_username,
        'password': default_password,
        'name': default_name,
        'user_agent': default_user_agent,
        'user_agent_password': default_user_agent_password,
        'rets_version': default_rets_version,
        'token_url': default_token_url,
        'client_id': default_client_id,
        'client_secret': default_client_secret,
        'scope': default_scope,
        'auth_method': default_auth_method,
        'access_token': default_access_token
    }

def render_connection_form():
    """Render the connection form in the sidebar."""
    defaults = get_connection_defaults()
    
    # Protocol selection (outside form to allow dynamic updates)
    st.subheader("New Connection")
    protocol_index = 0 if defaults['protocol'] == "RETS" else 1
    protocol = st.selectbox(
        "Protocol",
        options=["RETS", "RESO Web API"],
        help="Choose the protocol to connect with",
        index=protocol_index,
        key="form_protocol"
    )
    
    # Authentication method selection for RESO (outside form for dynamic updates)
    auth_method = "OAuth2 Flow"  # Default for RETS
    if protocol == "RESO Web API":
        auth_method = st.radio(
            "Authentication Method",
            options=["OAuth2 Flow", "Direct Access Token"],
            index=0 if defaults['auth_method'] == "OAuth2 Flow" else 1,
            help="Choose how to authenticate with the RESO API",
            key="form_auth_method"
        )
    
    # Connection form
    with st.form("connection_form"):
        
        connection_name = st.text_input(
            "Connection Name",
            value=defaults['name'],
            placeholder="My MLS Server",
            help="Name for saving this connection",
            key="form_connection_name"
        )
        
        if protocol == "RETS":
            server_url = st.text_input(
                "RETS Server URL",
                value=defaults['url'],
                placeholder="https://example.com/rets/login.ashx",
                help="Enter the RETS server URL",
                key="form_url"
            )
        else:  # RESO Web API
            server_url = st.text_input(
                "RESO API Base URL",
                value=defaults['url'],
                placeholder="https://api.example.com/reso/odata",
                help="Enter the RESO Web API base URL",
                key="form_url"
            )
        
        # RESO authentication fields (conditional based on auth method selected inside form)
        if protocol == "RESO Web API":
            if auth_method == "Direct Access Token":
                access_token = st.text_input(
                    "Access Token",
                    value=defaults['access_token'],
                    type="password",
                    placeholder="your_access_token",
                    help="Direct access token for RESO API",
                    key="form_access_token"
                )
                # Set other fields as empty for direct token auth
                token_url = ""
                client_id = ""
                client_secret = ""
                scope = ""
            else:  # OAuth2 Flow
                access_token = ""
                token_url = st.text_input(
                    "OAuth2 Token URL",
                    value=defaults['token_url'],
                    placeholder="https://api.example.com/oauth/token",
                    help="Enter the OAuth2 token endpoint URL",
                    key="form_token_url"
                )
                
                client_id = st.text_input(
                    "Client ID",
                    value=defaults['client_id'],
                    placeholder="your_client_id",
                    help="OAuth2 client ID provided by your MLS",
                    key="form_client_id"
                )
                
                client_secret = st.text_input(
                    "Client Secret",
                    value=defaults['client_secret'],
                    type="password",
                    placeholder="your_client_secret",
                    help="OAuth2 client secret provided by your MLS",
                    key="form_client_secret"
                )
                
                scope = st.text_input(
                    "OAuth2 Scope",
                    value=defaults['scope'],
                    placeholder="odata_api",
                    help="OAuth2 scope for API access",
                    key="form_scope"
                )
        else:
            # For RETS protocol, set all RESO fields as empty
            access_token = ""
            token_url = ""
            client_id = ""
            client_secret = ""
            scope = ""
        
        # Username and password (conditional for RESO)
        if protocol == "RETS" or (protocol == "RESO Web API" and auth_method == "OAuth2 Flow"):
            username = st.text_input(
                "Username",
                value=defaults['username'],
                placeholder="your_username",
                help=f"{protocol} username",
                key="form_username"
            )
            
            password = st.text_input(
                "Password",
                value=defaults['password'],
                type="password",
                placeholder="your_password",
                help=f"{protocol} password",
                key="form_password"
            )
        else:
            # For direct token auth, username/password not needed
            username = ""
            password = ""
        
        # Advanced settings and debug mode in expander
        with st.expander("Advanced Settings"):
            if protocol == "RETS":
                user_agent = st.text_input(
                    "User Agent",
                    value=defaults['user_agent'],
                    placeholder="RETS-Dashboard/1.0",
                    help="User Agent string required by RETS server",
                    key="form_user_agent"
                )
                
                user_agent_password = st.text_input(
                    "User Agent Password",
                    value=defaults['user_agent_password'],
                    type="password",
                    placeholder="Optional User Agent password",
                    help="User Agent password (if required by server)",
                    key="form_user_agent_password"
                )
                
                rets_version_options = ["1.7.2", "1.8", "1.5", "1.0"]
                rets_version_index = rets_version_options.index(defaults['rets_version']) if defaults['rets_version'] in rets_version_options else 0
                rets_version = st.selectbox(
                    "RETS Version",
                    options=rets_version_options,
                    index=rets_version_index,
                    help="RETS protocol version",
                    key="form_rets_version"
                )
            else:
                # For RESO protocol, set RETS fields as defaults
                user_agent = "RETS-Dashboard/1.0"
                user_agent_password = ""
                rets_version = "1.7.2"
            
            debug_mode = st.checkbox(
                "Debug Mode",
                value=False,
                help="Show detailed connection debugging information",
                key="form_debug_mode"
            )
        
        # Connection options and submit button (outside Advanced Settings)
        col1, col2 = st.columns(2)
        with col1:
            save_connection = st.checkbox("Save Connection", value=True, key="form_save_connection")
        with col2:
            if st.form_submit_button("Connect", use_container_width=True):
                st.session_state.form_submitted = True

def test_connection():
    """Test connection without saving."""
    if st.button("🔍 Test Connection", use_container_width=True, help="Test connection without saving"):
        if validate_connection_params(st.session_state.form_url, st.session_state.form_username, st.session_state.form_password):
            with st.spinner("Testing connection..."):
                try:
                    test_client = None
                    if st.session_state.form_protocol == "RETS":
                        test_client = RETSClient(
                            st.session_state.form_url, 
                            st.session_state.form_username, 
                            st.session_state.form_password,
                            st.session_state.form_user_agent,
                            st.session_state.form_user_agent_password,
                            st.session_state.form_rets_version
                        )
                    else:  # RESO Web API
                        auth_method = st.session_state.get('form_auth_method', 'OAuth2 Flow')
                        if auth_method == "Direct Access Token":
                            if not st.session_state.get('form_access_token'):
                                st.error("❌ Please provide an access token")
                                test_client = None
                            else:
                                test_client = RESOWebAPIClient(
                                    st.session_state.form_url,
                                    access_token=st.session_state.form_access_token
                                )
                        else:  # OAuth2 Flow
                            if not st.session_state.get('form_token_url') or not st.session_state.get('form_client_id'):
                                st.error("❌ Please fill in all required OAuth2 fields")
                                test_client = None
                            else:
                                test_client = RESOWebAPIClient(
                                    st.session_state.form_url,
                                    st.session_state.form_token_url,
                                    st.session_state.form_client_id,
                                    st.session_state.form_client_secret,
                                    st.session_state.form_username,
                                    st.session_state.form_password,
                                    st.session_state.form_scope
                                )
                    if test_client:
                        success = test_client.connect()
                    else:
                        success = False
                    if success:
                        st.success(f"✅ Test connection successful! ({st.session_state.form_protocol})")
                        if test_client:
                            test_client.disconnect()
                    else:
                        st.error(f"❌ Test connection failed. Please check your {st.session_state.form_protocol} credentials and URL.")
                        # Show debugging info if enabled
                        if st.session_state.get('form_debug_mode', False):
                            with st.expander("Debug Information"):
                                if st.session_state.form_protocol == "RETS":
                                    st.write("**Tried URLs:**")
                                    if test_client and hasattr(test_client, 'url') and isinstance(test_client, RETSClient) and test_client.url.endswith('.ashx'):
                                        st.write(f"- {test_client.url} (Direct .ashx URL)")
                                    else:
                                        base_url = st.session_state.form_url
                                        for endpoint in ['/login', '/Login', '/RETS/Login', '/rets/login']:
                                            st.write(f"- {base_url}{endpoint}")
                                    st.write("**Headers Used:**")
                                    st.write(f"- User-Agent: {st.session_state.form_user_agent}")
                                    st.write(f"- RETS-Version: {st.session_state.form_rets_version}")
                                    if st.session_state.form_user_agent_password:
                                        st.write("- RETS-UA-Authorization: [Present]")
                                else:  # RESO Web API
                                    auth_method = st.session_state.get('form_auth_method', 'OAuth2 Flow')
                                    st.write(f"**RESO Authentication Method:** {auth_method}")
                                    if auth_method == "Direct Access Token":
                                        st.write("**Token Details:**")
                                        token = st.session_state.get('form_access_token', '')
                                        if token:
                                            st.write(f"- Token Length: {len(token)} characters")
                                            st.write(f"- Token Preview: {token[:20]}...{token[-10:] if len(token) > 30 else ''}")
                                            st.write(f"- Base URL: {st.session_state.form_url}")
                                        else:
                                            st.write("- No access token provided")
                                    else:
                                        st.write("**OAuth2 Details:**")
                                        st.write(f"- Token URL: {st.session_state.get('form_token_url', 'Not set')}")
                                        st.write(f"- Client ID: {st.session_state.get('form_client_id', 'Not set')}")
                                        st.write(f"- Scope: {st.session_state.get('form_scope', 'Not set')}")
                                        st.write("- Grant Type: password")
                                    st.write("**Common RESO Issues:**")
                                    st.write("- **Token Expiration**: Access tokens typically expire in 1 hour or less")
                                    st.write("- **Wrong Base URL**: Ensure URL points to OData endpoint (often ends with /odata)")
                                    st.write("- **Missing Permissions**: Token may not have access to required resources")
                                    st.write("- **API Version**: Some RESO APIs require specific OData version headers")
                                st.write("**Authentication Methods Tried:**")
                                st.write("- Basic Authentication")
                                st.write("- Digest Authentication")
                                st.write("**Suggestions:**")
                                if 'matrix' in st.session_state.form_url.lower():
                                    st.write("- Matrix servers often require specific User Agent strings")
                                    st.write("- Try User Agent: 'Matrix/1.0' or contact your MLS for the exact string")
                                    st.write("- **IMPORTANT**: Matrix servers typically require a User Agent Password")
                                    st.write("- Contact Canopy MLS support for your User Agent Password")
                                    st.write("- Verify your IP address is whitelisted with Canopy MLS")
                                    st.write("- Some Matrix servers use custom authentication beyond standard methods")
                except Exception as e:
                    st.error(f"❌ Test connection error: {str(e)}")
        else:
            st.error("❌ Please fill in all required fields for testing.")

def handle_connection():
    """Handle the actual connection process."""
    if st.session_state.get('form_submitted', False) or st.session_state.auto_connect:
        # Get values from session state since form variables are not in scope here
        protocol = st.session_state.get('form_protocol', 'RETS')
        auth_method = st.session_state.get('form_auth_method', 'OAuth2 Flow')
        
        # Validate connection parameters based on protocol and auth method
        valid_params = False
        if protocol == "RETS":
            valid_params = validate_connection_params(st.session_state.form_url, st.session_state.form_username, st.session_state.form_password)
        else:  # RESO Web API
            if auth_method == "Direct Access Token":
                valid_params = bool(st.session_state.form_url and st.session_state.form_access_token)
            else:  # OAuth2 Flow
                valid_params = validate_connection_params(st.session_state.form_url, st.session_state.form_username, st.session_state.form_password)
        
        if valid_params:
            # Clear previous connection state to ensure clean refresh
            clear_connection_state()
            
            with st.spinner(f"Connecting to {protocol} server..."):
                try:
                    if protocol == "RETS":
                        client = RETSClient(
                            st.session_state.form_url, 
                            st.session_state.form_username, 
                            st.session_state.form_password,
                            st.session_state.form_user_agent,
                            st.session_state.form_user_agent_password,
                            st.session_state.form_rets_version
                        )
                    else:  # RESO Web API
                        if auth_method == "Direct Access Token":
                            if not st.session_state.form_access_token:
                                st.error("❌ Please provide an access token")
                                client = None
                            else:
                                client = RESOWebAPIClient(st.session_state.form_url, access_token=st.session_state.form_access_token)
                        else:  # OAuth2 Flow
                            if not st.session_state.form_token_url or not st.session_state.form_client_id:
                                st.error("❌ Please fill in all required OAuth2 fields")
                                client = None
                            else:
                                client = RESOWebAPIClient(
                                    st.session_state.form_url,
                                    st.session_state.form_token_url,
                                    st.session_state.form_client_id,
                                    st.session_state.form_client_secret,
                                    st.session_state.form_username,
                                    st.session_state.form_password,
                                    st.session_state.form_scope
                                )
                    
                    if client:
                        success = client.connect()
                        
                        if success:
                            st.session_state.rets_client = client  # Store client regardless of protocol
                            st.session_state.connected = True
                            st.session_state.protocol = protocol  # Store which protocol is being used
                            st.session_state.current_connection_name = st.session_state.get('form_connection_name', '')  # Store connection name for title
                            st.success(f"✅ Connected successfully to {protocol} server!")
                            
                            # Save connection if requested
                            if st.session_state.get('form_save_connection', True) and st.session_state.get('form_connection_name'):
                                # Check if connection already exists
                                existing_conn = next((conn for conn in st.session_state.saved_connections if conn['name'] == st.session_state.form_connection_name), None)
                                
                                new_connection = {
                                    'name': st.session_state.form_connection_name,
                                    'protocol': protocol,
                                    'url': st.session_state.form_url,
                                    'username': st.session_state.form_username,
                                    'password': st.session_state.form_password
                                }
                                
                                if protocol == "RETS":
                                    new_connection.update({
                                        'user_agent': st.session_state.form_user_agent,
                                        'user_agent_password': st.session_state.form_user_agent_password,
                                        'rets_version': st.session_state.form_rets_version
                                    })
                                else:  # RESO Web API
                                    new_connection['auth_method'] = auth_method
                                    if auth_method == "Direct Access Token":
                                        new_connection['access_token'] = st.session_state.form_access_token
                                    else:  # OAuth2 Flow
                                        new_connection.update({
                                            'token_url': st.session_state.form_token_url,
                                            'client_id': st.session_state.form_client_id,
                                            'client_secret': st.session_state.form_client_secret,
                                            'scope': st.session_state.form_scope
                                        })
                                
                                if existing_conn:
                                    # Update existing connection
                                    existing_index = st.session_state.saved_connections.index(existing_conn)
                                    st.session_state.saved_connections[existing_index] = new_connection
                                    st.info(f"✅ Updated saved connection: {st.session_state.form_connection_name} ({protocol})")
                                else:
                                    # Add new connection
                                    st.session_state.saved_connections.append(new_connection)
                                    st.info(f"✅ Saved connection: {st.session_state.form_connection_name} ({protocol})")
                        
                        # Load metadata (will be cached)
                        with st.spinner("Loading metadata..."):
                            try:
                                # Initialize cache with initial data
                                st.session_state.cache_metadata = client.get_metadata()
                                st.session_state.cache_resources = client.get_resources()
                                
                                st.session_state.metadata = st.session_state.cache_metadata
                                st.session_state.resources = st.session_state.cache_resources
                            except Exception as e:
                                st.warning(f"⚠️ Connected but failed to load metadata: {str(e)}")
                                st.session_state.metadata = None
                                st.session_state.resources = []
                                st.session_state.cache_metadata = {}
                                st.session_state.cache_resources = {}
                            
                        st.session_state.auto_connect = False
                        st.session_state.form_submitted = False
                        st.rerun()
                    else:
                        st.error("❌ Connection failed. Please check your credentials.")
                        st.session_state.auto_connect = False
                        st.session_state.form_submitted = False
                
                except Exception as e:
                    st.error(f"❌ Connection error: {str(e)}")
                    st.session_state.auto_connect = False
                    st.session_state.form_submitted = False
        else:
            st.error("❌ Please fill in all required connection fields.")
            st.session_state.auto_connect = False
            st.session_state.form_submitted = False

def render_connection_status():
    """Render connection status and disconnect button."""
    if st.session_state.connected:
        protocol = st.session_state.get('protocol', 'RETS')
        connection_name = st.session_state.get('current_connection_name', '')
        
        # Connection status and disconnect button
        status_col1, status_col2 = st.columns([3, 1])
        
        with status_col1:
            footer_status = f"🟢 Connected ({protocol})"
            if connection_name:
                footer_status += f" - {connection_name}"
            st.markdown(f"**{footer_status}**")
        
        with status_col2:
            if st.button("🔴 Disconnect", use_container_width=True, type="secondary"):
                clear_connection_state()
                st.success("Disconnected successfully!")
                st.rerun()
    else:
        st.markdown("**🔴 Not Connected**")

def render_connection_sidebar():
    """Render the complete connection sidebar."""
    with st.sidebar:
        st.header("Connection Manager")
        
        # Saved connections section
        render_saved_connections()
        
        st.markdown("---")
        
        # Connection form
        render_connection_form()
        
        # Test connection button
        test_connection()
        
        # Handle connection
        handle_connection() 