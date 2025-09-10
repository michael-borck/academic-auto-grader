"""
Configuration Service for GUI Application

Provides configuration management functionality for the GUI,
wrapping the existing CLI ConfigLoader for GUI use.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add CLI core to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CLI_CORE_DIR = PROJECT_ROOT / "cli" / "core"
sys.path.insert(0, str(CLI_CORE_DIR))

try:
    from config_loader import ConfigLoader
except ImportError as e:
    raise ImportError(f"Could not import ConfigLoader from CLI: {e}")


class ConfigService:
    """GUI Configuration Service
    
    Provides configuration management for the GUI application,
    including assignment loading, path validation, and preferences.
    """
    
    def __init__(self, assignments_dir: str = None):
        """Initialize the configuration service
        
        Args:
            assignments_dir: Path to assignments directory (relative to project root)
        """
        if assignments_dir is None:
            assignments_dir = str(PROJECT_ROOT / "assignments")
        
        self.assignments_dir = assignments_dir
        self.config_loader = ConfigLoader(assignments_dir)
        self._cached_assignments = None
    
    def load_assignments(self) -> List[Dict[str, Any]]:
        """Load all available assignments with metadata
        
        Returns:
            List of assignment dictionaries with metadata for GUI display
        """
        try:
            assignment_names = self.config_loader.list_available_assignments()
            assignments = []
            
            for name in assignment_names:
                try:
                    config = self.config_loader.load_assignment_config(name)
                    
                    # Extract key information for GUI display
                    assignment_info = {
                        'name': name,
                        'display_name': config['assignment']['name'],
                        'description': config['assignment']['description'],
                        'type': config['assignment']['type'],
                        'total_points': config['assignment']['total_points'],
                        'github_enabled': config.get('github_integration', {}).get('enabled', False),
                        'required_functions': len(config['context'].get('required_functions', [])),
                        'rubric_criteria': len(config.get('rubric', {})),
                        'config': config  # Full config for detailed access
                    }
                    assignments.append(assignment_info)
                    
                except Exception as e:
                    # Log error but continue with other assignments
                    print(f"Warning: Could not load assignment '{name}': {e}")
                    continue
            
            self._cached_assignments = assignments
            return assignments
            
        except Exception as e:
            print(f"Error loading assignments: {e}")
            return []
    
    def get_assignment_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get specific assignment by name
        
        Args:
            name: Assignment identifier
            
        Returns:
            Assignment dictionary or None if not found
        """
        assignments = self.load_assignments()
        for assignment in assignments:
            if assignment['name'] == name:
                return assignment
        return None
    
    def validate_paths(self, submissions_folder: str, roster_file: str = None) -> Dict[str, Any]:
        """Validate user input paths
        
        Args:
            submissions_folder: Path to submissions folder
            roster_file: Optional path to roster CSV file
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            'submissions_valid': False,
            'submissions_message': '',
            'submissions_count': 0,
            'roster_valid': True,  # Optional, so valid by default
            'roster_message': '',
            'overall_valid': False
        }
        
        # Validate submissions folder
        if not submissions_folder or not submissions_folder.strip():
            validation['submissions_message'] = "Please select a submissions folder"
        elif not os.path.exists(submissions_folder):
            validation['submissions_message'] = f"Folder does not exist: {submissions_folder}"
        elif not os.path.isdir(submissions_folder):
            validation['submissions_message'] = f"Path is not a directory: {submissions_folder}"
        else:
            # Count ZIP files in folder
            try:
                zip_files = [f for f in os.listdir(submissions_folder) if f.endswith('.zip')]
                validation['submissions_count'] = len(zip_files)
                
                if len(zip_files) == 0:
                    validation['submissions_message'] = f"No ZIP files found in {submissions_folder}"
                else:
                    validation['submissions_valid'] = True
                    validation['submissions_message'] = f"Found {len(zip_files)} ZIP files"
                    
            except PermissionError:
                validation['submissions_message'] = f"Permission denied accessing: {submissions_folder}"
            except Exception as e:
                validation['submissions_message'] = f"Error reading folder: {str(e)}"
        
        # Validate roster file (optional)
        if roster_file and roster_file.strip():
            if not os.path.exists(roster_file):
                validation['roster_valid'] = False
                validation['roster_message'] = f"Roster file does not exist: {roster_file}"
            elif not roster_file.lower().endswith('.csv'):
                validation['roster_valid'] = False
                validation['roster_message'] = f"Roster file must be a CSV file: {roster_file}"
            else:
                try:
                    # Try to read first few lines to validate CSV
                    with open(roster_file, 'r') as f:
                        lines = f.readlines()[:5]  # Read first 5 lines
                    validation['roster_message'] = f"Roster file valid ({len(lines)} lines preview)"
                except Exception as e:
                    validation['roster_valid'] = False
                    validation['roster_message'] = f"Error reading roster file: {str(e)}"
        else:
            validation['roster_message'] = "No roster file selected (optional)"
        
        # Overall validation
        validation['overall_valid'] = validation['submissions_valid'] and validation['roster_valid']
        
        return validation
    
    def get_assignments_directory(self) -> str:
        """Get the assignments directory path"""
        return self.assignments_dir
    
    def refresh_assignments(self) -> List[Dict[str, Any]]:
        """Refresh the assignments cache and return updated list"""
        self._cached_assignments = None
        return self.load_assignments()
    
    def validate_assignment_config(self, assignment_name: str) -> Dict[str, Any]:
        """Validate a specific assignment configuration
        
        Args:
            assignment_name: Name of assignment to validate
            
        Returns:
            Validation results with any errors or warnings
        """
        try:
            config = self.config_loader.load_assignment_config(assignment_name)
            
            # Basic validation - the ConfigLoader already does most validation
            validation = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            # Check for common issues
            if not config.get('context', {}).get('required_functions'):
                validation['warnings'].append("No required functions specified")
            
            if not config.get('context', {}).get('requirements'):
                validation['warnings'].append("No requirements specified")
            
            # Check GitHub integration configuration
            github_config = config.get('github_integration', {})
            if github_config.get('enabled') and not os.getenv('GITHUB_TOKEN'):
                validation['warnings'].append("GitHub integration enabled but no GITHUB_TOKEN environment variable found")
            
            return validation
            
        except Exception as e:
            return {
                'valid': False,
                'errors': [f"Configuration error: {str(e)}"],
                'warnings': []
            }
    
    def get_assignment_summary(self, assignment_name: str) -> str:
        """Get a text summary of an assignment for display
        
        Args:
            assignment_name: Name of assignment
            
        Returns:
            Formatted text summary
        """
        assignment = self.get_assignment_by_name(assignment_name)
        if not assignment:
            return f"Assignment '{assignment_name}' not found"
        
        summary_lines = [
            f"📋 {assignment['display_name']}",
            f"Type: {assignment['type'].replace('_', ' ').title()}",
            f"Points: {assignment['total_points']}",
            f"Functions: {assignment['required_functions']} required",
            f"Rubric: {assignment['rubric_criteria']} criteria",
            f"GitHub: {'✅ Enabled' if assignment['github_enabled'] else '❌ Disabled'}",
            "",
            f"Description: {assignment['description']}"
        ]
        
        return "\n".join(summary_lines)


def main():
    """Test the configuration service"""
    print("Testing ConfigService...")
    
    service = ConfigService()
    
    # Test loading assignments
    assignments = service.load_assignments()
    print(f"Found {len(assignments)} assignments:")
    for assignment in assignments:
        print(f"  - {assignment['name']}: {assignment['display_name']}")
    
    # Test path validation
    validation = service.validate_paths("/nonexistent/path")
    print(f"Path validation test: {validation}")
    
    # Test assignment summary
    if assignments:
        summary = service.get_assignment_summary(assignments[0]['name'])
        print(f"Assignment summary:\n{summary}")


if __name__ == "__main__":
    main()