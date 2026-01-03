# AI Video Generator - Multi-User Flask App

Secure web app for generating videos using OpenAI Sora API.
Tested to work with Sora 2 API on Linux x64 & ARM (M2 Macbook Air) system.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Setup environment:
```bash
cp .env.example .env
# Edit .env with your OpenAI API key
```

3. Run:
```bash
python app.py
```

4. Open: http://localhost:5000

## Features
- Secure authentication with hashed passwords
- User-specific video history
- Real-time progress tracking
- Video & thumbnail downloads
- Delete videos
- Persistent storage

## Security
- Passwords hashed with PBKDF2 SHA-256
- Session-based auth
- User isolation
- Protected routes

Ready to deploy!
