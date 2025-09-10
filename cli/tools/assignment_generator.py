#!/usr/bin/env python3
"""
Interactive Assignment Configuration Generator
Creates new assignment configurations through guided prompts
"""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any


class AssignmentGenerator:
    """Generates assignment configurations interactively"""
    
    def __init__(self, assignments_dir: str = "assignments"):
        self.assignments_dir = Path(assignments_dir)
        self.assignments_dir.mkdir(exist_ok=True)
    
    def create_assignment(self) -> str:
        """Create a new assignment configuration interactively"""
        print("🎯 Assignment Configuration Generator")
        print("=" * 50)
        
        # Get basic assignment info
        assignment_name = self._get_assignment_name()
        assignment_info = self._get_assignment_info()
        context = self._get_context_info()
        rubric = self._get_rubric_info()
        github_config = self._get_github_config()
        
        # Build complete configuration
        config = {
            'assignment': assignment_info,
            'context': context,
            'rubric': rubric,
            'github_integration': github_config
        }
        
        # Validate configuration
        self._validate_config(config)
        
        # Save configuration
        config_path = self._save_config(assignment_name, config)
        
        print(f"\n✅ Assignment configuration created: {config_path}")
        print(f"🚀 You can now use: grader grade submissions/ --assignment {assignment_name}")
        
        return assignment_name
    
    def _get_assignment_name(self) -> str:
        """Get assignment name and validate uniqueness"""
        while True:
            name = input("\n📝 Assignment identifier (lowercase, no spaces): ").strip().lower()
            
            if not name:
                print("❌ Assignment name cannot be empty")
                continue
            
            if not name.replace('_', '').replace('-', '').isalnum():
                print("❌ Assignment name can only contain letters, numbers, hyphens, and underscores")
                continue
            
            assignment_dir = self.assignments_dir / name
            if assignment_dir.exists():
                overwrite = input(f"⚠️  Assignment '{name}' already exists. Overwrite? (y/N): ").lower()
                if overwrite != 'y':
                    continue
            
            return name
    
    def _get_assignment_info(self) -> Dict[str, Any]:
        """Get basic assignment information"""
        print("\n📋 Basic Assignment Information")
        print("-" * 30)
        
        name = input("Assignment title (e.g., 'WeatherWise'): ").strip()
        description = input("Brief description: ").strip()
        
        print("\nAssignment types:")
        print("1. python_application")
        print("2. web_application") 
        print("3. data_analysis")
        print("4. machine_learning")
        print("5. other")
        
        while True:
            type_choice = input("Select type (1-5): ").strip()
            types = ["python_application", "web_application", "data_analysis", "machine_learning", "other"]
            
            try:
                assignment_type = types[int(type_choice) - 1]
                break
            except (ValueError, IndexError):
                print("❌ Please enter a number between 1-5")
        
        if assignment_type == "other":
            assignment_type = input("Enter custom type: ").strip()
        
        while True:
            try:
                total_points = int(input("Total points (default: 100): ") or "100")
                if total_points <= 0:
                    print("❌ Total points must be positive")
                    continue
                break
            except ValueError:
                print("❌ Please enter a valid number")
        
        return {
            'name': name,
            'description': description,
            'type': assignment_type,
            'total_points': total_points
        }
    
    def _get_context_info(self) -> Dict[str, Any]:
        """Get assignment context and requirements"""
        print("\n🎯 Assignment Context")
        print("-" * 20)
        
        print("Enter assignment requirements (one per line, empty line to finish):")
        requirements = []
        while True:
            req = input(f"  Requirement {len(requirements) + 1}: ").strip()
            if not req:
                break
            requirements.append(req)
        
        print("\nEnter required functions (empty name to finish):")
        required_functions = []
        while True:
            name = input(f"  Function {len(required_functions) + 1} name: ").strip()
            if not name:
                break
            
            signature = input(f"    Signature (e.g., {name}(param1, param2)): ").strip()
            description = input(f"    Description: ").strip()
            
            required_functions.append({
                'name': name,
                'signature': signature or f"{name}()",
                'description': description or f"Implementation of {name} function"
            })
        
        print("\nFile expectations:")
        file_expectations = {}
        
        files = ['notebook', 'conversation_files', 'readme', 'github']
        for file_type in files:
            while True:
                required = input(f"  {file_type} (required/optional/skip): ").lower()
                if required in ['required', 'optional', 'skip']:
                    if required != 'skip':
                        file_expectations[file_type] = required
                    break
                print("❌ Please enter 'required', 'optional', or 'skip'")
        
        return {
            'requirements': requirements,
            'required_functions': required_functions,
            'file_expectations': file_expectations
        }
    
    def _get_rubric_info(self) -> Dict[str, Any]:
        """Get rubric configuration"""
        print("\n📊 Rubric Configuration")
        print("-" * 22)
        
        print("Enter rubric criteria (weights must sum to 100%):")
        
        rubric = {}
        total_weight = 0
        
        # Default criteria
        default_criteria = [
            ("functionality", "Core features work; required functions implemented correctly"),
            ("code_quality", "Well-structured, readable code with proper documentation"),
            ("technical_implementation", "Appropriate use of libraries and efficient implementation")
        ]
        
        print("\nDefault criteria (press Enter to use, or type new description):")
        for criterion, default_desc in default_criteria:
            print(f"\n{criterion.replace('_', ' ').title()}:")
            
            description = input(f"  Description (default: {default_desc}): ").strip()
            if not description:
                description = default_desc
            
            while True:
                try:
                    weight = int(input(f"  Weight % (remaining: {100 - total_weight}%): "))
                    if weight <= 0 or weight > 100 - total_weight:
                        print(f"❌ Weight must be between 1 and {100 - total_weight}")
                        continue
                    break
                except ValueError:
                    print("❌ Please enter a valid number")
            
            rubric[criterion] = {
                'weight': weight,
                'max_score': weight,  # Default to same as weight
                'criteria': description
            }
            total_weight += weight
        
        # Additional criteria
        print(f"\nAdd custom criteria (remaining weight: {100 - total_weight}%):")
        while total_weight < 100:
            criterion = input("  Criterion name (empty to finish): ").strip().lower().replace(' ', '_')
            if not criterion:
                break
            
            description = input(f"  Description for {criterion}: ").strip()
            
            while True:
                try:
                    weight = int(input(f"  Weight % (remaining: {100 - total_weight}%): "))
                    if weight <= 0 or weight > 100 - total_weight:
                        print(f"❌ Weight must be between 1 and {100 - total_weight}")
                        continue
                    break
                except ValueError:
                    print("❌ Please enter a valid number")
            
            rubric[criterion] = {
                'weight': weight,
                'max_score': weight,
                'criteria': description
            }
            total_weight += weight
        
        if total_weight < 100:
            print(f"⚠️  Warning: Total weight is {total_weight}%, not 100%")
            adjust = input("Add remaining weight to 'functionality'? (Y/n): ").lower()
            if adjust != 'n':
                if 'functionality' in rubric:
                    rubric['functionality']['weight'] += (100 - total_weight)
                    rubric['functionality']['max_score'] += (100 - total_weight)
        
        return rubric
    
    def _get_github_config(self) -> Dict[str, Any]:
        """Get GitHub integration configuration"""
        print("\n🐙 GitHub Integration")
        print("-" * 19)
        
        enabled = input("Enable GitHub integration? (Y/n): ").lower() != 'n'
        
        if enabled:
            while True:
                try:
                    min_commits = int(input("Minimum required commits (default: 15): ") or "15")
                    if min_commits < 0:
                        print("❌ Minimum commits cannot be negative")
                        continue
                    break
                except ValueError:
                    print("❌ Please enter a valid number")
            
            repo_analysis = input("Enable repository analysis? (Y/n): ").lower() != 'n'
            readme_comparison = input("Compare README files? (Y/n): ").lower() != 'n'
            
            return {
                'enabled': True,
                'minimum_commits': min_commits,
                'repository_analysis': repo_analysis,
                'readme_comparison': readme_comparison
            }
        else:
            return {
                'enabled': False,
                'minimum_commits': 10,
                'repository_analysis': True,
                'readme_comparison': True
            }
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate the configuration"""
        # Check total weight
        total_weight = sum(details['weight'] for details in config['rubric'].values())
        if abs(total_weight - 100) > 0.1:
            raise ValueError(f"Rubric weights must sum to 100%, got {total_weight}%")
        
        # Check total points match rubric
        expected_total = sum(details['max_score'] for details in config['rubric'].values())
        if config['assignment']['total_points'] != expected_total:
            print(f"⚠️  Adjusting total points from {config['assignment']['total_points']} to {expected_total} to match rubric")
            config['assignment']['total_points'] = expected_total
    
    def _save_config(self, assignment_name: str, config: Dict[str, Any]) -> str:
        """Save configuration to file"""
        assignment_dir = self.assignments_dir / assignment_name
        assignment_dir.mkdir(exist_ok=True)
        
        config_path = assignment_dir / "config.yaml"
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
        
        return str(config_path)
    
    def create_from_existing(self, existing_assignment: str) -> str:
        """Create new assignment based on existing one"""
        print(f"📋 Creating assignment based on: {existing_assignment}")
        
        # Load existing config
        existing_config_path = self.assignments_dir / existing_assignment / "config.yaml"
        
        if not existing_config_path.exists():
            raise ValueError(f"Existing assignment config not found: {existing_config_path}")
        
        with open(existing_config_path, 'r') as f:
            existing_config = yaml.safe_load(f)
        
        # Get new assignment name
        new_name = self._get_assignment_name()
        
        # Update basic info
        print(f"\nUpdating assignment info (current: {existing_config['assignment']['name']}):")
        name = input(f"New title (default: {existing_config['assignment']['name']}): ").strip()
        if name:
            existing_config['assignment']['name'] = name
        
        description = input(f"New description (default: {existing_config['assignment']['description']}): ").strip()
        if description:
            existing_config['assignment']['description'] = description
        
        # Save new config
        config_path = self._save_config(new_name, existing_config)
        
        print(f"\n✅ Assignment configuration created: {config_path}")
        print(f"🚀 You can now use: grader grade submissions/ --assignment {new_name}")
        
        return new_name


def main():
    """Interactive main function"""
    print("🎯 Assignment Configuration Generator")
    print("=" * 40)
    
    generator = AssignmentGenerator()
    
    print("Choose an option:")
    print("1. Create new assignment from scratch")
    print("2. Create assignment based on existing one")
    print("3. Exit")
    
    while True:
        choice = input("\nSelect option (1-3): ").strip()
        
        if choice == "1":
            try:
                generator.create_assignment()
                break
            except KeyboardInterrupt:
                print("\n❌ Cancelled by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        elif choice == "2":
            try:
                from config_loader import ConfigLoader
                config_loader = ConfigLoader()
                assignments = config_loader.list_available_assignments()
                
                if not assignments:
                    print("❌ No existing assignments found")
                    continue
                
                print("\nExisting assignments:")
                for i, assignment in enumerate(assignments, 1):
                    print(f"  {i}. {assignment}")
                
                while True:
                    try:
                        idx = int(input(f"Select assignment (1-{len(assignments)}): ")) - 1
                        if 0 <= idx < len(assignments):
                            existing = assignments[idx]
                            break
                        else:
                            print(f"❌ Please enter a number between 1 and {len(assignments)}")
                    except ValueError:
                        print("❌ Please enter a valid number")
                
                generator.create_from_existing(existing)
                break
                
            except KeyboardInterrupt:
                print("\n❌ Cancelled by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                break
        
        elif choice == "3":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Please enter 1, 2, or 3")


if __name__ == "__main__":
    main()