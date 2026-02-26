# High-Level Design: <Feature Title>

## Overview

<!-- 1-2 paragraph summary of the architectural approach for this feature.
     Explain the "big picture" — how the system will solve the problem. -->

## Components

<!-- List each component involved in this feature. For each component, provide:
     - Name (must match the COMP_<name>.md file in design/)
     - Brief description (1-2 sentences)
     - Whether it's new or existing (and what changes if existing)

     Every component listed here MUST have a corresponding design/COMP_<name>.md
     with full detail. -->

### <ComponentName>
- **Status**: New | Modified
- **Purpose**: <1-2 sentence description>
- **Design doc**: `design/COMP_<name>.md`

## Data Flow

<!-- Describe how data moves through the system for this feature.
     Use numbered steps or ASCII diagrams. Show the path from
     user action to final result. -->

## API Changes

<!-- New or modified endpoints/interfaces. For each:
     - Method and path (e.g., POST /api/cart/save)
     - Request/response shape (brief)
     - Authentication requirements
     Mark "None" if no API changes. -->

## Data Model Changes

<!-- New or modified data structures, database tables, schemas.
     For each: name, fields, relationships, indexes.
     Mark "None" if no data model changes. -->

## Architectural Decisions

<!-- Record every significant design decision using the ADR format below.
     Each decision MUST include at least two alternatives considered. -->

### ADR-001: <Decision Title>
- **Decision**: <what was decided>
- **Alternatives Considered**:
  1. <alternative 1> — <why rejected>
  2. <alternative 2> — <why rejected>
- **Rationale**: <why this approach was chosen>

## Dependencies

<!-- External dependencies: libraries, services, APIs, infrastructure.
     For each: name, version constraints, why it's needed. -->

## Risks & Constraints

<!-- Known risks with severity (low/medium/high) and mitigation strategies.
     Known constraints: performance, compatibility, timeline, etc. -->
