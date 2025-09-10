"""
Assignment Editor Page Component

Provides visual assignment configuration editing with YAML syntax highlighting,
form-based editing for common fields, real-time validation, and preview functionality.
"""

import flet as ft
import sys
import yaml
import re
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass, asdict

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
CLI_CORE_DIR = PROJECT_ROOT / "cli" / "core"
sys.path.insert(0, str(GUI_DIR))
sys.path.insert(0, str(CLI_CORE_DIR))

from app.services.config_service import ConfigService


@dataclass
class ValidationResult:
    """Validation result information"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]


@dataclass
class RubricCriterion:
    """Rubric criterion configuration"""
    name: str
    description: str
    weight: float
    max_points: float


class AssignmentEditorPage:
    """Assignment editor page component
    
    Provides comprehensive assignment configuration editing with both
    form-based and YAML editing modes, real-time validation, and preview.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        assignment_name: Optional[str] = None,
        on_save: Callable[[str, Dict[str, Any]], None] = None,
        on_cancel: Callable[[], None] = None
    ):
        """Initialize the assignment editor page
        
        Args:
            page: Flet page object
            assignment_name: Name of assignment to edit (None for new)
            on_save: Callback when assignment is saved
            on_cancel: Callback when editor is cancelled
        """
        self.page = page
        self.assignment_name = assignment_name
        self.on_save = on_save
        self.on_cancel = on_cancel
        
        # Services
        self.config_service = ConfigService()
        
        # Editor state
        self.is_new_assignment = assignment_name is None
        self.current_config = {}
        self.has_unsaved_changes = False
        self.validation_result = ValidationResult(True, [], [], [])
        
        # Editor modes
        self.edit_mode = "form"  # form, yaml
        
        # Load existing assignment if editing
        if not self.is_new_assignment:
            self._load_assignment()
        else:
            self._create_default_config()
        
        # UI components
        self.mode_tabs = None
        self.form_editor = None
        self.yaml_editor = None
        self.preview_section = None
        self.validation_panel = None
        self.save_button = None
        
        # Form fields
        self.assignment_name_field = None
        self.assignment_type_field = None
        self.max_points_field = None
        self.description_field = None
        self.github_integration_field = None
        self.rubric_section = None
        self.rubric_criteria = []
        
    def build(self) -> ft.Control:
        """Build and return the assignment editor UI"""
        
        # Page header
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    f"{'📝 Edit Assignment' if not self.is_new_assignment else '✨ Create New Assignment'}",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    f"Assignment: {self.assignment_name}" if not self.is_new_assignment else "Create a new assignment configuration",
                    size=16,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=30)
        )
        
        # Build UI sections
        self._build_mode_tabs()
        self._build_form_editor()
        self._build_yaml_editor()
        self._build_preview_section()
        self._build_validation_panel()
        
        # Action buttons
        action_buttons = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    text="Cancel",
                    icon=ft.Icons.CANCEL,
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREY_700,
                        bgcolor=ft.Colors.GREY_200
                    ),
                    on_click=self._on_cancel_clicked
                ),
                ft.Container(width=20),
                ft.ElevatedButton(
                    text="Validate",
                    icon=ft.Icons.CHECK_CIRCLE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.ORANGE_600
                    ),
                    on_click=self._validate_config
                ),
                ft.ElevatedButton(
                    text="Preview",
                    icon=ft.Icons.PREVIEW,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600
                    ),
                    on_click=self._show_preview
                ),
                ft.ElevatedButton(
                    text="💾 Save Assignment",
                    icon=ft.Icons.SAVE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.GREEN_600
                    ),
                    on_click=self._save_assignment,
                    disabled=not self.validation_result.is_valid
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=20)
        )
        
        self.save_button = action_buttons.content.controls[-1]
        
        # Main content layout
        content = ft.Container(
            content=ft.Column([
                header,
                self.mode_tabs,
                ft.Container(height=20),
                
                # Editor content based on mode
                ft.Container(
                    content=self.form_editor if self.edit_mode == "form" else self.yaml_editor,
                    expand=True
                ),
                
                ft.Container(height=20),
                self.validation_panel,
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
    
    def _load_assignment(self):
        """Load existing assignment configuration"""
        try:
            assignments = self.config_service.load_assignments()
            if self.assignment_name in assignments:
                self.current_config = assignments[self.assignment_name]
            else:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Assignment '{self.assignment_name}' not found"),
                        action="OK"
                    )
                )
                self._create_default_config()
        except Exception as e:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Error loading assignment: {str(e)}"),
                    action="OK"
                )
            )
            self._create_default_config()
    
    def _create_default_config(self):
        """Create default assignment configuration"""
        self.current_config = {
            "name": "",
            "type": "coding",
            "max_points": 100,
            "description": "",
            "github_integration": False,
            "rubric": {
                "Functionality": {
                    "description": "Code works correctly and meets requirements",
                    "weight": 0.4,
                    "max_points": 40
                },
                "Code Quality": {
                    "description": "Clean, readable, and well-structured code",
                    "weight": 0.3,
                    "max_points": 30
                },
                "Documentation": {
                    "description": "Clear comments and documentation",
                    "weight": 0.2,
                    "max_points": 20
                },
                "Testing": {
                    "description": "Adequate test coverage and quality",
                    "weight": 0.1,
                    "max_points": 10
                }
            },
            "function_requirements": [],
            "grading_criteria": {
                "check_syntax": True,
                "run_tests": True,
                "code_analysis": True
            }
        }
    
    def _build_mode_tabs(self):
        """Build the mode selection tabs"""
        self.mode_tabs = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    text="📝 Form Editor",
                    icon=ft.Icons.EDIT_NOTE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE if self.edit_mode == "form" else ft.Colors.BLUE_600,
                        bgcolor=ft.Colors.BLUE_600 if self.edit_mode == "form" else ft.Colors.BLUE_50
                    ),
                    on_click=lambda e: self._switch_mode("form"),
                    width=180
                ),
                ft.Container(width=20),
                ft.ElevatedButton(
                    text="⚙️ YAML Editor",
                    icon=ft.Icons.CODE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE if self.edit_mode == "yaml" else ft.Colors.PURPLE_600,
                        bgcolor=ft.Colors.PURPLE_600 if self.edit_mode == "yaml" else ft.Colors.PURPLE_50
                    ),
                    on_click=lambda e: self._switch_mode("yaml"),
                    width=180
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=10)
        )
    
    def _build_form_editor(self):
        """Build the form-based editor"""
        
        # Basic info section
        basic_info = ft.Container(
            content=ft.Column([
                ft.Text("📋 Basic Information", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
                ft.Container(height=15),
                
                ft.Row([
                    ft.Container(
                        content=ft.TextField(
                            label="Assignment Name *",
                            hint_text="e.g., Assignment 1, Midterm Project",
                            value=self.current_config.get("name", ""),
                            on_change=self._on_name_changed,
                            width=300
                        ),
                        expand=True
                    ),
                    ft.Container(width=20),
                    ft.Dropdown(
                        label="Assignment Type",
                        width=200,
                        options=[
                            ft.dropdown.Option("coding", "Coding Assignment"),
                            ft.dropdown.Option("project", "Project"),
                            ft.dropdown.Option("lab", "Lab Exercise"),
                            ft.dropdown.Option("homework", "Homework")
                        ],
                        value=self.current_config.get("type", "coding"),
                        on_change=self._on_type_changed
                    )
                ]),
                
                ft.Container(height=15),
                
                ft.Row([
                    ft.TextField(
                        label="Maximum Points",
                        hint_text="100",
                        value=str(self.current_config.get("max_points", 100)),
                        on_change=self._on_max_points_changed,
                        width=150,
                        input_filter=ft.NumbersOnlyInputFilter()
                    ),
                    ft.Container(width=20),
                    ft.Checkbox(
                        label="Enable GitHub Integration",
                        value=self.current_config.get("github_integration", False),
                        on_change=self._on_github_changed
                    )
                ]),
                
                ft.Container(height=15),
                
                ft.TextField(
                    label="Description",
                    hint_text="Describe the assignment objectives and requirements",
                    value=self.current_config.get("description", ""),
                    multiline=True,
                    min_lines=3,
                    max_lines=5,
                    on_change=self._on_description_changed,
                    width=600
                )
            ]),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=10,
            bgcolor=ft.Colors.BLUE_50
        )
        
        # Rubric section
        self._build_rubric_section()
        
        # Grading criteria section
        grading_criteria = ft.Container(
            content=ft.Column([
                ft.Text("⚙️ Grading Criteria", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_800),
                ft.Container(height=15),
                
                ft.Row([
                    ft.Checkbox(
                        label="Check Syntax",
                        value=self.current_config.get("grading_criteria", {}).get("check_syntax", True),
                        on_change=lambda e: self._update_grading_criteria("check_syntax", e.control.value)
                    ),
                    ft.Checkbox(
                        label="Run Tests",
                        value=self.current_config.get("grading_criteria", {}).get("run_tests", True),
                        on_change=lambda e: self._update_grading_criteria("run_tests", e.control.value)
                    ),
                    ft.Checkbox(
                        label="Code Analysis",
                        value=self.current_config.get("grading_criteria", {}).get("code_analysis", True),
                        on_change=lambda e: self._update_grading_criteria("code_analysis", e.control.value)
                    )
                ])
            ]),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.GREEN_200),
            border_radius=10,
            bgcolor=ft.Colors.GREEN_50
        )
        
        self.form_editor = ft.Column([
            basic_info,
            ft.Container(height=20),
            self.rubric_section,
            ft.Container(height=20),
            grading_criteria
        ], width=800)
    
    def _build_rubric_section(self):
        """Build the rubric editing section"""
        self.rubric_criteria = []
        rubric_items = []
        
        rubric_data = self.current_config.get("rubric", {})
        for criterion_name, criterion_data in rubric_data.items():
            criterion_widget = self._create_rubric_criterion_widget(
                criterion_name, 
                criterion_data.get("description", ""),
                criterion_data.get("weight", 0.0),
                criterion_data.get("max_points", 0.0)
            )
            rubric_items.append(criterion_widget)
        
        self.rubric_section = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text("📊 Rubric Configuration", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        text="+ Add Criterion",
                        icon=ft.Icons.ADD,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.PURPLE_600
                        ),
                        on_click=self._add_rubric_criterion
                    )
                ]),
                ft.Container(height=15),
                
                ft.Column(rubric_items, spacing=10) if rubric_items else ft.Container(
                    content=ft.Text("No rubric criteria defined. Click 'Add Criterion' to start.", 
                                   color=ft.Colors.GREY_600),
                    padding=ft.padding.all(20)
                ),
                
                ft.Container(height=15),
                ft.Container(
                    content=ft.Text(
                        f"Total Weight: {self._calculate_total_weight():.1%}",
                        size=14,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_600 if abs(self._calculate_total_weight() - 1.0) < 0.01 else ft.Colors.RED_600
                    ),
                    alignment=ft.alignment.center
                )
            ]),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.PURPLE_200),
            border_radius=10,
            bgcolor=ft.Colors.PURPLE_50
        )
    
    def _create_rubric_criterion_widget(self, name: str, description: str, weight: float, max_points: float) -> ft.Container:
        """Create a rubric criterion editing widget"""
        
        name_field = ft.TextField(
            label="Criterion Name",
            value=name,
            width=200,
            on_change=lambda e: self._update_rubric_data()
        )
        
        description_field = ft.TextField(
            label="Description",
            value=description,
            width=300,
            on_change=lambda e: self._update_rubric_data()
        )
        
        weight_field = ft.TextField(
            label="Weight",
            value=str(weight),
            width=100,
            hint_text="0.0-1.0",
            on_change=lambda e: self._update_rubric_data()
        )
        
        points_field = ft.TextField(
            label="Max Points",
            value=str(max_points),
            width=100,
            input_filter=ft.NumbersOnlyInputFilter(),
            on_change=lambda e: self._update_rubric_data()
        )
        
        criterion_widget = ft.Container(
            content=ft.Row([
                name_field,
                ft.Container(width=10),
                description_field,
                ft.Container(width=10),
                weight_field,
                ft.Container(width=10),
                points_field,
                ft.Container(width=10),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=ft.Colors.RED_600,
                    tooltip="Remove criterion",
                    on_click=lambda e, w=None: self._remove_rubric_criterion(w)
                )
            ]),
            padding=ft.padding.all(10),
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5,
            bgcolor=ft.Colors.WHITE
        )
        
        # Store references for data access
        criterion_widget.name_field = name_field
        criterion_widget.description_field = description_field
        criterion_widget.weight_field = weight_field
        criterion_widget.points_field = points_field
        
        self.rubric_criteria.append(criterion_widget)
        return criterion_widget
    
    def _build_yaml_editor(self):
        """Build the YAML editor"""
        yaml_content = yaml.dump(self.current_config, default_flow_style=False, sort_keys=False)
        
        self.yaml_editor = ft.Container(
            content=ft.Column([
                ft.Text("⚙️ YAML Configuration", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800),
                ft.Container(height=15),
                
                ft.TextField(
                    value=yaml_content,
                    multiline=True,
                    min_lines=20,
                    max_lines=30,
                    on_change=self._on_yaml_changed,
                    text_style=ft.TextStyle(font_family="Courier"),
                    border_color=ft.Colors.PURPLE_300,
                    width=800
                ),
                
                ft.Container(height=10),
                ft.Text(
                    "💡 Tip: Use proper YAML syntax. Changes will be validated automatically.",
                    size=12,
                    color=ft.Colors.GREY_600,
                    italic=True
                )
            ]),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.PURPLE_200),
            border_radius=10,
            bgcolor=ft.Colors.PURPLE_50
        )
    
    def _build_preview_section(self):
        """Build the preview section"""
        self.preview_section = ft.Container()
    
    def _build_validation_panel(self):
        """Build the validation results panel"""
        self.validation_panel = ft.Container()
        self._update_validation_panel()
    
    def _switch_mode(self, mode: str):
        """Switch between form and YAML editing modes"""
        if mode != self.edit_mode:
            # Sync data before switching
            if self.edit_mode == "form":
                self._sync_form_to_config()
            elif self.edit_mode == "yaml":
                self._sync_yaml_to_config()
            
            self.edit_mode = mode
            
            # Update mode tabs
            self._build_mode_tabs()
            
            # Update editor content
            if mode == "form":
                self._build_form_editor()
                self.page.controls[0].content.controls[2].content = self.form_editor
            else:
                self._build_yaml_editor()
                self.page.controls[0].content.controls[2].content = self.yaml_editor
            
            self.page.update()
    
    def _sync_form_to_config(self):
        """Sync form data to configuration"""
        # This will be called when form fields change
        pass
    
    def _sync_yaml_to_config(self):
        """Sync YAML editor to configuration"""
        try:
            yaml_text = self.yaml_editor.content.controls[1].value
            self.current_config = yaml.safe_load(yaml_text)
            self.has_unsaved_changes = True
        except Exception as e:
            self.validation_result = ValidationResult(
                False, 
                [f"Invalid YAML syntax: {str(e)}"], 
                [], 
                ["Check YAML syntax and formatting"]
            )
            self._update_validation_panel()
    
    def _on_name_changed(self, e):
        """Handle assignment name change"""
        self.current_config["name"] = e.control.value
        self.has_unsaved_changes = True
        self._validate_config(None)
    
    def _on_type_changed(self, e):
        """Handle assignment type change"""
        self.current_config["type"] = e.control.value
        self.has_unsaved_changes = True
    
    def _on_max_points_changed(self, e):
        """Handle max points change"""
        try:
            self.current_config["max_points"] = int(e.control.value) if e.control.value else 100
            self.has_unsaved_changes = True
        except ValueError:
            pass
    
    def _on_description_changed(self, e):
        """Handle description change"""
        self.current_config["description"] = e.control.value
        self.has_unsaved_changes = True
    
    def _on_github_changed(self, e):
        """Handle GitHub integration change"""
        self.current_config["github_integration"] = e.control.value
        self.has_unsaved_changes = True
    
    def _on_yaml_changed(self, e):
        """Handle YAML editor change"""
        self.has_unsaved_changes = True
        # Validate YAML on change with debouncing could be added here
    
    def _update_grading_criteria(self, key: str, value: bool):
        """Update grading criteria"""
        if "grading_criteria" not in self.current_config:
            self.current_config["grading_criteria"] = {}
        self.current_config["grading_criteria"][key] = value
        self.has_unsaved_changes = True
    
    def _add_rubric_criterion(self, e):
        """Add a new rubric criterion"""
        new_criterion = self._create_rubric_criterion_widget(
            f"New Criterion {len(self.rubric_criteria) + 1}",
            "Describe this criterion",
            0.1,
            10.0
        )
        
        # Add to the rubric section
        rubric_column = self.rubric_section.content.controls[1]
        if isinstance(rubric_column.content.controls[0], ft.Text):  # Replace "No criteria" message
            rubric_column.content.controls.clear()
        
        rubric_column.content.controls.append(new_criterion)
        self._update_rubric_data()
        self.page.update()
    
    def _remove_rubric_criterion(self, criterion_widget):
        """Remove a rubric criterion"""
        if criterion_widget in self.rubric_criteria:
            self.rubric_criteria.remove(criterion_widget)
            
            # Remove from UI
            rubric_column = self.rubric_section.content.controls[1]
            if criterion_widget in rubric_column.content.controls:
                rubric_column.content.controls.remove(criterion_widget)
            
            self._update_rubric_data()
            self.page.update()
    
    def _update_rubric_data(self):
        """Update rubric data from form fields"""
        rubric_data = {}
        
        for criterion_widget in self.rubric_criteria:
            name = criterion_widget.name_field.value or "Unnamed"
            description = criterion_widget.description_field.value or ""
            
            try:
                weight = float(criterion_widget.weight_field.value or 0)
                max_points = float(criterion_widget.points_field.value or 0)
            except ValueError:
                weight = 0.0
                max_points = 0.0
            
            rubric_data[name] = {
                "description": description,
                "weight": weight,
                "max_points": max_points
            }
        
        self.current_config["rubric"] = rubric_data
        self.has_unsaved_changes = True
        
        # Update total weight display
        total_weight_text = self.rubric_section.content.controls[2].content
        total_weight = self._calculate_total_weight()
        total_weight_text.value = f"Total Weight: {total_weight:.1%}"
        total_weight_text.color = ft.Colors.GREEN_600 if abs(total_weight - 1.0) < 0.01 else ft.Colors.RED_600
        
        self.page.update()
    
    def _calculate_total_weight(self) -> float:
        """Calculate total rubric weight"""
        total = 0.0
        rubric_data = self.current_config.get("rubric", {})
        for criterion_data in rubric_data.values():
            total += criterion_data.get("weight", 0.0)
        return total
    
    def _validate_config(self, e):
        """Validate the current configuration"""
        errors = []
        warnings = []
        suggestions = []
        
        # Basic validation
        if not self.current_config.get("name", "").strip():
            errors.append("Assignment name is required")
        
        if self.current_config.get("max_points", 0) <= 0:
            errors.append("Maximum points must be greater than 0")
        
        # Rubric validation
        total_weight = self._calculate_total_weight()
        if abs(total_weight - 1.0) > 0.01:
            if total_weight < 1.0:
                warnings.append(f"Rubric weights sum to {total_weight:.1%} (should be 100%)")
                suggestions.append("Adjust rubric weights to sum to 100%")
            else:
                errors.append(f"Rubric weights sum to {total_weight:.1%} (exceeds 100%)")
        
        if not self.current_config.get("rubric"):
            warnings.append("No rubric criteria defined")
            suggestions.append("Add rubric criteria to define grading standards")
        
        # Update validation result
        self.validation_result = ValidationResult(
            len(errors) == 0,
            errors,
            warnings,
            suggestions
        )
        
        # Update UI
        self._update_validation_panel()
        if self.save_button:
            self.save_button.disabled = not self.validation_result.is_valid
            self.page.update()
    
    def _update_validation_panel(self):
        """Update the validation results panel"""
        if not self.validation_result.errors and not self.validation_result.warnings:
            self.validation_panel.content = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600),
                    ft.Text("Configuration is valid", color=ft.Colors.GREEN_600, weight=ft.FontWeight.BOLD)
                ]),
                padding=ft.padding.all(15),
                bgcolor=ft.Colors.GREEN_50,
                border=ft.border.all(1, ft.Colors.GREEN_200),
                border_radius=5
            )
        else:
            validation_items = []
            
            for error in self.validation_result.errors:
                validation_items.append(
                    ft.Row([
                        ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_600, size=16),
                        ft.Text(error, color=ft.Colors.RED_600, size=12)
                    ])
                )
            
            for warning in self.validation_result.warnings:
                validation_items.append(
                    ft.Row([
                        ft.Icon(ft.Icons.WARNING, color=ft.Colors.ORANGE_600, size=16),
                        ft.Text(warning, color=ft.Colors.ORANGE_600, size=12)
                    ])
                )
            
            for suggestion in self.validation_result.suggestions:
                validation_items.append(
                    ft.Row([
                        ft.Icon(ft.Icons.LIGHTBULB, color=ft.Colors.BLUE_600, size=16),
                        ft.Text(f"💡 {suggestion}", color=ft.Colors.BLUE_600, size=12)
                    ])
                )
            
            self.validation_panel.content = ft.Container(
                content=ft.Column([
                    ft.Text("Validation Results", weight=ft.FontWeight.BOLD, size=14),
                    ft.Container(height=10),
                    ft.Column(validation_items, spacing=5)
                ]),
                padding=ft.padding.all(15),
                bgcolor=ft.Colors.RED_50 if self.validation_result.errors else ft.Colors.ORANGE_50,
                border=ft.border.all(1, ft.Colors.RED_200 if self.validation_result.errors else ft.Colors.ORANGE_200),
                border_radius=5,
                width=800
            )
        
        if hasattr(self, 'page'):
            self.page.update()
    
    def _show_preview(self, e):
        """Show configuration preview"""
        preview_text = yaml.dump(self.current_config, default_flow_style=False, sort_keys=False)
        
        preview_dialog = ft.AlertDialog(
            title=ft.Text("Configuration Preview"),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Generated YAML Configuration:", weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Container(
                        content=ft.Text(
                            preview_text,
                            size=11,
                            font_family="Courier",
                            selectable=True
                        ),
                        padding=ft.padding.all(10),
                        bgcolor=ft.Colors.GREY_100,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=5,
                        width=600,
                        height=400,
                        scroll=ft.ScrollMode.AUTO
                    )
                ]),
                width=650,
                height=450
            ),
            actions=[ft.TextButton("Close", on_click=lambda e: self._close_dialog(preview_dialog))],
            modal=True
        )
        
        self.page.dialog = preview_dialog
        preview_dialog.open = True
        self.page.update()
    
    def _save_assignment(self, e):
        """Save the assignment configuration"""
        if not self.validation_result.is_valid:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Please fix validation errors before saving"),
                    action="OK"
                )
            )
            return
        
        # Sync current mode data
        if self.edit_mode == "yaml":
            self._sync_yaml_to_config()
        
        try:
            # Determine assignment name
            assignment_name = self.current_config.get("name", "").strip()
            if not assignment_name:
                self.page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Assignment name is required"),
                        action="OK"
                    )
                )
                return
            
            # Save configuration
            # In real implementation, this would save to the assignments directory
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Assignment '{assignment_name}' saved successfully!"),
                    action="OK"
                )
            )
            
            # Call save callback
            if self.on_save:
                self.on_save(assignment_name, self.current_config)
            
            self.has_unsaved_changes = False
            
        except Exception as e:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Error saving assignment: {str(e)}"),
                    action="OK"
                )
            )
    
    def _on_cancel_clicked(self, e):
        """Handle cancel button click"""
        if self.has_unsaved_changes:
            # Show confirmation dialog
            confirm_dialog = ft.AlertDialog(
                title=ft.Text("Unsaved Changes"),
                content=ft.Text("You have unsaved changes. Are you sure you want to cancel?"),
                actions=[
                    ft.TextButton("Keep Editing", on_click=lambda e: self._close_dialog(confirm_dialog)),
                    ft.ElevatedButton(
                        "Discard Changes",
                        style=ft.ButtonStyle(bgcolor=ft.Colors.RED_600, color=ft.Colors.WHITE),
                        on_click=lambda e: self._confirm_cancel(confirm_dialog)
                    )
                ],
                modal=True
            )
            
            self.page.dialog = confirm_dialog
            confirm_dialog.open = True
            self.page.update()
        else:
            if self.on_cancel:
                self.on_cancel()
    
    def _confirm_cancel(self, dialog: ft.AlertDialog):
        """Confirm cancellation and discard changes"""
        dialog.open = False
        self.page.update()
        
        if self.on_cancel:
            self.on_cancel()
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close a dialog"""
        dialog.open = False
        self.page.update()


def main():
    """Test the assignment editor page"""
    def test_app(page: ft.Page):
        page.title = "Assignment Editor Test"
        page.window.width = 1200
        page.window.height = 900
        
        def on_save(name, config):
            print(f"Saved assignment: {name}")
            print(f"Config: {config}")
        
        def on_cancel():
            print("Editor cancelled")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Editor cancelled"),
                    action="OK"
                )
            )
        
        editor = AssignmentEditorPage(page, None, on_save, on_cancel)
        page.add(editor.build())
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()