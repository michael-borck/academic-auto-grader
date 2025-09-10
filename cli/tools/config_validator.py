#!/usr/bin/env python3
"""
Configuration validator for assignment configs
Validates assignment configurations for completeness and correctness
"""

import yaml
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple


class ConfigValidator:
    """Validates assignment configurations"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_assignment_config(self, config_path: str) -> Tuple[bool, List[str], List[str]]:
        """Validate an assignment configuration file"""
        self.errors = []
        self.warnings = []
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            self.errors.append(f"Configuration file not found: {config_path}")
            return False, self.errors, self.warnings
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            self.errors.append(f"Invalid YAML format: {e}")
            return False, self.errors, self.warnings
        
        # Validate structure
        self._validate_structure(config)
        self._validate_assignment_section(config.get('assignment', {}))
        self._validate_context_section(config.get('context', {}))
        self._validate_rubric_section(config.get('rubric', {}))
        self._validate_github_section(config.get('github_integration', {}))
        
        # Cross-validation
        self._validate_cross_references(config)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors, self.warnings
    
    def _validate_structure(self, config: Dict[str, Any]):
        """Validate top-level structure"""
        required_sections = ['assignment', 'context', 'rubric']
        
        for section in required_sections:
            if section not in config:
                self.errors.append(f"Missing required section: '{section}'")
            elif not isinstance(config[section], dict):
                self.errors.append(f"Section '{section}' must be a dictionary")
    
    def _validate_assignment_section(self, assignment: Dict[str, Any]):
        """Validate assignment section"""
        required_fields = ['name', 'description', 'type', 'total_points']
        
        for field in required_fields:
            if field not in assignment:
                self.errors.append(f"Missing required field: 'assignment.{field}'")
        
        # Validate specific fields
        if 'name' in assignment:
            if not isinstance(assignment['name'], str) or not assignment['name'].strip():
                self.errors.append("'assignment.name' must be a non-empty string")
        
        if 'description' in assignment:
            if not isinstance(assignment['description'], str) or not assignment['description'].strip():
                self.errors.append("'assignment.description' must be a non-empty string")
        
        if 'type' in assignment:
            valid_types = ['python_application', 'web_application', 'data_analysis', 'machine_learning']
            if assignment['type'] not in valid_types and not isinstance(assignment['type'], str):
                self.warnings.append(f"'assignment.type' is not a standard type. Consider using one of: {', '.join(valid_types)}")
        
        if 'total_points' in assignment:
            if not isinstance(assignment['total_points'], int) or assignment['total_points'] <= 0:
                self.errors.append("'assignment.total_points' must be a positive integer")
    
    def _validate_context_section(self, context: Dict[str, Any]):
        """Validate context section"""
        required_fields = ['requirements', 'required_functions', 'file_expectations']
        
        for field in required_fields:
            if field not in context:
                self.errors.append(f"Missing required field: 'context.{field}'")
        
        # Validate requirements
        if 'requirements' in context:
            if not isinstance(context['requirements'], list):
                self.errors.append("'context.requirements' must be a list")
            elif len(context['requirements']) == 0:
                self.warnings.append("'context.requirements' is empty")
            else:
                for i, req in enumerate(context['requirements']):
                    if not isinstance(req, str) or not req.strip():
                        self.errors.append(f"'context.requirements[{i}]' must be a non-empty string")
        
        # Validate required_functions
        if 'required_functions' in context:
            if not isinstance(context['required_functions'], list):
                self.errors.append("'context.required_functions' must be a list")
            else:
                for i, func in enumerate(context['required_functions']):
                    if not isinstance(func, dict):
                        self.errors.append(f"'context.required_functions[{i}]' must be a dictionary")
                        continue
                    
                    required_func_fields = ['name', 'signature', 'description']
                    for field in required_func_fields:
                        if field not in func:
                            self.errors.append(f"Missing field 'context.required_functions[{i}].{field}'")
                        elif not isinstance(func[field], str) or not func[field].strip():
                            self.errors.append(f"'context.required_functions[{i}].{field}' must be a non-empty string")
        
        # Validate file_expectations
        if 'file_expectations' in context:
            if not isinstance(context['file_expectations'], dict):
                self.errors.append("'context.file_expectations' must be a dictionary")
            else:
                valid_expectations = ['required', 'optional']
                for file_type, expectation in context['file_expectations'].items():
                    if expectation not in valid_expectations:
                        self.errors.append(f"'context.file_expectations.{file_type}' must be one of: {', '.join(valid_expectations)}")
    
    def _validate_rubric_section(self, rubric: Dict[str, Any]):
        """Validate rubric section"""
        if not rubric:
            self.errors.append("Rubric section is empty")
            return
        
        total_weight = 0
        total_max_score = 0
        
        for criterion, details in rubric.items():
            if not isinstance(details, dict):
                self.errors.append(f"'rubric.{criterion}' must be a dictionary")
                continue
            
            required_fields = ['weight', 'max_score', 'criteria']
            for field in required_fields:
                if field not in details:
                    self.errors.append(f"Missing field 'rubric.{criterion}.{field}'")
            
            # Validate weight
            if 'weight' in details:
                if not isinstance(details['weight'], (int, float)) or details['weight'] <= 0:
                    self.errors.append(f"'rubric.{criterion}.weight' must be a positive number")
                else:
                    total_weight += details['weight']
            
            # Validate max_score
            if 'max_score' in details:
                if not isinstance(details['max_score'], (int, float)) or details['max_score'] <= 0:
                    self.errors.append(f"'rubric.{criterion}.max_score' must be a positive number")
                else:
                    total_max_score += details['max_score']
            
            # Validate criteria
            if 'criteria' in details:
                if not isinstance(details['criteria'], str) or not details['criteria'].strip():
                    self.errors.append(f"'rubric.{criterion}.criteria' must be a non-empty string")
        
        # Check total weight
        if abs(total_weight - 100) > 0.1:
            self.errors.append(f"Rubric weights must sum to 100%, got {total_weight}%")
        
        return total_max_score
    
    def _validate_github_section(self, github: Dict[str, Any]):
        """Validate GitHub integration section"""
        if not github:
            self.warnings.append("No GitHub integration configuration found")
            return
        
        # Validate enabled field
        if 'enabled' in github:
            if not isinstance(github['enabled'], bool):
                self.errors.append("'github_integration.enabled' must be a boolean")
        
        # If enabled, validate other fields
        if github.get('enabled', False):
            if 'minimum_commits' in github:
                if not isinstance(github['minimum_commits'], int) or github['minimum_commits'] < 0:
                    self.errors.append("'github_integration.minimum_commits' must be a non-negative integer")
            
            bool_fields = ['repository_analysis', 'readme_comparison']
            for field in bool_fields:
                if field in github and not isinstance(github[field], bool):
                    self.errors.append(f"'github_integration.{field}' must be a boolean")
    
    def _validate_cross_references(self, config: Dict[str, Any]):
        """Validate cross-references between sections"""
        # Check total points matches rubric
        if 'assignment' in config and 'rubric' in config:
            assignment_total = config['assignment'].get('total_points')
            rubric_total = sum(details.get('max_score', 0) for details in config['rubric'].values())
            
            if assignment_total and abs(assignment_total - rubric_total) > 0.1:
                self.errors.append(f"Assignment total points ({assignment_total}) doesn't match rubric total ({rubric_total})")
        
        # Check GitHub expectations match GitHub config
        if 'context' in config and 'github_integration' in config:
            file_expectations = config['context'].get('file_expectations', {})
            github_enabled = config['github_integration'].get('enabled', False)
            
            if 'github' in file_expectations and file_expectations['github'] == 'required' and not github_enabled:
                self.warnings.append("GitHub files are required but GitHub integration is disabled")


def validate_single_config(config_path: str) -> bool:
    """Validate a single configuration file and print results"""
    validator = ConfigValidator()
    is_valid, errors, warnings = validator.validate_assignment_config(config_path)
    
    print(f"Validating: {config_path}")
    print("-" * 50)
    
    if errors:
        print("❌ ERRORS:")
        for error in errors:
            print(f"  • {error}")
    
    if warnings:
        print("⚠️  WARNINGS:")
        for warning in warnings:
            print(f"  • {warning}")
    
    if is_valid:
        print("✅ Configuration is valid!")
    else:
        print("❌ Configuration has errors and needs to be fixed")
    
    print()
    return is_valid


def validate_all_assignments(assignments_dir: str = "assignments") -> bool:
    """Validate all assignment configurations"""
    assignments_path = Path(assignments_dir)
    
    if not assignments_path.exists():
        print(f"❌ Assignments directory not found: {assignments_path}")
        return False
    
    config_files = list(assignments_path.glob("*/config.yaml"))
    
    if not config_files:
        print(f"❌ No assignment configurations found in {assignments_path}")
        return False
    
    print(f"🔍 Validating {len(config_files)} assignment configurations...")
    print("=" * 60)
    
    all_valid = True
    
    for config_file in config_files:
        valid = validate_single_config(config_file)
        all_valid = all_valid and valid
    
    print("=" * 60)
    if all_valid:
        print("✅ All configurations are valid!")
    else:
        print("❌ Some configurations have errors")
    
    return all_valid


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate assignment configurations")
    parser.add_argument('config_path', nargs='?', help='Path to specific config file to validate')
    parser.add_argument('--all', action='store_true', help='Validate all assignments in assignments/ directory')
    parser.add_argument('--assignments-dir', default='assignments', help='Path to assignments directory (default: assignments)')
    
    args = parser.parse_args()
    
    if args.all:
        success = validate_all_assignments(args.assignments_dir)
        sys.exit(0 if success else 1)
    elif args.config_path:
        success = validate_single_config(args.config_path)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()