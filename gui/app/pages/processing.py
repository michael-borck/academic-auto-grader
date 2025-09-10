"""
Processing Page Component

Displays real-time grading progress with detailed status updates, progress tracking,
and process control functionality.
"""

import flet as ft
import asyncio
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime, timedelta

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.services.grader_service import GraderService, GradingStatus, ProgressUpdate
from app.components.progress_bar import AdvancedProgressBar, IndividualStudentTracker


class ProcessingPage:
    """Processing page component
    
    Displays real-time grading progress with comprehensive status tracking,
    progress visualization, and process control capabilities.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        config_data: Dict[str, Any] = None,
        on_processing_complete: Callable[[Dict[str, Any]], None] = None,
        on_view_results: Callable[[Dict[str, Any]], None] = None,
        on_back_to_config: Callable[[], None] = None
    ):
        """Initialize the processing page
        
        Args:
            page: Flet page object
            config_data: Configuration data from previous pages
            on_processing_complete: Callback when processing completes
            on_view_results: Callback to view results
            on_back_to_config: Callback to return to configuration
        """
        self.page = page
        self.config_data = config_data or {}
        self.on_processing_complete = on_processing_complete
        self.on_view_results = on_view_results
        self.on_back_to_config = on_back_to_config
        
        # Services
        self.grader_service = GraderService()
        
        # Advanced progress components
        self.advanced_progress_bar = AdvancedProgressBar(page, width=700)
        self.student_tracker = IndividualStudentTracker(page, max_visible_students=8)
        
        # Processing state
        self.is_processing = False
        self.processing_results = None
        self.start_time = None
        self.estimated_end_time = None
        
        # Progress tracking
        self.progress_updates: List[ProgressUpdate] = []
        self.current_status = GradingStatus.IDLE
        self.progress_percentage = 0.0
        
        # UI components
        self.status_card = None
        self.progress_bar = None
        self.progress_text = None
        self.current_operation_text = None
        self.student_progress_text = None
        self.cost_tracker = None
        self.time_tracker = None
        self.activity_log = None
        self.control_buttons = None
        self.results_section = None
        self.log_viewer_dialog = None
        self.error_dialog = None
        
        # Activity log data
        self.activity_entries: List[Dict[str, Any]] = []
        self.max_log_entries = 100
        
    def build(self) -> ft.Control:
        """Build and return the processing page UI"""
        
        # Page header
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    "🔄 Processing",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Real-time grading progress and status updates",
                    size=16,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=30)
        )
        
        # Build all UI sections
        self._build_status_section()
        self._build_progress_section()
        self._build_tracking_section()
        self._build_activity_log()
        self._build_control_buttons()
        self._build_results_section()
        
        # Main content layout
        content_sections = ft.Column([
            # Status and progress
            ft.Row([
                self.status_card,
                ft.Container(width=20),
                self.progress_section
            ], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
            
            ft.Container(height=20),
            
            # Advanced progress tracking
            self.advanced_progress_bar.build(),
            
            ft.Container(height=20),
            
            # Individual student tracking and cost/time info
            ft.Row([
                self.student_tracker.build(),
                ft.Container(width=20),
                ft.Column([
                    self.cost_tracker,
                    ft.Container(height=15),
                    self.time_tracker
                ], spacing=0)
            ], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
            
            ft.Container(height=20),
            
            # Activity log
            self.activity_log,
            
            ft.Container(height=20),
            
            # Control buttons
            self.control_buttons,
            
            # Results section (hidden initially)
            self.results_section
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        
        # Main content container
        content = ft.Container(
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
        
        # Set up grader service callbacks
        self._setup_grader_service()
        
        # Auto-start processing if configuration is ready
        if self._is_ready_to_process():
            self._schedule_auto_start()
        
        return content
    
    def _build_status_section(self):
        """Build the status display section"""
        self.status_card = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PENDING, color=ft.Colors.BLUE_600, size=24),
                    ft.Text(
                        "Status: Ready",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800
                    )
                ], spacing=10),
                
                ft.Divider(color=ft.Colors.BLUE_300),
                
                ft.Text(
                    "Waiting to start grading process...",
                    size=12,
                    color=ft.Colors.GREY_700
                ),
                
                ft.Container(height=10),
                
                ft.Text(
                    self._get_config_summary(),
                    size=11,
                    color=ft.Colors.GREY_600
                )
            ], spacing=8),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=10,
            bgcolor=ft.Colors.BLUE_50,
            width=350,
            height=180
        )
    
    def _build_progress_section(self):
        """Build the progress tracking section"""
        # Overall progress bar
        self.progress_bar = ft.ProgressBar(
            width=300,
            height=20,
            value=0,
            color=ft.Colors.GREEN_600,
            bgcolor=ft.Colors.GREY_300,
            border_radius=10
        )
        
        # Progress text
        self.progress_text = ft.Text(
            "0% Complete",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_800,
            text_align=ft.TextAlign.CENTER
        )
        
        # Current operation
        self.current_operation_text = ft.Text(
            "No operation in progress",
            size=12,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER
        )
        
        # Student progress
        self.student_progress_text = ft.Text(
            "0 of 0 submissions processed",
            size=11,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER
        )
        
        self.progress_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.TIMELINE, color=ft.Colors.GREEN_600, size=24),
                    ft.Text(
                        "Progress",
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_800
                    )
                ], spacing=10),
                
                ft.Divider(color=ft.Colors.GREEN_300),
                
                self.progress_text,
                ft.Container(height=10),
                self.progress_bar,
                ft.Container(height=15),
                self.current_operation_text,
                ft.Container(height=5),
                self.student_progress_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.GREEN_200),
            border_radius=10,
            bgcolor=ft.Colors.GREEN_50,
            width=350,
            height=180
        )
    
    def _build_tracking_section(self):
        """Build cost and time tracking sections"""
        # Cost tracker
        self.cost_tracker = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ATTACH_MONEY, color=ft.Colors.ORANGE_600, size=20),
                    ft.Text(
                        "Cost Tracking",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.ORANGE_800
                    )
                ], spacing=8),
                
                ft.Divider(color=ft.Colors.ORANGE_300),
                
                ft.Column([
                    ft.Row([
                        ft.Text("Used:", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("$0.00", size=12, color=ft.Colors.ORANGE_700)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Estimated:", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("$0.00", size=12, color=ft.Colors.GREY_600)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Remaining:", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("$0.00", size=12, color=ft.Colors.GREEN_600)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], spacing=5)
            ], spacing=8),
            padding=ft.padding.all(15),
            border=ft.border.all(1, ft.Colors.ORANGE_200),
            border_radius=10,
            bgcolor=ft.Colors.ORANGE_50,
            width=300,
            height=120
        )
        
        # Time tracker
        self.time_tracker = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.SCHEDULE, color=ft.Colors.PURPLE_600, size=20),
                    ft.Text(
                        "Time Tracking",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.PURPLE_800
                    )
                ], spacing=8),
                
                ft.Divider(color=ft.Colors.PURPLE_300),
                
                ft.Column([
                    ft.Row([
                        ft.Text("Elapsed:", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("00:00:00", size=12, color=ft.Colors.PURPLE_700)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Estimated:", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("--:--:--", size=12, color=ft.Colors.GREY_600)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        ft.Text("Remaining:", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text("--:--:--", size=12, color=ft.Colors.GREEN_600)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], spacing=5)
            ], spacing=8),
            padding=ft.padding.all(15),
            border=ft.border.all(1, ft.Colors.PURPLE_200),
            border_radius=10,
            bgcolor=ft.Colors.PURPLE_50,
            width=300,
            height=120
        )
    
    def _build_activity_log(self):
        """Build the activity log section"""
        # Activity log list view
        activity_list = ft.ListView(
            height=200,
            spacing=5,
            padding=ft.padding.all(10)
        )
        
        # Add initial entry
        activity_list.controls.append(
            ft.Container(
                content=ft.Row([
                    ft.Text(
                        datetime.now().strftime("%H:%M:%S"),
                        size=10,
                        color=ft.Colors.GREY_500,
                        width=60
                    ),
                    ft.Text(
                        "Processing page loaded - ready to start grading",
                        size=11,
                        color=ft.Colors.GREY_700
                    )
                ], spacing=10),
                padding=ft.padding.symmetric(vertical=2)
            )
        )
        
        self.activity_log = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.LIST_ALT, color=ft.Colors.INDIGO_600, size=20),
                    ft.Text(
                        "Activity Log",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.INDIGO_800
                    ),
                    ft.Container(expand=True),
                    ft.IconButton(
                        icon=ft.Icons.ARTICLE,
                        tooltip="View detailed logs",
                        icon_size=16,
                        on_click=self._show_detailed_logs
                    ),
                    ft.IconButton(
                        icon=ft.Icons.CLEAR_ALL,
                        tooltip="Clear log",
                        icon_size=16,
                        on_click=self._clear_activity_log
                    )
                ], spacing=8),
                
                ft.Divider(color=ft.Colors.INDIGO_300),
                
                activity_list
            ], spacing=8),
            padding=ft.padding.all(15),
            border=ft.border.all(1, ft.Colors.INDIGO_200),
            border_radius=10,
            bgcolor=ft.Colors.INDIGO_50,
            width=700
        )
        
        # Store reference to the list for updates
        self.activity_list = activity_list
    
    def _build_control_buttons(self):
        """Build the control buttons section"""
        self.start_button = ft.ElevatedButton(
            text="Start Grading",
            icon=ft.Icons.PLAY_ARROW,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_600,
                padding=ft.padding.symmetric(horizontal=30, vertical=15)
            ),
            on_click=self._on_start_clicked
        )
        
        self.pause_button = ft.ElevatedButton(
            text="Pause",
            icon=ft.Icons.PAUSE,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.ORANGE_600
            ),
            visible=False,
            on_click=self._on_pause_clicked
        )
        
        self.cancel_button = ft.ElevatedButton(
            text="Cancel",
            icon=ft.Icons.STOP,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.RED_600
            ),
            visible=False,
            on_click=self._on_cancel_clicked
        )
        
        self.back_button = ft.ElevatedButton(
            text="← Back to Configuration",
            icon=ft.Icons.ARROW_BACK,
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
                bgcolor=ft.Colors.GREY_200
            ),
            on_click=self._on_back_clicked
        )
        
        self.control_buttons = ft.Container(
            content=ft.Row([
                self.back_button,
                ft.Container(width=20),
                self.start_button,
                self.pause_button,
                self.cancel_button
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=20)
        )
    
    def _build_results_section(self):
        """Build the results display section (initially hidden)"""
        self.results_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.ASSESSMENT, color=ft.Colors.GREEN_600, size=24),
                    ft.Text(
                        "Processing Complete!",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_800
                    )
                ], spacing=10),
                
                ft.Divider(color=ft.Colors.GREEN_300),
                
                ft.Text(
                    "Grading has completed successfully.",
                    size=14,
                    color=ft.Colors.GREEN_700
                ),
                
                ft.Container(height=20),
                
                ft.ElevatedButton(
                    text="View Results",
                    icon=ft.Icons.VISIBILITY,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.GREEN_600,
                        padding=ft.padding.symmetric(horizontal=30, vertical=15)
                    ),
                    on_click=self._on_view_results_clicked
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=ft.padding.all(30),
            border=ft.border.all(2, ft.Colors.GREEN_300),
            border_radius=15,
            bgcolor=ft.Colors.GREEN_50,
            width=600,
            visible=False
        )
    
    def _get_config_summary(self) -> str:
        """Get a summary of the current configuration"""
        if not self.config_data:
            return "No configuration data available"
        
        assignment_name = self.config_data.get('assignment_name', 'Unknown')
        config = self.config_data.get('configuration', {})
        
        parts = [f"Assignment: {assignment_name}"]
        
        if config.get('github_enabled'):
            parts.append("GitHub: Enabled")
        
        if config.get('dry_run'):
            parts.append("Mode: Dry Run")
        
        if config.get('preprocessing_enabled'):
            parts.append("Preprocessing: Enabled")
        
        return " | ".join(parts)
    
    def _is_ready_to_process(self) -> bool:
        """Check if we have all required data to start processing"""
        if not self.config_data:
            return False
        
        required_fields = ['submissions_folder', 'assignment_name']
        return all(self.config_data.get(field) for field in required_fields)
    
    def _schedule_auto_start(self):
        """Schedule automatic start after a brief delay"""
        import threading
        def delayed_start():
            # Add to activity log
            self._add_activity_entry("Auto-starting grading process...")
            # Trigger start asynchronously
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._start_processing())
            except RuntimeError:
                # No event loop, just log that auto-start was attempted
                self._add_activity_entry("Auto-start disabled - click Start Grading to begin")
        
        timer = threading.Timer(2.0, delayed_start)
        timer.start()
    
    def _setup_grader_service(self):
        """Set up grader service with progress callbacks"""
        self.grader_service.set_progress_callback(self._on_progress_update)
    
    async def _start_processing(self):
        """Start the grading process"""
        if self.is_processing:
            return
        
        self.is_processing = True
        self.start_time = datetime.now()
        
        # Update UI for processing state
        self._update_ui_for_processing_start()
        
        try:
            # Extract configuration
            config = self.config_data.get('configuration', {})
            
            # Start grading with retry capability
            results = await self.grader_service.run_grading_with_retry(
                submissions_folder=self.config_data['submissions_folder'],
                assignment_name=self.config_data['assignment_name'],
                enable_github=config.get('github_enabled', False),
                dry_run=config.get('dry_run', False),
                roster_file=self.config_data.get('roster_file'),
                preprocessing=config.get('preprocessing_enabled', True)
            )
            
            # Store results
            self.processing_results = results
            
            # Check if results indicate an error
            if not results.get('success', True):
                self._update_ui_for_error(results)
            else:
                # Update UI for completion
                self._update_ui_for_completion(results)
                
                # Notify callback
                if self.on_processing_complete:
                    self.on_processing_complete(results)
                
        except Exception as e:
            # Handle both simple exceptions and enhanced error results
            if hasattr(e, 'args') and len(e.args) > 0 and isinstance(e.args[0], dict):
                error_data = e.args[0]
            else:
                error_data = str(e)
            
            self._update_ui_for_error(error_data)
        
        finally:
            self.is_processing = False
    
    def _update_ui_for_processing_start(self):
        """Update UI when processing starts"""
        # Update status card
        self.status_card.content.controls[0].controls[0].icon = ft.Icons.PLAY_CIRCLE
        self.status_card.content.controls[0].controls[1].value = "Status: Processing"
        self.status_card.content.controls[2].value = "Grading in progress..."
        self.status_card.bgcolor = ft.Colors.GREEN_50
        self.status_card.border = ft.border.all(1, ft.Colors.GREEN_200)
        
        # Update buttons
        self.start_button.visible = False
        self.pause_button.visible = True
        self.cancel_button.visible = True
        self.back_button.disabled = True
        
        # Initialize advanced progress tracking
        submissions_folder = self.config_data.get('submissions_folder', '')
        if submissions_folder:
            try:
                import os
                zip_files = [f for f in os.listdir(submissions_folder) if f.endswith('.zip')]
                student_ids = [os.path.splitext(f)[0] for f in zip_files]
                self.advanced_progress_bar.start_processing(len(student_ids), student_ids)
                self._add_activity_entry(f"Initialized tracking for {len(student_ids)} students")
            except Exception as e:
                self._add_activity_entry(f"Could not initialize detailed tracking: {str(e)}")
                # Fallback to basic tracking
                self.advanced_progress_bar.start_processing(1, ["Unknown"])
        
        # Add activity entry
        self._add_activity_entry("Grading process started")
        
        self.page.update()
    
    def _update_ui_for_completion(self, results: Dict[str, Any]):
        """Update UI when processing completes"""
        # Update status card
        self.status_card.content.controls[0].controls[0].icon = ft.Icons.CHECK_CIRCLE
        self.status_card.content.controls[0].controls[1].value = "Status: Complete"
        self.status_card.content.controls[2].value = "Grading completed successfully!"
        
        # Update progress to 100%
        self.progress_bar.value = 1.0
        self.progress_text.value = "100% Complete"
        self.current_operation_text.value = "All submissions processed"
        
        # Update buttons
        self.pause_button.visible = False
        self.cancel_button.visible = False
        self.back_button.disabled = False
        
        # Show results section
        self.results_section.visible = True
        
        # Add final activity entry
        self._add_activity_entry("Grading process completed successfully")
        
        self.page.update()
    
    def _update_ui_for_error(self, error_data):
        """Update UI when processing encounters an error"""
        if isinstance(error_data, str):
            # Legacy simple error message
            error_msg = error_data
            is_recoverable = True
            suggested_action = "Try restarting the operation"
        else:
            # Enhanced error data
            error_msg = error_data.get('error', 'Unknown error')
            is_recoverable = error_data.get('is_recoverable', True)
            suggested_action = error_data.get('suggested_action', 'Try restarting the operation')
        
        # Update status card
        self.status_card.content.controls[0].controls[0].icon = ft.Icons.ERROR
        self.status_card.content.controls[0].controls[1].value = "Status: Error"
        self.status_card.content.controls[2].value = f"Error: {error_msg[:100]}{'...' if len(error_msg) > 100 else ''}"
        self.status_card.bgcolor = ft.Colors.RED_50
        self.status_card.border = ft.border.all(1, ft.Colors.RED_200)
        
        # Update buttons based on error recoverability
        self.start_button.visible = is_recoverable
        self.start_button.text = "Retry Grading" if is_recoverable else "Start New Grading"
        self.pause_button.visible = False
        self.cancel_button.visible = False
        self.back_button.disabled = False
        
        # Add error details button
        self._add_error_details_button(error_data if not isinstance(error_data, str) else None)
        
        # Add error activity entry
        self._add_activity_entry(f"Error: {error_msg}", is_error=True)
        
        # Show error dialog for serious errors
        if not isinstance(error_data, str) and not is_recoverable:
            self._show_error_dialog(error_data)
        
        self.page.update()
    
    def _add_error_details_button(self, error_data):
        """Add button to show error details"""
        if error_data and hasattr(self, 'control_buttons'):
            # Add error details button
            error_button = ft.ElevatedButton(
                text="View Error Details",
                icon=ft.Icons.ERROR_OUTLINE,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.RED_600
                ),
                on_click=lambda e: self._show_error_dialog(error_data)
            )
            
            # Insert error button into control buttons row
            try:
                button_row = self.control_buttons.content
                if len(button_row.controls) >= 3:  # back, spacer, start button
                    button_row.controls.insert(-1, error_button)  # Insert before start button
                    button_row.controls.insert(-1, ft.Container(width=10))  # Add spacer
            except (AttributeError, IndexError):
                pass  # Graceful fallback
    
    def _show_error_dialog(self, error_data):
        """Show detailed error dialog with recovery options"""
        if not error_data:
            return
        
        error_msg = error_data.get('error', 'Unknown error')
        error_type = error_data.get('error_type', 'Error')
        is_recoverable = error_data.get('is_recoverable', True)
        suggested_action = error_data.get('suggested_action', 'Try restarting the operation')
        retry_attempts = error_data.get('retry_attempts', 0)
        partial_file = error_data.get('partial_results_file')
        completed_students = error_data.get('completed_students', 0)
        total_students = error_data.get('total_students', 0)
        recovery_suggestions = error_data.get('recovery_suggestions', [])
        
        # Build error content
        error_content = ft.Column([
            ft.Row([
                ft.Icon(
                    ft.Icons.ERROR if not is_recoverable else ft.Icons.WARNING,
                    color=ft.Colors.RED_600 if not is_recoverable else ft.Colors.ORANGE_600,
                    size=32
                ),
                ft.Column([
                    ft.Text(
                        f"{error_type}: {error_msg}",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.RED_800 if not is_recoverable else ft.Colors.ORANGE_800
                    ),
                    ft.Text(
                        f"Recoverable: {'Yes' if is_recoverable else 'No'}",
                        size=12,
                        color=ft.Colors.GREY_600
                    )
                ], expand=True, spacing=5)
            ], spacing=15),
            
            ft.Divider(),
            
            # Progress information
            ft.Text("Progress Information:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(f"• Completed: {completed_students} of {total_students} students"),
            ft.Text(f"• Retry attempts: {retry_attempts}"),
            
            ft.Container(height=10),
            
            # Suggested action
            ft.Text("Suggested Action:", size=14, weight=ft.FontWeight.BOLD),
            ft.Text(suggested_action, color=ft.Colors.BLUE_700),
            
            ft.Container(height=10),
        ], spacing=10)
        
        # Add recovery suggestions if available
        if recovery_suggestions:
            error_content.controls.extend([
                ft.Text("Recovery Suggestions:", size=14, weight=ft.FontWeight.BOLD),
                ft.Column([
                    ft.Text(f"• {suggestion}", size=12) 
                    for suggestion in recovery_suggestions
                ], spacing=5),
                ft.Container(height=10)
            ])
        
        # Add partial results info
        if partial_file:
            error_content.controls.extend([
                ft.Text("Partial Results:", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(f"Partial results saved to: {partial_file}", size=11, color=ft.Colors.GREY_600),
                ft.Text("You can attempt to recover from this point.", size=11, color=ft.Colors.BLUE_600),
                ft.Container(height=10)
            ])
        
        # Dialog actions
        actions = [
            ft.TextButton("Close", on_click=self._close_error_dialog)
        ]
        
        if is_recoverable:
            actions.insert(0, ft.TextButton(
                "Retry Now", 
                on_click=lambda e: self._retry_from_error_dialog()
            ))
        
        if partial_file:
            actions.insert(-1, ft.TextButton(
                "Export Error Report",
                on_click=lambda e: self._export_error_report(error_data)
            ))
        
        # Create dialog
        self.error_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Grading Error Details"),
            content=ft.Container(
                content=error_content,
                width=600,
                height=400
            ),
            actions=actions,
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog = self.error_dialog
        self.error_dialog.open = True
        self.page.update()
    
    def _close_error_dialog(self, e):
        """Close the error dialog"""
        if self.error_dialog:
            self.error_dialog.open = False
            self.page.update()
    
    def _retry_from_error_dialog(self):
        """Retry grading from error dialog"""
        self._close_error_dialog(None)
        asyncio.create_task(self._start_processing())
    
    def _export_error_report(self, error_data):
        """Export detailed error report"""
        try:
            from datetime import datetime
            import json
            from pathlib import Path
            
            # Create error report
            report = {
                'timestamp': datetime.now().isoformat(),
                'error_details': error_data,
                'system_info': {
                    'assignment': self.config_data.get('assignment_name', 'Unknown'),
                    'config': self.config_data.get('configuration', {}),
                    'log_entries': self.grader_service.get_log_entries(last_n=50)
                }
            }
            
            # Save to user's home directory
            home_dir = Path.home()
            report_file = home_dir / f"grader_error_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Error report exported to {report_file}"),
                    action="OK"
                )
            )
            
        except Exception as e:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Failed to export error report: {str(e)}"),
                    action="OK"
                )
            )
    
    def _on_progress_update(self, update: ProgressUpdate):
        """Handle progress updates from grader service"""
        self.progress_updates.append(update)
        self.current_status = update.status
        
        # Update basic progress bar
        if update.total_count > 0:
            self.progress_percentage = update.completed_count / update.total_count
            self.progress_bar.value = self.progress_percentage
            self.progress_text.value = f"{int(self.progress_percentage * 100)}% Complete"
            self.student_progress_text.value = f"{update.completed_count} of {update.total_count} submissions processed"
        
        # Update current operation
        if update.current_operation:
            self.current_operation_text.value = update.current_operation
        
        # Update advanced progress tracking
        if update.current_student:
            # Extract student ID from current_student string
            student_id = self._extract_student_id(update.current_student)
            
            if student_id:
                # Determine status based on the update status
                if update.status.name == 'COMPLETED' or update.completed_count > 0:
                    # Check if this is a new completion
                    prev_completed = len([s for s in self.progress_updates[:-1] 
                                        if s.completed_count > 0 and 
                                        self._extract_student_id(getattr(s, 'current_student', '')) == student_id])
                    
                    if prev_completed == 0 or update.completed_count > prev_completed:
                        # This student just completed
                        score = getattr(update, 'score', None)  # If available
                        cost = getattr(update, 'cost_increment', 0.0)  # If available
                        self.advanced_progress_bar.update_student_progress(student_id, 'completed', score, cost)
                        self.student_tracker.update_student(student_id, 'completed', score, cost)
                        self._add_activity_entry(f"Completed grading for {student_id}")
                    else:
                        # Student is currently processing
                        self.advanced_progress_bar.update_student_progress(student_id, 'processing')
                        self.student_tracker.update_student(student_id, 'processing')
                elif update.status.name == 'ERROR':
                    # Student processing failed
                    error_msg = getattr(update, 'error_message', 'Processing failed')
                    self.advanced_progress_bar.update_student_progress(student_id, 'error', error_message=error_msg)
                    self.student_tracker.update_student(student_id, 'error')
                    self._add_activity_entry(f"Error processing {student_id}: {error_msg}", is_error=True)
                else:
                    # Student is currently processing
                    self.advanced_progress_bar.update_student_progress(student_id, 'processing')
                    self.student_tracker.update_student(student_id, 'processing')
        
        # Update cost tracking
        if hasattr(update, 'cost_used') and update.cost_used > 0:
            # Update cost tracker display
            try:
                cost_controls = self.cost_tracker.content.controls[2].controls
                cost_controls[0].controls[1].value = f"${update.cost_used:.2f}"
                
                # Update estimated vs used
                if hasattr(update, 'cost_estimated') and update.cost_estimated > 0:
                    remaining = max(0, update.cost_estimated - update.cost_used)
                    cost_controls[1].controls[1].value = f"${update.cost_estimated:.2f}"
                    cost_controls[2].controls[1].value = f"${remaining:.2f}"
            except (AttributeError, IndexError):
                pass  # Graceful fallback if cost tracker structure differs
        
        # Update time tracking with progress summary
        try:
            progress_summary = self.advanced_progress_bar.get_progress_summary()
            time_controls = self.time_tracker.content.controls[2].controls
            
            # Update elapsed time
            if self.start_time:
                elapsed = datetime.now() - self.start_time
                hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    elapsed_str = f"{minutes:02d}:{seconds:02d}"
                time_controls[0].controls[1].value = elapsed_str
            
            # Update estimated completion
            if progress_summary.get('estimated_completion'):
                est_completion = progress_summary['estimated_completion']
                remaining = est_completion - datetime.now()
                if remaining.total_seconds() > 0:
                    hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                    minutes, _ = divmod(remainder, 60)
                    if hours > 0:
                        remaining_str = f"{hours}h {minutes}m"
                    else:
                        remaining_str = f"{minutes}m"
                    time_controls[2].controls[1].value = remaining_str
                    
                    # Also update estimated time
                    est_total = est_completion - self.start_time
                    est_hours, est_remainder = divmod(int(est_total.total_seconds()), 3600)
                    est_minutes, _ = divmod(est_remainder, 60)
                    if est_hours > 0:
                        est_str = f"{est_hours}h {est_minutes}m"
                    else:
                        est_str = f"{est_minutes}m"
                    time_controls[1].controls[1].value = est_str
        except (AttributeError, IndexError, KeyError):
            pass  # Graceful fallback
        
        # Add to activity log
        if update.message:
            self._add_activity_entry(update.message)
        
        self.page.update()
    
    def _extract_student_id(self, current_student_string: str) -> Optional[str]:
        """Extract student ID from progress update string
        
        Args:
            current_student_string: String containing student information
            
        Returns:
            Extracted student ID or None
        """
        if not current_student_string:
            return None
        
        # Handle different formats:
        # "student_12345.zip", "Processing submission: student_12345.zip", "[1/25] student_12345"
        import re
        
        # Try to extract student ID from various patterns
        patterns = [
            r'student_(\d+)',  # student_12345
            r'(\w+)\.zip',     # filename.zip
            r'submission:\s*(\S+)',  # "Processing submission: filename"
            r'\]\s*(\S+)',     # "[1/25] student_name"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, current_student_string)
            if match:
                return match.group(1) if 'student_' in pattern else match.group(0).replace('.zip', '')
        
        # Fallback: use the string as-is, cleaned up
        return current_student_string.strip().replace('.zip', '').split('/')[-1]
    
    def _add_activity_entry(self, message: str, is_error: bool = False):
        """Add an entry to the activity log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        color = ft.Colors.RED_700 if is_error else ft.Colors.GREY_700
        
        entry = ft.Container(
            content=ft.Row([
                ft.Text(
                    timestamp,
                    size=10,
                    color=ft.Colors.GREY_500,
                    width=60
                ),
                ft.Text(
                    message,
                    size=11,
                    color=color
                )
            ], spacing=10),
            padding=ft.padding.symmetric(vertical=2)
        )
        
        # Add to list
        self.activity_list.controls.append(entry)
        
        # Keep only last N entries
        if len(self.activity_list.controls) > self.max_log_entries:
            self.activity_list.controls.pop(0)
        
        # Auto-scroll to bottom
        self.activity_list.auto_scroll = True
        
        self.page.update()
    
    def _clear_activity_log(self, e):
        """Clear the activity log"""
        self.activity_list.controls.clear()
        self._add_activity_entry("Activity log cleared")
    
    def _show_detailed_logs(self, e):
        """Show detailed CLI logs in a dialog"""
        # Get logs from grader service
        log_entries = self.grader_service.get_log_entries()
        
        # Create log list view
        log_list = ft.ListView(
            height=400,
            spacing=2,
            padding=ft.padding.all(10)
        )
        
        # Populate with log entries
        for entry in log_entries:
            log_list.controls.append(
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Text(
                                entry['timestamp'],
                                size=10,
                                color=ft.Colors.GREY_500,
                                width=60
                            ),
                            ft.Text(
                                entry['message'],
                                size=10,
                                color=ft.Colors.BLACK87,
                                expand=True,
                                selectable=True
                            )
                        ],
                        spacing=10
                    ),
                    padding=ft.padding.symmetric(vertical=1)
                )
            )
        
        # Create export button
        def export_logs(e):
            import os
            from pathlib import Path
            
            # Default export path
            home_dir = Path.home()
            default_filename = f"grader_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            default_path = home_dir / default_filename
            
            try:
                self.grader_service.export_log_to_file(str(default_path))
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Logs exported to {default_path}"),
                        action="OK"
                    )
                )
            except Exception as ex:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Export failed: {str(ex)}"),
                        action="OK"
                    )
                )
        
        # Create dialog
        self.log_viewer_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Detailed CLI Logs"),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Text(
                            f"Showing {len(log_entries)} log entries",
                            size=12,
                            color=ft.Colors.GREY_600
                        ),
                        ft.Container(height=10),
                        log_list
                    ],
                    spacing=0
                ),
                width=800,
                height=450
            ),
            actions=[
                ft.TextButton("Export", on_click=export_logs),
                ft.TextButton("Close", on_click=self._close_log_viewer)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = self.log_viewer_dialog
        self.log_viewer_dialog.open = True
        self.page.update()
    
    def _close_log_viewer(self, e):
        """Close the log viewer dialog"""
        if self.log_viewer_dialog:
            self.log_viewer_dialog.open = False
            self.page.update()
    
    def _on_start_clicked(self, e):
        """Handle start button click"""
        asyncio.create_task(self._start_processing())
    
    def _on_pause_clicked(self, e):
        """Handle pause button click"""
        self.grader_service.pause_grading()
        self._add_activity_entry("Grading paused by user")
    
    def _on_cancel_clicked(self, e):
        """Handle cancel button click"""
        self.grader_service.cancel_grading()
        self._add_activity_entry("Grading cancelled by user")
        
        # Reset UI
        self.is_processing = False
        self.start_button.visible = True
        self.pause_button.visible = False
        self.cancel_button.visible = False
        self.back_button.disabled = False
        
        self.page.update()
    
    def _on_back_clicked(self, e):
        """Handle back button click"""
        if self.on_back_to_config:
            self.on_back_to_config()
    
    def _on_view_results_clicked(self, e):
        """Handle view results button click"""
        if self.on_view_results and self.processing_results:
            self.on_view_results(self.processing_results)


def main():
    """Test the processing page"""
    def test_app(page: ft.Page):
        page.title = "Processing Page Test"
        page.window.width = 1000
        page.window.height = 800
        
        # Mock config data
        mock_config = {
            'submissions_folder': '/path/to/submissions',
            'assignment_name': 'weatherwise',
            'roster_file': '/path/to/roster.csv',
            'configuration': {
                'github_enabled': True,
                'preprocessing_enabled': True,
                'dry_run': False
            }
        }
        
        def on_processing_complete(results):
            print(f"Processing complete: {results}")
        
        def on_view_results(results):
            print(f"View results: {results}")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Would navigate to results page"),
                    action="OK"
                )
            )
        
        def on_back_to_config():
            print("Back to configuration")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Would navigate back to configuration"),
                    action="OK"
                )
            )
        
        processing_page = ProcessingPage(
            page,
            mock_config,
            on_processing_complete,
            on_view_results,
            on_back_to_config
        )
        
        page.add(processing_page.build())
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()