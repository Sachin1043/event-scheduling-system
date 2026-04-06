# 🗓️ Event Scheduling & Resource Allocation System

A full-featured **Event Scheduling and Resource Allocation** web application built with **Python/Flask** and **MySQL**. The system supports multi-role user management, event CRUD, resource tracking with real-time availability, an intelligent **conflict-detection engine**, weekly calendar views, utilisation reports with CSV export, and a complete REST API — all wrapped in a modern, dark-themed UI.

---

## 📑 Table of Contents

- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Screenshots](#-screenshots)
- [Demo Video](#-demo-video)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Database Schema](#-database-schema)
- [Project Structure](#-project-structure)
- [REST API Reference](#-rest-api-reference)
- [Docker Deployment](#-docker-deployment)
- [Testing](#-testing)
- [License](#-license)

---

## ✨ Features

| Category | Details |
|---|---|
| **Authentication** | Register, Login, Logout with secure password hashing (Werkzeug) |
| **Role-Based Access** | Three roles — `admin`, `organizer`, `viewer` — with granular route protection |
| **User Management** | Admin panel to create, edit, activate/deactivate user accounts |
| **Event Management** | Full CRUD for events with search, timezone support, and soft-delete |
| **Resource Management** | Manage rooms, instructors, and equipment with capacity tracking |
| **Resource Allocation** | Allocate resources to events with attendee & quantity validation |
| **Conflict Detection Engine** | Automatic checks for time-overlap, room capacity, and equipment availability |
| **Calendar View** | Weekly calendar with navigation to browse events across weeks |
| **Utilisation Reports** | Resource utilisation analytics with date-range filtering and **CSV export** |
| **Audit Logs** | Full audit trail of all create, update, delete, and toggle actions |
| **Settings** | Profile editing, password change, and admin-level app preferences |
| **REST API** | Complete JSON API for Events, Resources, and Allocations |
| **Docker Support** | Production-ready `Dockerfile` + `docker-compose.yml` |
| **Soft Delete & Restore** | Resources use soft-delete with admin restore capability |
| **Error Handling** | Custom 404 / 403 error pages |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11, Flask 3.x |
| **Database** | MySQL 8.0 |
| **ORM / DB** | Raw SQL via `mysql-connector-python` |
| **Templating** | Jinja2 |
| **Auth** | Werkzeug password hashing, Flask sessions |
| **Frontend** | HTML5, Vanilla CSS (dark theme), Jinja2 templates |
| **Containerisation** | Docker, Docker Compose |
| **Testing** | Python `unittest` |

---

## 📸 Screenshots


| Page | Screenshot |
|---|---|
| Login | ![Login](screenshots/login.jpeg) |
| Dashboard | ![Dashboard](screenshots/dashboard.jpeg) |
| Events | ![Events](screenshots/events.jpeg) |
| Event Detail | ![Event Detail](screenshots/event_detail.jpeg) |
| Resources | ![Resources](screenshots/resources.jpeg) |
| Calendar | ![Calendar](screenshots/calendar.jpeg) |
| Report | ![Report](screenshots/report.jpeg) |
| Audit Logs | ![Audit Logs](screenshots/audit.jpeg) |
| Settings | ![Settings](screenshots/settings.jpeg) |



## 🚀 Getting Started

### Prerequisites

- **Python 3.10+**
- **MySQL 8.0+** (or use Docker)
- **pip** (Python package manager)

### 1. Clone the Repository

```bash
git clone https://github.com/Sachin1043/event-scheduling-system.git
cd event-scheduling-system
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up the Database

Create the MySQL database and tables:

```sql
CREATE DATABASE event_scheduler;
USE event_scheduler;

-- Users table
CREATE TABLE users (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(100) NOT NULL UNIQUE,
    email         VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role          ENUM('admin','organizer','viewer') DEFAULT 'viewer',
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Events table
CREATE TABLE events (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    title       VARCHAR(255) NOT NULL,
    description TEXT,
    start_time  DATETIME NOT NULL,
    end_time    DATETIME NOT NULL,
    timezone    VARCHAR(50) DEFAULT 'UTC',
    created_by  INT NOT NULL,
    is_deleted  BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- Resources table
CREATE TABLE resources (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(255) NOT NULL,
    resource_type ENUM('room','instructor','equipment') NOT NULL,
    capacity      INT DEFAULT 1,
    description   TEXT,
    location      VARCHAR(255),
    is_active     BOOLEAN DEFAULT TRUE,
    is_deleted    BOOLEAN DEFAULT FALSE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Allocations table
CREATE TABLE allocations (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    event_id        INT NOT NULL,
    resource_id     INT NOT NULL,
    quantity_needed INT DEFAULT 1,
    attendees_count INT DEFAULT 1,
    notes           TEXT,
    allocated_by    INT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (event_id)    REFERENCES events(id),
    FOREIGN KEY (resource_id) REFERENCES resources(id),
    FOREIGN KEY (allocated_by) REFERENCES users(id)
);

-- Audit Logs table
CREATE TABLE audit_logs (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT,
    action      VARCHAR(50) NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    entity_id   INT,
    details     TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Seed an admin user (password: admin123)
INSERT INTO users (username, email, password_hash, role)
VALUES ('admin', 'admin@example.com',
        'scrypt:32768:8:1$...',  -- generate via: python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('admin123'))"
        'admin');
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=event_scheduler
SECRET_KEY=your-secret-key-here
FLASK_DEBUG=1
```

### 6. Run the Application

```bash
python app.py
```

The app will be available at **http://localhost:5000**

---

## 🔑 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DB_HOST` | MySQL host address | `localhost` |
| `DB_USER` | MySQL username | `root` |
| `DB_PASSWORD` | MySQL password | *(empty)* |
| `DB_NAME` | Database name | `event_scheduler` |
| `SECRET_KEY` | Flask session secret key | `fallback-secret-key` |
| `FLASK_DEBUG` | Enable debug mode (`1` = on) | `1` |

---

## 🗄️ Database Schema

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    users     │     │    events    │     │  resources   │
├──────────────┤     ├──────────────┤     ├──────────────┤
│ id (PK)      │◄────│ created_by   │     │ id (PK)      │
│ username     │     │ id (PK)      │     │ name         │
│ email        │     │ title        │     │ resource_type│
│ password_hash│     │ description  │     │ capacity     │
│ role         │     │ start_time   │     │ description  │
│ is_active    │     │ end_time     │     │ location     │
│ created_at   │     │ timezone     │     │ is_active    │
└──────────────┘     │ is_deleted   │     │ is_deleted   │
        │            │ created_at   │     │ created_at   │
        │            └──────┬───────┘     └──────┬───────┘
        │                   │                    │
        │            ┌──────┴────────────────────┘
        │            │
        ▼            ▼
┌──────────────────────────┐     ┌──────────────┐
│      allocations         │     │  audit_logs  │
├──────────────────────────┤     ├──────────────┤
│ id (PK)                  │     │ id (PK)      │
│ event_id (FK → events)   │     │ user_id (FK) │
│ resource_id (FK → res.)  │     │ action       │
│ quantity_needed           │     │ entity_type  │
│ attendees_count           │     │ entity_id    │
│ notes                     │     │ details      │
│ allocated_by (FK → users) │     │ created_at   │
│ created_at                │     └──────────────┘
└──────────────────────────┘
```

---

## 📁 Project Structure

```
event_schedular/
│
├── app.py                  # Main Flask application — all routes & API
├── models.py               # Database query functions (users, events, resources, allocations, reports, audit)
├── conflict.py             # Conflict detection engine (time overlap, capacity, quantity)
├── database.py             # MySQL connection helper
├── test_conflict.py        # Unit tests for the conflict engine
│
├── templates/
│   ├── base.html           # Base layout with navigation & dark theme
│   ├── login.html          # Login page
│   ├── register.html       # Registration page
│   ├── index.html          # Dashboard with stats & upcoming events
│   ├── events.html         # Events listing with search
│   ├── event_form.html     # Create / Edit event form
│   ├── event_detail.html   # Event detail + resource allocation
│   ├── resources.html      # Resources listing with type filter
│   ├── resources_form.html # Create / Edit resource form
│   ├── deleted_resources.html # Deleted resources (admin restore)
│   ├── allocations.html    # All allocations overview
│   ├── calendar.html       # Weekly calendar view
│   ├── report.html         # Utilisation report with CSV export
│   ├── audit.html          # Audit log viewer
│   ├── settings.html       # Profile & app preferences
│   ├── users.html          # User management (admin)
│   └── 404.html            # Error page
│
├── static/
│   └── style.css           # Global CSS (dark theme)
│
├── requirements.txt        # Python dependencies
├── DockerFile              # Docker image build file
├── docker-compose.yml      # Docker Compose (MySQL + Flask)
├── preferences.json        # App preferences (timezone, date/time format)
├── .env                    # Environment variables (not committed)
└── .gitignore              # Git ignore rules
```

---

## 🔌 REST API Reference

All API endpoints require session-based authentication. Send requests with an active session cookie.

### Events API

| Method | Endpoint | Role Required | Description |
|---|---|---|---|
| `GET` | `/api/events` | Any authenticated | List all events |
| `GET` | `/api/events/:id` | Any authenticated | Get event by ID |
| `POST` | `/api/events` | Organizer / Admin | Create a new event |
| `PUT` | `/api/events/:id` | Organizer / Admin | Update an event |
| `DELETE` | `/api/events/:id` | Admin only | Delete an event |

**Create Event — Request Body:**
```json
{
  "title": "Team Meeting",
  "description": "Weekly sync-up",
  "start_time": "2026-04-10T09:00",
  "end_time": "2026-04-10T10:00",
  "timezone": "UTC"
}
```

### Resources API

| Method | Endpoint | Role Required | Description |
|---|---|---|---|
| `GET` | `/api/resources` | Any authenticated | List all resources |
| `GET` | `/api/resources/:id` | Any authenticated | Get resource by ID |
| `POST` | `/api/resources` | Organizer / Admin | Create a resource |
| `PUT` | `/api/resources/:id` | Organizer / Admin | Update a resource |
| `DELETE` | `/api/resources/:id` | Admin only | Delete a resource |

**Create Resource — Request Body:**
```json
{
  "name": "Conference Room A",
  "resource_type": "room",
  "capacity": 50,
  "description": "Main conference room",
  "location": "Building 1, Floor 2"
}
```

### Allocations API

| Method | Endpoint | Role Required | Description |
|---|---|---|---|
| `GET` | `/api/allocations` | Any authenticated | List all allocations |
| `POST` | `/api/allocations` | Organizer / Admin | Create an allocation |
| `DELETE` | `/api/allocations/:id` | Organizer / Admin | Remove an allocation |

**Create Allocation — Request Body:**
```json
{
  "event_id": 1,
  "resource_id": 2,
  "quantity_needed": 1,
  "attendees_count": 30,
  "notes": "Need projector setup"
}
```

> ⚠️ Allocations go through the **conflict detection engine** which checks for time overlaps, capacity violations, and equipment availability before allowing creation.

---

## 🐳 Docker Deployment

### Quick Start with Docker Compose

```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

This starts:
- **MySQL 8.0** database on port `3306`
- **Flask app** on port `5000`

The database is automatically initialized with the schema from `schema.sql`.

---

## 🧪 Testing

Run the conflict engine unit tests:

```bash
python -m pytest test_conflict.py -v
```

Or with `unittest`:

```bash
python -m unittest test_conflict -v
```

---

## 🔒 Default Credentials

| Role | Email | Password |
|---|---|---|
| Admin | `admin@example.com` | `admin123` |

> ⚠️ **Change the default admin password in production!**

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📧 Submission

- **To:** hr@aerele.in
- **CC:** vignesh@aerele.in
- **Subject:** Assignment Submission - Event Scheduling & Resource Allocation System

---

## 📄 License

This project is built as an assignment submission for Aerele Technologies.

---

<p align="center">
  Built with ❤️ using Flask & MySQL
</p>
