"""
Welcome Page Component

The main welcome screen for the Academic Auto Grader GUI application.
Provides application branding, overview, and navigation to main functionality.
"""

import flet as ft
from typing import Callable, Optional


class WelcomePage:
    """Welcome page component for the GUI application
    
    Displays application branding, version information, and provides
    navigation to the main grading workflow.
    """
    
    def __init__(self, page: ft.Page, on_get_started: Callable[[], None] = None):
        """Initialize the welcome page
        
        Args:
            page: Flet page object
            on_get_started: Callback function when user clicks "Get Started"
        """
        self.page = page
        self.on_get_started = on_get_started
        self.content = None
        
    def build(self) -> ft.Control:
        """Build and return the welcome page UI
        
        Returns:
            Flet control containing the welcome page
        """
        # Application header with branding
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    "🎓 Academic Auto Grader",
                    size=40,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Automated Assignment Grading with AI",
                    size=18,
                    color=ft.Colors.BLUE_600,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Version 1.0.0",
                    size=12,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=30)
        )
        
        # Features overview
        features = ft.Container(
            content=ft.Column([
                ft.Text(
                    "✨ Features",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=20),  # Spacer
                
                # Feature cards
                ft.Row([
                    self._create_feature_card(
                        "🤖", "AI-Powered Grading",
                        "Uses OpenAI GPT-4 and Anthropic Claude for intelligent assessment"
                    ),
                    self._create_feature_card(
                        "📊", "Detailed Analytics",
                        "Comprehensive rubric-based scoring with detailed feedback"
                    ),
                    self._create_feature_card(
                        "🔗", "GitHub Integration",
                        "Direct integration with GitHub repositories for code analysis"
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
                
                ft.Container(height=10),  # Spacer
                
                ft.Row([
                    self._create_feature_card(
                        "💰", "Cost Estimation",
                        "Transparent cost tracking and estimation before processing"
                    ),
                    self._create_feature_card(
                        "⚡", "Batch Processing",
                        "Grade multiple submissions efficiently with progress tracking"
                    ),
                    self._create_feature_card(
                        "📋", "Multiple Formats",
                        "Support for various assignment types and export formats"
                    )
                ], alignment=ft.MainAxisAlignment.CENTER, wrap=True)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=40)
        )
        
        # Getting started section
        getting_started = ft.Container(
            content=ft.Column([
                ft.Text(
                    "🚀 Ready to Get Started?",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=15),
                ft.Text(
                    "Select your assignment submissions and let AI handle the grading!",
                    size=16,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=25),
                
                # Main action button
                ft.ElevatedButton(
                    text="Get Started",
                    icon=ft.Icons.ARROW_FORWARD,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600,
                        padding=ft.padding.symmetric(horizontal=40, vertical=15)
                    ),
                    on_click=self._on_get_started_clicked
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=30)
        )
        
        # Quick links section
        quick_links = ft.Container(
            content=ft.Column([
                ft.Divider(color=ft.Colors.GREY_300),
                ft.Container(height=10),
                ft.Text(
                    "Quick Links",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=15),
                ft.Row([
                    ft.TextButton(
                        text="📖 Documentation",
                        on_click=lambda _: self._open_documentation()
                    ),
                    ft.VerticalDivider(width=1),
                    ft.TextButton(
                        text="⚙️ Settings",
                        on_click=lambda _: self._open_settings()
                    ),
                    ft.VerticalDivider(width=1),
                    ft.TextButton(
                        text="ℹ️ About",
                        on_click=lambda _: self._show_about_dialog()
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        )
        
        # Main content container
        self.content = ft.Container(
            content=ft.Column([
                header,
                features,
                getting_started,
                quick_links
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
            ),
            padding=ft.padding.all(40),
            alignment=ft.alignment.top_center,
            expand=True
        )
        
        return self.content
    
    def _create_feature_card(self, icon: str, title: str, description: str) -> ft.Container:
        """Create a feature card component
        
        Args:
            icon: Emoji icon for the feature
            title: Feature title
            description: Feature description
            
        Returns:
            Container with feature card
        """
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    icon,
                    size=32,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    title,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    description,
                    size=12,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8
            ),
            width=200,
            height=120,
            padding=ft.padding.all(15),
            margin=ft.margin.all(5),
            border_radius=10,
            bgcolor=ft.Colors.BLUE_50,
            border=ft.border.all(1, ft.Colors.BLUE_200)
        )
    
    def _on_get_started_clicked(self, e):
        """Handle get started button click"""
        if self.on_get_started:
            self.on_get_started()
        else:
            # Default behavior - show message
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Navigation not configured yet"),
                    action="OK"
                )
            )
    
    def _open_documentation(self):
        """Open documentation (placeholder)"""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Documentation will open here"),
                action="OK"
            )
        )
    
    def _open_settings(self):
        """Open settings (placeholder)"""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Settings will open here"),
                action="OK"
            )
        )
    
    def _show_about_dialog(self):
        """Show about dialog"""
        about_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("About Academic Auto Grader"),
            content=ft.Column([
                ft.Text("🎓 Academic Auto Grader v1.0.0"),
                ft.Text(""),
                ft.Text("An intelligent automated grading system for educational assignments."),
                ft.Text(""),
                ft.Text("Features:"),
                ft.Text("• AI-powered grading with GPT-4 and Claude"),
                ft.Text("• GitHub repository integration"),
                ft.Text("• Detailed rubric-based assessment"),
                ft.Text("• Cost tracking and estimation"),
                ft.Text("• Batch processing capabilities"),
                ft.Text(""),
                ft.Text("Built with Python and Flet for cross-platform compatibility."),
                ft.Text(""),
                ft.Text("© 2024 Academic Auto Grader")
            ], 
            height=300,
            scroll=ft.ScrollMode.AUTO
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda _: self._close_dialog())
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = about_dialog
        about_dialog.open = True
        self.page.update()
    
    def _close_dialog(self):
        """Close the current dialog"""
        if self.page.dialog:
            self.page.dialog.open = False
            self.page.update()


def main():
    """Test the welcome page component"""
    def test_app(page: ft.Page):
        page.title = "Academic Auto Grader - Welcome"
        page.window_width = 900
        page.window_height = 700
        page.window_center()
        
        def on_get_started():
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Get Started clicked! (Navigation would happen here)"),
                    action="OK"
                )
            )
        
        welcome_page = WelcomePage(page, on_get_started)
        page.add(welcome_page.build())
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()