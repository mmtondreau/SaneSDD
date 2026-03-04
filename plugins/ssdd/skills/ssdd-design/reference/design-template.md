# System Architecture

## Overview

<!-- System-wide architectural summary. This is the single global view of how
     the entire system is structured. Updated as features are added. -->

## Component Map

<!-- How components relate to each other. Use an ASCII diagram or prose
     description showing the major components and their connections.

     Example:
     ```
     [Client] → [API Gateway] → [Auth Service]
                      ↓
               [Business Logic] → [Database]
                      ↓
               [Event Bus] → [Notification Service]
     ``` -->

## System-Level Data Flow

<!-- How data flows across the full system, not scoped to any single feature.
     Describe the primary data paths: user requests, background jobs,
     event processing, etc. -->

## Cross-Cutting Concerns

<!-- Concerns that span multiple components:
     - Authentication & Authorization
     - Logging & Observability
     - Error Handling & Recovery
     - Configuration Management
     - Security
     - Performance & Caching -->

## Domain Index

<!-- Master table of all domains (bounded contexts) in the system. Each domain
     groups related components. -->

| Domain | Path | Purpose |
|--------|------|---------|
| <DomainName> | `.ssdd/design/DOMAIN_<NNN>_<name>/` | <1-line purpose> |

## Component Index

<!-- Master table of all components in the system. Every component listed here
     MUST have a corresponding COMP_<name>.md within its domain directory. -->

| Component | Domain | Design Doc | Purpose | Status |
|-----------|--------|-----------|---------|--------|
| <Name> | <DomainName> | `.ssdd/design/DOMAIN_<NNN>_<name>/COMP_<name>.md` | <1-line purpose> | New / Modified / Existing |
