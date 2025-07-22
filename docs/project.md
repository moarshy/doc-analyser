# Doc Analyser Project

## Overview

Doc Analyser is a distributed system that automatically analyzes GitHub repositories' documentation to extract use cases and validate them through practical implementation. The system uses Claude Code to intelligently process documentation, identify practical use cases, and test them by implementing working code examples.

## Architecture

The system consists of three main components:

### 1. Gateway (FastAPI)
- **Purpose**: REST API gateway for external communication
- **Responsibilities**:
  - Accept repository analysis requests
  - Queue tasks for processing
  - Provide status updates and results
  - Manage job lifecycle

### 2. Worker (Celery)
- **Purpose**: Background processing of document analysis tasks
- **Responsibilities**:
  - Clone GitHub repositories
  - Analyze documentation using Claude Code
  - Extract use cases from documentation
  - Execute use cases to validate documentation quality
  - Generate comprehensive analysis reports

### 3. Frontend (Future)
- **Purpose**: Web interface for managing and viewing analysis results
- **Planned Features**:
  - Repository submission interface
  - Job status monitoring
  - Results visualization
  - Documentation quality metrics

## How It Works

### Analysis Pipeline

1. **Repository Submission**: User submits a GitHub repository URL via the API
2. **Task Queuing**: Gateway creates a Celery task for analysis
3. **Repository Processing**: Worker spins up a Docker container to:
   - Clone the repository
   - Mount a volume for results storage
   - Run analysis scripts
4. **Documentation Analysis**: Claude Code analyzes documentation to:
   - Identify use cases and examples
   - Extract practical scenarios
   - Categorize by difficulty level
5. **Use Case Validation**: Each identified use case is:
   - Implemented as working code
   - Tested for functionality
   - Evaluated against documentation accuracy
6. **Results Generation**: Comprehensive report including:
   - Use cases with implementation status
   - Documentation quality assessment
   - Suggestions for documentation improvements
   - Code examples that work

### Technology Stack

- **Message Queue**: Redis
- **API Gateway**: FastAPI
- **Task Processing**: Celery
- **Document Analysis**: Claude Code SDK
- **Container Runtime**: Docker
- **Development**: Make, Docker Compose

## Development Setup

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- Redis
- Claude Code SDK access

### Quick Start

1. **Setup Environment**:
   ```bash
   make setup
   ```

2. **Start Infrastructure**:
   ```bash
   make redis-up
   ```

3. **Run Services**:
   ```bash
   # Terminal 1: Start FastAPI gateway
   make gateway

   # Terminal 2: Start Celery worker
   make worker
   ```

### Directory Structure

```
doc-analyser/
├── backend/
│   ├── gateway/          # FastAPI application
│   ├── worker/           # Celery worker
│   └── shared/           # Shared utilities
├── docs/                 # Documentation
├── scripts/              # Utility scripts
├── docker-compose.yml    # Development services
├── Makefile             # Development commands
└── README.md
```

## Use Cases

The system is designed to help:
- **Library maintainers**: Validate documentation accuracy
- **Developers**: Understand library capabilities through tested examples
- **Technical writers**: Identify gaps in documentation
- **Teams**: Ensure documentation quality across projects

## Future Enhancements

- Web-based frontend for easy repository submission
- Batch processing for multiple repositories
- Historical analysis and trends
- Integration with CI/CD pipelines
- Support for additional documentation formats
- Enhanced visualization of results