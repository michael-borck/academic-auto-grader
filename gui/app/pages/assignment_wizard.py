"""
Assignment Creation Wizard Component

Provides a step-by-step guided workflow for creating new assignments with
form-based input, rubric builder, and function requirement specification.
"""

import flet as ft
import sys
import yaml
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
CLI_CORE_DIR = PROJECT_ROOT / "cli" / "core"
sys.path.insert(0, str(GUI_DIR))
sys.path.insert(0, str(CLI_CORE_DIR))


class WizardStep(Enum):
    """Wizard step enumeration"""
    WELCOME = 1
    BASIC_INFO = 2
    ASSIGNMENT_TYPE = 3
    RUBRIC_BUILDER = 4
    FUNCTION_REQUIREMENTS = 5
    GRADING_OPTIONS = 6
    REVIEW_CONFIRM = 7


@dataclass
class WizardState:
    """Wizard state container"""
    current_step: WizardStep = WizardStep.WELCOME
    assignment_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.assignment_config is None:
            self.assignment_config = {}


class AssignmentWizardPage:
    """Assignment creation wizard component
    
    Provides a step-by-step guided workflow for creating new assignments
    with validation at each step and a user-friendly interface.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        on_complete: Callable[[str, Dict[str, Any]], None] = None,
        on_cancel: Callable[[], None] = None
    ):
        """Initialize the assignment wizard
        
        Args:
            page: Flet page object
            on_complete: Callback when wizard is completed
            on_cancel: Callback when wizard is cancelled
        """
        self.page = page
        self.on_complete = on_complete
        self.on_cancel = on_cancel
        
        # Wizard state
        self.state = WizardState()
        self.state.assignment_config = self._create_default_config()
        
        # UI components
        self.progress_indicator = None
        self.step_content = None
        self.navigation_buttons = None
        
        # Step-specific components
        self.step_components = {}
        
        # Validation state
        self.current_step_valid = True
        
    def build(self) -> ft.Control:
        """Build and return the wizard UI"""
        
        # Build wizard components
        self._build_progress_indicator()
        self._build_navigation_buttons()
        
        # Initial step content
        self._build_current_step()
        
        # Main wizard layout
        content = ft.Container(
            content=ft.Column([
                # Wizard header
                ft.Container(
                    content=ft.Column([
                        ft.Text(
                            "🧙‍♂️ Assignment Creation Wizard",
                            size=32,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.BLUE_800,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Text(
                            "Let's create your assignment step by step",
                            size=16,
                            color=ft.Colors.GREY_700,
                            text_align=ft.TextAlign.CENTER
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.only(bottom=30)
                ),
                
                # Progress indicator
                self.progress_indicator,
                ft.Container(height=30),
                
                # Step content
                ft.Container(
                    content=self.step_content,
                    expand=True
                ),
                
                # Navigation buttons
                self.navigation_buttons
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO
            ),
            padding=ft.padding.all(40),
            alignment=ft.alignment.top_center,
            expand=True
        )
        
        return content
    
    def _create_default_config(self) -> Dict[str, Any]:
        """Create default assignment configuration"""
        return {
            "name": "",
            "type": "coding",
            "max_points": 100,
            "description": "",
            "github_integration": False,
            "rubric": {},
            "function_requirements": [],
            "grading_criteria": {
                "check_syntax": True,
                "run_tests": True,
                "code_analysis": True
            },
            "wizard_metadata": {
                "created_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
    
    def _build_progress_indicator(self):
        """Build the progress indicator"""
        steps = [
            ("👋", "Welcome"),
            ("📝", "Basic Info"),
            ("🎯", "Type"),
            ("📊", "Rubric"),
            ("⚙️", "Functions"),
            ("✅", "Options"),
            ("🔍", "Review")
        ]
        
        current_step_index = self.state.current_step.value - 1
        
        step_indicators = []
        for i, (icon, label) in enumerate(steps):
            is_current = i == current_step_index
            is_completed = i < current_step_index
            
            # Step circle
            if is_completed:
                step_circle = ft.Container(
                    content=ft.Icon(ft.Icons.CHECK, color=ft.Colors.WHITE, size=16),
                    width=40,
                    height=40,
                    bgcolor=ft.Colors.GREEN_600,
                    border_radius=20,
                    alignment=ft.alignment.center
                )
                text_color = ft.Colors.GREEN_600
            elif is_current:
                step_circle = ft.Container(
                    content=ft.Text(icon, size=16, color=ft.Colors.WHITE),
                    width=40,
                    height=40,
                    bgcolor=ft.Colors.BLUE_600,
                    border_radius=20,
                    alignment=ft.alignment.center
                )
                text_color = ft.Colors.BLUE_600
            else:
                step_circle = ft.Container(
                    content=ft.Text(icon, size=16, color=ft.Colors.GREY_600),
                    width=40,
                    height=40,
                    bgcolor=ft.Colors.GREY_200,
                    border_radius=20,
                    alignment=ft.alignment.center
                )
                text_color = ft.Colors.GREY_600
            
            # Step container
            step_container = ft.Column([
                step_circle,
                ft.Container(height=5),
                ft.Text(
                    label,
                    size=12,
                    color=text_color,
                    weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
            
            step_indicators.append(step_container)
            
            # Add connector line (except for last step)
            if i < len(steps) - 1:
                line_color = ft.Colors.GREEN_600 if is_completed else ft.Colors.GREY_300
                step_indicators.append(
                    ft.Container(
                        width=50,
                        height=2,
                        bgcolor=line_color,
                        margin=ft.margin.only(top=20)
                    )
                )
        
        self.progress_indicator = ft.Container(
            content=ft.Row(
                step_indicators,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=0
            ),
            padding=ft.padding.symmetric(vertical=20)
        )
    
    def _build_navigation_buttons(self):
        """Build navigation buttons"""
        # Previous button
        prev_button = ft.ElevatedButton(
            text="← Previous",
            style=ft.ButtonStyle(
                color=ft.Colors.GREY_700,
                bgcolor=ft.Colors.GREY_200
            ),
            on_click=self._go_previous,
            disabled=self.state.current_step == WizardStep.WELCOME
        )
        
        # Next/Finish button
        if self.state.current_step == WizardStep.REVIEW_CONFIRM:
            next_button = ft.ElevatedButton(
                text="🎉 Create Assignment",
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.GREEN_600
                ),
                on_click=self._finish_wizard
            )
        else:
            next_button = ft.ElevatedButton(
                text="Next →",
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.BLUE_600 if self.current_step_valid else ft.Colors.GREY_400
                ),
                on_click=self._go_next,
                disabled=not self.current_step_valid
            )
        
        # Cancel button
        cancel_button = ft.TextButton(
            text="Cancel",
            on_click=self._cancel_wizard
        )
        
        self.navigation_buttons = ft.Container(
            content=ft.Row([
                cancel_button,
                ft.Container(expand=True),
                prev_button,
                ft.Container(width=10),
                next_button
            ]),
            padding=ft.padding.symmetric(vertical=20)
        )
    
    def _build_current_step(self):
        """Build content for the current step"""
        step_builders = {
            WizardStep.WELCOME: self._build_welcome_step,
            WizardStep.BASIC_INFO: self._build_basic_info_step,
            WizardStep.ASSIGNMENT_TYPE: self._build_assignment_type_step,
            WizardStep.RUBRIC_BUILDER: self._build_rubric_builder_step,
            WizardStep.FUNCTION_REQUIREMENTS: self._build_function_requirements_step,
            WizardStep.GRADING_OPTIONS: self._build_grading_options_step,
            WizardStep.REVIEW_CONFIRM: self._build_review_confirm_step
        }
        
        builder = step_builders.get(self.state.current_step)
        if builder:
            self.step_content = builder()
        else:
            self.step_content = ft.Container(
                content=ft.Text("Step not implemented yet"),
                alignment=ft.alignment.center
            )
    
    def _build_welcome_step(self) -> ft.Container:
        """Build welcome step"""
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Icon(ft.Icons.SCHOOL, size=80, color=ft.Colors.BLUE_600),
                    alignment=ft.alignment.center
                ),
                ft.Container(height=30),
                ft.Text(
                    "Welcome to the Assignment Creation Wizard!",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=20),
                ft.Text(
                    "This wizard will guide you through creating a new assignment configuration step by step.",
                    size=16,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=30),
                ft.Container(
                    content=ft.Column([
                        ft.Text("What we'll configure:", weight=ft.FontWeight.BOLD, size=16),
                        ft.Container(height=15),
                        self._create_feature_item("📝", "Basic assignment information"),
                        self._create_feature_item("🎯", "Assignment type and objectives"),
                        self._create_feature_item("📊", "Rubric and grading criteria"),
                        self._create_feature_item("⚙️", "Function requirements (if applicable)"),
                        self._create_feature_item("✅", "Grading options and integration"),
                        self._create_feature_item("🔍", "Review and finalize")
                    ]),
                    padding=ft.padding.all(30),
                    bgcolor=ft.Colors.BLUE_50,
                    border=ft.border.all(1, ft.Colors.BLUE_200),
                    border_radius=10,
                    width=500
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center,
            width=600
        )
    
    def _create_feature_item(self, icon: str, text: str) -> ft.Row:
        """Create a feature list item"""
        return ft.Row([
            ft.Text(icon, size=16),
            ft.Container(width=10),
            ft.Text(text, size=14, color=ft.Colors.GREY_700)
        ])
    
    def _build_basic_info_step(self) -> ft.Container:
        """Build basic information step"""
        # Create form fields
        name_field = ft.TextField(
            label="Assignment Name *",
            hint_text="e.g., Programming Assignment 1, Data Structures Lab",
            value=self.state.assignment_config.get("name", ""),
            on_change=self._on_name_changed,
            width=400,
            autofocus=True
        )
        
        description_field = ft.TextField(
            label="Assignment Description",
            hint_text="Describe the assignment objectives and what students will learn",
            value=self.state.assignment_config.get("description", ""),
            multiline=True,
            min_lines=3,
            max_lines=5,
            on_change=self._on_description_changed,
            width=400
        )
        
        max_points_field = ft.TextField(
            label="Maximum Points",
            hint_text="100",
            value=str(self.state.assignment_config.get("max_points", 100)),
            on_change=self._on_max_points_changed,
            width=150,
            input_filter=ft.NumbersOnlyInputFilter()
        )
        
        # Store references for validation
        self.step_components["basic_info"] = {
            "name_field": name_field,
            "description_field": description_field,
            "max_points_field": max_points_field
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "📝 Basic Assignment Information",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800
                ),
                ft.Container(height=10),
                ft.Text(
                    "Let's start with the basic details of your assignment.",
                    size=16,
                    color=ft.Colors.GREY_700
                ),
                ft.Container(height=30),
                
                ft.Container(
                    content=ft.Column([
                        name_field,
                        ft.Container(height=20),
                        description_field,
                        ft.Container(height=20),
                        ft.Row([
                            max_points_field,
                            ft.Container(width=20),
                            ft.Container(
                                content=ft.Column([
                                    ft.Text("💡 Tip:", weight=ft.FontWeight.BOLD, size=12),
                                    ft.Text(
                                        "Choose a clear, descriptive name that\nhelps students understand the assignment.",
                                        size=12,
                                        color=ft.Colors.GREY_600
                                    )
                                ]),
                                padding=ft.padding.all(15),
                                bgcolor=ft.Colors.BLUE_50,
                                border_radius=5,
                                width=200
                            )
                        ])
                    ]),
                    padding=ft.padding.all(30),
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    width=600
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center
        )
    
    def _build_assignment_type_step(self) -> ft.Container:
        """Build assignment type selection step"""
        
        # Assignment type options
        type_options = [
            ("coding", "💻 Coding Assignment", "Students write code to solve programming problems"),
            ("project", "🎯 Project", "Multi-part assignment with design and implementation"),
            ("lab", "🔬 Lab Exercise", "Hands-on practice with guided instructions"),
            ("homework", "📚 Homework", "Practice problems and exercises")
        ]
        
        current_type = self.state.assignment_config.get("type", "coding")
        
        type_cards = []
        for type_id, title, description in type_options:
            is_selected = type_id == current_type
            
            card = ft.Container(
                content=ft.Column([
                    ft.Text(title, size=18, weight=ft.FontWeight.BOLD),
                    ft.Container(height=10),
                    ft.Text(description, size=14, color=ft.Colors.GREY_600)
                ]),
                padding=ft.padding.all(20),
                bgcolor=ft.Colors.BLUE_100 if is_selected else ft.Colors.WHITE,
                border=ft.border.all(
                    2 if is_selected else 1, 
                    ft.Colors.BLUE_600 if is_selected else ft.Colors.GREY_300
                ),
                border_radius=10,
                width=280,
                height=120,
                on_click=lambda e, t=type_id: self._select_assignment_type(t)
            )
            
            type_cards.append(card)
        
        # GitHub integration option
        github_checkbox = ft.Checkbox(
            label="Enable GitHub Integration",
            value=self.state.assignment_config.get("github_integration", False),
            on_change=self._on_github_integration_changed
        )
        
        self.step_components["assignment_type"] = {
            "github_checkbox": github_checkbox
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "🎯 Assignment Type",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800
                ),
                ft.Container(height=10),
                ft.Text(
                    "What type of assignment are you creating?",
                    size=16,
                    color=ft.Colors.GREY_700
                ),
                ft.Container(height=30),
                
                # Type selection cards
                ft.Row([
                    type_cards[0],
                    ft.Container(width=20),
                    type_cards[1]
                ], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=20),
                ft.Row([
                    type_cards[2],
                    ft.Container(width=20),
                    type_cards[3]
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Container(height=30),
                
                # Additional options
                ft.Container(
                    content=ft.Column([
                        ft.Text("Additional Options:", weight=ft.FontWeight.BOLD, size=16),
                        ft.Container(height=15),
                        github_checkbox,
                        ft.Container(height=10),
                        ft.Text(
                            "💡 GitHub integration allows automatic repository cloning and analysis",
                            size=12,
                            color=ft.Colors.GREY_600,
                            italic=True
                        )
                    ]),
                    padding=ft.padding.all(20),
                    bgcolor=ft.Colors.GREY_50,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    width=580
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center
        )
    
    def _build_rubric_builder_step(self) -> ft.Container:
        """Build rubric builder step"""
        
        # Get current rubric data
        rubric_data = self.state.assignment_config.get("rubric", {})
        
        # Rubric criteria list
        criteria_list = []
        for criterion_name, criterion_data in rubric_data.items():
            criterion_widget = self._create_rubric_criterion_widget(
                criterion_name,
                criterion_data.get("description", ""),
                criterion_data.get("weight", 0.0),
                criterion_data.get("max_points", 0.0)
            )
            criteria_list.append(criterion_widget)
        
        # If no criteria, show default suggestions
        if not criteria_list:
            criteria_list = [
                ft.Container(
                    content=ft.Column([
                        ft.Text("No rubric criteria defined yet.", color=ft.Colors.GREY_600),
                        ft.Container(height=10),
                        ft.Text("💡 Suggested criteria for coding assignments:", weight=ft.FontWeight.BOLD, size=14),
                        ft.Container(height=10),
                        ft.ElevatedButton(
                            text="+ Add Default Criteria",
                            icon=ft.Icons.AUTO_FIX_HIGH,
                            on_click=self._add_default_rubric_criteria,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE)
                        )
                    ]),
                    padding=ft.padding.all(20),
                    bgcolor=ft.Colors.BLUE_50,
                    border=ft.border.all(1, ft.Colors.BLUE_200),
                    border_radius=10
                )
            ]
        
        # Total weight calculation
        total_weight = sum(
            criterion_data.get("weight", 0.0) 
            for criterion_data in rubric_data.values()
        )
        
        weight_status = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.CHECK_CIRCLE if abs(total_weight - 1.0) < 0.01 else ft.Icons.WARNING,
                    color=ft.Colors.GREEN_600 if abs(total_weight - 1.0) < 0.01 else ft.Colors.ORANGE_600
                ),
                ft.Text(
                    f"Total Weight: {total_weight:.1%}",
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_600 if abs(total_weight - 1.0) < 0.01 else ft.Colors.ORANGE_600
                )
            ]),
            padding=ft.padding.all(15),
            bgcolor=ft.Colors.GREEN_50 if abs(total_weight - 1.0) < 0.01 else ft.Colors.ORANGE_50,
            border=ft.border.all(
                1, 
                ft.Colors.GREEN_200 if abs(total_weight - 1.0) < 0.01 else ft.Colors.ORANGE_200
            ),
            border_radius=5
        )
        
        self.step_components["rubric_builder"] = {
            "criteria_list": criteria_list,
            "weight_status": weight_status
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "📊 Rubric Builder",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800
                ),
                ft.Container(height=10),
                ft.Text(
                    "Define how your assignment will be graded.",
                    size=16,
                    color=ft.Colors.GREY_700
                ),
                ft.Container(height=30),
                
                # Add criterion button
                ft.Row([
                    ft.ElevatedButton(
                        text="+ Add Criterion",
                        icon=ft.Icons.ADD,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.PURPLE_600
                        ),
                        on_click=self._add_rubric_criterion
                    ),
                    ft.Container(expand=True),
                    weight_status
                ]),
                
                ft.Container(height=20),
                
                # Criteria list
                ft.Container(
                    content=ft.Column(criteria_list, spacing=15),
                    width=700,
                    height=400,
                    scroll=ft.ScrollMode.AUTO
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center
        )
    
    def _build_function_requirements_step(self) -> ft.Container:
        """Build function requirements step"""
        
        # Get current function requirements
        func_reqs = self.state.assignment_config.get("function_requirements", [])
        
        # Function requirements list
        func_widgets = []
        for i, func_req in enumerate(func_reqs):
            func_widget = self._create_function_requirement_widget(
                func_req.get("name", ""),
                func_req.get("description", ""),
                func_req.get("parameters", []),
                func_req.get("return_type", ""),
                i
            )
            func_widgets.append(func_widget)
        
        # If no requirements, show explanation
        if not func_widgets:
            func_widgets = [
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.FUNCTIONS, size=48, color=ft.Colors.GREY_400),
                        ft.Container(height=15),
                        ft.Text("No function requirements defined yet.", color=ft.Colors.GREY_600),
                        ft.Container(height=10),
                        ft.Text(
                            "Function requirements specify the exact functions students must implement.",
                            size=14,
                            color=ft.Colors.GREY_600,
                            text_align=ft.TextAlign.CENTER
                        ),
                        ft.Container(height=20),
                        ft.ElevatedButton(
                            text="+ Add Function Requirement",
                            icon=ft.Icons.ADD_BOX,
                            on_click=self._add_function_requirement,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)
                        )
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    padding=ft.padding.all(30),
                    bgcolor=ft.Colors.GREY_50,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    width=500,
                    alignment=ft.alignment.center
                )
            ]
        
        self.step_components["function_requirements"] = {
            "func_widgets": func_widgets
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "⚙️ Function Requirements",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800
                ),
                ft.Container(height=10),
                ft.Text(
                    "Specify functions that students must implement (optional for coding assignments).",
                    size=16,
                    color=ft.Colors.GREY_700
                ),
                ft.Container(height=30),
                
                # Add function button (if we have functions)
                ft.Row([
                    ft.ElevatedButton(
                        text="+ Add Function",
                        icon=ft.Icons.ADD,
                        style=ft.ButtonStyle(
                            color=ft.Colors.WHITE,
                            bgcolor=ft.Colors.GREEN_600
                        ),
                        on_click=self._add_function_requirement
                    ) if func_reqs else ft.Container(),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(
                            f"{len(func_reqs)} function(s) defined",
                            size=12,
                            color=ft.Colors.GREY_600
                        ),
                        padding=ft.padding.all(10)
                    ) if func_reqs else ft.Container()
                ]),
                
                ft.Container(height=20),
                
                # Function requirements list
                ft.Container(
                    content=ft.Column(func_widgets, spacing=15),
                    width=700,
                    height=400,
                    scroll=ft.ScrollMode.AUTO
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center
        )
    
    def _build_grading_options_step(self) -> ft.Container:
        """Build grading options step"""
        
        # Get current grading criteria
        grading_criteria = self.state.assignment_config.get("grading_criteria", {})
        
        # Grading options
        syntax_check = ft.Checkbox(
            label="Check Syntax",
            value=grading_criteria.get("check_syntax", True),
            on_change=lambda e: self._update_grading_criteria("check_syntax", e.control.value)
        )
        
        run_tests = ft.Checkbox(
            label="Run Tests",
            value=grading_criteria.get("run_tests", True),
            on_change=lambda e: self._update_grading_criteria("run_tests", e.control.value)
        )
        
        code_analysis = ft.Checkbox(
            label="Code Analysis",
            value=grading_criteria.get("code_analysis", True),
            on_change=lambda e: self._update_grading_criteria("code_analysis", e.control.value)
        )
        
        self.step_components["grading_options"] = {
            "syntax_check": syntax_check,
            "run_tests": run_tests,
            "code_analysis": code_analysis
        }
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "✅ Grading Options",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800
                ),
                ft.Container(height=10),
                ft.Text(
                    "Configure how submissions will be automatically graded.",
                    size=16,
                    color=ft.Colors.GREY_700
                ),
                ft.Container(height=30),
                
                ft.Container(
                    content=ft.Column([
                        ft.Text("Automatic Checks:", weight=ft.FontWeight.BOLD, size=18),
                        ft.Container(height=20),
                        
                        self._create_grading_option_card(
                            syntax_check,
                            "🔍 Syntax Checking",
                            "Verify that code compiles and has correct syntax"
                        ),
                        
                        ft.Container(height=15),
                        
                        self._create_grading_option_card(
                            run_tests,
                            "🧪 Test Execution",
                            "Run automated tests to verify functionality"
                        ),
                        
                        ft.Container(height=15),
                        
                        self._create_grading_option_card(
                            code_analysis,
                            "📊 Code Analysis",
                            "Analyze code quality, style, and best practices"
                        ),
                        
                        ft.Container(height=30),
                        
                        ft.Container(
                            content=ft.Column([
                                ft.Text("💡 Recommendation:", weight=ft.FontWeight.BOLD, size=14),
                                ft.Container(height=5),
                                ft.Text(
                                    "Enable all options for comprehensive automated grading. "
                                    "You can always adjust these later.",
                                    size=12,
                                    color=ft.Colors.GREY_600
                                )
                            ]),
                            padding=ft.padding.all(15),
                            bgcolor=ft.Colors.BLUE_50,
                            border=ft.border.all(1, ft.Colors.BLUE_200),
                            border_radius=5
                        )
                    ]),
                    padding=ft.padding.all(30),
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=10,
                    width=600
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center
        )
    
    def _create_grading_option_card(self, checkbox: ft.Checkbox, title: str, description: str) -> ft.Container:
        """Create a grading option card"""
        return ft.Container(
            content=ft.Row([
                checkbox,
                ft.Container(width=15),
                ft.Column([
                    ft.Text(title, weight=ft.FontWeight.BOLD, size=14),
                    ft.Text(description, size=12, color=ft.Colors.GREY_600)
                ], spacing=5)
            ]),
            padding=ft.padding.all(15),
            bgcolor=ft.Colors.GREY_50,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=5
        )
    
    def _build_review_confirm_step(self) -> ft.Container:
        """Build review and confirmation step"""
        
        config = self.state.assignment_config
        
        # Configuration summary
        summary_items = [
            ("📝 Name", config.get("name", "Unnamed Assignment")),
            ("🎯 Type", config.get("type", "coding").title()),
            ("💯 Max Points", str(config.get("max_points", 100))),
            ("🔗 GitHub", "Enabled" if config.get("github_integration", False) else "Disabled"),
            ("📊 Rubric Criteria", str(len(config.get("rubric", {})))),
            ("⚙️ Function Requirements", str(len(config.get("function_requirements", [])))),
        ]
        
        summary_rows = []
        for label, value in summary_items:
            summary_rows.append(
                ft.Row([
                    ft.Text(label, weight=ft.FontWeight.BOLD, width=200),
                    ft.Text(value, color=ft.Colors.GREY_700)
                ])
            )
        
        # YAML preview
        yaml_preview = yaml.dump(config, default_flow_style=False, sort_keys=False)
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "🔍 Review & Confirm",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800
                ),
                ft.Container(height=10),
                ft.Text(
                    "Review your assignment configuration before creating it.",
                    size=16,
                    color=ft.Colors.GREY_700
                ),
                ft.Container(height=30),
                
                ft.Row([
                    # Summary panel
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Assignment Summary", weight=ft.FontWeight.BOLD, size=16),
                            ft.Container(height=15),
                            ft.Column(summary_rows, spacing=10)
                        ]),
                        padding=ft.padding.all(20),
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        width=350,
                        height=300
                    ),
                    
                    ft.Container(width=20),
                    
                    # YAML preview panel
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Generated Configuration", weight=ft.FontWeight.BOLD, size=16),
                            ft.Container(height=15),
                            ft.Container(
                                content=ft.Text(
                                    yaml_preview,
                                    size=10,
                                    font_family="Courier",
                                    selectable=True
                                ),
                                bgcolor=ft.Colors.GREY_100,
                                border=ft.border.all(1, ft.Colors.GREY_300),
                                border_radius=5,
                                padding=ft.padding.all(10),
                                width=320,
                                height=250,
                                scroll=ft.ScrollMode.AUTO
                            )
                        ]),
                        padding=ft.padding.all(20),
                        bgcolor=ft.Colors.WHITE,
                        border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=10,
                        width=350,
                        height=300
                    )
                ], alignment=ft.MainAxisAlignment.CENTER),
                
                ft.Container(height=30),
                
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=ft.Colors.GREEN_600),
                        ft.Container(width=10),
                        ft.Text(
                            "Configuration is valid and ready to be created!",
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREEN_600
                        )
                    ]),
                    padding=ft.padding.all(15),
                    bgcolor=ft.Colors.GREEN_50,
                    border=ft.border.all(1, ft.Colors.GREEN_200),
                    border_radius=5
                )
            ], 
            horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            alignment=ft.alignment.center
        )
    
    # Event handlers and utility methods
    def _go_next(self, e):
        """Go to next step"""
        if self._validate_current_step():
            next_step_value = self.state.current_step.value + 1
            if next_step_value <= len(WizardStep):
                self.state.current_step = WizardStep(next_step_value)
                self._refresh_wizard()
    
    def _go_previous(self, e):
        """Go to previous step"""
        prev_step_value = self.state.current_step.value - 1
        if prev_step_value >= 1:
            self.state.current_step = WizardStep(prev_step_value)
            self._refresh_wizard()
    
    def _validate_current_step(self) -> bool:
        """Validate the current step"""
        if self.state.current_step == WizardStep.BASIC_INFO:
            name = self.state.assignment_config.get("name", "").strip()
            return len(name) > 0
        elif self.state.current_step == WizardStep.RUBRIC_BUILDER:
            rubric = self.state.assignment_config.get("rubric", {})
            if not rubric:
                return True  # Allow empty rubric
            total_weight = sum(criterion.get("weight", 0.0) for criterion in rubric.values())
            return abs(total_weight - 1.0) < 0.01
        
        return True
    
    def _refresh_wizard(self):
        """Refresh the wizard UI"""
        self._build_progress_indicator()
        self._build_current_step()
        self._build_navigation_buttons()
        
        # Update step validation
        self.current_step_valid = self._validate_current_step()
        
        # Update UI
        if hasattr(self, 'page'):
            # Update progress indicator
            self.page.controls[0].content.controls[1] = self.progress_indicator
            # Update step content
            self.page.controls[0].content.controls[3].content = self.step_content
            # Update navigation buttons
            self.page.controls[0].content.controls[4] = self.navigation_buttons
            self.page.update()
    
    def _finish_wizard(self, e):
        """Finish the wizard and create assignment"""
        if self._validate_current_step():
            assignment_name = self.state.assignment_config.get("name", "").strip()
            if assignment_name and self.on_complete:
                self.on_complete(assignment_name, self.state.assignment_config)
    
    def _cancel_wizard(self, e):
        """Cancel the wizard"""
        if self.on_cancel:
            self.on_cancel()
    
    # Form field event handlers
    def _on_name_changed(self, e):
        """Handle assignment name change"""
        self.state.assignment_config["name"] = e.control.value
        self.current_step_valid = self._validate_current_step()
        self._update_navigation_buttons()
    
    def _on_description_changed(self, e):
        """Handle description change"""
        self.state.assignment_config["description"] = e.control.value
    
    def _on_max_points_changed(self, e):
        """Handle max points change"""
        try:
            self.state.assignment_config["max_points"] = int(e.control.value) if e.control.value else 100
        except ValueError:
            pass
    
    def _select_assignment_type(self, type_id: str):
        """Select assignment type"""
        self.state.assignment_config["type"] = type_id
        self._refresh_wizard()
    
    def _on_github_integration_changed(self, e):
        """Handle GitHub integration toggle"""
        self.state.assignment_config["github_integration"] = e.control.value
    
    def _update_grading_criteria(self, key: str, value: bool):
        """Update grading criteria"""
        if "grading_criteria" not in self.state.assignment_config:
            self.state.assignment_config["grading_criteria"] = {}
        self.state.assignment_config["grading_criteria"][key] = value
    
    def _update_navigation_buttons(self):
        """Update navigation button states"""
        if hasattr(self, 'page') and self.navigation_buttons:
            # Update next button state
            next_button = self.navigation_buttons.content.controls[-1]
            next_button.disabled = not self.current_step_valid
            if self.current_step_valid:
                next_button.style.bgcolor = ft.Colors.BLUE_600
            else:
                next_button.style.bgcolor = ft.Colors.GREY_400
            self.page.update()
    
    # Rubric builder methods
    def _add_default_rubric_criteria(self, e):
        """Add default rubric criteria for coding assignments"""
        default_criteria = {
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
        }
        
        self.state.assignment_config["rubric"] = default_criteria
        self._refresh_wizard()
    
    def _add_rubric_criterion(self, e):
        """Add a new rubric criterion"""
        if "rubric" not in self.state.assignment_config:
            self.state.assignment_config["rubric"] = {}
        
        # Find a unique name
        criterion_count = len(self.state.assignment_config["rubric"])
        new_name = f"Criterion {criterion_count + 1}"
        
        while new_name in self.state.assignment_config["rubric"]:
            criterion_count += 1
            new_name = f"Criterion {criterion_count + 1}"
        
        self.state.assignment_config["rubric"][new_name] = {
            "description": "Describe this criterion",
            "weight": 0.1,
            "max_points": 10
        }
        
        self._refresh_wizard()
    
    def _create_rubric_criterion_widget(self, name: str, description: str, weight: float, max_points: float) -> ft.Container:
        """Create a rubric criterion widget for the wizard"""
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(name, weight=ft.FontWeight.BOLD, size=14),
                        ft.Text(description, size=12, color=ft.Colors.GREY_600)
                    ]),
                    width=300
                ),
                ft.Container(width=20),
                ft.Text(f"Weight: {weight:.1%}", size=12, width=80),
                ft.Text(f"Points: {max_points}", size=12, width=80),
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_color=ft.Colors.BLUE_600,
                    tooltip="Edit criterion",
                    on_click=lambda e, n=name: self._edit_rubric_criterion(n)
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=ft.Colors.RED_600,
                    tooltip="Remove criterion",
                    on_click=lambda e, n=name: self._remove_rubric_criterion(n)
                )
            ]),
            padding=ft.padding.all(15),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5
        )
    
    def _edit_rubric_criterion(self, criterion_name: str):
        """Edit a rubric criterion"""
        # For simplicity in the wizard, we'll show a simple edit dialog
        criterion_data = self.state.assignment_config.get("rubric", {}).get(criterion_name, {})
        
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"Editing '{criterion_name}' - Feature coming in advanced editor!"),
                action="OK"
            )
        )
    
    def _remove_rubric_criterion(self, criterion_name: str):
        """Remove a rubric criterion"""
        if "rubric" in self.state.assignment_config and criterion_name in self.state.assignment_config["rubric"]:
            del self.state.assignment_config["rubric"][criterion_name]
            self._refresh_wizard()
    
    # Function requirements methods
    def _add_function_requirement(self, e):
        """Add a new function requirement"""
        if "function_requirements" not in self.state.assignment_config:
            self.state.assignment_config["function_requirements"] = []
        
        new_function = {
            "name": f"function_{len(self.state.assignment_config['function_requirements']) + 1}",
            "description": "Describe what this function should do",
            "parameters": [],
            "return_type": "void"
        }
        
        self.state.assignment_config["function_requirements"].append(new_function)
        self._refresh_wizard()
    
    def _create_function_requirement_widget(self, name: str, description: str, parameters: List, return_type: str, index: int) -> ft.Container:
        """Create a function requirement widget for the wizard"""
        param_text = ", ".join([f"{p.get('type', 'type')} {p.get('name', 'param')}" for p in parameters]) if parameters else "no parameters"
        
        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"{return_type} {name}({param_text})", weight=ft.FontWeight.BOLD, size=14, font_family="Courier"),
                        ft.Text(description, size=12, color=ft.Colors.GREY_600)
                    ]),
                    width=500
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.EDIT,
                    icon_color=ft.Colors.BLUE_600,
                    tooltip="Edit function",
                    on_click=lambda e, i=index: self._edit_function_requirement(i)
                ),
                ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color=ft.Colors.RED_600,
                    tooltip="Remove function",
                    on_click=lambda e, i=index: self._remove_function_requirement(i)
                )
            ]),
            padding=ft.padding.all(15),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=5
        )
    
    def _edit_function_requirement(self, index: int):
        """Edit a function requirement"""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Function editing - Feature coming in advanced editor!"),
                action="OK"
            )
        )
    
    def _remove_function_requirement(self, index: int):
        """Remove a function requirement"""
        func_reqs = self.state.assignment_config.get("function_requirements", [])
        if 0 <= index < len(func_reqs):
            func_reqs.pop(index)
            self._refresh_wizard()


def main():
    """Test the assignment wizard"""
    def test_app(page: ft.Page):
        page.title = "Assignment Wizard Test"
        page.window.width = 1200
        page.window.height = 900
        
        def on_complete(name, config):
            print(f"Wizard completed: {name}")
            print(f"Config: {config}")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Assignment '{name}' created successfully!"),
                    action="OK"
                )
            )
        
        def on_cancel():
            print("Wizard cancelled")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Wizard cancelled"),
                    action="OK"
                )
            )
        
        wizard = AssignmentWizardPage(page, on_complete, on_cancel)
        page.add(wizard.build())
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()