"""
Cost Estimator Component

Provides real-time cost estimation functionality for the GUI application.
Integrates with the GraderService to estimate grading costs before processing.
"""

import flet as ft
import asyncio
import sys
from pathlib import Path
from typing import Callable, Optional, Dict, Any

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.services.grader_service import GraderService


class CostEstimator:
    """Cost estimation component
    
    Provides background cost estimation with loading states and
    detailed breakdown of estimated costs by provider.
    """
    
    def __init__(
        self, 
        page: ft.Page,
        on_estimate_complete: Callable[[Dict[str, Any]], None] = None,
        on_estimate_error: Callable[[str], None] = None
    ):
        """Initialize the cost estimator
        
        Args:
            page: Flet page object
            on_estimate_complete: Callback when estimation completes
            on_estimate_error: Callback when estimation fails
        """
        self.page = page
        self.on_estimate_complete = on_estimate_complete
        self.on_estimate_error = on_estimate_error
        
        # Services
        self.grader_service = GraderService()
        
        # State
        self.is_estimating = False
        self.last_estimate = None
        self.last_estimate_params = None
        
        # UI components
        self.cost_card = None
        self.loading_indicator = None
        self.estimate_button = None
        self.auto_estimate_switch = None
        
        # Auto-estimation settings
        self.auto_estimate_enabled = True
        self.estimation_task = None
        
    def build(self) -> ft.Control:
        """Build and return the cost estimator UI"""
        
        # Loading indicator
        self.loading_indicator = ft.Container(
            content=ft.Column([
                ft.ProgressRing(width=30, height=30, stroke_width=3),
                ft.Text("Estimating costs...", size=12, color=ft.Colors.BLUE_600)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            visible=False,
            padding=ft.padding.all(20)
        )
        
        # Manual estimate button
        self.estimate_button = ft.ElevatedButton(
            text="Estimate Costs",
            icon=ft.Icons.CALCULATE,
            style=ft.ButtonStyle(
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.BLUE_600
            ),
            on_click=self._on_estimate_clicked
        )
        
        # Auto-estimate toggle
        self.auto_estimate_switch = ft.Switch(
            label="Auto-estimate when configuration changes",
            value=self.auto_estimate_enabled,
            on_change=self._on_auto_estimate_changed
        )
        
        # Initial cost card (empty state)
        self._build_cost_card()
        
        # Main container
        return ft.Column([
            # Header
            ft.Row([
                ft.Icon(ft.Icons.ATTACH_MONEY, color=ft.Colors.GREEN_600, size=24),
                ft.Text(
                    "Cost Estimation",
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_800
                )
            ], spacing=10),
            
            ft.Divider(color=ft.Colors.GREEN_300),
            
            # Controls
            ft.Row([
                self.estimate_button,
                ft.Container(width=20),
                self.auto_estimate_switch
            ], alignment=ft.MainAxisAlignment.START),
            
            ft.Container(height=15),
            
            # Cost display
            self.loading_indicator,
            self.cost_card
        ], spacing=10, width=700)
    
    def _build_cost_card(self, estimate_data: Dict[str, Any] = None):
        """Build or update the cost display card"""
        
        if estimate_data:
            # Show detailed cost breakdown
            content = ft.Column([
                # Summary header
                ft.Row([
                    ft.Icon(ft.Icons.RECEIPT, color=ft.Colors.GREEN_600, size=20),
                    ft.Text(
                        f"Estimated Total: ${estimate_data.get('total_cost', 0):.2f}",
                        size=16,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.GREEN_800
                    )
                ], spacing=8),
                
                ft.Divider(color=ft.Colors.GREEN_300),
                
                # Submission details
                ft.Row([
                    ft.Column([
                        ft.Text("📊 Submissions", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(str(estimate_data.get('total_submissions', 0)), size=14)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    
                    ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                    
                    ft.Column([
                        ft.Text("🔢 Est. Tokens", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(f"{estimate_data.get('estimated_tokens', 0):,}", size=14)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    
                    ft.VerticalDivider(width=1, color=ft.Colors.GREY_300),
                    
                    ft.Column([
                        ft.Text("💵 Per Submission", size=12, weight=ft.FontWeight.BOLD),
                        ft.Text(f"${estimate_data.get('per_submission_cost', 0):.3f}", size=14)
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                ], alignment=ft.MainAxisAlignment.SPACE_AROUND),
                
                ft.Container(height=10),
                
                # Provider breakdown
                ft.Text("Provider Breakdown:", size=12, weight=ft.FontWeight.BOLD),
                ft.Column([
                    ft.Row([
                        ft.Icon(ft.Icons.SMART_TOY, color=ft.Colors.BLUE_600, size=16),
                        ft.Text("OpenAI GPT-4:", size=11, weight=ft.FontWeight.BOLD),
                        ft.Text(f"${estimate_data.get('openai_cost', 0):.2f}", size=11, color=ft.Colors.BLUE_700)
                    ], spacing=5),
                    ft.Row([
                        ft.Icon(ft.Icons.PSYCHOLOGY, color=ft.Colors.PURPLE_600, size=16),
                        ft.Text("Anthropic Claude:", size=11, weight=ft.FontWeight.BOLD),
                        ft.Text(f"${estimate_data.get('anthropic_cost', 0):.2f}", size=11, color=ft.Colors.PURPLE_700)
                    ], spacing=5)
                ], spacing=5),
                
                ft.Container(height=10),
                
                # Cost analysis
                self._get_cost_analysis(estimate_data)
            ], spacing=8)
            
            bgcolor = ft.Colors.GREEN_50
            border_color = ft.Colors.GREEN_200
            
        else:
            # Empty state
            content = ft.Column([
                ft.Icon(ft.Icons.RECEIPT_LONG, color=ft.Colors.GREY_400, size=48),
                ft.Text(
                    "Cost Estimation",
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREY_600
                ),
                ft.Text(
                    "Click 'Estimate Costs' or enable auto-estimation to see pricing details",
                    size=12,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
            
            bgcolor = ft.Colors.GREY_50
            border_color = ft.Colors.GREY_200
        
        self.cost_card = ft.Container(
            content=content,
            padding=ft.padding.all(20),
            border=ft.border.all(1, border_color),
            border_radius=10,
            bgcolor=bgcolor,
            width=700
        )
    
    def _get_cost_analysis(self, estimate_data: Dict[str, Any]) -> ft.Control:
        """Generate cost analysis and recommendations"""
        total_cost = estimate_data.get('total_cost', 0)
        submissions = estimate_data.get('total_submissions', 0)
        
        if total_cost == 0:
            return ft.Container()
        
        # Cost level analysis
        if total_cost < 1.0:
            icon = ft.Icons.SAVINGS
            color = ft.Colors.GREEN
            level = "Low Cost"
            message = "Very affordable - suitable for small to medium assignments"
        elif total_cost < 5.0:
            icon = ft.Icons.PAYMENT
            color = ft.Colors.BLUE
            level = "Moderate Cost"
            message = "Reasonable cost for comprehensive grading"
        elif total_cost < 20.0:
            icon = ft.Icons.CREDIT_CARD
            color = ft.Colors.ORANGE
            level = "Higher Cost"
            message = "Consider if budget allows - large assignment or many submissions"
        else:
            icon = ft.Icons.WARNING
            color = ft.Colors.RED
            level = "High Cost"
            message = "Significant expense - review settings and consider cost limits"
        
        # Recommendations
        recommendations = []
        
        if total_cost > 10.0:
            recommendations.append("💡 Consider setting a cost limit to prevent overruns")
        
        if submissions > 50 and estimate_data.get('per_submission_cost', 0) > 0.20:
            recommendations.append("💡 High per-submission cost - check assignment complexity")
        
        if estimate_data.get('estimated_tokens', 0) > 100000:
            recommendations.append("💡 High token usage - consider shorter prompts or simpler rubrics")
        
        analysis_content = ft.Column([
            ft.Row([
                ft.Icon(icon, color=color, size=16),
                ft.Text(level, size=11, weight=ft.FontWeight.BOLD, color=color),
                ft.Text(message, size=11, color=ft.Colors.GREY_700)
            ], spacing=5)
        ], spacing=5)
        
        if recommendations:
            analysis_content.controls.extend([
                ft.Container(height=5),
                ft.Column([
                    ft.Text(rec, size=10, color=ft.Colors.BLUE_700)
                    for rec in recommendations
                ], spacing=3)
            ])
        
        return ft.Container(
            content=analysis_content,
            padding=ft.padding.all(10),
            border=ft.border.all(1, ft.Colors.BLUE_200),
            border_radius=5,
            bgcolor=ft.Colors.BLUE_50
        )
    
    async def estimate_cost(
        self, 
        submissions_folder: str, 
        assignment_name: str,
        enable_github: bool = False,
        roster_file: str = None
    ):
        """Run cost estimation asynchronously
        
        Args:
            submissions_folder: Path to submissions folder
            assignment_name: Name of assignment
            enable_github: Whether GitHub integration is enabled
            roster_file: Optional roster file path
        """
        if self.is_estimating:
            return
        
        # Check if we need to re-estimate
        current_params = {
            'submissions_folder': submissions_folder,
            'assignment_name': assignment_name,
            'enable_github': enable_github,
            'roster_file': roster_file
        }
        
        if self.last_estimate_params == current_params and self.last_estimate:
            # Use cached estimate
            self._update_cost_display(self.last_estimate)
            return
        
        self.is_estimating = True
        self.loading_indicator.visible = True
        self.cost_card.visible = False
        self.estimate_button.disabled = True
        self.page.update()
        
        try:
            # Run estimation in background
            estimate = await asyncio.get_event_loop().run_in_executor(
                None,
                self._run_cost_estimation,
                submissions_folder,
                assignment_name,
                enable_github,
                roster_file
            )
            
            # Cache the estimate
            self.last_estimate = estimate
            self.last_estimate_params = current_params
            
            # Update UI
            self._update_cost_display(estimate)
            
            # Notify callback
            if self.on_estimate_complete:
                self.on_estimate_complete(estimate)
                
        except Exception as e:
            error_msg = f"Cost estimation failed: {str(e)}"
            self._show_estimation_error(error_msg)
            
            if self.on_estimate_error:
                self.on_estimate_error(error_msg)
        
        finally:
            self.is_estimating = False
            self.loading_indicator.visible = False
            self.cost_card.visible = True
            self.estimate_button.disabled = False
            self.page.update()
    
    def _run_cost_estimation(
        self, 
        submissions_folder: str, 
        assignment_name: str,
        enable_github: bool,
        roster_file: str
    ) -> Dict[str, Any]:
        """Run the actual cost estimation (synchronous)"""
        return self.grader_service.estimate_cost(
            submissions_folder=submissions_folder,
            assignment_name=assignment_name,
            enable_github=enable_github,
            roster_file=roster_file
        )
    
    def _update_cost_display(self, estimate_data: Dict[str, Any]):
        """Update the cost display with new estimate data"""
        self._build_cost_card(estimate_data)
        self.page.update()
    
    def _show_estimation_error(self, error_msg: str):
        """Show estimation error in the cost card"""
        error_content = ft.Column([
            ft.Icon(ft.Icons.ERROR, color=ft.Colors.RED_600, size=48),
            ft.Text(
                "Estimation Failed",
                size=16,
                weight=ft.FontWeight.BOLD,
                color=ft.Colors.RED_800
            ),
            ft.Text(
                error_msg,
                size=12,
                color=ft.Colors.RED_700,
                text_align=ft.TextAlign.CENTER
            ),
            ft.Container(height=10),
            ft.ElevatedButton(
                text="Retry",
                icon=ft.Icons.REFRESH,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.RED_600
                ),
                on_click=self._on_estimate_clicked
            )
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10)
        
        self.cost_card = ft.Container(
            content=error_content,
            padding=ft.padding.all(20),
            border=ft.border.all(1, ft.Colors.RED_200),
            border_radius=10,
            bgcolor=ft.Colors.RED_50,
            width=700
        )
    
    def _on_estimate_clicked(self, e):
        """Handle manual estimate button click"""
        # This will be called by the parent component with current parameters
        if hasattr(self, '_manual_estimate_callback') and self._manual_estimate_callback:
            self._manual_estimate_callback()
    
    def _on_auto_estimate_changed(self, e):
        """Handle auto-estimate toggle change"""
        self.auto_estimate_enabled = e.control.value
        
        if not self.auto_estimate_enabled and self.estimation_task:
            self.estimation_task.cancel()
            self.estimation_task = None
    
    def set_manual_estimate_callback(self, callback: Callable[[], None]):
        """Set callback for manual estimation trigger"""
        self._manual_estimate_callback = callback
    
    def trigger_auto_estimate(
        self, 
        submissions_folder: str, 
        assignment_name: str,
        enable_github: bool = False,
        roster_file: str = None,
        delay_seconds: float = 2.0
    ):
        """Trigger auto-estimation with debouncing
        
        Args:
            submissions_folder: Path to submissions folder
            assignment_name: Name of assignment
            enable_github: Whether GitHub integration is enabled
            roster_file: Optional roster file path
            delay_seconds: Delay before estimation to debounce rapid changes
        """
        if not self.auto_estimate_enabled:
            return
        
        # Cancel existing task
        if self.estimation_task:
            self.estimation_task.cancel()
        
        # Schedule new estimation
        async def delayed_estimate():
            await asyncio.sleep(delay_seconds)
            await self.estimate_cost(submissions_folder, assignment_name, enable_github, roster_file)
        
        try:
            # Try to create task in current event loop
            loop = asyncio.get_running_loop()
            self.estimation_task = loop.create_task(delayed_estimate())
        except RuntimeError:
            # No event loop running, schedule for later
            def schedule_when_ready():
                try:
                    loop = asyncio.get_running_loop()
                    self.estimation_task = loop.create_task(delayed_estimate())
                except RuntimeError:
                    # Still no loop, create a new one temporarily for this task
                    import threading
                    def run_in_thread():
                        asyncio.run(delayed_estimate())
                    threading.Thread(target=run_in_thread, daemon=True).start()
            
            # Use page timer to schedule when event loop is ready
            import threading
            timer = threading.Timer(0.1, schedule_when_ready)
            timer.start()
    
    def get_last_estimate(self) -> Optional[Dict[str, Any]]:
        """Get the last cost estimate"""
        return self.last_estimate
    
    def clear_estimate(self):
        """Clear the current estimate display"""
        self.last_estimate = None
        self.last_estimate_params = None
        self._build_cost_card()
        self.page.update()


def main():
    """Test the cost estimator component"""
    def test_app(page: ft.Page):
        page.title = "Cost Estimator Test"
        page.window.width = 800
        page.window.height = 700
        
        def on_estimate_complete(estimate):
            print(f"Estimation complete: {estimate}")
        
        def on_estimate_error(error):
            print(f"Estimation error: {error}")
        
        # Create cost estimator
        estimator = CostEstimator(page, on_estimate_complete, on_estimate_error)
        
        # Manual estimate trigger
        def trigger_estimate():
            asyncio.create_task(estimator.estimate_cost(
                submissions_folder="./test_submissions",
                assignment_name="weatherwise",
                enable_github=True
            ))
        
        estimator.set_manual_estimate_callback(trigger_estimate)
        
        # Test auto-estimation
        auto_estimate_button = ft.ElevatedButton(
            text="Test Auto-Estimate",
            on_click=lambda _: estimator.trigger_auto_estimate(
                "./test_submissions", "weatherwise", True
            )
        )
        
        # Layout
        page.add(
            ft.Column([
                ft.Text("Cost Estimator Test", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                
                estimator.build(),
                
                ft.Container(height=20),
                ft.Divider(),
                
                ft.Text("Test Controls:", size=16, weight=ft.FontWeight.BOLD),
                auto_estimate_button
            ],
            spacing=10,
            expand=True,
            scroll=ft.ScrollMode.AUTO
            )
        )
    
    ft.app(target=test_app)


if __name__ == "__main__":
    main()