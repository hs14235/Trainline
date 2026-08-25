

## Welcome to Trainline!
![Trainline Demo](backend/docs/Trainline-GIF.gif)


---


## Overview

Trainline is an independently developed full-stack train-booking platform built with
React, Django REST Framework, PostgreSQL, and Docker.

The application supports end-to-end workflows for authentication, trip discovery,
seat selection, booking, payment validation, notifications, and in-app chat. Its
architecture separates the frontend, REST API, and relational database into
independently containerized services, with environment-based configuration and
production-oriented security controls.

The project was built to deepen hands-on experience across API design, relational
data modeling, frontend/backend integration, security hardening, containerized
deployment, and the end-to-end software development lifecycle.
---
## Engineering Highlights

- Containerized frontend, backend, and PostgreSQL services
- Relational models for users, trips, tickets, seating, and payments
- Authentication and authorization controls
- Input validation and API boundary protections
- Environment-based secret management
- Security headers and HTTPS-oriented production settings
- Documented Docker production deployment
---

## Features
-  User Authentication (Register/Login)
-  Browse and book train trips
-  Ticket + Seat selection
-  Payment system
-  Notifications widget
-  Chat widget

---

## Screenshots
![Login](backend/docs/traindemo-login.jpg)
![Signup](backend/docs/traindemo-signup.jpg)
![Book a Trip](backend/docs/tripdemo-booking.jpg)
![Payment](backend/docs/traindemopayment.jpg)




## Relational Schema
| Table             | Key Fields                        | Relationships                                |
|-------------------|-----------------------------------|----------------------------------------------|
| **User**          | user_id (PK), email, password     | One-to-many with Tickets                     |
| **Ticket**        | ticket_id (PK), user_id (FK)      | Many-to-many with Passenger (via bridge)     |
| **Passenger**     | passenger_id (PK), name           | Linked to Ticket via Ticket_Passenger        |
| **Flight/Train**  | flight_id (PK), route, time       | One-to-many with Tickets                     |
| **Payment**       | payment_id (PK), ticket_id (FK)   | One-to-one with Ticket                       |
| **Notifications** | notif_id (PK), user_id (FK)       | One-to-many with User                        |

---

## Tech Stack

- **Frontend:** React, JavaScript, CSS, Axios
- **Backend:** Django, Django REST Framework
- **Database:** PostgreSQL
- **Authentication:** Django REST authentication / token and session authentication
- **Infrastructure:** Docker, Docker Compose

---

## Architecture

React Client
    ↓ REST
Django REST Framework
    ↓ ORM
PostgreSQL


## Local Setup & Installation [POWERSHELL]
Backend 
1) cd $HOME\Desktop\Trainline
   [ACTIVATE VIRTUAL ENVIRONMENT]
2) .\.venv\Scripts\Activate.ps1
   [IF YOU GET ERROR] 
3) Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
4) python manage.py runserver


Frontend 
1) cd frontend
2) cp .env.example .env
3) npm install
4) npm start

---

## Security & Production Deployment

This application has undergone a comprehensive security audit. For production deployment:

- **[SECURITY.md](SECURITY.md)** - Security audit report, vulnerabilities fixed, and best practices
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Step-by-step production deployment guide with Docker

### Quick Production Setup
```bash
# Generate secure secret key
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

# Create .env file with production values
cp .env.production.example .env

# Deploy with Docker Compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

** Important:** Never use default credentials in production. See SECURITY.md for full checklist.

---



## License
This project is licensed under the [MIT License](LICENSE).
