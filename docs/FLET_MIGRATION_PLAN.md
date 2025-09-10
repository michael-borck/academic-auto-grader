# Flet GUI Migration Plan for Academic Auto Grader

## 📋 Overview
Transform the CLI-based academic-auto-grader into a user-friendly GUI application using Flet, while maintaining full CLI functionality. This will make the tool accessible to educators who prefer visual interfaces.

## 🎯 Architecture Strategy

### **Hybrid Approach: GUI + CLI Coexistence**
- Keep existing CLI functionality intact (backward compatibility)
- Add new GUI layer that wraps and extends CLI capabilities
- Share core business logic between both interfaces
- Allow advanced users to still use CLI, beginners to use GUI

## 📁 New Project Structure
```
academic-auto-grader/
├── cli/                         # Renamed from current root structure
│   ├── core/                   # (existing core logic)
│   ├── preprocessing/          # (existing preprocessing)
│   ├── templates/              # (existing templates)
│   ├── tools/                  # (existing tools)
│   └── grader                  # (existing CLI script)
├── gui/                        # NEW: Flet GUI application
│   ├── main.py                 # Flet entry point
│   ├── app/                    # GUI application modules
│   │   ├── __init__.py
│   │   ├── pages/              # Different GUI pages/screens
│   │   │   ├── welcome.py      # Welcome/setup screen
│   │   │   ├── configuration.py # Assignment selection & config
│   │   │   ├── processing.py   # Progress tracking screen
│   │   │   └── results.py      # Results viewer
│   │   ├── components/         # Reusable UI components
│   │   │   ├── file_picker.py  # Custom file selection
│   │   │   ├── progress_bar.py # Enhanced progress tracking
│   │   │   └── cost_estimator.py # Live cost estimation
│   │   ├── models/             # Data models for GUI state
│   │   └── services/           # Business logic adapters
│   │       ├── grader_service.py # Wraps CLI functionality
│   │       └── config_service.py # Configuration management
│   ├── assets/                 # GUI assets
│   │   ├── icons/              # Application icons
│   │   └── images/             # Logo, screenshots
│   └── build/                  # Build configurations & outputs
├── shared/                     # NEW: Shared utilities
│   ├── __init__.py
│   ├── config/                 # Shared configuration logic
│   ├── models/                 # Common data models
│   └── utils/                  # Utility functions
├── dist/                       # NEW: Distribution packages
│   ├── windows/               # Windows .exe builds
│   ├── macos/                 # macOS .app builds
│   └── linux/                 # Linux AppImage builds
├── assignments/               # (existing, unchanged)
├── docs/                      # (existing + GUI documentation)
└── tests/                     # NEW: Unit tests for both CLI & GUI
```

## 🚀 Implementation Phases

### **Phase 1: Foundation & Basic GUI (Week 1)**
1. **Project Restructuring**
   - Move existing code to `cli/` directory
   - Create new `gui/` and `shared/` directories
   - Update import paths and dependencies
   - Test CLI functionality still works

2. **Flet Integration**
   - Add Flet to requirements.txt
   - Create basic GUI entry point (`gui/main.py`)
   - Implement welcome screen with branding
   - Add file/folder selection dialogs

3. **Core GUI Services**
   - Create `GraderService` class to wrap CLI functionality
   - Implement basic configuration loading
   - Add assignment selection dropdown

### **Phase 2: Main Workflow GUI (Week 2)**
1. **Configuration Screen**
   - Assignment selection with descriptions
   - File/folder pickers for submissions and roster
   - Options toggles (GitHub integration, preprocessing, dry-run)
   - Real-time validation and feedback

2. **Processing Screen**
   - Progress tracking with visual progress bars
   - Live cost estimation updates
   - Real-time log display
   - Cancel/pause functionality

3. **CLI Integration**
   - Adapt existing CLI commands to work as background processes
   - Capture and parse CLI output for GUI display
   - Handle errors gracefully with user-friendly messages

### **Phase 3: Advanced Features (Week 3)**
1. **Results Viewer**
   - Embedded Excel/JSON viewer
   - Summary statistics dashboard
   - Individual student result details
   - Export options

2. **Configuration Management**
   - Visual assignment configuration editor
   - Assignment creation wizard (wraps existing tool)
   - Configuration validation with visual feedback

3. **Settings & Preferences**
   - API key management with secure storage
   - Default folder preferences
   - Theme selection (light/dark)

### **Phase 4: Distribution & Polish (Week 4)**
1. **Packaging & Building**
   - PyInstaller configurations for each platform
   - Automated build scripts
   - Icon and branding integration
   - Installer creation (optional)

2. **Testing & Documentation**
   - Cross-platform testing
   - GUI user guide with screenshots
   - Installation instructions for non-technical users
   - Video tutorials (optional)

## 🎨 GUI Design Mockups

### **Welcome Screen**
```
┌──────────────────────────────────────────────────┐
│ 🎓 Academic Auto Grader                         │
│ Configuration-driven automated grading          │
│                                                  │
│ ┌────────────────────────────────────────────┐   │
│ │  [📁] Select Submissions Folder           │   │
│ │  📂 C:/Users/Prof/Downloads/submissions   │   │
│ └────────────────────────────────────────────┘   │
│                                                  │
│ ┌────────────────────────────────────────────┐   │
│ │  [📋] Choose Assignment                    │   │
│ │  WeatherWise ▼                           │   │
│ └────────────────────────────────────────────┘   │
│                                                  │
│ Optional:                                        │
│ ┌────────────────────────────────────────────┐   │
│ │  [👥] Student Roster (CSV)                │   │
│ │  📄 students.csv                          │   │
│ └────────────────────────────────────────────┘   │
│                                                  │
│               [🚀 Continue]                     │
└──────────────────────────────────────────────────┘
```

### **Configuration Screen**
```
┌──────────────────────────────────────────────────┐
│ ⚙️ Grading Configuration                         │
│                                                  │
│ Assignment: WeatherWise                          │
│ Type: Python Application | Points: 100          │
│ Description: Intelligent Weather Analysis...     │
│                                                  │
│ 📊 Options:                                     │
│ ☑️ Enable GitHub Integration                    │
│ ☑️ Run Preprocessing Pipeline                   │
│ ☐ Dry Run (Cost Estimation Only)               │
│                                                  │
│ 💰 Estimated Cost:                              │
│ ┌────────────────────────────────────────────┐   │
│ │ Analyzing 25 submissions...                │   │
│ │ OpenAI: ~$12.50 | Anthropic: ~$8.75      │   │
│ │ Total: ~$21.25                            │   │
│ └────────────────────────────────────────────┘   │
│                                                  │
│          [🔙 Back]    [▶️ Start Grading]        │
└──────────────────────────────────────────────────┘
```

### **Processing Screen**
```
┌──────────────────────────────────────────────────┐
│ 🏃‍♂️ Grading in Progress                           │
│                                                  │
│ Overall Progress:                                │
│ ████████████████████░░░░ 80% (20/25 complete)   │
│                                                  │
│ Current: Processing student_12345                │
│ ████████████████████████ Extracting content...  │
│                                                  │
│ 💰 Cost Tracking:                               │
│ Used: $17.20 | Remaining: ~$4.05               │
│                                                  │
│ 📝 Recent Activity:                             │
│ ┌────────────────────────────────────────────┐   │
│ │ ✅ student_12344: Grade A (89/100)         │   │
│ │ ✅ student_12343: Grade B (82/100)         │   │
│ │ 🔄 student_12345: Analyzing notebook...    │   │
│ │ ⏳ student_12346: Queued                   │   │
│ └────────────────────────────────────────────┘   │
│                                                  │
│               [⏸️ Pause]  [❌ Cancel]             │
└──────────────────────────────────────────────────┘
```

### **Results Screen**
```
┌──────────────────────────────────────────────────┐
│ 📊 Grading Results                               │
│                                                  │
│ ✅ Completed: 25/25 submissions                  │
│ 💰 Total Cost: $21.18 | Time: 12 minutes        │
│                                                  │
│ 📈 Summary Statistics:                           │
│ Average Score: 78.2/100 | Grade Distribution:    │
│ A: 6 | B: 11 | C: 5 | D: 2 | F: 1              │
│                                                  │
│ 📋 Individual Results:                           │
│ ┌────────────────────────────────────────────┐   │
│ │ Student ID    | Score | Grade | GitHub     │   │
│ │ student_12344 | 89/100| A     | ✅         │   │
│ │ student_12343 | 82/100| B     | ✅         │   │
│ │ student_12342 | 76/100| C     | ❌         │   │
│ │ ...                                        │   │
│ └────────────────────────────────────────────┘   │
│                                                  │
│ [📊 View Detailed Report] [📁 Open Results]     │
│              [🔄 Grade More]                     │
└──────────────────────────────────────────────────┘
```

## 🔧 Technical Implementation Details

### **Dependencies to Add**
```python
# GUI Framework
flet>=0.21.0

# Packaging
pyinstaller>=6.0.0
auto-py-to-exe>=2.4.0  # Optional: GUI for PyInstaller

# Enhanced file handling
send2trash>=1.8.0  # Safe file deletion

# Secure credential storage
keyring>=24.0.0  # For API key management

# Async processing
asyncio  # Built-in, for background tasks
threading  # Built-in, for CLI process management
```

### **Key Integration Points**

#### **1. CLI Wrapper Service**
```python
class GraderService:
    def __init__(self):
        self.process = None
        self.progress_callback = None
        self.is_running = False
        
    async def run_grading(self, config):
        """Execute CLI commands as background process"""
        # Build CLI command from GUI config
        # Execute as subprocess with output capture
        # Parse output for progress updates
        # Emit progress events to GUI
        
    def estimate_cost(self, config):
        """Run dry-run command for cost estimation"""
        # Run CLI dry-run command
        # Parse cost estimation output
        # Return structured cost data
        
    def cancel_grading(self):
        """Safely cancel ongoing grading process"""
        # Terminate subprocess gracefully
        # Clean up temporary files
        # Reset service state
```

#### **2. Real-time Progress Tracking**
```python
class ProgressTracker:
    def parse_cli_output(self, line):
        """Parse CLI output lines for progress indicators"""
        # Extract student IDs, completion status, costs
        # Update GUI progress bars and status
        # Handle error messages and warnings
        
    def calculate_progress(self, completed, total):
        """Calculate and format progress information"""
        # Percentage complete
        # Time estimates
        # Cost tracking
```

#### **3. Configuration Bridge**
```python
class ConfigService:
    def load_assignments(self):
        """Use existing ConfigLoader for GUI"""
        # Load all available assignments
        # Format for GUI dropdown/selection
        # Include descriptions and metadata
        
    def validate_paths(self, submissions_folder):
        """Validate user input paths"""
        # Check folder exists, contains ZIP files
        # Count submissions for estimation
        # Return validation status for GUI
        
    def save_preferences(self, prefs):
        """Save user preferences"""
        # API keys (securely with keyring)
        # Default folders
        # UI preferences
```

#### **4. Secure API Key Management**
```python
class APIKeyManager:
    def store_key(self, service, key):
        """Securely store API key using keyring"""
        # Use system keyring for secure storage
        # Different storage per service (OpenAI, Anthropic)
        
    def get_key(self, service):
        """Retrieve stored API key"""
        # Get from secure storage
        # Handle missing keys gracefully
        
    def validate_key(self, service, key):
        """Test API key validity"""
        # Make test API call
        # Return validation status
```

## 📦 Distribution Strategy

### **Build Configurations**

#### **Windows (.exe)**
```bash
flet build windows \
  --name "Academic Auto Grader" \
  --icon assets/icons/grader.ico \
  --add-data "assignments;assignments" \
  --add-data "templates;templates" \
  --exclude-module tkinter \
  --onefile
```

#### **macOS (.app)**
```bash
flet build macos \
  --name "Academic Auto Grader" \
  --icon assets/icons/grader.icns \
  --add-data "assignments:assignments" \
  --add-data "templates:templates" \
  --bundle-identifier "edu.university.academic-auto-grader"
```

#### **Linux (AppImage)**
```bash
flet build linux \
  --name "academic-auto-grader" \
  --icon assets/icons/grader.png \
  --add-data "assignments:assignments" \
  --add-data "templates:templates"
```

### **Installation Options**

#### **1. Download & Run (Target: Non-technical educators)**
- Single executable file per platform
- No Python installation required
- Simple double-click to launch
- Includes all dependencies and templates
- Size: ~50-100MB per platform

#### **2. Python Package (Technical users)**
```bash
# Install with GUI support
pip install academic-auto-grader[gui]

# Launch GUI
grader-gui

# Use CLI (unchanged)
grader grade submissions/ --assignment weatherwise
```

#### **3. Portable Package**
- ZIP with executable + sample data
- Perfect for workshop distributions
- Includes tutorial files and documentation
- No installation required

### **Automated Building**
```yaml
# GitHub Actions workflow
name: Build GUI Executables
on: [push, release]
jobs:
  build:
    strategy:
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install flet pyinstaller
      - name: Build executable
        run: flet build ${{ matrix.os }}
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: ${{ matrix.os }}-executable
          path: dist/
```

## 🎯 User Experience Design

### **Target User Personas**

#### **1. Tech-Savvy Educator (40%)**
- Comfortable with command line but prefers GUI
- Wants full control and visibility
- Uses advanced features like cost estimation
- Appreciates detailed progress tracking

#### **2. Non-Technical Educator (50%)**
- Intimidated by command line
- Wants simple, guided workflow
- Needs clear error messages and help
- Values visual feedback and confirmation

#### **3. Teaching Assistant (10%)**
- Processes multiple assignment types
- Needs batch operations
- Values efficiency and shortcuts
- May use both CLI and GUI

### **Accessibility Considerations**
- **High contrast mode** support
- **Keyboard navigation** for all functions
- **Screen reader compatibility** with proper labels
- **Large font options** for readability
- **Color-blind friendly** design choices

### **Error Handling Strategy**
- **Progressive disclosure** - simple errors shown first, details on demand
- **Actionable messages** - always suggest next steps
- **Recovery options** - ability to retry, skip, or modify settings
- **Context preservation** - remember user choices during error resolution

## 🔄 Migration Strategy

### **Backwards Compatibility**
- **CLI unchanged** - all existing scripts and workflows continue to work
- **Configuration files** - same YAML format used by both interfaces
- **Output formats** - identical results from CLI and GUI
- **API compatibility** - same core grading logic used by both

### **Gradual Adoption**
1. **Phase 1**: Release GUI alongside CLI, market both options
2. **Phase 2**: User feedback and iterative improvements
3. **Phase 3**: GUI becomes primary interface, CLI remains available
4. **Phase 4**: Consider web interface for institutional deployments

### **Data Migration**
- No migration needed - both interfaces use same config format
- User preferences stored in platform-appropriate locations
- Easy export/import of settings between installations

## 🎯 Benefits Analysis

### **For Educators**
- **Reduced barrier to entry** - from 30+ minute setup to 2-minute download
- **Visual feedback** during long processing operations
- **Cost transparency** before committing to API usage
- **Error prevention** through validation and guided workflows
- **Professional appearance** increases confidence and adoption

### **For Students (Indirect)**
- **Faster feedback** - easier for instructors to use = more frequent grading
- **Consistent grading** - GUI reduces human error in configuration
- **Better feedback quality** - instructors can focus on content, not technical issues

### **For Institutions**
- **Lower support burden** - fewer technical support requests
- **Wider adoption** - more faculty can use the system
- **Professional image** - polished tools reflect well on institution
- **Scalability** - easier to train new staff on GUI vs CLI

### **For Open Source Community**
- **Broader appeal** - attracts non-technical contributors
- **Better documentation** - GUI serves as interactive documentation
- **Increased usage** - more users = more feedback and contributions
- **Professional recognition** - polished tools get more academic citations

## 📊 Success Metrics

### **Adoption Metrics**
- **Download/install rate** of GUI vs CLI packages
- **User retention** - how often users return to the tool
- **Error rates** - frequency of user-reported issues
- **Feature usage** - which GUI features are most/least used

### **Performance Metrics**
- **Time to first successful grade** for new users
- **Task completion rate** - percentage of users who complete full workflow
- **User satisfaction scores** via in-app feedback
- **Support request volume** compared to CLI-only period

### **Technical Metrics**
- **Build success rate** across platforms
- **Startup time** and responsiveness
- **Memory usage** and resource efficiency
- **Crash rates** and error handling effectiveness

## 🚧 Risks and Mitigation

### **Technical Risks**
- **Cross-platform compatibility issues**
  - *Mitigation*: Automated testing on all platforms, early beta testing
- **Large executable sizes**
  - *Mitigation*: Optimize dependencies, consider streaming updates
- **Performance degradation**
  - *Mitigation*: Profile early, optimize hot paths, async operations

### **User Experience Risks**
- **Feature creep** making GUI too complex
  - *Mitigation*: Progressive disclosure, user testing, minimal viable product approach
- **Loss of CLI power user features**
  - *Mitigation*: Maintain CLI, add advanced GUI modes
- **Poor error handling**
  - *Mitigation*: Comprehensive error testing, user feedback loops

### **Maintenance Risks**
- **Double maintenance burden** (CLI + GUI)
  - *Mitigation*: Shared core logic, automated testing, clear architecture boundaries
- **Platform-specific bugs**
  - *Mitigation*: Standardized build process, user feedback channels, rapid release cycle

## 🎯 Future Enhancements

### **Phase 5+ Features (Post-MVP)**
- **Web interface** for institutional deployments
- **Batch assignment processing** for multiple courses
- **Integration APIs** for LMS systems (Canvas, Moodle, Blackboard)
- **Analytics dashboard** for department-level insights
- **Mobile companion app** for progress monitoring
- **Cloud deployment options** for processing-heavy workloads
- **Collaborative grading** for multiple instructors
- **Student self-assessment tools** integrated workflow

### **Enterprise Features**
- **Single sign-on (SSO)** integration
- **Audit logging** for compliance
- **Role-based access control**
- **Institutional branding** customization
- **API rate limiting** and quota management
- **Bulk user management**

This comprehensive plan provides a roadmap for transforming the academic-auto-grader from a powerful but technical CLI tool into an accessible, professional-grade application suitable for widespread adoption in educational institutions.