"""
File Picker Components

Provides file and folder selection components for the GUI application.
Includes validation and user feedback for selected paths.
"""

import flet as ft
import os
from pathlib import Path
from typing import Callable, Optional, Dict, Any


def create_file_picker(
    page: ft.Page,
    label: str,
    pick_files: bool = True,
    pick_folders: bool = False,
    file_type: ft.FilePickerFileType = ft.FilePickerFileType.ANY,
    allowed_extensions: list = None,
    on_selection_changed: Callable[[str], None] = None,
    validator: Callable[[str], Dict[str, Any]] = None,
    width: int = 400
) -> Dict[str, Any]:
    """Create a file picker component
    
    Args:
        page: Flet page object
        label: Label for the picker button
        pick_files: Whether to allow file selection
        pick_folders: Whether to allow folder selection
        file_type: Type of files to filter
        allowed_extensions: List of allowed file extensions
        on_selection_changed: Callback when selection changes
        validator: Function to validate selected path
        width: Width of the component
        
    Returns:
        Dictionary with 'control' (UI component) and helper methods
    """
    
    # State
    state = {
        'selected_path': "",
        'validation_result': None
    }
    
    # UI components
    path_display = ft.Container(
        content=ft.Text(
            "No file selected",
            size=12,
            color=ft.Colors.GREY_600,
            italic=True
        ),
        padding=ft.padding.symmetric(horizontal=10, vertical=5),
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=5,
        bgcolor=ft.Colors.GREY_50,
        expand=True
    )
    
    clear_button = ft.IconButton(
        icon=ft.Icons.CLEAR,
        tooltip="Clear selection",
        visible=False
    )
    
    validation_display = ft.Container(
        content=ft.Text("", size=11),
        padding=ft.padding.only(left=10, top=5),
        visible=False
    )
    
    def set_path(path: str):
        """Set the selected path and update UI"""
        state['selected_path'] = path
        
        # Update path display
        if path:
            # Show shortened path if too long
            display_path = path
            if len(path) > 50:
                path_obj = Path(path)
                display_path = f".../{path_obj.parent.name}/{path_obj.name}"
            
            path_display.content = ft.Text(
                display_path,
                size=12,
                color=ft.Colors.BLACK87,
                weight=ft.FontWeight.NORMAL
            )
            path_display.bgcolor = ft.Colors.WHITE
            path_display.border = ft.border.all(1, ft.Colors.GREEN_300)
            clear_button.visible = True
        else:
            path_display.content = ft.Text(
                "No file selected",
                size=12,
                color=ft.Colors.GREY_600,
                italic=True
            )
            path_display.bgcolor = ft.Colors.GREY_50
            path_display.border = ft.border.all(1, ft.Colors.GREY_300)
            clear_button.visible = False
        
        # Validate path
        validate_path()
        
        # Update UI
        page.update()
        
        # Notify callback
        if on_selection_changed:
            on_selection_changed(path)
    
    def validate_path():
        """Validate the selected path"""
        if not validator or not state['selected_path']:
            validation_display.visible = False
            return
        
        try:
            state['validation_result'] = validator(state['selected_path'])
            
            if state['validation_result']:
                is_valid = state['validation_result'].get('valid', False)
                message = state['validation_result'].get('message', '')
                
                if message:
                    validation_display.content = ft.Row([
                        ft.Icon(
                            ft.Icons.CHECK_CIRCLE if is_valid else ft.Icons.ERROR,
                            color=ft.Colors.GREEN if is_valid else ft.Colors.RED,
                            size=16
                        ),
                        ft.Text(
                            message,
                            size=11,
                            color=ft.Colors.GREEN_700 if is_valid else ft.Colors.RED_700
                        )
                    ], spacing=5)
                    validation_display.visible = True
                else:
                    validation_display.visible = False
            else:
                validation_display.visible = False
                
        except Exception as e:
            validation_display.content = ft.Row([
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=16),
                ft.Text(f"Validation error: {str(e)}", size=11, color=ft.Colors.RED_700)
            ], spacing=5)
            validation_display.visible = True
    
    def on_file_result(e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        if e.files:
            selected_file = e.files[0]
            set_path(selected_file.path)
    
    def on_folder_result(e: ft.FilePickerResultEvent):
        """Handle folder picker result"""
        if e.path:
            set_path(e.path)
    
    def on_select_clicked(e):
        """Handle select button click"""
        if pick_folders:
            file_picker.get_directory_path(dialog_title=f"Select {label}")
        else:
            file_picker.pick_files(
                dialog_title=f"Select {label}",
                file_type=file_type,
                allowed_extensions=allowed_extensions or [],
                allow_multiple=False
            )
    
    def on_clear_clicked(e):
        """Handle clear button click"""
        set_path("")
    
    # Create file picker dialog
    if pick_folders:
        file_picker = ft.FilePicker(on_result=on_folder_result)
    else:
        file_picker = ft.FilePicker(on_result=on_file_result)
    
    # Selection button
    select_button = ft.ElevatedButton(
        text=label,
        icon=ft.Icons.FOLDER_OPEN if pick_folders else ft.Icons.FILE_OPEN,
        on_click=on_select_clicked,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_600
        )
    )
    
    clear_button.on_click = on_clear_clicked
    
    # Main layout
    control = ft.Column([
        # Hidden file picker
        file_picker,
        
        # Selection row
        ft.Row([
            select_button,
            ft.Container(width=10),  # Spacer
            path_display,
            clear_button
        ], alignment=ft.MainAxisAlignment.START),
        
        # Validation feedback
        validation_display
    ], 
    width=width,
    spacing=5
    )
    
    return {
        'control': control,
        'set_path': set_path,
        'get_path': lambda: state['selected_path'],
        'get_validation_result': lambda: state['validation_result'],
        'is_valid': lambda: state['validation_result'].get('valid', False) if state['validation_result'] else bool(state['selected_path'])
    }
def validate_submissions_folder(path: str) -> Dict[str, Any]:
    """Validate submissions folder"""
    if not path:
        return {'valid': False, 'message': 'Please select a folder'}
    
    if not os.path.exists(path):
        return {'valid': False, 'message': 'Folder does not exist'}
    
    if not os.path.isdir(path):
        return {'valid': False, 'message': 'Path is not a directory'}
    
    try:
        # Count ZIP files
        zip_files = [f for f in os.listdir(path) if f.lower().endswith('.zip')]
        zip_count = len(zip_files)
        
        if zip_count == 0:
            return {
                'valid': False, 
                'message': 'No ZIP files found in folder',
                'count': 0
            }
        else:
            return {
                'valid': True, 
                'message': f'Found {zip_count} ZIP file{"s" if zip_count != 1 else ""}',
                'count': zip_count
            }
            
    except PermissionError:
        return {'valid': False, 'message': 'Permission denied accessing folder'}
    except Exception as e:
        return {'valid': False, 'message': f'Error reading folder: {str(e)}'}


def validate_roster_file(path: str) -> Dict[str, Any]:
    """Validate roster CSV file"""
    if not path:
        return {'valid': True, 'message': 'Roster file is optional'}
    
    if not os.path.exists(path):
        return {'valid': False, 'message': 'File does not exist'}
    
    if not path.lower().endswith('.csv'):
        return {'valid': False, 'message': 'File must be a CSV file'}
    
    try:
        # Try to read first few lines
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()[:5]
        
        if not lines:
            return {'valid': False, 'message': 'CSV file is empty'}
        
        # Check for common CSV header patterns
        first_line = lines[0].strip().lower()
        if any(header in first_line for header in ['student', 'name', 'id', 'email']):
            return {
                'valid': True, 
                'message': f'Valid CSV file ({len(lines)} lines preview)',
                'lines': len(lines)
            }
        else:
            return {
                'valid': True, 
                'message': f'CSV file loaded ({len(lines)} lines, verify headers)',
                'lines': len(lines),
                'warning': 'No standard headers detected'
            }
            
    except UnicodeDecodeError:
        return {'valid': False, 'message': 'File encoding error (not UTF-8)'}
    except Exception as e:
        return {'valid': False, 'message': f'Error reading file: {str(e)}'}


def create_submissions_folder_picker(page: ft.Page, on_selection_changed: Callable[[str], None] = None):
    """Create a submissions folder picker"""
    return create_file_picker(
        page=page,
        label="📁 Select Submissions Folder",
        pick_folders=True,
        on_selection_changed=on_selection_changed,
        validator=validate_submissions_folder,
        width=500
    )


def create_roster_file_picker(page: ft.Page, on_selection_changed: Callable[[str], None] = None):
    """Create a roster file picker"""
    return create_file_picker(
        page=page,
        label="📋 Select Roster File (Optional)",
        pick_files=True,
        file_type=ft.FilePickerFileType.CUSTOM,
        allowed_extensions=['csv'],
        on_selection_changed=on_selection_changed,
        validator=validate_roster_file,
        width=500
    )


def main():
    """Test the file picker components"""
    def test_app(page: ft.Page):
        page.title = "File Picker Test"
        page.window.width = 800
        page.window.height = 600
        
        # Status display
        status_text = ft.Text("Select files to see validation results", size=14)
        
        def update_status():
            submissions_valid = submissions_picker['is_valid']()
            roster_valid = roster_picker['is_valid']()
            
            status_parts = []
            submissions_path = submissions_picker['get_path']()
            roster_path = roster_picker['get_path']()
            
            if submissions_path:
                status_parts.append(f"Submissions: {'✅' if submissions_valid else '❌'}")
            if roster_path:
                status_parts.append(f"Roster: {'✅' if roster_valid else '❌'}")
            
            if status_parts:
                status_text.value = " | ".join(status_parts)
            else:
                status_text.value = "No files selected"
            
            page.update()
        
        def on_submissions_changed(path):
            print(f"Submissions folder: {path}")
            update_status()
        
        def on_roster_changed(path):
            print(f"Roster file: {path}")
            update_status()
        
        # Test components
        submissions_picker = create_submissions_folder_picker(page, on_submissions_changed)
        roster_picker = create_roster_file_picker(page, on_roster_changed)
        
        # Layout
        page.add(
            ft.Column([
                ft.Text("File Picker Components Test", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                ft.Text("Select Submissions Folder:", size=16, weight=ft.FontWeight.BOLD),
                submissions_picker['control'],
                
                ft.Container(height=20),
                
                ft.Text("Select Roster File:", size=16, weight=ft.FontWeight.BOLD),
                roster_picker['control'],
                
                ft.Container(height=20),
                ft.Divider(),
                
                ft.Text("Status:", size=16, weight=ft.FontWeight.BOLD),
                status_text,
                
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Test Validation",
                    on_click=lambda _: update_status()
                )
            ],
            spacing=10,
            expand=True
            )
        )
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()