"""
Advanced Progress Bar Components

Provides detailed progress tracking components including individual student progress,
cost tracking, time estimation, and activity monitoring for the grading process.
"""

import flet as ft
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class StudentProgressInfo:
    """Information about individual student progress"""
    student_id: str
    status: str  # 'pending', 'processing', 'completed', 'error'
    score: Optional[float] = None
    cost: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None


class AdvancedProgressBar:
    """Advanced progress bar with detailed tracking capabilities"""
    
    def __init__(self, page: ft.Page, width: int = 600):
        """Initialize the advanced progress bar
        
        Args:
            page: Flet page object
            width: Width of the progress bar component
        """
        self.page = page
        self.width = width
        
        # Progress state
        self.total_students = 0
        self.completed_students = 0
        self.failed_students = 0
        self.current_student = None
        self.overall_progress = 0.0
        
        # Student tracking
        self.student_progress: Dict[str, StudentProgressInfo] = {}
        self.processing_order: List[str] = []
        
        # Time estimation
        self.start_time: Optional[datetime] = None
        self.estimated_completion: Optional[datetime] = None
        self.avg_time_per_student = 0.0
        
        # UI components
        self.main_progress_bar = None
        self.progress_text = None
        self.time_remaining_text = None
        self.throughput_text = None
        
    def build(self) -> ft.Control:
        """Build and return the advanced progress bar UI"""
        
        # Main progress bar
        self.main_progress_bar = ft.ProgressBar(
            width=self.width - 40,
            height=12,
            value=0,
            color=ft.Colors.GREEN_600,
            bgcolor=ft.Colors.GREY_300,
            border_radius=6
        )
        
        # Progress text
        self.progress_text = ft.Text(
            "0 / 0 students (0%)",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.GREEN_800,
            text_align=ft.TextAlign.CENTER
        )
        
        # Time remaining text
        self.time_remaining_text = ft.Text(
            "Time remaining: Calculating...",
            size=12,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER
        )
        
        # Throughput text
        self.throughput_text = ft.Text(
            "Processing rate: -- students/min",
            size=11,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER
        )
        
        # Progress breakdown
        progress_breakdown = ft.Row([
            ft.Column([
                ft.Text("✅", size=16),
                ft.Text("Completed", size=10, weight=ft.FontWeight.BOLD),
                ft.Text("0", size=12, color=ft.Colors.GREEN_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            
            ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
            
            ft.Column([
                ft.Text("🔄", size=16),
                ft.Text("Processing", size=10, weight=ft.FontWeight.BOLD),
                ft.Text("0", size=12, color=ft.Colors.BLUE_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            
            ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
            
            ft.Column([
                ft.Text("⏳", size=16),
                ft.Text("Pending", size=10, weight=ft.FontWeight.BOLD),
                ft.Text("0", size=12, color=ft.Colors.GREY_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2),
            
            ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
            
            ft.Column([
                ft.Text("❌", size=16),
                ft.Text("Failed", size=10, weight=ft.FontWeight.BOLD),
                ft.Text("0", size=12, color=ft.Colors.RED_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2)
        ], alignment=ft.MainAxisAlignment.SPACE_AROUND)
        
        # Store references for updates
        self.breakdown_refs = {
            'completed': progress_breakdown.controls[0].controls[2],
            'processing': progress_breakdown.controls[2].controls[2],
            'pending': progress_breakdown.controls[4].controls[2],
            'failed': progress_breakdown.controls[6].controls[2]
        }
        
        return ft.Container(
            content=ft.Column([
                self.progress_text,
                ft.Container(height=8),
                self.main_progress_bar,
                ft.Container(height=12),
                progress_breakdown,
                ft.Container(height=8),
                self.time_remaining_text,
                self.throughput_text
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=5),
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.GREEN_200),
            border_radius=10,
            bgcolor=ft.Colors.GREEN_50,
            width=self.width
        )
    
    def start_processing(self, total_students: int, student_ids: List[str] = None):
        """Start progress tracking
        
        Args:
            total_students: Total number of students to process
            student_ids: Optional list of student IDs for detailed tracking
        """
        self.total_students = total_students
        self.completed_students = 0
        self.failed_students = 0
        self.start_time = datetime.now()
        self.overall_progress = 0.0
        
        # Initialize student tracking
        if student_ids:
            self.processing_order = student_ids.copy()
            for student_id in student_ids:
                self.student_progress[student_id] = StudentProgressInfo(
                    student_id=student_id,
                    status='pending'
                )
        else:
            # Generate generic student IDs
            self.processing_order = [f"student_{i+1}" for i in range(total_students)]
            for student_id in self.processing_order:
                self.student_progress[student_id] = StudentProgressInfo(
                    student_id=student_id,
                    status='pending'
                )
        
        self._update_display()
    
    def update_student_progress(
        self, 
        student_id: str, 
        status: str, 
        score: float = None, 
        cost: float = 0.0,
        error_message: str = None
    ):
        """Update progress for a specific student
        
        Args:
            student_id: Student identifier
            status: Current status ('processing', 'completed', 'error')
            score: Grade score if completed
            cost: Processing cost for this student
            error_message: Error message if failed
        """
        if student_id not in self.student_progress:
            # Add new student if not already tracked
            self.student_progress[student_id] = StudentProgressInfo(
                student_id=student_id,
                status='pending'
            )
            if student_id not in self.processing_order:
                self.processing_order.append(student_id)
                self.total_students = len(self.processing_order)
        
        student_info = self.student_progress[student_id]
        old_status = student_info.status
        
        # Update student info
        student_info.status = status
        if score is not None:
            student_info.score = score
        student_info.cost += cost
        if error_message:
            student_info.error_message = error_message
        
        # Update timestamps
        if status == 'processing' and old_status == 'pending':
            student_info.start_time = datetime.now()
            self.current_student = student_id
        elif status in ['completed', 'error'] and student_info.start_time:
            student_info.end_time = datetime.now()
            
            # Update counters
            if status == 'completed':
                if old_status != 'completed':
                    self.completed_students += 1
            elif status == 'error':
                if old_status != 'error':
                    self.failed_students += 1
        
        # Calculate overall progress
        self.overall_progress = (self.completed_students + self.failed_students) / self.total_students
        
        # Update time estimates
        self._update_time_estimates()
        
        # Update display
        self._update_display()
    
    def _update_time_estimates(self):
        """Update time estimation calculations"""
        if not self.start_time or self.completed_students == 0:
            return
        
        # Calculate average time per completed student
        completed_times = []
        for student_info in self.student_progress.values():
            if (student_info.status in ['completed', 'error'] and 
                student_info.start_time and student_info.end_time):
                duration = (student_info.end_time - student_info.start_time).total_seconds()
                completed_times.append(duration)
        
        if completed_times:
            self.avg_time_per_student = sum(completed_times) / len(completed_times)
            
            # Estimate remaining time
            remaining_students = self.total_students - self.completed_students - self.failed_students
            estimated_remaining_seconds = remaining_students * self.avg_time_per_student
            self.estimated_completion = datetime.now() + timedelta(seconds=estimated_remaining_seconds)
    
    def _update_display(self):
        """Update the progress display"""
        if not self.main_progress_bar:
            return
        
        # Update main progress bar
        self.main_progress_bar.value = self.overall_progress
        
        # Update progress text
        completed_total = self.completed_students + self.failed_students
        percentage = int(self.overall_progress * 100)
        self.progress_text.value = f"{completed_total} / {self.total_students} students ({percentage}%)"
        
        # Update breakdown counters
        processing_count = len([s for s in self.student_progress.values() if s.status == 'processing'])
        pending_count = len([s for s in self.student_progress.values() if s.status == 'pending'])
        
        self.breakdown_refs['completed'].value = str(self.completed_students)
        self.breakdown_refs['processing'].value = str(processing_count)
        self.breakdown_refs['pending'].value = str(pending_count)
        self.breakdown_refs['failed'].value = str(self.failed_students)
        
        # Update time display
        if self.estimated_completion and self.overall_progress < 1.0:
            remaining = self.estimated_completion - datetime.now()
            if remaining.total_seconds() > 0:
                hours, remainder = divmod(int(remaining.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    time_str = f"{hours}h {minutes}m"
                elif minutes > 0:
                    time_str = f"{minutes}m {seconds}s"
                else:
                    time_str = f"{seconds}s"
                self.time_remaining_text.value = f"Time remaining: ~{time_str}"
            else:
                self.time_remaining_text.value = "Time remaining: Nearly complete"
        else:
            self.time_remaining_text.value = "Time remaining: Calculating..."
        
        # Update throughput
        if self.start_time and self.completed_students > 0:
            elapsed = (datetime.now() - self.start_time).total_seconds() / 60  # minutes
            if elapsed > 0:
                rate = self.completed_students / elapsed
                self.throughput_text.value = f"Processing rate: {rate:.1f} students/min"
        
        self.page.update()
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of current progress"""
        return {
            'total_students': self.total_students,
            'completed': self.completed_students,
            'failed': self.failed_students,
            'processing': len([s for s in self.student_progress.values() if s.status == 'processing']),
            'pending': len([s for s in self.student_progress.values() if s.status == 'pending']),
            'overall_progress': self.overall_progress,
            'avg_time_per_student': self.avg_time_per_student,
            'estimated_completion': self.estimated_completion,
            'total_cost': sum(s.cost for s in self.student_progress.values()),
            'avg_score': self._calculate_avg_score()
        }
    
    def _calculate_avg_score(self) -> Optional[float]:
        """Calculate average score for completed students"""
        completed_scores = [
            s.score for s in self.student_progress.values() 
            if s.status == 'completed' and s.score is not None
        ]
        return sum(completed_scores) / len(completed_scores) if completed_scores else None


class IndividualStudentTracker:
    """Component for tracking individual student progress"""
    
    def __init__(self, page: ft.Page, max_visible_students: int = 10):
        """Initialize the individual student tracker
        
        Args:
            page: Flet page object
            max_visible_students: Maximum number of students to show in the list
        """
        self.page = page
        self.max_visible_students = max_visible_students
        
        # Student tracking
        self.students: Dict[str, StudentProgressInfo] = {}
        self.visible_students: List[str] = []
        
        # UI components
        self.student_list = None
        
    def build(self) -> ft.Control:
        """Build and return the student tracker UI"""
        
        # Student list
        self.student_list = ft.ListView(
            height=300,
            spacing=5,
            padding=ft.padding.all(10)
        )
        
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PEOPLE, color=ft.Colors.BLUE_600, size=20),
                    ft.Text(
                        "Individual Student Progress",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_800
                    )
                ], spacing=8),
                
                ft.Divider(color=ft.Colors.BLUE_300),
                
                self.student_list
            ], spacing=8),
            padding=ft.padding.all(15),
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=10,
            bgcolor=ft.Colors.BLUE_50,
            width=400
        )
    
    def update_student(self, student_id: str, status: str, score: float = None, cost: float = 0.0):
        """Update a student's progress
        
        Args:
            student_id: Student identifier
            status: Current status
            score: Grade score if available
            cost: Processing cost
        """
        # Update or create student info
        if student_id not in self.students:
            self.students[student_id] = StudentProgressInfo(
                student_id=student_id,
                status='pending'
            )
        
        student_info = self.students[student_id]
        student_info.status = status
        if score is not None:
            student_info.score = score
        student_info.cost += cost
        
        # Update timestamps
        if status == 'processing':
            student_info.start_time = datetime.now()
        elif status in ['completed', 'error']:
            student_info.end_time = datetime.now()
        
        # Update visible students list
        self._update_visible_students(student_id)
        
        # Update display
        self._update_display()
    
    def _update_visible_students(self, current_student: str):
        """Update the list of visible students"""
        # Add current student if not already visible
        if current_student not in self.visible_students:
            self.visible_students.append(current_student)
        
        # Keep only the most recent students
        if len(self.visible_students) > self.max_visible_students:
            # Remove oldest students, but keep currently processing ones
            processing_students = [
                s for s in self.visible_students 
                if s in self.students and self.students[s].status == 'processing'
            ]
            recent_students = self.visible_students[-self.max_visible_students:]
            
            # Combine processing and recent, removing duplicates
            self.visible_students = list(dict.fromkeys(processing_students + recent_students))
    
    def _update_display(self):
        """Update the student list display"""
        if not self.student_list:
            return
        
        # Clear existing items
        self.student_list.controls.clear()
        
        # Add student items
        for student_id in self.visible_students:
            if student_id in self.students:
                student_info = self.students[student_id]
                self.student_list.controls.append(self._create_student_item(student_info))
        
        self.page.update()
    
    def _create_student_item(self, student_info: StudentProgressInfo) -> ft.Control:
        """Create a display item for a student"""
        
        # Status icon and color
        if student_info.status == 'completed':
            icon = ft.Icons.CHECK_CIRCLE
            color = ft.Colors.GREEN_600
            status_text = f"✅ Complete"
            if student_info.score is not None:
                status_text += f" ({student_info.score:.1f})"
        elif student_info.status == 'processing':
            icon = ft.Icons.SYNC
            color = ft.Colors.BLUE_600
            status_text = "🔄 Processing..."
        elif student_info.status == 'error':
            icon = ft.Icons.ERROR
            color = ft.Colors.RED_600
            status_text = "❌ Error"
        else:  # pending
            icon = ft.Icons.SCHEDULE
            color = ft.Colors.GREY_600
            status_text = "⏳ Pending"
        
        # Time info
        time_info = ""
        if student_info.start_time and student_info.end_time:
            duration = student_info.end_time - student_info.start_time
            seconds = int(duration.total_seconds())
            if seconds < 60:
                time_info = f"{seconds}s"
            else:
                minutes = seconds // 60
                time_info = f"{minutes}m {seconds % 60}s"
        elif student_info.start_time:
            duration = datetime.now() - student_info.start_time
            seconds = int(duration.total_seconds())
            if seconds < 60:
                time_info = f"{seconds}s elapsed"
            else:
                minutes = seconds // 60
                time_info = f"{minutes}m {seconds % 60}s elapsed"
        
        # Cost info
        cost_text = f"${student_info.cost:.3f}" if student_info.cost > 0 else ""
        
        return ft.Container(
            content=ft.Row([
                ft.Icon(icon, color=color, size=16),
                ft.Column([
                    ft.Text(
                        student_info.student_id,
                        size=12,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLACK87
                    ),
                    ft.Text(
                        status_text,
                        size=10,
                        color=color
                    )
                ], spacing=2, expand=True),
                ft.Column([
                    ft.Text(time_info, size=10, color=ft.Colors.GREY_600),
                    ft.Text(cost_text, size=10, color=ft.Colors.ORANGE_600)
                ], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.symmetric(horizontal=10, vertical=8),
            border_radius=5,
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, ft.Colors.GREY_200)
        )


def main():
    """Test the advanced progress bar components"""
    def test_app(page: ft.Page):
        page.title = "Advanced Progress Bar Test"
        page.window.width = 1000
        page.window.height = 800
        
        # Create components
        progress_bar = AdvancedProgressBar(page, width=600)
        student_tracker = IndividualStudentTracker(page)
        
        # Test data
        student_ids = [f"student_{i:03d}" for i in range(1, 26)]  # 25 students
        
        # Start processing
        progress_bar.start_processing(len(student_ids), student_ids)
        
        # Simulate progress updates
        import threading
        import time
        import random
        
        def simulate_progress():
            for i, student_id in enumerate(student_ids):
                time.sleep(0.5)  # Simulate processing time
                
                # Update to processing
                progress_bar.update_student_progress(student_id, 'processing')
                student_tracker.update_student(student_id, 'processing')
                
                time.sleep(random.uniform(0.5, 2.0))  # Variable processing time
                
                # Complete or fail
                if random.random() < 0.9:  # 90% success rate
                    score = random.uniform(70, 100)
                    cost = random.uniform(0.05, 0.15)
                    progress_bar.update_student_progress(student_id, 'completed', score, cost)
                    student_tracker.update_student(student_id, 'completed', score, cost)
                else:
                    progress_bar.update_student_progress(student_id, 'error', error_message="Processing failed")
                    student_tracker.update_student(student_id, 'error')
        
        # Start simulation
        threading.Thread(target=simulate_progress, daemon=True).start()
        
        # Layout
        page.add(
            ft.Column([
                ft.Text("Advanced Progress Tracking Test", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                progress_bar.build(),
                
                ft.Container(height=20),
                
                student_tracker.build(),
                
                ft.Container(height=20),
                ft.ElevatedButton(
                    "Get Progress Summary",
                    on_click=lambda _: print(progress_bar.get_progress_summary())
                )
            ],
            spacing=10,
            expand=True,
            scroll=ft.ScrollMode.AUTO
            )
        )
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()