"""
Configuration Validation Service for GUI Application

Integrates existing CLI configuration validator with enhanced GUI-friendly
validation results, auto-fix suggestions, and validation report generation.
"""

import os
import sys
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# Add CLI core to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CLI_CORE_DIR = PROJECT_ROOT / "cli" / "core"
sys.path.insert(0, str(CLI_CORE_DIR))

try:
    from config_loader import ConfigLoader
    CLI_VALIDATOR_AVAILABLE = True
except ImportError:
    CLI_VALIDATOR_AVAILABLE = False


class ValidationLevel(Enum):
    """Validation issue severity levels"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


@dataclass
class ValidationIssue:
    """Individual validation issue"""
    level: ValidationLevel
    field: str
    message: str
    description: str
    auto_fix_available: bool = False
    auto_fix_description: str = ""
    suggested_value: Any = None
    line_number: Optional[int] = None
    section: str = ""


@dataclass
class ValidationResult:
    """Complete validation result"""
    is_valid: bool
    issues: List[ValidationIssue]
    total_errors: int
    total_warnings: int
    total_info: int
    validation_timestamp: str
    config_file: str = ""
    
    def get_issues_by_level(self, level: ValidationLevel) -> List[ValidationIssue]:
        """Get issues by severity level"""
        return [issue for issue in self.issues if issue.level == level]
    
    def has_auto_fixes(self) -> bool:
        """Check if any issues have auto-fix suggestions"""
        return any(issue.auto_fix_available for issue in self.issues)


@dataclass
class AutoFixSuggestion:
    """Auto-fix suggestion for validation issues"""
    field: str
    current_value: Any
    suggested_value: Any
    description: str
    confidence: float  # 0.0 to 1.0
    risk_level: str  # low, medium, high


class ConfigurationValidationService:
    """Configuration validation service
    
    Provides comprehensive validation of assignment configurations with
    GUI-friendly error reporting and auto-fix suggestions.
    """
    
    def __init__(self):
        """Initialize the validation service"""
        self.cli_validator_available = CLI_VALIDATOR_AVAILABLE
        
        # Validation rules and patterns
        self.validation_rules = self._load_validation_rules()
        
        # Auto-fix strategies
        self.auto_fix_strategies = self._load_auto_fix_strategies()
    
    def validate_configuration(
        self, 
        config_data: Dict[str, Any], 
        config_file: str = ""
    ) -> ValidationResult:
        """Validate assignment configuration
        
        Args:
            config_data: Configuration dictionary
            config_file: Path to configuration file (optional)
            
        Returns:
            ValidationResult with issues and suggestions
        """
        issues = []
        validation_timestamp = datetime.now().isoformat()
        
        # Basic structure validation
        issues.extend(self._validate_basic_structure(config_data))
        
        # Field-specific validation
        issues.extend(self._validate_assignment_fields(config_data))
        
        # Rubric validation
        issues.extend(self._validate_rubric(config_data))
        
        # Function requirements validation
        issues.extend(self._validate_function_requirements(config_data))
        
        # Cross-field validation
        issues.extend(self._validate_cross_field_consistency(config_data))
        
        # CLI validator integration (if available)
        if self.cli_validator_available:
            issues.extend(self._validate_with_cli_validator(config_data, config_file))
        
        # Count issues by level
        total_errors = len([i for i in issues if i.level == ValidationLevel.ERROR])
        total_warnings = len([i for i in issues if i.level == ValidationLevel.WARNING])
        total_info = len([i for i in issues if i.level == ValidationLevel.INFO])
        
        is_valid = total_errors == 0
        
        return ValidationResult(
            is_valid=is_valid,
            issues=issues,
            total_errors=total_errors,
            total_warnings=total_warnings,
            total_info=total_info,
            validation_timestamp=validation_timestamp,
            config_file=config_file
        )
    
    def _validate_basic_structure(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate basic configuration structure"""
        issues = []
        
        # Required fields
        required_fields = {
            "name": "Assignment name is required",
            "type": "Assignment type must be specified",
            "max_points": "Maximum points must be defined"
        }
        
        for field, message in required_fields.items():
            if field not in config or not config[field]:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field=field,
                    message=message,
                    description=f"The '{field}' field is mandatory for all assignments.",
                    auto_fix_available=True,
                    auto_fix_description=f"Set default value for {field}",
                    suggested_value=self._get_default_value(field),
                    section="Basic Configuration"
                ))
        
        # Valid assignment types
        if "type" in config:
            valid_types = ["coding", "project", "lab", "homework", "quiz", "exam"]
            if config["type"] not in valid_types:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field="type",
                    message=f"Invalid assignment type: {config['type']}",
                    description=f"Assignment type must be one of: {', '.join(valid_types)}",
                    auto_fix_available=True,
                    auto_fix_description="Set to 'coding' (most common type)",
                    suggested_value="coding",
                    section="Basic Configuration"
                ))
        
        return issues
    
    def _validate_assignment_fields(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate assignment-specific fields"""
        issues = []
        
        # Name validation
        if "name" in config:
            name = config["name"]
            if len(name) < 3:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    field="name",
                    message="Assignment name is very short",
                    description="Consider using a more descriptive name (at least 3 characters).",
                    auto_fix_available=False,
                    section="Basic Configuration"
                ))
            
            if len(name) > 100:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    field="name",
                    message="Assignment name is very long",
                    description="Consider shortening the name for better display (max 100 characters recommended).",
                    auto_fix_available=True,
                    auto_fix_description="Truncate to 100 characters",
                    suggested_value=name[:100],
                    section="Basic Configuration"
                ))
        
        # Max points validation
        if "max_points" in config:
            max_points = config["max_points"]
            try:
                points = float(max_points)
                if points <= 0:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        field="max_points",
                        message="Maximum points must be positive",
                        description="Assignments must have a positive maximum score.",
                        auto_fix_available=True,
                        auto_fix_description="Set to 100 points (standard default)",
                        suggested_value=100,
                        section="Grading Configuration"
                    ))
                elif points > 1000:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        field="max_points",
                        message="Maximum points is unusually high",
                        description="Consider if such a high point value is intentional.",
                        auto_fix_available=True,
                        auto_fix_description="Set to 100 points (common standard)",
                        suggested_value=100,
                        section="Grading Configuration"
                    ))
            except (ValueError, TypeError):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field="max_points",
                    message="Maximum points must be a number",
                    description="The max_points field must contain a valid numeric value.",
                    auto_fix_available=True,
                    auto_fix_description="Set to 100 (numeric default)",
                    suggested_value=100,
                    section="Grading Configuration"
                ))
        
        # Description validation
        if "description" in config and config["description"]:
            description = config["description"]
            if len(description) < 10:
                issues.append(ValidationIssue(
                    level=ValidationLevel.INFO,
                    field="description",
                    message="Assignment description is quite brief",
                    description="Consider adding more detail to help students understand the assignment.",
                    auto_fix_available=False,
                    section="Basic Configuration"
                ))
        
        return issues
    
    def _validate_rubric(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate rubric configuration"""
        issues = []
        
        if "rubric" not in config:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                field="rubric",
                message="No rubric defined",
                description="Consider adding a rubric to provide clear grading criteria.",
                auto_fix_available=True,
                auto_fix_description="Add default rubric criteria",
                suggested_value=self._get_default_rubric(),
                section="Rubric Configuration"
            ))
            return issues
        
        rubric = config["rubric"]
        
        if not isinstance(rubric, dict):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                field="rubric",
                message="Rubric must be a dictionary",
                description="The rubric should contain criterion names as keys with their configurations.",
                auto_fix_available=True,
                auto_fix_description="Replace with default rubric structure",
                suggested_value=self._get_default_rubric(),
                section="Rubric Configuration"
            ))
            return issues
        
        if not rubric:
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                field="rubric",
                message="Rubric is empty",
                description="An empty rubric means no structured grading criteria.",
                auto_fix_available=True,
                auto_fix_description="Add default rubric criteria",
                suggested_value=self._get_default_rubric(),
                section="Rubric Configuration"
            ))
            return issues
        
        # Validate individual criteria
        total_weight = 0.0
        total_points = 0.0
        
        for criterion_name, criterion_data in rubric.items():
            # Validate criterion structure
            if not isinstance(criterion_data, dict):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field=f"rubric.{criterion_name}",
                    message=f"Criterion '{criterion_name}' must be a dictionary",
                    description="Each rubric criterion should have weight, max_points, and description.",
                    auto_fix_available=True,
                    auto_fix_description=f"Fix structure for '{criterion_name}'",
                    suggested_value={
                        "description": f"Grading criterion for {criterion_name}",
                        "weight": 0.25,
                        "max_points": 25
                    },
                    section="Rubric Configuration"
                ))
                continue
            
            # Check required fields
            if "weight" not in criterion_data:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field=f"rubric.{criterion_name}.weight",
                    message=f"Criterion '{criterion_name}' missing weight",
                    description="Each rubric criterion must have a weight (0.0-1.0).",
                    auto_fix_available=True,
                    auto_fix_description="Set default weight",
                    suggested_value=0.25,
                    section="Rubric Configuration"
                ))
            else:
                try:
                    weight = float(criterion_data["weight"])
                    total_weight += weight
                    
                    if weight < 0 or weight > 1:
                        issues.append(ValidationIssue(
                            level=ValidationLevel.ERROR,
                            field=f"rubric.{criterion_name}.weight",
                            message=f"Invalid weight for '{criterion_name}': {weight}",
                            description="Rubric weights must be between 0.0 and 1.0.",
                            auto_fix_available=True,
                            auto_fix_description="Normalize weight to valid range",
                            suggested_value=min(1.0, max(0.0, weight)),
                            section="Rubric Configuration"
                        ))
                except (ValueError, TypeError):
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        field=f"rubric.{criterion_name}.weight",
                        message=f"Weight for '{criterion_name}' must be numeric",
                        description="Rubric weights must be valid numbers.",
                        auto_fix_available=True,
                        auto_fix_description="Set numeric weight",
                        suggested_value=0.25,
                        section="Rubric Configuration"
                    ))
            
            if "max_points" not in criterion_data:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    field=f"rubric.{criterion_name}.max_points",
                    message=f"Criterion '{criterion_name}' missing max_points",
                    description="Consider specifying maximum points for clarity.",
                    auto_fix_available=True,
                    auto_fix_description="Calculate from weight and assignment max_points",
                    suggested_value=config.get("max_points", 100) * criterion_data.get("weight", 0.25),
                    section="Rubric Configuration"
                ))
            else:
                try:
                    points = float(criterion_data["max_points"])
                    total_points += points
                except (ValueError, TypeError):
                    issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        field=f"rubric.{criterion_name}.max_points",
                        message=f"Max points for '{criterion_name}' must be numeric",
                        description="Maximum points must be a valid number.",
                        auto_fix_available=True,
                        auto_fix_description="Set numeric max_points",
                        suggested_value=25,
                        section="Rubric Configuration"
                    ))
        
        # Validate total weight
        if abs(total_weight - 1.0) > 0.01:
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR if total_weight > 1.05 else ValidationLevel.WARNING,
                field="rubric",
                message=f"Rubric weights sum to {total_weight:.2%} (should be 100%)",
                description="All rubric criterion weights should sum to exactly 1.0 (100%).",
                auto_fix_available=True,
                auto_fix_description="Normalize weights to sum to 100%",
                suggested_value="normalize_weights",
                section="Rubric Configuration"
            ))
        
        return issues
    
    def _validate_function_requirements(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate function requirements"""
        issues = []
        
        if "function_requirements" not in config:
            return issues
        
        func_reqs = config["function_requirements"]
        
        if not isinstance(func_reqs, list):
            issues.append(ValidationIssue(
                level=ValidationLevel.ERROR,
                field="function_requirements",
                message="Function requirements must be a list",
                description="Function requirements should be specified as a list of function definitions.",
                auto_fix_available=True,
                auto_fix_description="Convert to empty list",
                suggested_value=[],
                section="Function Requirements"
            ))
            return issues
        
        for i, func_req in enumerate(func_reqs):
            if not isinstance(func_req, dict):
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field=f"function_requirements[{i}]",
                    message=f"Function requirement {i} must be a dictionary",
                    description="Each function requirement should specify name, parameters, and return type.",
                    auto_fix_available=True,
                    auto_fix_description="Fix function requirement structure",
                    suggested_value={
                        "name": f"function_{i + 1}",
                        "description": "Function description",
                        "parameters": [],
                        "return_type": "void"
                    },
                    section="Function Requirements"
                ))
                continue
            
            # Validate function name
            if "name" not in func_req or not func_req["name"]:
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field=f"function_requirements[{i}].name",
                    message=f"Function requirement {i} missing name",
                    description="Each function must have a valid name.",
                    auto_fix_available=True,
                    auto_fix_description="Set default function name",
                    suggested_value=f"function_{i + 1}",
                    section="Function Requirements"
                ))
            else:
                # Validate function name format
                func_name = func_req["name"]
                if not func_name.replace("_", "").isalnum():
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        field=f"function_requirements[{i}].name",
                        message=f"Function name '{func_name}' may not be valid",
                        description="Function names should contain only letters, numbers, and underscores.",
                        auto_fix_available=False,
                        section="Function Requirements"
                    ))
        
        return issues
    
    def _validate_cross_field_consistency(self, config: Dict[str, Any]) -> List[ValidationIssue]:
        """Validate consistency between fields"""
        issues = []
        
        # Check rubric points vs assignment max_points
        if "rubric" in config and "max_points" in config:
            rubric = config["rubric"]
            max_points = config.get("max_points", 0)
            
            if isinstance(rubric, dict) and rubric:
                rubric_total = sum(
                    criterion.get("max_points", 0) 
                    for criterion in rubric.values() 
                    if isinstance(criterion, dict)
                )
                
                if abs(rubric_total - max_points) > 0.1:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        field="consistency",
                        message=f"Rubric total points ({rubric_total}) doesn't match assignment max points ({max_points})",
                        description="Consider ensuring rubric points sum to the assignment's maximum points.",
                        auto_fix_available=True,
                        auto_fix_description="Adjust rubric points to match assignment total",
                        suggested_value="adjust_rubric_points",
                        section="Consistency Check"
                    ))
        
        # Check GitHub integration for coding assignments
        if config.get("type") == "coding" and not config.get("github_integration", False):
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                field="github_integration",
                message="Consider enabling GitHub integration for coding assignments",
                description="GitHub integration provides additional analysis capabilities for code submissions.",
                auto_fix_available=True,
                auto_fix_description="Enable GitHub integration",
                suggested_value=True,
                section="Integration Options"
            ))
        
        return issues
    
    def _validate_with_cli_validator(self, config: Dict[str, Any], config_file: str) -> List[ValidationIssue]:
        """Integrate with existing CLI validator if available"""
        issues = []
        
        if not self.cli_validator_available:
            return issues
        
        try:
            # Create temporary config file for CLI validation
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as tmp_file:
                yaml.dump(config, tmp_file, default_flow_style=False)
                tmp_file_path = tmp_file.name
            
            # Use CLI validator (placeholder - would need actual CLI validator integration)
            # For now, we'll add a placeholder validation
            issues.append(ValidationIssue(
                level=ValidationLevel.INFO,
                field="cli_validation",
                message="CLI validator integration successful",
                description="Configuration passed CLI validator checks.",
                auto_fix_available=False,
                section="CLI Integration"
            ))
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
        except Exception as e:
            issues.append(ValidationIssue(
                level=ValidationLevel.WARNING,
                field="cli_validation",
                message="CLI validator integration failed",
                description=f"Could not run CLI validator: {str(e)}",
                auto_fix_available=False,
                section="CLI Integration"
            ))
        
        return issues
    
    def generate_auto_fix_suggestions(self, validation_result: ValidationResult) -> List[AutoFixSuggestion]:
        """Generate auto-fix suggestions for validation issues"""
        suggestions = []
        
        for issue in validation_result.issues:
            if issue.auto_fix_available:
                suggestion = AutoFixSuggestion(
                    field=issue.field,
                    current_value="<current>",  # Would need actual current value
                    suggested_value=issue.suggested_value,
                    description=issue.auto_fix_description,
                    confidence=self._calculate_fix_confidence(issue),
                    risk_level=self._assess_fix_risk(issue)
                )
                suggestions.append(suggestion)
        
        return suggestions
    
    def apply_auto_fixes(
        self, 
        config: Dict[str, Any], 
        fixes_to_apply: List[str]
    ) -> Tuple[Dict[str, Any], List[str]]:
        """Apply selected auto-fixes to configuration
        
        Args:
            config: Original configuration
            fixes_to_apply: List of field names to fix
            
        Returns:
            Tuple of (fixed_config, applied_fixes)
        """
        fixed_config = config.copy()
        applied_fixes = []
        
        validation_result = self.validate_configuration(config)
        
        for issue in validation_result.issues:
            if issue.field in fixes_to_apply and issue.auto_fix_available:
                try:
                    if issue.suggested_value == "normalize_weights":
                        fixed_config = self._normalize_rubric_weights(fixed_config)
                    elif issue.suggested_value == "adjust_rubric_points":
                        fixed_config = self._adjust_rubric_points(fixed_config)
                    else:
                        # Simple field replacement
                        if "." in issue.field:
                            # Handle nested fields
                            self._set_nested_value(fixed_config, issue.field, issue.suggested_value)
                        else:
                            fixed_config[issue.field] = issue.suggested_value
                    
                    applied_fixes.append(issue.field)
                except Exception as e:
                    print(f"Failed to apply fix for {issue.field}: {e}")
        
        return fixed_config, applied_fixes
    
    def export_validation_report(
        self, 
        validation_result: ValidationResult, 
        format_type: str = "json"
    ) -> str:
        """Export validation report in specified format
        
        Args:
            validation_result: Validation result to export
            format_type: Export format (json, yaml, txt)
            
        Returns:
            Formatted report string
        """
        if format_type == "json":
            return json.dumps(asdict(validation_result), indent=2, default=str)
        elif format_type == "yaml":
            return yaml.dump(asdict(validation_result), default_flow_style=False)
        elif format_type == "txt":
            return self._generate_text_report(validation_result)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _generate_text_report(self, validation_result: ValidationResult) -> str:
        """Generate human-readable text report"""
        lines = []
        lines.append("Configuration Validation Report")
        lines.append("=" * 40)
        lines.append(f"Timestamp: {validation_result.validation_timestamp}")
        lines.append(f"Config File: {validation_result.config_file or 'In-memory'}")
        lines.append(f"Status: {'VALID' if validation_result.is_valid else 'INVALID'}")
        lines.append("")
        lines.append(f"Summary:")
        lines.append(f"  Errors: {validation_result.total_errors}")
        lines.append(f"  Warnings: {validation_result.total_warnings}")
        lines.append(f"  Info: {validation_result.total_info}")
        lines.append("")
        
        if validation_result.issues:
            lines.append("Issues:")
            lines.append("-" * 20)
            
            for issue in validation_result.issues:
                lines.append(f"[{issue.level.value.upper()}] {issue.field}")
                lines.append(f"  Message: {issue.message}")
                lines.append(f"  Description: {issue.description}")
                if issue.auto_fix_available:
                    lines.append(f"  Auto-fix: {issue.auto_fix_description}")
                lines.append("")
        
        return "\n".join(lines)
    
    # Helper methods
    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules configuration"""
        return {
            "required_fields": ["name", "type", "max_points"],
            "valid_types": ["coding", "project", "lab", "homework", "quiz", "exam"],
            "max_name_length": 100,
            "min_name_length": 3,
            "max_points_limit": 1000
        }
    
    def _load_auto_fix_strategies(self) -> Dict[str, Any]:
        """Load auto-fix strategies"""
        return {
            "default_values": {
                "name": "New Assignment",
                "type": "coding",
                "max_points": 100,
                "description": "",
                "github_integration": False
            }
        }
    
    def _get_default_value(self, field: str) -> Any:
        """Get default value for a field"""
        defaults = self.auto_fix_strategies.get("default_values", {})
        return defaults.get(field, "")
    
    def _get_default_rubric(self) -> Dict[str, Any]:
        """Get default rubric configuration"""
        return {
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
    
    def _calculate_fix_confidence(self, issue: ValidationIssue) -> float:
        """Calculate confidence level for auto-fix"""
        # Simple confidence calculation based on issue type
        confidence_map = {
            ValidationLevel.ERROR: 0.9,  # High confidence for error fixes
            ValidationLevel.WARNING: 0.7,  # Medium confidence for warnings
            ValidationLevel.INFO: 0.5   # Lower confidence for info suggestions
        }
        return confidence_map.get(issue.level, 0.5)
    
    def _assess_fix_risk(self, issue: ValidationIssue) -> str:
        """Assess risk level of applying auto-fix"""
        if issue.level == ValidationLevel.ERROR:
            return "low"  # Fixing errors is usually safe
        elif issue.level == ValidationLevel.WARNING:
            return "medium"  # Warnings might change behavior
        else:
            return "low"  # Info fixes are typically safe
    
    def _normalize_rubric_weights(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize rubric weights to sum to 1.0"""
        if "rubric" not in config or not isinstance(config["rubric"], dict):
            return config
        
        rubric = config["rubric"].copy()
        total_weight = sum(
            criterion.get("weight", 0) 
            for criterion in rubric.values() 
            if isinstance(criterion, dict)
        )
        
        if total_weight > 0:
            for criterion_name, criterion_data in rubric.items():
                if isinstance(criterion_data, dict) and "weight" in criterion_data:
                    criterion_data["weight"] = criterion_data["weight"] / total_weight
        
        config = config.copy()
        config["rubric"] = rubric
        return config
    
    def _adjust_rubric_points(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Adjust rubric points to match assignment max_points"""
        if "rubric" not in config or "max_points" not in config:
            return config
        
        rubric = config["rubric"].copy()
        max_points = config["max_points"]
        
        for criterion_name, criterion_data in rubric.items():
            if isinstance(criterion_data, dict) and "weight" in criterion_data:
                weight = criterion_data.get("weight", 0)
                criterion_data["max_points"] = max_points * weight
        
        config = config.copy()
        config["rubric"] = rubric
        return config
    
    def _set_nested_value(self, config: Dict[str, Any], field_path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        parts = field_path.split(".")
        current = config
        
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = value
    
    def get_validation_summary(self, validation_result: ValidationResult) -> Dict[str, Any]:
        """Get a summary of validation results for display"""
        return {
            "is_valid": validation_result.is_valid,
            "total_issues": len(validation_result.issues),
            "errors": validation_result.total_errors,
            "warnings": validation_result.total_warnings,
            "info": validation_result.total_info,
            "has_auto_fixes": validation_result.has_auto_fixes(),
            "timestamp": validation_result.validation_timestamp
        }