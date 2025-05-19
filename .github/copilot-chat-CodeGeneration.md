# Copilot Chat – Code Generation

- Target **Azure Functions Python v2** (azure-functions ≥ 1.23) with Durable Functions Blueprints.
- Orchestrators must be `def`, use `yield`, and run inside a `df.Blueprint`.
- Activity functions are `async def`; return JSON-serialisable values.
- Prefer async Azure SDK clients (`BlobServiceClient`, `CosmosClient`, …).
- Add full type hints and a one-line Google-style docstring.
- Use `logging` at INFO level; never use `print`.
- Do **not** await synchronous APIs (`req.get_json()`, `client.create_check_status_response()`).
- Secrets come from `os.environ[...]`; no hard-coded connection strings.
- Write idiomatic Python 3.11. Match statements allowed.
