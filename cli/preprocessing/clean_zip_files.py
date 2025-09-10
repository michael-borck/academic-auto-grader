#!/usr/bin/env python3
"""
Zip File Cleaner Based on Student CSV

This script reads a students.csv file and deletes any zip files in a specified folder
that don't correspond to student IDs found in the CSV.

Usage: python clean_zip_files.py [zip_folder_path] [csv_file_path]

The script expects:
- Zip files named as <STUDENT_ID>.zip
- CSV file with a "Student ID" column containing valid student IDs
"""

import os
import csv
import argparse
from pathlib import Path


def read_student_ids_from_csv(csv_file_path):
    """Read student IDs from CSV file, handling encoding issues."""
    student_ids = set()
    
    # Try different encodings
    encodings_to_try = ['utf-16', 'utf-16le', 'utf-16be', 'utf-8', 'cp1252', 'iso-8859-1']
    
    for encoding in encodings_to_try:
        try:
            with open(csv_file_path, 'r', encoding=encoding) as file:
                # Read first few characters to check for BOM or encoding issues
                content = file.read()
                file.seek(0)
                
                # Handle UTF-16 with BOM
                if content.startswith('\ufeff') or '\x00' in content[:100]:
                    # This looks like UTF-16 encoded
                    if encoding not in ['utf-16', 'utf-16le', 'utf-16be']:
                        continue
                
                reader = csv.DictReader(file)
                
                # Look for student ID column (handle different possible names)
                student_id_column = None
                for fieldname in reader.fieldnames:
                    clean_fieldname = fieldname.strip().replace('\ufeff', '')
                    if 'student' in clean_fieldname.lower() and 'id' in clean_fieldname.lower():
                        student_id_column = fieldname
                        break
                
                if not student_id_column:
                    print(f"Available columns: {reader.fieldnames}")
                    raise ValueError("Could not find 'Student ID' column in CSV")
                
                # Read all student IDs
                for row in reader:
                    student_id = str(row[student_id_column]).strip()
                    if student_id and student_id.isdigit():
                        student_ids.add(student_id)
                
                print(f"Successfully read CSV with encoding: {encoding}")
                print(f"Found {len(student_ids)} valid student IDs")
                return student_ids
                
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"Error with encoding {encoding}: {e}")
            continue
    
    raise ValueError("Could not read CSV file with any of the attempted encodings")


def find_zip_files(folder_path):
    """Find all zip files in the specified folder."""
    zip_files = []
    
    if not os.path.exists(folder_path):
        raise FileNotFoundError(f"Folder not found: {folder_path}")
    
    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.zip'):
            zip_files.append(filename)
    
    return zip_files


def extract_student_id_from_zip_name(zip_filename):
    """Extract student ID from zip filename (assumes format: <STUDENT_ID>.zip)."""
    # Remove .zip extension
    name_without_ext = os.path.splitext(zip_filename)[0]
    
    # Check if it's all digits (student ID)
    if name_without_ext.isdigit():
        return name_without_ext
    
    return None


def clean_zip_files(zip_folder_path, csv_file_path, dry_run=False):
    """Main function to clean zip files based on student CSV."""
    
    print(f"Reading student IDs from: {csv_file_path}")
    valid_student_ids = read_student_ids_from_csv(csv_file_path)
    
    print(f"Looking for zip files in: {zip_folder_path}")
    zip_files = find_zip_files(zip_folder_path)
    
    print(f"Found {len(zip_files)} zip files")
    
    # Analyze zip files
    valid_zips = []
    invalid_zips = []
    non_student_zips = []
    
    for zip_file in zip_files:
        student_id = extract_student_id_from_zip_name(zip_file)
        
        if student_id is None:
            # Zip file doesn't follow <STUDENT_ID>.zip pattern
            non_student_zips.append(zip_file)
        elif student_id in valid_student_ids:
            # Valid student ID
            valid_zips.append(zip_file)
        else:
            # Student ID not in CSV
            invalid_zips.append(zip_file)
    
    # Print summary
    print(f"\nAnalysis Results:")
    print(f"Valid zip files (student in CSV): {len(valid_zips)}")
    print(f"Invalid zip files (student not in CSV): {len(invalid_zips)}")
    print(f"Non-student zip files (doesn't match pattern): {len(non_student_zips)}")
    
    # Show files to be deleted
    files_to_delete = invalid_zips + non_student_zips
    
    if files_to_delete:
        print(f"\nFiles to be deleted ({len(files_to_delete)}):")
        for file in sorted(files_to_delete):
            student_id = extract_student_id_from_zip_name(file)
            if student_id:
                print(f"  {file} (Student ID {student_id} not in CSV)")
            else:
                print(f"  {file} (doesn't match student ID pattern)")
        
        if not dry_run:
            print(f"\nDeleting {len(files_to_delete)} files...")
            deleted_count = 0
            
            for file in files_to_delete:
                file_path = os.path.join(zip_folder_path, file)
                try:
                    os.remove(file_path)
                    print(f"  Deleted: {file}")
                    deleted_count += 1
                except Exception as e:
                    print(f"  Error deleting {file}: {e}")
            
            print(f"\nSuccessfully deleted {deleted_count} files")
        else:
            print("\n*** DRY RUN MODE - No files were actually deleted ***")
            print("Run without --dry-run to actually delete files")
    else:
        print("\nNo files need to be deleted - all zip files correspond to students in the CSV")
    
    # Show valid files (keeping)
    if valid_zips:
        print(f"\nKeeping {len(valid_zips)} valid files:")
        for file in sorted(valid_zips):
            student_id = extract_student_id_from_zip_name(file)
            print(f"  {file} (Student ID {student_id})")
    
    # Check for missing students
    zip_student_ids = {extract_student_id_from_zip_name(f) for f in valid_zips}
    zip_student_ids.discard(None)
    
    missing_students = valid_student_ids - zip_student_ids
    if missing_students:
        print(f"\nStudents in CSV but no zip file found ({len(missing_students)}):")
        for student_id in sorted(missing_students):
            print(f"  {student_id}.zip (missing)")


def main():
    parser = argparse.ArgumentParser(description='Clean zip files based on student CSV')
    parser.add_argument('zip_folder', nargs='?', default='.', 
                       help='Path to folder containing zip files (default: current directory)')
    parser.add_argument('csv_file', nargs='?', default='students.csv',
                       help='Path to students CSV file (default: students.csv)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without actually deleting')
    
    args = parser.parse_args()
    
    zip_folder_path = os.path.abspath(args.zip_folder)
    csv_file_path = os.path.abspath(args.csv_file)
    
    print(f"Zip folder: {zip_folder_path}")
    print(f"CSV file: {csv_file_path}")
    
    if args.dry_run:
        print("*** DRY RUN MODE ***")
    
    try:
        clean_zip_files(zip_folder_path, csv_file_path, dry_run=args.dry_run)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
