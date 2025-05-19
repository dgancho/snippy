# Copilot Chat – Code Review

- Flag any synchronous API that is accidentally `await`ed.
- Verify orchestrators are sync functions registered in a blueprint and use `yield`.
- Check for missing error handling, missing logging, or leaked secrets.
- Ensure environment-variable names match those referenced in local.settings.json.
- Confirm all new tests fail without the fix and pass with it.
