# Security & Production Deployment Guide

## 🔒 Security Fixes Applied

This document outlines the security improvements made to the Trainline application and provides guidance for secure production deployment.

---

## Critical Security Fixes

### 1. ✅ Removed Hardcoded Credentials
**Issue**: Database passwords and Django secret key were hardcoded in `docker-compose.yml`

**Fix**:
- Modified `docker-compose.yml` to use environment variables
- Created `.env.production.example` template
- Added network isolation between containers
- Removed public database port exposure (5432)

**Action Required**:
```bash
# Create a .env file for production (DO NOT commit to git)
cp .env.production.example .env

# Generate a strong Django secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Edit .env with secure values
nano .env
```

---

### 2. ✅ Fixed Debug Mode Configuration
**Issue**: `DJANGO_DEBUG=True` was set in docker-compose.yml

**Fix**:
- Changed default to `DJANGO_DEBUG=False` in docker-compose.yml
- Added production override in `docker-compose.prod.yml`

**Verification**:
```bash
# Ensure DEBUG=False in production
grep DJANGO_DEBUG docker-compose.yml
```

---

### 3. ✅ Fixed Seat Assignment Authorization Vulnerability
**Issue**: Any authenticated user could assign seats to any ticket by guessing ticket IDs

**Fix** (`backend/core/views.py`):
- Added input validation for `seat_num` and `ticket_id`
- Added flight ID verification
- Added race condition protection (check if seat already taken)
- Added proper error handling with appropriate HTTP status codes

**Test**:
```bash
# Attempt to assign a seat for another user's ticket (should fail)
curl -X POST http://localhost:8000/api/seats/FL123/ \
  -H "Authorization: Token YOUR_TOKEN" \
  -d "ticket_id=999&seat_num=1A"
```

---

### 4. ✅ Removed Debug Print Statement
**Issue**: Password and sensitive data logged to console in `serializers.py`

**Fix**:
- Removed `print("VALIDATED DATA IN REGISTER SERIALIZER:", data)`

---

### 5. ✅ Replaced Development Server with Gunicorn
**Issue**: Using `python manage.py runserver` in production (single-threaded, debug-enabled)

**Fix** (`backend/Dockerfile`):
- Replaced with `gunicorn booking.wsgi:application --bind 0.0.0.0:8000 --workers 3`
- Added static file collection
- Configured proper timeout and worker count

---

### 6. ✅ Added Security Headers

**Backend** (`backend/booking/settings.py`):
- `SECURE_HSTS_SECONDS = 31536000` (1 year)
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True`
- `SECURE_SSL_REDIRECT = True` (production only)
- `SESSION_COOKIE_HTTPONLY = True`
- `CSRF_COOKIE_HTTPONLY = True`
- `X_FRAME_OPTIONS = 'DENY'`

**Frontend** (`nginx.conf`):
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Content-Security-Policy configured
- Removed server version exposure

---

### 7. ✅ Pinned Dependency Versions
**Issue**: Unpinned dependencies could introduce vulnerabilities

**Fix** (`requirements.txt`):
- Pinned all dependencies to specific version ranges
- Added comments for clarity

**Maintenance**:
```bash
# Regularly check for security updates
pip list --outdated

# Audit dependencies for vulnerabilities
pip install pip-audit
pip-audit
```

---

### 8. ✅ Enhanced Input Validation

**Payment Endpoint** (`backend/core/views.py`):
- Validate payment method against whitelist
- Prevent double payment
- Proper error messages

**Booking Endpoint**:
- Server-side amount calculation (don't trust client)
- Boolean parsing with fallback

---

## 🚨 Remaining Considerations

### Token Storage (Medium Priority)
**Current**: Auth tokens stored in localStorage (vulnerable to XSS)

**Recommendation**:
- Consider migrating to HttpOnly secure cookies
- Or implement short-lived access tokens + refresh tokens

**Workaround**: Ensure CSP headers prevent script injection

---

### Rate Limiting
**Current**: Global rate limit of 2000/day per user

**Recommendation**:
- Add per-endpoint rate limits for sensitive operations
- Example: 10 seat assignments per minute

```python
# In settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_RATES': {
        'user': '2000/day',
        'seat_assignment': '10/minute',
        'booking': '20/hour',
    }
}
```

---

## 🚀 Production Deployment Checklist

### Pre-Deployment

- [ ] Generate strong `DJANGO_SECRET_KEY` (50+ characters)
- [ ] Create `.env` file with production credentials
- [ ] Set `DJANGO_DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Use strong database passwords (32+ characters)
- [ ] Review `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`
- [ ] Set up HTTPS/SSL certificate (Let's Encrypt)
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Configure logging and monitoring

### Deployment

```bash
# Use production compose file
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Verify DEBUG is disabled
docker exec trainline-backend python manage.py shell -c "from django.conf import settings; print(f'DEBUG={settings.DEBUG}')"

# Run security checks
docker exec trainline-backend python manage.py check --deploy
```

### Post-Deployment

- [ ] Test all authentication flows
- [ ] Verify HTTPS is working
- [ ] Test CORS configuration
- [ ] Monitor logs for errors
- [ ] Set up automated security scanning
- [ ] Configure backup retention policy
- [ ] Document incident response procedures

---

## 🔐 Security Best Practices

### 1. Secrets Management
- Never commit secrets to git
- Use environment variables or secrets managers (AWS Secrets Manager, HashiCorp Vault)
- Rotate secrets regularly (every 90 days)

### 2. Database Security
- Use connection pooling for performance
- Implement read replicas for scaling
- Regular backups with encryption at rest
- Restrict database access by IP

### 3. Application Security
- Keep dependencies updated
- Run automated security scans (OWASP ZAP, Bandit)
- Implement proper logging (but don't log sensitive data)
- Use prepared statements (Django ORM does this by default)

### 4. Network Security
- Use private networks for container communication
- Implement firewall rules
- Use VPN for administrative access
- DDoS protection (Cloudflare, AWS Shield)

### 5. Monitoring
- Set up alerts for failed login attempts
- Monitor unusual API usage patterns
- Track error rates and response times
- Use APM tools (New Relic, DataDog)

---

## 📞 Security Incident Response

If you discover a security vulnerability:

1. **Do NOT** publicly disclose the issue
2. Document the vulnerability details
3. Assess the impact and affected systems
4. Implement a fix and test thoroughly
5. Deploy the fix to production
6. Notify affected users if data was compromised
7. Document lessons learned

---

## 🛠️ Useful Commands

```bash
# Generate Django secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Run Django security checks
python manage.py check --deploy

# Audit Python dependencies
pip install pip-audit
pip-audit

# Check for outdated packages
pip list --outdated

# Test HTTPS configuration
curl -I https://yourdomain.com

# Verify security headers
curl -I https://yourdomain.com | grep -E "(X-Frame|X-Content|Strict-Transport)"
```

---

## 📚 Additional Resources

- [Django Security Checklist](https://docs.djangoproject.com/en/stable/topics/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Mozilla Observatory](https://observatory.mozilla.org/)
- [SSL Labs](https://www.ssllabs.com/ssltest/)

---

## Version History

- **v1.0** (2026-01-24): Initial security audit and fixes
  - Fixed hardcoded credentials
  - Added security headers
  - Fixed authorization vulnerabilities
  - Replaced runserver with Gunicorn
  - Pinned dependency versions
