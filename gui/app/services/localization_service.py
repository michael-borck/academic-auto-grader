"""
Localization Service

Provides basic localization support for the GUI application with
support for multiple languages and internationalization features.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from enum import Enum

from .preferences_service import Language


class LocalizationService:
    """Service for managing application localization
    
    Provides translation support and locale-specific formatting
    for the GUI application.
    """
    
    def __init__(self):
        """Initialize the localization service"""
        self.locales_dir = Path(__file__).parent.parent / "locales"
        self.current_language = Language.ENGLISH
        self.translations: Dict[str, str] = {}
        self.fallback_translations: Dict[str, str] = {}
        
        # Load English as fallback
        self._load_translations(Language.ENGLISH, is_fallback=True)
        
        # Load current language
        self._load_translations(self.current_language)
    
    def set_language(self, language: Language) -> bool:
        """Set the current language
        
        Args:
            language: Language to set
            
        Returns:
            True if language was loaded successfully
        """
        if language == self.current_language:
            return True
        
        success = self._load_translations(language)
        if success:
            self.current_language = language
        
        return success
    
    def get_text(self, key: str, **kwargs) -> str:
        """Get translated text for a key
        
        Args:
            key: Translation key
            **kwargs: Format arguments
            
        Returns:
            Translated text
        """
        # Try current language first
        text = self.translations.get(key)
        
        # Fall back to English if not found
        if text is None:
            text = self.fallback_translations.get(key)
        
        # Fall back to key if still not found
        if text is None:
            text = key
        
        # Apply formatting if needed
        try:
            if kwargs:
                text = text.format(**kwargs)
        except (KeyError, ValueError):
            # If formatting fails, return unformatted text
            pass
        
        return text
    
    def get_available_languages(self) -> Dict[Language, str]:
        """Get available languages with their display names
        
        Returns:
            Dictionary mapping Language enum to display names
        """
        return {
            Language.ENGLISH: "English",
            Language.SPANISH: "Español",
            Language.FRENCH: "Français", 
            Language.GERMAN: "Deutsch",
            Language.CHINESE: "中文"
        }
    
    def format_number(self, number: float, decimal_places: int = 2) -> str:
        """Format number according to current locale
        
        Args:
            number: Number to format
            decimal_places: Number of decimal places
            
        Returns:
            Formatted number string
        """
        # Basic number formatting (would be enhanced with proper locale support)
        return f"{number:.{decimal_places}f}"
    
    def format_currency(self, amount: float, currency: str = "USD") -> str:
        """Format currency according to current locale
        
        Args:
            amount: Amount to format
            currency: Currency code
            
        Returns:
            Formatted currency string
        """
        # Basic currency formatting
        if currency == "USD":
            return f"${amount:.2f}"
        elif currency == "EUR":
            return f"€{amount:.2f}"
        else:
            return f"{amount:.2f} {currency}"
    
    def format_date(self, date_str: str) -> str:
        """Format date according to current locale
        
        Args:
            date_str: ISO date string
            
        Returns:
            Formatted date string
        """
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            
            # Basic date formatting by language
            if self.current_language == Language.ENGLISH:
                return dt.strftime("%m/%d/%Y %I:%M %p")
            elif self.current_language == Language.GERMAN:
                return dt.strftime("%d.%m.%Y %H:%M")
            elif self.current_language == Language.FRENCH:
                return dt.strftime("%d/%m/%Y %H:%M")
            else:
                return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return date_str
    
    def _load_translations(self, language: Language, is_fallback: bool = False) -> bool:
        """Load translations for a language
        
        Args:
            language: Language to load
            is_fallback: Whether this is fallback translations
            
        Returns:
            True if loaded successfully
        """
        try:
            locale_file = self.locales_dir / f"{language.value}.json"
            
            if not locale_file.exists():
                # Create default translation file if it doesn't exist
                self._create_default_translations(language)
            
            with open(locale_file, 'r', encoding='utf-8') as f:
                translations = json.load(f)
            
            if is_fallback:
                self.fallback_translations = translations
            else:
                self.translations = translations
            
            return True
            
        except Exception as e:
            print(f"Failed to load translations for {language.value}: {e}")
            return False
    
    def _create_default_translations(self, language: Language):
        """Create default translation file for a language"""
        
        # Create locales directory if it doesn't exist
        self.locales_dir.mkdir(exist_ok=True)
        
        # Base translations (English)
        base_translations = {
            # Application
            "app.title": "Academic Auto Grader",
            "app.version": "Version {version}",
            
            # Navigation
            "nav.welcome": "Welcome",
            "nav.files": "Files",
            "nav.configuration": "Configuration", 
            "nav.processing": "Processing",
            "nav.results": "Results",
            "nav.settings": "Settings",
            
            # Common actions
            "action.save": "Save",
            "action.cancel": "Cancel",
            "action.close": "Close",
            "action.edit": "Edit",
            "action.delete": "Delete",
            "action.add": "Add",
            "action.remove": "Remove",
            "action.browse": "Browse",
            "action.refresh": "Refresh",
            "action.export": "Export",
            "action.import": "Import",
            "action.reset": "Reset",
            "action.apply": "Apply",
            "action.continue": "Continue",
            "action.back": "Back",
            "action.next": "Next",
            "action.finish": "Finish",
            
            # Messages
            "msg.success": "Operation completed successfully",
            "msg.error": "An error occurred",
            "msg.warning": "Warning",
            "msg.info": "Information",
            "msg.confirm_delete": "Are you sure you want to delete this item?",
            "msg.unsaved_changes": "You have unsaved changes. Continue?",
            
            # File operations
            "file.select": "Select File",
            "file.folder": "Select Folder",
            "file.not_found": "File not found",
            "file.invalid": "Invalid file format",
            
            # API Keys
            "api.title": "API Key Manager",
            "api.add": "Add API Key",
            "api.provider": "Provider",
            "api.name": "Key Name",
            "api.key": "API Key",
            "api.test": "Test Key",
            "api.valid": "Valid",
            "api.invalid": "Invalid",
            
            # Preferences
            "pref.title": "User Preferences",
            "pref.theme": "Theme",
            "pref.language": "Language",
            "pref.folders": "Default Folders",
            "pref.processing": "Processing",
            "pref.notifications": "Notifications",
            
            # Theme options
            "theme.light": "Light",
            "theme.dark": "Dark", 
            "theme.system": "System Default",
            
            # Processing
            "proc.dry_run": "Dry Run",
            "proc.start": "Start Processing",
            "proc.cancel": "Cancel Processing",
            "proc.progress": "Progress",
            "proc.complete": "Processing Complete",
            "proc.failed": "Processing Failed",
            
            # Results
            "results.title": "Grading Results",
            "results.summary": "Summary",
            "results.student": "Student",
            "results.score": "Score",
            "results.export": "Export Results",
            
            # Validation
            "val.title": "Configuration Validator",
            "val.valid": "Configuration is valid",
            "val.invalid": "Configuration has issues",
            "val.errors": "Errors",
            "val.warnings": "Warnings",
            "val.suggestions": "Suggestions"
        }
        
        # Language-specific translations
        if language == Language.SPANISH:
            translations = {
                "app.title": "Calificador Automático Académico",
                "nav.welcome": "Bienvenida",
                "nav.files": "Archivos",
                "nav.configuration": "Configuración",
                "nav.processing": "Procesamiento",
                "nav.results": "Resultados",
                "nav.settings": "Configuraciones",
                "action.save": "Guardar",
                "action.cancel": "Cancelar",
                "action.close": "Cerrar",
                "theme.light": "Claro",
                "theme.dark": "Oscuro",
                "theme.system": "Sistema por Defecto"
            }
        elif language == Language.FRENCH:
            translations = {
                "app.title": "Correcteur Automatique Académique",
                "nav.welcome": "Bienvenue",
                "nav.files": "Fichiers",
                "nav.configuration": "Configuration",
                "nav.processing": "Traitement",
                "nav.results": "Résultats",
                "nav.settings": "Paramètres",
                "action.save": "Enregistrer",
                "action.cancel": "Annuler",
                "action.close": "Fermer",
                "theme.light": "Clair",
                "theme.dark": "Sombre",
                "theme.system": "Système par Défaut"
            }
        elif language == Language.GERMAN:
            translations = {
                "app.title": "Akademischer Auto-Bewerter",
                "nav.welcome": "Willkommen",
                "nav.files": "Dateien",
                "nav.configuration": "Konfiguration",
                "nav.processing": "Verarbeitung",
                "nav.results": "Ergebnisse",
                "nav.settings": "Einstellungen",
                "action.save": "Speichern",
                "action.cancel": "Abbrechen",
                "action.close": "Schließen",
                "theme.light": "Hell",
                "theme.dark": "Dunkel",
                "theme.system": "System-Standard"
            }
        elif language == Language.CHINESE:
            translations = {
                "app.title": "学术自动评分器",
                "nav.welcome": "欢迎",
                "nav.files": "文件",
                "nav.configuration": "配置",
                "nav.processing": "处理中",
                "nav.results": "结果",
                "nav.settings": "设置",
                "action.save": "保存",
                "action.cancel": "取消",
                "action.close": "关闭",
                "theme.light": "浅色",
                "theme.dark": "深色",
                "theme.system": "系统默认"
            }
        else:
            # Default to English
            translations = base_translations
        
        # Merge with base translations for missing keys
        if language != Language.ENGLISH:
            full_translations = base_translations.copy()
            full_translations.update(translations)
            translations = full_translations
        
        # Save to file
        locale_file = self.locales_dir / f"{language.value}.json"
        try:
            with open(locale_file, 'w', encoding='utf-8') as f:
                json.dump(translations, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Failed to create translation file for {language.value}: {e}")


# Global localization service instance
_localization_service = None

def get_localization_service() -> LocalizationService:
    """Get global localization service instance"""
    global _localization_service
    if _localization_service is None:
        _localization_service = LocalizationService()
    return _localization_service

def t(key: str, **kwargs) -> str:
    """Shorthand function for getting translated text
    
    Args:
        key: Translation key
        **kwargs: Format arguments
        
    Returns:
        Translated text
    """
    return get_localization_service().get_text(key, **kwargs)


def main():
    """Test the localization service"""
    service = LocalizationService()
    
    print("Testing localization service...")
    
    # Test English (default)
    print(f"English: {service.get_text('app.title')}")
    
    # Test Spanish
    service.set_language(Language.SPANISH)
    print(f"Spanish: {service.get_text('app.title')}")
    
    # Test missing key fallback
    print(f"Fallback: {service.get_text('missing.key')}")
    
    # Test formatting
    print(f"Formatted: {service.get_text('app.version', version='1.0.0')}")
    
    print("Localization service test completed!")


if __name__ == "__main__":
    main()