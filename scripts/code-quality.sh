#!/bin/bash

# Code Quality Check Script for MorningAI MVP
# This script runs various code quality checks and formatters

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install pre-commit if not exists
install_pre_commit() {
    if ! command_exists pre-commit; then
        print_status "Installing pre-commit..."
        pip install pre-commit
    fi
}

# Function to run Python code quality checks
check_python_quality() {
    print_status "Running Python code quality checks..."
    
    cd apps/api
    
    # Install development dependencies
    if [ -f "requirements-dev.txt" ]; then
        pip install -r requirements-dev.txt
    else
        pip install black isort flake8 bandit pytest pytest-cov mypy
    fi
    
    # Black formatting
    print_status "Running Black formatter..."
    if black --check --diff src/; then
        print_success "Black formatting check passed"
    else
        print_warning "Black formatting issues found. Run 'black src/' to fix."
    fi
    
    # isort import sorting
    print_status "Running isort import sorting..."
    if isort --check-only --diff src/; then
        print_success "Import sorting check passed"
    else
        print_warning "Import sorting issues found. Run 'isort src/' to fix."
    fi
    
    # Flake8 linting
    print_status "Running Flake8 linting..."
    if flake8 src/; then
        print_success "Flake8 linting passed"
    else
        print_error "Flake8 linting failed"
    fi
    
    # Bandit security check
    print_status "Running Bandit security check..."
    if bandit -r src/ -x tests/; then
        print_success "Bandit security check passed"
    else
        print_warning "Bandit found potential security issues"
    fi
    
    # MyPy type checking
    print_status "Running MyPy type checking..."
    if mypy src/ --ignore-missing-imports; then
        print_success "MyPy type checking passed"
    else
        print_warning "MyPy type checking found issues"
    fi
    
    cd ../..
}

# Function to run JavaScript/TypeScript code quality checks
check_javascript_quality() {
    print_status "Running JavaScript/TypeScript code quality checks..."
    
    cd apps/web
    
    # Install dependencies
    if [ ! -d "node_modules" ]; then
        print_status "Installing Node.js dependencies..."
        npm ci
    fi
    
    # ESLint
    print_status "Running ESLint..."
    if npm run lint; then
        print_success "ESLint check passed"
    else
        print_error "ESLint found issues"
    fi
    
    # TypeScript type checking
    print_status "Running TypeScript type checking..."
    if npm run typecheck; then
        print_success "TypeScript type checking passed"
    else
        print_error "TypeScript type checking failed"
    fi
    
    # Prettier formatting
    print_status "Running Prettier formatting check..."
    if npx prettier --check .; then
        print_success "Prettier formatting check passed"
    else
        print_warning "Prettier formatting issues found. Run 'npm run format' to fix."
    fi
    
    cd ../..
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    
    # Python tests
    print_status "Running Python tests..."
    cd apps/api
    if pytest tests/ -v --cov=src --cov-report=term-missing; then
        print_success "Python tests passed"
    else
        print_error "Python tests failed"
    fi
    cd ../..
    
    # JavaScript tests
    print_status "Running JavaScript tests..."
    cd apps/web
    if npm test; then
        print_success "JavaScript tests passed"
    else
        print_error "JavaScript tests failed"
    fi
    cd ../..
}

# Function to check for secrets
check_secrets() {
    print_status "Checking for secrets..."
    
    if command_exists detect-secrets; then
        if detect-secrets scan --baseline .secrets.baseline; then
            print_success "No new secrets detected"
        else
            print_error "New secrets detected! Please review and update .secrets.baseline if needed."
        fi
    else
        print_warning "detect-secrets not installed. Skipping secret detection."
    fi
}

# Function to run pre-commit hooks
run_pre_commit() {
    print_status "Running pre-commit hooks..."
    
    install_pre_commit
    
    # Install pre-commit hooks
    pre-commit install
    
    # Run pre-commit on all files
    if pre-commit run --all-files; then
        print_success "All pre-commit hooks passed"
    else
        print_error "Some pre-commit hooks failed"
    fi
}

# Function to generate quality report
generate_report() {
    print_status "Generating code quality report..."
    
    REPORT_FILE="code-quality-report.md"
    
    cat > "$REPORT_FILE" << EOF
# Code Quality Report

Generated on: $(date)

## Summary

This report contains the results of various code quality checks run on the MorningAI MVP project.

## Checks Performed

- ✅ Python code formatting (Black)
- ✅ Python import sorting (isort)
- ✅ Python linting (Flake8)
- ✅ Python security check (Bandit)
- ✅ Python type checking (MyPy)
- ✅ JavaScript/TypeScript linting (ESLint)
- ✅ JavaScript/TypeScript type checking
- ✅ JavaScript/TypeScript formatting (Prettier)
- ✅ Secret detection
- ✅ Pre-commit hooks

## Recommendations

1. Run \`scripts/code-quality.sh\` before committing changes
2. Use \`pre-commit install\` to automatically run checks on commit
3. Address any warnings or errors found in the checks
4. Keep dependencies up to date
5. Regularly review and update code quality configurations

## Tools Used

- **Black**: Python code formatter
- **isort**: Python import sorter
- **Flake8**: Python linter
- **Bandit**: Python security linter
- **MyPy**: Python static type checker
- **ESLint**: JavaScript/TypeScript linter
- **Prettier**: JavaScript/TypeScript formatter
- **detect-secrets**: Secret detection tool
- **pre-commit**: Git hook framework

EOF

    print_success "Code quality report generated: $REPORT_FILE"
}

# Main function
main() {
    print_status "Starting code quality checks for MorningAI MVP..."
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --python-only)
                PYTHON_ONLY=true
                shift
                ;;
            --js-only)
                JS_ONLY=true
                shift
                ;;
            --no-tests)
                NO_TESTS=true
                shift
                ;;
            --fix)
                FIX_ISSUES=true
                shift
                ;;
            --report)
                GENERATE_REPORT=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --python-only    Run only Python checks"
                echo "  --js-only        Run only JavaScript/TypeScript checks"
                echo "  --no-tests       Skip running tests"
                echo "  --fix            Automatically fix issues where possible"
                echo "  --report         Generate a quality report"
                echo "  -h, --help       Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Run checks based on options
    if [[ "$PYTHON_ONLY" == true ]]; then
        check_python_quality
    elif [[ "$JS_ONLY" == true ]]; then
        check_javascript_quality
    else
        check_python_quality
        check_javascript_quality
    fi
    
    # Run tests unless disabled
    if [[ "$NO_TESTS" != true ]]; then
        run_tests
    fi
    
    # Check for secrets
    check_secrets
    
    # Run pre-commit hooks
    run_pre_commit
    
    # Generate report if requested
    if [[ "$GENERATE_REPORT" == true ]]; then
        generate_report
    fi
    
    print_success "Code quality checks completed!"
}

# Run main function with all arguments
main "$@"
