#!/bin/bash
# run_tests.sh - Test execution script

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse arguments
RUN_UNIT=true
RUN_INTEGRATION=true
RUN_MANUAL=false
COVERAGE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit-only)
            RUN_INTEGRATION=false
            shift
            ;;
        --integration-only)
            RUN_UNIT=false
            shift
            ;;
        --manual)
            RUN_MANUAL=true
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --unit-only        Run only unit tests"
            echo "  --integration-only Run only integration tests"
            echo "  --manual          Run manual verification"
            echo "  --coverage        Generate coverage report"
            echo "  --verbose, -v     Verbose output"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check pytest
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}❌ pytest not installed${NC}"
    echo "Install: pip install pytest pytest-asyncio pytest-cov"
    exit 1
fi

export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Build command
PYTEST_CMD="pytest"
[ "$VERBOSE" = true ] && PYTEST_CMD="$PYTEST_CMD -v" || PYTEST_CMD="$PYTEST_CMD -q"
[ "$COVERAGE" = true ] && PYTEST_CMD="$PYTEST_CMD --cov=. --cov-report=html --cov-report=term-missing"

EXIT_CODE=0

if [ "$RUN_MANUAL" = true ]; then
    echo -e "${BLUE}Running Manual Tests...${NC}"
    python tests/manual/test_quick_verification.py || EXIT_CODE=1
fi

if [ "$RUN_UNIT" = true ]; then
    echo -e "${BLUE}Running Unit Tests...${NC}"
    $PYTEST_CMD tests/unit/ || EXIT_CODE=1
fi

if [ "$RUN_INTEGRATION" = true ]; then
    echo -e "${BLUE}Running Integration Tests...${NC}"
    $PYTEST_CMD tests/integration/ || EXIT_CODE=1
fi

if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
else
    echo -e "${RED}⚠️  Some tests failed${NC}"
fi

exit $EXIT_CODE
