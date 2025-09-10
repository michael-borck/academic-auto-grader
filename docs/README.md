# Automated Grading System

A generalized, configuration-driven automated grading system for programming assignments. Supports multiple assignments through YAML configurations and Jinja2 templates.

## 🚀 Quick Start

```bash
# List available assignments
./grader list

# Complete workflow for WeatherWise assignment
./grader process-all submissions/ --assignment weatherwise --roster students.csv

# Dry run to estimate costs
./grader grade submissions/ --assignment weatherwise --dry-run
```

## 📁 Project Structure

```
automated-grader/
├── core/                           # Core grading functionality
│   ├── auto_grader.py             # Main grading engine (generalized)
│   ├── config_loader.py           # YAML configuration loader
│   ├── prompt_builder.py          # Jinja2 template-based prompt generation
│   └── github_scanner.py          # GitHub repository scanner
├── preprocessing/                  # Pre-processing pipeline
│   ├── consolidate_assignments.py # Group student files by ID
│   └── clean_zip_files.py         # Remove non-enrolled students
├── templates/                      # Jinja2 prompt templates
│   ├── base_prompt.j2             # Main grading prompt template
│   ├── github_analysis.j2         # GitHub repository analysis
│   ├── function_analysis.j2       # Required function checking
│   ├── notebook_structure.j2      # Notebook organization analysis
│   ├── conversation_analysis.j2   # AI conversation evaluation
│   ├── additional_documents.j2    # Additional document processing
│   ├── readme_analysis.j2         # README evaluation
│   └── code_sample.j2             # Code sample display
├── assignments/                    # Assignment configurations
│   └── weatherwise/
│       └── config.yaml            # WeatherWise assignment configuration
├── tools/                         # Utility tools
│   ├── assignment_generator.py    # Interactive assignment creator
│   └── config_validator.py        # Configuration validator
├── grader*                        # Unified CLI interface
└── docs/
    ├── README.md                  # This file
    ├── USAGE.md                   # Detailed usage guide
    └── ASSIGNMENTS.md             # Creating new assignments
```

## 🎯 Core Features

### ✅ Preserved from Original System
- **Multi-LLM grading** (OpenAI + Anthropic) with token tracking
- **Cost analysis** and dry-run capabilities
- **GitHub integration** with commit analysis and repository structure evaluation
- **Multiple document formats** (PDF, DOCX, Jupyter notebooks, text files)
- **Second-person feedback style** for personalized student communication
- **Comprehensive error handling** and progress tracking
- **Pre-processing workflow** integration for Blackboard downloads

### 🆕 New Generalized Features
- **Configuration-driven assignments** - Create new assignments without touching code
- **Template-based prompt generation** - Jinja2 templates for flexible, reusable prompts
- **Unified CLI interface** - Single command for complete workflows
- **Assignment generator tools** - Interactive creation of new assignment configs
- **Validation system** - Ensures assignment configurations are correct
- **Backward compatibility** - WeatherWise assignment still works exactly as before

## 🔧 Installation

1. **Clone or copy the automated-grader directory**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set up environment variables:**
   ```bash
   export OPENAI_API_KEY="your-openai-key"
   export ANTHROPIC_API_KEY="your-anthropic-key"
   export GITHUB_TOKEN="your-github-token"  # Optional, for GitHub integration
   ```
4. **Make CLI executable:**
   ```bash
   chmod +x grader
   ```

## 📋 Usage Examples

### List Available Assignments
```bash
./grader list
```

### Complete Workflow (Recommended)
```bash
# Process WeatherWise submissions with full pipeline
./grader process-all submissions/ \
  --assignment weatherwise \
  --roster students.csv
```

### Individual Steps

#### 1. Preprocessing Only
```bash
./grader preprocess submissions/ --roster students.csv
```

#### 2. GitHub Scanning Only
```bash
./grader github-scan submissions/
```

#### 3. Grading Only
```bash
# With GitHub integration
./grader grade submissions/ --assignment weatherwise --github

# Without GitHub integration (faster)
./grader grade submissions/ --assignment weatherwise --no-github

# Dry run (estimate costs)
./grader grade submissions/ --assignment weatherwise --dry-run
```

## 📊 Assignment Configuration

Each assignment is defined by a YAML configuration file in `assignments/<assignment_name>/config.yaml`.

### Example Configuration Structure
```yaml
assignment:
  name: "WeatherWise"
  description: "Intelligent Weather Analysis & Advisory System"
  type: "python_application"
  total_points: 100

context:
  requirements:
    - "Weather data retrieval and display"
    - "Natural language interface for weather queries"
    - "At least 2 data visualizations"
  
  required_functions:
    - name: "get_weather_data"
      signature: "get_weather_data(location, forecast_days=5)"
      description: "Retrieve weather data from API"
  
  file_expectations:
    notebook: required
    conversation_files: required
    readme: optional
    github: optional

rubric:
  functionality:
    weight: 15
    max_score: 15
    criteria: "Application works as expected; core functions implemented correctly"
  
  intentional_prompting:
    weight: 30
    max_score: 30
    criteria: "Documentation of AI interactions; evidence of strategic prompting techniques"
  
  # ... more criteria

github_integration:
  enabled: true
  minimum_commits: 15
  repository_analysis: true
  readme_comparison: true
```

## 🛠️ Creating New Assignments

### Option 1: Interactive Generator (Recommended)
```bash
python tools/assignment_generator.py
```

### Option 2: Copy and Modify Existing
```bash
cp -r assignments/weatherwise assignments/new_assignment
# Edit assignments/new_assignment/config.yaml
```

### Option 3: Manual Creation
Create `assignments/<name>/config.yaml` following the structure above.

### Validate Configuration
```bash
python tools/config_validator.py assignments/new_assignment/config.yaml
# Or validate all assignments
python tools/config_validator.py --all
```

## 📈 Token Usage and Cost Tracking

The system provides comprehensive token usage tracking:

- **Real-time cost estimation** during dry runs
- **Per-student cost breakdown** in results
- **Provider comparison** (OpenAI vs Anthropic efficiency)
- **Detailed token reports** saved alongside grading results

### Cost Estimation Example
```bash
./grader grade submissions/ --assignment weatherwise --dry-run
```

Output includes:
- Estimated tokens per submission
- Cost breakdown by provider
- Total estimated cost for all submissions
- Content analysis summary

## 🔄 Migration from Original System

Your existing WeatherWise workflow continues to work:

### Before (Original)
```bash
python auto_grader.py submissions/ --no-github
```

### After (Generalized)
```bash
./grader grade submissions/ --assignment weatherwise --no-github
```

The results are identical, but now you can:
- Create new assignments without code changes
- Use templates for consistent prompt structure
- Benefit from the unified CLI interface
- Access improved validation and error handling

## 🐛 Troubleshooting

### Common Issues

1. **"Assignment not found"**
   ```bash
   # List available assignments
   ./grader list
   # Validate assignment config
   python tools/config_validator.py assignments/your_assignment/config.yaml
   ```

2. **"Missing API keys"**
   ```bash
   export OPENAI_API_KEY="your-key"
   export ANTHROPIC_API_KEY="your-key"
   ```

3. **"Template errors"**
   ```bash
   # Validate templates
   python core/prompt_builder.py
   ```

4. **"GitHub integration issues"**
   ```bash
   # Run GitHub scanner separately
   ./grader github-scan submissions/
   # Or disable GitHub integration
   ./grader grade submissions/ --assignment name --no-github
   ```

### Debug Mode
Add `--dry-run` to any grading command to see what would happen without making API calls.

## 📚 Additional Documentation

- **[USAGE.md](USAGE.md)** - Detailed usage guide with advanced examples
- **[ASSIGNMENTS.md](ASSIGNMENTS.md)** - Complete guide to creating and configuring assignments
- **Original documentation** in `docs/` folder for reference

## 🤝 Contributing

1. Create new assignments in `assignments/` folder
2. Add new templates in `templates/` folder
3. Validate configurations with `tools/config_validator.py`
4. Test with dry runs before live grading

## 📝 License

This project inherits the license from the original grading system.