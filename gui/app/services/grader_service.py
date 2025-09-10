"""
Grader Service for GUI Application

Provides grading functionality for the GUI, wrapping the existing CLI
grader functionality with progress tracking and background processing.
"""

import os
import sys
import subprocess
import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
import logging
import traceback

# Add CLI core to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CLI_CORE_DIR = PROJECT_ROOT / "cli" / "core"
CLI_GRADER_PATH = PROJECT_ROOT / "cli" / "grader"
sys.path.insert(0, str(CLI_CORE_DIR))


class GradingStatus(Enum):
    """Grading process status"""
    IDLE = "idle"
    PREPARING = "preparing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass
class ProgressUpdate:
    """Progress update information"""
    status: GradingStatus
    current_student: Optional[str] = None
    completed_count: int = 0
    total_count: int = 0
    current_operation: str = ""
    cost_used: float = 0.0
    cost_estimated: float = 0.0
    message: str = ""
    error: Optional[str] = None


@dataclass
class CostEstimate:
    """Cost estimation information"""
    total_submissions: int
    estimated_tokens: int
    openai_cost: float
    anthropic_cost: float
    total_cost: float
    per_submission_cost: float


@dataclass
class ErrorInfo:
    """Error information with context"""
    error_type: str
    error_message: str
    is_recoverable: bool
    suggested_action: str
    technical_details: str
    timestamp: str


@dataclass
class PartialResults:
    """Partial results for recovery"""
    completed_students: List[str]
    failed_students: List[str]
    total_cost: float
    partial_data: Dict[str, Any]
    save_timestamp: str


class GraderService:
    """GUI Grader Service
    
    Provides grading functionality for the GUI application,
    including progress tracking, cost estimation, and process management.
    """
    
    def __init__(self):
        """Initialize the grader service"""
        self.process: Optional[subprocess.Popen] = None
        self.progress_callback: Optional[Callable[[ProgressUpdate], None]] = None
        self.status = GradingStatus.IDLE
        self.is_running = False
        self.current_assignment = None
        self.current_config = None
        
        # Progress tracking
        self.completed_students = []
        self.total_students = 0
        self.current_student = None
        self.cost_used = 0.0
        self.cost_estimated = 0.0
        
        # Process management
        self._should_cancel = False
        self._is_paused = False
        self._pause_event = asyncio.Event()
        self._pause_event.set()  # Initially not paused
        self._cleanup_tasks = []
        self._temp_files = []
        
        # Log management
        self.log_buffer = []
        self.max_log_entries = 1000
        
        # Task management
        self._current_task = None
        self._task_timeout = 1800  # 30 minutes default timeout
        
        # Error handling and recovery
        self._retry_count = 0
        self._max_retries = 3
        self._partial_results_file = None
        self._error_log = []
        self._recovery_data = None
        
        # Setup logging
        self._setup_logging()
    
    def set_progress_callback(self, callback: Callable[[ProgressUpdate], None]):
        """Set callback function for progress updates
        
        Args:
            callback: Function to call with progress updates
        """
        self.progress_callback = callback
    
    def estimate_cost(self, submissions_folder: str, assignment_name: str, 
                     enable_github: bool = False, roster_file: str = None) -> CostEstimate:
        """Run dry-run cost estimation
        
        Args:
            submissions_folder: Path to submissions folder
            assignment_name: Name of assignment to grade
            enable_github: Whether to enable GitHub integration
            roster_file: Optional roster file for filtering
            
        Returns:
            Cost estimation details
        """
        try:
            # Build command for dry run
            cmd = [
                sys.executable,
                str(CLI_GRADER_PATH),
                "grade",
                submissions_folder,
                "--assignment", assignment_name,
                "--dry-run"
            ]
            
            if enable_github:
                cmd.append("--github")
            else:
                cmd.append("--no-github")
            
            if roster_file:
                # Note: Roster filtering happens in preprocessing, not grading
                # For cost estimation, we'll count all ZIP files
                pass
            
            # Run dry-run command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,  # 1 minute timeout for cost estimation
                cwd=PROJECT_ROOT
            )
            
            if result.returncode != 0:
                raise Exception(f"Dry run failed: {result.stderr}")
            
            # Parse output for cost information
            output = result.stdout
            return self._parse_cost_output(output)
            
        except subprocess.TimeoutExpired:
            raise Exception("Cost estimation timed out after 60 seconds")
        except Exception as e:
            raise Exception(f"Cost estimation failed: {str(e)}")
    
    async def run_grading(self, submissions_folder: str, assignment_name: str,
                         enable_github: bool = False, dry_run: bool = False,
                         roster_file: str = None, preprocessing: bool = False) -> Dict[str, Any]:
        """Execute grading process with progress tracking
        
        Args:
            submissions_folder: Path to submissions folder
            assignment_name: Name of assignment to grade
            enable_github: Whether to enable GitHub integration
            dry_run: Whether to run in dry-run mode
            roster_file: Optional roster file for filtering
            preprocessing: Whether to run preprocessing first
            
        Returns:
            Grading results summary
        """
        if self.is_running:
            raise Exception("Grading is already in progress")
        
        try:
            self.is_running = True
            self.status = GradingStatus.PREPARING
            self._should_cancel = False
            self._is_paused = False
            self.current_assignment = assignment_name
            
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.PREPARING,
                message="Preparing grading process..."
            ))
            
            # Build command
            if preprocessing:
                # Run complete workflow
                cmd = [
                    sys.executable,
                    str(CLI_GRADER_PATH),
                    "process-all",
                    submissions_folder,
                    "--assignment", assignment_name
                ]
                
                if roster_file:
                    cmd.extend(["--roster", roster_file])
            else:
                # Run grading only
                cmd = [
                    sys.executable,
                    str(CLI_GRADER_PATH),
                    "grade",
                    submissions_folder,
                    "--assignment", assignment_name
                ]
            
            if enable_github:
                cmd.append("--github")
            else:
                cmd.append("--no-github")
            
            if dry_run:
                cmd.append("--dry-run")
            
            # Start process
            self.status = GradingStatus.RUNNING
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.RUNNING,
                message="Starting grading process..."
            ))
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                cwd=PROJECT_ROOT
            )
            
            # Monitor process output with timeout and cancellation support
            self._current_task = asyncio.create_task(self._monitor_process_with_timeout())
            
            try:
                results = await self._current_task
            except asyncio.CancelledError:
                self.status = GradingStatus.CANCELLED
                self._emit_progress(ProgressUpdate(
                    status=GradingStatus.CANCELLED,
                    message="Grading cancelled by user"
                ))
                await self._cleanup_process()
                return {'success': False, 'error': 'Cancelled by user'}
            except asyncio.TimeoutError:
                self.status = GradingStatus.ERROR
                self._emit_progress(ProgressUpdate(
                    status=GradingStatus.ERROR,
                    message=f"Grading timed out after {self._task_timeout} seconds",
                    error="Timeout"
                ))
                await self._cleanup_process()
                return {'success': False, 'error': 'Operation timed out'}
            
            if self._should_cancel:
                self.status = GradingStatus.CANCELLED
                self._emit_progress(ProgressUpdate(
                    status=GradingStatus.CANCELLED,
                    message="Grading cancelled by user"
                ))
            else:
                self.status = GradingStatus.COMPLETED
                self._emit_progress(ProgressUpdate(
                    status=GradingStatus.COMPLETED,
                    message="Grading completed successfully"
                ))
            
            return results
            
        except Exception as e:
            self.status = GradingStatus.ERROR
            
            # Create comprehensive error info
            error_info = self._create_error_info(e, "Grading process failed")
            self._log_error(e, "Grading process")
            
            # Save partial results
            partial_file = self._save_partial_results()
            
            # Emit detailed error progress update
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.ERROR,
                error=error_info.error_message,
                message=f"Grading failed: {error_info.error_message}"
            ))
            
            # Return error result with recovery information
            return {
                'success': False,
                'error': error_info.error_message,
                'error_type': error_info.error_type,
                'is_recoverable': error_info.is_recoverable,
                'suggested_action': error_info.suggested_action,
                'partial_results_file': partial_file,
                'completed_students': len(self.completed_students),
                'total_students': self.total_students
            }
        finally:
            self.is_running = False
            if self.process:
                try:
                    self.process.terminate()
                except:
                    pass
                self.process = None
    
    async def run_grading_with_retry(
        self, 
        submissions_folder: str, 
        assignment_name: str,
        enable_github: bool = False, 
        dry_run: bool = False, 
        roster_file: str = None,
        preprocessing: bool = True
    ) -> Dict[str, Any]:
        """Run grading with automatic retry on recoverable errors"""
        
        # Wrapper function for retry mechanism
        async def _grading_operation():
            return await self.run_grading(
                submissions_folder=submissions_folder,
                assignment_name=assignment_name,
                enable_github=enable_github,
                dry_run=dry_run,
                roster_file=roster_file,
                preprocessing=preprocessing
            )
        
        try:
            return await self.retry_operation(_grading_operation)
        except Exception as e:
            # Final failure after all retries
            error_info = self._create_error_info(e, "All retry attempts failed")
            self._log_error(e, "Final retry failure")
            
            return {
                'success': False,
                'error': error_info.error_message,
                'error_type': error_info.error_type,
                'is_recoverable': error_info.is_recoverable,
                'suggested_action': error_info.suggested_action,
                'retry_attempts': self._retry_count,
                'partial_results_file': self._partial_results_file,
                'completed_students': len(self.completed_students),
                'total_students': self.total_students,
                'recovery_suggestions': self.get_recovery_suggestions()
            }
    
    def cancel_grading(self):
        """Cancel ongoing grading process with proper cleanup"""
        if not self.is_running:
            return
        
        self._should_cancel = True
        
        # Cancel the current task if it exists
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
        
        # Perform cleanup
        asyncio.create_task(self._cleanup_process())
        
        self.status = GradingStatus.CANCELLED
    
    def pause_grading(self):
        """Pause ongoing grading process"""
        if not self.is_running or self._is_paused:
            return
        
        self._is_paused = True
        self._pause_event.clear()  # Signal pause
        self.status = GradingStatus.PAUSED
        
        self._emit_progress(ProgressUpdate(
            status=GradingStatus.PAUSED,
            message="Grading process paused"
        ))
    
    def resume_grading(self):
        """Resume paused grading process"""
        if not self.is_running or not self._is_paused:
            return
        
        self._is_paused = False
        self._pause_event.set()  # Signal resume
        self.status = GradingStatus.RUNNING
        
        self._emit_progress(ProgressUpdate(
            status=GradingStatus.RUNNING,
            message="Grading process resumed"
        ))
    
    def get_status(self) -> Dict[str, Any]:
        """Get current grading status
        
        Returns:
            Status information dictionary
        """
        return {
            'status': self.status.value,
            'is_running': self.is_running,
            'current_assignment': self.current_assignment,
            'completed_students': len(self.completed_students),
            'total_students': self.total_students,
            'current_student': self.current_student,
            'cost_used': self.cost_used,
            'cost_estimated': self.cost_estimated,
            'is_paused': self._is_paused
        }
    
    async def _cleanup_process(self):
        """Clean up process and temporary files"""
        try:
            # Terminate the subprocess
            if self.process:
                try:
                    self.process.terminate()
                    # Give process time to terminate gracefully
                    try:
                        await asyncio.wait_for(asyncio.to_thread(self.process.wait), timeout=5)
                    except asyncio.TimeoutError:
                        # Force kill if it doesn't terminate
                        self.process.kill()
                        await asyncio.to_thread(self.process.wait)
                except Exception as e:
                    print(f"Error terminating process: {e}")
                finally:
                    self.process = None
            
            # Clean up temporary files
            await self._cleanup_temp_files()
            
            # Run any additional cleanup tasks
            for cleanup_task in self._cleanup_tasks:
                try:
                    if asyncio.iscoroutinefunction(cleanup_task):
                        await cleanup_task()
                    else:
                        cleanup_task()
                except Exception as e:
                    print(f"Error in cleanup task: {e}")
            
            self._cleanup_tasks.clear()
            
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    async def _cleanup_temp_files(self):
        """Clean up temporary files created during processing"""
        for temp_file in self._temp_files:
            try:
                if os.path.exists(temp_file):
                    if os.path.isfile(temp_file):
                        os.unlink(temp_file)
                    elif os.path.isdir(temp_file):
                        import shutil
                        shutil.rmtree(temp_file)
            except Exception as e:
                print(f"Error cleaning up temp file {temp_file}: {e}")
        
        self._temp_files.clear()
    
    def add_temp_file(self, filepath: str):
        """Add a temporary file to be cleaned up later"""
        self._temp_files.append(filepath)
    
    def add_cleanup_task(self, cleanup_func):
        """Add a cleanup function to be called on cancellation"""
        self._cleanup_tasks.append(cleanup_func)
    
    def set_timeout(self, timeout_seconds: int):
        """Set the timeout for grading operations"""
        self._task_timeout = timeout_seconds
    
    def _setup_logging(self):
        """Setup logging for error tracking"""
        try:
            # Create logs directory if it doesn't exist
            log_dir = PROJECT_ROOT / "logs"
            log_dir.mkdir(exist_ok=True)
            
            # Setup file logging
            log_file = log_dir / "grader_service.log"
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            print(f"Failed to setup logging: {e}")
            self.logger = None
    
    def _log_error(self, error: Exception, context: str = ""):
        """Log error with context"""
        if self.logger:
            self.logger.error(f"{context}: {str(error)}")
            self.logger.error(traceback.format_exc())
    
    def _create_error_info(self, error: Exception, context: str = "") -> ErrorInfo:
        """Create comprehensive error information"""
        from datetime import datetime
        
        error_type = type(error).__name__
        error_message = str(error)
        technical_details = traceback.format_exc()
        
        # Determine if error is recoverable and suggest action
        is_recoverable, suggested_action = self._analyze_error(error, error_message)
        
        error_info = ErrorInfo(
            error_type=error_type,
            error_message=error_message,
            is_recoverable=is_recoverable,
            suggested_action=suggested_action,
            technical_details=technical_details,
            timestamp=datetime.now().isoformat()
        )
        
        # Add to error log
        self._error_log.append(error_info)
        
        return error_info
    
    def _analyze_error(self, error: Exception, error_message: str) -> tuple[bool, str]:
        """Analyze error to determine if it's recoverable and suggest action"""
        error_type = type(error).__name__
        error_msg_lower = error_message.lower()
        
        # Network/API errors - usually recoverable
        if any(keyword in error_msg_lower for keyword in [
            'connection', 'timeout', 'network', 'api', 'rate limit', 'server error'
        ]):
            return True, "Check network connection and API keys. Try again in a few minutes."
        
        # File/permission errors - sometimes recoverable
        if any(keyword in error_msg_lower for keyword in [
            'permission', 'access denied', 'file not found', 'no such file'
        ]):
            return True, "Check file permissions and paths. Ensure all files are accessible."
        
        # Memory errors - sometimes recoverable with smaller batches
        if any(keyword in error_msg_lower for keyword in [
            'memory', 'out of memory', 'memoryerror'
        ]):
            return True, "Reduce batch size or close other applications to free memory."
        
        # CLI/subprocess errors - often recoverable
        if any(keyword in error_msg_lower for keyword in [
            'subprocess', 'command', 'exit code'
        ]):
            return True, "Check CLI installation and try restarting the process."
        
        # Authentication errors - usually user-fixable
        if any(keyword in error_msg_lower for keyword in [
            'auth', 'unauthorized', 'invalid key', 'api key'
        ]):
            return True, "Check API keys are correct and have sufficient permissions."
        
        # Critical system errors - usually not recoverable
        if any(keyword in error_msg_lower for keyword in [
            'system', 'critical', 'fatal', 'corruption'
        ]):
            return False, "System error occurred. Contact support with error details."
        
        # Default: assume recoverable for now
        return True, "An unexpected error occurred. Try restarting the operation."
    
    def _save_partial_results(self) -> Optional[str]:
        """Save partial results for recovery"""
        try:
            from datetime import datetime
            import json
            
            # Create partial results directory
            results_dir = PROJECT_ROOT / "partial_results"
            results_dir.mkdir(exist_ok=True)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"partial_results_{timestamp}.json"
            filepath = results_dir / filename
            
            # Collect partial results
            partial_results = PartialResults(
                completed_students=self.completed_students.copy(),
                failed_students=[],  # Could enhance to track failed students
                total_cost=self.cost_used,
                partial_data={
                    'total_students': self.total_students,
                    'current_student': self.current_student,
                    'assignment': self.current_assignment,
                    'log_entries': self.get_log_entries(last_n=100)
                },
                save_timestamp=datetime.now().isoformat()
            )
            
            # Save to file
            with open(filepath, 'w') as f:
                json.dump({
                    'completed_students': partial_results.completed_students,
                    'failed_students': partial_results.failed_students,
                    'total_cost': partial_results.total_cost,
                    'partial_data': partial_results.partial_data,
                    'save_timestamp': partial_results.save_timestamp
                }, f, indent=2)
            
            self._partial_results_file = str(filepath)
            return str(filepath)
            
        except Exception as e:
            self._log_error(e, "Failed to save partial results")
            return None
    
    def load_partial_results(self, filepath: str) -> Optional[PartialResults]:
        """Load partial results for recovery"""
        try:
            import json
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            return PartialResults(
                completed_students=data['completed_students'],
                failed_students=data['failed_students'],
                total_cost=data['total_cost'],
                partial_data=data['partial_data'],
                save_timestamp=data['save_timestamp']
            )
            
        except Exception as e:
            self._log_error(e, f"Failed to load partial results from {filepath}")
            return None
    
    async def retry_operation(self, operation_func, *args, **kwargs) -> Any:
        """Retry an operation with exponential backoff"""
        import asyncio
        
        for attempt in range(self._max_retries + 1):
            try:
                self._retry_count = attempt
                result = await operation_func(*args, **kwargs)
                self._retry_count = 0  # Reset on success
                return result
                
            except Exception as e:
                error_info = self._create_error_info(e, f"Attempt {attempt + 1}")
                
                if not error_info.is_recoverable or attempt >= self._max_retries:
                    # Save partial results before giving up
                    self._save_partial_results()
                    raise
                
                # Exponential backoff: 2^attempt seconds
                delay = 2 ** attempt
                self._emit_progress(ProgressUpdate(
                    status=GradingStatus.ERROR,
                    message=f"Error occurred, retrying in {delay} seconds... (Attempt {attempt + 1}/{self._max_retries + 1})",
                    error=str(e)
                ))
                
                await asyncio.sleep(delay)
        
        # Should not reach here, but just in case
        raise Exception("Maximum retries exceeded")
    
    def get_error_log(self) -> List[ErrorInfo]:
        """Get the error log"""
        return self._error_log.copy()
    
    def clear_error_log(self):
        """Clear the error log"""
        self._error_log.clear()
    
    def get_recovery_suggestions(self) -> List[str]:
        """Get recovery suggestions based on recent errors"""
        if not self._error_log:
            return []
        
        suggestions = set()
        recent_errors = self._error_log[-5:]  # Last 5 errors
        
        for error in recent_errors:
            if error.is_recoverable:
                suggestions.add(error.suggested_action)
        
        return list(suggestions)
    
    async def _monitor_process_with_timeout(self) -> Dict[str, Any]:
        """Monitor process with timeout and pause support"""
        try:
            return await asyncio.wait_for(self._monitor_process(), timeout=self._task_timeout)
        except asyncio.TimeoutError:
            # Cleanup will be handled by the calling method
            raise
    
    async def _monitor_process(self) -> Dict[str, Any]:
        """Monitor the grading process and emit progress updates"""
        output_lines = []
        
        try:
            while True:
                if self._should_cancel:
                    break
                
                # Check for pause state
                await self._pause_event.wait()
                
                # Check cancellation again after pause
                if self._should_cancel:
                    break
                
                # Read line from process
                line = await asyncio.get_event_loop().run_in_executor(
                    None, self.process.stdout.readline
                )
                
                if not line:  # Process finished
                    break
                
                line = line.strip()
                if line:  # Only store non-empty lines
                    output_lines.append(line)
                    
                    # Parse line for progress information
                    self._parse_output_line(line)
                
                # Small delay to prevent overwhelming the callback
                await asyncio.sleep(0.01)
            
            # Wait for process to complete
            return_code = await asyncio.get_event_loop().run_in_executor(
                None, self.process.wait
            )
            
            # Parse final output for results
            full_output = "\n".join(output_lines)
            return self._parse_final_results(full_output, return_code)
            
        except Exception as e:
            raise Exception(f"Error monitoring process: {str(e)}")
    
    def _parse_output_line(self, line: str):
        """Parse a single output line for progress information"""
        if not line:
            return
        
        # Store in log buffer for later viewing
        self._add_to_log_buffer(line)
        
        # Look for progress indicators in CLI output
        # Enhanced patterns based on actual CLI output
        
        # Student progress pattern: [1/25] student_12345.zip
        student_match = re.search(r'\[(\d+)/(\d+)\]\s+(.+)', line)
        if student_match:
            current_num = int(student_match.group(1))
            total_num = int(student_match.group(2))
            student_file = student_match.group(3)
            
            self.total_students = total_num
            self.current_student = student_file
            
            # Extract student ID from filename
            student_id = self._extract_student_id(student_file)
            
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.RUNNING,
                current_student=student_id,
                completed_count=current_num - 1,  # Adjust because this is "starting" the student
                total_count=total_num,
                current_operation=f"Starting {student_id}",
                cost_used=self.cost_used,
                cost_estimated=self.cost_estimated,
                message=line
            ))
            return
        
        # Processing submission pattern
        processing_match = re.search(r'Processing submission:\s+(.+)', line)
        if processing_match:
            submission_path = processing_match.group(1)
            student_file = os.path.basename(submission_path)
            student_id = self._extract_student_id(student_file)
            self.current_student = student_file
            
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.RUNNING,
                current_student=student_id,
                current_operation=f"Processing {student_id}",
                message=line
            ))
            return
        
        # Dry run processing pattern
        dry_run_match = re.search(r'🔍 DRY RUN - Processing submission:\s+(.+)', line)
        if dry_run_match:
            submission_path = dry_run_match.group(1)
            student_file = os.path.basename(submission_path)
            student_id = self._extract_student_id(student_file)
            
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.RUNNING,
                current_student=student_id,
                current_operation=f"Analyzing {student_id} (dry run)",
                message=line
            ))
            return
        
        # Student completion with token summary
        student_total_match = re.search(r'Student total:\s+([0-9,]+)\s+tokens\s+\(\$(\d+\.\d+)\)', line)
        if student_total_match:
            tokens = int(student_total_match.group(1).replace(',', ''))
            cost = float(student_total_match.group(2))
            student_id = self._extract_student_id(self.current_student) if self.current_student else "Unknown"
            
            # Mark this student as completed
            if student_id not in self.completed_students:
                self.completed_students.append(student_id)
            
            self.cost_used += cost
            
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.RUNNING,
                current_student=student_id,
                completed_count=len(self.completed_students),
                total_count=self.total_students,
                current_operation=f"Completed {student_id}",
                cost_used=self.cost_used,
                message=f"Completed {student_id}: {tokens:,} tokens (${cost:.4f})"
            ))
            return
        
        # Per-provider cost tracking patterns
        provider_cost_match = re.search(r'(OpenAI|Anthropic|Cohere):\s+(\d+)\s+input\s+\+\s+(\d+)\s+output\s+=\s+(\d+)\s+tokens\s+\(\$(\d+\.\d+)\)', line)
        if provider_cost_match:
            provider = provider_cost_match.group(1)
            input_tokens = int(provider_cost_match.group(2))
            output_tokens = int(provider_cost_match.group(3))
            total_tokens = int(provider_cost_match.group(4))
            cost = float(provider_cost_match.group(5))
            
            student_id = self._extract_student_id(self.current_student) if self.current_student else "Unknown"
            
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.RUNNING,
                current_student=student_id,
                current_operation=f"Processing with {provider}",
                message=f"{provider}: {total_tokens:,} tokens (${cost:.4f})"
            ))
            return
        
        # Dry run token estimates
        token_estimate_match = re.search(r'📊 Token estimate:\s+([0-9,]+)\s+input\s+\+\s+([0-9,]+)\s+output\s+=\s+([0-9,]+)\s+total', line)
        if token_estimate_match:
            total_tokens = int(token_estimate_match.group(3).replace(',', ''))
            student_id = self._extract_student_id(self.current_student) if self.current_student else "Unknown"
            
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.RUNNING,
                current_student=student_id,
                current_operation=f"Token analysis complete",
                message=f"Estimated {total_tokens:,} tokens for {student_id}"
            ))
            return
        
        # Dry run cost estimates per student
        cost_estimate_match = re.search(r'💰 Cost estimate:\s+\$(\d+\.\d+)', line)
        if cost_estimate_match:
            estimated_cost = float(cost_estimate_match.group(1))
            student_id = self._extract_student_id(self.current_student) if self.current_student else "Unknown"
            
            # Mark as completed for dry run
            if student_id not in self.completed_students:
                self.completed_students.append(student_id)
                
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.RUNNING,
                current_student=student_id,
                completed_count=len(self.completed_students),
                total_count=self.total_students,
                current_operation=f"Cost analysis complete",
                cost_estimated=estimated_cost,
                message=f"Estimated ${estimated_cost:.4f} for {student_id}"
            ))
            return
        
        # Batch initialization patterns
        if "DRY RUN MODE" in line:
            batch_match = re.search(r'Analyzing (\d+) submissions', line)
            if batch_match:
                self.total_students = int(batch_match.group(1))
                self._emit_progress(ProgressUpdate(
                    status=GradingStatus.PREPARING,
                    total_count=self.total_students,
                    current_operation="Starting dry run analysis",
                    message=line
                ))
            return
        
        if "LIVE GRADING" in line:
            batch_match = re.search(r'Processing (\d+) submissions', line)
            if batch_match:
                self.total_students = int(batch_match.group(1))
                self._emit_progress(ProgressUpdate(
                    status=GradingStatus.PREPARING,
                    total_count=self.total_students,
                    current_operation="Starting live grading",
                    message=line
                ))
            return
        
        # Error patterns
        if "❌" in line or ("Error" in line and "error" in line.lower()):
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.ERROR,
                current_operation="Error occurred",
                message=line,
                error=line
            ))
            return
        
        # Operation status updates
        if "Grading with multiple LLMs" in line:
            student_id = self._extract_student_id(self.current_student) if self.current_student else None
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.RUNNING,
                current_student=student_id,
                current_operation="Grading with AI models",
                message=line
            ))
        elif "Extracting content" in line:
            student_id = self._extract_student_id(self.current_student) if self.current_student else None
            self._emit_progress(ProgressUpdate(
                status=GradingStatus.RUNNING,
                current_student=student_id,
                current_operation="Extracting submission content",
                message=line
            ))
    
    def _extract_student_id(self, filename_or_path: str) -> str:
        """Extract student ID from filename or path
        
        Args:
            filename_or_path: Student filename or path
            
        Returns:
            Extracted student ID
        """
        if not filename_or_path:
            return "Unknown"
            
        # Get just the filename
        filename = os.path.basename(filename_or_path)
        
        # Remove .zip extension
        if filename.endswith('.zip'):
            filename = filename[:-4]
        
        # Try various patterns to extract student ID
        patterns = [
            r'student_(\d+)',  # student_12345
            r'(\d+)',          # Just numbers
            r'([a-zA-Z]\d+)',  # A12345, etc.
            r'([a-zA-Z]+\d+)', # abc123, etc.
        ]
        
        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1) if 'student_' in pattern else match.group(0)
        
        # Fallback: clean up the filename
        return filename.replace('_', ' ').strip()
    
    def _parse_cost_output(self, output: str) -> CostEstimate:
        """Parse cost estimation output"""
        try:
            # Look for cost summary in output
            lines = output.split('\n')
            
            total_submissions = 0
            estimated_tokens = 0
            openai_cost = 0.0
            anthropic_cost = 0.0
            total_cost = 0.0
            
            for line in lines:
                # Parse submission count
                if "submissions" in line and "analyzing" in line.lower():
                    match = re.search(r'(\d+)\s+submissions', line)
                    if match:
                        total_submissions = int(match.group(1))
                
                # Parse token estimate
                if "estimated tokens:" in line.lower():
                    match = re.search(r'(\d+(?:,\d+)*)', line)
                    if match:
                        estimated_tokens = int(match.group(1).replace(',', ''))
                
                # Parse cost estimates
                if "openai estimated:" in line.lower():
                    match = re.search(r'\$(\d+\.\d+)', line)
                    if match:
                        openai_cost = float(match.group(1))
                
                if "anthropic estimated:" in line.lower():
                    match = re.search(r'\$(\d+\.\d+)', line)
                    if match:
                        anthropic_cost = float(match.group(1))
                
                if "total estimated cost:" in line.lower():
                    match = re.search(r'\$(\d+\.\d+)', line)
                    if match:
                        total_cost = float(match.group(1))
            
            # Calculate per-submission cost
            per_submission_cost = total_cost / total_submissions if total_submissions > 0 else 0.0
            
            return CostEstimate(
                total_submissions=total_submissions,
                estimated_tokens=estimated_tokens,
                openai_cost=openai_cost,
                anthropic_cost=anthropic_cost,
                total_cost=total_cost,
                per_submission_cost=per_submission_cost
            )
            
        except Exception as e:
            # Return default estimate if parsing fails
            return CostEstimate(
                total_submissions=0,
                estimated_tokens=0,
                openai_cost=0.0,
                anthropic_cost=0.0,
                total_cost=0.0,
                per_submission_cost=0.0
            )
    
    def _parse_final_results(self, output: str, return_code: int) -> Dict[str, Any]:
        """Parse final grading results"""
        results = {
            'success': return_code == 0,
            'return_code': return_code,
            'total_cost': self.cost_used,
            'students_processed': len(self.completed_students),
            'output': output
        }
        
        if return_code != 0:
            # Extract error information
            error_lines = [line for line in output.split('\n') if 'error' in line.lower() or 'failed' in line.lower()]
            results['error'] = '\n'.join(error_lines[-3:]) if error_lines else 'Unknown error occurred'
        
        return results
    
    def _add_to_log_buffer(self, line: str):
        """Add line to log buffer with timestamp"""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'message': line.strip()
        }
        
        self.log_buffer.append(log_entry)
        
        # Keep buffer size manageable
        if len(self.log_buffer) > self.max_log_entries:
            self.log_buffer.pop(0)
    
    def get_log_entries(self, last_n: int = None) -> List[Dict[str, str]]:
        """Get log entries
        
        Args:
            last_n: Number of recent entries to return (None for all)
            
        Returns:
            List of log entries with timestamp and message
        """
        if last_n is None:
            return self.log_buffer.copy()
        else:
            return self.log_buffer[-last_n:] if last_n > 0 else []
    
    def clear_log_buffer(self):
        """Clear the log buffer"""
        self.log_buffer.clear()
    
    def export_log_to_file(self, filepath: str):
        """Export log buffer to a file
        
        Args:
            filepath: Path to save log file
        """
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("Academic Auto Grader - GUI Log Export\n")
                f.write("=" * 50 + "\n\n")
                
                for entry in self.log_buffer:
                    f.write(f"[{entry['timestamp']}] {entry['message']}\n")
                    
        except Exception as e:
            raise Exception(f"Failed to export log: {str(e)}")
    
    def _emit_progress(self, update: ProgressUpdate):
        """Emit progress update to callback"""
        if self.progress_callback:
            try:
                self.progress_callback(update)
            except Exception as e:
                print(f"Error in progress callback: {e}")


def main():
    """Test the grader service"""
    import asyncio
    
    def progress_callback(update: ProgressUpdate):
        print(f"Progress: {update.status.value} - {update.message}")
        if update.current_student:
            print(f"  Current: {update.current_student}")
        if update.completed_count > 0:
            print(f"  Progress: {update.completed_count}/{update.total_count}")
    
    async def test_grader():
        service = GraderService()
        service.set_progress_callback(progress_callback)
        
        print("Testing cost estimation...")
        try:
            # This will fail if no submissions folder exists, but tests the service
            estimate = service.estimate_cost(".", "weatherwise")
            print(f"Cost estimate: ${estimate.total_cost:.2f}")
        except Exception as e:
            print(f"Cost estimation test failed (expected): {e}")
        
        print("Grader service test completed")
    
    asyncio.run(test_grader())


if __name__ == "__main__":
    main()