"""
About Dialog Component for Academic Auto Grader
Professional about dialog with application information, credits, and system details
"""

import flet as ft
import platform
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any
import subprocess

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.version import get_app_metadata, get_system_info, get_build_info


class AboutDialog:
    """About dialog component with comprehensive application information"""
    
    def __init__(
        self, 
        page: ft.Page,
        on_close: Optional[Callable[[], None]] = None
    ):
        """Initialize the about dialog
        
        Args:
            page: Flet page object
            on_close: Callback when dialog is closed
        """
        self.page = page
        self.on_close = on_close
        self.dialog = None
        
        # Get application metadata
        self.app_metadata = get_app_metadata()
        self.app_version = self.app_metadata['app']['version']
    
    def _get_system_info(self) -> Dict[str, str]:
        """Get system information for display"""
        return get_system_info()
    
    def _get_build_info(self) -> Dict[str, str]:
        """Get build information"""
        build_info = get_build_info()
        return {
            "Version": build_info['version'],
            "Commit": build_info.get('git_commit', 'Unknown'),
            "Branch": build_info.get('git_branch', 'Unknown'),
            "Build Type": build_info.get('build_type', 'Unknown'),
            "Build Date": build_info.get('build_date', 'Unknown')[:19] if build_info.get('build_date') else 'Unknown',
            "Bundled": "Yes" if build_info['is_bundled'] else "No"
        }
    
    def _create_info_section(self, title: str, info: Dict[str, str]) -> ft.Column:
        """Create an information section"""
        items = []
        
        # Section title
        items.append(
            ft.Text(
                title,
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_800
            )
        )
        items.append(ft.Container(height=5))
        
        # Information items
        for key, value in info.items():
            row = ft.Row([
                ft.Text(f"{key}:", weight=ft.FontWeight.W_500, width=100),
                ft.Text(value, selectable=True)
            ])
            items.append(row)
        
        return ft.Column(items, spacing=3)
    
    def _create_credits_section(self) -> ft.Column:
        """Create credits section"""
        credits = [
            {
                "category": "Development Team",
                "items": [
                    "Academic Auto Grader Team",
                    "Open Source Contributors"
                ]
            },
            {
                "category": "Key Technologies",
                "items": [
                    "Flet - Cross-platform GUI framework",
                    "OpenAI API - GPT language models",
                    "Anthropic API - Claude language models",
                    "PyInstaller - Application packaging",
                    "Python - Core programming language"
                ]
            },
            {
                "category": "Special Thanks",
                "items": [
                    "Educators who provided feedback",
                    "Beta testers and early adopters",
                    "Open source community"
                ]
            }
        ]
        
        items = []
        items.append(
            ft.Text(
                "Credits & Acknowledgments",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.BLUE_800
            )
        )
        items.append(ft.Container(height=10))
        
        for credit in credits:
            # Category
            items.append(
                ft.Text(
                    credit["category"],
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=ft.Colors.GREY_800
                )
            )
            
            # Items
            for item in credit["items"]:
                items.append(
                    ft.Container(
                        content=ft.Text(f"• {item}", size=12, color=ft.Colors.GREY_700),
                        margin=ft.margin.only(left=10, top=2)
                    )
                )
            
            items.append(ft.Container(height=8))
        
        return ft.Column(items, spacing=2)
    
    def build(self) -> ft.AlertDialog:
        """Build and return the about dialog"""
        
        # Header with logo and title
        header = ft.Container(
            content=ft.Row([
                # Logo placeholder
                ft.Icon(
                    ft.Icons.SCHOOL_ROUNDED,
                    size=48,
                    color=ft.Colors.BLUE_600
                ),
                ft.Container(width=15),
                ft.Column([
                    ft.Text(
                        self.app_metadata['app']['name'],
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800
                    ),
                    ft.Text(
                        f"Version {self.app_version}",
                        size=14,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Text(
                        self.app_metadata['app']['description'],
                        size=12,
                        color=ft.Colors.GREY_500
                    )
                ], spacing=2)
            ]),
            margin=ft.margin.only(bottom=20)
        )
        
        # System information
        system_info = self._get_system_info()
        build_info = self._get_build_info()
        
        # Create tabs for different sections
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            height=400,
            tabs=[
                ft.Tab(
                    text="About",
                    content=ft.Container(
                        content=ft.Column([
                            ft.Text(
                                "Academic Auto Grader is a comprehensive tool for automated "
                                "assignment grading using artificial intelligence. It supports "
                                "multiple programming languages, provides detailed feedback, "
                                "and integrates with popular learning management systems.",
                                size=13,
                                color=ft.Colors.GREY_700
                            ),
                            ft.Container(height=15),
                            ft.Text(
                                "Key Features:",
                                size=14,
                                weight=ft.FontWeight.W_600,
                                color=ft.Colors.GREY_800
                            ),
                            ft.Column([
                                ft.Text("• AI-powered code analysis and grading", size=12),
                                ft.Text("• Support for multiple programming languages", size=12),
                                ft.Text("• Detailed feedback and rubric-based scoring", size=12),
                                ft.Text("• GitHub integration for repository analysis", size=12),
                                ft.Text("• Export results to Excel, PDF, and other formats", size=12),
                                ft.Text("• Cross-platform desktop application", size=12),
                            ], spacing=2),
                            ft.Container(height=15),
                            ft.Text(
                                f"© 2024 {self.app_metadata['app']['author']}. All rights reserved.",
                                size=11,
                                color=ft.Colors.GREY_500,
                                italic=True
                            )
                        ], spacing=5),
                        padding=ft.padding.all(10)
                    )
                ),
                ft.Tab(
                    text="System Info",
                    content=ft.Container(
                        content=ft.Column([
                            self._create_info_section("System Information", system_info),
                            ft.Container(height=15),
                            self._create_info_section("Build Information", build_info),
                        ], spacing=5, scroll=ft.ScrollMode.AUTO),
                        padding=ft.padding.all(10)
                    )
                ),
                ft.Tab(
                    text="Credits",
                    content=ft.Container(
                        content=ft.Column([
                            self._create_credits_section()
                        ], scroll=ft.ScrollMode.AUTO),
                        padding=ft.padding.all(10)
                    )
                )
            ]
        )
        
        # Dialog content
        content = ft.Column([
            header,
            tabs
        ], width=500, height=500)
        
        # Create the dialog
        self.dialog = ft.AlertDialog(
            title=None,  # We'll use custom header
            content=content,
            actions=[
                ft.Row([
                    ft.TextButton(
                        "Visit Website",
                        on_click=self._open_website
                    ),
                    ft.TextButton(
                        "Report Issue",
                        on_click=self._open_issues
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Close",
                        on_click=self._close_dialog
                    )
                ])
            ],
            actions_alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
        
        return self.dialog
    
    def show(self):
        """Show the about dialog"""
        if self.page:
            self.dialog = self.build()
            self.page.dialog = self.dialog
            self.dialog.open = True
            self.page.update()
    
    def _close_dialog(self, e=None):
        """Close the dialog"""
        if self.dialog:
            self.dialog.open = False
            self.page.update()
        
        if self.on_close:
            self.on_close()
    
    def _open_website(self, e):
        """Open project website"""
        try:
            import webbrowser
            webbrowser.open(self.app_metadata['app']['url'])
        except Exception:
            pass
    
    def _open_issues(self, e):
        """Open issues page"""
        try:
            import webbrowser
            webbrowser.open(f"{self.app_metadata['app']['url']}/issues")
        except Exception:
            pass


def main():
    """Test the about dialog component"""
    def test_app(page: ft.Page):
        page.title = "About Dialog Test"
        page.window.width = 800
        page.window.height = 700
        
        def show_about():
            about = AboutDialog(page)
            about.show()
        
        # Main content
        page.add(
            ft.Container(
                content=ft.Column([
                    ft.Text("About Dialog Test", size=24, weight=ft.FontWeight.BOLD),
                    ft.Container(height=20),
                    ft.ElevatedButton(
                        "Show About Dialog",
                        icon=ft.Icons.INFO,
                        on_click=lambda e: show_about()
                    )
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
        )
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()