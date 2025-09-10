"""
Results Page Component

Displays comprehensive grading results with summary statistics, grade distribution
visualization, individual student results table, and search/filter functionality.
"""

import flet as ft
import sys
import json
import statistics
from pathlib import Path
from typing import Callable, Optional, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.services.export_service import ExportService, ExportConfig, ExportResult


@dataclass
class StudentResult:
    """Individual student result information"""
    student_id: str
    student_name: str = ""
    total_score: float = 0.0
    max_score: float = 100.0
    percentage: float = 0.0
    grade: str = ""
    feedback: str = ""
    rubric_scores: Dict[str, float] = None
    token_usage: int = 0
    cost: float = 0.0
    github_repo: str = ""
    processing_time: float = 0.0
    status: str = "completed"  # completed, failed, partial


@dataclass
class ResultsSummary:
    """Summary statistics for all results"""
    total_students: int = 0
    completed_students: int = 0
    failed_students: int = 0
    average_score: float = 0.0
    median_score: float = 0.0
    std_deviation: float = 0.0
    min_score: float = 0.0
    max_score: float = 0.0
    total_cost: float = 0.0
    average_cost: float = 0.0
    total_tokens: int = 0
    completion_rate: float = 0.0
    grade_distribution: Dict[str, int] = None


class ResultsPage:
    """Results page component
    
    Displays comprehensive grading results with statistics, visualizations,
    and detailed student information with search and filter capabilities.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        results_data: Dict[str, Any] = None,
        on_back: Callable[[], None] = None,
        on_export: Callable[[str], None] = None
    ):
        """Initialize the results page
        
        Args:
            page: Flet page object
            results_data: Grading results data
            on_back: Callback to go back to previous page
            on_export: Callback for export functionality
        """
        self.page = page
        self.results_data = results_data or {}
        self.on_back = on_back
        self.on_export = on_export
        
        # Parse results data
        self.student_results: List[StudentResult] = []
        self.summary: ResultsSummary = ResultsSummary()
        self._parse_results_data()
        
        # Export service
        self.export_service = ExportService()
        self.export_capabilities = self.export_service.get_export_capabilities()
        
        # Search and filter state
        self.search_query = ""
        self.filter_status = "all"  # all, completed, failed
        self.filter_grade = "all"   # all, A, B, C, D, F
        self.sort_by = "score_desc" # score_desc, score_asc, name_asc, name_desc
        
        # UI components
        self.summary_cards = None
        self.grade_distribution_chart = None
        self.search_field = None
        self.filter_controls = None
        self.results_table = None
        self.filtered_results = []
        self.export_dialog = None
        
    def build(self) -> ft.Control:
        """Build and return the results page UI"""
        
        # Page header
        header = ft.Container(
            content=ft.Column([
                ft.Text(
                    "📊 Grading Results",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_800,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Text(
                    f"Results for {self.summary.total_students} students",
                    size=16,
                    color=ft.Colors.GREY_700,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.only(bottom=30)
        )
        
        # Build UI sections
        self._build_summary_cards()
        self._build_grade_distribution()
        self._build_search_and_filters()
        self._build_results_table()
        
        # Initial filter application
        self._apply_filters()
        
        # Action buttons
        action_buttons = ft.Container(
            content=ft.Row([
                ft.ElevatedButton(
                    text="← Back",
                    icon=ft.Icons.ARROW_BACK,
                    style=ft.ButtonStyle(
                        color=ft.Colors.GREY_700,
                        bgcolor=ft.Colors.GREY_200
                    ),
                    on_click=self._on_back_clicked
                ),
                ft.Container(width=20),
                ft.ElevatedButton(
                    text="📊 Export Options",
                    icon=ft.Icons.DOWNLOAD,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600
                    ),
                    on_click=self._show_export_dialog
                ),
                ft.ElevatedButton(
                    text="📁 Archive Results",
                    icon=ft.Icons.ARCHIVE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.ORANGE_600
                    ),
                    on_click=self._archive_results
                ),
                ft.ElevatedButton(
                    text="📤 Share Results",
                    icon=ft.Icons.SHARE,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.PURPLE_600
                    ),
                    on_click=self._show_share_dialog
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            padding=ft.padding.symmetric(vertical=20)
        )
        
        # Main content layout
        content_sections = ft.Column([
            # Summary cards
            self.summary_cards,
            
            ft.Container(height=30),
            
            # Grade distribution and search/filters row
            ft.Row([
                self.grade_distribution_chart,
                ft.Container(width=30),
                self.search_and_filters
            ], alignment=ft.MainAxisAlignment.CENTER, wrap=True),
            
            ft.Container(height=30),
            
            # Results table
            self.results_table,
            
            # Action buttons
            action_buttons
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
        
        return content
    
    def _parse_results_data(self):
        """Parse the results data into structured format"""
        if not self.results_data:
            return
        
        # Initialize with sample data if no real data provided
        # In real implementation, this would parse actual grading results
        self._create_sample_data()
        
        # Calculate summary statistics
        self._calculate_summary_statistics()
    
    def _create_sample_data(self):
        """Create sample data for demonstration"""
        import random
        
        # Generate sample student results
        grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
        grade_ranges = {
            'A+': (95, 100), 'A': (90, 94), 'A-': (87, 89),
            'B+': (83, 86), 'B': (80, 82), 'B-': (77, 79),
            'C+': (73, 76), 'C': (70, 72), 'C-': (67, 69),
            'D': (60, 66), 'F': (0, 59)
        }
        
        num_students = self.results_data.get('total_students', 25)
        
        for i in range(1, num_students + 1):
            # Simulate realistic grade distribution (mostly B-A range)
            if random.random() < 0.7:  # 70% get B- or better
                possible_grades = ['A+', 'A', 'A-', 'B+', 'B', 'B-']
            else:
                possible_grades = grades
            
            grade = random.choice(possible_grades)
            score_range = grade_ranges[grade]
            total_score = random.uniform(score_range[0], score_range[1])
            
            # Sample rubric scores (assuming 4 criteria)
            rubric_scores = {
                'Functionality': random.uniform(score_range[0] * 0.3, min(100, score_range[1] + 5)) * 0.3,
                'Code Quality': random.uniform(score_range[0] * 0.25, min(100, score_range[1] + 3)) * 0.25,
                'Documentation': random.uniform(score_range[0] * 0.25, min(100, score_range[1] + 2)) * 0.25,
                'Testing': random.uniform(score_range[0] * 0.2, min(100, score_range[1] + 1)) * 0.2
            }
            
            student_result = StudentResult(
                student_id=f"student_{i:03d}",
                student_name=f"Student {i}",
                total_score=total_score,
                max_score=100.0,
                percentage=total_score,
                grade=grade,
                feedback=f"Good work on assignment. {random.choice(['Excellent implementation.', 'Well documented code.', 'Creative solution approach.', 'Solid understanding demonstrated.'])}",
                rubric_scores=rubric_scores,
                token_usage=random.randint(800, 2500),
                cost=random.uniform(0.05, 0.25),
                github_repo=f"https://github.com/student{i}/assignment" if random.random() > 0.3 else "",
                processing_time=random.uniform(45, 180),
                status="completed" if random.random() > 0.05 else "failed"
            )
            
            self.student_results.append(student_result)
    
    def _calculate_summary_statistics(self):
        """Calculate summary statistics from student results"""
        if not self.student_results:
            return
        
        completed_results = [r for r in self.student_results if r.status == "completed"]
        failed_results = [r for r in self.student_results if r.status == "failed"]
        
        if completed_results:
            scores = [r.total_score for r in completed_results]
            costs = [r.cost for r in completed_results]
            tokens = [r.token_usage for r in completed_results]
            
            # Grade distribution
            grade_dist = {}
            for result in completed_results:
                grade_dist[result.grade] = grade_dist.get(result.grade, 0) + 1
            
            self.summary = ResultsSummary(
                total_students=len(self.student_results),
                completed_students=len(completed_results),
                failed_students=len(failed_results),
                average_score=statistics.mean(scores),
                median_score=statistics.median(scores),
                std_deviation=statistics.stdev(scores) if len(scores) > 1 else 0.0,
                min_score=min(scores),
                max_score=max(scores),
                total_cost=sum(costs),
                average_cost=statistics.mean(costs),
                total_tokens=sum(tokens),
                completion_rate=(len(completed_results) / len(self.student_results)) * 100,
                grade_distribution=grade_dist
            )
        else:
            self.summary = ResultsSummary(
                total_students=len(self.student_results),
                failed_students=len(failed_results),
                completion_rate=0.0,
                grade_distribution={}
            )
    
    def _build_summary_cards(self):
        """Build summary statistics cards"""
        # Create summary cards
        cards = [
            self._create_summary_card(
                "📈 Overall Performance",
                [
                    f"Average Score: {self.summary.average_score:.1f}%",
                    f"Median Score: {self.summary.median_score:.1f}%",
                    f"Std Deviation: {self.summary.std_deviation:.1f}",
                    f"Range: {self.summary.min_score:.1f} - {self.summary.max_score:.1f}"
                ],
                ft.Colors.BLUE_600
            ),
            
            self._create_summary_card(
                "✅ Completion Stats",
                [
                    f"Total Students: {self.summary.total_students}",
                    f"Completed: {self.summary.completed_students}",
                    f"Failed: {self.summary.failed_students}",
                    f"Success Rate: {self.summary.completion_rate:.1f}%"
                ],
                ft.Colors.GREEN_600
            ),
            
            self._create_summary_card(
                "💰 Cost Analysis",
                [
                    f"Total Cost: ${self.summary.total_cost:.2f}",
                    f"Average per Student: ${self.summary.average_cost:.3f}",
                    f"Total Tokens: {self.summary.total_tokens:,}",
                    f"Avg Tokens/Student: {int(self.summary.total_tokens / max(1, self.summary.completed_students)):,}"
                ],
                ft.Colors.ORANGE_600
            )
        ]
        
        self.summary_cards = ft.Row(
            cards,
            alignment=ft.MainAxisAlignment.CENTER,
            wrap=True
        )
    
    def _create_summary_card(self, title: str, stats: List[str], color: ft.Colors) -> ft.Container:
        """Create a summary statistics card"""
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    title,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=color
                ),
                ft.Divider(color=color),
                ft.Column([
                    ft.Text(stat, size=12, color=ft.Colors.GREY_700)
                    for stat in stats
                ], spacing=5)
            ], spacing=10),
            padding=ft.padding.all(20),
            border=ft.border.all(1, color),
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            width=280,
            height=160
        )
    
    def _build_grade_distribution(self):
        """Build grade distribution visualization"""
        if not self.summary.grade_distribution:
            self.grade_distribution_chart = ft.Container(
                content=ft.Text("No grade data available"),
                width=400,
                height=300
            )
            return
        
        # Create simple bar chart representation
        grade_order = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']
        max_count = max(self.summary.grade_distribution.values()) if self.summary.grade_distribution else 1
        
        bars = []
        for grade in grade_order:
            count = self.summary.grade_distribution.get(grade, 0)
            if count > 0:  # Only show grades that exist
                bar_height = (count / max_count) * 200
                bars.append(
                    ft.Column([
                        ft.Container(
                            width=30,
                            height=max(5, bar_height),
                            bgcolor=self._get_grade_color(grade),
                            border_radius=3
                        ),
                        ft.Text(grade, size=10, text_align=ft.TextAlign.CENTER),
                        ft.Text(str(count), size=9, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=3)
                )
        
        self.grade_distribution_chart = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Grade Distribution",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.INDIGO_800
                ),
                ft.Container(height=10),
                ft.Row(
                    bars,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=10
                ) if bars else ft.Text("No grades to display", color=ft.Colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.INDIGO_200),
            border_radius=10,
            bgcolor=ft.Colors.INDIGO_50,
            width=400,
            height=300
        )
    
    def _get_grade_color(self, grade: str) -> ft.Colors:
        """Get color for grade visualization"""
        color_map = {
            'A+': ft.Colors.GREEN_700, 'A': ft.Colors.GREEN_600, 'A-': ft.Colors.GREEN_500,
            'B+': ft.Colors.BLUE_600, 'B': ft.Colors.BLUE_500, 'B-': ft.Colors.BLUE_400,
            'C+': ft.Colors.ORANGE_500, 'C': ft.Colors.ORANGE_400, 'C-': ft.Colors.ORANGE_300,
            'D': ft.Colors.RED_400, 'F': ft.Colors.RED_600
        }
        return color_map.get(grade, ft.Colors.GREY_500)
    
    def _build_search_and_filters(self):
        """Build search and filter controls"""
        # Search field
        self.search_field = ft.TextField(
            label="Search students",
            hint_text="Enter student name or ID",
            prefix_icon=ft.Icons.SEARCH,
            on_change=self._on_search_changed,
            width=250
        )
        
        # Filter controls
        status_filter = ft.Dropdown(
            label="Status",
            width=120,
            options=[
                ft.dropdown.Option("all", "All"),
                ft.dropdown.Option("completed", "Completed"),
                ft.dropdown.Option("failed", "Failed")
            ],
            value="all",
            on_change=self._on_filter_changed
        )
        
        grade_filter = ft.Dropdown(
            label="Grade",
            width=100,
            options=[
                ft.dropdown.Option("all", "All"),
                ft.dropdown.Option("A", "A's"),
                ft.dropdown.Option("B", "B's"),
                ft.dropdown.Option("C", "C's"),
                ft.dropdown.Option("D", "D's"),
                ft.dropdown.Option("F", "F's")
            ],
            value="all",
            on_change=self._on_filter_changed
        )
        
        sort_dropdown = ft.Dropdown(
            label="Sort by",
            width=150,
            options=[
                ft.dropdown.Option("score_desc", "Score ↓"),
                ft.dropdown.Option("score_asc", "Score ↑"),
                ft.dropdown.Option("name_asc", "Name A-Z"),
                ft.dropdown.Option("name_desc", "Name Z-A")
            ],
            value="score_desc",
            on_change=self._on_sort_changed
        )
        
        self.search_and_filters = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Search & Filter",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PURPLE_800
                ),
                ft.Container(height=10),
                self.search_field,
                ft.Container(height=10),
                status_filter,
                ft.Container(height=10),
                grade_filter,
                ft.Container(height=10),
                sort_dropdown,
                ft.Container(height=10),
                ft.ElevatedButton(
                    text="Clear Filters",
                    icon=ft.Icons.CLEAR,
                    on_click=self._clear_filters
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.PURPLE_200),
            border_radius=10,
            bgcolor=ft.Colors.PURPLE_50,
            width=300,
            height=300
        )
    
    def _build_results_table(self):
        """Build the results table"""
        # Table header
        header = ft.Row([
            ft.Text("Student", weight=ft.FontWeight.BOLD, width=120),
            ft.Text("Score", weight=ft.FontWeight.BOLD, width=80),
            ft.Text("Grade", weight=ft.FontWeight.BOLD, width=60),
            ft.Text("Cost", weight=ft.FontWeight.BOLD, width=80),
            ft.Text("Tokens", weight=ft.FontWeight.BOLD, width=80),
            ft.Text("Status", weight=ft.FontWeight.BOLD, width=80),
            ft.Text("Actions", weight=ft.FontWeight.BOLD, width=100)
        ], spacing=10)
        
        # Table container
        self.results_table = ft.Container(
            content=ft.Column([
                ft.Text(
                    "Student Results",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.TEAL_800
                ),
                ft.Container(height=10),
                header,
                ft.Divider(),
                ft.Container(
                    content=ft.ListView(
                        height=400,
                        spacing=5,
                        padding=ft.padding.all(10)
                    ),
                    height=400
                )
            ]),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.TEAL_200),
            border_radius=10,
            bgcolor=ft.Colors.TEAL_50,
            width=900
        )
        
        # Store reference to ListView for updates
        self.results_list = self.results_table.content.controls[3].content
    
    def _apply_filters(self):
        """Apply current search and filter settings"""
        filtered = self.student_results.copy()
        
        # Apply search filter
        if self.search_query:
            filtered = [
                r for r in filtered 
                if self.search_query.lower() in r.student_id.lower() 
                or self.search_query.lower() in r.student_name.lower()
            ]
        
        # Apply status filter
        if self.filter_status != "all":
            filtered = [r for r in filtered if r.status == self.filter_status]
        
        # Apply grade filter
        if self.filter_grade != "all":
            filtered = [r for r in filtered if r.grade.startswith(self.filter_grade)]
        
        # Apply sorting
        if self.sort_by == "score_desc":
            filtered.sort(key=lambda x: x.total_score, reverse=True)
        elif self.sort_by == "score_asc":
            filtered.sort(key=lambda x: x.total_score)
        elif self.sort_by == "name_asc":
            filtered.sort(key=lambda x: x.student_name)
        elif self.sort_by == "name_desc":
            filtered.sort(key=lambda x: x.student_name, reverse=True)
        
        self.filtered_results = filtered
        self._update_results_table()
    
    def _update_results_table(self):
        """Update the results table with filtered results"""
        if not hasattr(self, 'results_list'):
            return
        
        self.results_list.controls.clear()
        
        for result in self.filtered_results:
            row = self._create_result_row(result)
            self.results_list.controls.append(row)
        
        # Add "no results" message if empty
        if not self.filtered_results:
            self.results_list.controls.append(
                ft.Container(
                    content=ft.Text(
                        "No results match current filters",
                        color=ft.Colors.GREY_600,
                        text_align=ft.TextAlign.CENTER
                    ),
                    padding=ft.padding.all(20)
                )
            )
        
        self.page.update()
    
    def _create_result_row(self, result: StudentResult) -> ft.Container:
        """Create a row for the results table"""
        status_color = ft.Colors.GREEN_600 if result.status == "completed" else ft.Colors.RED_600
        
        return ft.Container(
            content=ft.Row([
                ft.Text(f"{result.student_name}\n({result.student_id})", width=120, size=11),
                ft.Text(f"{result.total_score:.1f}%", width=80, color=self._get_grade_color(result.grade)),
                ft.Text(result.grade, width=60, weight=ft.FontWeight.BOLD, color=self._get_grade_color(result.grade)),
                ft.Text(f"${result.cost:.3f}", width=80, size=11),
                ft.Text(f"{result.token_usage:,}", width=80, size=11),
                ft.Text(result.status, width=80, color=status_color, size=11),
                ft.ElevatedButton(
                    text="Details",
                    width=90,
                    height=30,
                    on_click=lambda e, r=result: self._show_student_details(r)
                )
            ], spacing=10),
            padding=ft.padding.symmetric(horizontal=5, vertical=8),
            border_radius=5,
            bgcolor=ft.Colors.WHITE if self.filtered_results.index(result) % 2 == 0 else ft.Colors.GREY_50,
            border=ft.border.all(1, ft.Colors.GREY_200)
        )
    
    def _show_student_details(self, result: StudentResult):
        """Show detailed student results in a dialog"""
        self._create_student_details_dialog(result)
    
    def _on_search_changed(self, e):
        """Handle search field changes"""
        self.search_query = e.control.value
        self._apply_filters()
    
    def _on_filter_changed(self, e):
        """Handle filter dropdown changes"""
        if "Status" in e.control.label:
            self.filter_status = e.control.value
        elif "Grade" in e.control.label:
            self.filter_grade = e.control.value
        self._apply_filters()
    
    def _on_sort_changed(self, e):
        """Handle sort dropdown changes"""
        self.sort_by = e.control.value
        self._apply_filters()
    
    def _clear_filters(self, e):
        """Clear all filters and search"""
        self.search_query = ""
        self.filter_status = "all"
        self.filter_grade = "all"
        self.sort_by = "score_desc"
        
        # Reset UI controls
        self.search_field.value = ""
        # Note: Would need references to dropdowns to reset them
        
        self._apply_filters()
    
    def _show_export_dialog(self, e):
        """Show comprehensive export options dialog"""
        self._create_export_dialog()
    
    def _create_export_dialog(self):
        """Create export options dialog"""
        
        # Export format selection
        format_selection = ft.Column([
            ft.Text("Select Export Format:", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton(
                    text="📊 Excel (.xlsx)",
                    icon=ft.Icons.TABLE_CHART,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.GREEN_600 if self.export_capabilities["excel"] else ft.Colors.GREY_400
                    ),
                    disabled=not self.export_capabilities["excel"],
                    on_click=lambda e: self._export_with_options("excel"),
                    width=180
                ),
                ft.ElevatedButton(
                    text="📄 PDF Report",
                    icon=ft.Icons.PICTURE_AS_PDF,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.RED_600 if self.export_capabilities["pdf"] else ft.Colors.GREY_400
                    ),
                    disabled=not self.export_capabilities["pdf"],
                    on_click=lambda e: self._export_with_options("pdf"),
                    width=180
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton(
                    text="🔗 JSON Data",
                    icon=ft.Icons.DATA_OBJECT,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.PURPLE_600
                    ),
                    on_click=lambda e: self._export_with_options("json"),
                    width=180
                ),
                ft.ElevatedButton(
                    text="📋 CSV Table",
                    icon=ft.Icons.TABLE_ROWS,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600
                    ),
                    on_click=lambda e: self._export_with_options("csv"),
                    width=180
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
        ])
        
        # Export options
        self.export_options = {
            "include_summary": ft.Checkbox(label="Summary Statistics", value=True),
            "include_individual_results": ft.Checkbox(label="Individual Results", value=True),
            "include_rubric_details": ft.Checkbox(label="Rubric Details", value=True),
            "include_feedback": ft.Checkbox(label="Student Feedback", value=True),
            "include_cost_analysis": ft.Checkbox(label="Cost Analysis", value=True),
            "include_github_info": ft.Checkbox(label="GitHub Information", value=True)
        }
        
        options_section = ft.Column([
            ft.Text("Export Options:", size=16, weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            ft.Column([
                ft.Row([
                    self.export_options["include_summary"],
                    self.export_options["include_individual_results"]
                ]),
                ft.Row([
                    self.export_options["include_rubric_details"],
                    self.export_options["include_feedback"]
                ]),
                ft.Row([
                    self.export_options["include_cost_analysis"],
                    self.export_options["include_github_info"]
                ])
            ])
        ])
        
        # Capability warnings
        warnings = []
        if not self.export_capabilities["excel"]:
            warnings.append("⚠️ Excel export requires 'openpyxl' package")
        if not self.export_capabilities["pdf"]:
            warnings.append("⚠️ PDF export requires 'reportlab' package")
        
        warning_section = ft.Column([
            ft.Text(warning, size=11, color=ft.Colors.ORANGE_600)
            for warning in warnings
        ]) if warnings else ft.Container()
        
        # Dialog content
        dialog_content = ft.Column([
            format_selection,
            ft.Container(height=20),
            options_section,
            ft.Container(height=15),
            warning_section
        ], width=500, height=400, scroll=ft.ScrollMode.AUTO)
        
        # Create dialog
        self.export_dialog = ft.AlertDialog(
            title=ft.Text("Export Results"),
            content=dialog_content,
            actions=[
                ft.TextButton("Cancel", on_click=self._close_export_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True
        )
        
        self.page.dialog = self.export_dialog
        self.export_dialog.open = True
        self.page.update()
    
    def _export_with_options(self, format_type: str):
        """Export results with selected options"""
        # Create export config from selected options
        config = ExportConfig(
            include_summary=self.export_options["include_summary"].value,
            include_individual_results=self.export_options["include_individual_results"].value,
            include_rubric_details=self.export_options["include_rubric_details"].value,
            include_feedback=self.export_options["include_feedback"].value,
            include_cost_analysis=self.export_options["include_cost_analysis"].value,
            include_github_info=self.export_options["include_github_info"].value,
            file_name_prefix=f"grading_results_{format_type}"
        )
        
        # Close dialog
        self._close_export_dialog(None)
        
        # Show progress
        progress_dialog = ft.AlertDialog(
            title=ft.Text(f"Exporting to {format_type.upper()}..."),
            content=ft.Container(
                content=ft.Column([
                    ft.ProgressRing(),
                    ft.Text("Please wait while your results are being exported.")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=300,
                height=100
            ),
            modal=True
        )
        
        self.page.dialog = progress_dialog
        progress_dialog.open = True
        self.page.update()
        
        # Perform export
        try:
            result = self.export_service.export_results(
                self.results_data,
                self.student_results,
                self.summary,
                format_type,
                config
            )
            
            # Close progress dialog
            progress_dialog.open = False
            self.page.update()
            
            if result.success:
                # Show success message
                success_dialog = ft.AlertDialog(
                    title=ft.Text("Export Successful! ✅"),
                    content=ft.Column([
                        ft.Text(f"Results exported to {format_type.upper()} format"),
                        ft.Container(height=10),
                        ft.Text(f"File: {Path(result.file_path).name}", size=12, color=ft.Colors.GREY_600),
                        ft.Text(f"Size: {result.file_size:,} bytes", size=12, color=ft.Colors.GREY_600),
                        ft.Text(f"Location: {Path(result.file_path).parent}", size=11, color=ft.Colors.GREY_600),
                        ft.Container(height=15),
                        ft.Row([
                            ft.ElevatedButton(
                                text="Open Folder",
                                icon=ft.Icons.FOLDER_OPEN,
                                on_click=lambda e: self._open_export_folder(result.file_path)
                            ),
                            ft.ElevatedButton(
                                text="Copy Path",
                                icon=ft.Icons.COPY,
                                on_click=lambda e: self._copy_file_path(result.file_path)
                            )
                        ], alignment=ft.MainAxisAlignment.CENTER)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    actions=[ft.TextButton("OK", on_click=lambda e: self._close_dialog(success_dialog))],
                    modal=True
                )
                
                self.page.dialog = success_dialog
                success_dialog.open = True
                self.page.update()
            else:
                # Show error message
                self._show_export_error(result.error_message)
                
        except Exception as e:
            # Close progress dialog
            progress_dialog.open = False
            self.page.update()
            self._show_export_error(f"Export failed: {str(e)}")
    
    def _show_export_error(self, error_message: str):
        """Show export error dialog"""
        error_dialog = ft.AlertDialog(
            title=ft.Text("Export Failed ❌"),
            content=ft.Column([
                ft.Text("The export operation failed with the following error:"),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Text(error_message, size=12, color=ft.Colors.RED_600),
                    padding=ft.padding.all(10),
                    bgcolor=ft.Colors.RED_50,
                    border=ft.border.all(1, ft.Colors.RED_200),
                    border_radius=5,
                    width=400
                )
            ]),
            actions=[ft.TextButton("OK", on_click=lambda e: self._close_dialog(error_dialog))],
            modal=True
        )
        
        self.page.dialog = error_dialog
        error_dialog.open = True
        self.page.update()
    
    def _archive_results(self, e):
        """Archive current results"""
        # Show archive dialog
        assignment_name_field = ft.TextField(
            label="Assignment Name (optional)",
            hint_text="e.g., Assignment 1, Midterm Project",
            width=300
        )
        
        archive_dialog = ft.AlertDialog(
            title=ft.Text("Archive Results"),
            content=ft.Column([
                ft.Text("Archive these results for future reference?"),
                ft.Container(height=15),
                assignment_name_field,
                ft.Container(height=10),
                ft.Text(
                    "This will save complete results in multiple formats for long-term storage.",
                    size=12,
                    color=ft.Colors.GREY_600
                )
            ], width=350),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(archive_dialog)),
                ft.ElevatedButton(
                    "Archive",
                    icon=ft.Icons.ARCHIVE,
                    on_click=lambda e: self._perform_archive(assignment_name_field.value, archive_dialog)
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True
        )
        
        self.page.dialog = archive_dialog
        archive_dialog.open = True
        self.page.update()
    
    def _perform_archive(self, assignment_name: str, dialog: ft.AlertDialog):
        """Perform the archiving operation"""
        dialog.open = False
        self.page.update()
        
        # Show progress
        progress_dialog = ft.AlertDialog(
            title=ft.Text("Creating Archive..."),
            content=ft.Container(
                content=ft.Column([
                    ft.ProgressRing(),
                    ft.Text("Archiving results for future reference...")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=300,
                height=100
            ),
            modal=True
        )
        
        self.page.dialog = progress_dialog
        progress_dialog.open = True
        self.page.update()
        
        # Perform archive
        try:
            result = self.export_service.archive_results(
                self.results_data,
                self.student_results,
                self.summary,
                assignment_name.strip() if assignment_name else ""
            )
            
            progress_dialog.open = False
            self.page.update()
            
            if result.success:
                success_dialog = ft.AlertDialog(
                    title=ft.Text("Archive Created! 📁"),
                    content=ft.Column([
                        ft.Text("Results have been successfully archived."),
                        ft.Container(height=10),
                        ft.Text(f"Archive location: {result.file_path}", size=11, color=ft.Colors.GREY_600),
                        ft.Container(height=10),
                        ft.Text("Archive includes JSON and CSV formats for maximum compatibility.", size=12)
                    ]),
                    actions=[ft.TextButton("OK", on_click=lambda e: self._close_dialog(success_dialog))],
                    modal=True
                )
                
                self.page.dialog = success_dialog
                success_dialog.open = True
                self.page.update()
            else:
                self._show_export_error(result.error_message)
                
        except Exception as e:
            progress_dialog.open = False
            self.page.update()
            self._show_export_error(f"Archive failed: {str(e)}")
    
    def _show_share_dialog(self, e):
        """Show sharing options dialog"""
        share_dialog = ft.AlertDialog(
            title=ft.Text("Share Results"),
            content=ft.Column([
                ft.Text("Choose sharing method:"),
                ft.Container(height=15),
                ft.ElevatedButton(
                    text="📧 Email Summary",
                    icon=ft.Icons.EMAIL,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_600
                    ),
                    on_click=lambda e: self._share_via_email(),
                    width=200
                ),
                ft.Container(height=10),
                ft.ElevatedButton(
                    text="🔗 Generate Share Link",
                    icon=ft.Icons.LINK,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.GREEN_600
                    ),
                    on_click=lambda e: self._generate_share_link(),
                    width=200
                ),
                ft.Container(height=10),
                ft.ElevatedButton(
                    text="📤 Quick Export & Copy",
                    icon=ft.Icons.CONTENT_COPY,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.PURPLE_600
                    ),
                    on_click=lambda e: self._quick_export_copy(),
                    width=200
                ),
                ft.Container(height=15),
                ft.Text(
                    "Note: Email and link sharing are placeholder features for this demo.",
                    size=11,
                    color=ft.Colors.GREY_600,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, width=300),
            actions=[ft.TextButton("Cancel", on_click=lambda e: self._close_dialog(share_dialog))],
            modal=True
        )
        
        self.page.dialog = share_dialog
        share_dialog.open = True
        self.page.update()
    
    def _share_via_email(self):
        """Share results via email (placeholder)"""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("📧 Email sharing functionality would integrate with email client"),
                action="OK"
            )
        )
    
    def _generate_share_link(self):
        """Generate shareable link (placeholder)"""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("🔗 Share link generation would create secure temporary access"),
                action="OK"
            )
        )
    
    def _quick_export_copy(self):
        """Quick export and copy summary to clipboard"""
        summary_text = f"""Grading Results Summary
========================
Total Students: {self.summary.total_students}
Completed: {self.summary.completed_students}
Average Score: {self.summary.average_score:.1f}%
Completion Rate: {self.summary.completion_rate:.1f}%
Total Cost: ${self.summary.total_cost:.2f}

Generated by Academic Auto Grader"""
        
        # In real implementation, this would copy to clipboard
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("📋 Summary copied to clipboard for easy sharing!"),
                action="OK"
            )
        )
    
    def _open_export_folder(self, file_path: str):
        """Open the folder containing exported file"""
        # In real implementation, this would open the file manager
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"Would open folder: {Path(file_path).parent}"),
                action="OK"
            )
        )
    
    def _copy_file_path(self, file_path: str):
        """Copy file path to clipboard"""
        # In real implementation, this would copy to clipboard
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("File path copied to clipboard!"),
                action="OK"
            )
        )
    
    def _close_export_dialog(self, e):
        """Close export dialog"""
        if self.export_dialog:
            self.export_dialog.open = False
            self.page.update()
    
    def _create_student_details_dialog(self, result: StudentResult):
        """Create and show detailed student results dialog"""
        
        # Header section with student info
        header_section = ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(ft.Icons.PERSON, size=40, color=ft.Colors.BLUE_600),
                    width=60,
                    height=60,
                    bgcolor=ft.Colors.BLUE_50,
                    border_radius=30,
                    alignment=ft.alignment.center
                ),
                ft.Container(width=15),
                ft.Column([
                    ft.Text(
                        result.student_name,
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800
                    ),
                    ft.Text(
                        f"ID: {result.student_id}",
                        size=14,
                        color=ft.Colors.GREY_600
                    ),
                    ft.Text(
                        f"Status: {result.status.title()}",
                        size=12,
                        color=ft.Colors.GREEN_600 if result.status == "completed" else ft.Colors.RED_600,
                        weight=ft.FontWeight.BOLD
                    )
                ], spacing=2)
            ], alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10
        )
        
        # Score summary section
        score_section = ft.Container(
            content=ft.Column([
                ft.Text(
                    "📊 Score Summary",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.INDIGO_800
                ),
                ft.Container(height=10),
                ft.Row([
                    self._create_score_metric("Total Score", f"{result.total_score:.1f}%", result.grade),
                    self._create_score_metric("Max Score", f"{result.max_score:.1f}%", "100"),
                    self._create_score_metric("Grade", result.grade, result.grade),
                    self._create_score_metric("Percentage", f"{result.percentage:.1f}%", result.grade)
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND, wrap=True)
            ]),
            padding=ft.padding.all(15),
            border=ft.border.all(1, ft.Colors.INDIGO_200),
            border_radius=8,
            bgcolor=ft.Colors.INDIGO_50
        )
        
        # Rubric scores section
        rubric_section = self._create_rubric_scores_section(result)
        
        # Cost and performance section
        perf_section = ft.Container(
            content=ft.Column([
                ft.Text(
                    "💰 Cost & Performance",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.ORANGE_800
                ),
                ft.Container(height=10),
                ft.Row([
                    self._create_perf_metric("Cost", f"${result.cost:.3f}", ft.Colors.ORANGE_600),
                    self._create_perf_metric("Tokens", f"{result.token_usage:,}", ft.Colors.PURPLE_600),
                    self._create_perf_metric("Processing Time", f"{result.processing_time:.1f}s", ft.Colors.TEAL_600),
                    self._create_perf_metric("Cost/Token", f"${result.cost/max(1, result.token_usage):.6f}", ft.Colors.BROWN_600)
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND, wrap=True)
            ]),
            padding=ft.padding.all(15),
            border=ft.border.all(1, ft.Colors.ORANGE_200),
            border_radius=8,
            bgcolor=ft.Colors.ORANGE_50
        )
        
        # GitHub repository section
        github_section = self._create_github_section(result)
        
        # Feedback section
        feedback_section = ft.Container(
            content=ft.Column([
                ft.Text(
                    "📝 Feedback",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_800
                ),
                ft.Container(height=10),
                ft.Container(
                    content=ft.Text(
                        result.feedback or "No feedback available",
                        size=12,
                        color=ft.Colors.GREY_700,
                        selectable=True
                    ),
                    padding=ft.padding.all(15),
                    bgcolor=ft.Colors.WHITE,
                    border=ft.border.all(1, ft.Colors.GREY_300),
                    border_radius=5,
                    width=500
                )
            ]),
            padding=ft.padding.all(15),
            border=ft.border.all(1, ft.Colors.GREEN_200),
            border_radius=8,
            bgcolor=ft.Colors.GREEN_50
        )
        
        # Export buttons
        export_buttons = ft.Row([
            ft.ElevatedButton(
                text="Export PDF",
                icon=ft.Icons.PICTURE_AS_PDF,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.RED_600
                ),
                on_click=lambda e: self._export_individual_result(result, "pdf")
            ),
            ft.ElevatedButton(
                text="Export JSON",
                icon=ft.Icons.DATA_OBJECT,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.PURPLE_600
                ),
                on_click=lambda e: self._export_individual_result(result, "json")
            ),
            ft.ElevatedButton(
                text="Copy Details",
                icon=ft.Icons.COPY,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.BLUE_600
                ),
                on_click=lambda e: self._copy_student_details(result)
            )
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        
        # Dialog content
        dialog_content = ft.Column([
            header_section,
            ft.Container(height=15),
            score_section,
            ft.Container(height=15),
            rubric_section,
            ft.Container(height=15),
            perf_section,
            ft.Container(height=15),
            github_section,
            ft.Container(height=15),
            feedback_section,
            ft.Container(height=20),
            export_buttons
        ], 
        spacing=0,
        scroll=ft.ScrollMode.AUTO,
        height=600
        )
        
        # Create and show dialog
        dialog = ft.AlertDialog(
            title=ft.Text(f"Student Details: {result.student_name}"),
            content=ft.Container(
                content=dialog_content,
                width=600,
                height=600
            ),
            actions=[
                ft.TextButton("Close", on_click=lambda e: self._close_dialog(dialog))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            modal=True
        )
        
        self.page.dialog = dialog
        dialog.open = True
        self.page.update()
    
    def _create_score_metric(self, label: str, value: str, grade: str) -> ft.Container:
        """Create a score metric display"""
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=10, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                ft.Text(
                    value, 
                    size=14, 
                    weight=ft.FontWeight.BOLD, 
                    color=self._get_grade_color(grade),
                    text_align=ft.TextAlign.CENTER
                )
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=110,
            padding=ft.padding.all(8),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=5
        )
    
    def _create_perf_metric(self, label: str, value: str, color: ft.Colors) -> ft.Container:
        """Create a performance metric display"""
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=10, color=ft.Colors.GREY_600, text_align=ft.TextAlign.CENTER),
                ft.Text(
                    value, 
                    size=12, 
                    weight=ft.FontWeight.BOLD, 
                    color=color,
                    text_align=ft.TextAlign.CENTER
                )
            ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=110,
            padding=ft.padding.all(8),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200),
            border_radius=5
        )
    
    def _create_rubric_scores_section(self, result: StudentResult) -> ft.Container:
        """Create rubric scores section"""
        if not result.rubric_scores:
            return ft.Container(
                content=ft.Text("No rubric scores available", color=ft.Colors.GREY_600),
                padding=ft.padding.all(15)
            )
        
        rubric_items = []
        for criterion, score in result.rubric_scores.items():
            rubric_items.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(
                            criterion,
                            size=12,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_800,
                            width=200
                        ),
                        ft.Container(
                            content=ft.Text(
                                f"{score:.1f}",
                                size=12,
                                weight=ft.FontWeight.BOLD,
                                color=self._get_score_color(score),
                                text_align=ft.TextAlign.CENTER
                            ),
                            width=60,
                            padding=ft.padding.all(5),
                            bgcolor=ft.Colors.WHITE,
                            border=ft.border.all(1, ft.Colors.GREY_300),
                            border_radius=3
                        ),
                        ft.Container(
                            content=ft.LinearProgressIndicator(
                                value=score / 100,
                                color=self._get_score_color(score),
                                bgcolor=ft.Colors.GREY_200
                            ),
                            width=150,
                            height=20,
                            alignment=ft.alignment.center
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.symmetric(vertical=5)
                )
            )
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "📋 Rubric Scores",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PURPLE_800
                ),
                ft.Container(height=10),
                ft.Column(rubric_items, spacing=5)
            ]),
            padding=ft.padding.all(15),
            border=ft.border.all(1, ft.Colors.PURPLE_200),
            border_radius=8,
            bgcolor=ft.Colors.PURPLE_50
        )
    
    def _create_github_section(self, result: StudentResult) -> ft.Container:
        """Create GitHub repository section"""
        if not result.github_repo:
            github_content = ft.Row([
                ft.Icon(ft.Icons.INFO, color=ft.Colors.GREY_500, size=16),
                ft.Text("No GitHub repository linked", color=ft.Colors.GREY_600, size=12)
            ])
        else:
            github_content = ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.CODE, color=ft.Colors.GREY_700, size=16),
                    ft.Text("Repository:", color=ft.Colors.GREY_700, size=12, weight=ft.FontWeight.BOLD)
                ]),
                ft.Container(height=5),
                ft.Row([
                    ft.Text(
                        result.github_repo,
                        size=11,
                        color=ft.Colors.BLUE_600,
                        selectable=True
                    ),
                    ft.IconButton(
                        icon=ft.Icons.OPEN_IN_NEW,
                        icon_size=16,
                        tooltip="Open repository",
                        on_click=lambda e: self._open_github_repo(result.github_repo)
                    ),
                    ft.IconButton(
                        icon=ft.Icons.COPY,
                        icon_size=16,
                        tooltip="Copy URL",
                        on_click=lambda e: self._copy_github_url(result.github_repo)
                    )
                ])
            ])
        
        return ft.Container(
            content=ft.Column([
                ft.Text(
                    "🔗 GitHub Repository",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_800
                ),
                ft.Container(height=10),
                github_content
            ]),
            padding=ft.padding.all(15),
            border=ft.border.all(1, ft.Colors.GREY_300),
            border_radius=8,
            bgcolor=ft.Colors.GREY_50
        )
    
    def _get_score_color(self, score: float) -> ft.Colors:
        """Get color based on score value"""
        if score >= 90:
            return ft.Colors.GREEN_600
        elif score >= 80:
            return ft.Colors.BLUE_600
        elif score >= 70:
            return ft.Colors.ORANGE_500
        elif score >= 60:
            return ft.Colors.ORANGE_700
        else:
            return ft.Colors.RED_600
    
    def _export_individual_result(self, result: StudentResult, format_type: str):
        """Export individual student result"""
        if format_type == "json":
            # Create JSON export
            export_data = {
                "student_id": result.student_id,
                "student_name": result.student_name,
                "total_score": result.total_score,
                "max_score": result.max_score,
                "percentage": result.percentage,
                "grade": result.grade,
                "feedback": result.feedback,
                "rubric_scores": result.rubric_scores,
                "token_usage": result.token_usage,
                "cost": result.cost,
                "github_repo": result.github_repo,
                "processing_time": result.processing_time,
                "status": result.status,
                "export_timestamp": datetime.now().isoformat()
            }
            
            # In a real implementation, this would save to file
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"JSON export for {result.student_name} ready! (Feature implementation in Task 3.1.3)"),
                    action="OK"
                )
            )
        else:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"PDF export for {result.student_name} - Feature coming in Task 3.1.3!"),
                    action="OK"
                )
            )
    
    def _copy_student_details(self, result: StudentResult):
        """Copy student details to clipboard"""
        details_text = f"""Student Details: {result.student_name}
ID: {result.student_id}
Total Score: {result.total_score:.1f}% ({result.grade})
Status: {result.status}
Cost: ${result.cost:.3f}
Tokens Used: {result.token_usage:,}
Processing Time: {result.processing_time:.1f}s
GitHub: {result.github_repo or 'Not available'}

Rubric Scores:
{chr(10).join([f"  {criterion}: {score:.1f}" for criterion, score in (result.rubric_scores or {}).items()])}

Feedback:
{result.feedback or 'No feedback available'}"""
        
        # In a real implementation, this would copy to clipboard
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("Student details copied to clipboard!"),
                action="OK"
            )
        )
    
    def _open_github_repo(self, repo_url: str):
        """Open GitHub repository in browser"""
        # In a real implementation, this would open the URL
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(f"Would open: {repo_url}"),
                action="OK"
            )
        )
    
    def _copy_github_url(self, repo_url: str):
        """Copy GitHub URL to clipboard"""
        # In a real implementation, this would copy to clipboard
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text("GitHub URL copied to clipboard!"),
                action="OK"
            )
        )
    
    def _close_dialog(self, dialog: ft.AlertDialog):
        """Close the dialog"""
        dialog.open = False
        self.page.update()
    
    def _on_back_clicked(self, e):
        """Handle back button click"""
        if self.on_back:
            self.on_back()


def main():
    """Test the results page"""
    def test_app(page: ft.Page):
        page.title = "Results Page Test"
        page.window.width = 1200
        page.window.height = 900
        
        # Mock results data
        mock_results = {
            'total_students': 25,
            'success': True
        }
        
        def on_back():
            print("Back to previous page")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text("Would navigate back to processing page"),
                    action="OK"
                )
            )
        
        def on_export(format_type):
            print(f"Export to {format_type}")
            page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(f"Would export results to {format_type.upper()}"),
                    action="OK"
                )
            )
        
        results_page = ResultsPage(
            page,
            mock_results,
            on_back,
            on_export
        )
        
        page.add(results_page.build())
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()