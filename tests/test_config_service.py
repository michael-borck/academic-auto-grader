#!/usr/bin/env python3
"""
Unit tests for ConfigService

Tests the GUI configuration service functionality.
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Add GUI modules to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GUI_DIR = PROJECT_ROOT / "gui"
sys.path.insert(0, str(GUI_DIR))

from app.services.config_service import ConfigService


class TestConfigService(unittest.TestCase):
    """Test cases for ConfigService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = ConfigService()
    
    def test_load_assignments(self):
        """Test loading assignments"""
        assignments = self.service.load_assignments()
        
        # Should have at least the weatherwise assignment
        self.assertGreater(len(assignments), 0)
        
        # Check structure of first assignment
        assignment = assignments[0]
        required_keys = ['name', 'display_name', 'description', 'type', 'total_points', 'github_enabled']
        for key in required_keys:
            self.assertIn(key, assignment)
    
    def test_get_assignment_by_name(self):
        """Test getting specific assignment"""
        assignment = self.service.get_assignment_by_name('weatherwise')
        self.assertIsNotNone(assignment)
        self.assertEqual(assignment['name'], 'weatherwise')
        
        # Test non-existent assignment
        assignment = self.service.get_assignment_by_name('nonexistent')
        self.assertIsNone(assignment)
    
    def test_validate_paths_nonexistent(self):
        """Test path validation with non-existent paths"""
        validation = self.service.validate_paths('/nonexistent/path')
        
        self.assertFalse(validation['submissions_valid'])
        self.assertFalse(validation['overall_valid'])
        self.assertIn('does not exist', validation['submissions_message'])
    
    def test_validate_paths_empty_directory(self):
        """Test path validation with empty directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            validation = self.service.validate_paths(temp_dir)
            
            self.assertFalse(validation['submissions_valid'])
            self.assertFalse(validation['overall_valid'])
            self.assertIn('No ZIP files', validation['submissions_message'])
            self.assertEqual(validation['submissions_count'], 0)
    
    def test_validate_paths_with_zip_files(self):
        """Test path validation with ZIP files"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test ZIP file
            test_zip = os.path.join(temp_dir, 'test_student.zip')
            with open(test_zip, 'w') as f:
                f.write('test')  # Not a real ZIP, but file exists
            
            validation = self.service.validate_paths(temp_dir)
            
            self.assertTrue(validation['submissions_valid'])
            self.assertTrue(validation['overall_valid'])
            self.assertEqual(validation['submissions_count'], 1)
            self.assertIn('Found 1 ZIP files', validation['submissions_message'])
    
    def test_validate_assignment_config(self):
        """Test assignment configuration validation"""
        validation = self.service.validate_assignment_config('weatherwise')
        
        self.assertTrue(validation['valid'])
        self.assertEqual(len(validation['errors']), 0)
    
    def test_get_assignment_summary(self):
        """Test assignment summary generation"""
        summary = self.service.get_assignment_summary('weatherwise')
        
        self.assertIn('WeatherWise', summary)
        self.assertIn('Points:', summary)
        self.assertIn('GitHub:', summary)
        
        # Test non-existent assignment
        summary = self.service.get_assignment_summary('nonexistent')
        self.assertIn('not found', summary)


if __name__ == '__main__':
    unittest.main()