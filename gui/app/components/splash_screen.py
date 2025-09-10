"""
Splash Screen Component for Academic Auto Grader
Displays during application startup with branding and loading progress
"""

import flet as ft
import asyncio
import sys
from pathlib import Path
from typing import Callable, Optional

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.version import get_app_metadata


class SplashScreen:
    """Splash screen component with loading animation and branding"""
    
    def __init__(
        self, 
        page: ft.Page,
        on_complete: Optional[Callable[[], None]] = None
    ):
        """Initialize the splash screen
        
        Args:
            page: Flet page object
            on_complete: Callback when splash screen finishes
        """
        self.page = page
        self.on_complete = on_complete
        
        # Get application metadata
        self.app_metadata = get_app_metadata()
        self.app_version = self.app_metadata['app']['version']
        
        # Loading state
        self.current_step = 0
        self.total_steps = 5
        self.loading_text = "Initializing..."
        self.progress_value = 0.0
        
        # UI components
        self.progress_bar = None
        self.status_text = None
        self.container = None
    
    def build(self) -> ft.Control:
        """Build and return the splash screen UI"""
        
        # Logo/Icon (using emoji for now, can be replaced with actual image)
        logo = ft.Container(
            content=ft.Icon(
                ft.Icons.SCHOOL_ROUNDED,
                size=120,
                color=ft.Colors.BLUE_600
            ),
            margin=ft.margin.only(bottom=30)
        )
        
        # Application title
        title = ft.Text(
            self.app_metadata['app']['name'],
            size=36,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_800,
            text_align=ft.TextAlign.CENTER
        )
        
        # Subtitle
        subtitle = ft.Text(
            self.app_metadata['app']['description'],
            size=16,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER
        )
        
        # Version
        version = ft.Text(
            f"Version {self.app_version}",
            size=12,
            color=ft.Colors.GREY_500,
            text_align=ft.TextAlign.CENTER
        )
        
        # Progress bar
        self.progress_bar = ft.ProgressBar(
            width=300,
            value=0,
            color=ft.Colors.BLUE_600,
            bgcolor=ft.Colors.GREY_200
        )
        
        # Status text
        self.status_text = ft.Text(
            self.loading_text,
            size=14,
            color=ft.Colors.GREY_700,
            text_align=ft.TextAlign.CENTER
        )
        
        # Loading animation (pulsing dots)
        loading_dots = ft.Row([
            ft.Container(
                width=8,
                height=8,
                bgcolor=ft.Colors.BLUE_400,
                border_radius=4,
                animate=ft.animation.Animation(1000, ft.AnimationCurve.EASE_IN_OUT)
            ),
            ft.Container(width=4),
            ft.Container(
                width=8,
                height=8,
                bgcolor=ft.Colors.BLUE_400,
                border_radius=4,
                animate=ft.animation.Animation(1000, ft.AnimationCurve.EASE_IN_OUT)
            ),
            ft.Container(width=4),
            ft.Container(
                width=8,
                height=8,
                bgcolor=ft.Colors.BLUE_400,
                border_radius=4,
                animate=ft.animation.Animation(1000, ft.AnimationCurve.EASE_IN_OUT)
            ),
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        # Copyright
        copyright = ft.Text(
            f"© 2024 {self.app_metadata['app']['author']}",
            size=10,
            color=ft.Colors.GREY_400,
            text_align=ft.TextAlign.CENTER
        )
        
        # Main content layout
        self.container = ft.Container(
            content=ft.Column([
                ft.Container(height=50),  # Top spacing
                logo,
                title,
                ft.Container(height=10),
                subtitle,
                ft.Container(height=20),
                version,
                ft.Container(height=50),
                self.progress_bar,
                ft.Container(height=20),
                self.status_text,
                ft.Container(height=10),
                loading_dots,
                ft.Container(expand=True),  # Push copyright to bottom
                copyright,
                ft.Container(height=30),  # Bottom spacing
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
            ),
            width=500,
            height=600,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.BLACK26,
                offset=ft.Offset(0, 4)
            ),
            padding=ft.padding.all(40),
            alignment=ft.alignment.center
        )
        
        # Center the splash screen
        return ft.Container(
            content=self.container,
            alignment=ft.alignment.center,
            expand=True,
            bgcolor=ft.Colors.BLACK38  # Semi-transparent overlay
        )
    
    async def start_loading(self):
        """Start the loading animation and process"""
        loading_steps = [
            ("Initializing application...", 0.2),
            ("Loading configuration...", 0.4),
            ("Setting up services...", 0.6),
            ("Preparing interface...", 0.8),
            ("Ready!", 1.0)
        ]
        
        for i, (step_text, progress) in enumerate(loading_steps):
            self.current_step = i + 1
            self.loading_text = step_text
            self.progress_value = progress
            
            # Update UI
            if self.status_text:
                self.status_text.value = step_text
            if self.progress_bar:
                self.progress_bar.value = progress
            
            if self.page:
                self.page.update()
            
            # Wait for step completion
            await asyncio.sleep(0.8)  # Adjust timing as needed
        
        # Brief pause at completion
        await asyncio.sleep(0.5)
        
        # Call completion callback
        if self.on_complete:
            self.on_complete()
    
    def show(self):
        """Show the splash screen and start loading"""
        if self.page:
            splash_content = self.build()
            self.page.add(splash_content)
            self.page.update()
            
            # Start loading asynchronously
            asyncio.create_task(self.start_loading())
    
    def hide(self):
        """Hide the splash screen"""
        if self.page and self.container:
            self.page.clean()  # Clear all content
            self.page.update()


def main():
    """Test the splash screen component"""
    def test_app(page: ft.Page):
        page.title = "Splash Screen Test"
        page.window.width = 800
        page.window.height = 700
        page.theme_mode = ft.ThemeMode.LIGHT
        
        def on_splash_complete():
            print("Splash screen completed!")
            splash.hide()
            
            # Show main content
            main_content = ft.Container(
                content=ft.Column([
                    ft.Text("🎉 Application Loaded!", size=24, weight=ft.FontWeight.BOLD),
                    ft.Text("Splash screen demonstration complete."),
                    ft.ElevatedButton("Show Splash Again", on_click=lambda e: show_splash())
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                alignment=ft.alignment.center,
                expand=True
            )
            page.add(main_content)
            page.update()
        
        def show_splash():
            page.clean()
            splash.show()
        
        splash = SplashScreen(page, on_complete=on_splash_complete)
        show_splash()
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()