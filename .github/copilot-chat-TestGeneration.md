# Copilot Chat – Test Generation

- Use **pytest** + **pytest-asyncio**.
- Mark async tests with `@pytest.mark.asyncio`.
- Mock Azure SDK calls with `unittest.mock.AsyncMock` or `MagicMock`.
- Aim for complete branch coverage of orchestrator fan-out / fan-in paths.
- Keep fixtures self-contained; no network or storage access.
