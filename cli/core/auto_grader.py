#!/usr/bin/env python3
"""
Generalized Automated Assignment Grading System
Supports multiple assignments through configuration-driven approach
"""

import os
import json
import zipfile
import nbformat
import requests
import statistics
import re
import docx
import PyPDF2
import base64
import warnings
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import openai
import anthropic
from datetime import datetime
import pandas as pd

from config_loader import ConfigLoader
from prompt_builder import PromptBuilder

# Suppress specific nbformat warnings for missing cell IDs
warnings.filterwarnings('ignore', category=nbformat.validator.MissingIDFieldWarning)
warnings.filterwarnings('ignore', message='Cell is missing an id field')


class AutomatedGrader:
    def __init__(self, 
                 assignment_name: str,
                 openai_api_key: str, 
                 anthropic_api_key: str, 
                 github_token: str = None,
                 cohere_api_key: str = None, 
                 enable_github: bool = None,
                 github_mapping_file: str = "student_github_mapping.json",
                 assignments_dir: str = "assignments",
                 templates_dir: str = "templates"):
        """Initialize the grader with assignment configuration"""
        
        # Load assignment configuration
        self.config_loader = ConfigLoader(assignments_dir)
        self.assignment_config = self.config_loader.load_assignment_config(assignment_name)
        self.assignment_name = assignment_name
        
        # Initialize prompt builder
        self.prompt_builder = PromptBuilder(templates_dir)
        
        # Initialize LLM clients
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        self.anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.github_token = github_token
        self.cohere_api_key = cohere_api_key
        
        # Determine GitHub integration setting
        github_config = self.config_loader.get_github_config(self.assignment_config)
        if enable_github is None:
            self.enable_github = github_config.get('enabled', False)
        else:
            self.enable_github = enable_github
        
        self.github_mapping = {}
        
        # Load GitHub mapping if enabled
        if self.enable_github:
            self.github_mapping = self._load_github_mapping(github_mapping_file)
            print(f"📂 GitHub integration enabled: {len(self.github_mapping)} student repositories loaded")
        else:
            print("🚫 GitHub integration disabled")
        
        # Token usage tracking
        self.token_usage = {
            "total": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost_usd": 0.0},
            "by_provider": {
                "openai": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost_usd": 0.0},
                "anthropic": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost_usd": 0.0},
                "cohere": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost_usd": 0.0}
            },
            "by_student": {},
            "detailed_log": []
        }
        
        # Current pricing (as of 2024 - update these as needed)
        self.pricing = {
            "openai": {
                "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},  # per 1K tokens
                "gpt-4": {"input": 0.03, "output": 0.06}
            },
            "anthropic": {
                "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},  # per 1K tokens
                "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125}
            },
            "cohere": {
                "command": {"input": 0.0015, "output": 0.002}  # per 1K tokens
            }
        }
        
        print(f"🎯 Initialized grader for: {self.assignment_config['assignment']['name']}")
        print(f"📋 Assignment type: {self.assignment_config['assignment']['type']}")
        print(f"🏆 Total points: {self.assignment_config['assignment']['total_points']}")

    def _load_github_mapping(self, mapping_file: str) -> Dict[str, str]:
        """Load student GitHub mapping from file"""
        try:
            if not os.path.exists(mapping_file):
                print(f"⚠️  GitHub mapping file not found: {mapping_file}")
                print("   Run github_scanner.py first to generate mapping")
                return {}
            
            with open(mapping_file, 'r') as f:
                data = json.load(f)
            
            mapping = data.get('mapping', {})
            recommendation = data.get('recommendation', 'UNKNOWN')
            
            print(f"📋 Mapping file recommendation: {recommendation}")
            if recommendation == 'DISABLE_GITHUB_INTEGRATION':
                print("⚠️  Warning: Mapping file recommends disabling GitHub integration")
                print("   Consider running with --no-github flag")
            
            return mapping
            
        except Exception as e:
            print(f"❌ Error loading GitHub mapping: {str(e)}")
            return {}

    def extract_submission_content(self, zip_path: str) -> Dict[str, Any]:
        """Extract and process content from a student submission ZIP file"""
        content = {
            "student_id": Path(zip_path).stem,
            "notebook_content": "",
            "conversation_files": [],
            "readme_content": "",
            "code_cells": [],
            "markdown_cells": [],
            "function_implementations": {},
            "github_info": {},
            "additional_documents": [],
            "errors": []
        }
        
        temp_dir = f"temp_{content['student_id']}"
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Extract to temporary directory
                zip_ref.extractall(temp_dir)
                
                # Process all files
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        try:
                            if file.endswith('.ipynb'):
                                content["notebook_content"] = self._extract_notebook_content(file_path)
                                
                            elif file.startswith('conversation') and file.endswith('.txt'):
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    conv_content = f.read()
                                    content["conversation_files"].append({
                                        "filename": file,
                                        "content": conv_content
                                    })
                                    
                            elif file.lower() == 'readme.md':
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    content["readme_content"] = f.read()
                            
                            # Handle Word documents
                            elif file.endswith('.docx'):
                                doc_content = self._extract_docx_content(file_path)
                                content["additional_documents"].append({
                                    "filename": file,
                                    "type": "docx",
                                    "content": doc_content
                                })
                            
                            # Handle PDF documents
                            elif file.endswith('.pdf'):
                                pdf_content = self._extract_pdf_content(file_path)
                                content["additional_documents"].append({
                                    "filename": file,
                                    "type": "pdf", 
                                    "content": pdf_content
                                })
                            
                            # Handle text files
                            elif file.endswith('.txt') and not file.startswith('conversation'):
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    txt_content = f.read()
                                    content["additional_documents"].append({
                                        "filename": file,
                                        "type": "txt",
                                        "content": txt_content
                                    })
                        
                        except Exception as file_error:
                            # Skip problematic files but continue processing
                            content["errors"].append(f"Error processing file {file}: {str(file_error)}")
                            continue
                
                # Add GitHub info if available and enabled
                if self.enable_github and content["student_id"] in self.github_mapping:
                    github_url = self.github_mapping[content["student_id"]]
                    content["github_info"] = self._fetch_github_repository_info(github_url)
        
        except Exception as e:
            content["errors"].append(f"Error extracting ZIP: {str(e)}")
        
        finally:
            # Always clean up temp directory, even if there was an error
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                content["errors"].append(f"Failed to clean up temp directory: {str(cleanup_error)}")
            
        return content

    def _extract_docx_content(self, docx_path: str) -> str:
        """Extract text content from Word document"""
        try:
            doc = docx.Document(docx_path)
            full_text = []
            for paragraph in doc.paragraphs:
                full_text.append(paragraph.text)
            return '\n'.join(full_text)
        except Exception as e:
            return f"Error reading DOCX: {str(e)}"

    def _extract_pdf_content(self, pdf_path: str) -> str:
        """Extract text content from PDF document"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"

    def _fetch_github_repository_info(self, github_url: str) -> Dict[str, Any]:
        """Fetch repository information from GitHub API"""
        if not self.github_token:
            return {"error": "No GitHub token provided", "url": github_url}
        
        try:
            # Extract owner and repo from URL
            parts = github_url.replace('https://github.com/', '').split('/')
            if len(parts) < 2:
                return {"error": "Invalid GitHub URL format", "url": github_url}
            
            owner, repo = parts[0], parts[1]
            
            headers = {
                'Authorization': f'token {self.github_token}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            # Get repository info
            repo_response = requests.get(f'https://api.github.com/repos/{owner}/{repo}', headers=headers)
            
            if repo_response.status_code != 200:
                return {
                    "error": f"Failed to access repository (status: {repo_response.status_code})",
                    "url": github_url,
                    "accessible": False
                }
            
            repo_data = repo_response.json()
            
            # Get commit history
            commits_response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/commits', headers=headers)
            commits_data = commits_response.json() if commits_response.status_code == 200 else []
            
            # Get repository contents
            contents_response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/contents', headers=headers)
            contents_data = contents_response.json() if contents_response.status_code == 200 else []
            
            # Get README from GitHub (might be different from ZIP)
            readme_response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/readme', headers=headers)
            github_readme = ""
            if readme_response.status_code == 200:
                readme_data = readme_response.json()
                if readme_data.get('content'):
                    github_readme = base64.b64decode(readme_data['content']).decode('utf-8', errors='ignore')
            
            return {
                "url": github_url,
                "accessible": True,
                "repository_info": {
                    "name": repo_data.get('name'),
                    "description": repo_data.get('description'),
                    "created_at": repo_data.get('created_at'),
                    "updated_at": repo_data.get('updated_at'),
                    "default_branch": repo_data.get('default_branch')
                },
                "commit_analysis": {
                    "total_commits": len(commits_data),
                    "commit_messages": [commit.get('commit', {}).get('message', '') for commit in commits_data[:20]],
                    "commit_dates": [commit.get('commit', {}).get('author', {}).get('date', '') for commit in commits_data[:10]],
                    "recent_commits": commits_data[:5] if commits_data else []
                },
                "repository_structure": {
                    "files": [item.get('name') for item in contents_data if item.get('type') == 'file'],
                    "folders": [item.get('name') for item in contents_data if item.get('type') == 'dir']
                },
                "github_readme": github_readme
            }
            
        except Exception as e:
            return {
                "error": f"Exception accessing GitHub: {str(e)}",
                "url": github_url,
                "accessible": False
            }

    def _extract_notebook_content(self, notebook_path: str) -> Dict[str, Any]:
        """Extract structured content from Jupyter notebook"""
        try:
            with open(notebook_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
            
            notebook_data = {
                "code_cells": [],
                "markdown_cells": [],
                "function_implementations": {},
                "imports": [],
                "structure_analysis": {}
            }
            
            current_section = "unknown"
            
            for cell in nb.cells:
                if cell.cell_type == 'markdown':
                    content = cell.source
                    notebook_data["markdown_cells"].append(content)
                    
                    # Detect section headers
                    if content.startswith('#'):
                        current_section = content.split('\n')[0].lower()
                        
                elif cell.cell_type == 'code':
                    code = cell.source
                    notebook_data["code_cells"].append({
                        "section": current_section,
                        "code": code,
                        "outputs": cell.get('outputs', [])
                    })
                    
                    # Extract function definitions
                    if 'def ' in code:
                        functions = self._extract_functions(code)
                        notebook_data["function_implementations"].update(functions)
                    
                    # Extract imports
                    if any(keyword in code for keyword in ['import ', 'from ']):
                        notebook_data["imports"].extend(self._extract_imports(code))
            
            return notebook_data
            
        except Exception as e:
            return {"error": f"Failed to parse notebook: {str(e)}"}

    def _extract_functions(self, code: str) -> Dict[str, str]:
        """Extract function definitions from code"""
        functions = {}
        lines = code.split('\n')
        current_function = None
        function_code = []
        
        for line in lines:
            if line.strip().startswith('def '):
                if current_function:
                    functions[current_function] = '\n'.join(function_code)
                current_function = line.strip().split('(')[0].replace('def ', '')
                function_code = [line]
            elif current_function and (line.startswith('    ') or line.strip() == ''):
                function_code.append(line)
            elif current_function and not line.startswith('    '):
                functions[current_function] = '\n'.join(function_code)
                current_function = None
                function_code = []
        
        if current_function:
            functions[current_function] = '\n'.join(function_code)
            
        return functions

    def _extract_imports(self, code: str) -> List[str]:
        """Extract import statements from code"""
        imports = []
        for line in code.split('\n'):
            line = line.strip()
            if line.startswith('import ') or line.startswith('from '):
                imports.append(line)
        return imports

    def create_grading_prompt(self, submission_content: Dict[str, Any]) -> str:
        """Create a comprehensive grading prompt using templates"""
        return self.prompt_builder.build_grading_prompt(
            self.assignment_config, 
            submission_content
        )

    def _track_token_usage(self, provider: str, model: str, input_tokens: int, output_tokens: int, student_id: str = None):
        """Track token usage and calculate costs"""
        total_tokens = input_tokens + output_tokens
        
        # Calculate cost
        model_pricing = self.pricing.get(provider, {}).get(model, {"input": 0, "output": 0})
        cost = (input_tokens * model_pricing["input"] / 1000) + (output_tokens * model_pricing["output"] / 1000)
        
        # Update totals
        self.token_usage["total"]["input_tokens"] += input_tokens
        self.token_usage["total"]["output_tokens"] += output_tokens
        self.token_usage["total"]["total_tokens"] += total_tokens
        self.token_usage["total"]["cost_usd"] += cost
        
        # Update by provider
        self.token_usage["by_provider"][provider]["input_tokens"] += input_tokens
        self.token_usage["by_provider"][provider]["output_tokens"] += output_tokens
        self.token_usage["by_provider"][provider]["total_tokens"] += total_tokens
        self.token_usage["by_provider"][provider]["cost_usd"] += cost
        
        # Update by student
        if student_id:
            if student_id not in self.token_usage["by_student"]:
                self.token_usage["by_student"][student_id] = {
                    "input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost_usd": 0.0,
                    "by_provider": {p: {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0, "cost_usd": 0.0} 
                                   for p in ["openai", "anthropic", "cohere"]}
                }
            
            student_data = self.token_usage["by_student"][student_id]
            student_data["input_tokens"] += input_tokens
            student_data["output_tokens"] += output_tokens
            student_data["total_tokens"] += total_tokens
            student_data["cost_usd"] += cost
            
            student_data["by_provider"][provider]["input_tokens"] += input_tokens
            student_data["by_provider"][provider]["output_tokens"] += output_tokens
            student_data["by_provider"][provider]["total_tokens"] += total_tokens
            student_data["by_provider"][provider]["cost_usd"] += cost
        
        # Log detailed entry
        self.token_usage["detailed_log"].append({
            "timestamp": datetime.now().isoformat(),
            "student_id": student_id,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "cost_usd": round(cost, 6)
        })
        
        return cost

    def grade_with_llm(self, prompt: str, llm_provider: str = "openai", student_id: str = None) -> Dict[str, Any]:
        """Send grading prompt to specific LLM and parse response with token tracking"""
        try:
            if llm_provider == "openai":
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are an expert programming instructor providing fair and detailed assessment of student work."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=4000
                )
                content = response.choices[0].message.content
                
                # Extract token usage from OpenAI response
                usage = response.usage
                input_tokens = usage.prompt_tokens
                output_tokens = usage.completion_tokens
                
                # Track usage
                cost = self._track_token_usage("openai", "gpt-4-turbo-preview", input_tokens, output_tokens, student_id)
                
                print(f"  OpenAI: {input_tokens} input + {output_tokens} output = {input_tokens + output_tokens} tokens (${cost:.4f})")
                
            elif llm_provider == "anthropic":
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=4000,
                    temperature=0.1,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                content = response.content[0].text
                
                # Extract token usage from Anthropic response
                usage = response.usage
                input_tokens = usage.input_tokens
                output_tokens = usage.output_tokens
                
                # Track usage
                cost = self._track_token_usage("anthropic", "claude-3-sonnet-20240229", input_tokens, output_tokens, student_id)
                
                print(f"  Anthropic: {input_tokens} input + {output_tokens} output = {input_tokens + output_tokens} tokens (${cost:.4f})")
                
            elif llm_provider == "cohere" and self.cohere_api_key:
                # Cohere API implementation with token tracking
                response = requests.post(
                    "https://api.cohere.ai/v1/generate",
                    headers={"Authorization": f"Bearer {self.cohere_api_key}"},
                    json={
                        "model": "command",
                        "prompt": prompt,
                        "max_tokens": 4000,
                        "temperature": 0.1,
                        "return_likelihoods": "NONE"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["generations"][0]["text"]
                    
                    # Estimate tokens for Cohere (they don't always provide exact counts)
                    # Rough estimation: ~4 characters per token for English text
                    input_tokens = len(prompt) // 4
                    output_tokens = len(content) // 4
                    
                    cost = self._track_token_usage("cohere", "command", input_tokens, output_tokens, student_id)
                    
                    print(f"  Cohere: ~{input_tokens} input + ~{output_tokens} output = ~{input_tokens + output_tokens} tokens (${cost:.4f})")
                else:
                    raise Exception(f"Cohere API error: {response.status_code}")
            
            # Extract JSON from response
            result = self._parse_grading_response(content, llm_provider)
            
            # Add token info to result
            if llm_provider in ["openai", "anthropic"]:
                result["token_usage"] = {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "cost_usd": cost
                }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Failed to grade with {llm_provider}: {str(e)}",
                "llm_provider": llm_provider
            }

    def _parse_grading_response(self, response_text: str, llm_provider: str) -> Dict[str, Any]:
        """Parse the JSON response from LLM"""
        try:
            # Find JSON block in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx]
                result = json.loads(json_str)
                result["llm_provider"] = llm_provider
                result["raw_response"] = response_text
                return result
            else:
                return {
                    "error": "Could not find JSON in response",
                    "llm_provider": llm_provider,
                    "raw_response": response_text
                }
        except json.JSONDecodeError as e:
            return {
                "error": f"JSON parsing error: {str(e)}",
                "llm_provider": llm_provider,
                "raw_response": response_text
            }

    def grade_submission(self, zip_path: str) -> Dict[str, Any]:
        """Complete grading workflow for a single submission"""
        student_id = Path(zip_path).stem
        print(f"Processing submission: {zip_path}")
        
        # Extract content
        content = self.extract_submission_content(zip_path)
        
        if content.get("errors"):
            return {
                "student_id": content["student_id"],
                "status": "error",
                "errors": content["errors"]
            }
        
        # Create grading prompt
        prompt = self.create_grading_prompt(content)
        
        # Grade with multiple LLMs
        llm_results = []
        print(f"  Grading with multiple LLMs...")
        
        for provider in ["openai", "anthropic"]:
            result = self.grade_with_llm(prompt, provider, student_id)
            if "error" not in result:
                llm_results.append(result)
        
        if not llm_results:
            return {
                "student_id": content["student_id"],
                "status": "error",
                "errors": ["All LLM grading attempts failed"]
            }
        
        # Aggregate results
        final_result = self._aggregate_llm_results(llm_results)
        final_result["student_id"] = content["student_id"]
        
        # Analyze submission content
        notebook_analysis = self.prompt_builder._analyze_notebook_content(content.get("notebook_content", {}))
        final_result["submission_analysis"] = {
            "functions_found": list(notebook_analysis["function_implementations"].keys()),
            "conversation_files": len(content.get("conversation_files", [])),
            "has_readme": bool(content.get("readme_content")),
            "notebook_cells": len(notebook_analysis["code_cells"])
        }
        
        # Add token summary for this student
        if student_id in self.token_usage["by_student"]:
            student_tokens = self.token_usage["by_student"][student_id]
            final_result["token_summary"] = {
                "total_tokens": student_tokens["total_tokens"],
                "cost_usd": round(student_tokens["cost_usd"], 4),
                "by_provider": {
                    provider: {
                        "tokens": data["total_tokens"],
                        "cost": round(data["cost_usd"], 4)
                    } for provider, data in student_tokens["by_provider"].items()
                    if data["total_tokens"] > 0
                }
            }
            print(f"  Student total: {student_tokens['total_tokens']} tokens (${student_tokens['cost_usd']:.4f})")
        
        return final_result

    def _aggregate_llm_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple LLMs"""
        if len(results) == 1:
            return results[0]
        
        # Calculate average scores using assignment rubric
        avg_scores = {}
        rubric_criteria = list(self.assignment_config['rubric'].keys())
        
        for criterion in rubric_criteria:
            scores = [r["scores"][criterion] for r in results if criterion in r.get("scores", {})]
            if scores:
                avg_scores[criterion] = round(statistics.mean(scores), 1)
        
        total_score = sum(avg_scores.values())
        
        # Aggregate feedback
        all_strengths = []
        all_improvements = []
        all_comments = {}
        
        for result in results:
            feedback = result.get("detailed_feedback", {})
            all_strengths.extend(feedback.get("strengths", []))
            all_improvements.extend(feedback.get("areas_for_improvement", []))
            
            for criterion, comment in feedback.get("specific_comments", {}).items():
                if criterion not in all_comments:
                    all_comments[criterion] = []
                all_comments[criterion].append(comment)
        
        # Determine letter grade
        letter_grade = "F"
        if total_score >= 90: letter_grade = "A"
        elif total_score >= 80: letter_grade = "B"
        elif total_score >= 70: letter_grade = "C"
        elif total_score >= 60: letter_grade = "D"
        
        return {
            "scores": avg_scores,
            "total_score": total_score,
            "letter_grade": letter_grade,
            "detailed_feedback": {
                "strengths": list(set(all_strengths)),  # Remove duplicates
                "areas_for_improvement": list(set(all_improvements)),
                "specific_comments": {k: " | ".join(v) for k, v in all_comments.items()}
            },
            "llm_consensus": len(results),
            "individual_llm_results": results
        }

    def estimate_token_usage(self, prompt: str) -> Dict[str, int]:
        """Estimate token usage for a prompt without making API calls"""
        # Rough estimation: ~4 characters per token for English text
        # This is approximate but gives a reasonable ballpark
        input_tokens = len(prompt) // 4
        
        # Estimate output tokens based on typical grading response length
        # JSON response + detailed feedback typically ~800-1200 tokens
        estimated_output_tokens = 1000
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": estimated_output_tokens,
            "total_tokens": input_tokens + estimated_output_tokens
        }

    def dry_run_grade_submission(self, zip_path: str) -> Dict[str, Any]:
        """Dry run grading - extracts content and estimates costs without LLM calls"""
        student_id = Path(zip_path).stem
        print(f"🔍 DRY RUN - Processing submission: {zip_path}")
        
        # Extract content (this is fast and safe to do)
        content = self.extract_submission_content(zip_path)
        
        if content.get("errors"):
            return {
                "student_id": content["student_id"],
                "status": "error",
                "errors": content["errors"],
                "dry_run": True
            }
        
        # Create grading prompt (no API calls)
        prompt = self.create_grading_prompt(content)
        
        # Estimate token usage
        token_estimate = self.estimate_token_usage(prompt)
        
        # Estimate costs for both providers
        openai_cost = (
            (token_estimate["input_tokens"] * self.pricing["openai"]["gpt-4-turbo-preview"]["input"] / 1000) +
            (token_estimate["output_tokens"] * self.pricing["openai"]["gpt-4-turbo-preview"]["output"] / 1000)
        )
        
        anthropic_cost = (
            (token_estimate["input_tokens"] * self.pricing["anthropic"]["claude-3-sonnet-20240229"]["input"] / 1000) +
            (token_estimate["output_tokens"] * self.pricing["anthropic"]["claude-3-sonnet-20240229"]["output"] / 1000)
        )
        
        total_estimated_cost = openai_cost + anthropic_cost
        
        print(f"  📊 Token estimate: {token_estimate['input_tokens']:,} input + {token_estimate['output_tokens']:,} output = {token_estimate['total_tokens']:,} total")
        print(f"  💰 Cost estimate: ${total_estimated_cost:.4f} (OpenAI: ${openai_cost:.4f}, Anthropic: ${anthropic_cost:.4f})")
        
        # Analyze submission content
        notebook_analysis = self.prompt_builder._analyze_notebook_content(content.get("notebook_content", {}))
        
        submission_analysis = {
            "functions_found": list(notebook_analysis["function_implementations"].keys()),
            "conversation_files": len(content.get("conversation_files", [])),
            "has_readme": bool(content.get("readme_content")),
            "notebook_cells": len(notebook_analysis["code_cells"]),
            "additional_documents": len(content.get("additional_documents", [])),
            "has_github": bool(content.get("github_info", {}).get("accessible"))
        }
        
        print(f"  📋 Content analysis:")
        print(f"    Functions found: {len(submission_analysis['functions_found'])}")
        print(f"    Conversation files: {submission_analysis['conversation_files']}")
        print(f"    Has README: {submission_analysis['has_readme']}")
        print(f"    Notebook cells: {submission_analysis['notebook_cells']}")
        if self.enable_github:
            print(f"    GitHub accessible: {submission_analysis['has_github']}")
        
        return {
            "student_id": content["student_id"],
            "status": "dry_run_success",
            "token_estimate": token_estimate,
            "cost_estimate": {
                "openai": openai_cost,
                "anthropic": anthropic_cost,
                "total": total_estimated_cost
            },
            "submission_analysis": submission_analysis,
            "prompt_length": len(prompt),
            "dry_run": True
        }

    def batch_grade(self, submissions_folder: str, output_file: str = None, dry_run: bool = False):
        """Grade all submissions in a folder (with optional dry run)"""
        if output_file is None:
            output_file = f"{self.assignment_name}_grading_results.json"
        
        results = []
        zip_files = [f for f in os.listdir(submissions_folder) if f.endswith('.zip')]
        
        if dry_run:
            print(f"🧪 DRY RUN MODE - Analyzing {len(zip_files)} submissions without API calls")
        else:
            print(f"🚀 LIVE GRADING - Processing {len(zip_files)} submissions")
        print("=" * 60)
        
        total_estimated_cost = 0
        total_estimated_tokens = 0
        
        for i, zip_file in enumerate(zip_files, 1):
            print(f"\n[{i}/{len(zip_files)}] {zip_file}")
            zip_path = os.path.join(submissions_folder, zip_file)
            
            if dry_run:
                result = self.dry_run_grade_submission(zip_path)
                if result.get("cost_estimate"):
                    total_estimated_cost += result["cost_estimate"]["total"]
                    total_estimated_tokens += result.get("token_estimate", {}).get("total_tokens", 0)
            else:
                result = self.grade_submission(zip_path)
            
            results.append(result)
            
            # Save intermediate results
            if not dry_run and i % 10 == 0:
                self._save_results(results, f"intermediate_{i}_{output_file}")
                self._save_token_report(f"token_report_intermediate_{i}.json")
            
            print("-" * 40)
        
        if dry_run:
            print("\n" + "=" * 60)
            print("🧪 DRY RUN SUMMARY")
            print("=" * 60)
            print(f"📊 Total estimated tokens: {total_estimated_tokens:,}")
            print(f"💰 Total estimated cost: ${total_estimated_cost:.2f}")
            print(f"📈 Average cost per submission: ${total_estimated_cost/len(zip_files):.3f}")
            
            # Cost breakdown
            successful_runs = [r for r in results if r.get("cost_estimate")]
            if successful_runs:
                openai_total = sum(r["cost_estimate"]["openai"] for r in successful_runs)
                anthropic_total = sum(r["cost_estimate"]["anthropic"] for r in successful_runs)
                print(f"   OpenAI estimated: ${openai_total:.2f}")
                print(f"   Anthropic estimated: ${anthropic_total:.2f}")
            
            # Content analysis summary
            functions_found = sum(len(r.get("submission_analysis", {}).get("functions_found", [])) for r in results)
            with_conversations = sum(1 for r in results if r.get("submission_analysis", {}).get("conversation_files", 0) > 0)
            with_readme = sum(1 for r in results if r.get("submission_analysis", {}).get("has_readme", False))
            
            print(f"\n📋 Content Summary:")
            print(f"   Total functions found: {functions_found}")
            print(f"   Submissions with conversation files: {with_conversations}/{len(zip_files)} ({with_conversations/len(zip_files)*100:.1f}%)")
            print(f"   Submissions with README: {with_readme}/{len(zip_files)} ({with_readme/len(zip_files)*100:.1f}%)")
            
            if self.enable_github:
                with_github = sum(1 for r in results if r.get("submission_analysis", {}).get("has_github", False))
                print(f"   Accessible GitHub repos: {with_github}/{len(zip_files)} ({with_github/len(zip_files)*100:.1f}%)")
            
            print(f"\n🎯 Ready to proceed with live grading?")
            print(f"   Estimated total cost: ${total_estimated_cost:.2f}")
            print(f"   Remove --dry-run flag to execute")
            
        else:
            # Save final results (live grading)
            self._save_results(results, output_file)
            self._generate_summary_report(results, output_file.replace('.json', '_summary.xlsx'))
            self._save_token_report(output_file.replace('.json', '_token_report.json'))
            
            print("\n" + "=" * 60)
            print("FINAL TOKEN USAGE SUMMARY")
            print("=" * 60)
            self._print_token_summary()
        
        return results

    def _print_token_summary(self):
        """Print current token usage summary"""
        total = self.token_usage["total"]
        by_provider = self.token_usage["by_provider"]
        
        print(f"\nToken Usage Summary:")
        print(f"  Total: {total['total_tokens']:,} tokens (${total['cost_usd']:.2f})")
        
        for provider, data in by_provider.items():
            if data['total_tokens'] > 0:
                print(f"  {provider.title()}: {data['total_tokens']:,} tokens (${data['cost_usd']:.2f})")
                print(f"    Input: {data['input_tokens']:,} | Output: {data['output_tokens']:,}")

    def _save_token_report(self, filename: str):
        """Save detailed token usage report"""
        token_report = {
            "generated_at": datetime.now().isoformat(),
            "assignment": self.assignment_name,
            "summary": self.token_usage,
            "cost_breakdown": self._generate_cost_breakdown(),
            "top_expensive_students": self._get_top_expensive_students(),
            "provider_comparison": self._get_provider_comparison()
        }
        
        with open(filename, 'w') as f:
            json.dump(token_report, f, indent=2)
        print(f"Token usage report saved to {filename}")

    def _generate_cost_breakdown(self) -> Dict[str, Any]:
        """Generate detailed cost breakdown"""
        breakdown = {}
        
        for provider, data in self.token_usage["by_provider"].items():
            if data['total_tokens'] > 0:
                breakdown[provider] = {
                    "total_cost": round(data['cost_usd'], 4),
                    "input_cost": round((data['input_tokens'] / 1000) * 
                                      list(self.pricing[provider].values())[0]['input'], 4),
                    "output_cost": round((data['output_tokens'] / 1000) * 
                                       list(self.pricing[provider].values())[0]['output'], 4),
                    "tokens_per_dollar": round(data['total_tokens'] / data['cost_usd'], 0) if data['cost_usd'] > 0 else 0,
                    "avg_cost_per_student": round(data['cost_usd'] / len([s for s in self.token_usage["by_student"].values() 
                                                                        if s["by_provider"][provider]["total_tokens"] > 0]), 4) if len(self.token_usage["by_student"]) > 0 else 0
                }
        
        return breakdown

    def _get_top_expensive_students(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Get top N most expensive students by token usage"""
        student_costs = []
        
        for student_id, data in self.token_usage["by_student"].items():
            student_costs.append({
                "student_id": student_id,
                "total_tokens": data["total_tokens"],
                "cost_usd": round(data["cost_usd"], 4),
                "provider_breakdown": {
                    provider: round(prov_data["cost_usd"], 4) 
                    for provider, prov_data in data["by_provider"].items()
                    if prov_data["total_tokens"] > 0
                }
            })
        
        return sorted(student_costs, key=lambda x: x["cost_usd"], reverse=True)[:top_n]

    def _get_provider_comparison(self) -> Dict[str, Any]:
        """Compare efficiency and costs between providers"""
        comparison = {}
        
        for provider, data in self.token_usage["by_provider"].items():
            if data['total_tokens'] > 0:
                comparison[provider] = {
                    "total_tokens": data["total_tokens"],
                    "total_cost": round(data["cost_usd"], 4),
                    "cost_per_1k_tokens": round((data["cost_usd"] / data["total_tokens"]) * 1000, 4),
                    "input_output_ratio": round(data["input_tokens"] / data["output_tokens"], 2) if data["output_tokens"] > 0 else 0,
                    "students_processed": len([s for s in self.token_usage["by_student"].values() 
                                             if s["by_provider"][provider]["total_tokens"] > 0])
                }
        
        return comparison

    def _save_results(self, results: List[Dict], filename: str):
        """Save results to JSON file"""
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to {filename}")

    def _generate_summary_report(self, results: List[Dict], filename: str):
        """Generate Excel summary report with token usage"""
        summary_data = []
        
        for result in results:
            if result.get("status") == "error":
                row = {
                    "Student ID": result["student_id"],
                    "Status": "ERROR",
                    "Total Score": 0,
                    "Letter Grade": "F",
                    "Total Tokens": 0,
                    "Cost USD": 0.0,
                    "Errors": "; ".join(result.get("errors", []))
                }
            else:
                token_summary = result.get("token_summary", {})
                row = {
                    "Student ID": result["student_id"],
                    "Status": "Graded",
                    "Total Score": result["total_score"],
                    "Letter Grade": result["letter_grade"],
                    "Total Tokens": token_summary.get("total_tokens", 0),
                    "Cost USD": token_summary.get("cost_usd", 0.0),
                    "Functions Found": len(result.get("submission_analysis", {}).get("functions_found", [])),
                    "Conversation Files": result.get("submission_analysis", {}).get("conversation_files", 0),
                    "Has README": result.get("submission_analysis", {}).get("has_readme", False),
                    "LLM Consensus": result.get("llm_consensus", 1)
                }
                
                # Add individual criterion scores
                for criterion, score in result.get("scores", {}).items():
                    row[f"{criterion.replace('_', ' ').title()} Score"] = score
                
                # Add per-provider token costs
                provider_breakdown = token_summary.get("by_provider", {})
                for provider, prov_data in provider_breakdown.items():
                    row[f"{provider.title()} Tokens"] = prov_data.get("tokens", 0)
                    row[f"{provider.title()} Cost"] = prov_data.get("cost", 0.0)
            
            summary_data.append(row)
        
        df = pd.DataFrame(summary_data)
        
        # Add summary statistics at the bottom
        if summary_data:
            total_cost = sum(row.get("Cost USD", 0) for row in summary_data)
            total_tokens = sum(row.get("Total Tokens", 0) for row in summary_data)
            graded_submissions = [r for r in summary_data if r.get("Status") == "Graded"]
            avg_score = sum(row.get("Total Score", 0) for row in graded_submissions) / len(graded_submissions) if graded_submissions else 0
            
            summary_row = {
                "Student ID": "SUMMARY",
                "Status": f"Processed {len(summary_data)} submissions",
                "Total Score": f"Avg: {avg_score:.1f}",
                "Letter Grade": "",
                "Total Tokens": total_tokens,
                "Cost USD": round(total_cost, 2),
                "Functions Found": "",
                "Conversation Files": "",
                "Has README": "",
                "LLM Consensus": ""
            }
            
            # Add empty row then summary
            df = pd.concat([df, pd.DataFrame([{}]), pd.DataFrame([summary_row])], ignore_index=True)
        
        df.to_excel(filename, index=False)
        print(f"Summary report with token usage saved to {filename}")


def main():
    """Main function with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description="Generalized Automated Assignment Grading System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available assignments
  python auto_grader.py --list-assignments
  
  # Dry run to estimate costs (no API calls)
  python auto_grader.py submissions/ --assignment weatherwise --dry-run
  
  # Grade without GitHub integration
  python auto_grader.py submissions/ --assignment weatherwise --no-github
  
  # Grade with GitHub integration (requires mapping file)
  python auto_grader.py submissions/ --assignment weatherwise --github --mapping student_github_mapping.json
  
  # Test with dry run first, then live grading
  python auto_grader.py submissions/ --assignment weatherwise --dry-run --no-github
  python auto_grader.py submissions/ --assignment weatherwise --no-github
        """
    )
    
    parser.add_argument(
        "submissions_folder",
        nargs='?',
        help="Path to folder containing student ZIP submissions"
    )
    
    parser.add_argument(
        "--assignment",
        required=False,
        help="Assignment name (must have corresponding config in assignments/ folder)"
    )
    
    parser.add_argument(
        "--list-assignments",
        action="store_true",
        help="List available assignments and exit"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Analyze submissions and estimate costs without making LLM API calls"
    )
    
    github_group = parser.add_mutually_exclusive_group()
    github_group.add_argument(
        "--github",
        action="store_true",
        default=False,
        help="Enable GitHub integration (requires mapping file)"
    )
    github_group.add_argument(
        "--no-github",
        action="store_true", 
        default=False,
        help="Disable GitHub integration (faster, content-only grading)"
    )
    
    parser.add_argument(
        "--mapping",
        default="student_github_mapping.json",
        help="Path to GitHub mapping file (default: student_github_mapping.json)"
    )
    
    parser.add_argument(
        "--output",
        help="Output filename for grading results (default: <assignment>_grading_results.json)"
    )
    
    parser.add_argument(
        "--assignments-dir",
        default="assignments",
        help="Path to assignments directory (default: assignments)"
    )
    
    parser.add_argument(
        "--templates-dir", 
        default="templates",
        help="Path to templates directory (default: templates)"
    )
    
    args = parser.parse_args()
    
    # Handle list assignments
    if args.list_assignments:
        config_loader = ConfigLoader(args.assignments_dir)
        assignments = config_loader.list_available_assignments()
        
        if assignments:
            print("Available assignments:")
            for assignment in assignments:
                try:
                    config = config_loader.load_assignment_config(assignment)
                    print(f"  {assignment}: {config['assignment']['name']} ({config['assignment']['type']})")
                except Exception as e:
                    print(f"  {assignment}: ERROR - {str(e)}")
        else:
            print(f"No assignments found in {args.assignments_dir}/")
        return
    
    # Validate required arguments
    if not args.submissions_folder:
        print("Error: submissions_folder is required (unless using --list-assignments)")
        parser.print_help()
        return
    
    if not args.assignment:
        print("Error: --assignment is required")
        parser.print_help()
        return
    
    # Validate assignments directory and assignment
    config_loader = ConfigLoader(args.assignments_dir)
    available_assignments = config_loader.list_available_assignments()
    
    if not available_assignments:
        print(f"❌ Error: No assignments found in {args.assignments_dir}/")
        return
    
    if args.assignment not in available_assignments:
        print(f"❌ Error: Assignment '{args.assignment}' not found")
        print(f"Available assignments: {', '.join(available_assignments)}")
        return
    
    # Determine GitHub integration setting
    if args.no_github:
        enable_github = False
    elif args.github:
        enable_github = True
    else:
        # Auto-detect based on assignment config and mapping file
        try:
            assignment_config = config_loader.load_assignment_config(args.assignment)
            github_config = config_loader.get_github_config(assignment_config)
            enable_github = github_config.get('enabled', False)
            
            if enable_github and os.path.exists(args.mapping):
                try:
                    with open(args.mapping, 'r') as f:
                        mapping_data = json.load(f)
                    if mapping_data.get('recommendation') == 'DISABLE_GITHUB_INTEGRATION':
                        enable_github = False
                        print("🤖 Auto-detected: Disabling GitHub integration based on mapping file recommendation")
                    else:
                        print("🤖 Auto-detected: Enabling GitHub integration based on assignment config and mapping file")
                except:
                    enable_github = False
                    print("🤖 Auto-detected: Disabling GitHub integration due to mapping file issues")
            elif enable_github:
                print("🤖 Auto-detected: GitHub enabled in assignment config but no mapping file found")
                enable_github = False
            else:
                print("🤖 Auto-detected: GitHub integration disabled in assignment config")
        except Exception as e:
            enable_github = False
            print(f"🤖 Auto-detected: Disabling GitHub integration due to config error: {str(e)}")
    
    # Validate submissions folder
    if not os.path.exists(args.submissions_folder):
        print(f"❌ Error: Submissions folder not found: {args.submissions_folder}")
        return
    
    # Check for ZIP files
    zip_files = [f for f in os.listdir(args.submissions_folder) if f.endswith('.zip')]
    if not zip_files:
        print(f"❌ Error: No ZIP files found in {args.submissions_folder}")
        return
    
    # Initialize grader
    if args.dry_run:
        print("🧪 Initializing Dry Run Analysis...")
    else:
        print("🚀 Initializing Automated Grading System...")
    print("=" * 60)
    
    # Get API keys from environment (only required for live grading)
    if not args.dry_run:
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not openai_key or not anthropic_key:
            print("❌ Error: Missing required API keys for live grading")
            print("   Please set OPENAI_API_KEY and ANTHROPIC_API_KEY environment variables")
            print("   Or use --dry-run flag to analyze without API calls")
            return
    else:
        # For dry run, we don't need real API keys
        openai_key = "dry-run-key"
        anthropic_key = "dry-run-key"
    
    github_token = os.getenv("GITHUB_TOKEN")
    
    if enable_github and not github_token and not args.dry_run:
        print("⚠️  Warning: GitHub integration enabled but no GITHUB_TOKEN found")
        print("   GitHub repository analysis will be limited")
    
    # Create grader instance
    try:
        grader = AutomatedGrader(
            assignment_name=args.assignment,
            openai_api_key=openai_key,
            anthropic_api_key=anthropic_key,
            github_token=github_token,
            enable_github=enable_github,
            github_mapping_file=args.mapping,
            assignments_dir=args.assignments_dir,
            templates_dir=args.templates_dir
        )
    except Exception as e:
        print(f"❌ Error initializing grader: {str(e)}")
        return
    
    print(f"📁 Processing {len(zip_files)} submissions from: {args.submissions_folder}")
    if args.dry_run:
        print("🧪 DRY RUN MODE: No API calls will be made")
    print("=" * 60)
    
    # Run batch grading
    results = grader.batch_grade(args.submissions_folder, args.output, dry_run=args.dry_run)
    
    if args.dry_run:
        print(f"\n🧪 Dry run completed! No files created.")
        print(f"   Remove --dry-run flag to execute live grading")
    else:
        output_file = args.output or f"{args.assignment}_grading_results.json"
        print(f"\n✅ Grading completed! Results saved to: {output_file}")


if __name__ == "__main__":
    main()