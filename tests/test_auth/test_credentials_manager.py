"""Tests for credentials manager module."""

import pytest
import os
import json
import tempfile
from unittest.mock import MagicMock, patch
from google.oauth2.credentials import Credentials

from src.auth.credentials_manager import CredentialsManager
from src.utils.errors import CredentialsError


@pytest.fixture
def temp_credentials_file():
    """Create a temporary credentials file."""
    fd, temp_file = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    yield temp_file
    if os.path.exists(temp_file):
        os.remove(temp_file)


@pytest.fixture
def mock_credentials():
    """Create mock credentials."""
    creds = MagicMock(spec=Credentials)
    creds.token = 'mock_token'
    creds.refresh_token = 'mock_refresh_token'
    creds.token_uri = 'https://oauth2.googleapis.com/token'
    creds.client_id = 'mock_client_id'
    creds.client_secret = 'mock_client_secret'
    creds.scopes = ['https://www.googleapis.com/auth/analytics.readonly']
    creds.expired = False
    return creds


def test_credentials_manager_init():
    """Test CredentialsManager initialization."""
    manager = CredentialsManager()
    assert manager.credentials_file == '.ga4_credentials.json'
    assert manager._credentials is None


def test_credentials_manager_custom_file():
    """Test CredentialsManager with custom file path."""
    custom_file = 'custom_creds.json'
    manager = CredentialsManager(custom_file)
    assert manager.credentials_file == custom_file


def test_save_credentials(temp_credentials_file, mock_credentials):
    """Test saving credentials to file."""
    manager = CredentialsManager(temp_credentials_file)
    
    manager.save_credentials(mock_credentials)
    
    # Verify file was created and contains correct data
    assert os.path.exists(temp_credentials_file)
    
    with open(temp_credentials_file, 'r') as f:
        saved_data = json.load(f)
    
    assert saved_data['token'] == 'mock_token'
    assert saved_data['client_id'] == 'mock_client_id'
    assert manager._credentials == mock_credentials


def test_load_credentials_success(temp_credentials_file):
    """Test loading credentials from file successfully."""
    # Create test credentials file
    test_data = {
        'token': 'test_token',
        'refresh_token': 'test_refresh_token',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'client_id': 'test_client_id',
        'client_secret': 'test_client_secret',
        'scopes': ['https://www.googleapis.com/auth/analytics.readonly']
    }
    
    with open(temp_credentials_file, 'w') as f:
        json.dump(test_data, f)
    
    manager = CredentialsManager(temp_credentials_file)
    
    with patch('src.auth.credentials_manager.Credentials') as mock_creds_class:
        mock_creds_instance = MagicMock()
        mock_creds_class.return_value = mock_creds_instance
        
        result = manager.load_credentials()
        
        assert result == mock_creds_instance
        assert manager._credentials == mock_creds_instance
        mock_creds_class.assert_called_once_with(
            token='test_token',
            refresh_token='test_refresh_token',
            token_uri='https://oauth2.googleapis.com/token',
            client_id='test_client_id',
            client_secret='test_client_secret',
            scopes=['https://www.googleapis.com/auth/analytics.readonly']
        )


def test_load_credentials_file_not_found():
    """Test loading credentials when file doesn't exist."""
    manager = CredentialsManager('nonexistent_file.json')
    
    with pytest.raises(CredentialsError) as exc_info:
        manager.load_credentials()
    
    assert "No saved credentials found" in str(exc_info.value)


def test_load_credentials_invalid_json(temp_credentials_file):
    """Test loading credentials with invalid JSON."""
    # Create invalid JSON file
    with open(temp_credentials_file, 'w') as f:
        f.write("invalid json content")
    
    manager = CredentialsManager(temp_credentials_file)
    
    with pytest.raises(CredentialsError) as exc_info:
        manager.load_credentials()
    
    assert "Invalid credentials file format" in str(exc_info.value)


def test_is_authenticated_true(mock_credentials):
    """Test is_authenticated property when authenticated."""
    manager = CredentialsManager()
    manager._credentials = mock_credentials
    mock_credentials.expired = False
    
    assert manager.is_authenticated is True


def test_is_authenticated_false_no_credentials():
    """Test is_authenticated property with no credentials."""
    manager = CredentialsManager()
    
    assert manager.is_authenticated is False


def test_is_authenticated_false_expired(mock_credentials):
    """Test is_authenticated property with expired credentials."""
    manager = CredentialsManager()
    manager._credentials = mock_credentials
    mock_credentials.expired = True
    
    assert manager.is_authenticated is False


def test_clear_credentials(temp_credentials_file, mock_credentials):
    """Test clearing credentials."""
    # Create credentials file
    with open(temp_credentials_file, 'w') as f:
        json.dump({'test': 'data'}, f)
    
    manager = CredentialsManager(temp_credentials_file)
    manager._credentials = mock_credentials
    
    manager.clear_credentials()
    
    assert manager._credentials is None
    assert not os.path.exists(temp_credentials_file)


def test_get_credentials_info_with_credentials(mock_credentials):
    """Test get_credentials_info with valid credentials."""
    manager = CredentialsManager()
    manager._credentials = mock_credentials
    
    info = manager.get_credentials_info()
    
    assert info['authenticated'] is True
    assert info['expired'] is False
    assert info['client_id'] == 'mock_client_id'
    assert info['scopes'] == ['https://www.googleapis.com/auth/analytics.readonly']


def test_get_credentials_info_no_credentials():
    """Test get_credentials_info with no credentials."""
    manager = CredentialsManager()
    
    info = manager.get_credentials_info()
    
    assert info['authenticated'] is False
    assert info['expired'] is True
    assert info['client_id'] is None
    assert info['scopes'] == []