---
name: PO-Driven TDD Workflow
description: A workflow for executing features where the agent writes tests first based on PO requirements, gets approval on the tests as acceptance criteria, and then implements the code to pass them.
---

# PO-Driven Test First Workflow

When implementing a feature, especially one involving complex Home Assistant entity logic or API responses, you must adopt this Test-Driven Development workflow so the Product Owner can verify *what* you are building without needing to review *how* you built it.

## The Workflow

1. **Write Tests First**: Based on the approved `implementation_plan.md` or feature discussion, write the unit tests for the feature first. 
    - For the library (`lib/`), write tests that mock the HTTP responses and verify the parsed models.
    - For the integration (`custom_components/kospel/`), write tests verifying the entity state and behavior.
2. **Present Tests as Acceptance Criteria**: Stop and present the newly written tests to the user. Explain that these tests serve as the formal Acceptance Criteria.
3. **Wait for Approval**: Do not write the actual implementation code until the PO agrees that the tests accurately reflect the desired behavior.
4. **Implement**: Once approved, write the actual code to make the tests pass.
5. **Self-Heal**: Run the tests locally (`uv run python -m pytest tests/ -v`). If they fail, fix your implementation until they pass. Do not ask the user for help unless you are fundamentally blocked by an architectural constraint.
