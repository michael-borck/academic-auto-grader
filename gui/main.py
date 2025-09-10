#!/usr/bin/env python3
"""
Academic Auto Grader - GUI Application
Main entry point for the Flet-based GUI interface
"""

import flet as ft
import os
import sys
from pathlib import Path

# Add project directories to Python path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CLI_CORE_DIR = PROJECT_ROOT / "cli" / "core"
GUI_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(CLI_CORE_DIR))
sys.path.insert(0, str(GUI_DIR))

from app.pages.welcome import WelcomePage
from app.pages.file_selection import FileSelectionPage
from app.pages.configuration import ConfigurationPage
from app.pages.processing import ProcessingPage
from app.pages.results import ResultsPage
from app.pages.assignment_editor import AssignmentEditorPage
from app.pages.assignment_wizard import AssignmentWizardPage
from app.pages.config_validator import ConfigValidatorPage
from app.pages.api_key_manager import APIKeyManagerPage
from app.pages.user_preferences import UserPreferencesPage
from app.pages.application_settings import ApplicationSettingsPage
from app.services.preferences_service import PreferencesService, ThemeMode
from app.router import Router, PageRoute
from app.version import APP_NAME, VERSION, VERSION_STRING, get_app_metadata


class AcademicAutoGraderApp:
    """Main application class for the Academic Auto Grader GUI"""
    
    def __init__(self):
        self.page = None
        self.router = None
        self.app_title = APP_NAME
        self.app_version = VERSION
        self.app_metadata = get_app_metadata()
        
        # Initialize preferences service
        self.preferences_service = PreferencesService()
        self.preferences_service.add_theme_change_callback(self._on_theme_change)
    
    def main(self, page: ft.Page):
        """Main application entry point called by Flet"""
        self.page = page
        
        # Load preferences
        preferences = self.preferences_service.get_preferences()
        
        # Configure page properties from preferences
        page.title = f"{self.app_title} v{self.app_version}"
        window_state = preferences.window
        page.window.width = window_state.width
        page.window.height = window_state.height
        page.window.min_width = window_state.min_width
        page.window.min_height = window_state.min_height
        
        # Apply saved window position if available
        if window_state.x is not None and window_state.y is not None:
            page.window.left = window_state.x
            page.window.top = window_state.y
        
        # Apply theme from preferences
        self._apply_theme_mode(preferences.interface.theme_mode)
        
        # Set up window state change handler
        page.on_window_event = self._on_window_event
        
        # Center the window (Flet will center automatically)
        
        # Set application icon
        icon_path = GUI_DIR / "assets" / "icons" / "grader.ico"
        if icon_path.exists():
            page.window.icon = str(icon_path)
        
        # Initialize router
        self.router = Router(page)
        
        # Register pages
        self.setup_pages()
        
        # Set up app bar
        page.appbar = self.router.create_app_bar(self.app_title)
        
        # Start with welcome page
        self.router.navigate_to(PageRoute.WELCOME)
    
    def setup_pages(self):
        """Register all pages with the router"""
        
        # Application state for sharing data between pages
        self.app_state = {
            'selection_data': None,
            'configuration': None,
            'processing_results': None
        }
        
        # Welcome page factory
        def create_welcome_page():
            return WelcomePage(
                self.page, 
                on_get_started=lambda: self.router.navigate_to(PageRoute.FILE_SELECTION)
            )
        
        # File selection page factory
        def create_file_selection_page():
            def on_selection_complete(data):
                self.app_state['selection_data'] = data
                print(f"File selection complete: {data}")
            
            def on_next_step():
                # Navigate to configuration with selection data
                self.router.navigate_to(PageRoute.CONFIGURATION)
            
            return FileSelectionPage(
                self.page,
                on_selection_complete,
                on_next_step
            )
        
        # Configuration page factory
        def create_configuration_page():
            def on_configuration_complete(data):
                self.app_state['configuration'] = data
                print(f"Configuration complete: {data}")
            
            def on_start_grading(data):
                print(f"Starting grading with: {data}")
                self.router.navigate_to(PageRoute.PROCESSING)
            
            def on_back():
                self.router.navigate_to(PageRoute.FILE_SELECTION)  # Back to file selection
            
            return ConfigurationPage(
                self.page,
                self.app_state.get('selection_data'),
                on_configuration_complete,
                on_start_grading,
                on_back
            )
        
        # Processing page factory
        def create_processing_page():
            def on_processing_complete(results):
                print(f"Processing complete: {results}")
                # Store results in app state
                self.app_state['processing_results'] = results
            
            def on_view_results(results):
                print(f"View results: {results}")
                self.router.navigate_to(PageRoute.RESULTS)
            
            def on_back_to_config():
                self.router.navigate_to(PageRoute.CONFIGURATION)
            
            return ProcessingPage(
                self.page,
                self.app_state.get('configuration'),
                on_processing_complete,
                on_view_results,
                on_back_to_config
            )
        
        # Results page factory
        def create_results_page():
            def on_back():
                self.router.navigate_to(PageRoute.PROCESSING)
            
            def on_export(format_type):
                print(f"Export to {format_type}")
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Export to {format_type.upper()} functionality coming in Task 3.1.3!"),
                        action="OK"
                    )
                )
            
            results_page = ResultsPage(
                self.page,
                self.app_state.get('processing_results', {}),
                on_back,
                on_export
            )
            return results_page.build()
        
        # Assignment editor page factory
        def create_assignment_editor_page():
            def on_save(name, config):
                print(f"Assignment saved: {name}")
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Assignment '{name}' saved successfully!"),
                        action="OK"
                    )
                )
                self.router.navigate_to(PageRoute.WELCOME)
            
            def on_cancel():
                self.router.navigate_to(PageRoute.WELCOME)
            
            return AssignmentEditorPage(
                self.page,
                assignment_name=None,  # New assignment
                on_save=on_save,
                on_cancel=on_cancel
            )
        
        # Assignment wizard page factory
        def create_assignment_wizard_page():
            def on_complete(name, config):
                print(f"Wizard completed: {name}")
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Assignment '{name}' created successfully via wizard!"),
                        action="OK"
                    )
                )
                self.router.navigate_to(PageRoute.WELCOME)
            
            def on_cancel():
                self.router.navigate_to(PageRoute.WELCOME)
            
            return AssignmentWizardPage(
                self.page,
                on_complete=on_complete,
                on_cancel=on_cancel
            )
        
        # Configuration validator page factory
        def create_config_validator_page():
            def on_close():
                self.router.navigate_to(PageRoute.WELCOME)
            
            # Sample configuration for testing
            test_config = {
                "name": "Sample Assignment",
                "type": "coding",
                "max_points": 100,
                "description": "A sample assignment for validation testing",
                "rubric": {
                    "Functionality": {
                        "description": "Code works correctly",
                        "weight": 0.5,
                        "max_points": 50
                    },
                    "Quality": {
                        "description": "Code quality",
                        "weight": 0.6,  # This will cause validation warning
                        "max_points": 60
                    }
                }
            }
            
            return ConfigValidatorPage(
                self.page,
                config_data=test_config,
                config_file="sample_config.yaml",
                on_close=on_close
            )
        
        # API Key Manager page factory
        def create_api_key_manager_page():
            def on_close():
                self.router.navigate_to(PageRoute.SETTINGS)
            
            return APIKeyManagerPage(
                self.page,
                on_close=on_close
            )
        
        # User Preferences page factory
        def create_user_preferences_page():
            def on_close():
                self.router.navigate_to(PageRoute.SETTINGS)
            
            return UserPreferencesPage(
                self.page,
                on_close=on_close
            )
        
        # Application Settings page factory
        def create_application_settings_page():
            def on_close():
                self.router.navigate_to(PageRoute.SETTINGS)
            
            return ApplicationSettingsPage(
                self.page,
                on_close=on_close
            )
        
        # Settings page factory (placeholder)
        def create_settings_page():
            return ft.Container(
                content=ft.Column([
                    ft.Text(
                        "Settings Page",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Text(
                        "Application settings and preferences",
                        size=16,
                        color=ft.Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=30),
                    ft.Row([
                        ft.ElevatedButton(
                            text="🧙‍♂️ Assignment Wizard",
                            icon=ft.Icons.AUTO_FIX_HIGH,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.PURPLE_600
                            ),
                            on_click=lambda e: self.router.navigate_to(PageRoute.ASSIGNMENT_WIZARD),
                            width=200
                        ),
                        ft.Container(width=20),
                        ft.ElevatedButton(
                            text="📝 Advanced Editor",
                            icon=ft.Icons.EDIT,
                            style=ft.ButtonStyle(
                                color=ft.Colors.WHITE,
                                bgcolor=ft.Colors.BLUE_600
                            ),
                            on_click=lambda e: self.router.navigate_to(PageRoute.ASSIGNMENT_EDITOR),
                            width=200
                        )
                    ], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Container(height=20),
                    ft.Text(
                        "💡 New to assignment creation? Use the Wizard for guided setup!\n"
                        "Need full control? Use the Advanced Editor for complete customization.",
                        size=12,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=30),
                    ft.Divider(),
                    ft.Container(height=20),
                    ft.Text("Configuration Tools", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        text="🔍 Validate Configuration",
                        icon=ft.Icons.VERIFIED,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.ORANGE_600
                        ),
                        on_click=lambda e: self.router.navigate_to(PageRoute.CONFIG_VALIDATOR),
                        width=250
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "Check assignment configurations for errors and get auto-fix suggestions",
                        size=12,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=30),
                    ft.Divider(),
                    ft.Container(height=20),
                    ft.Text("API Key Management", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        text="🔐 Manage API Keys",
                        icon=ft.Icons.KEY,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.PURPLE_600
                        ),
                        on_click=lambda e: self.router.navigate_to(PageRoute.API_KEY_MANAGER),
                        width=250
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "Securely store and manage API keys for AI providers",
                        size=12,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=30),
                    ft.Divider(),
                    ft.Container(height=20),
                    ft.Text("User Preferences", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        text="⚙️ Preferences",
                        icon=ft.Icons.SETTINGS,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.INDIGO_600
                        ),
                        on_click=lambda e: self.router.navigate_to(PageRoute.USER_PREFERENCES),
                        width=250
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "Customize themes, default folders, and application behavior",
                        size=12,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=30),
                    ft.Divider(),
                    ft.Container(height=20),
                    ft.Text("Application Settings", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        text="🔧 Advanced Settings",
                        icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.TEAL_600
                        ),
                        on_click=lambda e: self.router.navigate_to(PageRoute.APPLICATION_SETTINGS),
                        width=250
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        "Configure logging, updates, performance, and system diagnostics",
                        size=12,
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    )
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15
                ),
                padding=40,
                alignment=ft.alignment.center,
                expand=True
            )
        
        # Register all pages
        self.router.register_page(PageRoute.WELCOME, create_welcome_page)
        self.router.register_page(PageRoute.FILE_SELECTION, create_file_selection_page)
        self.router.register_page(PageRoute.CONFIGURATION, create_configuration_page)
        self.router.register_page(PageRoute.PROCESSING, create_processing_page)
        self.router.register_page(PageRoute.RESULTS, create_results_page)
        self.router.register_page(PageRoute.ASSIGNMENT_EDITOR, create_assignment_editor_page)
        self.router.register_page(PageRoute.ASSIGNMENT_WIZARD, create_assignment_wizard_page)
        self.router.register_page(PageRoute.CONFIG_VALIDATOR, create_config_validator_page)
        self.router.register_page(PageRoute.API_KEY_MANAGER, create_api_key_manager_page)
        self.router.register_page(PageRoute.USER_PREFERENCES, create_user_preferences_page)
        self.router.register_page(PageRoute.APPLICATION_SETTINGS, create_application_settings_page)
        self.router.register_page(PageRoute.SETTINGS, create_settings_page)
    
    def _apply_theme_mode(self, theme_mode: ThemeMode):
        """Apply theme mode to the page"""
        if theme_mode == ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        elif theme_mode == ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.DARK
        else:  # SYSTEM
            self.page.theme_mode = ft.ThemeMode.SYSTEM
        
        if self.page:
            self.page.update()
    
    def _on_theme_change(self, theme_mode: ThemeMode):
        """Handle theme change from preferences"""
        self._apply_theme_mode(theme_mode)
    
    def _on_window_event(self, e):
        """Handle window events to save state"""
        if e.event_type == "resize":
            # Save window size
            self.preferences_service.update_window_state(
                width=self.page.window.width,
                height=self.page.window.height
            )
        elif e.event_type == "move":
            # Save window position
            self.preferences_service.update_window_state(
                x=self.page.window.left,
                y=self.page.window.top
            )


def main():
    """Launch the GUI application"""
    app = AcademicAutoGraderApp()
    ft.app(target=app.main, name="Academic Auto Grader")


if __name__ == "__main__":
    main()