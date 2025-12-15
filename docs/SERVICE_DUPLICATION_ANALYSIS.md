# Service Duplication Analysis

## Executive Summary

**Finding:** Moderate duplication found in services (5-8% of service code)
**Priority:** Redis cache guards, clear_cache() patterns, search delegators

---

## 🔴 HIGH Priority: Redis Cache Availability Guards (10x Duplication)

### Problem

**File:** `services/cache/redis_cache.py`

**Duplicate pattern found 10 times:**
```python
if not self.enabled or not self.redis_client:
    return None  # or False, or {}, etc.
```

**Locations:**
1. Line 109: `is_available()` → returns False
2. Line 128: `get()` → returns None
3. Line 168: `set()` → returns False
4. Line 208: `delete()` → returns False
5. Line 230: `delete_pattern()` → returns 0
6. Line 255: `exists()` → returns False
7. Line 273: `clear_all()` → returns False
8. Line 292: `get_stats()` → returns {}
9. Line 372: `increment()` → returns None
10. Line 392: `get_ttl()` → returns None

### ✅ SOLUTION: Create availability guard decorator

```python
def require_redis(default_return=None):
    """Decorator to check Redis availability before method execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.enabled or not self.redis_client:
                return default_return
            return func(self, *args, **kwargs)
        return wrapper
    return decorator

# Usage:
@require_redis(default_return=None)
def get(self, key: str) -> Optional[Any]:
    """Get value from cache"""
    try:
        value = self.redis_client.get(key)
        # ... rest of implementation
```

**Impact:**
- Eliminates 10 duplicate guard clauses
- Cleaner, more maintainable code
- Easy to modify behavior in one place

---

## 🟡 MEDIUM Priority: clear_cache() Methods (5x Similar)

### Problem

Multiple services have `clear_cache()` methods with similar implementation:

1. **services/moe/expert_router.py:465**
   ```python
   def clear_cache(self):
       """Clear routing cache"""
       self._routing_cache.clear()
   ```

2. **services/moe/embedding_service.py:316**
   ```python
   def clear_cache(self):
       """Clear embedding cache"""
       self._cache.clear()
   ```

3. **services/sentiment_service.py:358**
   ```python
   def clear_cache(self):
       """Clear sentiment cache"""
       self.sentiment_cache.clear()
   ```

4. **services/query_rewriter_service.py:280**
   ```python
   def clear_cache(self):
       """Clear query rewriter cache"""
       self._cache.clear()
   ```

### Analysis

**Are these duplicates?**
- ❌ No - Each clears a different cache
- ✅ Already using CacheableMixin pattern from base classes
- ✅ Consistent interface is GOOD (Liskov Substitution Principle)

**Decision:** ✅ **DO NOT consolidate** - Intentional consistent interface

---

## 🟡 MEDIUM Priority: search_X() Delegator Methods (9x Similar)

### Problem

Three services have similar search delegator patterns:

**services/rag_search_service.py:**
```python
def search_deals(self, query: str, n_results: int = 5):
    return self._search_collection(query, EntityTypes.DEALS, n_results)

def search_activities(self, query: str, n_results: int = 5):
    return self._search_collection(query, EntityTypes.ACTIVITIES, n_results)

def search_agents(self, query: str, n_results: int = 5):
    return self._search_collection(query, EntityTypes.AGENTS, n_results)
```

**services/cag_orchestrator_service.py:**
```python
def search_deals(self, query: str, n_results: int = 5):
    return self.search(query, document_type='deal', n_results=n_results)

def search_activities(self, query: str, n_results: int = 5):
    return self.search(query, document_type='activity', n_results=n_results)

def search_agents(self, query: str, n_results: int = 5):
    return self.search(query, document_type='agent', n_results=n_results)
```

**services/batch_search_service.py:**
```python
def search_deals_batch(self, queries: List[str], n_results: int = 5):
    # Similar pattern
```

### Analysis

**Are these duplicates?**
- ❌ No - Thin delegators providing consistent interface
- ✅ Different underlying implementations (RAG vs CAG vs Batch)
- ✅ Follows Facade pattern for API consistency

**Decision:** ✅ **DO NOT consolidate** - Intentional design pattern

---

## 🟢 LOW Priority: invalidate_deal_cache() (2x Similar)

### Locations:
1. **services/analytics_service.py:187**
2. **services/cache/two_level_cache.py:151**

### Analysis

```python
# analytics_service.py
def invalidate_deal_cache(self, deal_id: str) -> bool:
    """Invalidate cache for specific deal"""
    # Implementation for analytics

# two_level_cache.py
def invalidate_deal_cache(self, deal_id: str) -> None:
    """Invalidate deal-related caches in both levels"""
    # Implementation for two-level cache
```

**Decision:** ✅ **DO NOT consolidate** - Different layers, different purposes

---

## Summary

### Consolidate (HIGH Value):
1. ✅ **Redis cache availability guards** (10 duplicates) - Use decorator pattern

### Keep Separate (Intentional Design):
1. ❌ `clear_cache()` methods - Consistent interface (good)
2. ❌ `search_X()` delegators - Facade pattern (good)
3. ❌ `invalidate_deal_cache()` - Different layers (good)

### Estimated Impact:
- **Duplicate code eliminated:** ~20-30 lines
- **Maintenance improvement:** Single point of change for Redis availability logic
- **Code clarity:** Cleaner methods without boilerplate guards

---

## Implementation Plan

### Step 1: Add decorator to redis_cache.py ✅
- Create `require_redis()` decorator
- Apply to all 10 methods
- Test thoroughly

### Step 2: Verify no regressions ✅
- Run full test suite
- Check Redis functionality
- Verify error handling

### Status: Ready to implement
