#!/usr/bin/env python3
"""
Enhanced GitHub Scanner for WeatherWise Submissions
- Finds GitHub URLs in submissions
- Searches for GitHub usernames in text
- Cross-references with accessible repositories
- Interactive repo selection for multiple matches
- Generates mapping file for auto_grader
"""

import os
import json
import zipfile
import re
import docx
import PyPDF2
import warnings
import requests
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd

# Suppress nbformat warnings
warnings.filterwarnings('ignore')

class EnhancedGitHubScanner:
    def __init__(self, github_token: str = None):
        self.github_token = github_token
        self.github_patterns = [
            r'https://github\.com/[\w\-\.]+/[\w\-\.]+',
            r'github\.com/[\w\-\.]+/[\w\-\.]+',
            r'git@github\.com:[\w\-\.]+/[\w\-\.]+\.git'
        ]
        
        # GitHub username patterns (more flexible)
        self.username_patterns = [
            r'github\.com/([a-zA-Z0-9\-_]+)',  # Any github.com/username
            r'@([a-zA-Z0-9\-_]+)',            # @username mentions
            r'GitHub\s*[Uu]ser(?:name)?:?\s*([a-zA-Z0-9\-_]+)',  # "GitHub user: username"
            r'[Uu]sername:?\s*([a-zA-Z0-9\-_]+)',  # "Username: something"
            r'[Gg]it[Hh]ub:?\s*([a-zA-Z0-9\-_]+)',  # "GitHub: username"
        ]
        
        # URLs to ignore
        self.ignore_urls = {
            'https://github.com/teaching-repositories/fetch-my-weather',
            'https://github.com/teaching-repositories/hands-on-ai',
            'https://github.com/chubin/wttr.in',
            'https://github.com/yourusername/weather-assistant',
            'https://github.com/user-attachments/assets',
            'https://github.com/michael-borck/fetch-my-weather',
            'https://github.com/username/repository-name',
            'https://github.com/your-username/your-repo',
            'https://github.com/student/weatherwise',
            'https://github.com/example/weather-app'
        }
        
        # Usernames to ignore
        self.ignore_usernames = {
            'yourusername', 'username', 'your-username', 'student', 'user',
            'teaching-repositories', 'chubin', 'michael-borck', 'example',
            'user-attachments', 'github', 'git'
        }
        
        # Setup headers for GitHub API
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'WeatherWise-Grader/1.0'
        }
        if self.github_token:
            self.headers['Authorization'] = f'token {self.github_token}'
            
        # Cache for accessible repos
        self.accessible_repos = None
    
    def get_accessible_repos(self) -> List[Dict]:
        """Get list of all repositories you have access to"""
        if self.accessible_repos is not None:
            return self.accessible_repos
            
        if not self.github_token:
            print("❌ No GitHub token provided - cannot fetch accessible repositories")
            return []
        
        print("🔍 Fetching all accessible repositories...")
        repos = []
        page = 1
        
        try:
            while True:
                # Get repos you have access to (both owned and collaborator)
                response = requests.get(
                    f'https://api.github.com/user/repos?per_page=100&page={page}&type=all',
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code != 200:
                    print(f"❌ Failed to fetch repositories: {response.status_code}")
                    break
                
                page_repos = response.json()
                if not page_repos:
                    break
                    
                repos.extend(page_repos)
                page += 1
                
                # Rate limiting
                time.sleep(0.1)
                
                # Progress indicator
                if len(repos) % 100 == 0:
                    print(f"   Found {len(repos)} repositories...")
        
        except Exception as e:
            print(f"❌ Error fetching repositories: {str(e)}")
            return []
        
        print(f"✅ Found {len(repos)} accessible repositories")
        self.accessible_repos = repos
        return repos
    
    def enhanced_scan_submissions(self, submissions_folder: str) -> Dict[str, any]:
        """Enhanced scanning with username detection and repo matching"""
        print("🚀 Starting Enhanced GitHub Detection...")
        print("=" * 70)
        
        results = {
            "total_submissions": 0,
            "phase1_url_found": 0,
            "phase2_username_matches": 0,
            "phase3_interactive_selections": 0,
            "no_github_detected": 0,
            "student_github_mapping": {},
            "detailed_results": [],
            "accessible_repos_count": 0,
            "recommendation": ""
        }
        
        zip_files = [f for f in os.listdir(submissions_folder) if f.endswith('.zip')]
        results["total_submissions"] = len(zip_files)
        
        # Get accessible repos once
        accessible_repos = self.get_accessible_repos()
        results["accessible_repos_count"] = len(accessible_repos)
        
        if not accessible_repos and self.github_token:
            print("⚠️  No accessible repositories found - proceeding with URL detection only")
        
        print(f"\n📂 Processing {len(zip_files)} submissions...")
        print("=" * 70)
        
        for i, zip_file in enumerate(zip_files, 1):
            student_id = Path(zip_file).stem
            print(f"\n[{i}/{len(zip_files)}] Processing: {student_id}")
            
            zip_path = os.path.join(submissions_folder, zip_file)
            submission_result = self._process_single_submission(
                zip_path, accessible_repos
            )
            
            results["detailed_results"].append(submission_result)
            
            # Update counters
            if submission_result["github_url"]:
                if submission_result["detection_method"] == "url_found":
                    results["phase1_url_found"] += 1
                elif submission_result["detection_method"] == "username_match":
                    results["phase2_username_matches"] += 1
                elif submission_result["detection_method"] == "interactive_selection":
                    results["phase3_interactive_selections"] += 1
                    
                # Add to mapping
                results["student_github_mapping"][student_id] = submission_result["github_url"]
                
                print(f"   ✅ GitHub repo: {submission_result['github_url']}")
                print(f"   📍 Method: {submission_result['detection_method']}")
            else:
                results["no_github_detected"] += 1
                print(f"   ❌ No GitHub repository detected")
        
        # Calculate recommendation
        total_with_github = (results["phase1_url_found"] + 
                           results["phase2_username_matches"] + 
                           results["phase3_interactive_selections"])
        
        github_percentage = (total_with_github / results["total_submissions"]) * 100
        
        if github_percentage >= 50:
            results["recommendation"] = "ENABLE_GITHUB_INTEGRATION"
        else:
            results["recommendation"] = "DISABLE_GITHUB_INTEGRATION"
        
        print("\n" + "=" * 70)
        self._print_final_summary(results)
        
        return results
    
    def _process_single_submission(self, zip_path: str, accessible_repos: List[Dict]) -> Dict[str, any]:
        """Process a single submission through all detection phases"""
        student_id = Path(zip_path).stem
        result = {
            "student_id": student_id,
            "github_url": None,
            "detection_method": None,
            "found_in_files": [],
            "usernames_found": [],
            "potential_repos": [],
            "errors": []
        }
        
        temp_dir = f"temp_scan_{student_id}"
        
        try:
            # Extract submission
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Extract all text content
            all_text_content = self._extract_all_text(temp_dir)
            
            # Phase 1: Look for GitHub URLs
            github_url = self._find_github_urls_in_content(all_text_content)
            if github_url:
                result["github_url"] = github_url[0]  # Take first valid URL
                result["detection_method"] = "url_found"
                result["found_in_files"] = [github_url[1]]  # filename
                return result
            
            # Phase 2: Look for GitHub usernames
            usernames = self._find_github_usernames_in_content(all_text_content)
            result["usernames_found"] = usernames
            
            if usernames and accessible_repos:
                # Check for matching repositories
                potential_repos = self._find_matching_repos(usernames, accessible_repos)
                result["potential_repos"] = potential_repos
                
                if potential_repos:
                    # Phase 3: Handle multiple matches
                    selected_repo = self._select_repository(student_id, potential_repos)
                    if selected_repo:
                        result["github_url"] = selected_repo
                        if len(potential_repos) > 1:
                            result["detection_method"] = "interactive_selection"
                        else:
                            result["detection_method"] = "username_match"
        
        except Exception as e:
            result["errors"].append(f"Error processing submission: {str(e)}")
        
        finally:
            # Cleanup
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception:
                pass
        
        return result
    
    def _extract_all_text(self, temp_dir: str) -> List[Tuple[str, str]]:
        """Extract text from all files in submission"""
        all_text_content = []
        
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                
                try:
                    if file.endswith('.txt') or file.endswith('.md'):
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            all_text_content.append((file, content))
                    
                    elif file.endswith('.docx'):
                        content = self._extract_docx_content(file_path)
                        if not content.startswith("Error"):
                            all_text_content.append((file, content))
                    
                    elif file.endswith('.pdf'):
                        content = self._extract_pdf_content(file_path)
                        if not content.startswith("Error"):
                            all_text_content.append((file, content))
                    
                    elif file.endswith('.ipynb'):
                        content = self._extract_notebook_text(file_path)
                        if content:
                            all_text_content.append((file, content))
                
                except Exception:
                    continue
        
        return all_text_content
    
    def _find_github_urls_in_content(self, all_text_content: List[Tuple[str, str]]) -> Optional[Tuple[str, str]]:
        """Find valid GitHub URLs in content"""
        for filename, content in all_text_content:
            urls = self._find_all_github_urls(content)
            for url in urls:
                if self._is_valid_student_url(url):
                    return (url, filename)
        return None
    
    def _find_github_usernames_in_content(self, all_text_content: List[Tuple[str, str]]) -> List[str]:
        """Extract potential GitHub usernames from content"""
        usernames = set()
        
        for filename, content in all_text_content:
            for pattern in self.username_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    username = match.strip().lower()
                    if (len(username) >= 3 and 
                        username not in self.ignore_usernames and
                        username.replace('-', '').replace('_', '').isalnum()):
                        usernames.add(username)
        
        return list(usernames)
    
    def _find_matching_repos(self, usernames: List[str], accessible_repos: List[Dict]) -> List[str]:
        """Find repositories that match the detected usernames"""
        potential_repos = []
        
        for repo in accessible_repos:
            repo_owner = repo['owner']['login'].lower()
            repo_name = repo['name'].lower()
            repo_url = repo['html_url']
            
            # Check if any username matches the repo owner
            for username in usernames:
                if username == repo_owner:
                    # Prioritize repos that look like assignments
                    if any(term in repo_name for term in ['weather', 'isys', 'assignment', 'a2']):
                        potential_repos.insert(0, repo_url)  # Add to front
                    else:
                        potential_repos.append(repo_url)
                    break
        
        return list(dict.fromkeys(potential_repos))  # Remove duplicates while preserving order
    
    def _select_repository(self, student_id: str, potential_repos: List[str]) -> Optional[str]:
        """Select repository - automatic for single match, interactive for multiple"""
        if len(potential_repos) == 1:
            return potential_repos[0]
        
        if len(potential_repos) > 1:
            print(f"\n   🤔 Multiple repositories found for {student_id}:")
            for i, repo in enumerate(potential_repos, 1):
                print(f"      {i}. {repo}")
            
            while True:
                try:
                    choice = input(f"   Select repository (1-{len(potential_repos)}, or 0 for none): ").strip()
                    if choice == '0':
                        return None
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(potential_repos):
                        return potential_repos[choice_idx]
                    else:
                        print(f"   Please enter a number between 1 and {len(potential_repos)}")
                except (ValueError, KeyboardInterrupt):
                    print("   Please enter a valid number")
        
        return None
    
    def _print_final_summary(self, results: Dict[str, any]):
        """Print comprehensive summary"""
        total = results["total_submissions"]
        url_found = results["phase1_url_found"]
        username_matches = results["phase2_username_matches"]
        interactive = results["phase3_interactive_selections"]
        no_github = results["no_github_detected"]
        total_with_github = url_found + username_matches + interactive
        
        print("📊 ENHANCED GITHUB DETECTION SUMMARY")
        print("=" * 70)
        print(f"Total submissions processed: {total}")
        print(f"✅ Phase 1 - URLs found in submissions: {url_found} ({url_found/total*100:.1f}%)")
        print(f"✅ Phase 2 - Username matches with accessible repos: {username_matches} ({username_matches/total*100:.1f}%)")
        print(f"✅ Phase 3 - Interactive selections: {interactive} ({interactive/total*100:.1f}%)")
        print(f"❌ No GitHub detected: {no_github} ({no_github/total*100:.1f}%)")
        print("-" * 50)
        print(f"🎯 Total with GitHub repositories: {total_with_github} ({total_with_github/total*100:.1f}%)")
        print(f"📂 Accessible repositories checked: {results['accessible_repos_count']}")
        
        print(f"\n🚀 RECOMMENDATION:")
        if results["recommendation"] == "ENABLE_GITHUB_INTEGRATION":
            print("✅ ENABLE GitHub integration in auto_grader.py")
            print("   Sufficient GitHub repositories detected for meaningful analysis")
        else:
            print("❌ DISABLE GitHub integration in auto_grader.py")
            print("   Too few GitHub repositories detected (<50%) - not worth the complexity")
    
    def save_student_mapping(self, results: Dict[str, any], filename: str = "student_github_mapping.json"):
        """Save student ID to GitHub URL mapping"""
        mapping_data = {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_submissions": results["total_submissions"],
            "total_with_github": len(results["student_github_mapping"]),
            "recommendation": results["recommendation"],
            "mapping": results["student_github_mapping"],
            "summary": {
                "phase1_url_found": results["phase1_url_found"],
                "phase2_username_matches": results["phase2_username_matches"],
                "phase3_interactive_selections": results["phase3_interactive_selections"],
                "no_github_detected": results["no_github_detected"]
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(mapping_data, f, indent=2)
        
        print(f"\n💾 Student-GitHub mapping saved to: {filename}")
        print(f"   This file can be used by auto_grader.py for GitHub integration")
    
    def create_detailed_report(self, results: Dict[str, any], filename: str = "enhanced_github_report.xlsx"):
        """Create detailed Excel report"""
        data = []
        
        for result in results["detailed_results"]:
            data.append({
                "Student ID": result["student_id"],
                "GitHub URL": result["github_url"] or "",
                "Detection Method": result["detection_method"] or "none",
                "Found In Files": ", ".join(result["found_in_files"]),
                "Usernames Found": ", ".join(result["usernames_found"]),
                "Potential Repos": ", ".join(result["potential_repos"]),
                "Errors": "; ".join(result["errors"])
            })
        
        # Add summary
        summary_data = {
            "Student ID": "SUMMARY",
            "GitHub URL": f"{len(results['student_github_mapping'])}/{results['total_submissions']} repositories found",
            "Detection Method": results["recommendation"],
            "Found In Files": "",
            "Usernames Found": "",
            "Potential Repos": f"{results['accessible_repos_count']} accessible repos checked",
            "Errors": ""
        }
        
        df = pd.DataFrame(data)
        df = pd.concat([df, pd.DataFrame([{}]), pd.DataFrame([summary_data])], ignore_index=True)
        df.to_excel(filename, index=False)
        print(f"📊 Detailed report saved to: {filename}")
    
    # Include the helper methods from the original scanner
    def _find_all_github_urls(self, text: str) -> List[str]:
        """Find all GitHub repository URLs in text"""
        found_urls = []
        for pattern in self.github_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                url = self._normalize_github_url(match)
                if url not in found_urls:
                    found_urls.append(url)
        return found_urls
    
    def _normalize_github_url(self, url: str) -> str:
        """Normalize GitHub URL to standard HTTPS format"""
        if url.startswith('git@'):
            url = url.replace('git@github.com:', 'https://github.com/').replace('.git', '')
        elif not url.startswith('https://'):
            url = 'https://' + url
        if url.endswith('.git'):
            url = url[:-4]
        return url
    
    def _is_valid_student_url(self, url: str) -> bool:
        """Check if URL is a valid student repository"""
        normalized_url = self._normalize_github_url(url).lower()
        
        for ignore_url in self.ignore_urls:
            ignore_normalized = ignore_url.lower()
            if ignore_normalized.endswith('.git'):
                ignore_normalized = ignore_normalized[:-4]
            if normalized_url.startswith(ignore_normalized):
                return False
        
        url_parts = normalized_url.replace('https://github.com/', '').split('/')
        if len(url_parts) >= 2:
            owner, repo = url_parts[0], url_parts[1]
            
            if any(term in owner.lower() for term in ['teaching', 'example', 'template', 'sample']):
                return False
            if any(term in repo.lower() for term in ['template', 'example', 'sample', 'wttr']):
                return False
            if owner.lower() in ['yourusername', 'username', 'your-username', 'student', 'user']:
                return False
        
        return True
    
    def _extract_docx_content(self, docx_path: str) -> str:
        """Extract text from Word document"""
        try:
            doc = docx.Document(docx_path)
            return '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"
    
    def _extract_pdf_content(self, pdf_path: str) -> str:
        """Extract text from PDF"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def _extract_notebook_text(self, notebook_path: str) -> str:
        """Extract text from Jupyter notebook"""
        try:
            import nbformat
            with open(notebook_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            
            text_content = []
            for cell in nb.cells:
                if cell.cell_type in ['markdown', 'code']:
                    text_content.append(cell.source)
            
            return '\n'.join(text_content)
        except Exception:
            return ""


def main():
    """Main execution function"""
    # Initialize scanner with GitHub token
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("⚠️  Warning: No GITHUB_TOKEN environment variable found")
        print("   Some features (username matching) will be limited")
    
    scanner = EnhancedGitHubScanner(github_token=github_token)
    
    # Run enhanced scanning
    results = scanner.enhanced_scan_submissions("submissions/")
    
    # Save results
    scanner.save_student_mapping(results, "student_github_mapping.json")
    scanner.create_detailed_report(results, "enhanced_github_report.xlsx")
    
    print(f"\n🎯 Next Steps:")
    if results["recommendation"] == "ENABLE_GITHUB_INTEGRATION":
        print("1. Use 'student_github_mapping.json' in your auto_grader.py")
        print("2. Enable GitHub integration for enhanced grading")
    else:
        print("1. Consider running auto_grader.py without GitHub integration")
        print("2. Focus on submission content analysis only")


if __name__ == "__main__":
    main()
