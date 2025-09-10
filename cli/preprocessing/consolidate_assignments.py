#!/usr/bin/env python3
"""
Student Assignment File Consolidator

This script processes student assignment files by:
1. Grouping files by student ID
2. Renaming files to <STUDENT_ID>.<original_extension>
3. Consolidating all files into a single zip per student
4. If a student has a zip file, extracting it and combining with other files
5. Creating final zip files named <STUDENT_ID>.zip

Usage: python consolidate_assignments.py [folder_path]
"""

import os
import re
import zipfile
import shutil
import tempfile
from pathlib import Path
from collections import defaultdict
import argparse


def extract_student_id(filename):
    """Extract student ID from filename using regex pattern."""
    # Pattern matches: Assignment 2 Submission_<STUDENT_ID>_attempt_...
    pattern = r'Assignment 2 Submission[s]?_(\d+)_attempt_'
    match = re.search(pattern, filename)
    return match.group(1) if match else None


def get_file_extension(filename):
    """Get the file extension, handling special cases."""
    # Handle files without extensions
    if '.' not in filename:
        return ''
    
    # Get the last part after the last dot
    ext = filename.split('.')[-1].lower()
    
    # Handle double extensions like .zip.zip
    if filename.lower().endswith('.zip.zip'):
        return 'zip'
    
    return ext


def is_zip_file(filename):
    """Check if file is a zip file based on extension."""
    return filename.lower().endswith('.zip')


def safely_extract_zip(zip_path, extract_to):
    """Safely extract zip file, handling potential issues."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # Check for potentially dangerous paths
            for member in zip_ref.namelist():
                if os.path.isabs(member) or ".." in member:
                    print(f"Warning: Skipping potentially unsafe path in {zip_path}: {member}")
                    continue
                zip_ref.extract(member, extract_to)
        return True
    except zipfile.BadZipFile:
        print(f"Error: {zip_path} is not a valid zip file")
        return False
    except Exception as e:
        print(f"Error extracting {zip_path}: {e}")
        return False


def collect_all_files_recursive(directory):
    """Recursively collect all files from a directory."""
    all_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            all_files.append(file_path)
    return all_files


def process_student_files(folder_path):
    """Main function to process all student files."""
    if not os.path.exists(folder_path):
        print(f"Error: Folder {folder_path} does not exist")
        return
    
    # Group files by student ID
    student_files = defaultdict(list)
    
    # Get all files in the folder
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            student_id = extract_student_id(filename)
            if student_id:
                student_files[student_id].append(filename)
            else:
                print(f"Warning: Could not extract student ID from {filename}")
    
    print(f"Found {len(student_files)} students with files")
    
    # Create output directory for processed files
    output_dir = os.path.join(folder_path, "processed_submissions")
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each student's files
    for student_id, files in student_files.items():
        print(f"\nProcessing student {student_id} ({len(files)} files)")
        
        # Create temporary directory for this student
        with tempfile.TemporaryDirectory() as temp_dir:
            student_temp_dir = os.path.join(temp_dir, student_id)
            os.makedirs(student_temp_dir, exist_ok=True)
            
            zip_files = []
            non_zip_files = []
            
            # Separate zip and non-zip files
            for filename in files:
                if is_zip_file(filename):
                    zip_files.append(filename)
                else:
                    non_zip_files.append(filename)
            
            # Process zip files first (extract contents)
            for zip_filename in zip_files:
                zip_path = os.path.join(folder_path, zip_filename)
                print(f"  Extracting: {zip_filename}")
                
                # Create subdirectory for this zip's contents
                zip_extract_dir = os.path.join(student_temp_dir, f"extracted_from_{zip_filename}")
                os.makedirs(zip_extract_dir, exist_ok=True)
                
                if safely_extract_zip(zip_path, zip_extract_dir):
                    # Collect all extracted files recursively
                    extracted_files = collect_all_files_recursive(zip_extract_dir)
                    
                    # Copy extracted files to student temp directory with proper names
                    for extracted_file_path in extracted_files:
                        # Get relative path from extraction directory
                        rel_path = os.path.relpath(extracted_file_path, zip_extract_dir)
                        
                        # Skip directories and hidden files
                        if os.path.isfile(extracted_file_path) and not os.path.basename(rel_path).startswith('.'):
                            # Get original extension
                            original_ext = get_file_extension(os.path.basename(extracted_file_path))
                            
                            # Create new filename
                            if original_ext:
                                new_filename = f"{student_id}.{original_ext}"
                            else:
                                new_filename = f"{student_id}_no_ext"
                            
                            # Handle duplicate extensions by adding a counter
                            counter = 1
                            base_new_filename = new_filename
                            while os.path.exists(os.path.join(student_temp_dir, new_filename)):
                                if original_ext:
                                    new_filename = f"{student_id}_{counter}.{original_ext}"
                                else:
                                    new_filename = f"{student_id}_no_ext_{counter}"
                                counter += 1
                            
                            # Copy file with new name
                            dest_path = os.path.join(student_temp_dir, new_filename)
                            shutil.copy2(extracted_file_path, dest_path)
                            print(f"    Extracted: {os.path.basename(extracted_file_path)} -> {new_filename}")
            
            # Process non-zip files
            for filename in non_zip_files:
                source_path = os.path.join(folder_path, filename)
                original_ext = get_file_extension(filename)
                
                # Create new filename
                if original_ext:
                    new_filename = f"{student_id}.{original_ext}"
                else:
                    new_filename = f"{student_id}_no_ext"
                
                # Handle duplicate extensions by adding a counter
                counter = 1
                base_new_filename = new_filename
                while os.path.exists(os.path.join(student_temp_dir, new_filename)):
                    if original_ext:
                        new_filename = f"{student_id}_{counter}.{original_ext}"
                    else:
                        new_filename = f"{student_id}_no_ext_{counter}"
                    counter += 1
                
                # Copy file with new name
                dest_path = os.path.join(student_temp_dir, new_filename)
                shutil.copy2(source_path, dest_path)
                print(f"  Copied: {filename} -> {new_filename}")
            
            # Create final zip file for this student
            final_zip_path = os.path.join(output_dir, f"{student_id}.zip")
            
            # Get all files in student temp directory
            student_files_to_zip = []
            for root, dirs, files in os.walk(student_temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    student_files_to_zip.append(file_path)
            
            if student_files_to_zip:
                with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                    for file_path in student_files_to_zip:
                        # Use just the filename (not the full path) in the zip
                        arcname = os.path.basename(file_path)
                        zip_ref.write(file_path, arcname)
                
                print(f"  Created: {student_id}.zip ({len(student_files_to_zip)} files)")
            else:
                print(f"  Warning: No files found for student {student_id}")
    
    print(f"\nProcessing complete! Output files are in: {output_dir}")
    
    # Print summary
    output_files = [f for f in os.listdir(output_dir) if f.endswith('.zip')]
    print(f"Created {len(output_files)} student zip files:")
    for zip_file in sorted(output_files):
        print(f"  {zip_file}")


def main():
    parser = argparse.ArgumentParser(description='Consolidate student assignment files')
    parser.add_argument('folder_path', nargs='?', default='.', 
                       help='Path to folder containing assignment files (default: current directory)')
    
    args = parser.parse_args()
    
    folder_path = os.path.abspath(args.folder_path)
    print(f"Processing files in: {folder_path}")
    
    process_student_files(folder_path)


if __name__ == "__main__":
    main()
