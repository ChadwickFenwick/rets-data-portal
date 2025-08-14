# RETs Dashboard

## Overview

The RETs Dashboard is a Streamlit-based web application designed to interact with Real Estate Transaction Standard (RETS) servers. The application provides a user-friendly interface for connecting to RETS servers, browsing metadata, executing queries, and downloading real estate data. It's built using Python with Streamlit as the frontend framework, making it accessible through a web browser.

## System Architecture

The application follows a simple three-tier architecture:

1. **Presentation Layer**: Streamlit web interface (`app.py`)
2. **Business Logic Layer**: RETS client and utility functions (`rets_client.py`, `utils.py`)
3. **Data Layer**: Direct connection to external RETS servers (no local database)

### Architecture Decisions

- **Streamlit Framework**: Chosen for rapid development of data-driven web applications with minimal frontend code
- **Session-based State Management**: Uses Streamlit's session state to maintain connection status and query history across user interactions
- **Direct HTTP Communication**: Implements direct HTTP requests to RETS servers without intermediate caching layers for real-time data access
- **Stateless Design**: No persistent local storage, all data is fetched on-demand from RETS servers

## Key Components

### 1. Main Application (`app.py`)
- **Purpose**: Primary Streamlit application entry point
- **Responsibilities**:
  - User interface rendering
  - Session state management
  - Connection form handling
  - Query result display
  - Download functionality

### 2. RETS Client (`rets_client.py`)
- **Purpose**: Handles communication with RETS servers
- **Responsibilities**:
  - Authentication and session management
  - Metadata retrieval
  - Query execution
  - XML response parsing
  - Error handling for RETS-specific protocols

### 3. Utility Functions (`utils.py`)
- **Purpose**: Supporting functions for data processing and validation
- **Responsibilities**:
  - Connection parameter validation
  - Metadata formatting for display
  - Data transformation utilities
  - URL parsing and validation

## Data Flow

1. **Connection Establishment**:
   - User enters RETS server credentials via sidebar form
   - Credentials are validated using `validate_connection_params()`
   - `RETSClient` establishes authenticated session with RETS server
   - Connection status stored in session state

2. **Metadata Retrieval**:
   - Upon successful connection, client fetches available resources
   - Metadata is parsed and formatted for display
   - Resource information cached in session state

3. **Query Execution**:
   - User selects resources and constructs queries
   - Queries sent to RETS server via authenticated session
   - Results parsed from XML/CSV response formats
   - Data presented in tabular format with download options

4. **Data Export**:
   - Query results converted to pandas DataFrames
   - Export functionality provides CSV/Excel download options
   - Download links generated dynamically

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for the user interface
- **pandas**: Data manipulation and analysis
- **requests**: HTTP library for RETS server communication
- **xml.etree.ElementTree**: XML parsing for RETS responses

### RETS Protocol
- **Authentication**: HTTP Basic Authentication
- **Data Formats**: XML metadata, CSV/XML query results
- **Version Support**: RETS 1.7.2 protocol compliance

## Deployment Strategy

### Current Setup
- **Platform**: Designed for Replit deployment
- **Runtime**: Python 3.x environment
- **Dependencies**: Managed via pip/requirements.txt
- **Port Configuration**: Streamlit default port (8501)

### Scalability Considerations
- **Session Management**: Currently single-user focused
- **Performance**: Direct server queries without caching
- **Security**: Basic authentication passed through to RETS servers

### Future Enhancements
- Multi-user session isolation
- Query result caching
- Database integration for query history
- Enhanced error handling and logging

## Changelog
- July 07, 2025. Initial setup
- July 07, 2025. Added save login feature with persistent connection storage
- July 07, 2025. Enhanced connection handling with multiple RETs endpoint support
- July 07, 2025. Added test connection functionality and troubleshooting guide

## Recent Changes

### RESO Web API Support Added (July 08, 2025)
- Added comprehensive RESO Web API client with OAuth2 authentication
- Dual protocol support: Both RETS and RESO Web API in single dashboard
- Protocol selection dropdown in connection form
- OAuth2 password grant flow implementation with scope support
- Conditional form fields based on selected protocol
- Enhanced test connection functionality for both protocols
- Added requests-oauthlib dependency for OAuth2 support
- Updated connection form with RESO-specific fields (token URL, client ID/secret)
- **BREAKTHROUGH**: Successfully connected to Spark API RESO endpoint
- Fixed 415 "Unsupported Media Type" error by accepting XML format for metadata
- Enhanced debug output and troubleshooting for RESO connections
- Dual authentication methods: Direct Access Token and OAuth2 Flow working
- **MAJOR UPDATE**: Implemented unified interface for both RETS and RESO protocols
- RESO metadata parsing from OData XML schema with EntitySets, EntityTypes, and EnumTypes
- RESO Resources Browser showing properties, types, and entity details similar to RETS format
- RESO Field Values system extracting enum-based lookup values from metadata
- RESO Query Builder with OData $filter syntax and comprehensive examples
- Protocol-aware formatting throughout all tabs maintaining similar layouts for both systems

### Field Values Enhancement & Metadata Downloads (July 08, 2025)
- **COMPLETED**: Fixed RESO Field Values functionality to properly display lookup values
- Enhanced RESO lookup values method to handle Collection(Edm.String) field types via data sampling
- Fixed protocol detection issue preventing RETS Field Values from displaying correctly
- Added comprehensive metadata download functionality for both protocols
- RESO metadata downloads as complete OData XML schema with all definitions
- RETS metadata downloads as structured JSON with all parsed resources and fields
- Download buttons available in Metadata tab with timestamp naming
- Removed debug output for clean production interface
- **SUCCESS**: Both RETS and RESO Field Values now working perfectly with proper protocol detection

### Session State Management Enhancement (July 08, 2025)
- **RESOLVED**: Fixed interface refresh issue when switching between RETS and RESO connections
- Added comprehensive session state clearing function to ensure clean interface refresh
- Enhanced disconnect functionality to properly clear all connection-related data
- Improved connection process to clear previous state before establishing new connections
- Protocol detection now properly refreshes when switching between connection types
- **SOLUTION**: Dashboard now properly reloads when disconnecting or connecting to different feeds

### Connection Import/Export Feature (July 08, 2025)
- **NEW FEATURE**: Added ability to export saved connections as JSON files for sharing
- **NEW FEATURE**: Added ability to import connections from JSON files shared by teammates
- Export functionality generates timestamped JSON files with all connection details
- Import functionality validates JSON structure and merges with existing connections
- Smart duplicate handling: updates existing connections with same name, adds new ones
- Import/export available in sidebar for easy access and workflow integration
- **USE CASE**: Perfect for sharing MLS connection configurations with work teammates

### Fixed Footer Status Bar (July 08, 2025)
- **COMPLETED**: Fixed footer positioning to avoid sidebar overlap
- Status bar now positioned on right side of screen to remain always visible
- Resource count now shows accurate live count from client instead of cached value
- Disconnect button properly positioned within footer area for easy access
- Footer shows protocol type, connection name, and current resource count
- **UI IMPROVEMENT**: Clean, professional footer design with proper spacing and styling

### Matrix RETS Data Parsing Success (July 07, 2025)
- Successfully implemented Matrix RETS tab-delimited data parsing
- Fixed DATA element parsing to handle 347-column responses
- Added flexible field matching for variable column counts
- Query execution now returns actual property data from 2.4M+ records
- Streamlined Query Builder to DMQL-only interface per user request
- Removed unnecessary sample query dropdowns and form complexity
- Enhanced debugging and error handling for Matrix RETS responses

### Save Login Feature
- Added connection name field for organizing saved connections
- Passwords are stored in browser session for convenience (not public app)
- Load/delete saved connections from dropdown menu
- Auto-connect functionality for saved connections

### Enhanced Connection Handling
- Multiple RETs endpoint support (/login, /Login, /RETS/Login, /rets/login, .ashx)
- User Agent and User Agent Password support for Matrix servers
- RETs version selection (1.7.2, 1.8, 1.5, 1.0)
- Better error handling and timeout management
- Test connection feature for verification without saving
- Improved connection status display with details
- Debug mode for connection troubleshooting

### Matrix Server Support
- Special handling for Matrix-based RETs servers (.ashx endpoints)
- Matrix-specific troubleshooting guide
- User Agent requirements documentation
- IP whitelisting guidance

### Comprehensive Metadata System
- Enhanced metadata loading to fetch SYSTEM, RESOURCE, CLASS, and TABLE metadata
- Comprehensive Resources Browser with hierarchical exploration
- Field-level metadata with data types, lengths, and requirements
- Searchable metadata with CSV export functionality

### Streamlined Query Builder
- DMQL-focused query interface for advanced users
- Smart resource and class selection from actual metadata
- Direct DMQL text input without unnecessary dropdowns
- Real-time query execution with comprehensive Matrix RETS parsing
- Successfully parses Matrix RETS tab-delimited DATA elements
- Flexible field matching to handle variable column counts
- Results display with filtering and CSV export capabilities
- Query history tracking and management
- Simplified interface per user preference for DMQL-only functionality

### Field Values & Lookup System
- Added comprehensive Field Values tab for exploring field constraints
- Dynamic field selection based on resource/class metadata
- Lookup value retrieval from RETS server metadata
- Proper XML parsing for Matrix RETS lookup responses
- Field information display with data types and constraints
- Search and filter capabilities for lookup values
- CSV export functionality for field values
- Integration with query builder for valid field value selection

### User Interface Improvements
- Advanced settings expandable section with User Agent fields
- Connection troubleshooting guide with common issues
- Sample connection examples for major MLS providers
- Query examples and DMQL syntax help
- Connection details expandable section showing server info
- Debug mode with detailed connection attempt information
- Five-tab interface: Metadata, Resources, Query Builder, Field Values, Export

## User Preferences

Preferred communication style: Simple, everyday language.
User requested save login feature including password storage for convenience.
User prefers DMQL-only query interface without additional query types or sample dropdowns.
Focus on direct, functional interface without unnecessary complexity.