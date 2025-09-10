"""
Export Service for GUI Application

Provides comprehensive export functionality for grading results including
Excel, JSON, PDF formats and results archiving capabilities.
"""

import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

# Import for potential future use
try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
    from openpyxl.chart import BarChart, Reference
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


@dataclass
class ExportConfig:
    """Export configuration settings"""
    include_summary: bool = True
    include_individual_results: bool = True
    include_rubric_details: bool = True
    include_feedback: bool = True
    include_cost_analysis: bool = True
    include_github_info: bool = True
    file_name_prefix: str = "grading_results"
    timestamp_format: str = "%Y%m%d_%H%M%S"


@dataclass
class ExportResult:
    """Result of an export operation"""
    success: bool
    file_path: Optional[str] = None
    format_type: str = ""
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    export_timestamp: str = ""


class ExportService:
    """Export service for grading results
    
    Provides comprehensive export functionality supporting multiple formats
    including Excel, JSON, PDF, and CSV with customizable options.
    """
    
    def __init__(self, export_directory: Optional[str] = None):
        """Initialize the export service
        
        Args:
            export_directory: Directory for saving exported files
        """
        self.export_directory = Path(export_directory) if export_directory else Path.cwd() / "exports"
        self.export_directory.mkdir(exist_ok=True)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        
    def export_results(
        self,
        results_data: Dict[str, Any],
        student_results: List[Any],
        summary_stats: Any,
        format_type: str,
        config: Optional[ExportConfig] = None
    ) -> ExportResult:
        """Export results in specified format
        
        Args:
            results_data: Raw results data
            student_results: List of student result objects
            summary_stats: Summary statistics object
            format_type: Export format (excel, json, pdf, csv)
            config: Export configuration
            
        Returns:
            ExportResult with operation details
        """
        if config is None:
            config = ExportConfig()
        
        timestamp = datetime.now().strftime(config.timestamp_format)
        
        try:
            if format_type.lower() == "excel":
                return self._export_excel(student_results, summary_stats, config, timestamp)
            elif format_type.lower() == "json":
                return self._export_json(results_data, student_results, summary_stats, config, timestamp)
            elif format_type.lower() == "pdf":
                return self._export_pdf(student_results, summary_stats, config, timestamp)
            elif format_type.lower() == "csv":
                return self._export_csv(student_results, summary_stats, config, timestamp)
            else:
                return ExportResult(
                    success=False,
                    format_type=format_type,
                    error_message=f"Unsupported export format: {format_type}",
                    export_timestamp=timestamp
                )
                
        except Exception as e:
            self.logger.error(f"Export failed for format {format_type}: {str(e)}")
            return ExportResult(
                success=False,
                format_type=format_type,
                error_message=f"Export failed: {str(e)}",
                export_timestamp=timestamp
            )
    
    def _export_excel(self, student_results: List, summary_stats: Any, config: ExportConfig, timestamp: str) -> ExportResult:
        """Export results to Excel format"""
        if not EXCEL_AVAILABLE:
            return ExportResult(
                success=False,
                format_type="excel",
                error_message="Excel export requires openpyxl package. Install with: pip install openpyxl",
                export_timestamp=timestamp
            )
        
        file_name = f"{config.file_name_prefix}_{timestamp}.xlsx"
        file_path = self.export_directory / file_name
        
        # Create workbook and worksheets
        wb = openpyxl.Workbook()
        
        # Remove default sheet and create our sheets
        wb.remove(wb.active)
        
        if config.include_summary:
            self._create_summary_sheet(wb, summary_stats)
        
        if config.include_individual_results:
            self._create_students_sheet(wb, student_results, config)
        
        if config.include_rubric_details:
            self._create_rubric_sheet(wb, student_results)
        
        if config.include_cost_analysis:
            self._create_cost_analysis_sheet(wb, student_results, summary_stats)
        
        # Save workbook
        wb.save(file_path)
        
        return ExportResult(
            success=True,
            file_path=str(file_path),
            format_type="excel",
            file_size=file_path.stat().st_size,
            export_timestamp=timestamp
        )
    
    def _export_json(self, results_data: Dict, student_results: List, summary_stats: Any, config: ExportConfig, timestamp: str) -> ExportResult:
        """Export results to JSON format"""
        file_name = f"{config.file_name_prefix}_{timestamp}.json"
        file_path = self.export_directory / file_name
        
        # Prepare comprehensive JSON structure
        export_data = {
            "export_metadata": {
                "timestamp": timestamp,
                "format_version": "1.0",
                "generated_by": "Academic Auto Grader GUI",
                "export_config": asdict(config)
            }
        }
        
        if config.include_summary and summary_stats:
            export_data["summary_statistics"] = {
                "total_students": summary_stats.total_students,
                "completed_students": summary_stats.completed_students,
                "failed_students": summary_stats.failed_students,
                "average_score": summary_stats.average_score,
                "median_score": summary_stats.median_score,
                "std_deviation": summary_stats.std_deviation,
                "min_score": summary_stats.min_score,
                "max_score": summary_stats.max_score,
                "total_cost": summary_stats.total_cost,
                "average_cost": summary_stats.average_cost,
                "total_tokens": summary_stats.total_tokens,
                "completion_rate": summary_stats.completion_rate,
                "grade_distribution": summary_stats.grade_distribution
            }
        
        if config.include_individual_results:
            export_data["student_results"] = []
            for result in student_results:
                student_data = {
                    "student_id": result.student_id,
                    "student_name": result.student_name,
                    "total_score": result.total_score,
                    "max_score": result.max_score,
                    "percentage": result.percentage,
                    "grade": result.grade,
                    "token_usage": result.token_usage,
                    "cost": result.cost,
                    "processing_time": result.processing_time,
                    "status": result.status
                }
                
                if config.include_rubric_details and result.rubric_scores:
                    student_data["rubric_scores"] = result.rubric_scores
                
                if config.include_feedback and result.feedback:
                    student_data["feedback"] = result.feedback
                
                if config.include_github_info and result.github_repo:
                    student_data["github_repo"] = result.github_repo
                
                export_data["student_results"].append(student_data)
        
        # Add raw data if available
        if results_data:
            export_data["raw_results_data"] = results_data
        
        # Write JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return ExportResult(
            success=True,
            file_path=str(file_path),
            format_type="json",
            file_size=file_path.stat().st_size,
            export_timestamp=timestamp
        )
    
    def _export_pdf(self, student_results: List, summary_stats: Any, config: ExportConfig, timestamp: str) -> ExportResult:
        """Export results to PDF format"""
        if not PDF_AVAILABLE:
            return ExportResult(
                success=False,
                format_type="pdf",
                error_message="PDF export requires reportlab package. Install with: pip install reportlab",
                export_timestamp=timestamp
            )
        
        file_name = f"{config.file_name_prefix}_{timestamp}.pdf"
        file_path = self.export_directory / file_name
        
        # Create PDF document
        doc = SimpleDocTemplate(str(file_path), pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4e79'),
            alignment=1  # Center alignment
        )
        story.append(Paragraph("Grading Results Report", title_style))
        story.append(Spacer(1, 0.5*inch))
        
        # Summary section
        if config.include_summary and summary_stats:
            story.append(Paragraph("Summary Statistics", styles['Heading2']))
            
            summary_data = [
                ['Metric', 'Value'],
                ['Total Students', str(summary_stats.total_students)],
                ['Completed', str(summary_stats.completed_students)],
                ['Failed', str(summary_stats.failed_students)],
                ['Average Score', f"{summary_stats.average_score:.1f}%"],
                ['Median Score', f"{summary_stats.median_score:.1f}%"],
                ['Standard Deviation', f"{summary_stats.std_deviation:.1f}"],
                ['Completion Rate', f"{summary_stats.completion_rate:.1f}%"],
                ['Total Cost', f"${summary_stats.total_cost:.2f}"],
                ['Total Tokens', f"{summary_stats.total_tokens:,}"]
            ]
            
            summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e79')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(summary_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Grade distribution
        if summary_stats and summary_stats.grade_distribution:
            story.append(Paragraph("Grade Distribution", styles['Heading2']))
            
            grade_data = [['Grade', 'Count']]
            for grade, count in summary_stats.grade_distribution.items():
                grade_data.append([grade, str(count)])
            
            grade_table = Table(grade_data, colWidths=[1*inch, 1*inch])
            grade_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e79')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(grade_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Individual results
        if config.include_individual_results and student_results:
            story.append(Paragraph("Individual Student Results", styles['Heading2']))
            
            # Create table with student results
            student_data = [['Student ID', 'Name', 'Score', 'Grade', 'Cost', 'Status']]
            
            for result in student_results[:20]:  # Limit to first 20 for PDF space
                student_data.append([
                    result.student_id,
                    result.student_name,
                    f"{result.total_score:.1f}%",
                    result.grade,
                    f"${result.cost:.3f}",
                    result.status
                ])
            
            if len(student_results) > 20:
                student_data.append(['...', f'({len(student_results) - 20} more students)', '', '', '', ''])
            
            student_table = Table(student_data, colWidths=[1.2*inch, 1.5*inch, 0.8*inch, 0.6*inch, 0.8*inch, 0.8*inch])
            student_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f4e79')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            story.append(student_table)
        
        # Build PDF
        doc.build(story)
        
        return ExportResult(
            success=True,
            file_path=str(file_path),
            format_type="pdf",
            file_size=file_path.stat().st_size,
            export_timestamp=timestamp
        )
    
    def _export_csv(self, student_results: List, summary_stats: Any, config: ExportConfig, timestamp: str) -> ExportResult:
        """Export results to CSV format"""
        file_name = f"{config.file_name_prefix}_{timestamp}.csv"
        file_path = self.export_directory / file_name
        
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['student_id', 'student_name', 'total_score', 'grade', 'status', 'cost', 'token_usage', 'processing_time']
            
            if config.include_github_info:
                fieldnames.append('github_repo')
            
            if config.include_rubric_details:
                # Add rubric criteria columns (we'll determine these from first student)
                if student_results and student_results[0].rubric_scores:
                    for criterion in student_results[0].rubric_scores.keys():
                        fieldnames.append(f'rubric_{criterion.lower().replace(" ", "_")}')
            
            if config.include_feedback:
                fieldnames.append('feedback')
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in student_results:
                row = {
                    'student_id': result.student_id,
                    'student_name': result.student_name,
                    'total_score': result.total_score,
                    'grade': result.grade,
                    'status': result.status,
                    'cost': result.cost,
                    'token_usage': result.token_usage,
                    'processing_time': result.processing_time
                }
                
                if config.include_github_info:
                    row['github_repo'] = result.github_repo or ''
                
                if config.include_rubric_details and result.rubric_scores:
                    for criterion, score in result.rubric_scores.items():
                        row[f'rubric_{criterion.lower().replace(" ", "_")}'] = score
                
                if config.include_feedback:
                    row['feedback'] = result.feedback or ''
                
                writer.writerow(row)
        
        return ExportResult(
            success=True,
            file_path=str(file_path),
            format_type="csv",
            file_size=file_path.stat().st_size,
            export_timestamp=timestamp
        )
    
    def _create_summary_sheet(self, workbook, summary_stats):
        """Create summary statistics worksheet"""
        ws = workbook.create_sheet("Summary")
        
        # Headers
        ws['A1'] = "Grading Results Summary"
        ws['A1'].font = Font(size=16, bold=True, color="1F4E79")
        ws.merge_cells('A1:B1')
        
        # Summary data
        summary_data = [
            ("Total Students", summary_stats.total_students),
            ("Completed", summary_stats.completed_students),
            ("Failed", summary_stats.failed_students),
            ("Completion Rate", f"{summary_stats.completion_rate:.1f}%"),
            ("Average Score", f"{summary_stats.average_score:.1f}%"),
            ("Median Score", f"{summary_stats.median_score:.1f}%"),
            ("Standard Deviation", f"{summary_stats.std_deviation:.1f}"),
            ("Min Score", f"{summary_stats.min_score:.1f}%"),
            ("Max Score", f"{summary_stats.max_score:.1f}%"),
            ("Total Cost", f"${summary_stats.total_cost:.2f}"),
            ("Average Cost per Student", f"${summary_stats.average_cost:.3f}"),
            ("Total Tokens", f"{summary_stats.total_tokens:,}")
        ]
        
        for i, (label, value) in enumerate(summary_data, start=3):
            ws[f'A{i}'] = label
            ws[f'B{i}'] = value
            ws[f'A{i}'].font = Font(bold=True)
        
        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
    
    def _create_students_sheet(self, workbook, student_results, config):
        """Create individual student results worksheet"""
        ws = workbook.create_sheet("Student Results")
        
        # Headers
        headers = ['Student ID', 'Name', 'Total Score', 'Grade', 'Status', 'Cost', 'Tokens', 'Processing Time']
        
        if config.include_github_info:
            headers.append('GitHub Repo')
        
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        
        # Student data
        for row, result in enumerate(student_results, start=2):
            ws.cell(row=row, column=1, value=result.student_id)
            ws.cell(row=row, column=2, value=result.student_name)
            ws.cell(row=row, column=3, value=result.total_score)
            ws.cell(row=row, column=4, value=result.grade)
            ws.cell(row=row, column=5, value=result.status)
            ws.cell(row=row, column=6, value=result.cost)
            ws.cell(row=row, column=7, value=result.token_usage)
            ws.cell(row=row, column=8, value=result.processing_time)
            
            if config.include_github_info:
                ws.cell(row=row, column=9, value=result.github_repo or '')
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_rubric_sheet(self, workbook, student_results):
        """Create rubric scores worksheet"""
        ws = workbook.create_sheet("Rubric Scores")
        
        # Get all rubric criteria from first student
        if not student_results or not student_results[0].rubric_scores:
            ws['A1'] = "No rubric data available"
            return
        
        criteria = list(student_results[0].rubric_scores.keys())
        headers = ['Student ID', 'Name'] + criteria + ['Total Score']
        
        # Headers
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
        
        # Student rubric data
        for row, result in enumerate(student_results, start=2):
            ws.cell(row=row, column=1, value=result.student_id)
            ws.cell(row=row, column=2, value=result.student_name)
            
            for col, criterion in enumerate(criteria, start=3):
                score = result.rubric_scores.get(criterion, 0) if result.rubric_scores else 0
                ws.cell(row=row, column=col, value=score)
            
            ws.cell(row=row, column=len(headers), value=result.total_score)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_cost_analysis_sheet(self, workbook, student_results, summary_stats):
        """Create cost analysis worksheet"""
        ws = workbook.create_sheet("Cost Analysis")
        
        # Summary
        ws['A1'] = "Cost Analysis Summary"
        ws['A1'].font = Font(size=14, bold=True, color="1F4E79")
        ws.merge_cells('A1:B1')
        
        ws['A3'] = "Total Cost"
        ws['B3'] = f"${summary_stats.total_cost:.2f}"
        ws['A4'] = "Average per Student"
        ws['B4'] = f"${summary_stats.average_cost:.3f}"
        ws['A5'] = "Total Tokens"
        ws['B5'] = summary_stats.total_tokens
        
        # Individual costs
        ws['A7'] = "Individual Student Costs"
        ws['A7'].font = Font(bold=True, color="1F4E79")
        
        headers = ['Student ID', 'Name', 'Cost', 'Tokens', 'Cost per Token']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=8, column=col, value=header)
            cell.font = Font(bold=True)
        
        for row, result in enumerate(student_results, start=9):
            ws.cell(row=row, column=1, value=result.student_id)
            ws.cell(row=row, column=2, value=result.student_name)
            ws.cell(row=row, column=3, value=result.cost)
            ws.cell(row=row, column=4, value=result.token_usage)
            cost_per_token = result.cost / max(1, result.token_usage)
            ws.cell(row=row, column=5, value=f"{cost_per_token:.6f}")
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def archive_results(self, results_data: Dict, student_results: List, summary_stats: Any, assignment_name: str = "") -> ExportResult:
        """Archive results for later reference"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"archive_{assignment_name}_{timestamp}" if assignment_name else f"archive_{timestamp}"
        
        # Create archive directory
        archive_dir = self.export_directory / "archives" / archive_name
        archive_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Export in multiple formats for archival
            config = ExportConfig(file_name_prefix="archived_results")
            
            # JSON (complete data)
            json_result = self._export_json(results_data, student_results, summary_stats, config, timestamp)
            if json_result.success and json_result.file_path:
                import shutil
                shutil.move(json_result.file_path, archive_dir / f"complete_data_{timestamp}.json")
            
            # CSV (for compatibility)
            csv_result = self._export_csv(student_results, summary_stats, config, timestamp)
            if csv_result.success and csv_result.file_path:
                import shutil
                shutil.move(csv_result.file_path, archive_dir / f"student_results_{timestamp}.csv")
            
            # Create archive metadata
            metadata = {
                "archive_created": timestamp,
                "assignment_name": assignment_name,
                "total_students": len(student_results),
                "archive_format_version": "1.0",
                "files_included": ["complete_data.json", "student_results.csv"]
            }
            
            with open(archive_dir / "archive_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return ExportResult(
                success=True,
                file_path=str(archive_dir),
                format_type="archive",
                export_timestamp=timestamp
            )
            
        except Exception as e:
            return ExportResult(
                success=False,
                format_type="archive",
                error_message=f"Archive failed: {str(e)}",
                export_timestamp=timestamp
            )
    
    def get_export_capabilities(self) -> Dict[str, bool]:
        """Get available export capabilities"""
        return {
            "excel": EXCEL_AVAILABLE,
            "pdf": PDF_AVAILABLE,
            "json": True,
            "csv": True,
            "archive": True
        }
    
    def list_archives(self) -> List[Dict[str, Any]]:
        """List available archived results"""
        archives_dir = self.export_directory / "archives"
        if not archives_dir.exists():
            return []
        
        archives = []
        for archive_dir in archives_dir.iterdir():
            if archive_dir.is_dir():
                metadata_file = archive_dir / "archive_metadata.json"
                if metadata_file.exists():
                    try:
                        with open(metadata_file) as f:
                            metadata = json.load(f)
                        metadata["archive_path"] = str(archive_dir)
                        archives.append(metadata)
                    except Exception:
                        pass  # Skip invalid archives
        
        return sorted(archives, key=lambda x: x.get("archive_created", ""), reverse=True)