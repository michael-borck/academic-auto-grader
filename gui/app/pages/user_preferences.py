"""
User Preferences Page Component

Provides comprehensive interface for managing user preferences including
theme selection, default folders, window behavior, and application settings.
"""

import flet as ft
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.services.preferences_service import (
    PreferencesService, 
    ThemeMode, 
    Language, 
    UserPreferences,
    WindowState,
    FolderPreferences,
    InterfacePreferences,
    ProcessingPreferences,
    NotificationPreferences
)


class UserPreferencesPage:
    """User Preferences page component
    
    Provides comprehensive interface for managing all user preferences
    with real-time updates and persistent storage.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        on_close: Callable[[], None] = None
    ):
        """Initialize the user preferences page
        
        Args:
            page: Flet page object
            on_close: Callback when preferences page is closed
        """
        self.page = page
        self.on_close = on_close
        
        # Services
        self.preferences_service = PreferencesService()
        
        # Current preferences
        self.preferences = self.preferences_service.get_preferences()
        
        # UI components
        self.theme_dropdown = None
        self.language_dropdown = None
        self.folder_fields = {}
        self.processing_controls = {}
        self.notification_controls = {}
        
        # Track changes
        self.has_unsaved_changes = False
        
        # Set up preference change callback
        self.preferences_service.add_preference_change_callback(self._on_preferences_changed)
    
    def build(self) -> ft.Control:
        """Build and return the user preferences UI"""
        
        # Page header
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    "⚙️ User Preferences",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Customize your application experience",
                    size=16,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=30)
        )
        
        # Create preference sections
        interface_section = self._build_interface_section()
        folders_section = self._build_folders_section()
        processing_section = self._build_processing_section()
        notifications_section = self._build_notifications_section()
        
        # Action buttons
        action_buttons = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    text="💾 Save Changes",
                    icon=ft.Icons.SAVE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.GREEN_600
                    ),
                    on_click=self._save_preferences,
                    disabled=not self.has_unsaved_changes
                ),
                ft.ElevatedButton(
                    text="🔄 Reset to Defaults",
                    icon=ft.Icons.RESTORE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.ORANGE_600
                    ),
                    on_click=self._reset_to_defaults
                ),
                ft.ElevatedButton(
                    text="📤 Export Settings",
                    icon=ft.Icons.UPLOAD,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.PURPLE_600
                    ),
                    on_click=self._export_preferences
                ),
                ft.ElevatedButton(
                    text="📥 Import Settings",
                    icon=ft.Icons.DOWNLOAD,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.CYAN_600
                    ),
                    on_click=self._import_preferences
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    text="Close",
                    icon=ft.Icons.CLOSE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREY_700,
                        bgcolor=ft.Colors.GREY_200
                    ),
                    on_click=self._close_preferences
                )
            ]),
            padding=ft.padding.symmetric(vertical=20)
        )
        
        # Main content with tabs
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Interface",
                    icon=ft.Icons.PALETTE,
                    content=interface_section
                ),
                ft.Tab(
                    text="Folders",
                    icon=ft.Icons.FOLDER,
                    content=folders_section
                ),
                ft.Tab(
                    text="Processing",
                    icon=ft.Icons.SETTINGS,
                    content=processing_section
                ),
                ft.Tab(
                    text="Notifications",
                    icon=ft.Icons.NOTIFICATIONS,
                    content=notifications_section
                )
            ],
            expand=True
        )
        
        # Main content layout
        content = ft.Container(
            content=ft.Column([
                header,
                tabs,
                action_buttons
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
            ),
            padding=ft.padding.all(40),
            alignment=ft.alignment.top_center,
            expand=True
        )
        
        return content
    
    def _build_interface_section(self) -> ft.Container:
        """Build interface preferences section"""
        
        # Theme selection
        self.theme_dropdown = ft.Dropdown(
            label="Theme",
            options=[
                ft.dropdown.Option(text="Light", key=ThemeMode.LIGHT.value),
                ft.dropdown.Option(text="Dark", key=ThemeMode.DARK.value),
                ft.dropdown.Option(text="System Default", key=ThemeMode.SYSTEM.value)
            ],
            value=self.preferences.interface.theme_mode.value,
            on_change=self._on_theme_change,
            width=200
        )
        
        # Language selection
        self.language_dropdown = ft.Dropdown(
            label="Language",
            options=[
                ft.dropdown.Option(text="English", key=Language.ENGLISH.value),
                ft.dropdown.Option(text="Español", key=Language.SPANISH.value),
                ft.dropdown.Option(text="Français", key=Language.FRENCH.value),
                ft.dropdown.Option(text="Deutsch", key=Language.GERMAN.value),
                ft.dropdown.Option(text="中文", key=Language.CHINESE.value)
            ],
            value=self.preferences.interface.language.value,
            on_change=self._on_setting_change,
            width=200
        )
        
        # Interface options
        tooltips_checkbox = ft.Checkbox(
            label="Show tooltips",
            value=self.preferences.interface.show_tooltips,
            on_change=self._on_setting_change
        )
        
        animations_checkbox = ft.Checkbox(
            label="Enable animations",
            value=self.preferences.interface.animation_enabled,
            on_change=self._on_setting_change
        )
        
        compact_mode_checkbox = ft.Checkbox(
            label="Compact mode",
            value=self.preferences.interface.compact_mode,
            on_change=self._on_setting_change
        )
        
        welcome_screen_checkbox = ft.Checkbox(
            label="Show welcome screen on startup",
            value=self.preferences.interface.show_welcome_screen,
            on_change=self._on_setting_change
        )
        
        # Auto-save interval
        auto_save_field = ft.TextField(
            label="Auto-save interval (seconds)",
            value=str(self.preferences.interface.auto_save_interval),
            width=200,
            on_change=self._on_setting_change
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Theme & Appearance", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Theme Mode:", weight=ft.FontWeight.BOLD),
                        self.theme_dropdown
                    ]),
                    ft.Container(width=50),
                    ft.Column([
                        ft.Text("Language:", weight=ft.FontWeight.BOLD),
                        self.language_dropdown
                    ])
                ]),
                
                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=20),
                
                ft.Text("Interface Options", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                ft.Column([
                    tooltips_checkbox,
                    animations_checkbox,
                    compact_mode_checkbox,
                    welcome_screen_checkbox
                ], spacing=10),
                
                ft.Container(height=20),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Auto-save:", weight=ft.FontWeight.BOLD),
                        auto_save_field
                    ])
                ])
            ], spacing=10),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=10
        )
    
    def _build_folders_section(self) -> ft.Container:
        """Build folder preferences section"""
        
        folder_types = [
            ("submissions_folder", "Default Submissions Folder", "Where student submissions are typically located"),
            ("assignments_folder", "Assignments Configuration Folder", "Where assignment YAML files are stored"),
            ("output_folder", "Default Output Folder", "Where grading results are saved"),
            ("roster_folder", "Default Roster Folder", "Where student roster files are kept"),
            ("backup_folder", "Backup Folder", "Where backups are stored")
        ]
        
        folder_controls = []
        
        for folder_key, label, description in folder_types:
            current_value = getattr(self.preferences.folders, folder_key, "")
            
            folder_field = ft.TextField(
                label=label,
                value=current_value,
                hint_text=description,
                width=500,
                on_change=self._on_setting_change
            )
            
            browse_button = ft.IconButton(
                icon=ft.Icons.FOLDER_OPEN,
                tooltip="Browse for folder",
                on_click=lambda e, key=folder_key: self._browse_folder(key)
            )
            
            self.folder_fields[folder_key] = folder_field
            
            folder_controls.extend([
                ft.Row([
                    folder_field,
                    browse_button
                ]),
                ft.Container(height=10)
            ])
        
        # Remember last used folders option
        remember_checkbox = ft.Checkbox(
            label="Remember last used folders for each session",
            value=self.preferences.folders.remember_last_used,
            on_change=self._on_setting_change
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Default Folders", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                ft.Text(
                    "Set default folder locations to speed up your workflow. "
                    "These can be overridden in individual sessions.",
                    size=14,
                    color=ft.Colors.GREY_600
                ),
                ft.Container(height=20),
                
                ft.Column(folder_controls),
                
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=15),
                
                remember_checkbox
            ], spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=10
        )
    
    def _build_processing_section(self) -> ft.Container:
        """Build processing preferences section"""
        
        # Processing options
        dry_run_checkbox = ft.Checkbox(
            label="Enable dry-run by default (estimate costs without processing)",
            value=self.preferences.processing.default_dry_run,
            on_change=self._on_setting_change
        )
        
        auto_validate_checkbox = ft.Checkbox(
            label="Auto-validate configurations before processing",
            value=self.preferences.processing.auto_validate_config,
            on_change=self._on_setting_change
        )
        
        save_intermediate_checkbox = ft.Checkbox(
            label="Save intermediate results during processing",
            value=self.preferences.processing.save_intermediate_results,
            on_change=self._on_setting_change
        )
        
        backup_before_checkbox = ft.Checkbox(
            label="Create backup before processing",
            value=self.preferences.processing.backup_before_processing,
            on_change=self._on_setting_change
        )
        
        # Performance settings
        concurrent_field = ft.TextField(
            label="Max concurrent API requests",
            value=str(self.preferences.processing.max_concurrent_requests),
            width=200,
            on_change=self._on_setting_change
        )
        
        timeout_field = ft.TextField(
            label="Request timeout (seconds)",
            value=str(self.preferences.processing.request_timeout),
            width=200,
            on_change=self._on_setting_change
        )
        
        retry_field = ft.TextField(
            label="Retry attempts on failure",
            value=str(self.preferences.processing.retry_attempts),
            width=200,
            on_change=self._on_setting_change
        )
        
        # Store references for saving
        self.processing_controls = {
            "default_dry_run": dry_run_checkbox,
            "auto_validate_config": auto_validate_checkbox,
            "save_intermediate_results": save_intermediate_checkbox,
            "backup_before_processing": backup_before_checkbox,
            "max_concurrent_requests": concurrent_field,
            "request_timeout": timeout_field,
            "retry_attempts": retry_field
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Processing Preferences", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                ft.Text("Default Behavior", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                ft.Column([
                    dry_run_checkbox,
                    auto_validate_checkbox,
                    save_intermediate_checkbox,
                    backup_before_checkbox
                ], spacing=10),
                
                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=20),
                
                ft.Text("Performance Settings", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Concurrency:", weight=ft.FontWeight.BOLD),
                        concurrent_field
                    ]),
                    ft.Container(width=30),
                    ft.Column([
                        ft.Text("Timeout:", weight=ft.FontWeight.BOLD),
                        timeout_field
                    ]),
                    ft.Container(width=30),
                    ft.Column([
                        ft.Text("Retries:", weight=ft.FontWeight.BOLD),
                        retry_field
                    ])
                ]),
                
                ft.Container(height=15),
                ft.Text(
                    "⚠️ Adjusting these settings may affect processing speed and API usage costs.",
                    size=12,
                    color=ft.Colors.ORANGE_600
                )
            ], spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=10
        )
    
    def _build_notifications_section(self) -> ft.Container:
        """Build notifications preferences section"""
        
        # Notification options
        completion_checkbox = ft.Checkbox(
            label="Show completion notifications",
            value=self.preferences.notifications.show_completion_notifications,
            on_change=self._on_setting_change
        )
        
        error_checkbox = ft.Checkbox(
            label="Show error notifications",
            value=self.preferences.notifications.show_error_notifications,
            on_change=self._on_setting_change
        )
        
        progress_checkbox = ft.Checkbox(
            label="Show progress update notifications",
            value=self.preferences.notifications.show_progress_updates,
            on_change=self._on_setting_change
        )
        
        sound_checkbox = ft.Checkbox(
            label="Play notification sounds",
            value=self.preferences.notifications.notification_sound,
            on_change=self._on_setting_change
        )
        
        desktop_checkbox = ft.Checkbox(
            label="Show desktop notifications (when app is minimized)",
            value=self.preferences.notifications.desktop_notifications,
            on_change=self._on_setting_change
        )
        
        # Store references
        self.notification_controls = {
            "show_completion_notifications": completion_checkbox,
            "show_error_notifications": error_checkbox,
            "show_progress_updates": progress_checkbox,
            "notification_sound": sound_checkbox,
            "desktop_notifications": desktop_checkbox
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Notification Preferences", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                ft.Text(
                    "Configure when and how you receive notifications about processing status.",
                    size=14,
                    color=ft.Colors.GREY_600
                ),
                ft.Container(height=20),
                
                ft.Column([
                    completion_checkbox,
                    error_checkbox,
                    progress_checkbox,
                    sound_checkbox,
                    desktop_checkbox
                ], spacing=15),
                
                ft.Container(height=30),
                ft.Divider(),
                ft.Container(height=15),
                
                ft.Text(
                    "💡 Desktop notifications require system permissions and may not work in all environments.",
                    size=12,
                    color=ft.Colors.BLUE_600
                )
            ], spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=10
        )
    
    def _on_theme_change(self, e):
        """Handle theme change"""
        new_theme_value = e.control.value
        
        # Find matching theme mode
        for theme in ThemeMode:
            if theme.value == new_theme_value:
                # Apply theme immediately
                self.preferences_service.set_theme_mode(theme)
                self._apply_theme_to_page(theme)
                break
        
        self._mark_unsaved_changes()
    
    def _on_setting_change(self, e):
        """Handle general setting changes"""
        self._mark_unsaved_changes()
    
    def _apply_theme_to_page(self, theme_mode: ThemeMode):
        """Apply theme to the current page"""
        if theme_mode == ThemeMode.LIGHT:
            self.page.theme_mode = ft.ThemeMode.LIGHT
        elif theme_mode == ThemeMode.DARK:
            self.page.theme_mode = ft.ThemeMode.DARK
        else:  # SYSTEM
            self.page.theme_mode = ft.ThemeMode.SYSTEM
        
        self.page.update()
    
    def _browse_folder(self, folder_key: str):
        """Browse for folder selection"""
        # In a real implementation, this would open a folder picker dialog
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text(f"Folder picker for {folder_key} - feature placeholder"))
        )
    
    def _save_preferences(self, e):
        """Save all preference changes"""
        try:
            updates = {}
            
            # Collect interface updates
            if self.theme_dropdown.value:
                for theme in ThemeMode:
                    if theme.value == self.theme_dropdown.value:
                        updates["interface.theme_mode"] = theme
                        break
            
            if self.language_dropdown.value:
                for lang in Language:
                    if lang.value == self.language_dropdown.value:
                        updates["interface.language"] = lang
                        break
            
            # Collect folder updates
            for folder_key, field in self.folder_fields.items():
                updates[f"folders.{folder_key}"] = field.value or ""
            
            # Collect processing updates
            for setting_key, control in self.processing_controls.items():
                if hasattr(control, 'value'):
                    if isinstance(control, ft.TextField):
                        try:
                            updates[f"processing.{setting_key}"] = int(control.value)
                        except ValueError:
                            pass  # Skip invalid numeric values
                    else:
                        updates[f"processing.{setting_key}"] = control.value
            
            # Collect notification updates
            for setting_key, control in self.notification_controls.items():
                if hasattr(control, 'value'):
                    updates[f"notifications.{setting_key}"] = control.value
            
            # Save all updates
            success = self.preferences_service.update_preferences(**updates)
            
            if success:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Preferences saved successfully!"))
                )
                self.has_unsaved_changes = False
                self._update_action_buttons()
            else:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to save preferences"))
                )
        
        except Exception as ex:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Error saving preferences: {str(ex)}"))
            )
    
    def _reset_to_defaults(self, e):
        """Reset preferences to defaults with confirmation"""
        def confirm_reset(e):
            success = self.preferences_service.reset_to_defaults()
            
            if success:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Preferences reset to defaults!"))
                )
                # Reload the page to reflect changes
                self._reload_preferences()
            else:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to reset preferences"))
                )
            
            self._close_dialog(reset_dialog)
        
        reset_dialog = ft.AlertDialog(
            title=ft.Text("Reset to Defaults"),
            content=ft.Text(
                "Are you sure you want to reset all preferences to their default values?\n\n"
                "This action cannot be undone."
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(reset_dialog)),
                ft.ElevatedButton(
                    "Reset",
                    on_click=confirm_reset,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE_600, color=ft.Colors.WHITE)
                )
            ],
            modal=True
        )
        
        self.page.dialog = reset_dialog
        reset_dialog.open = True
        self.page.update()
    
    def _export_preferences(self, e):
        """Export preferences to file"""
        try:
            preferences_data = self.preferences_service.export_preferences()
            
            # In a real implementation, this would open a file save dialog
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Preferences exported! (Feature placeholder)"))
            )
        
        except Exception as ex:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Export failed: {str(ex)}"))
            )
    
    def _import_preferences(self, e):
        """Import preferences from file"""
        # In a real implementation, this would open a file picker
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text("Import preferences - feature placeholder"))
        )
    
    def _reload_preferences(self):
        """Reload preferences from service and update UI"""
        self.preferences = self.preferences_service.get_preferences()
        # In a full implementation, this would update all UI controls
        # For now, just mark as no unsaved changes
        self.has_unsaved_changes = False
        self._update_action_buttons()
    
    def _mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        self.has_unsaved_changes = True
        self._update_action_buttons()
    
    def _update_action_buttons(self):
        """Update action button states"""
        # This would update the save button state based on unsaved changes
        if hasattr(self, 'page'):
            self.page.update()
    
    def _on_preferences_changed(self, updates: Dict[str, Any]):
        """Handle preference changes from service"""
        # Update local preferences
        self.preferences = self.preferences_service.get_preferences()
    
    def _close_preferences(self, e):
        """Close the preferences page"""
        if self.on_close:
            self.on_close()
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close a dialog"""
        dialog.open = False
        self.page.update()


def main():
    """Test the user preferences page"""
    def test_app(page: ft.Page):
        page.title = "User Preferences Test"
        page.window.width = 1000
        page.window.height = 800
        
        def on_close():
            print("Preferences closed")
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Preferences closed"))
            )
        
        preferences_page = UserPreferencesPage(page, on_close=on_close)
        page.add(preferences_page.build())
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()