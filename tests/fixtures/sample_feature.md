---
id: "FEAT_001"
title: "Checkout Resume"
status: "TODO"
created: "2026-02-23"
updated: "2026-02-23"
---

# Checkout Resume

## Problem Statement
Users lose their cart when they close the browser.

## Proposed Solution
Save cart state server-side and restore it on login.

## Scope
### In Scope
- Save cart on logout/close
- Restore cart on login

### Out of Scope
- Guest checkout
- Cart merging

## Success Criteria
- Cart persists across browser sessions
