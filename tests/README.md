# Test Suite Documentation

## 📋 Overview

Complete test suite for Persian Deal Analyzer project covering manual tests, unit tests, integration tests, and fixtures.

## 🗂️ Directory Structure

```
tests/
├── README.md                    # This file
├── conftest.py                  # Shared pytest fixtures
├── manual/                      # Manual verification tests
│   ├── test_analytics_manual.py
│   └── README.md
├── unit/                        # Unit tests for individual components
│   ├── test_database.py
│   ├── test_repositories.py
│   ├── test_deal_service.py
│   ├── test_sentiment_service.py
│   ├── test_analytics_service.py
│   └── README.md
├── integration/                 # Integration tests for full workflows
│   ├── test_mcp_server.py
│   ├── test_end_to_end.py
│   ├── test_gradio_interface.py
│   └── README.md
└── fixtures/                    # Test data and fixtures
    ├── sample_deals.py
    ├── sample_activities.py
    └── sample_agents.py
```

## 🚀 Quick Start

### Run All Tests
```bash
# From project root
pytest tests/

# With coverage
pytest tests/ --cov=. --cov-report=html

# Verbose output
pytest tests/ -v
```

### Run Specific Test Suites
```bash
# Manual tests only
python tests/manual/test_analytics_manual.py

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_analytics_service.py

# Specific test function
pytest tests/unit/test_analytics_service.py::test_health_score_calculation
```

## 📊 Test Categories

### Manual Tests (`tests/manual/`)
**Purpose:** Quick verification that services are working
**When to run:** After major changes, before deployment
**Requirements:** Live database connection

**Tests:**
- ✅ Analytics service functionality
- ✅ Database connectivity
- ✅ Service creation and initialization

### Unit Tests (`tests/unit/`)
**Purpose:** Test individual components in isolation
**When to run:** During development, in CI/CD
**Requirements:** Mock database, no external dependencies

**Coverage:**
- Database manager operations
- Repository CRUD operations
- Service business logic
- Helper functions
- Edge cases and error handling

### Integration Tests (`tests/integration/`)
**Purpose:** Test components working together
**When to run:** Before deployment, in staging
**Requirements:** Test database, all services running

**Coverage:**
- MCP server full workflow
- End-to-end deal analysis
- Gradio interface interactions
- Multi-service coordination

## 🎯 Test Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Database Layer | 80%+ | TBD |
| Services Layer | 85%+ | TBD |
| MCP Server | 75%+ | TBD |
| Repositories | 90%+ | TBD |
| **Overall** | **80%+** | **TBD** |

## 📝 Writing New Tests

### Unit Test Template
```python
import pytest
from services.your_service import YourService

class TestYourService:
    """Test suite for YourService"""
    
    def setup_method(self):
        """Setup before each test"""
        self.service = YourService()
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        result = self.service.do_something()
        assert result is not None
    
    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ServiceError):
            self.service.invalid_operation()
```

### Integration Test Template
```python
import pytest
import asyncio

@pytest.mark.asyncio
async def test_full_workflow(test_db, test_repositories):
    """Test complete workflow"""
    # Setup
    service = AnalyticsService(test_repositories)
    
    # Execute
    result = await service.analyze_deal_comprehensive("test-id")
    
    # Verify
    assert result["health_score"] > 0
    assert "insights" in result
```

## 🔧 Test Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --cov-report=term-missing
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### conftest.py
Shared fixtures across all tests:
- Database connections
- Sample data
- Mock services
- Test configuration

## 🐛 Troubleshooting

### Tests Failing to Import Modules
```bash
# Ensure you're in project root
cd /home/challenger/Desktop/AI-agent

# Set PYTHONPATH
export PYTHONPATH=/home/challenger/Desktop/AI-agent:$PYTHONPATH

# Run tests
pytest tests/
```

### Database Connection Issues
```bash
# Check .env configuration
cat .env | grep DB_

# Test connection manually
python -c "from database.database import create_database_manager; db = create_database_manager(); print(db.test_connection())"
```

### Mock Data Issues
```bash
# Regenerate fixtures
python tests/fixtures/sample_deals.py
```

## 📈 Continuous Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ --cov
```

## 📚 Best Practices

### DO ✅
- Write tests before fixing bugs
- Test edge cases and error conditions
- Use descriptive test names
- Keep tests independent
- Mock external dependencies
- Use fixtures for common setup
- Aim for 80%+ coverage

### DON'T ❌
- Test implementation details
- Write flaky tests
- Have tests depend on each other
- Commit commented-out tests
- Skip writing tests for "simple" code
- Test external libraries

## 🎯 Test Metrics

Track these metrics:
- **Coverage:** Line and branch coverage
- **Performance:** Test execution time
- **Reliability:** Flaky test count
- **Maintenance:** Tests per feature

## 📞 Need Help?

- Check test-specific README in each directory
- Review conftest.py for available fixtures
- See example tests in each category
- Check troubleshooting section above

## 🔄 Test Lifecycle

1. **Write failing test** - TDD approach
2. **Implement feature** - Make test pass
3. **Run test suite** - Ensure no regression
4. **Check coverage** - Add tests if needed
5. **Review & commit** - Tests + code together

## 📅 Maintenance

- **Weekly:** Review test coverage
- **Monthly:** Update fixtures with new data
- **Quarterly:** Performance audit of tests
- **As needed:** Update mocks when APIs change

---

**Last Updated:** October 2025
**Maintained by:** Persian Deal Analyzer Team