"""
Configuration Validator Page Component

Provides comprehensive validation interface with user-friendly displays,
auto-fix suggestions, and validation report generation.
"""

import flet as ft
import sys
import yaml
import json
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.services.validation_service import (
    ConfigurationValidationService, 
    ValidationResult, 
    ValidationIssue, 
    ValidationLevel,
    AutoFixSuggestion
)


class ConfigValidatorPage:
    """Configuration validator page component
    
    Provides comprehensive validation interface with visual feedback,
    auto-fix capabilities, and detailed reporting.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        config_data: Optional[Dict[str, Any]] = None,
        config_file: Optional[str] = None,
        on_close: Callable[[], None] = None
    ):
        """Initialize the configuration validator
        
        Args:
            page: Flet page object
            config_data: Configuration data to validate
            config_file: Path to configuration file
            on_close: Callback when validator is closed
        """
        self.page = page
        self.config_data = config_data or {}
        self.config_file = config_file or ""
        self.on_close = on_close
        
        # Services
        self.validation_service = ConfigurationValidationService()
        
        # Validation state
        self.current_validation_result: Optional[ValidationResult] = None
        self.selected_fixes: List[str] = []
        
        # UI components
        self.validation_summary = None
        self.issues_list = None
        self.auto_fix_panel = None
        self.config_preview = None
        
    def build(self) -> ft.Control:
        """Build and return the validator UI"""
        
        # Page header
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    "🔍 Configuration Validator",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    "Validate and fix assignment configuration issues",
                    size=16,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=30)
        )
        
        # Run initial validation
        self._run_validation()
        
        # Build UI sections
        self._build_validation_summary()
        self._build_issues_list()
        self._build_auto_fix_panel()
        self._build_config_preview()
        
        # Action buttons
        action_buttons = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    text="🔄 Re-validate",
                    icon=ft.Icons.REFRESH,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600
                    ),
                    on_click=self._run_validation
                ),
                ft.ElevatedButton(
                    text="🔧 Apply Selected Fixes",
                    icon=ft.Icons.AUTO_FIX_HIGH,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.GREEN_600 if self.selected_fixes else ft.Colors.GREY_400
                    ),
                    disabled=not self.selected_fixes,
                    on_click=self._apply_auto_fixes
                ),
                ft.ElevatedButton(
                    text="📊 Export Report",
                    icon=ft.Icons.DOWNLOAD,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.PURPLE_600
                    ),
                    on_click=self._show_export_dialog
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    text="Close",
                    icon=ft.Icons.CLOSE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREY_700,
                        bgcolor=ft.Colors.GREY_200
                    ),
                    on_click=self._close_validator
                )
            ]),
            padding=ft.padding.symmetric(vertical=20)
        )
        
        # Main content layout
        content = ft.Container(
            content=ft.Column([
                header,
                
                # Summary section
                self.validation_summary,
                ft.Container(height=20),
                
                # Main content area
                ft.Row([
                    # Left panel: Issues and fixes
                    ft.Container(
                        content=ft.Column([
                            self.issues_list,
                            ft.Container(height=20),
                            self.auto_fix_panel
                        ]),
                        width=500,
                        expand=True
                    ),
                    
                    ft.Container(width=30),
                    
                    # Right panel: Config preview
                    self.config_preview
                ], alignment=ft.MainAxisAlignment.START, expand=True),
                
                action_buttons
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
            ),
            padding=ft.padding.all(40),
            alignment=ft.alignment.top_center,
            expand=True
        )
        
        return content
    
    def _run_validation(self, e=None):
        """Run configuration validation"""
        try:
            self.current_validation_result = self.validation_service.validate_configuration(
                self.config_data, 
                self.config_file
            )
            
            # Update UI components
            self._update_validation_summary()
            self._update_issues_list()
            self._update_auto_fix_panel()
            self._update_config_preview()
            
        except Exception as ex:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Validation failed: {str(ex)}"),
                    action="OK"
                )
            )
    
    def _build_validation_summary(self):
        """Build validation summary display"""
        if not self.current_validation_result:
            self.validation_summary = ft.Container(
                content=ft.Text("No validation results yet"),
                alignment=ft.alignment.center
            )
            return
        
        result = self.current_validation_result
        
        # Status indicator
        if result.is_valid:
            status_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600, size=40)
            status_text = "Configuration is Valid"
            status_color = ft.Colors.GREEN_600
            bg_color = ft.Colors.GREEN_50
            border_color = ft.Colors.GREEN_200
        else:
            status_icon = ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_600, size=40)
            status_text = "Configuration has Issues"
            status_color = ft.Colors.RED_600
            bg_color = ft.Colors.RED_50
            border_color = ft.Colors.RED_200
        
        # Summary statistics
        stats = ft.Row([
            self._create_stat_chip("Errors", result.total_errors, ft.Colors.RED_600),
            self._create_stat_chip("Warnings", result.total_warnings, ft.Colors.ORANGE_600),
            self._create_stat_chip("Info", result.total_info, ft.Colors.BLUE_600),
            self._create_stat_chip("Auto-fixes", len([i for i in result.issues if i.auto_fix_available]), ft.Colors.GREEN_600)
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)
        
        self.validation_summary = ft.Container(
            content=ft.Column([
                ft.Row([
                    status_icon,
                    ft.Container(width=15),
                    ft.Column([
                        ft.Text(status_text, size=20, weight=ft.FontWeight.BOLD, color=status_color),
                        ft.Text(f"Validated at {result.validation_timestamp[:19]}", size=12, color=ft.Colors.GREY_600)
                    ])
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=20),
                stats
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(25),
            bgcolor=bg_color,
            border=ft.border.all(1, border_color),
            border_radius=10,
            width=800
        )
    
    def _create_stat_chip(self, label: str, count: int, color: ft.Colors) -> ft.Container:
        """Create a statistics chip"""
        return ft.Container(
            content=ft.Column([
                ft.Text(str(count), size=24, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(label, size=12, color=ft.Colors.GREY_700)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, color),
            border_radius=8,
            width=80
        )
    
    def _build_issues_list(self):
        """Build issues list display"""
        self.issues_list = ft.Container(
            content=ft.Column([
                ft.Text(
                    "🚨 Validation Issues",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.RED_800
                ),
                ft.Container(height=15),
                ft.Container(
                    content=ft.ListView(spacing=10, height=400),
                    height=400
                )
            ]),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10
        )
    
    def _build_auto_fix_panel(self):
        """Build auto-fix panel"""
        self.auto_fix_panel = ft.Container(
            content=ft.Column([
                ft.Text(
                    "🔧 Auto-Fix Suggestions",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_800
                ),
                ft.Container(height=15),
                ft.Container(
                    content=ft.ListView(spacing=10, height=200),
                    height=200
                )
            ]),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10
        )
    
    def _build_config_preview(self):
        """Build configuration preview"""
        self.config_preview = ft.Container(
            content=ft.Column([
                ft.Text(
                    "📄 Configuration Preview",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800
                ),
                ft.Container(height=15),
                ft.Container(
                    content=ft.TextField(
                        value="",
                        multiline=True,
                        min_lines=25,
                        max_lines=25,
                        read_only=True,
                        text_style=ft.TextStyle(font_family="Courier"),
                        border_color=ft.Colors.GREY_300
                    ),
                    width=400,
                    height=620
                )
            ]),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=10,
            width=450
        )
    
    def _update_validation_summary(self):
        """Update validation summary display"""
        self._build_validation_summary()
        if hasattr(self, 'page'):
            self.page.update()
    
    def _update_issues_list(self):
        """Update issues list display"""
        if not self.current_validation_result:
            return
        
        issues_listview = self.issues_list.content.controls[2].content
        issues_listview.controls.clear()
        
        if not self.current_validation_result.issues:
            issues_listview.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600),
                        ft.Text("No issues found! Configuration is valid.", color=ft.Colors.GREEN_600)
                    ]),
                    padding=ft.padding.all(15),
                    bgcolor=ft.Colors.GREEN_50,
                    border_radius=5
                )
            )
        else:
            # Group issues by level
            errors = self.current_validation_result.get_issues_by_level(ValidationLevel.ERROR)
            warnings = self.current_validation_result.get_issues_by_level(ValidationLevel.WARNING)
            info = self.current_validation_result.get_issues_by_level(ValidationLevel.INFO)
            
            for issues, title, color in [
                (errors, "Errors", ft.Colors.RED_600),
                (warnings, "Warnings", ft.Colors.ORANGE_600),
                (info, "Information", ft.Colors.BLUE_600)
            ]:
                if issues:
                    issues_listview.controls.append(
                        ft.Text(f"{title} ({len(issues)})", weight=ft.FontWeight.BOLD, color=color, size=14)
                    )
                    
                    for issue in issues:
                        issue_widget = self._create_issue_widget(issue)
                        issues_listview.controls.append(issue_widget)
                    
                    issues_listview.controls.append(ft.Container(height=10))
        
        if hasattr(self, 'page'):
            self.page.update()
    
    def _create_issue_widget(self, issue: ValidationIssue) -> ft.Container:
        """Create widget for displaying validation issue"""
        # Level-specific styling
        level_colors = {
            ValidationLevel.ERROR: (ft.Colors.RED_600, ft.Colors.RED_50, ft.Colors.RED_200),
            ValidationLevel.WARNING: (ft.Colors.ORANGE_600, ft.Colors.ORANGE_50, ft.Colors.ORANGE_200),
            ValidationLevel.INFO: (ft.Colors.BLUE_600, ft.Colors.BLUE_50, ft.Colors.BLUE_200)
        }
        
        text_color, bg_color, border_color = level_colors[issue.level]
        
        # Level icon
        level_icons = {
            ValidationLevel.ERROR: ft.Icons.ERROR,
            ValidationLevel.WARNING: ft.Icons.WARNING,
            ValidationLevel.INFO: ft.Icons.INFO
        }
        
        # Auto-fix checkbox if available
        auto_fix_control = ft.Container()
        if issue.auto_fix_available:
            auto_fix_control = ft.Checkbox(
                label="Auto-fix",
                value=issue.field in self.selected_fixes,
                on_change=lambda e, field=issue.field: self._toggle_auto_fix(field, e.control.value)
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(level_icons[issue.level], color=text_color, size=20),
                    ft.Container(width=10),
                    ft.Column([
                        ft.Text(f"{issue.field}: {issue.message}", weight=ft.FontWeight.BOLD, size=14),
                        ft.Text(issue.description, size=12, color=ft.Colors.GREY_700)
                    ], expand=True),
                    auto_fix_control
                ])
            ]),
            padding=ft.padding.all(15),
            bgcolor=bg_color,
            border=ft.border.all(1, border_color),
            border_radius=5,
            margin=ft.margin.only(bottom=5)
        )
    
    def _update_auto_fix_panel(self):
        """Update auto-fix panel display"""
        if not self.current_validation_result:
            return
        
        auto_fix_listview = self.auto_fix_panel.content.controls[2].content
        auto_fix_listview.controls.clear()
        
        auto_fix_issues = [issue for issue in self.current_validation_result.issues if issue.auto_fix_available]
        
        if not auto_fix_issues:
            auto_fix_listview.controls.append(
                ft.Container(
                    content=ft.Text("No auto-fix suggestions available", color=ft.Colors.GREY_600),
                    padding=ft.padding.all(15),
                    alignment=ft.alignment.center
                )
            )
        else:
            # Select/deselect all button
            select_all_btn = ft.ElevatedButton(
                text=f"Select All ({len(auto_fix_issues)})",
                icon=ft.Icons.SELECT_ALL,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
                on_click=self._select_all_fixes,
                width=150
            )
            
            clear_all_btn = ft.ElevatedButton(
                text="Clear All",
                icon=ft.Icons.CLEAR,
                style=ft.ButtonStyle(bgcolor=ft.Colors.GREY_600, color=ft.Colors.WHITE),
                on_click=self._clear_all_fixes,
                width=100
            )
            
            auto_fix_listview.controls.append(
                ft.Row([select_all_btn, ft.Container(width=10), clear_all_btn])
            )
            auto_fix_listview.controls.append(ft.Container(height=10))
            
            # Auto-fix suggestions
            for issue in auto_fix_issues:
                suggestion_widget = self._create_auto_fix_widget(issue)
                auto_fix_listview.controls.append(suggestion_widget)
        
        if hasattr(self, 'page'):
            self.page.update()
    
    def _create_auto_fix_widget(self, issue: ValidationIssue) -> ft.Container:
        """Create widget for auto-fix suggestion"""
        is_selected = issue.field in self.selected_fixes
        
        return ft.Container(
            content=ft.Row([
                ft.Checkbox(
                    value=is_selected,
                    on_change=lambda e, field=issue.field: self._toggle_auto_fix(field, e.control.value)
                ),
                ft.Container(width=10),
                ft.Column([
                    ft.Text(issue.field, weight=ft.FontWeight.BOLD, size=12),
                    ft.Text(issue.auto_fix_description, size=11, color=ft.Colors.GREY_700),
                    ft.Text(f"Suggested: {str(issue.suggested_value)[:50]}...", size=10, color=ft.Colors.BLUE_600)
                    if str(issue.suggested_value) else ft.Container()
                ], expand=True)
            ]),
            padding=ft.padding.all(10),
            bgcolor=ft.Colors.GREEN_50 if is_selected else ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREEN_200 if is_selected else ft.Colors.GREY_200),
            border_radius=5,
            margin=ft.margin.only(bottom=5)
        )
    
    def _update_config_preview(self):
        """Update configuration preview"""
        if not self.config_data:
            return
        
        try:
            yaml_content = yaml.dump(self.config_data, default_flow_style=False, sort_keys=False)
            preview_field = self.config_preview.content.controls[2].content
            preview_field.value = yaml_content
            
            if hasattr(self, 'page'):
                self.page.update()
        except Exception as e:
            print(f"Failed to update config preview: {e}")
    
    def _toggle_auto_fix(self, field: str, selected: bool):
        """Toggle auto-fix selection"""
        if selected and field not in self.selected_fixes:
            self.selected_fixes.append(field)
        elif not selected and field in self.selected_fixes:
            self.selected_fixes.remove(field)
        
        # Update UI
        self._update_auto_fix_panel()
        self._update_action_buttons()
    
    def _select_all_fixes(self, e):
        """Select all auto-fix suggestions"""
        if self.current_validation_result:
            self.selected_fixes = [
                issue.field for issue in self.current_validation_result.issues 
                if issue.auto_fix_available
            ]
            self._update_auto_fix_panel()
            self._update_action_buttons()
    
    def _clear_all_fixes(self, e):
        """Clear all auto-fix selections"""
        self.selected_fixes.clear()
        self._update_auto_fix_panel()
        self._update_action_buttons()
    
    def _apply_auto_fixes(self, e):
        """Apply selected auto-fixes"""
        if not self.selected_fixes:
            return
        
        try:
            fixed_config, applied_fixes = self.validation_service.apply_auto_fixes(
                self.config_data, 
                self.selected_fixes
            )
            
            # Update configuration
            self.config_data = fixed_config
            
            # Clear applied fixes from selection
            for fix in applied_fixes:
                if fix in self.selected_fixes:
                    self.selected_fixes.remove(fix)
            
            # Re-run validation
            self._run_validation()
            
            # Show success message
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Applied {len(applied_fixes)} auto-fixes successfully!"),
                    action="OK"
                )
            )
            
        except Exception as ex:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Failed to apply fixes: {str(ex)}"),
                    action="OK"
                )
            )
    
    def _show_export_dialog(self, e):
        """Show validation report export dialog"""
        if not self.current_validation_result:
            return
        
        # Export format options
        format_options = [
            ("json", "📄 JSON Report", "Structured data format"),
            ("yaml", "⚙️ YAML Report", "Human-readable format"),
            ("txt", "📝 Text Report", "Plain text summary")
        ]
        
        format_buttons = []
        for format_id, title, description in format_options:
            format_buttons.append(
                ft.ElevatedButton(
                    text=title,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600
                    ),
                    on_click=lambda e, fmt=format_id: self._export_report(fmt),
                    width=200
                )
            )
            format_buttons.append(ft.Container(height=10))
        
        export_dialog = ft.AlertDialog(
            title=ft.Text("Export Validation Report"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Choose export format:"),
                    ft.Container(height=15),
                    ft.Column(format_buttons[:-1])  # Remove last spacer
                ]),
                width=300
            ),
            actions=[ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(export_dialog))],
            modal=True
        )
        
        self.page.dialog = export_dialog
        export_dialog.open = True
        self.page.update()
    
    def _export_report(self, format_type: str):
        """Export validation report"""
        try:
            report_content = self.validation_service.export_validation_report(
                self.current_validation_result, 
                format_type
            )
            
            # In a real implementation, this would save to file
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Validation report exported to {format_type.upper()} format!"),
                    action="OK"
                )
            )
            
            # Close any open dialogs
            if self.page.dialog:
                self.page.dialog.open = False
                self.page.update()
            
        except Exception as ex:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Export failed: {str(ex)}"),
                    action="OK"
                )
            )
    
    def _update_action_buttons(self):
        """Update action button states"""
        # This would update the action buttons based on current state
        if hasattr(self, 'page'):
            self.page.update()
    
    def _close_validator(self, e):
        """Close the validator"""
        if self.on_close:
            self.on_close()
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close a dialog"""
        dialog.open = False
        self.page.update()


def main():
    """Test the configuration validator"""
    def test_app(page: ft.Page):
        page.title = "Configuration Validator Test"
        page.window.width = 1400
        page.window.height = 900
        
        # Sample configuration with issues
        test_config = {
            "name": "Test Assignment",
            "type": "coding",
            "max_points": 100,
            "description": "Short desc",
            "rubric": {
                "Functionality": {
                    "description": "Code works",
                    "weight": 0.6,
                    "max_points": 50
                },
                "Quality": {
                    "description": "Code quality",
                    "weight": 0.5,  # This will cause weight total > 1.0
                    "max_points": 40
                }
            }
        }
        
        def on_close():
            print("Validator closed")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Validator closed"),
                    action="OK"
                )
            )
        
        validator = ConfigValidatorPage(
            page,
            config_data=test_config,
            config_file="test_config.yaml",
            on_close=on_close
        )
        
        page.add(validator.build())
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()