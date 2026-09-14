"""
Business-logic layer. Each module here is called by a thin route in
app/api/v1/ and does the actual work (DB queries, orchestration, calling
app/ai/ where relevant). Routes should never contain this logic directly.
"""
