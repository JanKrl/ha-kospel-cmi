---
name: PR Release for HACS
description: How to correctly create a pre-release for a pull request so it can be tested in Home Assistant via HACS.
---

# Creating PR Releases for HACS Testing

When working on a feature branch (Pull Request) and the user requests a test release for HACS, follow this process:

1. **Determine the next version tag:**
   Look at the existing releases for the current PR to find the next increment.
   Format: `v<base_version>-pr<pr_number>.<increment>`
   Example: If the PR is #120, and `v0.1.0-pr120.3` was the last release, the next tag should be `v0.1.0-pr120.4`.

2. **Use the GitHub CLI to create the release:**
   ALWAYS use the `gh release create` command. This ensures GitHub generates a proper release entry that HACS can discover.
   **DO NOT** use `git tag` and `git push --tags`.

   Run the following command in the terminal (adjusting the tag name, branch name, and PR number accordingly):
   ```bash
   env -u GITHUB_TOKEN gh release create v0.1.0-pr120.4 --target <branch_name> --prerelease --title "v0.1.0-pr120.4" --notes "Test release for PR 120"
   ```
   *Note: We unset `GITHUB_TOKEN` because the default agent environment token might lack permissions for release creation. The local environment should have the correct auth state.*

3. **Instruct the user to update HACS:**
   After creating the release, remind the user to:
   - Go to HACS -> Integrations -> Kospel Electric Heaters.
   - Click the three dots in the top right corner and select **Update information**.
   - Select **Redownload** and choose the new pre-release tag.
   - Restart Home Assistant.
