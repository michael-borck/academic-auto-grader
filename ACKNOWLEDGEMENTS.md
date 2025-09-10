# Acknowledgements

This project builds upon and integrates several excellent open source libraries and tools. We gratefully acknowledge the contributions of these projects and their maintainers.

## 🔧 Core Dependencies

### Language Model APIs
- **[OpenAI Python Library](https://github.com/openai/openai-python)** - Official Python client for OpenAI's APIs
  - License: Apache 2.0
  - Used for: GPT-4 integration and automated assessment generation

- **[Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python)** - Official Python client for Anthropic's Claude AI
  - License: MIT
  - Used for: Claude integration and multi-LLM consensus grading

### Document Processing
- **[nbformat](https://github.com/jupyter/nbformat)** - Jupyter Notebook format reference implementation
  - License: BSD 3-Clause
  - Used for: Parsing and analyzing Jupyter notebooks from student submissions

- **[python-docx](https://github.com/python-openxml/python-docx)** - Python library for creating and updating Microsoft Word documents
  - License: MIT
  - Used for: Extracting text content from Word document submissions

- **[PyPDF2](https://github.com/py-pdf/PyPDF2)** - Pure-python PDF library
  - License: BSD 3-Clause
  - Used for: Reading and extracting text from PDF submissions

### Configuration and Templating
- **[PyYAML](https://github.com/yaml/pyyaml)** - YAML parser and emitter for Python
  - License: MIT
  - Used for: Assignment configuration files and settings management

- **[Jinja2](https://github.com/pallets/jinja)** - Modern and designer-friendly templating language for Python
  - License: BSD 3-Clause
  - Used for: Template-based prompt generation and flexible grading criteria

### Data Processing and Analysis
- **[pandas](https://github.com/pandas-dev/pandas)** - Powerful data structures and data analysis tools
  - License: BSD 3-Clause
  - Used for: Data manipulation, summary reports, and Excel export functionality

- **[openpyxl](https://github.com/theorchard/openpyxl)** - Python library to read/write Excel 2010 xlsx/xlsm/xltx/xltm files
  - License: MIT
  - Used for: Generating detailed Excel reports with grading results and analytics

### HTTP and API Communication
- **[Requests](https://github.com/psf/requests)** - Simple, elegant HTTP library for Python
  - License: Apache 2.0
  - Used for: GitHub API integration and repository analysis

## 🎯 Development Tools and Inspiration

### Version Control Integration
- **[GitHub REST API](https://docs.github.com/en/rest)** - GitHub's REST API for repository access
  - Used for: Repository analysis, commit history tracking, and development progression assessment

### Educational Technology
This project was inspired by the need for fair, consistent, and comprehensive automated assessment in programming education, particularly for assignments involving AI-assisted development.

## 🤝 Community Contributions

We welcome contributions from the educational technology and open source communities. This project aims to:

- **Democratize Quality Assessment**: Make sophisticated grading tools accessible to educators worldwide
- **Promote Transparency**: Provide open, auditable algorithms for academic assessment
- **Foster Innovation**: Enable research and development in AI-assisted education
- **Support Educators**: Reduce grading workload while maintaining assessment quality

## 📚 Educational Context

This system was developed to address the evolving needs of programming education, particularly:

- **AI-Assisted Learning**: Evaluating how students work with AI tools like ChatGPT, Claude, and Copilot
- **Modern Development Practices**: Assessing version control usage, documentation quality, and iterative development
- **Comprehensive Assessment**: Balancing code functionality, development process, and learning demonstration
- **Scalable Evaluation**: Providing detailed, personalized feedback at scale

## 🙏 Special Thanks

- **Open Source Community**: For creating and maintaining the incredible ecosystem of tools this project relies upon
- **Educational Technology Researchers**: For advancing the field of automated assessment and learning analytics
- **Programming Instructors**: Who face the daily challenge of providing meaningful feedback on student code
- **Students**: Whose diverse approaches to problem-solving and learning drive the need for flexible, fair assessment tools

---

*If you use this project in your research or educational practice, we'd love to hear about it! Please consider citing this work and sharing your experiences with the community.*

## 📄 License Compatibility

This project is released under the MIT License, which is compatible with all the dependencies listed above. The MIT License ensures maximum flexibility for educational and research use while maintaining appropriate attribution requirements.