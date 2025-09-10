"""
File Selection Page Component

Combined page for selecting submissions folder, roster file, and assignment.
Integrates file pickers and assignment selector into a cohesive workflow.
"""

import flet as ft
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.components.file_picker import create_submissions_folder_picker, create_roster_file_picker
from app.components.assignment_selector import create_assignment_selector


class FileSelectionPage:
    """File selection page component
    
    Provides a comprehensive interface for selecting all required files
    and configuration for the grading process.
    """
    
    def __init__(
        self, 
        page: ft.Page, 
        on_selection_complete: Callable[[Dict[str, Any]], None] = None,
        on_next_step: Callable[[], None] = None
    ):
        """Initialize the file selection page
        
        Args:
            page: Flet page object
            on_selection_complete: Callback when all selections are complete
            on_next_step: Callback to proceed to next step
        """
        self.page = page
        self.on_selection_complete = on_selection_complete
        self.on_next_step = on_next_step
        
        # Component instances
        self.submissions_picker = None
        self.roster_picker = None
        self.assignment_selector = None
        
        # State
        self.state = {
            'submissions_folder': '',
            'roster_file': '',
            'selected_assignment': '',
            'all_valid': False
        }
        
        # UI components
        self.status_card = None
        self.next_button = None
        self.content = None
    
    def build(self) -> ft.Control:
        """Build and return the file selection page UI"""
        
        # Page header
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    "📁 File Selection",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Select your assignment submissions, roster file, and configuration",
                    size=16,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=30)
        )
        
        # Create file selection components
        self.submissions_picker = create_submissions_folder_picker(
            self.page, 
            self._on_submissions_changed
        )
        
        self.roster_picker = create_roster_file_picker(
            self.page,
            self._on_roster_changed
        )
        
        self.assignment_selector = create_assignment_selector(
            self.page,
            self._on_assignment_changed
        )
        
        # Selection sections
        sections = ft.Column([
            # Assignment selection
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.ASSIGNMENT, color=ft.Colors.BLUE_600, size=24),
                        ft.Text(
                            "Step 1: Select Assignment Configuration",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_800
                        )
                    ], spacing=10),
                    ft.Text(
                        "Choose the assignment configuration that matches your submissions.",
                        size=12,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Container(height=10),
                    self.assignment_selector['control']
                ], spacing=5),
                padding=ft.padding.all(20),
                border=ft.border.all(1, ft.Colors.BLUE_200),
                border_radius=10,
                bgcolor=ft.Colors.BLUE_50
            ),
            
            ft.Container(height=20),
            
            # Submissions folder selection
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.FOLDER_ZIP, color=ft.Colors.GREEN_600, size=24),
                        ft.Text(
                            "Step 2: Select Submissions Folder",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREEN_800
                        )
                    ], spacing=10),
                    ft.Text(
                        "Choose the folder containing student submission ZIP files.",
                        size=12,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Container(height=10),
                    self.submissions_picker['control']
                ], spacing=5),
                padding=ft.padding.all(20),
                border=ft.border.all(1, ft.Colors.GREEN_200),
                border_radius=10,
                bgcolor=ft.Colors.GREEN_50
            ),
            
            ft.Container(height=20),
            
            # Roster file selection
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.ORANGE_600, size=24),
                        ft.Text(
                            "Step 3: Select Roster File (Optional)",
                            size=18,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.ORANGE_800
                        )
                    ], spacing=10),
                    ft.Text(
                        "Optionally select a CSV roster file to filter submissions by enrolled students.",
                        size=12,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Container(height=10),
                    self.roster_picker['control']
                ], spacing=5),
                padding=ft.padding.all(20),
                border=ft.border.all(1, ft.Colors.ORANGE_200),
                border_radius=10,
                bgcolor=ft.Colors.ORANGE_50
            )
        ], spacing=0)
        
        # Status and action section
        self.status_card = ft.Container(
            content=ft.Column([
                ft.Text(
                    "📋 Selection Status",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_800
                ),
                ft.Container(height=10),
                ft.Text(
                    "Please complete all required selections above.",
                    size=12,
                    color=ft.Colors.GREY_600
                )
            ], spacing=5),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            bgcolor=ft.Colors.GREY_50,
            width=600
        )
        
        self.next_button = ft.ElevatedButton(
            text="Continue to Configuration",
            icon=ft.Icons.ARROW_FORWARD,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600,
                padding=ft.padding.symmetric(horizontal=30, vertical=15)
            ),
            disabled=True,
            on_click=self._on_next_clicked
        )
        
        action_section = ft.Container(
            content=ft.Column([
                self.status_card,
                ft.Container(height=20),
                ft.Row([
                    self.next_button
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(top=30)
        )
        
        # Main content
        self.content = ft.Container(
            content=ft.Column([
                header,
                sections,
                action_section
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
            ),
            padding=ft.padding.all(40),
            alignment=ft.alignment.top_center,
            expand=True
        )
        
        # Initial status update
        self._update_status()
        
        return self.content
    
    def _on_submissions_changed(self, path: str):
        """Handle submissions folder selection change"""
        self.state['submissions_folder'] = path
        self._update_status()
    
    def _on_roster_changed(self, path: str):
        """Handle roster file selection change"""
        self.state['roster_file'] = path
        self._update_status()
    
    def _on_assignment_changed(self, assignment_name: str):
        """Handle assignment selection change"""
        self.state['selected_assignment'] = assignment_name
        self._update_status()
    
    def _update_status(self):
        """Update the status display and next button"""
        # Check validation states
        submissions_valid = self.submissions_picker['is_valid']() if self.submissions_picker else False
        roster_valid = self.roster_picker['is_valid']() if self.roster_picker else True  # Optional
        assignment_selected = bool(self.state['selected_assignment'])
        
        # Build status content
        status_items = []
        
        # Assignment status
        if assignment_selected:
            assignment_data = self.assignment_selector['get_selected_assignment_data']()
            assignment_name = assignment_data['display_name'] if assignment_data else self.state['selected_assignment']
            status_items.append(
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=16),
                    ft.Text(f"Assignment: {assignment_name}", size=12)
                ], spacing=5)
            )
        else:
            status_items.append(
                ft.Row([
                    ft.Icon(ft.Icons.RADIO_BUTTON_UNCHECKED, color=ft.Colors.GREY, size=16),
                    ft.Text("Assignment: Not selected", size=12, color=ft.Colors.GREY_600)
                ], spacing=5)
            )
        
        # Submissions status
        if submissions_valid:
            submissions_result = self.submissions_picker['get_validation_result']()
            count = submissions_result.get('count', 0) if submissions_result else 0
            status_items.append(
                ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=16),
                    ft.Text(f"Submissions: {count} ZIP files found", size=12)
                ], spacing=5)
            )
        else:
            status_items.append(
                ft.Row([
                    ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED, size=16),
                    ft.Text("Submissions: Folder not selected or invalid", size=12, color=ft.Colors.RED_700)
                ], spacing=5)
            )
        
        # Roster status
        if self.state['roster_file']:
            if roster_valid:
                status_items.append(
                    ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN, size=16),
                        ft.Text("Roster: CSV file loaded", size=12)
                    ], spacing=5)
                )
            else:
                status_items.append(
                    ft.Row([
                        ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE, size=16),
                        ft.Text("Roster: File selected but invalid", size=12, color=ft.Colors.ORANGE_700)
                    ], spacing=5)
                )
        else:
            status_items.append(
                ft.Row([
                    ft.Icon(ft.Icons.INFO, color=ft.Colors.BLUE, size=16),
                    ft.Text("Roster: No file selected (optional)", size=12, color=ft.Colors.BLUE_700)
                ], spacing=5)
            )
        
        # Overall status
        self.state['all_valid'] = assignment_selected and submissions_valid and roster_valid
        
        if self.state['all_valid']:
            status_header = ft.Text(
                "✅ Ready to Continue",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREEN_800
            )
            self.status_card.bgcolor = ft.Colors.GREEN_50
            self.status_card.border = ft.border.all(1, ft.Colors.GREEN_300)
            self.next_button.disabled = False
        else:
            status_header = ft.Text(
                "📋 Selection Status",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREY_800
            )
            self.status_card.bgcolor = ft.Colors.GREY_50
            self.status_card.border = ft.border.all(1, ft.Colors.GREY_300)
            self.next_button.disabled = True
        
        # Update status card content
        self.status_card.content = ft.Column([
            status_header,
            ft.Container(height=10),
            ft.Column(status_items, spacing=8)
        ], spacing=5)
        
        # Update page
        self.page.update()
        
        # Notify callback
        if self.on_selection_complete and self.state['all_valid']:
            selection_data = {
                'submissions_folder': self.state['submissions_folder'],
                'roster_file': self.state['roster_file'],
                'assignment_name': self.state['selected_assignment'],
                'assignment_data': self.assignment_selector['get_selected_assignment_data']()
            }
            self.on_selection_complete(selection_data)
    
    def _on_next_clicked(self, e):
        """Handle next button click"""
        if self.state['all_valid'] and self.on_next_step:
            self.on_next_step()
    
    def get_selection_data(self) -> Dict[str, Any]:
        """Get the current selection data"""
        return {
            'submissions_folder': self.state['submissions_folder'],
            'roster_file': self.state['roster_file'],
            'assignment_name': self.state['selected_assignment'],
            'assignment_data': self.assignment_selector['get_selected_assignment_data']() if self.assignment_selector else None,
            'valid': self.state['all_valid']
        }


def main():
    """Test the file selection page"""
    def test_app(page: ft.Page):
        page.title = "File Selection Page Test"
        page.window.width = 900
        page.window.height = 800
        
        def on_selection_complete(data):
            print(f"Selection complete: {data}")
        
        def on_next_step():
            print("Proceeding to next step!")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Proceeding to configuration..."),
                    action="OK"
                )
            )
        
        file_selection_page = FileSelectionPage(
            page, 
            on_selection_complete,
            on_next_step
        )
        
        page.add(file_selection_page.build())
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()