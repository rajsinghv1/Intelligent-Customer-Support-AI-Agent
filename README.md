# Intelligent Customer Support AI Agent

An AI-powered customer support application built with Python, Google Gemini, and Retrieval-Augmented Generation (RAG). The project aims to help support teams understand customer queries, retrieve relevant knowledge-base information, and manage support tickets through a Streamlit interface.

> **Development status:** In progress. The feature list below is based on a static project audit, not end-to-end functional verification.

## Features

### Detected in the project audit
- **Google Gemini integration:** Generate AI-assisted support responses.
- **RAG / knowledge base:** Retrieve relevant reference information for customer questions.
- **Customer intelligence:** Analyze customer-related information.
- **Support tickets:** Support ticket-related functionality.
- **CSV export:** Export data to CSV.

### Planned or not yet detected
- Agent assignment
- Email notifications and email logs
- Conversation history
- Internal agent notes
- Duplicate ticket prevention
- SLA monitoring

The last static audit found **5 of 12 feature indicators (approximately 42%)** and **no Python syntax errors across 28 Python files**. This is *not* a measure of tested feature completion.

## Tech Stack

- **Language:** Python
- **LLM:** Google Gemini API
- **Interface:** Streamlit (where configured)
- **Approach:** Retrieval-Augmented Generation (RAG)

Additional dependencies and storage technologies should be confirmed against the repository's `requirements.txt` and source files.

## Getting Started (Windows PowerShell)

### 1. Clone the repository

```powershell
git clone <YOUR_REPOSITORY_URL>
cd Intelligent-Customer-Support-AI-Agent
```

If you already have the project locally:

```powershell
cd E:\Intelligent-Customer-Support-AI-Agent
```

### 2. Create and activate a virtual environment

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If `.venv` already exists, activate it without recreating it.

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If Streamlit or pytest is missing:

```powershell
python -m pip install streamlit pytest
```

### 4. Configure Gemini API credentials

Create a `.env` file using the project's `.env.example`, if one exists, and set the Gemini API key using the **exact environment-variable name expected by the source code** (for example, `GOOGLE_API_KEY` or `GEMINI_API_KEY`).

**Security:** Never commit `.env`, API keys, customer records, or other secrets to GitHub.

### 5. Find and launch the Streamlit entry point

Locate the application's Python file:

```powershell
Get-ChildItem -Recurse -Filter "*.py" | Select-Object FullName
```

Then run the command matching your actual Streamlit entry point:

```powershell
python -m streamlit run streamlit_app.py
```

or

```powershell
python -m streamlit run app.py
```

or, if your Streamlit application is in `app/main.py`:

```powershell
python -m streamlit run app/main.py
```

Open **http://localhost:8501** in your browser. These are alternative commands, not commands to run together. Confirm which file contains the Streamlit UI before launching.

## Run Tests

```powershell
python -m pip install pytest
python -m pytest -v
```

Review failing tests and verify the Gemini integration, retrieval results, ticket persistence, and CSV export. No successful test run has been established by the available audit.

## Example Workflow

1. A customer asks: *“My order has not arrived. Can you help?”*
2. The application analyzes the message using Gemini.
3. The retrieval component searches relevant knowledge-base content.
4. The AI prepares a response grounded in the available information.
5. Ticket functionality can be used to record or track the issue, depending on the implemented workflow.

*This workflow illustrates the intended experience and should be verified against the running application.*

## Project Structure

The repository contains Python modules for its AI and support functionality. To document the **actual** directory structure, run:

```powershell
tree /F /A
```

Replace this section with the output after removing virtual-environment, cache, and secret files. An unverified folder structure is intentionally not included.

## Roadmap

- [ ] Verify end-to-end Streamlit startup and Gemini API connectivity
- [ ] Add automated integration tests for RAG and ticket workflows
- [ ] Implement and test conversation history
- [ ] Implement internal notes and agent assignment
- [ ] Add duplicate ticket prevention
- [ ] Add email notifications and email logs
- [ ] Add SLA monitoring and escalation rules
- [ ] Improve error handling, logging, and access controls
- [ ] Document screenshots and measured evaluation results

## Resume Description

**Intelligent Customer Support AI Agent** — Python, Google Gemini, RAG, Streamlit

Developing an AI-assisted customer support application integrating Gemini-powered responses, knowledge-base retrieval, customer intelligence, ticket functionality, and CSV export. Expanding the system with conversation history, duplicate prevention, and SLA monitoring.

## Notes

- This README is based on the latest available audit summary rather than a full source-code inspection.
- Feature detection does not establish that features work correctly.
- Update the run command, environment variables, screenshots, and test results after checking the actual repository.

## License

Add a `LICENSE` file if you want to publish this project under an open-source license.
