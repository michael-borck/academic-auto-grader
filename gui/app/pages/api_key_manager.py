"""
API Key Manager Page Component

Provides comprehensive interface for managing API keys including
secure storage, validation, testing, and key management operations.
"""

import flet as ft
import asyncio
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.services.api_key_service import (
    APIKeyService, 
    APIProvider, 
    APIKeyInfo, 
    ValidationResult
)


class APIKeyManagerPage:
    """API Key Manager page component
    
    Provides comprehensive interface for secure API key management
    with validation, testing, and backup/restore capabilities.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        on_close: Callable[[], None] = None
    ):
        """Initialize the API key manager
        
        Args:
            page: Flet page object
            on_close: Callback when manager is closed
        """
        self.page = page
        self.on_close = on_close
        
        # Services
        self.api_key_service = APIKeyService()
        
        # State
        self.current_keys: List[APIKeyInfo] = []
        self.selected_provider: Optional[APIProvider] = None
        self.validation_in_progress = False
        
        # UI components
        self.keys_list = None
        self.add_key_dialog = None
        self.edit_key_dialog = None
        self.validation_dialog = None
        
    def build(self) -> ft.Control:
        """Build and return the API key manager UI"""
        
        # Page header
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    "🔐 API Key Manager",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Securely manage API keys for AI providers",
                    size=16,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=10),
                ft.Row([
                    ft.Icon(ft.Icons.SECURITY, color=ft.Colors.GREEN_600),
                    ft.Text(
                        "All API keys are stored securely using your system's keyring",
                        size=12,
                        color=ft.Colors.GREEN_700
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=30)
        )
        
        # Provider filter
        provider_filter = self._build_provider_filter()
        
        # Action buttons
        action_buttons = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    text="➕ Add API Key",
                    icon=ft.Icons.ADD,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.GREEN_600
                    ),
                    on_click=self._show_add_key_dialog
                ),
                ft.ElevatedButton(
                    text="🔄 Refresh List",
                    icon=ft.Icons.REFRESH,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600
                    ),
                    on_click=self._refresh_keys_list
                ),
                ft.ElevatedButton(
                    text="💾 Backup Keys",
                    icon=ft.Icons.BACKUP,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.PURPLE_600
                    ),
                    on_click=self._show_backup_dialog
                ),
                ft.ElevatedButton(
                    text="📥 Restore Keys",
                    icon=ft.Icons.RESTORE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.ORANGE_600
                    ),
                    on_click=self._show_restore_dialog
                )
            ], spacing=15),
            padding=ft.padding.symmetric(vertical=20)
        )
        
        # Keys list
        self._build_keys_list()
        
        # Main content layout
        content = ft.Container(
            content=ft.Column([
                header,
                provider_filter,
                action_buttons,
                self.keys_list,
                ft.Container(height=20),
                
                # Close button
                ft.Container(
                    content=ft.ElevatedButton(
                        text="Close",
                        icon=ft.Icons.CLOSE,
                        style=ft.ButtonStyle(
                            color=ft.Colors.GREY_700,
                            bgcolor=ft.Colors.GREY_200
                        ),
                        on_click=self._close_manager,
                        width=150
                    ),
                    alignment=ft.alignment.center
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
            ),
            padding=ft.padding.all(40),
            alignment=ft.alignment.top_center,
            expand=True
        )
        
        # Load initial data
        self._refresh_keys_list()
        
        return content
    
    def _build_provider_filter(self) -> ft.Container:
        """Build provider filter dropdown"""
        providers = [("All Providers", None)] + [(p.value.title(), p) for p in APIProvider]
        
        provider_dropdown = ft.Dropdown(
            label="Filter by Provider",
            options=[
                ft.dropdown.Option(text=name, key=str(provider))
                for name, provider in providers
            ],
            value="None",
            on_change=self._on_provider_filter_change,
            width=200
        )
        
        return ft.Container(
            content=ft.Row([
                ft.Text("Filter:", weight=ft.FontWeight.BOLD),
                ft.Container(width=15),
                provider_dropdown
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=15)
        )
    
    def _build_keys_list(self):
        """Build API keys list display"""
        self.keys_list = ft.Container(
            content=ft.Column([
                ft.Text(
                    "🔑 Stored API Keys",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800
                ),
                ft.Container(height=15),
                ft.Container(
                    content=ft.ListView(spacing=10, height=400),
                    height=400,
                    width=1000
                )
            ]),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10
        )
    
    def _refresh_keys_list(self, e=None):
        """Refresh the API keys list"""
        # Load keys from service
        self.current_keys = self.api_key_service.list_api_keys(self.selected_provider)
        
        # Update UI
        keys_listview = self.keys_list.content.controls[2].content
        keys_listview.controls.clear()
        
        if not self.current_keys:
            keys_listview.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.KEY_OFF, size=50, color=ft.Colors.GREY_400),
                        ft.Text(
                            "No API keys found",
                            size=16,
                            color=ft.Colors.GREY_600,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "Click 'Add API Key' to get started",
                            size=12,
                            color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.all(50),
                    alignment=ft.alignment.center
                )
            )
        else:
            for key_info in self.current_keys:
                key_widget = self._create_key_widget(key_info)
                keys_listview.controls.append(key_widget)
        
        self.page.update()
    
    def _create_key_widget(self, key_info: APIKeyInfo) -> ft.Container:
        """Create widget for displaying API key information"""
        
        # Status indicator
        status_colors = {
            "valid": (ft.Icons.CHECK_CIRCLE, ft.Colors.GREEN_600),
            "invalid": (ft.Icons.ERROR, ft.Colors.RED_600),
            "expired": (ft.Icons.SCHEDULE, ft.Colors.ORANGE_600),
            "unknown": (ft.Icons.HELP, ft.Colors.GREY_500)
        }
        
        status_icon, status_color = status_colors.get(
            key_info.validation_status, 
            status_colors["unknown"]
        )
        
        # Provider badge
        provider_colors = {
            APIProvider.OPENAI: ft.Colors.GREEN_600,
            APIProvider.ANTHROPIC: ft.Colors.PURPLE_600,
            APIProvider.GOOGLE: ft.Colors.BLUE_600,
            APIProvider.AZURE: ft.Colors.CYAN_600
        }
        
        provider_color = provider_colors.get(key_info.provider, ft.Colors.GREY_600)
        
        # Action buttons
        action_buttons = ft.Row([
            ft.IconButton(
                icon=ft.Icons.EDIT,
                tooltip="Edit Key",
                on_click=lambda e, key=key_info: self._show_edit_key_dialog(key),
                icon_color=ft.Colors.BLUE_600
            ),
            ft.IconButton(
                icon=ft.Icons.VERIFIED,
                tooltip="Test Key",
                on_click=lambda e, key=key_info: self._test_api_key(key),
                icon_color=ft.Colors.GREEN_600
            ),
            ft.IconButton(
                icon=ft.Icons.VISIBILITY if key_info.is_active else ft.Icons.VISIBILITY_OFF,
                tooltip="Toggle Active",
                on_click=lambda e, key=key_info: self._toggle_key_active(key),
                icon_color=ft.Colors.ORANGE_600
            ),
            ft.IconButton(
                icon=ft.Icons.DELETE,
                tooltip="Delete Key",
                on_click=lambda e, key=key_info: self._delete_api_key(key),
                icon_color=ft.Colors.RED_600
            )
        ], spacing=5)
        
        return ft.Container(
            content=ft.Row([
                # Provider badge
                ft.Container(
                    content=ft.Text(
                        key_info.provider.value.upper(),
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.WHITE
                    ),
                    padding=ft.padding.symmetric(horizontal=10, vertical=5),
                    bgcolor=provider_color,
                    border_radius=5,
                    width=80
                ),
                
                ft.Container(width=15),
                
                # Key info
                ft.Column([
                    ft.Row([
                        ft.Text(
                            key_info.key_name,
                            size=16,
                            weight=ft.FontWeight.BOLD
                        ),
                        ft.Icon(status_icon, color=status_color, size=20)
                    ]),
                    ft.Text(
                        f"Key: {key_info.masked_key}",
                        size=12,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Text(
                        f"Status: {key_info.validation_status.title()} | "
                        f"Used: {key_info.usage_count} times | "
                        f"Active: {'Yes' if key_info.is_active else 'No'}",
                        size=11,
                        color=ft.Colors.GREY_500
                    ),
                    ft.Text(
                        key_info.notes if key_info.notes else "No notes",
                        size=10,
                        color=ft.Colors.GREY_400,
                        italic=not key_info.notes
                    ) if key_info.notes or True else ft.Container()
                ], expand=True, spacing=2),
                
                ft.Container(width=15),
                
                # Actions
                action_buttons
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.all(15),
            bgcolor=ft.Colors.GREEN_50 if key_info.is_active else ft.Colors.GREY_50,
            border=ft.border.all(
                1, 
                ft.Colors.GREEN_200 if key_info.is_active else ft.Colors.GREY_200
            ),
            border_radius=10,
            margin=ft.margin.only(bottom=10)
        )
    
    def _on_provider_filter_change(self, e):
        """Handle provider filter change"""
        selected_value = e.control.value
        
        if selected_value == "None":
            self.selected_provider = None
        else:
            for provider in APIProvider:
                if str(provider) == selected_value:
                    self.selected_provider = provider
                    break
        
        self._refresh_keys_list()
    
    def _show_add_key_dialog(self, e):
        """Show add API key dialog"""
        provider_dropdown = ft.Dropdown(
            label="Provider",
            options=[
                ft.dropdown.Option(text=p.value.title(), key=p.value)
                for p in APIProvider
            ],
            width=200
        )
        
        key_name_field = ft.TextField(
            label="Key Name",
            hint_text="e.g., 'My OpenAI Key' or 'Production Key'",
            width=300
        )
        
        api_key_field = ft.TextField(
            label="API Key",
            hint_text="Enter your API key",
            password=True,
            can_reveal_password=True,
            width=400
        )
        
        notes_field = ft.TextField(
            label="Notes (Optional)",
            hint_text="Additional notes about this key",
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=400
        )
        
        async def add_key(e):
            if not all([provider_dropdown.value, key_name_field.value, api_key_field.value]):
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Please fill in all required fields"))
                )
                return
            
            # Get provider enum
            provider = None
            for p in APIProvider:
                if p.value == provider_dropdown.value:
                    provider = p
                    break
            
            if not provider:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Invalid provider selected"))
                )
                return
            
            # Add the key
            success = self.api_key_service.add_api_key(
                provider=provider,
                key_name=key_name_field.value,
                api_key=api_key_field.value,
                notes=notes_field.value or ""
            )
            
            if success:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("API key added successfully!"))
                )
                self._close_dialog(self.add_key_dialog)
                self._refresh_keys_list()
            else:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to add API key"))
                )
        
        self.add_key_dialog = ft.AlertDialog(
            title=ft.Text("Add New API Key"),
            content=ft.Container(
                content=ft.Column([
                    provider_dropdown,
                    ft.Container(height=10),
                    key_name_field,
                    ft.Container(height=10),
                    api_key_field,
                    ft.Container(height=10),
                    notes_field
                ]),
                width=450,
                height=350
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(self.add_key_dialog)),
                ft.ElevatedButton("Add Key", on_click=add_key)
            ],
            modal=True
        )
        
        self.page.dialog = self.add_key_dialog
        self.add_key_dialog.open = True
        self.page.update()
    
    def _show_edit_key_dialog(self, key_info: APIKeyInfo):
        """Show edit API key dialog"""
        key_name_field = ft.TextField(
            label="Key Name",
            value=key_info.key_name,
            width=300
        )
        
        notes_field = ft.TextField(
            label="Notes",
            value=key_info.notes,
            multiline=True,
            min_lines=2,
            max_lines=4,
            width=400
        )
        
        active_checkbox = ft.Checkbox(
            label="Active",
            value=key_info.is_active
        )
        
        def update_key(e):
            success = self.api_key_service.update_api_key(
                provider=key_info.provider,
                key_name=key_info.key_name,  # Use original name for lookup
                new_notes=notes_field.value,
                is_active=active_checkbox.value
            )
            
            if success:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("API key updated successfully!"))
                )
                self._close_dialog(self.edit_key_dialog)
                self._refresh_keys_list()
            else:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to update API key"))
                )
        
        self.edit_key_dialog = ft.AlertDialog(
            title=ft.Text(f"Edit API Key - {key_info.provider.value.title()}"),
            content=ft.Container(
                content=ft.Column([
                    key_name_field,
                    ft.Container(height=10),
                    notes_field,
                    ft.Container(height=10),
                    active_checkbox
                ]),
                width=450,
                height=250
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(self.edit_key_dialog)),
                ft.ElevatedButton("Update", on_click=update_key)
            ],
            modal=True
        )
        
        self.page.dialog = self.edit_key_dialog
        self.edit_key_dialog.open = True
        self.page.update()
    
    async def _test_api_key(self, key_info: APIKeyInfo):
        """Test API key connectivity"""
        if self.validation_in_progress:
            return
        
        self.validation_in_progress = True
        
        # Show validation dialog
        validation_progress = ft.ProgressRing()
        validation_text = ft.Text("Testing API key connectivity...")
        
        self.validation_dialog = ft.AlertDialog(
            title=ft.Text("Testing API Key"),
            content=ft.Container(
                content=ft.Column([
                    validation_progress,
                    ft.Container(height=15),
                    validation_text
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=300,
                height=150
            ),
            modal=True
        )
        
        self.page.dialog = self.validation_dialog
        self.validation_dialog.open = True
        self.page.update()
        
        try:
            # Get API key from secure storage
            api_key = self.api_key_service.get_api_key(key_info.provider, key_info.key_name)
            
            if not api_key:
                validation_text.value = "Failed to retrieve API key from storage"
                self.page.update()
                await asyncio.sleep(2)
                self._close_dialog(self.validation_dialog)
                return
            
            # Validate the key
            result = await self.api_key_service.validate_api_key(key_info.provider, api_key)
            
            # Update validation status in metadata
            new_status = "valid" if result.is_valid else "invalid"
            self.api_key_service.update_api_key(
                provider=key_info.provider,
                key_name=key_info.key_name,
                is_active=key_info.is_active  # Keep current active status
            )
            
            # Show results
            if result.is_valid:
                validation_text.value = "✅ API key is valid and working!"
                validation_text.color = ft.Colors.GREEN_600
            else:
                validation_text.value = f"❌ API key validation failed:\n{result.error_message}"
                validation_text.color = ft.Colors.RED_600
            
            validation_progress.visible = False
            self.page.update()
            
            await asyncio.sleep(3)
            self._close_dialog(self.validation_dialog)
            self._refresh_keys_list()
            
        except Exception as e:
            validation_text.value = f"❌ Validation error: {str(e)}"
            validation_text.color = ft.Colors.RED_600
            validation_progress.visible = False
            self.page.update()
            
            await asyncio.sleep(3)
            self._close_dialog(self.validation_dialog)
        
        finally:
            self.validation_in_progress = False
    
    def _toggle_key_active(self, key_info: APIKeyInfo):
        """Toggle API key active status"""
        new_active_status = not key_info.is_active
        
        success = self.api_key_service.update_api_key(
            provider=key_info.provider,
            key_name=key_info.key_name,
            is_active=new_active_status
        )
        
        if success:
            status = "activated" if new_active_status else "deactivated"
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"API key {status} successfully!"))
            )
            self._refresh_keys_list()
        else:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Failed to update API key status"))
            )
    
    def _delete_api_key(self, key_info: APIKeyInfo):
        """Delete API key with confirmation"""
        def confirm_delete(e):
            success = self.api_key_service.delete_api_key(
                provider=key_info.provider,
                key_name=key_info.key_name
            )
            
            if success:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("API key deleted successfully!"))
                )
                self._refresh_keys_list()
            else:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to delete API key"))
                )
            
            self._close_dialog(delete_dialog)
        
        delete_dialog = ft.AlertDialog(
            title=ft.Text("Confirm Delete"),
            content=ft.Text(
                f"Are you sure you want to delete the API key '{key_info.key_name}' "
                f"for {key_info.provider.value.title()}?\n\n"
                "This action cannot be undone."
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(delete_dialog)),
                ft.ElevatedButton(
                    "Delete",
                    on_click=confirm_delete,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)
                )
            ],
            modal=True
        )
        
        self.page.dialog = delete_dialog
        delete_dialog.open = True
        self.page.update()
    
    def _show_backup_dialog(self, e):
        """Show backup dialog"""
        backup_info = ft.Text(
            "This will export API key metadata (names, providers, status) but NOT the actual keys.\n"
            "The backup file can be used to restore key configurations on another system.",
            size=12
        )
        
        def create_backup(e):
            try:
                metadata = self.api_key_service.export_keys_metadata()
                
                # In a real implementation, this would open a file save dialog
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Backup created successfully! (Feature placeholder)"))
                )
                self._close_dialog(backup_dialog)
                
            except Exception as ex:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(f"Backup failed: {str(ex)}"))
                )
        
        backup_dialog = ft.AlertDialog(
            title=ft.Text("Backup API Keys"),
            content=ft.Container(
                content=ft.Column([
                    backup_info,
                    ft.Container(height=15),
                    ft.Text(f"Found {len(self.current_keys)} API keys to backup", weight=ft.FontWeight.BOLD)
                ]),
                width=400
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(backup_dialog)),
                ft.ElevatedButton("Create Backup", on_click=create_backup)
            ],
            modal=True
        )
        
        self.page.dialog = backup_dialog
        backup_dialog.open = True
        self.page.update()
    
    def _show_restore_dialog(self, e):
        """Show restore dialog"""
        restore_info = ft.Text(
            "Restore API key configurations from a backup file.\n"
            "This will restore key metadata but you'll need to re-enter the actual API keys.",
            size=12
        )
        
        def restore_backup(e):
            # In a real implementation, this would open a file picker
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Restore functionality placeholder - would open file picker"))
            )
            self._close_dialog(restore_dialog)
        
        restore_dialog = ft.AlertDialog(
            title=ft.Text("Restore API Keys"),
            content=ft.Container(
                content=ft.Column([
                    restore_info
                ]),
                width=400
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(restore_dialog)),
                ft.ElevatedButton("Select Backup File", on_click=restore_backup)
            ],
            modal=True
        )
        
        self.page.dialog = restore_dialog
        restore_dialog.open = True
        self.page.update()
    
    def _close_manager(self, e):
        """Close the API key manager"""
        if self.on_close:
            self.on_close()
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close a dialog"""
        dialog.open = False
        self.page.update()


def main():
    """Test the API key manager"""
    def test_app(page: ft.Page):
        page.title = "API Key Manager Test"
        page.window.width = 1200
        page.window.height = 800
        
        def on_close():
            print("Manager closed")
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("API Key Manager closed"))
            )
        
        manager = APIKeyManagerPage(page, on_close=on_close)
        page.add(manager.build())
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()