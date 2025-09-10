#!/usr/bin/env python3
"""
Template-based prompt builder for automated grading.
Uses Jinja2 templates to generate grading prompts from configuration.
"""

import os
from pathlib import Path
from typing import Dict, Any
from jinja2 import Environment, FileSystemLoader, Template


class PromptBuilder:
    """Builds grading prompts using Jinja2 templates"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['default'] = self._default_filter
    
    def build_grading_prompt(self, 
                           assignment_config: Dict[str, Any],
                           submission_content: Dict[str, Any]) -> str:
        """Build complete grading prompt from config and submission"""
        
        # Load main template
        template = self.env.get_template('base_prompt.j2')
        
        # Prepare template context
        context = self._prepare_template_context(assignment_config, submission_content)
        
        # Render template
        prompt = template.render(context)
        
        return prompt
    
    def _prepare_template_context(self, 
                                assignment_config: Dict[str, Any],
                                submission_content: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context variables for template rendering"""
        
        # Extract notebook analysis
        notebook_analysis = self._analyze_notebook_content(
            submission_content.get('notebook_content', {})
        )
        
        # Build context
        context = {
            # Assignment configuration
            'assignment': assignment_config['assignment'],
            'rubric': assignment_config['rubric'],
            'github_integration': assignment_config.get('github_integration', {'enabled': False}),
            
            # Submission data
            'submission': {
                'student_id': submission_content['student_id']
            },
            
            # GitHub information
            'github_info': submission_content.get('github_info', {}),
            
            # Content analysis
            'functions_found': list(notebook_analysis['function_implementations'].keys()),
            'function_implementations': notebook_analysis['function_implementations'],
            'code_cells': notebook_analysis['code_cells'],
            'markdown_cells': notebook_analysis['markdown_cells'],
            'imports': notebook_analysis['imports'],
            
            # Files and documents
            'conversation_files': submission_content.get('conversation_files', []),
            'additional_documents': submission_content.get('additional_documents', []),
            'readme_content': submission_content.get('readme_content', ''),
            
            # Assignment-specific context
            'assignment_requirements': assignment_config['context']['requirements'],
            'required_functions': assignment_config['context']['required_functions']
        }
        
        return context
    
    def _analyze_notebook_content(self, notebook_content) -> Dict[str, Any]:
        """Safely analyze notebook content regardless of format"""
        if isinstance(notebook_content, str):
            # Error case - notebook parsing failed
            return {
                "function_implementations": {},
                "code_cells": [],
                "markdown_cells": [],
                "imports": [],
                "parse_error": notebook_content
            }
        else:
            # Normal case - return as-is but ensure all keys exist
            return {
                "function_implementations": notebook_content.get("function_implementations", {}),
                "code_cells": notebook_content.get("code_cells", []),
                "markdown_cells": notebook_content.get("markdown_cells", []),
                "imports": notebook_content.get("imports", []),
                "parse_error": None
            }
    
    def _default_filter(self, value, default_value=''):
        """Jinja2 filter for default values"""
        return value if value is not None else default_value
    
    def estimate_prompt_length(self, prompt: str) -> Dict[str, int]:
        """Estimate token length of prompt"""
        # Rough estimation: ~4 characters per token for English text
        estimated_tokens = len(prompt) // 4
        
        return {
            'characters': len(prompt),
            'estimated_tokens': estimated_tokens,
            'words': len(prompt.split())
        }
    
    def validate_templates(self) -> Dict[str, Any]:
        """Validate that all required templates exist and are valid"""
        required_templates = [
            'base_prompt.j2',
            'github_analysis.j2',
            'function_analysis.j2',
            'notebook_structure.j2',
            'conversation_analysis.j2',
            'additional_documents.j2',
            'readme_analysis.j2',
            'code_sample.j2'
        ]
        
        validation_results = {
            'valid': True,
            'missing_templates': [],
            'template_errors': [],
            'templates_found': []
        }
        
        for template_name in required_templates:
            template_path = self.templates_dir / template_name
            
            if not template_path.exists():
                validation_results['missing_templates'].append(template_name)
                validation_results['valid'] = False
            else:
                validation_results['templates_found'].append(template_name)
                
                # Try to load template to check for syntax errors
                try:
                    self.env.get_template(template_name)
                except Exception as e:
                    validation_results['template_errors'].append({
                        'template': template_name,
                        'error': str(e)
                    })
                    validation_results['valid'] = False
        
        return validation_results


def main():
    """Test the prompt builder"""
    from config_loader import ConfigLoader
    
    # Test with sample data
    config_loader = ConfigLoader('../assignments')
    assignments = config_loader.list_available_assignments()
    
    if not assignments:
        print("No assignments found for testing")
        return
    
    # Load assignment config
    assignment_config = config_loader.load_assignment_config(assignments[0])
    
    # Create sample submission content
    sample_submission = {
        'student_id': 'test_student',
        'notebook_content': {
            'function_implementations': {
                'get_weather_data': 'def get_weather_data():\n    pass',
                'parse_weather_question': 'def parse_weather_question():\n    pass'
            },
            'code_cells': [{'code': 'import requests\nprint("hello")'}],
            'markdown_cells': ['# Weather App\nThis is my weather app.'],
            'imports': ['import requests', 'import json']
        },
        'conversation_files': [
            {'filename': 'conversation1.txt', 'content': 'User: How do I get weather data?\nAssistant: You can use an API...'}
        ],
        'readme_content': '# My Weather App\nThis app gets weather data.',
        'github_info': {
            'accessible': True,
            'url': 'https://github.com/student/weather-app',
            'repository_info': {'name': 'weather-app', 'description': 'Weather application'},
            'commit_analysis': {'total_commits': 20, 'commit_messages': ['Initial commit', 'Add weather API']},
            'repository_structure': {'files': ['main.py', 'README.md'], 'folders': ['data']}
        }
    }
    
    # Build prompt
    builder = PromptBuilder('../templates')
    
    # Validate templates first
    validation = builder.validate_templates()
    print(f"Template validation: {'PASSED' if validation['valid'] else 'FAILED'}")
    
    if not validation['valid']:
        print(f"Missing templates: {validation['missing_templates']}")
        print(f"Template errors: {validation['template_errors']}")
        return
    
    # Build prompt
    prompt = builder.build_grading_prompt(assignment_config, sample_submission)
    
    # Show statistics
    stats = builder.estimate_prompt_length(prompt)
    print(f"\nGenerated prompt:")
    print(f"- Characters: {stats['characters']:,}")
    print(f"- Estimated tokens: {stats['estimated_tokens']:,}")
    print(f"- Words: {stats['words']:,}")
    
    print(f"\nFirst 500 characters:")
    print(prompt[:500] + "...")


if __name__ == "__main__":
    main()