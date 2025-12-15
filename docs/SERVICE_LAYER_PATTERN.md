# Service Layer Pattern

## Overview

This document defines the Service Layer pattern used in the Persian Deal Analyzer project. Following this pattern ensures consistent data access, enables caching, and maintains clean separation of concerns.

## ✅ CORRECT Pattern

### Always Use Service Layer

**DO:**
```python
# ✅ GOOD: Use service layer
from services.deal_service import DealService

deal_service = DealService(repositories)
deal = deal_service.get_deal_with_activities(deal_id)
```

**DON'T:**
```python
# ❌ BAD: Direct repository access
with repositories as uow:
    deal = uow.deals.get_deal_by_id(deal_id)
    activities = uow.activities.get_activities_by_deal_id(deal_id)
```

### Why?

1. **Caching**: Services implement caching; direct repository access bypasses cache
2. **Business Logic**: Services contain business logic (e.g., calculating health scores)
3. **Consistency**: Single place to update data access patterns
4. **Testability**: Easier to mock services than repositories

## 📚 Service Catalog

### DealService
- `get_deal(deal_id)` - Get deal by ID
- `get_deal_with_activities(deal_id)` - Get deal with related activities
- `get_all_deals()` - Get all deals
- `update_deal_status(deal_id, status)` - Update deal status

### AnalyticsService
- `generate_portfolio_overview()` - Portfolio analytics
- `calculate_deal_health(deal_id)` - Health score calculation
- `get_performance_metrics()` - Performance metrics

### SentimentService
- `analyze_text(text)` - Analyze sentiment of text
- `analyze_deal_sentiment(deal_id)` - Analyze all activities for a deal
- `get_sentiment_summary(activities)` - Aggregate sentiment

### ActivityService
- `get_activities_by_deal(deal_id)` - Get activities for deal
- `create_activity(activity_data)` - Create new activity
- `get_recent_activities(limit)` - Get recent activities

## 🚫 Anti-Patterns

### 1. Direct Repository Access in Experts

**❌ WRONG:**
```python
class DealAnalysisExpert(BaseExpert):
    def analyze(self, query, context):
        # Don't do this!
        with self.repositories as uow:
            deal = uow.deals.get_deal_by_id(deal_id)
```

**✅ CORRECT:**
```python
class DealAnalysisExpert(BaseExpert):
    def analyze(self, query, context):
        # Use service layer
        deal_service = self.services.get('deal_service')
        deal = deal_service.get_deal_with_activities(deal_id)
```

### 2. Bypassing Service for "Simple" Queries

**❌ WRONG:**
```python
# "It's just one field, I'll query directly"
with repositories as uow:
    deal_status = uow.deals.get_deal_by_id(deal_id).status
```

**✅ CORRECT:**
```python
# Use service even for simple queries - caching helps!
deal = deal_service.get_deal(deal_id)
deal_status = deal.get('status')
```

### 3. Mixing Service and Repository Access

**❌ WRONG:**
```python
# Inconsistent access patterns
deal = deal_service.get_deal(deal_id)  # Via service
with repositories as uow:
    activities = uow.activities.get_activities_by_deal_id(deal_id)  # Direct!
```

**✅ CORRECT:**
```python
# Consistent service layer access
deal_data = deal_service.get_deal_with_activities(deal_id)
deal = deal_data['deal']
activities = deal_data['activities']
```

## 🏗️ Architecture Layers

```
┌─────────────────────────────────────┐
│         UI / API Layer              │
│  (Gradio Interface, MCP Server)     │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│      MoE Orchestrator Layer         │
│  (Expert Router, Expert Instances)  │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│        Service Layer ✅              │
│  (Business Logic, Caching, etc.)    │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│      Repository Layer               │
│  (Database Access, SQL Queries)     │
└─────────────────┬───────────────────┘
                  │
┌─────────────────▼───────────────────┐
│         Database                    │
│       (PostgreSQL)                  │
└─────────────────────────────────────┘
```

**Rules:**
- Experts → Services → Repositories → Database
- Never skip layers (e.g., Experts → Repositories directly)
- Each layer has single responsibility

## 📝 Code Review Checklist

When reviewing code, check for:

- [ ] **No direct repository access** in experts or UI
- [ ] **All data access goes through services**
- [ ] **Consistent patterns** across similar code
- [ ] **Services are injected**, not created inline
- [ ] **Error handling** uses service layer patterns
- [ ] **Caching** is leveraged through services

## 🔍 Finding Violations

Search for anti-patterns:

```bash
# Find direct repository access in experts
grep -r "with.*repositories.*as.*uow" services/moe/experts/

# Find repository imports in experts (should use services)
grep -r "from.*repositories" services/moe/experts/
```

## ✨ Examples from Codebase

### Good Examples ✅

**services/analytics/insight_generator.py:117**
```python
# Uses service layer correctly
def generate_deal_insights(self, context: DealAnalysisContext):
    # Service methods provide all needed data
    deal = context.deal
    activities = context.activities
```

**services/moe/experts/deal_analysis_expert.py**
```python
# Injects services, uses them consistently
def analyze(self, query, context):
    deal_service = self.services.get('deal_service')
    analytics_service = self.services.get('analytics_service')
```

### Bad Examples ❌

If you find code like this, refactor it:

```python
# DON'T DO THIS
class SomeExpert(BaseExpert):
    def analyze(self, query, context):
        # Direct repository access - breaks caching!
        with self.repositories as uow:
            deal = uow.deals.get_deal_by_id(deal_id)
            # ... rest of code
```

Should be:

```python
# DO THIS
class SomeExpert(BaseExpert):
    def analyze(self, query, context):
        # Use service layer - benefits from caching!
        deal_service = self.services.get('deal_service')
        deal_data = deal_service.get_deal_with_activities(deal_id)
        # ... rest of code
```

## 📖 References

- **SOLID Principles**: Service layer follows Single Responsibility
- **DRY**: Avoids duplicate data access logic
- **Separation of Concerns**: Clear boundaries between layers

---

**Last Updated:** 2025-12-15
**Status:** ✅ Active Pattern
**Compliance:** Enforced in code reviews
