# RETS Dashboard - Modular Edition

A comprehensive Streamlit-based dashboard for querying real estate data via RETS and RESO Web API protocols, built with a modular architecture for maintainability and extensibility.

## 🏗️ Architecture

The application is organized into logical modules for better maintainability:

```
RetsDataPortal/
├── app_new.py              # Main application entry point
├── connection.py           # Connection management and forms
├── query_builder.py        # Query builder interface and execution
├── history.py             # Query history and export/import
├── visualization.py       # Data visualization and analytics
├── utils.py               # Shared utilities and helpers
├── clients/               # Client implementations
│   ├── __init__.py
│   └── rets_client.py     # RETS and RESO client classes
├── pyproject.toml         # Project dependencies
└── README.md             # This file
```

## 🚀 Features

### 🔌 Connection Management
- **Multi-Protocol Support**: Connect to both RETS and RESO Web API servers
- **Authentication Methods**: OAuth2 Flow and Direct Access Token for RESO
- **Connection Persistence**: Save and load connection configurations
- **Import/Export**: Share connection settings between users
- **Test Connections**: Verify credentials before saving

### 📊 Metadata Explorer
- **Comprehensive Metadata**: Browse all available resources, classes, and fields
- **Search Functionality**: Find specific metadata elements quickly
- **Export Capabilities**: Download metadata in JSON/XML format
- **Protocol-Specific Views**: Optimized displays for RETS vs RESO

### 🔍 Query Builder
- **Text-Based Editor**: Write queries in native DMQL (RETS) or OData (RESO)
- **Query History**: Save and re-enter previous queries
- **Export/Import**: Share query configurations
- **Real-time Validation**: Validate queries before execution
- **Results Display**: View query results in interactive tables

### 📈 Data Visualization
- **Interactive Charts**: Price distributions, property types, bedrooms/bathrooms
- **Geographic Mapping**: Scatter plots for location data
- **Time Series Analysis**: Date-based trend analysis
- **Export Options**: Download visualizations and data

### 🔎 Field Values & Lookups
- **Lookup Discovery**: Find fields with predefined values
- **Value Browsing**: Explore available lookup values
- **Search Functionality**: Filter lookup values
- **Export Capabilities**: Download lookup tables

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd RetsDataPortal
   ```

2. **Install dependencies**:
   ```bash
   pip install streamlit pandas
   ```

3. **Run the application**:
   ```bash
   streamlit run app_new.py
   ```

## 📖 Usage

### Getting Started

1. **Connect to a Server**:
   - Use the sidebar to enter your RETS or RESO server credentials
   - Choose the appropriate protocol (RETS or RESO Web API)
   - Test your connection before saving

2. **Browse Metadata**:
   - Explore available resources and classes
   - Search for specific fields or metadata elements
   - Export metadata for offline reference

3. **Build Queries**:
   - Select a resource and class (RETS) or resource (RESO)
   - Write your query using the appropriate syntax
   - Execute and view results

4. **Analyze Data**:
   - Use the visualization tools to understand your data
   - Export results in various formats
   - Save queries for future use

### Query Syntax

#### RETS (DMQL)
```dmql
(Status=Active),(ListPrice=100000+)
(PropertyType=Residential),(BedroomsTotal=3+)
(City=Austin),(ListPrice=200000-500000)
```

#### RESO (OData)
```odata
StandardStatus eq 'Active' and ListPrice gt 100000
PropertyType eq 'Residential' and BedroomsTotal ge 3
City eq 'Austin' and ListPrice ge 200000 and ListPrice le 500000
```

## 🔧 Configuration

### Environment Variables
- No environment variables required - all configuration is done through the UI

### Connection Settings
- **RETS**: URL, username, password, user agent, RETS version
- **RESO**: Base URL, authentication method, credentials/token

## 🏗️ Development

### Module Structure

#### `connection.py`
- Connection form rendering
- Session state management
- Connection validation and handling
- Saved connections management

#### `query_builder.py`
- Query editor interfaces
- Query execution logic
- Results handling
- Protocol-specific query building

#### `history.py`
- Query history management
- Export/import functionality
- Re-enter query logic

#### `visualization.py`
- Data visualization components
- Chart generation
- Export functionality

#### `utils.py`
- Shared utility functions
- Data formatting helpers
- Validation functions

#### `clients/rets_client.py`
- RETS client implementation
- RESO Web API client implementation
- Protocol-specific connection handling

### Adding New Features

1. **Create a new module** for the feature
2. **Import and integrate** in `app_new.py`
3. **Update this README** with new functionality

### Testing

- Test connections with various RETS/RESO servers
- Validate query syntax and execution
- Verify export/import functionality
- Check visualization accuracy

## 🐛 Troubleshooting

### Common Issues

1. **Connection Failures**:
   - Verify URL format and credentials
   - Check User Agent requirements
   - Ensure IP whitelisting if required

2. **Query Errors**:
   - Validate query syntax
   - Check field names in metadata
   - Verify resource/class selection

3. **Performance Issues**:
   - Limit query results
   - Use specific field selection
   - Clear query history if needed

### Debug Mode

Enable debug mode in Advanced Settings to see detailed connection information and troubleshooting tips.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review the help documentation in the app
- Open an issue on GitHub

---

**Built with ❤️ for the real estate data community** 