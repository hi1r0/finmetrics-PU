# Version Control & Commit Guidelines

## Always Commit Changes
- **Completion Invariant**: After completing tasks that add, modify, or generate code, documentation, benchmarks, or configuration files, always ensure tests/verifications pass and commit the resulting changes to git.
- **Untracked Files**: Check `git status` for untracked artifacts or data additions that belong in version control and stage them intentionally (respecting `.gitignore`).
- **Commit Style**: Use Conventional Commits formatting:
  - `feat(...)`: new features or benchmark datasets
  - `fix(...)`: bug fixes
  - `refactor(...)`: code restructuring without behavior changes
  - `docs(...)`: documentation or report updates
  - `test(...)`: test additions or adjustments
- **Clean State**: Leave the working tree clean at the end of feature/task implementations. Prompt or push to the upstream branch when instructed or when finishing development tasks.
