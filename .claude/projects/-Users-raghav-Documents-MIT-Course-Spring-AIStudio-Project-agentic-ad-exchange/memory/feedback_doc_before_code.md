---
name: Document design before coding
description: Always update design docs and validate the architecture before writing implementation code
type: feedback
---

Update design docs first, then validate the design works across all phases/acts, then execute.

**Why:** Raghav wants the architectural thinking documented and reviewed before any code is written. Jumping straight to execution without updating the doc led to the Phase 1/2 misalignment where we built technically correct infrastructure but fundamentally broken agent architecture.

**How to apply:** When planning a major feature or rephasing, update the product doc (docs/product-architecture.md) or create a new design doc first. Review the design for consistency across all phases. Only then create an execution plan and write code.
