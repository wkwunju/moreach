# Authentication Setup Guide

This guide explains how to set up and use the new authentication system in moreach.

## Overview

The authentication system uses:
- **JWT tokens** for session management
- **bcrypt** for password hashing
- **Email/password** authentication
- User profile information collection during registration

## Backend Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data handling
- `email-validator` - Email validation

### 2. Run Database Migration

```bash
cd backend
python scripts/migrate_add_users.py
```

This creates the `users` table with the following fields:
- `email` - User's email (unique)
- `hashed_password` - Bcrypt hashed password
- `full_name` - User's full name
- `company` - Company name (optional)
- `job_title` - Job title (optional)
- `industry` - Industry type (required)
- `usage_type` - How they'll use moreach (required)
- `role` - USER or ADMIN
- `is_active` - Account status
- `email_verified` - Email verification status

### 3. Configure Secret Key (Production)

For production, set a secure secret key in your environment:

```bash
export SECRET_KEY="your-very-secure-random-secret-key-here"
```

Or add to `.env` file:
```
SECRET_KEY=your-very-secure-random-secret-key-here
```

### 4. Start Backend Server

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

## Frontend Setup

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Start Frontend Server

```bash
npm run dev
```

## API Endpoints

### Register
```
POST /api/v1/auth/register
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "company": "Acme Inc.",
  "job_title": "Marketing Manager",
  "industry": "E-commerce",
  "usage_type": "Personal Use"
}
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "company": "Acme Inc.",
    "job_title": "Marketing Manager",
    "industry": "E-commerce",
    "usage_type": "Personal Use",
    "role": "USER",
    "is_active": true,
    "email_verified": false,
    "created_at": "2024-01-23T10:00:00"
  }
}
```

### Login
```
POST /api/v1/auth/login
```

Request body:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

Response: Same as register

### Get Current User
```
GET /api/v1/auth/me
```

Headers:
```
Authorization: Bearer <access_token>
```

Response:
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  ...
}
```

## Industry Options

The following industries are available:
- E-commerce
- SaaS
- Marketing Agency
- Content Creator
- Retail
- Fashion & Beauty
- Health & Fitness
- Food & Beverage
- Technology
- Education
- Other

## Usage Types

- **Personal Use** - Individual using for their own business
- **Agency Use** - Managing campaigns for clients
- **Team Use** - Part of a marketing team

## Frontend Usage

### Storing Token

After successful login/register, the token is stored in localStorage:

```javascript
localStorage.setItem("token", data.access_token);
localStorage.setItem("user", JSON.stringify(data.user));
```

### Making Authenticated Requests

Include the token in the Authorization header:

```javascript
const token = localStorage.getItem("token");

fetch("http://localhost:8000/api/v1/some-endpoint", {
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  }
});
```

### Checking if User is Logged In

```javascript
const token = localStorage.getItem("token");
const user = JSON.parse(localStorage.getItem("user") || "null");

if (token && user) {
  // User is logged in
} else {
  // Redirect to login
}
```

### Logout

```javascript
localStorage.removeItem("token");
localStorage.removeItem("user");
// Redirect to login page
```

## Protecting Backend Routes

To require authentication for an endpoint:

```python
from app.core.auth import get_current_user
from app.models.tables import User

@router.get("/protected-endpoint")
async def protected_route(current_user: User = Depends(get_current_user)):
    # current_user is automatically populated
    return {"message": f"Hello {current_user.full_name}"}
```

## Security Features

1. **Password Hashing**: Passwords are hashed using bcrypt before storage
2. **JWT Tokens**: Tokens expire after 7 days
3. **Email Validation**: Email format is validated
4. **Password Requirements**: Minimum 8 characters
5. **Account Status**: Accounts can be deactivated

## Next Steps

Consider adding:
1. Email verification flow
2. Password reset functionality
3. OAuth providers (Google, GitHub)
4. Two-factor authentication
5. Rate limiting on auth endpoints
6. Session management (logout all devices)
7. User profile update endpoint

## Troubleshooting

### "Email already registered"
- The email is already in use. Try logging in or use a different email.

### "Incorrect email or password"
- Check your credentials. Passwords are case-sensitive.

### "Could not validate credentials"
- Your token may have expired. Log in again.

### "Account is inactive"
- Contact support to reactivate your account.

