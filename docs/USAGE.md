# Detailed Usage Guide

This guide covers advanced usage patterns, customization options, and troubleshooting for the Automated Grading System.

## 📋 Table of Contents

1. [Command Reference](#command-reference)
2. [Assignment Configuration](#assignment-configuration)
3. [Template Customization](#template-customization)
4. [Cost Management](#cost-management)
5. [GitHub Integration](#github-integration)
6. [Troubleshooting](#troubleshooting)
7. [Advanced Workflows](#advanced-workflows)

## 🎯 Command Reference

### Unified CLI (`./grader`)

#### `list` - List Available Assignments
```bash
./grader list [--assignments-dir PATH]
```

Shows all configured assignments with their descriptions and GitHub integration status.

#### `preprocess` - Run Preprocessing Pipeline
```bash
./grader preprocess FOLDER [OPTIONS]
```

**Options:**
- `--roster FILE` - Student roster CSV for filtering
- `--consolidate` - Group files by student ID (default: true)
- `--clean` - Remove non-enrolled students (requires --roster)
- `--all` - Run all preprocessing steps

**Examples:**
```bash
# Basic preprocessing
./grader preprocess submissions/

# With roster filtering
./grader preprocess submissions/ --roster students.csv

# Full preprocessing pipeline
./grader preprocess submissions/ --roster students.csv --all
```

#### `github-scan` - Scan for GitHub Repositories
```bash
./grader github-scan FOLDER
```

Analyzes submissions for GitHub URLs and accessible repositories. Creates `student_github_mapping.json` for use in grading.

#### `grade` - Run Automated Grading
```bash
./grader grade FOLDER --assignment NAME [OPTIONS]
```

**Required:**
- `FOLDER` - Path to submissions folder
- `--assignment NAME` - Assignment identifier

**Options:**
- `--dry-run` - Estimate costs without API calls
- `--github` / `--no-github` - Enable/disable GitHub integration
- `--mapping FILE` - GitHub mapping file (default: student_github_mapping.json)
- `--output FILE` - Results filename
- `--assignments-dir PATH` - Assignments directory (default: assignments)
- `--templates-dir PATH` - Templates directory (default: templates)

**Examples:**
```bash
# Dry run for cost estimation
./grader grade submissions/ --assignment weatherwise --dry-run

# Grade without GitHub
./grader grade submissions/ --assignment weatherwise --no-github

# Grade with custom output
./grader grade submissions/ --assignment weatherwise --output my_results.json
```

#### `process-all` - Complete Workflow
```bash
./grader process-all FOLDER --assignment NAME [OPTIONS]
```

Runs the complete pipeline: preprocess → github-scan → grade

**Options:**
- All options from `grade` command
- `--roster FILE` - Student roster for preprocessing
- `--skip-preprocess` - Skip preprocessing steps
- `--skip-github` - Skip GitHub scanning

**Examples:**
```bash
# Complete workflow
./grader process-all submissions/ --assignment weatherwise --roster students.csv

# Skip preprocessing (already done)
./grader process-all submissions/ --assignment weatherwise --skip-preprocess

# Dry run of complete workflow
./grader process-all submissions/ --assignment weatherwise --dry-run
```

## 📊 Assignment Configuration

### Configuration File Structure

Each assignment requires a `config.yaml` file in `assignments/<assignment_name>/`:

```yaml
assignment:
  name: "Assignment Display Name"
  description: "Brief description of what students need to build"
  type: "python_application"  # or web_application, data_analysis, etc.
  total_points: 100

context:
  requirements:
    - "List of requirements"
    - "What students need to implement"
    - "Expected deliverables"
  
  required_functions:
    - name: "function_name"
      signature: "function_name(param1, param2)"
      description: "What this function should do"
  
  file_expectations:
    notebook: required      # or optional
    conversation_files: required
    readme: optional
    github: optional

rubric:
  criterion_name:
    weight: 30             # Percentage weight (must sum to 100)
    max_score: 30          # Maximum points for this criterion
    criteria: "Description of what this criterion evaluates"

github_integration:
  enabled: true
  minimum_commits: 15
  repository_analysis: true
  readme_comparison: true
```

### Configuration Guidelines

#### Assignment Types
- `python_application` - Python programs/applications
- `web_application` - Web development projects
- `data_analysis` - Data science/analysis projects
- `machine_learning` - ML/AI projects
- Custom string for other types

#### Rubric Design
- **Weights must sum to 100%**
- **Max scores typically equal weights**
- **Include AI interaction criteria** for assignments involving AI tools
- **Standard criteria:**
  - `functionality` (15-25%) - Core features working
  - `code_quality` (10-15%) - Code structure and documentation
  - `intentional_prompting` (20-35%) - AI interaction quality
  - `technical_implementation` (10-15%) - Technical execution

#### Required Functions
- **Specify exact function names** to check for implementation
- **Include realistic signatures** for better analysis
- **Provide clear descriptions** for context

### Creating New Assignments

#### Method 1: Interactive Generator
```bash
python tools/assignment_generator.py
```

Follow the prompts to create a complete configuration.

#### Method 2: Copy and Modify
```bash
# Copy existing assignment
cp -r assignments/weatherwise assignments/new_assignment

# Edit the configuration
nano assignments/new_assignment/config.yaml

# Validate
python tools/config_validator.py assignments/new_assignment/config.yaml
```

#### Method 3: From Scratch
```bash
# Create directory
mkdir assignments/my_assignment

# Create config file
nano assignments/my_assignment/config.yaml

# Validate
python tools/config_validator.py assignments/my_assignment/config.yaml
```

## 🎨 Template Customization

### Template System Overview

The system uses Jinja2 templates for generating grading prompts:

- **`base_prompt.j2`** - Main template that includes all others
- **`github_analysis.j2`** - GitHub repository analysis
- **`function_analysis.j2`** - Required function checking
- **`notebook_structure.j2`** - Jupyter notebook organization
- **`conversation_analysis.j2`** - AI conversation evaluation
- **Additional templates** for specific content types

### Available Template Variables

Templates have access to:

```jinja2
{{ assignment.name }}                    # Assignment name
{{ assignment.description }}             # Assignment description
{{ assignment.total_points }}            # Total points
{{ rubric }}                            # Complete rubric configuration
{{ github_integration.enabled }}        # GitHub integration status

{{ submission.student_id }}             # Student identifier
{{ functions_found }}                   # List of implemented function names
{{ function_implementations }}          # Dict of function code
{{ code_cells }}                        # Jupyter notebook code cells
{{ conversation_files }}                # AI conversation files
{{ readme_content }}                    # README file content
{{ github_info }}                       # GitHub repository data
```

### Customizing Templates

#### Modify Existing Templates
```bash
# Edit a template
nano templates/function_analysis.j2

# Test changes with dry run
./grader grade submissions/ --assignment name --dry-run
```

#### Create Assignment-Specific Templates
```bash
# Create assignment-specific template directory
mkdir templates/custom_assignment

# Copy and modify templates
cp templates/*.j2 templates/custom_assignment/

# Use custom templates
./grader grade submissions/ --assignment name --templates-dir templates/custom_assignment
```

#### Template Best Practices
1. **Preserve variable names** used by the prompt builder
2. **Test with dry runs** before live grading
3. **Maintain consistent formatting** for JSON output requirements
4. **Use conditional blocks** for optional features:
   ```jinja2
   {% if github_integration.enabled %}
   GitHub analysis content
   {% endif %}
   ```

## 💰 Cost Management

### Cost Estimation (Dry Runs)

Always run a dry run first to estimate costs:

```bash
./grader grade submissions/ --assignment weatherwise --dry-run
```

**Dry run output includes:**
- Token estimates per submission
- Cost breakdown by provider (OpenAI, Anthropic)
- Total estimated cost
- Content analysis summary (functions found, conversation files, etc.)

### Cost Optimization Strategies

#### 1. GitHub Integration
- **Enable** for assignments where repository quality matters
- **Disable** for content-only grading to reduce token usage:
  ```bash
  ./grader grade submissions/ --assignment name --no-github
  ```

#### 2. Provider Selection
- **Anthropic (Claude)** - Generally more cost-effective for longer prompts
- **OpenAI (GPT-4)** - May provide different perspectives
- System uses both by default and aggregates results

#### 3. Content Filtering
- The system automatically skips empty files and handles errors gracefully
- Large files are truncated to reasonable limits
- Consider preprocessing to remove unnecessary files

### Cost Tracking and Reporting

The system generates detailed cost reports:

#### Token Usage Report (`*_token_report.json`)
```json
{
  "summary": {
    "total": {"tokens": 45000, "cost_usd": 8.50},
    "by_provider": {
      "openai": {"tokens": 22000, "cost_usd": 5.20},
      "anthropic": {"tokens": 23000, "cost_usd": 3.30}
    }
  },
  "top_expensive_students": [...],
  "provider_comparison": {...}
}
```

#### Summary Excel Report (`*_summary.xlsx`)
- Per-student costs and scores
- Provider breakdown
- Content analysis statistics
- Aggregate statistics

## 🐙 GitHub Integration

### GitHub Integration Workflow

1. **Scan submissions** for GitHub URLs and usernames
2. **Cross-reference** with accessible repositories
3. **Extract repository data** (commits, structure, README)
4. **Integrate into grading** prompt and rubric

### Setting Up GitHub Integration

#### 1. Get GitHub Token
```bash
# Create personal access token at https://github.com/settings/tokens
export GITHUB_TOKEN="your_token_here"
```

#### 2. Run GitHub Scanner
```bash
./grader github-scan submissions/
```

This creates `student_github_mapping.json` with recommendations.

#### 3. Use in Grading
```bash
# Automatic detection based on mapping file
./grader grade submissions/ --assignment weatherwise

# Force enable
./grader grade submissions/ --assignment weatherwise --github

# Force disable
./grader grade submissions/ --assignment weatherwise --no-github
```

### GitHub Integration Features

#### Repository Analysis
- **Commit history** and quality assessment
- **Repository structure** analysis
- **README comparison** between GitHub and submission
- **Development progression** tracking

#### Grading Impact
- **Technical Implementation** score considers repository quality
- **Version Control** practices evaluation
- **Documentation** quality (GitHub README vs submission README)
- **Development Process** assessment through commit messages

### Troubleshooting GitHub Integration

#### Common Issues
1. **Rate limiting** - Add delays or reduce concurrent requests
2. **Private repositories** - Ensure token has appropriate permissions
3. **False positives** - Review and update ignore lists in scanner
4. **Missing repositories** - Some students may not have provided GitHub URLs

#### Debugging
```bash
# Test GitHub token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Run scanner with debugging
python core/github_scanner.py  # See detailed output

# Check mapping file
cat student_github_mapping.json | jq '.recommendation'
```

## 🔧 Troubleshooting

### Common Error Messages

#### "Assignment not found"
```bash
# Check available assignments
./grader list

# Validate assignment config
python tools/config_validator.py assignments/assignment_name/config.yaml
```

#### "Missing API keys"
```bash
# Set required environment variables
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"

# Test API connectivity
python -c "import openai; print('OpenAI key works')"
```

#### "Template rendering errors"
```bash
# Test template system
python core/prompt_builder.py

# Validate template syntax
python -c "from jinja2 import Template; Template(open('templates/base_prompt.j2').read())"
```

#### "JSON parsing errors from LLM"
- LLM responses sometimes contain malformed JSON
- System attempts to extract JSON automatically
- Check raw responses in detailed results
- Consider adjusting prompt templates for clearer JSON requirements

### Performance Issues

#### Slow Processing
1. **Disable GitHub integration** for faster processing
2. **Use dry runs** to test without API calls
3. **Process smaller batches** if memory constrained
4. **Check network connectivity** for API calls

#### High Token Usage
1. **Review submission content** - remove large unnecessary files
2. **Optimize templates** - reduce prompt length where possible
3. **Use dry runs** to estimate before processing
4. **Consider content filtering** for large submissions

### Debugging Mode

Enable verbose output:
```bash
# Add debugging to any command
PYTHONPATH=. python -m pdb core/auto_grader.py submissions/ --assignment name --dry-run
```

## 🚀 Advanced Workflows

### Batch Processing Multiple Assignments
```bash
# Process different assignments
./grader process-all submissions1/ --assignment assignment1 --roster roster1.csv
./grader process-all submissions2/ --assignment assignment2 --roster roster2.csv
```

### Custom Preprocessing
```bash
# Run only specific preprocessing steps
./grader preprocess raw_downloads/ --roster students.csv
# Move processed files
mv raw_downloads/processed_submissions/* submissions/
# Then grade
./grader grade submissions/ --assignment name --skip-preprocess
```

### Integration with External Systems
```bash
# Export results to custom format
python -c "
import json
results = json.load(open('results.json'))
# Process results for external system
"
```

### Continuous Integration
```bash
#!/bin/bash
# CI script for automated grading
set -e

# Validate configurations
python tools/config_validator.py --all

# Process submissions
./grader process-all submissions/ --assignment $ASSIGNMENT --roster students.csv

# Upload results to learning management system
# (custom integration code)
```

### Multiple Assignment Types in One Batch
```bash
# Grade different assignment types
for assignment in weatherwise data_analysis web_project; do
    if [ -d "submissions_$assignment" ]; then
        ./grader process-all "submissions_$assignment/" --assignment "$assignment"
    fi
done
```

This completes the detailed usage guide. The system is designed to be flexible and extensible while maintaining the reliability and thoroughness of the original grading system.