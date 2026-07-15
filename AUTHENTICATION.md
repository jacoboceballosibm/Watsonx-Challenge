# Authentication & User Management

## Overview

The ProM+ modernized app now includes a sign-in page with multiple demo users, allowing you to showcase different user profiles and data.

## Demo Users

All demo accounts use the same password (set via `DEMO_PASSWORD` environment variable, defaults to "password")

| Username | Name | Band | Location | Skills |
|----------|------|------|----------|--------|
| `anguyen` | Alysa Nguyen | 7 | United States | Python, AI/ML, Cloud, FastAPI, React |
| `jsmith` | John Smith | 6 | United Kingdom | JavaScript, TypeScript, Node.js, React, Docker |
| `mchen` | Marcus Chen | 8 | Singapore | Java, Spring Boot, Kubernetes, Microservices, DevOps |
| `swilliams` | Sarah Williams | 7 | Canada | Data Science, Machine Learning, Python, TensorFlow, SQL |
| `drodriguez` | David Rodriguez | 9 | Mexico | Cloud Architecture, AWS, Azure, Infrastructure, Security |

## How It Works

### 1. Sign-In Page (`login.html`)

- Visit `http://localhost:3000/login.html` (or open `frontend/login.html`)
- Click on any demo user card to auto-fill credentials
- Or manually enter username and password
- Upon successful login, you're redirected to the main app

### 2. Session Management

- Uses `localStorage` to store:
  - `prom_token`: Session token for authentication
  - `prom_user_id`: Professional ID (e.g., `JS7BQM3PXWK1`)
  - `prom_user_name`: Full name (e.g., `John Smith/UK/IBM`)

### 3. Protected Main App

- `index.html` checks for valid session on load
- Redirects to login page if not authenticated
- Displays personalized greeting in header
- Loads user-specific profile data

### 4. Sign Out

- Click "Sign out" in the header
- Clears session data and redirects to login page

## API Endpoints

### Authentication

```bash
# Get list of demo users
GET /api/auth/users

# Login
POST /api/auth/login
Body: {"username": "jsmith", "password": "<from DEMO_PASSWORD env var>"}
Response: {"professional_id": "JS7BQM3PXWK1", "name": "John Smith/UK/IBM", "token": "..."}

# Logout
POST /api/auth/logout?token=<session_token>
```

### Profile

```bash
# Get user profile
GET /api/profile/{professional_id}
```

## Testing Different Users

1. **Start the backend** (if not already running):
   ```bash
   cd backend
   source .venv/bin/activate
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **Open the frontend**:
   ```bash
   cd frontend
   python -m http.server 3000
   ```
   Or open `frontend/login.html` directly in your browser.

3. **Sign in as different users** to see:
   - Different profile data (name, band, location, skills)
   - Different availability dates
   - Personalized greetings
   - User-specific recommendations (when AI agents are integrated)

## Security Notes

⚠️ **This is a demo implementation. In production:**

- Use proper password hashing (bcrypt, argon2)
- Implement JWT tokens with expiration
- Use HTTPS for all requests
- Add CSRF protection
- Implement rate limiting on login endpoint
- Store sessions in Redis or database, not in-memory
- Never expose a `/auth/users` endpoint
- Add proper authorization checks on all API endpoints
