# Version Control & Commit Guidelines

## Always Commit and Push Changes
- **Automatic Execution**: Every single time work is finished, updated, or modified (code, documentation, reports, benchmarks, configurations, or fixes), immediately verify tests, stage all relevant changes, commit, and push to GitHub (`origin/main`). Do not wait for manual prompts or separate requests.
- **Untracked Files**: Actively check `git status` for untracked artifacts or data additions that belong in version control and stage them intentionally (respecting `.gitignore`).
- **Commit Style**: Use Conventional Commits formatting:
  - `feat(...)`: new features or benchmark datasets
  - `fix(...)`: bug fixes
  - `refactor(...)`: code restructuring without behavior changes
  - `docs(...)`: documentation or report updates
  - `test(...)`: test additions or adjustments
- **Clean State**: Always leave the working tree clean and local branch fully synchronized with `origin/main` at the conclusion of every turn/task.
