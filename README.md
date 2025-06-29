# GA4 MCP Server 

A modular, maintainable Google Analytics 4 MCP (Model Context Protocol) server built following Clean Code principles.

## 🏃‍♂️ Getting Started

### Prerequisits 
To be able to use your own instance of this MCP server you need to create your own Google Credentials and obtain the Client ID and Client Secret. 
Steps to create [Google Cloud Client Credientials](https://developers.google.com/workspace/guides/create-credentials#oauth-client-id)

Once you have obtained the Client ID and Client Seceret, add them to the .env.example file then change the name to .env

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GA4_CLIENT_ID="your_client_id"
export GA4_CLIENT_SECRET="your_client_secret"

# Run the server
fastmcp run app.py:mcp
```

### Install MCP to Claude Desktop
```bash
fastmcp install app.py:mcp
```

## 🏗️ Architecture Overview

The application has been completely refactored from a single 734-line file into a modular architecture:

```
backend/
├── src/                           # Main application code
│   ├── auth/                      # Authentication modules
│   │   ├── oauth_manager.py       # OAuth flow management
│   │   └── credentials_manager.py # Credential storage/retrieval
│   ├── analytics/                 # GA4 data processing
│   │   ├── ga4_client.py         # GA4 API client wrapper
│   │   ├── report_builder.py     # Request building logic
│   │   └── data_formatter.py     # Response formatting
│   ├── config/                   # Configuration management
│   │   ├── settings.py           # Environment variable handling
│   │   └── constants.py          # Application constants
│   ├── utils/                    # Utility modules
│   │   ├── errors.py             # Custom exception classes
│   │   ├── logging.py            # Logging configuration
│   │   └── validation.py         # Input validation
│   ├── server.py                 # FastMCP server setup
│   └── main.py                   # Application entry point
├── tests/                        # Organized test suite
│   ├── conftest.py              # Shared test fixtures
│   ├── test_auth/               # Authentication tests
│   ├── test_analytics/          # Analytics tests
│   └── test_integration/        # End-to-end tests
├── app_refactored.py            # Backward compatibility wrapper
└── requirements.txt
```

## 🚀 Key Features

### Authentication Management
```python
# OAuth flow management
oauth_manager = OAuthManager(settings, credentials_manager)
auth_url = oauth_manager.start_oauth_flow()
credentials = oauth_manager.complete_oauth_flow(auth_code)

# Credential persistence
credentials_manager = CredentialsManager()
credentials_manager.save_credentials(creds)
loaded_creds = credentials_manager.load_credentials()
```

### Analytics Data Retrieval
```python
# GA4 client with validation
ga4_client = GA4Client(credentials)
report = ga4_client.get_standard_report(
    property_id="123456789",
    start_date="7daysAgo",
    end_date="today",
    metrics="sessions,users",
    dimensions="date"
)
```

### Configuration Management
```python
# Centralized settings
settings = Settings()
client_config = settings.get_oauth_client_config()
debug_info = settings.get_debug_info()
```

## 🧪 Testing Structure

### Organized Test Suite
- **Unit Tests**: Individual module testing
- **Integration Tests**: End-to-end workflow testing
- **Fixtures**: Reusable test data and mocks in `conftest.py`
- **Coverage**: Comprehensive test coverage for all modules

### Running Tests
```bash
# Run all tests
pytest

# Run specific test module
pytest tests/test_auth/

# Run with coverage
pytest --cov=src tests/
```

## 🛠️ Development Guidelines

### Adding New Features
1. **Identify the Module**: Determine which module the feature belongs to
2. **Follow Patterns**: Use existing patterns for error handling, logging, validation
3. **Write Tests**: Add comprehensive tests in appropriate test directory
4. **Update Documentation**: Add docstrings and update README if needed

### Code Standards
- **Type Hints**: All public methods must have type hints
- **Docstrings**: All public methods must have descriptive docstrings
- **Error Handling**: Use custom exceptions from `utils.errors`
- **Logging**: Use structured logging from `utils.logging`
- **Validation**: Validate all inputs using `utils.validation`

## 📈 Future Enhancements

The modular architecture enables easy extension:

- **New Analytics Features**: Add to `analytics/` module
- **Additional Authentication Methods**: Extend `auth/` module
- **Enhanced Validation**: Expand `utils/validation.py`
- **Better Error Handling**: Add specific error types to `utils/errors.py`
- **Caching**: Add caching layer to improve performance
- **Rate Limiting**: Implement API rate limiting
