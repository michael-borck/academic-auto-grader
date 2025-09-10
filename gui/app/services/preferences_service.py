"""
User Preferences Service

Manages user preferences including default folders, theme selection,
window state, and application settings with persistence.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ThemeMode(Enum):
    """Application theme modes"""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class Language(Enum):
    """Supported languages"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    CHINESE = "zh"


@dataclass
class WindowState:
    """Window size and position state"""
    width: int = 900
    height: int = 700
    x: Optional[int] = None
    y: Optional[int] = None
    maximized: bool = False
    min_width: int = 800
    min_height: int = 600


@dataclass
class FolderPreferences:
    """Default folder preferences"""
    submissions_folder: str = ""
    assignments_folder: str = ""
    output_folder: str = ""
    roster_folder: str = ""
    backup_folder: str = ""
    remember_last_used: bool = True


@dataclass
class InterfacePreferences:
    """User interface preferences"""
    theme_mode: ThemeMode = ThemeMode.SYSTEM
    language: Language = Language.ENGLISH
    show_tooltips: bool = True
    animation_enabled: bool = True
    compact_mode: bool = False
    auto_save_interval: int = 300  # seconds
    show_welcome_screen: bool = True


@dataclass
class ProcessingPreferences:
    """Processing and grading preferences"""
    default_dry_run: bool = True
    auto_validate_config: bool = True
    max_concurrent_requests: int = 5
    request_timeout: int = 30
    retry_attempts: int = 3
    save_intermediate_results: bool = True
    backup_before_processing: bool = True


@dataclass
class NotificationPreferences:
    """Notification preferences"""
    show_completion_notifications: bool = True
    show_error_notifications: bool = True
    show_progress_updates: bool = True
    notification_sound: bool = False
    desktop_notifications: bool = True


@dataclass
class UserPreferences:
    """Complete user preferences"""
    window: WindowState
    folders: FolderPreferences
    interface: InterfacePreferences
    processing: ProcessingPreferences
    notifications: NotificationPreferences
    version: str = "1.0"
    last_updated: str = ""


class PreferencesService:
    """Service for managing user preferences
    
    Provides persistent storage and management of user preferences
    including theme, folders, window state, and application settings.
    """
    
    def __init__(self):
        """Initialize the preferences service"""
        self.config_dir = Path.home() / ".auto-grader"
        self.preferences_file = self.config_dir / "preferences.json"
        self.config_dir.mkdir(exist_ok=True)
        
        # Load current preferences
        self.preferences = self._load_preferences()
        
        # Theme change callbacks
        self.theme_change_callbacks: List[callable] = []
        
        # Preference change callbacks
        self.preference_change_callbacks: List[callable] = []
    
    def get_preferences(self) -> UserPreferences:
        """Get current user preferences
        
        Returns:
            Current UserPreferences object
        """
        return self.preferences
    
    def update_preferences(self, **updates) -> bool:
        """Update user preferences
        
        Args:
            **updates: Preference updates as keyword arguments
            
        Returns:
            True if update was successful
        """
        try:
            preferences_dict = asdict(self.preferences)
            
            # Apply updates to nested structure
            for key, value in updates.items():
                if "." in key:
                    # Handle nested updates like "interface.theme_mode"
                    parts = key.split(".")
                    current = preferences_dict
                    for part in parts[:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
                    current[parts[-1]] = value
                else:
                    preferences_dict[key] = value
            
            # Update timestamp
            preferences_dict["last_updated"] = self._get_current_timestamp()
            
            # Create new preferences object
            self.preferences = self._dict_to_preferences(preferences_dict)
            
            # Save to file
            success = self._save_preferences()
            
            if success:
                # Notify callbacks
                self._notify_preference_changes(updates)
                logger.info(f"Updated preferences: {list(updates.keys())}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to update preferences: {e}")
            return False
    
    def get_window_state(self) -> WindowState:
        """Get current window state preferences"""
        return self.preferences.window
    
    def update_window_state(
        self, 
        width: Optional[int] = None,
        height: Optional[int] = None,
        x: Optional[int] = None,
        y: Optional[int] = None,
        maximized: Optional[bool] = None
    ) -> bool:
        """Update window state preferences
        
        Args:
            width: Window width
            height: Window height
            x: Window x position
            y: Window y position
            maximized: Whether window is maximized
            
        Returns:
            True if update was successful
        """
        updates = {}
        
        if width is not None:
            updates["window.width"] = max(width, self.preferences.window.min_width)
        if height is not None:
            updates["window.height"] = max(height, self.preferences.window.min_height)
        if x is not None:
            updates["window.x"] = x
        if y is not None:
            updates["window.y"] = y
        if maximized is not None:
            updates["window.maximized"] = maximized
        
        return self.update_preferences(**updates)
    
    def get_theme_mode(self) -> ThemeMode:
        """Get current theme mode"""
        return self.preferences.interface.theme_mode
    
    def set_theme_mode(self, theme_mode: ThemeMode) -> bool:
        """Set theme mode
        
        Args:
            theme_mode: New theme mode
            
        Returns:
            True if update was successful
        """
        success = self.update_preferences(**{"interface.theme_mode": theme_mode})
        
        if success:
            # Notify theme change callbacks
            for callback in self.theme_change_callbacks:
                try:
                    callback(theme_mode)
                except Exception as e:
                    logger.warning(f"Theme change callback failed: {e}")
        
        return success
    
    def get_default_folders(self) -> FolderPreferences:
        """Get default folder preferences"""
        return self.preferences.folders
    
    def update_default_folders(self, **folder_updates) -> bool:
        """Update default folder preferences
        
        Args:
            **folder_updates: Folder path updates
            
        Returns:
            True if update was successful
        """
        # Validate folder paths
        validated_updates = {}
        for key, path in folder_updates.items():
            if path and not os.path.exists(path):
                logger.warning(f"Folder path does not exist: {path}")
                # Don't prevent update, just log warning
            validated_updates[f"folders.{key}"] = path
        
        return self.update_preferences(**validated_updates)
    
    def get_language(self) -> Language:
        """Get current language preference"""
        return self.preferences.interface.language
    
    def set_language(self, language: Language) -> bool:
        """Set language preference
        
        Args:
            language: New language setting
            
        Returns:
            True if update was successful
        """
        return self.update_preferences(**{"interface.language": language})
    
    def get_processing_preferences(self) -> ProcessingPreferences:
        """Get processing preferences"""
        return self.preferences.processing
    
    def update_processing_preferences(self, **processing_updates) -> bool:
        """Update processing preferences
        
        Args:
            **processing_updates: Processing preference updates
            
        Returns:
            True if update was successful
        """
        validated_updates = {}
        for key, value in processing_updates.items():
            validated_updates[f"processing.{key}"] = value
        
        return self.update_preferences(**validated_updates)
    
    def export_preferences(self) -> Dict[str, Any]:
        """Export preferences for backup
        
        Returns:
            Dictionary with all preferences
        """
        return {
            "version": "1.0",
            "exported_at": self._get_current_timestamp(),
            "preferences": asdict(self.preferences)
        }
    
    def import_preferences(self, preferences_data: Dict[str, Any]) -> bool:
        """Import preferences from backup
        
        Args:
            preferences_data: Exported preferences data
            
        Returns:
            True if import was successful
        """
        try:
            if "preferences" not in preferences_data:
                return False
            
            # Validate and merge preferences
            imported_prefs = preferences_data["preferences"]
            self.preferences = self._dict_to_preferences(imported_prefs)
            
            # Save imported preferences
            success = self._save_preferences()
            
            if success:
                logger.info("Imported user preferences successfully")
                # Notify all callbacks of changes
                self._notify_preference_changes({"all": "imported"})
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to import preferences: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset all preferences to defaults
        
        Returns:
            True if reset was successful
        """
        try:
            # Create default preferences
            self.preferences = UserPreferences(
                window=WindowState(),
                folders=FolderPreferences(),
                interface=InterfacePreferences(),
                processing=ProcessingPreferences(),
                notifications=NotificationPreferences(),
                last_updated=self._get_current_timestamp()
            )
            
            # Save defaults
            success = self._save_preferences()
            
            if success:
                logger.info("Reset preferences to defaults")
                self._notify_preference_changes({"all": "reset"})
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to reset preferences: {e}")
            return False
    
    def add_theme_change_callback(self, callback: callable):
        """Add callback for theme changes
        
        Args:
            callback: Function to call when theme changes
        """
        self.theme_change_callbacks.append(callback)
    
    def add_preference_change_callback(self, callback: callable):
        """Add callback for preference changes
        
        Args:
            callback: Function to call when preferences change
        """
        self.preference_change_callbacks.append(callback)
    
    def get_recent_folders(self, folder_type: str, limit: int = 5) -> List[str]:
        """Get recently used folders of a specific type
        
        Args:
            folder_type: Type of folder (submissions, assignments, etc.)
            limit: Maximum number of recent folders to return
            
        Returns:
            List of recent folder paths
        """
        # This would be implemented with a separate recent folders tracking
        # For now, return empty list
        return []
    
    def add_recent_folder(self, folder_type: str, folder_path: str):
        """Add a folder to recent folders list
        
        Args:
            folder_type: Type of folder
            folder_path: Path to add to recent list
        """
        # This would be implemented with recent folders tracking
        pass
    
    def _load_preferences(self) -> UserPreferences:
        """Load preferences from file"""
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return self._dict_to_preferences(data)
        except Exception as e:
            logger.warning(f"Failed to load preferences, using defaults: {e}")
        
        # Return default preferences
        return UserPreferences(
            window=WindowState(),
            folders=FolderPreferences(),
            interface=InterfacePreferences(),
            processing=ProcessingPreferences(),
            notifications=NotificationPreferences(),
            last_updated=self._get_current_timestamp()
        )
    
    def _save_preferences(self) -> bool:
        """Save preferences to file"""
        try:
            preferences_dict = asdict(self.preferences)
            
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences_dict, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to save preferences: {e}")
            return False
    
    def _dict_to_preferences(self, data: Dict[str, Any]) -> UserPreferences:
        """Convert dictionary to UserPreferences object"""
        try:
            # Handle enum conversions
            if "interface" in data and "theme_mode" in data["interface"]:
                theme_str = data["interface"]["theme_mode"]
                if isinstance(theme_str, str):
                    for theme in ThemeMode:
                        if theme.value == theme_str:
                            data["interface"]["theme_mode"] = theme
                            break
                    else:
                        data["interface"]["theme_mode"] = ThemeMode.SYSTEM
            
            if "interface" in data and "language" in data["interface"]:
                lang_str = data["interface"]["language"]
                if isinstance(lang_str, str):
                    for lang in Language:
                        if lang.value == lang_str:
                            data["interface"]["language"] = lang
                            break
                    else:
                        data["interface"]["language"] = Language.ENGLISH
            
            # Create objects from nested dictionaries
            window = WindowState(**data.get("window", {}))
            folders = FolderPreferences(**data.get("folders", {}))
            interface = InterfacePreferences(**data.get("interface", {}))
            processing = ProcessingPreferences(**data.get("processing", {}))
            notifications = NotificationPreferences(**data.get("notifications", {}))
            
            return UserPreferences(
                window=window,
                folders=folders,
                interface=interface,
                processing=processing,
                notifications=notifications,
                version=data.get("version", "1.0"),
                last_updated=data.get("last_updated", self._get_current_timestamp())
            )
            
        except Exception as e:
            logger.error(f"Failed to parse preferences data: {e}")
            # Return defaults on error
            return UserPreferences(
                window=WindowState(),
                folders=FolderPreferences(),
                interface=InterfacePreferences(),
                processing=ProcessingPreferences(),
                notifications=NotificationPreferences(),
                last_updated=self._get_current_timestamp()
            )
    
    def _notify_preference_changes(self, updates: Dict[str, Any]):
        """Notify callbacks about preference changes"""
        for callback in self.preference_change_callbacks:
            try:
                callback(updates)
            except Exception as e:
                logger.warning(f"Preference change callback failed: {e}")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as ISO string"""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Test the preferences service"""
    service = PreferencesService()
    
    print("Testing preferences service...")
    
    # Test getting preferences
    prefs = service.get_preferences()
    print(f"Current theme: {prefs.interface.theme_mode}")
    print(f"Window size: {prefs.window.width}x{prefs.window.height}")
    
    # Test updating preferences
    service.set_theme_mode(ThemeMode.DARK)
    service.update_window_state(width=1200, height=800)
    
    # Test folder preferences
    folders = service.get_default_folders()
    print(f"Default submissions folder: {folders.submissions_folder}")
    
    print("Preferences service test completed!")


if __name__ == "__main__":
    main()