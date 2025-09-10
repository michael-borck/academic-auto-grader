#!/usr/bin/env python3
"""
Configuration loader for the automated grading system.
Loads assignment configurations from YAML files.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Loads and validates assignment configurations"""
    
    def __init__(self, assignments_dir: str = "assignments"):
        self.assignments_dir = Path(assignments_dir)
    
    def load_assignment_config(self, assignment_name: str) -> Dict[str, Any]:
        """Load configuration for a specific assignment"""
        config_path = self.assignments_dir / assignment_name / "config.yaml"
        
        if not config_path.exists():
            raise ValueError(f"Assignment config not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Validate required fields
        self._validate_config(config, assignment_name)
        
        # Add computed fields
        config['assignment']['assignment_name'] = assignment_name
        config['assignment']['config_path'] = str(config_path)
        
        return config
    
    def list_available_assignments(self) -> list:
        """Get list of available assignments"""
        assignments = []
        
        if not self.assignments_dir.exists():
            return assignments
        
        for item in self.assignments_dir.iterdir():
            if item.is_dir():
                config_file = item / "config.yaml"
                if config_file.exists():
                    assignments.append(item.name)
        
        return sorted(assignments)
    
    def _validate_config(self, config: Dict[str, Any], assignment_name: str):
        """Validate configuration structure"""
        required_sections = ['assignment', 'context', 'rubric']
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section '{section}' in {assignment_name} config")
        
        # Validate assignment section
        assignment = config['assignment']
        required_assignment_fields = ['name', 'description', 'type', 'total_points']
        
        for field in required_assignment_fields:
            if field not in assignment:
                raise ValueError(f"Missing required field 'assignment.{field}' in {assignment_name} config")
        
        # Validate context section
        context = config['context']
        required_context_fields = ['requirements', 'required_functions', 'file_expectations']
        
        for field in required_context_fields:
            if field not in context:
                raise ValueError(f"Missing required field 'context.{field}' in {assignment_name} config")
        
        # Validate rubric section
        rubric = config['rubric']
        if not rubric:
            raise ValueError(f"Empty rubric section in {assignment_name} config")
        
        # Validate each rubric criterion
        total_weight = 0
        for criterion, details in rubric.items():
            required_rubric_fields = ['weight', 'max_score', 'criteria']
            
            for field in required_rubric_fields:
                if field not in details:
                    raise ValueError(f"Missing required field 'rubric.{criterion}.{field}' in {assignment_name} config")
            
            total_weight += details['weight']
        
        # Check total weight adds up to 100%
        if abs(total_weight - 100) > 0.1:  # Allow small floating point errors
            raise ValueError(f"Rubric weights must sum to 100%, got {total_weight}% in {assignment_name} config")
        
        # Validate total points matches rubric
        expected_total = sum(details['max_score'] for details in rubric.values())
        if assignment['total_points'] != expected_total:
            raise ValueError(f"Total points ({assignment['total_points']}) doesn't match rubric sum ({expected_total}) in {assignment_name} config")
    
    def get_rubric_weights(self, config: Dict[str, Any]) -> Dict[str, int]:
        """Extract rubric weights from config"""
        return {criterion: details['weight'] for criterion, details in config['rubric'].items()}
    
    def get_required_functions(self, config: Dict[str, Any]) -> list:
        """Extract required function names from config"""
        return [func['name'] for func in config['context']['required_functions']]
    
    def is_github_enabled(self, config: Dict[str, Any]) -> bool:
        """Check if GitHub integration is enabled for this assignment"""
        github_config = config.get('github_integration', {})
        return github_config.get('enabled', False)
    
    def get_github_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Get GitHub integration configuration"""
        return config.get('github_integration', {
            'enabled': False,
            'minimum_commits': 10,
            'repository_analysis': True,
            'readme_comparison': True
        })


def main():
    """Test the config loader"""
    loader = ConfigLoader()
    
    # List available assignments
    assignments = loader.list_available_assignments()
    print(f"Available assignments: {assignments}")
    
    if assignments:
        # Load first assignment as test
        config = loader.load_assignment_config(assignments[0])
        print(f"\nLoaded config for: {config['assignment']['name']}")
        print(f"Required functions: {loader.get_required_functions(config)}")
        print(f"GitHub enabled: {loader.is_github_enabled(config)}")


if __name__ == "__main__":
    main()