# Integration Checklist

Run this checklist before committing any cross-boundary code.

## Backend Implementation
- [ ] Endpoint route exists and matches `api-contracts.md`.
- [ ] Request schema (Pydantic) perfectly matches contract.
- [ ] Response schema (Pydantic) perfectly matches contract.
- [ ] Error schema returns `{"success": false, "error": "..."}` format.
- [ ] `pytest` passes for endpoint logic.
- [ ] Linter / formatting checks passed.

## Frontend Implementation
- [ ] Types defined in `src/types/api.ts` based on `api-contracts.md`.
- [ ] Using strictly typed API caller (no `any`).
- [ ] Loading state explicitly handled.
- [ ] Empty state explicitly handled.
- [ ] Error/Failure state explicitly handled.
- [ ] `npm run lint` and `npm run typecheck` passed.

## Integration Check
- [ ] Verified live backend response parses correctly in UI without errors.
- [ ] No console errors.
