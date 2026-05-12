# Constitution

## Hard Rules

- Only knowledge supported by the current RAW document may be committed.
- Do not introduce external facts, background knowledge, or inferred claims that are not grounded in the current RAW document.
- Every committed claim must be traceable to at least one RAW chunk.
- If a statement cannot be cited, it must not appear in the committed wiki page, `index.md`, `link.md`, or any ingest-generated knowledge output.
- Helper commits must remain atomic.
- The repository root is the knowledge base root.

## Writing Policy

- The default ingest behavior is knowledge-organization-first, not summary-first.
- A Wiki Page is not a shortened rendering of RAW. It is a knowledge page built by reorganizing, grouping, and normalizing RAW-supported content for later knowledge consumption.
- Prefer organizing content by concepts, mechanisms, constraints, decisions, and examples rather than mirroring the RAW document's original section order.
- When related evidence is scattered across the RAW document, combine it into more stable knowledge sections if the grouping is fully supported by the RAW content.
- Preserve important concepts, mechanisms, procedures, constraints, examples, formulas, edge cases, and caveats when they are present in the RAW document.
- Summary is an entry point, not the product itself.

## Page Organization

- Wiki pages should use a semi-structured layout.
- Prefer sections such as: overview, core concepts, mechanisms or workflow, important details, constraints or limitations, examples, and related knowledge when the RAW document supports them.
- Do not force empty sections when the RAW document does not support them.
- Do not mirror the RAW outline unless it already matches the best knowledge structure.
- Section choice and ordering should follow the most stable knowledge structure supported by the RAW document.

## Graph Policy

- `index.md` entries should be conservative and evidence-based.
- `link.md` entries should be conservative and evidence-based.
- Add index entries, aliases, or page relationships only when the current RAW document directly names them, clearly supports them, or the naming is clearly justified by existing naming context already provided to the ingest run.
- Richer page content does not justify speculative graph expansion.
