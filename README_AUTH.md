# Moreach Authentication System

Complete user registration and login system with email/password authentication.

## Features

- **Email/Password Registration** - Secure user registration flow
- **JWT Authentication** - Token-based stateless authentication
- **Password Encryption** - bcrypt hash protection
- **User Profile Collection** - Industry, job title, usage type, etc.
- **Form Validation** - Frontend and backend dual validation
- **Error Handling** - User-friendly error messages
- **Auto Login** - Automatic login after registration
- **Token Management** - 7-day validity period

## Quick Start

### 1. Installation and Migration

```bash
# Backend
cd backend
pip install -r requirements.txt
python scripts/migrate_add_users.py

# Frontend
cd frontend
npm install
```

### 2. Start Services

```bash
# Backend (Terminal 1)
cd backend
uvicorn app.main:app --reload

# Frontend (Terminal 2)
cd frontend
npm run dev
```

### 3. Access

- Register: http://localhost:3000/register
- Login: http://localhost:3000/login

## User Information Collection

### Required Fields
- **Email** - Used for login
- **Password** - Minimum 8 characters
- **Full Name** - User's real name
- **Industry** - 11 options (see below)
- **Usage Type** - Personal/Agency/Team

### Optional Fields
- **Company** - Company name
- **Job Title** - Work position

## Industry Options

The system supports the following moreach-related industries:

| Industry | Description |
|----------|-------------|
| E-commerce | E-commerce platforms |
| SaaS | Software as a Service |
| Marketing Agency | Marketing agency companies |
| Content Creator | Content creators/Influencers |
| Retail | Retailers |
| Fashion & Beauty | Fashion and beauty |
| Health & Fitness | Health and fitness |
| Food & Beverage | Food and beverage industry |
| Technology | Technology companies |
| Education | Education and training |
| Other | Other industries |

## Usage Types

| Type | Description |
|------|-------------|
| Personal Use | Using for your own business |
| Agency Use | Managing marketing campaigns for clients |
| Team Use | Part of a marketing team |

## Security Features

1. **Password Encryption** - bcrypt hash, irreversible
2. **JWT Token** - Signature verification, 7-day expiry
3. **Unique Email** - Prevents duplicate registration
4. **Account Status** - Supports account activation/deactivation
5. **Dual Validation** - Frontend and backend data validation

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM
- **SQLite** - Database
- **python-jose** - JWT handling
- **passlib** - Password encryption
- **pydantic** - Data validation

### Frontend
- **Next.js 13+** - React framework
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling framework

## API Endpoints

### Register
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe",
  "company": "Acme Inc.",
  "job_title": "Marketing Manager",
  "industry": "SaaS",
  "usage_type": "Personal Use"
}
```

### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

## Testing

### Automated Testing
```bash
cd backend
python scripts/test_auth.py
```

### Manual Testing
1. Visit http://localhost:3000/register
2. Fill out the form and submit
3. Automatically redirects to `/reddit`
4. Check token in localStorage

## Configuration

### Environment Variables

For production, set the following environment variables:

```bash
# .env
SECRET_KEY=your-very-secure-random-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days
```

### Production Checklist

- [ ] Change `SECRET_KEY` to a random key
- [ ] Enable HTTPS
- [ ] Configure CORS domain names
- [ ] Set up rate limiting
- [ ] Enable logging
- [ ] Configure email service (for verification)
- [ ] Set up database backup
- [ ] Add monitoring and alerts

## Usage Examples

### Frontend - Register User
```typescript
const response = await fetch("http://localhost:8000/api/v1/auth/register", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    email: "user@example.com",
    password: "password123",
    full_name: "John Doe",
    industry: "SaaS",
    usage_type: "Personal Use"
  })
});

const data = await response.json();
localStorage.setItem("token", data.access_token);
```

### Frontend - Authenticated Request
```typescript
const token = localStorage.getItem("token");

const response = await fetch("http://localhost:8000/api/v1/some-endpoint", {
  headers: {
    "Authorization": `Bearer ${token}`,
    "Content-Type": "application/json"
  }
});
```

### Backend - Protect Routes
```python
from app.core.auth import get_current_user
from app.models.tables import User

@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {
        "message": f"Hello {current_user.full_name}",
        "email": current_user.email,
        "industry": current_user.industry.value
    }
```

## Troubleshooting

### Problem: "Email already registered"
**Solution**: The email is already in use. Use a different email or log in.

### Problem: "Incorrect email or password"
**Solution**: Check that email and password are correct. Passwords are case-sensitive.

### Problem: "Could not validate credentials"
**Solution**: Token may have expired. Please log in again.

### Problem: Backend connection failed
**Solution**:
1. Ensure backend is running on http://localhost:8000
2. Check CORS configuration
3. Check browser console for errors

### Problem: Database error
**Solution**: Run the migration script
```bash
cd backend
python scripts/migrate_add_users.py
```

## Future Improvements

### Short Term
- [ ] Email verification
- [ ] Password reset
- [ ] User profile update
- [ ] Remember me functionality

### Medium Term
- [ ] OAuth login (Google, GitHub)
- [ ] Two-factor authentication (2FA)
- [ ] Session management
- [ ] API rate limiting

### Long Term
- [ ] User activity logging
- [ ] Advanced permission system
- [ ] Team management
- [ ] SSO integration

## Best Practices

1. **Never** log passwords
2. **Always** use HTTPS for sensitive data transmission
3. **Regularly** update dependencies
4. **Implement** rate limiting to prevent brute force attacks
5. **Monitor** abnormal login activity
6. **Backup** user data
7. **Test** all authentication flows

## Contributing

To improve the authentication system:
1. Create a feature branch
2. Implement and test the feature
3. Update documentation
4. Submit a PR

## License

This project follows the main project license.

---

**Version**: 1.0.0
**Last Updated**: 2026-01-31
**Status**: Production Ready
