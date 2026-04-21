# Document Processing Flow

## Overview
This system automates financial document processing for a Fund of Funds operation using Gmail, LLM classification, and human-in-the-loop review.

## Flow Stages

### 1. Gmail Integration
**File:** `app/gmail.py`

- **OAuth Setup**: `get_oauth_url()` generates consent URL for user authorization
- **Token Exchange**: `exchange_code()` converts authorization code to access tokens
- **Message Fetching**: `fetch_new_messages()` retrieves emails and attachments from Gmail
  - Filters by timestamp
  - Extracts: sender, subject, body, attachments (with MIME type)
  - Handles both simple and multipart messages

**Input**: User authorization + timestamp
**Output**: List of messages with metadata and attachment data

---

### 2. File Extraction from PDF Attachments
**File**: Handled via `extract_text_from_pdf()` in the processing pipeline

**Process**: For each PDF attachment:
- Decode base64-encoded PDF data from Gmail attachment
- Use PyPDF2 to extract text from each page
- Handle multi-page PDFs by combining extracted text
- Fall back gracefully for unreadable/corrupted PDFs

**Input**: Base64-encoded PDF from Gmail attachment

**Output**: Plain text extracted from all pages (concatenated with page markers)

---

### 3. LLM Classification
**File:** `app/agent.py` → `classify_node()`

**Model**: OpenAI GPT-4o-mini

**Input**: Document text (first 6000 chars)

**Processing**:
- Analyzes financial document language
- Classifies into: `capital_call` | `invoice` | `unknown`
- Provides confidence score and reasoning

**Prompt Context**: System knows about Fund of Funds operations:
- Capital Calls: Urgent fund drawdown requests
- Invoices: Management fees, legal fees, services
- Unknown: Documents that don't fit the above

**Output**: `{document_type, confidence, reasoning}`

---

### 4. LLM Extraction
**File:** `app/agent.py` → `extract_node()`

**Model**: OpenAI GPT-4o-mini

**Input**: Document type + text (first 6000 chars)

**Processing**:
- Conditional: Only runs if `document_type != "unknown"`
- Extracts key payment metadata
- Handles multi-currency amounts

**Output**: 
```json
{
  "fund_name": "exact fund name or null",
  "amount": 500000,
  "currency": "USD|EUR|GBP|JPY",
  "due_date": "YYYY-MM-DD or null",
  "confidence": 0.95
}
```

---

### 5. Human-In-The-Loop Review
**File:** `app/agent.py` → `human_review_node()`, `apply_review_node()`

**Graph Interruption**: Graph halts at `human_review` node after extraction

**Review Actions**:
- `approve`: Accept extracted metadata as-is OR apply overrides
- `reject`: Mark document for manual processing
- `overrides`: Provide corrected values (e.g., wrong fund name, amount typo)

**State Management**:
- Uses PostgreSQL checkpointing via LangGraph
- Preserves full document state during human review
- Resumes graph with user decisions via `resume_agent_run()`

**Output**: Final approved metadata or rejection status

---

## End-to-End State Flow

```
Gmail Fetch
    ↓
Email Entry (sender, subject, body, attachments)
    ↓
[Document extracted from email/attachment]
    ↓
classify_node: "capital_call" | "invoice" | "unknown"
    ↓
[if "unknown" → END]
[if known type → extract_node]
    ↓
extract_node: fund_name, amount, currency, due_date, confidence
    ↓
INTERRUPT at human_review
    ↓
[Human reviews & decides: approve/reject + optional overrides]
    ↓
apply_review_node: Apply human decisions
    ↓
Database: Store final metadata + audit trail
```

## Database Storage
**File:** `app/database.py`

- **Email Table**: Gmail metadata, status, received_at
- **Document Table**: Per-email documents (one email can have multiple attachments)
  - Status: `pending` → `extracted` → `reviewed` → `completed` or `rejected`
  - Stores: classification, extracted metadata, human review notes, confidence scores
  - Audit trail: All state transitions with timestamps and actor info

## API Endpoints
- `POST /emails`: Trigger email fetch
- `POST /documents/{id}/review`: Submit human review (approve/reject with overrides)
- `GET /dashboard`: Stats dashboard (pending count, urgent items, completion rate)
