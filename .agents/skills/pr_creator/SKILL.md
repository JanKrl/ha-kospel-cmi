---
name: PR Creator
description: Instructs the agent on how to correctly format and create a Pull Request for this monorepo, ensuring compatibility with the release-please workflow and project conventions.
---

# PR Creator Skill

When you are asked to create a pull request (or prepare the contents for one) in this repository, you must act as a strict Release Manager and follow these exact steps to ensure our `release-please` automation works correctly.

## 1. Use the PR Template
You MUST read the contents of `.github/pull_request_template.md` and use it as the exact boilerplate for your Pull Request body. Do not invent your own structure.

## 2. Strict PR Naming (Conventional Commits)
Because this is a monorepo managed by `release-please`, the PR title is critical. It will become the squash-merge commit on `master`.
- You MUST format the PR title as a [Conventional Commit](https://www.conventionalcommits.org/).
- You MUST include the correct scope: 
  - Use `(lib)` if changes are in `lib/`. Example: `feat(lib): add EkcoM4 device support`
  - Use `(ha)` if changes are in the root `custom_components/kospel/`. Example: `fix(ha): debounce connectivity sensor`
  - Use `(ci)` or `(chore)` for internal/workflow changes so they don't trigger a release. Example: `ci: update workflow`
- **NEVER** mix `lib` and `ha` changes in the same PR. If a feature requires both, it must be split into two PRs.

## 3. Issue Linking
If this PR addresses an existing issue, you MUST use `Relates to #123` instead of `Fixes #123` in the Motivation section. This prevents GitHub from closing the issue prematurely before the actual release is published.

## 4. Breaking Changes
If the PR introduces a breaking change, you MUST add `BREAKING CHANGE: <description>` as a footer at the very bottom of the PR description body. Remember that a breaking change must only apply to one package at a time to avoid unnecessarily bumping the major version of the unaffected package.

## 5. Intelligently Fill the Checklist
When filling out the checkboxes from the template (`- [x]`), evaluate the actual work done:
- Did you modify user-facing behavior? Check the Documentation box.
- Did you add/modify public methods? Check the Type hints box.
- Did you add UI entities? Check the `strings.json` translation keys box.
- If something is not applicable, leave it unchecked but do not remove the checkbox line.
