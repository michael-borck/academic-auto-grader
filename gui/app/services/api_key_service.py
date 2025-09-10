"""
API Key Management Service

Provides secure storage and management of API keys for various AI providers
using the system keyring for secure credential storage.
"""

import keyring
import requests
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class APIProvider(Enum):
    """Supported API providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    AZURE = "azure"


@dataclass
class APIKeyInfo:
    """API key information"""
    provider: APIProvider
    key_name: str
    masked_key: str
    is_active: bool
    last_validated: Optional[str] = None
    validation_status: str = "unknown"  # unknown, valid, invalid, expired
    usage_count: int = 0
    created_date: Optional[str] = None
    notes: str = ""


@dataclass
class ValidationResult:
    """API key validation result"""
    is_valid: bool
    provider: APIProvider
    error_message: str = ""
    account_info: Dict[str, Any] = None
    rate_limits: Dict[str, Any] = None
    quota_usage: Dict[str, Any] = None


class APIKeyService:
    """Service for managing API keys securely
    
    Uses system keyring for secure storage and provides validation,
    testing, and management capabilities for AI provider API keys.
    """
    
    def __init__(self):
        """Initialize the API key service"""
        self.service_name = "academic-auto-grader"
        self.config_file = Path.home() / ".auto-grader" / "api_keys.json"
        self.config_file.parent.mkdir(exist_ok=True)
        
        # Load key metadata
        self.key_metadata = self._load_key_metadata()
        
        # Provider-specific validation endpoints
        self.validation_endpoints = {
            APIProvider.OPENAI: "https://api.openai.com/v1/models",
            APIProvider.ANTHROPIC: "https://api.anthropic.com/v1/models",
            APIProvider.GOOGLE: "https://generativelanguage.googleapis.com/v1/models",
            APIProvider.AZURE: None  # Requires custom endpoint
        }
    
    def add_api_key(
        self, 
        provider: APIProvider, 
        key_name: str, 
        api_key: str,
        notes: str = ""
    ) -> bool:
        """Add a new API key
        
        Args:
            provider: API provider
            key_name: User-friendly name for the key
            api_key: The actual API key
            notes: Optional notes about the key
            
        Returns:
            True if key was added successfully
        """
        try:
            # Store key securely in keyring
            username = f"{provider.value}_{key_name}"
            keyring.set_password(self.service_name, username, api_key)
            
            # Store metadata
            key_info = APIKeyInfo(
                provider=provider,
                key_name=key_name,
                masked_key=self._mask_key(api_key),
                is_active=True,
                validation_status="unknown",
                usage_count=0,
                created_date=self._get_current_timestamp(),
                notes=notes
            )
            
            self.key_metadata[username] = asdict(key_info)
            self._save_key_metadata()
            
            logger.info(f"Added API key: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add API key {username}: {e}")
            return False
    
    def get_api_key(self, provider: APIProvider, key_name: str) -> Optional[str]:
        """Retrieve API key from secure storage
        
        Args:
            provider: API provider
            key_name: Key name
            
        Returns:
            API key if found, None otherwise
        """
        try:
            username = f"{provider.value}_{key_name}"
            return keyring.get_password(self.service_name, username)
        except Exception as e:
            logger.error(f"Failed to retrieve API key {username}: {e}")
            return None
    
    def list_api_keys(self, provider: Optional[APIProvider] = None) -> List[APIKeyInfo]:
        """List all stored API keys
        
        Args:
            provider: Filter by provider (optional)
            
        Returns:
            List of API key information
        """
        keys = []
        
        for username, metadata in self.key_metadata.items():
            try:
                key_info = APIKeyInfo(**metadata)
                
                # Filter by provider if specified
                if provider and key_info.provider != provider:
                    continue
                
                keys.append(key_info)
            except Exception as e:
                logger.warning(f"Invalid key metadata for {username}: {e}")
        
        return sorted(keys, key=lambda k: k.created_date or "", reverse=True)
    
    def update_api_key(
        self, 
        provider: APIProvider, 
        key_name: str,
        new_api_key: Optional[str] = None,
        new_notes: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> bool:
        """Update an existing API key
        
        Args:
            provider: API provider
            key_name: Key name
            new_api_key: New API key value (optional)
            new_notes: New notes (optional)
            is_active: Active status (optional)
            
        Returns:
            True if update was successful
        """
        try:
            username = f"{provider.value}_{key_name}"
            
            if username not in self.key_metadata:
                return False
            
            # Update API key in keyring if provided
            if new_api_key:
                keyring.set_password(self.service_name, username, new_api_key)
                self.key_metadata[username]["masked_key"] = self._mask_key(new_api_key)
                self.key_metadata[username]["validation_status"] = "unknown"
            
            # Update metadata
            if new_notes is not None:
                self.key_metadata[username]["notes"] = new_notes
            
            if is_active is not None:
                self.key_metadata[username]["is_active"] = is_active
            
            self._save_key_metadata()
            logger.info(f"Updated API key: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update API key {username}: {e}")
            return False
    
    def delete_api_key(self, provider: APIProvider, key_name: str) -> bool:
        """Delete an API key
        
        Args:
            provider: API provider
            key_name: Key name
            
        Returns:
            True if deletion was successful
        """
        try:
            username = f"{provider.value}_{key_name}"
            
            # Remove from keyring
            try:
                keyring.delete_password(self.service_name, username)
            except keyring.errors.PasswordDeleteError:
                # Key might not exist in keyring
                pass
            
            # Remove metadata
            if username in self.key_metadata:
                del self.key_metadata[username]
                self._save_key_metadata()
            
            logger.info(f"Deleted API key: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete API key {username}: {e}")
            return False
    
    async def validate_api_key(
        self, 
        provider: APIProvider, 
        api_key: str,
        custom_endpoint: Optional[str] = None
    ) -> ValidationResult:
        """Validate an API key by testing it with the provider
        
        Args:
            provider: API provider
            api_key: API key to validate
            custom_endpoint: Custom endpoint for validation (e.g., Azure)
            
        Returns:
            ValidationResult with validation details
        """
        try:
            if provider == APIProvider.OPENAI:
                return await self._validate_openai_key(api_key)
            elif provider == APIProvider.ANTHROPIC:
                return await self._validate_anthropic_key(api_key)
            elif provider == APIProvider.GOOGLE:
                return await self._validate_google_key(api_key)
            elif provider == APIProvider.AZURE:
                return await self._validate_azure_key(api_key, custom_endpoint)
            else:
                return ValidationResult(
                    is_valid=False,
                    provider=provider,
                    error_message=f"Validation not implemented for {provider.value}"
                )
        
        except Exception as e:
            logger.error(f"API key validation failed for {provider.value}: {e}")
            return ValidationResult(
                is_valid=False,
                provider=provider,
                error_message=str(e)
            )
    
    async def _validate_openai_key(self, api_key: str) -> ValidationResult:
        """Validate OpenAI API key"""
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Test with models endpoint (lightweight)
            async with asyncio.timeout(10):
                response = requests.get(
                    "https://api.openai.com/v1/models",
                    headers=headers,
                    timeout=5
                )
            
            if response.status_code == 200:
                data = response.json()
                return ValidationResult(
                    is_valid=True,
                    provider=APIProvider.OPENAI,
                    account_info={"models_available": len(data.get("data", []))},
                    rate_limits=dict(response.headers)
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    provider=APIProvider.OPENAI,
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )
        
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                provider=APIProvider.OPENAI,
                error_message=str(e)
            )
    
    async def _validate_anthropic_key(self, api_key: str) -> ValidationResult:
        """Validate Anthropic API key"""
        try:
            headers = {
                "x-api-key": api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            # Test with a minimal completion request
            test_data = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "test"}]
            }
            
            async with asyncio.timeout(10):
                response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=test_data,
                    timeout=5
                )
            
            if response.status_code in [200, 429]:  # 429 means valid but rate limited
                return ValidationResult(
                    is_valid=True,
                    provider=APIProvider.ANTHROPIC,
                    account_info={"status": "valid"},
                    rate_limits=dict(response.headers)
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    provider=APIProvider.ANTHROPIC,
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )
        
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                provider=APIProvider.ANTHROPIC,
                error_message=str(e)
            )
    
    async def _validate_google_key(self, api_key: str) -> ValidationResult:
        """Validate Google AI API key"""
        try:
            async with asyncio.timeout(10):
                response = requests.get(
                    f"https://generativelanguage.googleapis.com/v1/models?key={api_key}",
                    timeout=5
                )
            
            if response.status_code == 200:
                data = response.json()
                return ValidationResult(
                    is_valid=True,
                    provider=APIProvider.GOOGLE,
                    account_info={"models_available": len(data.get("models", []))},
                    rate_limits=dict(response.headers)
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    provider=APIProvider.GOOGLE,
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )
        
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                provider=APIProvider.GOOGLE,
                error_message=str(e)
            )
    
    async def _validate_azure_key(self, api_key: str, endpoint: Optional[str]) -> ValidationResult:
        """Validate Azure OpenAI API key"""
        if not endpoint:
            return ValidationResult(
                is_valid=False,
                provider=APIProvider.AZURE,
                error_message="Azure endpoint URL is required"
            )
        
        try:
            headers = {
                "api-key": api_key,
                "Content-Type": "application/json"
            }
            
            # Try to list deployments
            async with asyncio.timeout(10):
                response = requests.get(
                    f"{endpoint}/openai/deployments?api-version=2023-05-15",
                    headers=headers,
                    timeout=5
                )
            
            if response.status_code == 200:
                data = response.json()
                return ValidationResult(
                    is_valid=True,
                    provider=APIProvider.AZURE,
                    account_info={"deployments": len(data.get("data", []))},
                    rate_limits=dict(response.headers)
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    provider=APIProvider.AZURE,
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )
        
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                provider=APIProvider.AZURE,
                error_message=str(e)
            )
    
    def get_active_key(self, provider: APIProvider) -> Optional[Tuple[str, str]]:
        """Get the first active API key for a provider
        
        Args:
            provider: API provider
            
        Returns:
            Tuple of (key_name, api_key) if found, None otherwise
        """
        for username, metadata in self.key_metadata.items():
            try:
                key_info = APIKeyInfo(**metadata)
                
                if key_info.provider == provider and key_info.is_active:
                    api_key = self.get_api_key(provider, key_info.key_name)
                    if api_key:
                        return key_info.key_name, api_key
            except Exception:
                continue
        
        return None
    
    def export_keys_metadata(self) -> Dict[str, Any]:
        """Export API key metadata (without actual keys)
        
        Returns:
            Dictionary with key metadata for backup
        """
        return {
            "version": "1.0",
            "exported_at": self._get_current_timestamp(),
            "keys": self.key_metadata.copy()
        }
    
    def import_keys_metadata(self, metadata: Dict[str, Any]) -> bool:
        """Import API key metadata from backup
        
        Args:
            metadata: Exported metadata dictionary
            
        Returns:
            True if import was successful
        """
        try:
            if "keys" not in metadata:
                return False
            
            # Merge with existing metadata
            for username, key_metadata in metadata["keys"].items():
                if username not in self.key_metadata:
                    self.key_metadata[username] = key_metadata
            
            self._save_key_metadata()
            logger.info("Imported API key metadata")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import key metadata: {e}")
            return False
    
    def _load_key_metadata(self) -> Dict[str, Any]:
        """Load API key metadata from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load key metadata: {e}")
        
        return {}
    
    def _save_key_metadata(self):
        """Save API key metadata to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.key_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save key metadata: {e}")
    
    def _mask_key(self, api_key: str) -> str:
        """Mask API key for display"""
        if len(api_key) <= 8:
            return "*" * len(api_key)
        
        return api_key[:4] + "*" * (len(api_key) - 8) + api_key[-4:]
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Test the API key service"""
    async def test_service():
        service = APIKeyService()
        
        # Test adding a key
        print("Testing API key service...")
        
        # List existing keys
        keys = service.list_api_keys()
        print(f"Existing keys: {len(keys)}")
        
        # Test validation (with dummy key)
        test_key = "sk-test1234567890abcdef"
        result = await service.validate_api_key(APIProvider.OPENAI, test_key)
        print(f"Validation result: {result.is_valid}, {result.error_message}")
    
    asyncio.run(test_service())


if __name__ == "__main__":
    main()