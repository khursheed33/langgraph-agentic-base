Optimized workflow initialization by implementing singleton pattern for compiled workflow cache.

- Created workflow_cache.py utility module with get_cached_workflow() function
- Modified CLI to initialize workflow once at startup instead of per user query
- Agents and tools are now loaded once at startup and reused for all queries
- Improved performance by eliminating repeated initialization overhead