"""
Configuration Page Component

Displays assignment details and configuration options for the grading process.
Allows users to configure GitHub integration, preprocessing, and other options.
"""

import flet as ft
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.services.config_service import ConfigService
from app.components.cost_estimator import CostEstimator


class ConfigurationPage:
    """Configuration page component
    
    Displays selected assignment details and provides configuration options
    for the grading process including GitHub integration and preprocessing.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        selection_data: Dict[str, Any] = None,
        on_configuration_complete: Callable[[Dict[str, Any]], None] = None,
        on_start_grading: Callable[[Dict[str, Any]], None] = None,
        on_back: Callable[[], None] = None
    ):
        """Initialize the configuration page
        
        Args:
            page: Flet page object
            selection_data: Data from file selection page
            on_configuration_complete: Callback when configuration is complete
            on_start_grading: Callback to start grading process
            on_back: Callback to go back to file selection
        """
        self.page = page
        self.selection_data = selection_data or {}
        self.on_configuration_complete = on_configuration_complete
        self.on_start_grading = on_start_grading
        self.on_back = on_back
        
        # Initialize services
        self.config_service = ConfigService()
        self.cost_estimator = CostEstimator(
            page,
            on_estimate_complete=self._on_cost_estimate_complete,
            on_estimate_error=self._on_cost_estimate_error
        )
        
        # Configuration state
        self.config = {
            'github_enabled': False,
            'preprocessing_enabled': True,
            'dry_run': False,
            'cost_limit': 0.0,  # 0 means no limit
            'parallel_processing': True,
            'detailed_logging': False,
            'save_intermediate': False,
            'timeout_minutes': 30,
            'max_retries': 2
        }
        
        # Validation state
        self.validation_warnings = []
        self.validation_errors = []
        
        # UI components
        self.assignment_info_card = None
        self.file_info_card = None
        self.github_switch = None
        self.preprocessing_switch = None
        self.dry_run_switch = None
        self.cost_limit_field = None
        self.timeout_field = None
        self.retries_field = None
        self.parallel_switch = None
        self.logging_switch = None
        self.save_intermediate_switch = None
        self.advanced_section = None
        self.validation_card = None
        self.start_button = None
        self.content = None
    
    def build(self) -> ft.Control:
        """Build and return the configuration page UI"""
        
        # Page header
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    "⚙️ Configuration",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Review your selections and configure grading options",
                    size=16,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=30)
        )
        
        # Build information cards
        self._build_assignment_info_card()
        self._build_file_info_card()
        
        # Build configuration options
        self._build_configuration_options()
        
        # Set up cost estimator
        self._setup_cost_estimator()
        
        # Create start button
        self.start_button = ft.ElevatedButton(
            text="Start Grading",
            icon=ft.Icons.PLAY_ARROW,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_600,
                padding=ft.padding.symmetric(horizontal=30, vertical=15)
            ),
            on_click=self._on_start_grading_clicked
        )
        
        # Action buttons
        action_buttons = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    text="← Back to File Selection",
                    icon=ft.Icons.ARROW_BACK,
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREY_700,
                        bgcolor=ft.Colors.GREY_200
                    ),
                    on_click=self._on_back_clicked
                ),
                ft.Container(width=20),  # Spacer
                self.start_button
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.only(top=30)
        )
        
        # Main content layout
        content_sections = ft.Column([
            # Information cards row
            ft.Row([
                self.assignment_info_card,
                ft.Container(width=20),  # Spacer
                self.file_info_card
            ], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
            
            ft.Container(height=30),
            
            # Configuration options
            self._build_configuration_options(),
            
            ft.Container(height=30),
            
            # Cost estimation
            self.cost_estimator.build(),
            
            # Action buttons
            action_buttons
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        
        # Main content container
        self.content = ft.Container(
            content=ft.Column([
                header,
                content_sections
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
            ),
            padding=ft.padding.all(40),
            alignment=ft.alignment.top_center,
            expand=True
        )
        
        # Trigger initial validation
        self._validate_configuration()
        
        # Schedule initial cost estimation after a short delay
        import threading
        def delayed_initial_estimate():
            if (self.selection_data.get('submissions_folder') and 
                self.selection_data.get('assignment_name')):
                self._trigger_auto_estimation()
        
        timer = threading.Timer(1.0, delayed_initial_estimate)
        timer.start()
        
        return self.content
    
    def _build_assignment_info_card(self):
        """Build the assignment information card"""
        assignment_data = self.selection_data.get('assignment_data')
        assignment_name = self.selection_data.get('assignment_name', 'Unknown')
        
        if assignment_data:
            # Detailed assignment information
            content = ft.Column([
                # Header
                ft.Row([
                    ft.Icon(ft.Icons.ASSIGNMENT, color=ft.Colors.BLUE_600, size=24),
                    ft.Text(
                        "Assignment Details",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800
                    )
                ], spacing=10),
                
                ft.Divider(color=ft.Colors.BLUE_300),
                
                # Assignment info
                ft.Column([
                    ft.Text(
                        assignment_data['display_name'],
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK87
                    ),
                    ft.Text(
                        f"Type: {assignment_data['type'].replace('_', ' ').title()}",
                        size=12,
                        color=ft.Colors.GREY_700
                    ),
                    ft.Container(height=10),
                    
                    # Key metrics
                    ft.Row([
                        ft.Column([
                            ft.Text("📊", size=16),
                            ft.Text("Points", size=10, weight=ft.FontWeight.BOLD),
                            ft.Text(str(assignment_data['total_points']), size=12)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        
                        ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                        
                        ft.Column([
                            ft.Text("🔧", size=16),
                            ft.Text("Functions", size=10, weight=ft.FontWeight.BOLD),
                            ft.Text(str(assignment_data['required_functions']), size=12)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
                        
                        ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                        
                        ft.Column([
                            ft.Text("📋", size=16),
                            ft.Text("Criteria", size=10, weight=ft.FontWeight.BOLD),
                            ft.Text(str(assignment_data['rubric_criteria']), size=12)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
                    ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                    
                    ft.Container(height=10),
                    ft.Divider(color=ft.Colors.GREY_300),
                    
                    # Description
                    ft.Text("Description:", size=11, weight=ft.FontWeight.BOLD),
                    ft.Text(
                        assignment_data['description'],
                        size=10,
                        color=ft.Colors.GREY_700
                    )
                ], spacing=5)
            ], spacing=10)
            
            # Set initial GitHub setting from assignment config
            self.config['github_enabled'] = assignment_data.get('github_enabled', False)
        else:
            # Fallback if no assignment data
            content = ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE_600, size=24),
                    ft.Text(
                        "Assignment Information",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ORANGE_800
                    )
                ], spacing=10),
                ft.Text(
                    f"Assignment: {assignment_name}",
                    size=14,
                    color=ft.Colors.GREY_700
                ),
                ft.Text(
                    "Detailed information not available",
                    size=12,
                    color=ft.Colors.GREY_600
                )
            ], spacing=10)
        
        self.assignment_info_card = ft.Container(
            content=content,
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=10,
            bgcolor=ft.Colors.BLUE_50,
            width=350,
            height=280
        )
    
    def _build_file_info_card(self):
        """Build the file information card"""
        submissions_folder = self.selection_data.get('submissions_folder', '')
        roster_file = self.selection_data.get('roster_file', '')
        
        # Get submission count if available
        submission_count = "Unknown"
        if submissions_folder:
            try:
                validation = self.config_service.validate_paths(submissions_folder)
                submission_count = validation.get('submissions_count', 0)
            except:
                submission_count = "Error"
        
        content = ft.Column([
            # Header
            ft.Row([
                ft.Icon(ft.Icons.FOLDER, color=ft.Colors.GREEN_600, size=24),
                ft.Text(
                    "File Information",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_800
                )
            ], spacing=10),
            
            ft.Divider(color=ft.Colors.GREEN_300),
            
            # File details
            ft.Column([
                # Submissions folder
                ft.Row([
                    ft.Icon(ft.Icons.FOLDER_ZIP, color=ft.Colors.BLUE_600, size=16),
                    ft.Text("Submissions:", size=12, weight=ft.FontWeight.BOLD)
                ], spacing=5),
                ft.Text(
                    f"{submission_count} ZIP files" if submission_count != "Unknown" else "Files detected",
                    size=11,
                    color=ft.Colors.GREY_700
                ),
                ft.Text(
                    f"📁 {Path(submissions_folder).name}" if submissions_folder else "No folder selected",
                    size=10,
                    color=ft.Colors.GREY_600
                ),
                
                ft.Container(height=15),
                
                # Roster file
                ft.Row([
                    ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.ORANGE_600, size=16),
                    ft.Text("Roster:", size=12, weight=ft.FontWeight.BOLD)
                ], spacing=5),
                ft.Column([
                    ft.Text("CSV file selected", size=11, color=ft.Colors.GREY_700),
                    ft.Text(f"📄 {Path(roster_file).name}", size=10, color=ft.Colors.GREY_600)
                ], spacing=2) if roster_file else ft.Text("No roster file (optional)", size=11, color=ft.Colors.GREY_700),
                
                ft.Container(height=15),
                
                # Summary
                ft.Container(
                    content=ft.Column([
                        ft.Text("Ready for Processing", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
                        ft.Text("All required files selected", size=10, color=ft.Colors.GREEN_600)
                    ], spacing=2),
                    padding=ft.padding.all(10),
                    border=ft.border.all(1, ft.Colors.GREEN_300),
                    border_radius=5,
                    bgcolor=ft.Colors.GREEN_100
                )
            ], spacing=5)
        ], spacing=10)
        
        self.file_info_card = ft.Container(
            content=content,
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.GREEN_200),
            border_radius=10,
            bgcolor=ft.Colors.GREEN_50,
            width=350,
            height=280
        )
    
    def _build_configuration_options(self):
        """Build the configuration options section"""
        
        # Main options
        self.github_switch = ft.Switch(
            label="Enable GitHub Integration",
            value=self.config['github_enabled'],
            on_change=self._on_github_changed
        )
        
        self.preprocessing_switch = ft.Switch(
            label="Enable Preprocessing Pipeline",
            value=self.config['preprocessing_enabled'],
            on_change=self._on_preprocessing_changed
        )
        
        self.dry_run_switch = ft.Switch(
            label="Dry Run (Cost Estimation Only)",
            value=self.config['dry_run'],
            on_change=self._on_dry_run_changed
        )
        
        # Cost limit field
        self.cost_limit_field = ft.TextField(
            label="Cost Limit ($)",
            hint_text="0 = no limit",
            value=str(self.config['cost_limit']),
            width=150,
            on_change=self._on_cost_limit_changed,
            prefix_text="$"
        )
        
        # Advanced options
        self.parallel_switch = ft.Switch(
            label="Parallel Processing",
            value=self.config['parallel_processing'],
            on_change=self._on_parallel_changed
        )
        
        self.logging_switch = ft.Switch(
            label="Detailed Logging",
            value=self.config['detailed_logging'],
            on_change=self._on_logging_changed
        )
        
        self.save_intermediate_switch = ft.Switch(
            label="Save Intermediate Files",
            value=self.config['save_intermediate'],
            on_change=self._on_save_intermediate_changed
        )
        
        self.timeout_field = ft.TextField(
            label="Timeout (minutes)",
            value=str(self.config['timeout_minutes']),
            width=120,
            on_change=self._on_timeout_changed
        )
        
        self.retries_field = ft.TextField(
            label="Max Retries",
            value=str(self.config['max_retries']),
            width=100,
            on_change=self._on_retries_changed
        )
        
        # Main options section
        main_options = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SETTINGS, color=ft.Colors.PURPLE_600, size=24),
                    ft.Text(
                        "Grading Options",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PURPLE_800
                    )
                ], spacing=10),
                
                ft.Divider(color=ft.Colors.PURPLE_300),
                
                # GitHub option with warning
                ft.Column([
                    self.github_switch,
                    ft.Text(
                        "Analyze GitHub repositories for additional context and code quality assessment",
                        size=10,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Text(
                        "⚠️ Requires GITHUB_TOKEN environment variable",
                        size=9,
                        color=ft.Colors.ORANGE_700,
                        visible=self.config['github_enabled']
                    ) if self._check_github_token() == False else ft.Container()
                ], spacing=5),
                
                ft.Container(height=10),
                
                # Preprocessing option
                ft.Column([
                    self.preprocessing_switch,
                    ft.Text(
                        "Run complete preprocessing workflow including file extraction and organization",
                        size=10,
                        color=ft.Colors.GREY_600
                    )
                ], spacing=5),
                
                ft.Container(height=10),
                
                # Dry run option
                ft.Column([
                    self.dry_run_switch,
                    ft.Text(
                        "Estimate costs and validate configuration without running actual grading",
                        size=10,
                        color=ft.Colors.GREY_600
                    )
                ], spacing=5),
                
                ft.Container(height=15),
                ft.Divider(color=ft.Colors.GREY_300),
                
                # Cost control
                ft.Row([
                    self.cost_limit_field,
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text("Cost Control", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("Set 0 for no limit", size=9, color=ft.Colors.GREY_600)
                    ], spacing=2)
                ], alignment=ft.MainAxisAlignment.START)
            ], spacing=10),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.PURPLE_200),
            border_radius=10,
            bgcolor=ft.Colors.PURPLE_50,
            width=700
        )
        
        # Advanced options section (collapsible)
        self.advanced_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.TUNE, color=ft.Colors.INDIGO_600, size=20),
                    ft.Text(
                        "Advanced Options",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.INDIGO_800
                    )
                ], spacing=8),
                
                ft.Divider(color=ft.Colors.INDIGO_300),
                
                # Performance options
                ft.Column([
                    ft.Text("Performance", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700),
                    self.parallel_switch,
                    ft.Text(
                        "Process multiple submissions simultaneously for faster grading",
                        size=9,
                        color=ft.Colors.GREY_600
                    )
                ], spacing=5),
                
                ft.Container(height=10),
                
                # Debugging options
                ft.Column([
                    ft.Text("Debugging", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700),
                    self.logging_switch,
                    ft.Text(
                        "Enable verbose logging for troubleshooting and detailed output",
                        size=9,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Container(height=8),
                    self.save_intermediate_switch,
                    ft.Text(
                        "Save intermediate processing files for manual inspection",
                        size=9,
                        color=ft.Colors.GREY_600
                    )
                ], spacing=5),
                
                ft.Container(height=10),
                
                # Reliability options
                ft.Column([
                    ft.Text("Reliability", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_700),
                    ft.Row([
                        self.timeout_field,
                        ft.Container(width=10),
                        self.retries_field
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Text(
                        "Configure timeout and retry behavior for robust processing",
                        size=9,
                        color=ft.Colors.GREY_600
                    )
                ], spacing=5)
            ], spacing=8),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.INDIGO_200),
            border_radius=10,
            bgcolor=ft.Colors.INDIGO_50,
            width=700
        )
        
        # Validation card
        self._build_validation_card()
        
        return ft.Column([
            main_options,
            ft.Container(height=20),
            self.advanced_section,
            ft.Container(height=20),
            self.validation_card
        ], spacing=0)
    
    def _on_github_changed(self, e):
        """Handle GitHub integration toggle"""
        self.config['github_enabled'] = e.control.value
        self._validate_configuration()
        self._notify_configuration_changed()
    
    def _on_preprocessing_changed(self, e):
        """Handle preprocessing toggle"""
        self.config['preprocessing_enabled'] = e.control.value
        self._validate_configuration()
        self._notify_configuration_changed()
    
    def _on_dry_run_changed(self, e):
        """Handle dry run toggle"""
        self.config['dry_run'] = e.control.value
        self._validate_configuration()
        self._notify_configuration_changed()
    
    def _on_cost_limit_changed(self, e):
        """Handle cost limit field change"""
        try:
            value = float(e.control.value) if e.control.value else 0.0
            self.config['cost_limit'] = max(0.0, value)  # Ensure non-negative
        except ValueError:
            self.config['cost_limit'] = 0.0
            e.control.value = "0.0"
            self.page.update()
        self._validate_configuration()
        self._notify_configuration_changed()
    
    def _on_parallel_changed(self, e):
        """Handle parallel processing toggle"""
        self.config['parallel_processing'] = e.control.value
        self._validate_configuration()
        self._notify_configuration_changed()
    
    def _on_logging_changed(self, e):
        """Handle detailed logging toggle"""
        self.config['detailed_logging'] = e.control.value
        self._validate_configuration()
        self._notify_configuration_changed()
    
    def _on_save_intermediate_changed(self, e):
        """Handle save intermediate files toggle"""
        self.config['save_intermediate'] = e.control.value
        self._validate_configuration()
        self._notify_configuration_changed()
    
    def _on_timeout_changed(self, e):
        """Handle timeout field change"""
        try:
            value = int(e.control.value) if e.control.value else 30
            self.config['timeout_minutes'] = max(1, min(value, 180))  # 1-180 minutes
        except ValueError:
            self.config['timeout_minutes'] = 30
            e.control.value = "30"
            self.page.update()
        self._validate_configuration()
        self._notify_configuration_changed()
    
    def _on_retries_changed(self, e):
        """Handle max retries field change"""
        try:
            value = int(e.control.value) if e.control.value else 2
            self.config['max_retries'] = max(0, min(value, 10))  # 0-10 retries
        except ValueError:
            self.config['max_retries'] = 2
            e.control.value = "2"
            self.page.update()
        self._validate_configuration()
        self._notify_configuration_changed()
    
    def _check_github_token(self) -> bool:
        """Check if GitHub token is available"""
        import os
        return bool(os.getenv('GITHUB_TOKEN'))
    
    def _build_validation_card(self):
        """Build the validation card showing warnings and errors"""
        self.validation_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.VERIFIED, color=ft.Colors.GREEN_600, size=20),
                    ft.Text(
                        "Configuration Validation",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_800
                    )
                ], spacing=8),
                ft.Text(
                    "Configuration is valid and ready for grading",
                    size=12,
                    color=ft.Colors.GREEN_700
                )
            ], spacing=8),
            padding=ft.padding.all(15),
            border=ft.border.all(1, ft.Colors.GREEN_200),
            border_radius=10,
            bgcolor=ft.Colors.GREEN_50,
            width=700,
            visible=True
        )
    
    def _validate_configuration(self):
        """Validate the current configuration and update UI"""
        self.validation_warnings = []
        self.validation_errors = []
        
        # Check GitHub integration
        if self.config['github_enabled'] and not self._check_github_token():
            self.validation_warnings.append(
                "GitHub integration enabled but GITHUB_TOKEN environment variable not found"
            )
        
        # Check cost limit
        if self.config['cost_limit'] > 0 and self.config['cost_limit'] < 1.0:
            self.validation_warnings.append(
                f"Low cost limit (${self.config['cost_limit']:.2f}) may prevent processing of larger assignments"
            )
        
        # Check timeout vs parallel processing
        if self.config['parallel_processing'] and self.config['timeout_minutes'] < 10:
            self.validation_warnings.append(
                "Short timeout with parallel processing may cause unnecessary retries"
            )
        
        # Check preprocessing + dry run combination
        if not self.config['preprocessing_enabled'] and not self.config['dry_run']:
            self.validation_warnings.append(
                "Skipping preprocessing may result in incomplete file analysis"
            )
        
        # Check if save intermediate is enabled without detailed logging
        if self.config['save_intermediate'] and not self.config['detailed_logging']:
            self.validation_warnings.append(
                "Saving intermediate files without detailed logging may make debugging difficult"
            )
        
        # Update validation card
        self._update_validation_card()
    
    def _update_validation_card(self):
        """Update the validation card based on current warnings/errors"""
        if not self.validation_card:
            return
            
        if self.validation_errors:
            # Show errors
            icon = ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_600, size=20)
            title = ft.Text(
                "Configuration Errors",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.RED_800
            )
            content = ft.Column([
                ft.Text(
                    "Please fix the following errors before proceeding:",
                    size=12,
                    color=ft.Colors.RED_700
                ),
                ft.Column([
                    ft.Text(f"• {error}", size=11, color=ft.Colors.RED_600)
                    for error in self.validation_errors
                ], spacing=2)
            ], spacing=8)
            
            self.validation_card.bgcolor = ft.Colors.RED_50
            self.validation_card.border = ft.border.all(1, ft.Colors.RED_200)
            self.start_button.disabled = True
            
        elif self.validation_warnings:
            # Show warnings
            icon = ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE_600, size=20)
            title = ft.Text(
                "Configuration Warnings",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.ORANGE_800
            )
            content = ft.Column([
                ft.Text(
                    "Please review the following warnings:",
                    size=12,
                    color=ft.Colors.ORANGE_700
                ),
                ft.Column([
                    ft.Text(f"• {warning}", size=11, color=ft.Colors.ORANGE_600)
                    for warning in self.validation_warnings
                ], spacing=2),
                ft.Text(
                    "You can proceed, but consider addressing these issues.",
                    size=11,
                    color=ft.Colors.ORANGE_700,
                    italic=True
                )
            ], spacing=8)
            
            self.validation_card.bgcolor = ft.Colors.ORANGE_50
            self.validation_card.border = ft.border.all(1, ft.Colors.ORANGE_200)
            self.start_button.disabled = False
            
        else:
            # All good
            icon = ft.Icon(ft.Icons.VERIFIED, color=ft.Colors.GREEN_600, size=20)
            title = ft.Text(
                "Configuration Valid",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.GREEN_800
            )
            content = ft.Text(
                "Configuration is valid and ready for grading",
                size=12,
                color=ft.Colors.GREEN_700
            )
            
            self.validation_card.bgcolor = ft.Colors.GREEN_50
            self.validation_card.border = ft.border.all(1, ft.Colors.GREEN_200)
            self.start_button.disabled = False
        
        # Update card content
        self.validation_card.content = ft.Column([
            ft.Row([icon, title], spacing=8),
            content
        ], spacing=8)
        
        self.page.update()
    
    def _setup_cost_estimator(self):
        """Set up the cost estimator with current configuration"""
        def manual_estimate():
            """Trigger manual cost estimation"""
            submissions_folder = self.selection_data.get('submissions_folder', '')
            assignment_name = self.selection_data.get('assignment_name', '')
            roster_file = self.selection_data.get('roster_file', '')
            
            if submissions_folder and assignment_name:
                import asyncio
                asyncio.create_task(self.cost_estimator.estimate_cost(
                    submissions_folder=submissions_folder,
                    assignment_name=assignment_name,
                    enable_github=self.config['github_enabled'],
                    roster_file=roster_file if roster_file else None
                ))
        
        self.cost_estimator.set_manual_estimate_callback(manual_estimate)
        
        # Note: Initial estimation will be triggered after page is fully loaded
        # to avoid event loop issues during build
    
    def _trigger_auto_estimation(self):
        """Trigger auto cost estimation with current settings"""
        submissions_folder = self.selection_data.get('submissions_folder', '')
        assignment_name = self.selection_data.get('assignment_name', '')
        roster_file = self.selection_data.get('roster_file', '')
        
        if submissions_folder and assignment_name:
            self.cost_estimator.trigger_auto_estimate(
                submissions_folder=submissions_folder,
                assignment_name=assignment_name,
                enable_github=self.config['github_enabled'],
                roster_file=roster_file if roster_file else None,
                delay_seconds=1.5  # Shorter delay for responsive UI
            )
    
    def _on_cost_estimate_complete(self, estimate_data: Dict[str, Any]):
        """Handle cost estimation completion"""
        # Check against cost limit if set
        if self.config['cost_limit'] > 0:
            estimated_cost = estimate_data.get('total_cost', 0)
            if estimated_cost > self.config['cost_limit']:
                self.validation_warnings.append(
                    f"Estimated cost (${estimated_cost:.2f}) exceeds limit (${self.config['cost_limit']:.2f})"
                )
                self._update_validation_card()
        
        # Update start button text with cost
        if self.start_button:
            estimated_cost = estimate_data.get('total_cost', 0)
            if estimated_cost > 0:
                self.start_button.text = f"Start Grading (Est. ${estimated_cost:.2f})"
            else:
                self.start_button.text = "Start Grading"
            self.page.update()
    
    def _on_cost_estimate_error(self, error_msg: str):
        """Handle cost estimation error"""
        # Add warning about failed estimation
        self.validation_warnings.append(f"Cost estimation failed: {error_msg}")
        self._update_validation_card()
        
        # Reset start button text
        if self.start_button:
            self.start_button.text = "Start Grading"
            self.page.update()
    
    def _notify_configuration_changed(self):
        """Notify that configuration has changed"""
        # Trigger auto-estimation when configuration changes
        self._trigger_auto_estimation()
        
        if self.on_configuration_complete:
            config_data = {
                **self.selection_data,
                'configuration': self.config
            }
            self.on_configuration_complete(config_data)
    
    def _on_back_clicked(self, e):
        """Handle back button click"""
        if self.on_back:
            self.on_back()
    
    def _on_start_grading_clicked(self, e):
        """Handle start grading button click"""
        if self.on_start_grading:
            config_data = {
                **self.selection_data,
                'configuration': self.config
            }
            self.on_start_grading(config_data)
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get the current configuration"""
        return {
            **self.selection_data,
            'configuration': self.config
        }


def main():
    """Test the configuration page"""
    def test_app(page: ft.Page):
        page.title = "Configuration Page Test"
        page.window.width = 1000
        page.window.height = 800
        
        # Mock selection data
        mock_selection = {
            'submissions_folder': '/path/to/submissions',
            'roster_file': '/path/to/roster.csv',
            'assignment_name': 'weatherwise',
            'assignment_data': {
                'name': 'weatherwise',
                'display_name': 'WeatherWise Assignment',
                'description': 'Create a weather application using Python with data analysis and visualization features.',
                'type': 'programming_assignment',
                'total_points': 100,
                'github_enabled': True,
                'required_functions': 5,
                'rubric_criteria': 8
            }
        }
        
        def on_configuration_complete(data):
            print(f"Configuration updated: {data['configuration']}")
        
        def on_start_grading(data):
            print(f"Starting grading with config: {data}")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Starting grading process..."),
                    action="OK"
                )
            )
        
        def on_back():
            print("Going back to file selection")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Going back to file selection..."),
                    action="OK"
                )
            )
        
        config_page = ConfigurationPage(
            page,
            mock_selection,
            on_configuration_complete,
            on_start_grading,
            on_back
        )
        
        page.add(config_page.build())
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()