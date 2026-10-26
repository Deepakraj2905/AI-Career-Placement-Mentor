# Final checklist

## Features implemented in starter
- Flask app and SQLite database
- Hashed-password login and registration
- Profile save/load
- Resume upload and PDF/DOCX/TXT extraction
- Keyword-based skills, score, and suggestions
- Career role matching and learning roadmap
- Optional LLM chat and mock interview feedback
- Dashboard counters and mobile-responsive interface

## Manual tests to perform
- Register, logout, and login
- Save profile and refresh
- Upload text PDF, DOCX, and TXT; test invalid file type
- Generate role recommendations and roadmap
- Test chat with and without OPENAI_API_KEY
- Submit mock interview answer and check dashboard update

## Known gaps
No original source code was included in the report. Skill matching is heuristic; no live jobs feed or trained ML model is included. No email verification, password reset, CSRF protection, rate limiting, or production privacy/data-deletion workflows. Deployment requires a Python-capable host, not GitHub Pages alone.
