# Event Scheduling & Resource Allocation System
A web application built with Python, Flask, and MySQL to manage events, allocate resources, and automatically detect scheduling conflicts. It includes a dark-themed UI and role-based access for different types of users.

[Watch the Demo Video](https://drive.google.com/file/d/154w41FlCGjsuzQDUIkQSH6DgRGflfgLw/view?usp=drive_link)

## Features
* **Role-Based Access:** Secure login with `admin`, `organizer`, and `viewer` roles.
* **Event & Resource Management:** Full CRUD operations for events, rooms, instructors, and equipment.
* **Conflict Detection:** Automatically prevents overlapping times and room capacity issues.
* **Calendar View:** A weekly layout to easily navigate and visualize the schedule.
* **Reports:** Generate resource utilisation reports and export them as CSV files.
* **Audit Logs:** Track all user actions and system changes for accountability.
* **REST API:** Complete JSON API for backend operations.
* **Error Handling:** Custom 404 and 403 pages.

**Tech Stack:**
* **Backend:** Python, Flask, Flask Sessions, Werkzeug
* **Database:** MySQL
* **Frontend:** HTML, CSS, Jinja2
* **Deployment:** Docker, Docker Compose

## How It Works

1. **Login** — Open the app and log in. Your role (Admin, Organizer, or Viewer) decides what you can do.

2. **Add Resources** — Admin adds things that can be booked, like rooms, projectors, or instructors.

3. **Create an Event** — Organizer creates an event with a name, date, and time.

4. **Book a Resource** — Organizer picks a resource for that event. The app automatically checks if it is free at that time, has enough capacity, and enough units available. If something is wrong, it shows an error. If all is good, it is saved.

5. **View the Calendar** — Anyone can open the calendar to see what is scheduled for the week.

6. **Download Reports** — Admin can download a CSV to see how often each resource is being used.

7. **Check Audit Logs** — Admin can see a full history of who did what inside the app.

8. **Settings** — Every user can update their profile and password. Admin can also change the timezone and date format for the app.

## Screenshots

**Login Screen**
![Login Screen](screenshots/login.jpeg)

**Dashboard**
![Dashboard](screenshots/dashboard.jpeg)

**Events**
![Events](screenshots/events.jpeg)

**Event Detail**
![Event Detail](event_detail.jpeg)

**Resources**
![Resources](screenshots/resources.jpeg)

**Calendar**
![Calendar](screenshots/calendar.jpeg)

**Reports**
![Reports](screenshots/reports.jpeg)

**Audit Logs**
![Audit Logs](screenshots/audit.jpeg)

**Settings**
![Settings](screenshots/settings.jpeg)

## Getting Started

### 1. Prerequisites
Make sure you have Python 3.x and MySQL installed on your system.

### 2. Installation
Clone the repository and set up a virtual environment:
```bash
git clone https://github.com/Sachin1043/event-scheduling-system.git
cd event-scheduling-system
python -m venv venv
venv\Scripts\activate # On Mac/Linux use: source venv/bin/activate
pip install -r requirements.txt
```
