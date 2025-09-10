"""
Assignment Selection Components

Provides assignment selection dropdown and display components for the GUI application.
Integrates with the ConfigService to load and display available assignments.
"""

import flet as ft
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.services.config_service import ConfigService


def create_assignment_selector(
    page: ft.Page,
    on_assignment_changed: Callable[[str], None] = None,
    width: int = 500
) -> Dict[str, Any]:
    """Create an assignment selection dropdown component
    
    Args:
        page: Flet page object
        on_assignment_changed: Callback when assignment selection changes
        width: Width of the component
        
    Returns:
        Dictionary with 'control' (UI component) and helper methods
    """
    
    # Initialize config service
    config_service = ConfigService()
    
    # State
    state = {
        'selected_assignment': None,
        'assignments': [],
        'is_loading': False,
        'error_message': None
    }
    
    # UI components
    dropdown = ft.Dropdown(
        label="Select Assignment",
        hint_text="Choose an assignment configuration...",
        width=width - 100,
        options=[],
        disabled=True
    )
    
    refresh_button = ft.IconButton(
        icon=ft.Icons.REFRESH,
        tooltip="Refresh assignments",
        disabled=False
    )
    
    loading_indicator = ft.ProgressRing(
        width=20,
        height=20,
        stroke_width=2,
        visible=False
    )
    
    error_display = ft.Container(
        content=ft.Text("", size=11, color=ft.Colors.RED_700),
        padding=ft.padding.only(left=10, top=5),
        visible=False
    )
    
    assignment_details = ft.Container(
        content=ft.Column([
            ft.Text("Assignment Details", size=14, weight=ft.FontWeight.BOLD),
            ft.Text("Select an assignment to see details", size=12, color=ft.Colors.GREY_600)
        ], spacing=5),
        padding=ft.padding.all(15),
        border=ft.border.all(1, ft.Colors.GREY_300),
        border_radius=5,
        bgcolor=ft.Colors.GREY_50,
        visible=False,
        width=width
    )
    
    def load_assignments():
        """Load assignments from config service"""
        state['is_loading'] = True
        state['error_message'] = None
        loading_indicator.visible = True
        dropdown.disabled = True
        refresh_button.disabled = True
        error_display.visible = False
        
        page.update()
        
        try:
            assignments = config_service.load_assignments()
            state['assignments'] = assignments
            
            if assignments:
                # Update dropdown options
                dropdown.options = [
                    ft.dropdown.Option(
                        key=assignment['name'],
                        text=f"{assignment['display_name']} ({assignment['type'].replace('_', ' ').title()})"
                    )
                    for assignment in assignments
                ]
                dropdown.disabled = False
                state['error_message'] = None
            else:
                dropdown.options = []
                state['error_message'] = "No assignments found. Please check your assignments directory."
                error_display.content = ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE, size=16),
                    ft.Text(state['error_message'], size=11, color=ft.Colors.ORANGE_700)
                ], spacing=5)
                error_display.visible = True
                
        except Exception as e:
            state['error_message'] = f"Error loading assignments: {str(e)}"
            dropdown.options = []
            error_display.content = ft.Row([
                ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=16),
                ft.Text(state['error_message'], size=11, color=ft.Colors.RED_700)
            ], spacing=5)
            error_display.visible = True
        
        finally:
            state['is_loading'] = False
            loading_indicator.visible = False
            refresh_button.disabled = False
            page.update()
    
    def on_dropdown_change(e):
        """Handle dropdown selection change"""
        if e.control.value:
            assignment_name = e.control.value
            state['selected_assignment'] = assignment_name
            update_assignment_details(assignment_name)
            
            if on_assignment_changed:
                on_assignment_changed(assignment_name)
        else:
            state['selected_assignment'] = None
            assignment_details.visible = False
            page.update()
    
    def update_assignment_details(assignment_name: str):
        """Update the assignment details display"""
        try:
            # Find assignment in loaded assignments
            assignment = next(
                (a for a in state['assignments'] if a['name'] == assignment_name),
                None
            )
            
            if assignment:
                # Create detailed view
                details_content = ft.Column([
                    # Header
                    ft.Row([
                        ft.Text("📋", size=20),
                        ft.Column([
                            ft.Text(
                                assignment['display_name'],
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_800
                            ),
                            ft.Text(
                                f"Type: {assignment['type'].replace('_', ' ').title()}",
                                size=12,
                                color=ft.Colors.GREY_700
                            )
                        ], spacing=2, expand=True)
                    ], spacing=10),
                    
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    
                    # Key information
                    ft.Row([
                        ft.Column([
                            ft.Text("📊 Points", size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(str(assignment['total_points']), size=12)
                        ], spacing=2),
                        ft.VerticalDivider(width=1),
                        ft.Column([
                            ft.Text("🔧 Functions", size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(str(assignment['required_functions']), size=12)
                        ], spacing=2),
                        ft.VerticalDivider(width=1),
                        ft.Column([
                            ft.Text("📋 Criteria", size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(str(assignment['rubric_criteria']), size=12)
                        ], spacing=2),
                        ft.VerticalDivider(width=1),
                        ft.Column([
                            ft.Text("🔗 GitHub", size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(
                                "✅ Enabled" if assignment['github_enabled'] else "❌ Disabled",
                                size=12,
                                color=ft.Colors.GREEN if assignment['github_enabled'] else ft.Colors.RED
                            )
                        ], spacing=2)
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                    
                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                    
                    # Description
                    ft.Column([
                        ft.Text("Description", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(
                            assignment['description'],
                            size=11,
                            color=ft.Colors.GREY_700
                        )
                    ], spacing=5)
                ], spacing=10)
                
                assignment_details.content = details_content
                assignment_details.bgcolor = ft.Colors.BLUE_50
                assignment_details.border = ft.border.all(1, ft.Colors.BLUE_200)
                assignment_details.visible = True
            else:
                assignment_details.visible = False
                
        except Exception as e:
            # Show error in details
            assignment_details.content = ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=16),
                    ft.Text(f"Error loading assignment details: {str(e)}", size=11, color=ft.Colors.RED_700)
                ], spacing=5)
            ])
            assignment_details.bgcolor = ft.Colors.RED_50
            assignment_details.border = ft.border.all(1, ft.Colors.RED_200)
            assignment_details.visible = True
        
        page.update()
    
    def on_refresh_clicked(e):
        """Handle refresh button click"""
        load_assignments()
    
    def get_selected_assignment():
        """Get the currently selected assignment name"""
        return state['selected_assignment']
    
    def get_selected_assignment_data():
        """Get the full data for the selected assignment"""
        if state['selected_assignment']:
            return next(
                (a for a in state['assignments'] if a['name'] == state['selected_assignment']),
                None
            )
        return None
    
    def set_assignment(assignment_name: str):
        """Programmatically set the selected assignment"""
        if assignment_name in [opt.key for opt in dropdown.options]:
            dropdown.value = assignment_name
            state['selected_assignment'] = assignment_name
            update_assignment_details(assignment_name)
            
            if on_assignment_changed:
                on_assignment_changed(assignment_name)
            
            page.update()
    
    def get_assignments_count():
        """Get the number of available assignments"""
        return len(state['assignments'])
    
    def has_assignments():
        """Check if any assignments are available"""
        return len(state['assignments']) > 0
    
    # Set up event handlers
    dropdown.on_change = on_dropdown_change
    refresh_button.on_click = on_refresh_clicked
    
    # Main layout
    control = ft.Column([
        # Selection row
        ft.Row([
            dropdown,
            refresh_button,
            loading_indicator
        ], alignment=ft.MainAxisAlignment.START, spacing=10),
        
        # Error display
        error_display,
        
        # Assignment details
        assignment_details
    ], 
    width=width,
    spacing=10
    )
    
    # Load assignments on initialization
    load_assignments()
    
    return {
        'control': control,
        'get_selected_assignment': get_selected_assignment,
        'get_selected_assignment_data': get_selected_assignment_data,
        'set_assignment': set_assignment,
        'refresh_assignments': load_assignments,
        'get_assignments_count': get_assignments_count,
        'has_assignments': has_assignments,
        'is_loading': lambda: state['is_loading'],
        'get_error': lambda: state['error_message']
    }


def create_simple_assignment_dropdown(
    page: ft.Page,
    on_assignment_changed: Callable[[str], None] = None,
    width: int = 300
) -> Dict[str, Any]:
    """Create a simple assignment dropdown without details
    
    Args:
        page: Flet page object
        on_assignment_changed: Callback when assignment selection changes
        width: Width of the component
        
    Returns:
        Dictionary with 'control' (UI component) and helper methods
    """
    
    # Initialize config service
    config_service = ConfigService()
    
    # State
    state = {
        'selected_assignment': None,
        'assignments': []
    }
    
    # UI components
    dropdown = ft.Dropdown(
        label="Assignment",
        hint_text="Select assignment...",
        width=width,
        options=[]
    )
    
    def load_assignments():
        """Load assignments into dropdown"""
        try:
            assignments = config_service.load_assignments()
            state['assignments'] = assignments
            
            dropdown.options = [
                ft.dropdown.Option(
                    key=assignment['name'],
                    text=assignment['display_name']
                )
                for assignment in assignments
            ]
            
            page.update()
            
        except Exception as e:
            print(f"Error loading assignments: {e}")
    
    def on_dropdown_change(e):
        """Handle dropdown selection change"""
        if e.control.value:
            state['selected_assignment'] = e.control.value
            if on_assignment_changed:
                on_assignment_changed(e.control.value)
        else:
            state['selected_assignment'] = None
    
    # Set up event handler
    dropdown.on_change = on_dropdown_change
    
    # Load assignments on initialization
    load_assignments()
    
    return {
        'control': dropdown,
        'get_selected_assignment': lambda: state['selected_assignment'],
        'refresh_assignments': load_assignments,
        'has_assignments': lambda: len(state['assignments']) > 0
    }


def main():
    """Test the assignment selector components"""
    def test_app(page: ft.Page):
        page.title = "Assignment Selector Test"
        page.window.width = 800
        page.window.height = 700
        
        # Status display
        status_text = ft.Text("No assignment selected", size=14)
        
        def on_assignment_changed(assignment_name):
            print(f"Selected assignment: {assignment_name}")
            status_text.value = f"Selected: {assignment_name}"
            
            # Show assignment data
            assignment_data = selector['get_selected_assignment_data']()
            if assignment_data:
                print(f"Assignment data: {assignment_data['display_name']}")
            
            page.update()
        
        # Test components
        selector = create_assignment_selector(page, on_assignment_changed)
        simple_selector = create_simple_assignment_dropdown(page, on_assignment_changed, width=250)
        
        # Layout
        page.add(
            ft.Column([
                ft.Text("Assignment Selector Test", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                ft.Text("Full Assignment Selector:", size=16, weight=ft.FontWeight.BOLD),
                selector['control'],
                
                ft.Container(height=20),
                
                ft.Text("Simple Assignment Dropdown:", size=16, weight=ft.FontWeight.BOLD),
                simple_selector['control'],
                
                ft.Container(height=20),
                ft.Divider(),
                
                ft.Text("Status:", size=16, weight=ft.FontWeight.BOLD),
                status_text,
                
                ft.Container(height=20),
                ft.Row([
                    ft.ElevatedButton(
                        "Refresh Assignments",
                        on_click=lambda _: selector['refresh_assignments']()
                    ),
                    ft.ElevatedButton(
                        "Check Count",
                        on_click=lambda _: print(f"Assignments count: {selector['get_assignments_count']()}")
                    )
                ], spacing=10)
            ],
            spacing=10,
            expand=True,
            scroll=ft.ScrollMode.AUTO
            )
        )
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()