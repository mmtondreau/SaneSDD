# Implementation Phase Instructions

## Task Implementation (Developer Phase)

### Objective
Implement the assigned task to completion, satisfying all done criteria.

### Process
1. Read and understand the task specification and done criteria.
2. Read the parent story for user-value context.
3. Read relevant design documents (design/design.md, design/COMP_*.md).
4. Read existing code in areas you will modify.
5. Implement the solution:
   a. Write production code.
   b. Write unit tests (80% line coverage minimum).
   c. Use dependency injection for all external collaborators.
   d. Isolate each unit test to a single class, mock all dependencies.
6. Run linters and fix violations.
7. Run tests — all must pass.
8. If your implementation diverges from the design, update design docs.
9. Update INDEX.md for every file created or modified.
10. When complete, update the task frontmatter status to DONE.

### Done Checklist
- [ ] All done criteria from the task spec are met
- [ ] Unit tests exist and cover >= 80% of lines
- [ ] All tests pass
- [ ] Linter reports zero violations
- [ ] Design docs updated (if applicable)
- [ ] INDEX.md updated

---

## Task QA Validation

### Objective
Validate that the implemented task passes all quality gates.

### Validation Steps (execute ALL in order)

#### 1. Done Criteria Check
Read the "Done Criteria" section of the task spec. For each criterion, examine the implementation and determine if it is satisfied.

#### 2. Test Existence Check
Verify test files exist for each production module the task created or modified.

#### 3. Lint Check
Run the project's lint command. Verdict: PASS if exit code 0, FAIL otherwise.

#### 4. Test Execution Check
Run the project's test command. Verdict: PASS if all tests pass, FAIL otherwise.

#### 5. Coverage Check
Run coverage and verify line coverage >= 80% for modules the task touched.

#### 6. Design Documentation Check
If the task changed any interface or architecture, verify design docs are updated. If no changes, mark N/A.

#### 7. INDEX.md Check
Verify INDEX.md has entries for every file created or modified.

### Output
If ALL checks pass: update the task frontmatter status to DONE.
If ANY check fails: leave status as IN_PROGRESS and add a `qa_notes` field to frontmatter describing what failed.

---

## Story QA Validation

### Objective
Validate that all tasks for the story are complete and all acceptance criteria are satisfied.

### Validation Steps (execute ALL in order)

#### 1. Task Completion Check
For each task belonging to this story, verify its frontmatter status is DONE. List any that are not.

#### 2. AC-to-Task Mapping Check
For each acceptance criterion in this story, find all tasks whose ac_mapping includes this AC ID. Flag any ACs with no mapped tasks.

#### 3. AC Satisfaction Check
For each acceptance criterion, examine the implementation and tests. Run relevant tests. Verdict each AC as PASS or FAIL with evidence.

#### 4. Dependency Check
For each story ID in depends_on, verify that story's status is DONE.

#### 5. Regression Tests
Run the full test suite to verify no regressions were introduced.

#### 6. Overall Verdict
- If ALL checks pass: update each AC status to DONE in the story frontmatter. The story can move to DONE.
- If ANY check fails: leave ACs that failed as TODO/IN_PROGRESS. List all blocking issues.

---

## Remediation (Tech Lead Phase)

### Objective
Analyze incomplete acceptance criteria after Story QA and create remediation tasks.

### Process
1. For each incomplete AC, determine what additional work is needed.
2. Create new TASK files for the remediation work.
3. Map each new task to the ACs it will satisfy.
4. Set depends_on for new tasks as appropriate.

### Rules
- Only create tasks for ACs that are NOT yet DONE.
- New tasks should be minimal and focused.
- Do not duplicate work already completed in existing tasks.
- Set new task status to TODO.
