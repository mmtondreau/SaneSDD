---
id: "TASK_001"
title: "Create Cart Session Table"
status: "TODO"
story: "STORY_001"
depends_on: []
ac_mapping:
  - "AC_001"
  - "AC_002"
created: "2026-02-23"
updated: "2026-02-23"
---

## Description
Create a database table to persist cart sessions.

## Done Criteria
- Migration creates cart_sessions table
- Model class CartSession exists
- Unit tests cover CRUD operations

## Technical Approach
Use SQLAlchemy migration with Alembic.

## Files to Create or Modify
- src/models/cart_session.py (create)
- tests/test_cart_session.py (create)
