# Retrieve Context Prompt

**Objective:**
Analyze the user's task description and generate specific, keyword-rich search queries to retrieve relevant code context from the vector database.

**Input:**
- User Task: "{{ user_task }}"

**Instructions:**
1. Identify the core intent of the task (e.g., bug fix, feature addition, refactoring).
2. Extract key terms, function names, file names, or concepts mentioned.
3. Formulate 1-3 distinct search queries that would likely yield the code needing modification or reference.
4. Output ONLY the queries as a JSON list of strings.

**Example Input:**
"Fix the null pointer exception in the login handler when password is empty."

**Example Output:**
["login handler", "password validation", "null pointer exception login"]
