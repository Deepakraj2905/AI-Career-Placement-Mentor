# AI Career & Placement Mentor — starter source

This is a newly generated implementation based on the internship report. The PDF describes features and technologies but does not contain the original application source code, so this is not a merge into an existing codebase.

## Included modules
- Registration and login with hashed passwords
- Student profile
- Resume upload and text extraction for PDF, DOCX, TXT
- Keyword-based resume skill detection and suggestions
- Career-role matching and skill-gap roadmap
- AI mentor chat and mock interview feedback (requires a server-side OpenAI API key for generated answers)
- Placement-readiness dashboard

## Run
1. Install Python 3.10+.
2. In this folder run `pip install -r requirements.txt`.
3. Set `FLASK_SECRET_KEY` to a strong random value.
4. Optionally set `OPENAI_API_KEY` and `OPENAI_MODEL` on the server for real AI responses. Never place the API key in JavaScript or commit it to GitHub.
5. Run `python app.py` and open `http://127.0.0.1:5000`.

## Limitations
Resume analysis and role matching are heuristics, not a trained ML model or live jobs database. Readiness score is illustrative, not a hiring prediction. Before public deployment add CSRF protection, rate limits, secure cookie configuration, email verification/password reset, privacy/deletion controls, and robust file scanning. Static-only hosting such as GitHub Pages cannot run this Flask backend; use Python-capable hosting.
