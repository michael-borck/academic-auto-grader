"""
Page Router for GUI Application

Manages navigation between different pages in the application.
"""

import flet as ft
from enum import Enum
from typing import Dict, Callable, Any, Optional


class PageRoute(Enum):
    """Available page routes"""
    WELCOME = "welcome"
    FILE_SELECTION = "file_selection"
    CONFIGURATION = "configuration"
    PROCESSING = "processing"
    RESULTS = "results"
    SETTINGS = "settings"
    ASSIGNMENT_EDITOR = "assignment_editor"
    ASSIGNMENT_WIZARD = "assignment_wizard"
    CONFIG_VALIDATOR = "config_validator"
    API_KEY_MANAGER = "api_key_manager"
    USER_PREFERENCES = "user_preferences"
    APPLICATION_SETTINGS = "application_settings"


class Router:
    """Simple page router for the GUI application"""
    
    def __init__(self, page: ft.Page):
        """Initialize the router
        
        Args:
            page: Flet page object
        """
        self.page = page
        self.current_route = PageRoute.WELCOME
        self.pages: Dict[PageRoute, Callable] = {}
        self.page_instances: Dict[PageRoute, Any] = {}
        
        # Navigation history
        self.history = [PageRoute.WELCOME]
        
    def register_page(self, route: PageRoute, page_factory: Callable):
        """Register a page factory function
        
        Args:
            route: Page route enum
            page_factory: Function that returns a page instance
        """
        self.pages[route] = page_factory
        
    def navigate_to(self, route: PageRoute, **kwargs):
        """Navigate to a specific page
        
        Args:
            route: Target page route
            **kwargs: Additional parameters to pass to the page
        """
        if route not in self.pages:
            print(f"Warning: Route {route} not registered")
            return
            
        # Add to history if it's a new route
        if route != self.current_route:
            self.history.append(route)
            
        self.current_route = route
        
        # Clear current page content
        self.page.controls.clear()
        
        # Create or get page instance
        if route not in self.page_instances:
            self.page_instances[route] = self.pages[route](**kwargs)
        
        page_instance = self.page_instances[route]
        
        # Add page content
        if hasattr(page_instance, 'build'):
            content = page_instance.build()
        else:
            content = page_instance
            
        self.page.add(content)
        self.page.update()
        
    def go_back(self):
        """Navigate back to the previous page"""
        if len(self.history) > 1:
            # Remove current page from history
            self.history.pop()
            # Navigate to previous page
            previous_route = self.history[-1]
            self.navigate_to(previous_route)
    
    def get_current_route(self) -> PageRoute:
        """Get the current active route"""
        return self.current_route
    
    def can_go_back(self) -> bool:
        """Check if we can navigate back"""
        return len(self.history) > 1
    
    def create_navigation_bar(self) -> ft.NavigationBar:
        """Create a navigation bar for the application
        
        Returns:
            Navigation bar control
        """
        destinations = [
            ft.NavigationDestination(
                icon=ft.Icons.HOME,
                label="Welcome"
            ),
            ft.NavigationDestination(
                icon=ft.Icons.FOLDER,
                label="Files"
            ),
            ft.NavigationDestination(
                icon=ft.Icons.SETTINGS,
                label="Configuration"
            ),
            ft.NavigationDestination(
                icon=ft.Icons.PLAY_ARROW,
                label="Processing"
            ),
            ft.NavigationDestination(
                icon=ft.Icons.ASSESSMENT,
                label="Results"
            )
        ]
        
        # Map routes to navigation indices
        route_to_index = {
            PageRoute.WELCOME: 0,
            PageRoute.FILE_SELECTION: 1,
            PageRoute.CONFIGURATION: 2,
            PageRoute.PROCESSING: 3,
            PageRoute.RESULTS: 4
        }
        
        index_to_route = {v: k for k, v in route_to_index.items()}
        
        def on_destination_change(e):
            selected_index = e.control.selected_index
            if selected_index in index_to_route:
                target_route = index_to_route[selected_index]
                self.navigate_to(target_route)
        
        nav_bar = ft.NavigationBar(
            destinations=destinations,
            selected_index=route_to_index.get(self.current_route, 0),
            on_change=on_destination_change
        )
        
        return nav_bar
    
    def create_app_bar(self, title: str = "Academic Auto Grader") -> ft.AppBar:
        """Create an app bar with navigation controls
        
        Args:
            title: Application title
            
        Returns:
            App bar control
        """
        actions = []
        
        # Add back button if we can go back
        if self.can_go_back():
            actions.append(
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    tooltip="Go Back",
                    on_click=lambda _: self.go_back()
                )
            )
        
        # Add about button
        actions.append(
            ft.IconButton(
                icon=ft.Icons.INFO,
                tooltip="About",
                on_click=self._show_about_dialog
            )
        )
        
        # Add settings button
        actions.append(
            ft.IconButton(
                icon=ft.Icons.SETTINGS,
                tooltip="Settings",
                on_click=lambda _: self.navigate_to(PageRoute.SETTINGS)
            )
        )
        
        app_bar = ft.AppBar(
            title=ft.Text(title),
            center_title=True,
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
            actions=actions
        )
        
        return app_bar
    
    def _show_about_dialog(self, e):
        """Show the about dialog"""
        try:
            from app.components.about_dialog import AboutDialog
            about = AboutDialog(self.page)
            about.show()
        except ImportError:
            # Fallback if about dialog not available
            pass


def main():
    """Test the router"""
    def test_app(page: ft.Page):
        page.title = "Router Test"
        page.window_width = 800
        page.window_height = 600
        
        router = Router(page)
        
        # Mock page factories
        def create_welcome_page():
            return ft.Container(
                content=ft.Column([
                    ft.Text("Welcome Page", size=30),
                    ft.ElevatedButton(
                        "Go to Configuration",
                        on_click=lambda _: router.navigate_to(PageRoute.CONFIGURATION)
                    )
                ]),
                padding=20
            )
        
        def create_config_page():
            return ft.Container(
                content=ft.Column([
                    ft.Text("Configuration Page", size=30),
                    ft.ElevatedButton(
                        "Go to Processing",
                        on_click=lambda _: router.navigate_to(PageRoute.PROCESSING)
                    )
                ]),
                padding=20
            )
        
        def create_processing_page():
            return ft.Container(
                content=ft.Column([
                    ft.Text("Processing Page", size=30),
                    ft.ElevatedButton(
                        "Go Back",
                        on_click=lambda _: router.go_back()
                    )
                ]),
                padding=20
            )
        
        # Register pages
        router.register_page(PageRoute.WELCOME, create_welcome_page)
        router.register_page(PageRoute.CONFIGURATION, create_config_page)
        router.register_page(PageRoute.PROCESSING, create_processing_page)
        
        # Set up page
        page.appbar = router.create_app_bar()
        
        # Start with welcome page
        router.navigate_to(PageRoute.WELCOME)
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()