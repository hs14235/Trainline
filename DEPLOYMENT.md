# Quick Start Deployment Guide

## 🚀 Development Setup

### Prerequisites
- Docker & Docker Compose installed
- Git

### Local Development (Quick Start)

```bash
# Clone the repository
git clone https://github.com/hs14235/Trainline.git
cd Trainline

# Start all services with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api
# Admin panel: http://localhost:8000/admin
# API docs: http://localhost:8000/api/docs/
```

### Development without Docker

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your local settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env
# Edit .env with your API URL

# Start development server
npm start
```

---

## 🏭 Production Deployment

### Step 1: Prepare Environment

1. **Generate Secure Secret Key**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

2. **Create Production .env File**
```bash
# Copy the template
cp .env.production.example .env

# Edit with secure values
nano .env
```

Required variables:
```env
DJANGO_SECRET_KEY=<your-generated-secure-key>
DJANGO_DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
POSTGRES_USER=<secure-username>
POSTGRES_PASSWORD=<strong-random-password>
POSTGRES_DB=trainline_production
REACT_APP_API_BASE=https://api.yourdomain.com
```

### Step 2: Deploy with Docker

```bash
# Build and start services in production mode
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f backend
```

### Step 3: Initial Setup

```bash
# Create Django superuser
docker exec -it trainline-backend python manage.py createsuperuser

# Verify security checks pass
docker exec -it trainline-backend python manage.py check --deploy
```

### Step 4: Configure HTTPS

**Option A: Using Let's Encrypt with Nginx Reverse Proxy**

Create `nginx-ssl.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Proxy to Django backend
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Proxy to React frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$host$request_uri;
}
```

**Option B: Using Cloudflare**
1. Add your domain to Cloudflare
2. Enable "Full (strict)" SSL mode
3. Enable "Always Use HTTPS"
4. Enable "HSTS"

### Step 5: Database Backup

```bash
# Create backup script
cat > backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
docker exec trainline-db pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_DIR/backup_$DATE.sql
EOF

chmod +x backup-db.sh

# Schedule with cron (daily at 2 AM)
echo "0 2 * * * /path/to/backup-db.sh" | crontab -
```

---

## 🔒 Security Checklist

Before going live, verify:

- [ ] `DJANGO_DEBUG=False` in production
- [ ] Strong `DJANGO_SECRET_KEY` (50+ characters)
- [ ] Strong database passwords
- [ ] `ALLOWED_HOSTS` configured with your domain
- [ ] HTTPS/SSL certificate configured
- [ ] Firewall rules configured (allow only 80, 443, SSH)
- [ ] Database backups scheduled
- [ ] Monitoring and logging set up
- [ ] Security headers verified (check with https://securityheaders.com)
- [ ] All environment variables in `.env` (not in docker-compose.yml)
- [ ] `.env` file in `.gitignore` (never commit secrets)

---

## 📊 Monitoring & Maintenance

### Health Check
```bash
# Check if services are healthy
curl http://localhost:8000/healthz

# Should return: {"ok": true}
```

### View Logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Update Dependencies
```bash
# Check for outdated packages
docker exec trainline-backend pip list --outdated

# Update specific package
# Edit requirements.txt, then:
docker-compose down
docker-compose up -d --build
```

### Database Migrations
```bash
# After code changes that modify models
docker exec trainline-backend python manage.py makemigrations
docker exec trainline-backend python manage.py migrate
```

---

## 🆘 Troubleshooting

### Application Won't Start

```bash
# Check logs for errors
docker-compose logs backend

# Common issues:
# 1. Missing environment variables - check .env file
# 2. Database not ready - wait for healthcheck
# 3. Port already in use - change port in docker-compose.yml
```

### Database Connection Errors

```bash
# Check database is running
docker-compose ps db

# Test database connection
docker exec trainline-backend python manage.py dbshell
```

### Static Files Not Loading

```bash
# Collect static files
docker exec trainline-backend python manage.py collectstatic --noinput

# Restart backend
docker-compose restart backend
```

### CORS Errors

Edit `backend/booking/settings.py`:
```python
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

---

## 🔄 Updating Production

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml down
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

# Run migrations
docker exec trainline-backend python manage.py migrate

# Verify deployment
docker exec trainline-backend python manage.py check --deploy
```

---

## 📝 Common Tasks

### Create Admin User
```bash
docker exec -it trainline-backend python manage.py createsuperuser
```

### Reset Database (Development Only!)
```bash
docker-compose down -v
docker-compose up -d
```

### Run Security Audit
```bash
cd backend
pip install pip-audit
pip-audit
```

### Run Django Checks
```bash
docker exec trainline-backend python manage.py check --deploy
```

---

## 📞 Support

- **Security Issues**: See [SECURITY.md](SECURITY.md)
- **Documentation**: See [README.md](README.md)
- **Issues**: https://github.com/hs14235/Trainline/issues

---

## 📚 Additional Resources

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Let's Encrypt Setup](https://letsencrypt.org/getting-started/)
