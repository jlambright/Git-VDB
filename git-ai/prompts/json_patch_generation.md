# JSON Patch Generation Prompt

**Objective:**
Generate a valid JSON Patch (RFC 6902) to apply the necessary code changes based on the user task and retrieved context.

**Input:**
- User Task: "{{ user_task }}"
- Retrieved Context:
{{ context_json }}

**Instructions:**
1. Analyze the retrieved context to understand the existing code structure.
2. Determine the precise changes needed to satisfy the user task.
3. Construct a JSON Patch that modifies the file(s) correctly.
4. The context provided is a JSON object where keys are file paths (e.g. "src/main.py") and values are content.
5. **Crucial**: To target a key like "src/main.py", your path MUST be escaped as "/src~1main.py".
   - "/" is escaped as "~1".
   - "~" is escaped as "~0".
6. Output ONLY the JSON Patch list.

**Example Output:**
[
  {
    "op": "replace",
    "path": "/src~1login.py",
    "value": "def login(user, password):\n    if not password:\n        return False\n    ..."
  }
]
