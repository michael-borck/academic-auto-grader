"""
Application Settings Page Component

Provides comprehensive interface for managing application-level settings including
logging configuration, update checking, diagnostics, and performance tuning.
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

from app.services.application_settings_service import (
    ApplicationSettingsService,
    LogLevel,
    UpdateChannel,
    ApplicationSettings,
    LoggingSettings,
    UpdateSettings,
    PerformanceSettings,
    DiagnosticsSettings,
    SecuritySettings
)


class ApplicationSettingsPage:
    """Application Settings page component
    
    Provides comprehensive interface for managing application-level settings
    with real-time updates and system diagnostics.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        on_close: Callable[[], None] = None
    ):
        """Initialize the application settings page
        
        Args:
            page: Flet page object
            on_close: Callback when settings page is closed
        """
        self.page = page
        self.on_close = on_close
        
        # Services
        self.settings_service = ApplicationSettingsService()
        
        # Current settings
        self.settings = self.settings_service.get_settings()
        
        # UI components
        self.logging_controls = {}
        self.update_controls = {}
        self.performance_controls = {}
        self.diagnostics_controls = {}
        self.security_controls = {}
        
        # Track changes
        self.has_unsaved_changes = False
        
        # Update checking state
        self.update_check_in_progress = False
    
    def build(self) -> ft.Control:
        """Build and return the application settings UI"""
        
        # Page header
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    "🔧 Application Settings",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Configure logging, updates, performance, and diagnostics",
                    size=16,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=30)
        )
        
        # Create settings sections
        logging_section = self._build_logging_section()
        updates_section = self._build_updates_section()
        performance_section = self._build_performance_section()
        diagnostics_section = self._build_diagnostics_section()
        security_section = self._build_security_section()
        
        # Action buttons
        action_buttons = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    text="💾 Save Settings",
                    icon=ft.Icons.SAVE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.GREEN_600
                    ),
                    on_click=self._save_settings,
                    disabled=not self.has_unsaved_changes
                ),
                ft.ElevatedButton(
                    text="🔄 Check for Updates",
                    icon=ft.Icons.UPDATE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600
                    ),
                    on_click=self._check_for_updates,
                    disabled=self.update_check_in_progress
                ),
                ft.ElevatedButton(
                    text="📊 System Diagnostics",
                    icon=ft.Icons.COMPUTER,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.PURPLE_600
                    ),
                    on_click=self._show_diagnostics
                ),
                ft.ElevatedButton(
                    text="🗂️ View Logs",
                    icon=ft.Icons.ARTICLE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.ORANGE_600
                    ),
                    on_click=self._show_logs
                ),
                ft.ElevatedButton(
                    text="🔄 Reset to Defaults",
                    icon=ft.Icons.RESTORE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.RED_600
                    ),
                    on_click=self._reset_to_defaults
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    text="Close",
                    icon=ft.Icons.CLOSE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREY_700,
                        bgcolor=ft.Colors.GREY_200
                    ),
                    on_click=self._close_settings
                )
            ]),
            padding=ft.padding.symmetric(vertical=20)
        )
        
        # Main content with tabs
        tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Logging",
                    icon=ft.Icons.ARTICLE,
                    content=logging_section
                ),
                ft.Tab(
                    text="Updates",
                    icon=ft.Icons.UPDATE,
                    content=updates_section
                ),
                ft.Tab(
                    text="Performance",
                    icon=ft.Icons.SPEED,
                    content=performance_section
                ),
                ft.Tab(
                    text="Diagnostics",
                    icon=ft.Icons.BUG_REPORT,
                    content=diagnostics_section
                ),
                ft.Tab(
                    text="Security",
                    icon=ft.Icons.SECURITY,
                    content=security_section
                )
            ],
            expand=True
        )
        
        # Main content layout
        content = ft.Container(
            content=ft.Column([
                header,
                tabs,
                action_buttons
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
            ),
            padding=ft.padding.all(40),
            alignment=ft.alignment.top_center,
            expand=True
        )
        
        return content
    
    def _build_logging_section(self) -> ft.Container:
        """Build logging settings section"""
        
        # Log level dropdown
        log_level_dropdown = ft.Dropdown(
            label="Log Level",
            options=[
                ft.dropdown.Option(text=level.value, key=level.value)
                for level in LogLevel
            ],
            value=self.settings.logging.level.value,
            on_change=self._on_setting_change,
            width=150
        )
        
        # File logging settings
        enable_file_logging = ft.Checkbox(
            label="Enable file logging",
            value=self.settings.logging.enable_file_logging,
            on_change=self._on_setting_change
        )
        
        log_file_path = ft.TextField(
            label="Log file path",
            value=self.settings.logging.log_file_path,
            width=400,
            on_change=self._on_setting_change
        )
        
        max_log_size = ft.TextField(
            label="Max log file size (MB)",
            value=str(self.settings.logging.max_log_file_size),
            width=150,
            on_change=self._on_setting_change
        )
        
        max_log_files = ft.TextField(
            label="Max log files to keep",
            value=str(self.settings.logging.max_log_files),
            width=150,
            on_change=self._on_setting_change
        )
        
        # Console logging
        enable_console_logging = ft.Checkbox(
            label="Enable console logging",
            value=self.settings.logging.enable_console_logging,
            on_change=self._on_setting_change
        )
        
        # Log format
        log_format = ft.TextField(
            label="Log format",
            value=self.settings.logging.log_format,
            width=600,
            multiline=True,
            min_lines=2,
            max_lines=3,
            on_change=self._on_setting_change
        )
        
        # Store references
        self.logging_controls = {
            "level": log_level_dropdown,
            "enable_file_logging": enable_file_logging,
            "log_file_path": log_file_path,
            "max_log_file_size": max_log_size,
            "max_log_files": max_log_files,
            "enable_console_logging": enable_console_logging,
            "log_format": log_format
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Logging Configuration", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Log Level:", weight=ft.FontWeight.BOLD),
                        log_level_dropdown
                    ]),
                    ft.Container(width=30),
                    ft.Column([
                        enable_file_logging,
                        enable_console_logging
                    ])
                ]),
                
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=15),
                
                ft.Text("File Logging Settings", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                log_file_path,
                ft.Container(height=10),
                
                ft.Row([
                    max_log_size,
                    ft.Container(width=20),
                    max_log_files
                ]),
                
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=15),
                
                ft.Text("Log Format", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                log_format,
                ft.Container(height=10),
                
                ft.Text(
                    "Format variables: %(asctime)s, %(name)s, %(levelname)s, %(message)s",
                    size=12,
                    color=ft.Colors.GREY_600
                )
            ], spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=10
        )
    
    def _build_updates_section(self) -> ft.Container:
        """Build updates settings section"""
        
        # Auto-check settings
        auto_check_enabled = ft.Checkbox(
            label="Enable automatic update checking",
            value=self.settings.updates.auto_check_enabled,
            on_change=self._on_setting_change
        )
        
        check_interval = ft.TextField(
            label="Check interval (hours)",
            value=str(self.settings.updates.check_interval_hours),
            width=150,
            on_change=self._on_setting_change
        )
        
        # Update channel
        update_channel = ft.Dropdown(
            label="Update Channel",
            options=[
                ft.dropdown.Option(text=channel.value.title(), key=channel.value)
                for channel in UpdateChannel
            ],
            value=self.settings.updates.update_channel.value,
            on_change=self._on_setting_change,
            width=150
        )
        
        # Notification settings
        notify_on_updates = ft.Checkbox(
            label="Notify when updates are available",
            value=self.settings.updates.notify_on_updates,
            on_change=self._on_setting_change
        )
        
        auto_download = ft.Checkbox(
            label="Automatically download updates",
            value=self.settings.updates.auto_download,
            on_change=self._on_setting_change
        )
        
        include_prereleases = ft.Checkbox(
            label="Include pre-release versions",
            value=self.settings.updates.include_prereleases,
            on_change=self._on_setting_change
        )
        
        # Last check info
        last_check_text = ft.Text(
            f"Last checked: {self.settings.updates.last_check_time or 'Never'}",
            size=12,
            color=ft.Colors.GREY_600
        )
        
        # Store references
        self.update_controls = {
            "auto_check_enabled": auto_check_enabled,
            "check_interval_hours": check_interval,
            "update_channel": update_channel,
            "notify_on_updates": notify_on_updates,
            "auto_download": auto_download,
            "include_prereleases": include_prereleases
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Update Settings", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                auto_check_enabled,
                ft.Container(height=10),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Check Interval:", weight=ft.FontWeight.BOLD),
                        check_interval
                    ]),
                    ft.Container(width=30),
                    ft.Column([
                        ft.Text("Update Channel:", weight=ft.FontWeight.BOLD),
                        update_channel
                    ])
                ]),
                
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=15),
                
                ft.Text("Update Options", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                ft.Column([
                    notify_on_updates,
                    auto_download,
                    include_prereleases
                ], spacing=10),
                
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=15),
                
                ft.Text("Update Status", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                last_check_text,
                ft.Container(height=10),
                
                ft.Text(
                    "💡 Stable channel is recommended for production use. "
                    "Beta and Development channels may contain unstable features.",
                    size=12,
                    color=ft.Colors.BLUE_600
                )
            ], spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=10
        )
    
    def _build_performance_section(self) -> ft.Container:
        """Build performance settings section"""
        
        # Memory settings
        max_memory = ft.TextField(
            label="Max memory usage (MB)",
            value=str(self.settings.performance.max_memory_usage_mb),
            width=150,
            on_change=self._on_setting_change
        )
        
        # CPU settings
        max_threads = ft.TextField(
            label="Max CPU threads (0 = auto)",
            value=str(self.settings.performance.max_cpu_threads),
            width=150,
            on_change=self._on_setting_change
        )
        
        # Hardware acceleration
        hardware_accel = ft.Checkbox(
            label="Enable hardware acceleration",
            value=self.settings.performance.enable_hardware_acceleration,
            on_change=self._on_setting_change
        )
        
        # Cache settings
        cache_size = ft.TextField(
            label="Cache size (MB)",
            value=str(self.settings.performance.cache_size_mb),
            width=150,
            on_change=self._on_setting_change
        )
        
        # Background processing
        background_processing = ft.Checkbox(
            label="Enable background processing",
            value=self.settings.performance.enable_background_processing,
            on_change=self._on_setting_change
        )
        
        # Concurrent operations
        max_concurrent = ft.TextField(
            label="Max concurrent operations",
            value=str(self.settings.performance.max_concurrent_operations),
            width=150,
            on_change=self._on_setting_change
        )
        
        # Process priority
        process_priority = ft.Dropdown(
            label="Process Priority",
            options=[
                ft.dropdown.Option(text="Low", key="low"),
                ft.dropdown.Option(text="Normal", key="normal"),
                ft.dropdown.Option(text="High", key="high")
            ],
            value=self.settings.performance.process_priority,
            on_change=self._on_setting_change,
            width=150
        )
        
        # Store references
        self.performance_controls = {
            "max_memory_usage_mb": max_memory,
            "max_cpu_threads": max_threads,
            "enable_hardware_acceleration": hardware_accel,
            "cache_size_mb": cache_size,
            "enable_background_processing": background_processing,
            "max_concurrent_operations": max_concurrent,
            "process_priority": process_priority
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Performance Settings", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                ft.Text("Resource Limits", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                ft.Row([
                    max_memory,
                    ft.Container(width=20),
                    max_threads,
                    ft.Container(width=20),
                    cache_size
                ]),
                
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=15),
                
                ft.Text("Processing Options", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                ft.Column([
                    hardware_accel,
                    background_processing
                ], spacing=10),
                
                ft.Container(height=15),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Concurrency:", weight=ft.FontWeight.BOLD),
                        max_concurrent
                    ]),
                    ft.Container(width=30),
                    ft.Column([
                        ft.Text("Priority:", weight=ft.FontWeight.BOLD),
                        process_priority
                    ])
                ]),
                
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=15),
                
                ft.Text(
                    "⚠️ Changing these settings may affect application performance and stability. "
                    "High priority and excessive resource usage may impact system responsiveness.",
                    size=12,
                    color=ft.Colors.ORANGE_600
                )
            ], spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=10
        )
    
    def _build_diagnostics_section(self) -> ft.Container:
        """Build diagnostics settings section"""
        
        # Crash reporting
        crash_reporting = ft.Checkbox(
            label="Enable crash reporting",
            value=self.settings.diagnostics.enable_crash_reporting,
            on_change=self._on_setting_change
        )
        
        # Usage analytics
        usage_analytics = ft.Checkbox(
            label="Enable usage analytics",
            value=self.settings.diagnostics.enable_usage_analytics,
            on_change=self._on_setting_change
        )
        
        # Performance monitoring
        performance_monitoring = ft.Checkbox(
            label="Enable performance monitoring",
            value=self.settings.diagnostics.enable_performance_monitoring,
            on_change=self._on_setting_change
        )
        
        # System info collection
        system_info = ft.Checkbox(
            label="Collect system information",
            value=self.settings.diagnostics.collect_system_info,
            on_change=self._on_setting_change
        )
        
        # Send diagnostic data
        send_diagnostic = ft.Checkbox(
            label="Send diagnostic data to developers",
            value=self.settings.diagnostics.send_diagnostic_data,
            on_change=self._on_setting_change
        )
        
        # Diagnostic level
        diagnostic_level = ft.Dropdown(
            label="Diagnostic Level",
            options=[
                ft.dropdown.Option(text="Basic", key="basic"),
                ft.dropdown.Option(text="Detailed", key="detailed"),
                ft.dropdown.Option(text="Full", key="full")
            ],
            value=self.settings.diagnostics.diagnostic_level,
            on_change=self._on_setting_change,
            width=150
        )
        
        # Store references
        self.diagnostics_controls = {
            "enable_crash_reporting": crash_reporting,
            "enable_usage_analytics": usage_analytics,
            "enable_performance_monitoring": performance_monitoring,
            "collect_system_info": system_info,
            "send_diagnostic_data": send_diagnostic,
            "diagnostic_level": diagnostic_level
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Diagnostics & Telemetry", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                ft.Text("Data Collection", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                ft.Column([
                    crash_reporting,
                    usage_analytics,
                    performance_monitoring,
                    system_info
                ], spacing=10),
                
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=15),
                
                ft.Text("Data Sharing", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                send_diagnostic,
                ft.Container(height=15),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Detail Level:", weight=ft.FontWeight.BOLD),
                        diagnostic_level
                    ])
                ]),
                
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=15),
                
                ft.Text(
                    "🛡️ Privacy: All diagnostic data is anonymized and used only for improving the application. "
                    "No personally identifiable information or grading data is included.",
                    size=12,
                    color=ft.Colors.GREEN_600
                )
            ], spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=10
        )
    
    def _build_security_section(self) -> ft.Container:
        """Build security settings section"""
        
        # Connection security
        secure_connections = ft.Checkbox(
            label="Use secure connections (HTTPS)",
            value=self.settings.security.enable_secure_connections,
            on_change=self._on_setting_change
        )
        
        verify_ssl = ft.Checkbox(
            label="Verify SSL certificates",
            value=self.settings.security.verify_ssl_certificates,
            on_change=self._on_setting_change
        )
        
        # Local encryption
        local_encryption = ft.Checkbox(
            label="Enable local data encryption",
            value=self.settings.security.enable_local_encryption,
            on_change=self._on_setting_change
        )
        
        # Session management
        clear_on_exit = ft.Checkbox(
            label="Clear sensitive data on exit",
            value=self.settings.security.clear_sensitive_data_on_exit,
            on_change=self._on_setting_change
        )
        
        session_timeout = ft.TextField(
            label="Session timeout (minutes)",
            value=str(self.settings.security.session_timeout_minutes),
            width=150,
            on_change=self._on_setting_change
        )
        
        # Confirmation settings
        require_confirmation = ft.Checkbox(
            label="Require confirmation for sensitive operations",
            value=self.settings.security.require_confirmation_for_sensitive_ops,
            on_change=self._on_setting_change
        )
        
        # Store references
        self.security_controls = {
            "enable_secure_connections": secure_connections,
            "verify_ssl_certificates": verify_ssl,
            "enable_local_encryption": local_encryption,
            "clear_sensitive_data_on_exit": clear_on_exit,
            "session_timeout_minutes": session_timeout,
            "require_confirmation_for_sensitive_ops": require_confirmation
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text("Security & Privacy", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=15),
                
                ft.Text("Connection Security", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                ft.Column([
                    secure_connections,
                    verify_ssl
                ], spacing=10),
                
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=15),
                
                ft.Text("Data Protection", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=10),
                
                ft.Column([
                    local_encryption,
                    clear_on_exit,
                    require_confirmation
                ], spacing=10),
                
                ft.Container(height=15),
                
                ft.Row([
                    ft.Column([
                        ft.Text("Session Timeout:", weight=ft.FontWeight.BOLD),
                        session_timeout
                    ])
                ]),
                
                ft.Container(height=20),
                ft.Divider(),
                ft.Container(height=15),
                
                ft.Text(
                    "🔐 Security recommendations: Keep SSL verification enabled, use local encryption for sensitive data, "
                    "and require confirmations for critical operations.",
                    size=12,
                    color=ft.Colors.BLUE_600
                )
            ], spacing=5),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=10
        )
    
    def _on_setting_change(self, e):
        """Handle setting changes"""
        self._mark_unsaved_changes()
    
    def _save_settings(self, e):
        """Save all settings changes"""
        try:
            # Collect logging updates
            logging_updates = {}
            for key, control in self.logging_controls.items():
                if hasattr(control, 'value'):
                    if key == "level":
                        logging_updates[key] = control.value
                    elif key in ["max_log_file_size", "max_log_files"]:
                        try:
                            logging_updates[key] = int(control.value)
                        except ValueError:
                            pass
                    else:
                        logging_updates[key] = control.value
            
            # Collect update settings
            update_updates = {}
            for key, control in self.update_controls.items():
                if hasattr(control, 'value'):
                    if key == "check_interval_hours":
                        try:
                            update_updates[key] = int(control.value)
                        except ValueError:
                            pass
                    else:
                        update_updates[key] = control.value
            
            # Collect performance settings
            performance_updates = {}
            for key, control in self.performance_controls.items():
                if hasattr(control, 'value'):
                    if key in ["max_memory_usage_mb", "max_cpu_threads", "cache_size_mb", "max_concurrent_operations"]:
                        try:
                            performance_updates[key] = int(control.value)
                        except ValueError:
                            pass
                    else:
                        performance_updates[key] = control.value
            
            # Collect diagnostics settings
            diagnostics_updates = {}
            for key, control in self.diagnostics_controls.items():
                if hasattr(control, 'value'):
                    diagnostics_updates[key] = control.value
            
            # Collect security settings
            security_updates = {}
            for key, control in self.security_controls.items():
                if hasattr(control, 'value'):
                    if key == "session_timeout_minutes":
                        try:
                            security_updates[key] = int(control.value)
                        except ValueError:
                            pass
                    else:
                        security_updates[key] = control.value
            
            # Apply all updates
            success = all([
                self.settings_service.update_logging_settings(**logging_updates),
                self.settings_service.update_update_settings(**update_updates),
                self.settings_service.update_performance_settings(**performance_updates),
                self.settings_service.update_diagnostics_settings(**diagnostics_updates),
                self.settings_service.update_security_settings(**security_updates)
            ])
            
            if success:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Settings saved successfully!"))
                )
                self.has_unsaved_changes = False
                self._update_action_buttons()
            else:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to save some settings"))
                )
        
        except Exception as ex:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Error saving settings: {str(ex)}"))
            )
    
    async def _check_for_updates(self, e):
        """Check for application updates"""
        if self.update_check_in_progress:
            return
        
        self.update_check_in_progress = True
        self._update_action_buttons()
        
        try:
            # Show progress
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Checking for updates..."))
            )
            
            # Check for updates
            result = await self.settings_service.check_for_updates(force=True)
            
            if result.get("update_available"):
                # Show update available dialog
                self._show_update_available_dialog(result)
            else:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text(result.get("message", "No updates available")))
                )
        
        except Exception as ex:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Update check failed: {str(ex)}"))
            )
        
        finally:
            self.update_check_in_progress = False
            self._update_action_buttons()
    
    def _show_update_available_dialog(self, update_info: Dict[str, Any]):
        """Show update available dialog"""
        content = ft.Column([
            ft.Text(f"Version {update_info['latest_version']} is available!", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(f"Current version: {update_info['current_version']}"),
            ft.Container(height=10),
            ft.Text("Release Notes:", weight=ft.FontWeight.BOLD),
            ft.Text(update_info.get("release_notes", "No release notes available")),
            ft.Container(height=10),
            ft.Text(f"Release Date: {update_info.get('release_date', 'Unknown')}"),
            ft.Text(f"Download Size: {update_info.get('size_mb', 0):.1f} MB")
        ])
        
        def download_update(e):
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Download functionality would open browser to download page"))
            )
            self._close_dialog(update_dialog)
        
        update_dialog = ft.AlertDialog(
            title=ft.Text("Update Available"),
            content=ft.Container(content=content, width=400),
            actions=[
                ft.TextButton("Later", on_click=lambda e: self._close_dialog(update_dialog)),
                ft.ElevatedButton("Download", on_click=download_update)
            ],
            modal=True
        )
        
        self.page.dialog = update_dialog
        update_dialog.open = True
        self.page.update()
    
    def _show_diagnostics(self, e):
        """Show system diagnostics dialog"""
        # Get diagnostics (this might take a moment)
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text("Collecting system diagnostics..."))
        )
        
        try:
            diagnostics = self.settings_service.get_system_diagnostics()
            
            # Create diagnostics display
            diag_content = ft.ListView(
                controls=[
                    ft.Text("System Diagnostics", size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Text(f"Timestamp: {diagnostics.get('timestamp', 'Unknown')}"),
                    ft.Container(height=15),
                    
                    ft.Text("Application Info:", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Version: {diagnostics.get('application', {}).get('version', 'Unknown')}"),
                    ft.Text(f"Python: {diagnostics.get('application', {}).get('python_version', 'Unknown')[:50]}..."),
                    ft.Container(height=10),
                    
                    ft.Text("System Info:", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Platform: {diagnostics.get('system', {}).get('platform', 'Unknown')}"),
                    ft.Text(f"Hostname: {diagnostics.get('system', {}).get('hostname', 'Unknown')}"),
                    ft.Container(height=10),
                    
                    ft.Text("Performance:", weight=ft.FontWeight.BOLD),
                    ft.Text(f"CPU Usage: {diagnostics.get('performance', {}).get('cpu_percent', 'N/A')}%"),
                    ft.Text(f"Memory: {diagnostics.get('performance', {}).get('memory_percent', 'N/A')}%")
                ],
                height=400
            )
            
            diag_dialog = ft.AlertDialog(
                title=ft.Text("System Diagnostics"),
                content=ft.Container(content=diag_content, width=500, height=450),
                actions=[
                    ft.TextButton("Close", on_click=lambda e: self._close_dialog(diag_dialog))
                ],
                modal=True
            )
            
            self.page.dialog = diag_dialog
            diag_dialog.open = True
            self.page.update()
        
        except Exception as ex:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Failed to collect diagnostics: {str(ex)}"))
            )
    
    def _show_logs(self, e):
        """Show log files dialog"""
        log_files = self.settings_service.get_log_files()
        
        if not log_files:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("No log files found"))
            )
            return
        
        # Create log files list
        log_controls = []
        for log_file in log_files:
            log_controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(log_file["name"], weight=ft.FontWeight.BOLD),
                            ft.Text(f"Size: {log_file['size_mb']:.2f} MB"),
                            ft.Text(f"Modified: {log_file['modified'][:19]}")
                        ], expand=True),
                        ft.IconButton(
                            icon=ft.Icons.OPEN_IN_NEW,
                            tooltip="Open log file",
                            on_click=lambda e, path=log_file["path"]: self._show_log_content(path)
                        )
                    ]),
                    padding=ft.padding.all(10),
                    bgcolor=ft.Colors.GREY_100,
                    border_radius=5,
                    margin=ft.margin.only(bottom=5)
                )
            )
        
        logs_content = ft.ListView(controls=log_controls, height=300)
        
        logs_dialog = ft.AlertDialog(
            title=ft.Text("Log Files"),
            content=ft.Container(content=logs_content, width=400, height=350),
            actions=[
                ft.TextButton("Clear Old Logs", on_click=self._clear_old_logs),
                ft.TextButton("Close", on_click=lambda e: self._close_dialog(logs_dialog))
            ],
            modal=True
        )
        
        self.page.dialog = logs_dialog
        logs_dialog.open = True
        self.page.update()
    
    def _show_log_content(self, log_path: str):
        """Show log file content"""
        # In a real implementation, this would read and display the log file
        self.page.show_snack_bar(
            ft.SnackBar(content=ft.Text(f"Would open log file: {Path(log_path).name}"))
        )
    
    def _clear_old_logs(self, e):
        """Clear old log files"""
        try:
            deleted_count = self.settings_service.clear_log_files(older_than_days=30)
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Deleted {deleted_count} old log files"))
            )
        except Exception as ex:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text(f"Failed to clear logs: {str(ex)}"))
            )
    
    def _reset_to_defaults(self, e):
        """Reset settings to defaults with confirmation"""
        def confirm_reset(e):
            success = self.settings_service.reset_to_defaults()
            
            if success:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Settings reset to defaults!"))
                )
                # Reload settings
                self._reload_settings()
            else:
                self.page.show_snack_bar(
                    ft.SnackBar(content=ft.Text("Failed to reset settings"))
                )
            
            self._close_dialog(reset_dialog)
        
        reset_dialog = ft.AlertDialog(
            title=ft.Text("Reset to Defaults"),
            content=ft.Text(
                "Are you sure you want to reset all application settings to their default values?\n\n"
                "This action cannot be undone."
            ),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(reset_dialog)),
                ft.ElevatedButton(
                    "Reset",
                    on_click=confirm_reset,
                    style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE)
                )
            ],
            modal=True
        )
        
        self.page.dialog = reset_dialog
        reset_dialog.open = True
        self.page.update()
    
    def _reload_settings(self):
        """Reload settings from service and update UI"""
        self.settings = self.settings_service.get_settings()
        # In a full implementation, this would update all UI controls
        self.has_unsaved_changes = False
        self._update_action_buttons()
    
    def _mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        self.has_unsaved_changes = True
        self._update_action_buttons()
    
    def _update_action_buttons(self):
        """Update action button states"""
        if hasattr(self, 'page'):
            self.page.update()
    
    def _close_settings(self, e):
        """Close the settings page"""
        if self.on_close:
            self.on_close()
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close a dialog"""
        dialog.open = False
        self.page.update()


def main():
    """Test the application settings page"""
    def test_app(page: ft.Page):
        page.title = "Application Settings Test"
        page.window.width = 1000
        page.window.height = 800
        
        def on_close():
            print("Settings closed")
            page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Application Settings closed"))
            )
        
        settings_page = ApplicationSettingsPage(page, on_close=on_close)
        page.add(settings_page.build())
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()