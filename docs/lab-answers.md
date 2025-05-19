# MCP Lab Coding Exercise Answers

This document provides the answers for the core coding exercises in the MCP lab, focusing on:
- Defining MCP tool properties
- Registering the MCP tool trigger
- Adding the embeddings input binding

---

## 1. Define Tool Properties for `save_snippet`

Replace the empty list assignment for `tool_properties_save_snippets` with the following:

```python
# Define the tool properties for save_snippet
# Each ToolProperty describes an input expected by the MCP tool
# (name, project ID, and snippet content)
tool_properties_save_snippets = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The unique name for the code snippet."),
    ToolProperty(_PROJECT_ID_PROPERTY_NAME, "string", "The ID of the project the snippet belongs to. Optional, defaults to 'default-project' if not provided."),
    ToolProperty(_SNIPPET_PROPERTY_NAME, "string", "The actual code content of the snippet."),
]
```

---

## 2. Add MCP Tool Trigger Binding

Above the `mcp_save_snippet` function, add the following decorator to register it as an MCP tool:

```python
@app.generic_trigger(
    arg_name="context", # Variable name for the incoming MCP data
    type="mcpToolTrigger", # Specify the trigger type
    toolName="save_snippet", # How the agent refers to this tool
    description="Save a code snippet with name and project ID.", # Description for the agent
    toolProperties=tool_properties_save_snippets_json, # The input schema (from Ex 1)
)
```

---

## 3. Add Embeddings Input Binding

Directly above the `mcp_save_snippet` function (after the MCP trigger), add the following decorator to enable automatic embedding generation:

```python
@app.embeddings_input(
    arg_name="embeddings", 
    input="{arguments." + _SNIPPET_PROPERTY_NAME + "}", 
    input_type="rawText", 
    embeddings_model="%EMBEDDING_MODEL_DEPLOYMENT_NAME%"
)
```

---

## 4. (For Reference) Complete Function Signature

Your function should now look like this:

```python
@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="save_snippet",
    description="Save a code snippet with name and project ID.",
    toolProperties=tool_properties_save_snippets_json,
)
@app.embeddings_input(
    arg_name="embeddings",
    input="{arguments." + _SNIPPET_PROPERTY_NAME + "}",
    input_type="rawText",
    model="%EMBEDDING_MODEL_DEPLOYMENT_NAME%"
)
async def mcp_save_snippet(context: str, embeddings: str) -> str:
    # ... function body ...
```

Note that the function body logic has already been implemented for you to handle parsing the MCP context, extracting the embedding vector, and saving to Cosmos DB.

---

**End of lab answers.**