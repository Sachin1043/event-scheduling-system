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

**Tech Stack:** * **Backend:** Python, Flask, Flask Sessions, Werkzeug
* **Database:** MySQL
* **Frontend:** HTML, CSS, Jinja2
* **Deployment:** Docker, Docker Compose

## How It Works

Here is a quick rundown of the app's flow:

1. **Setup:** An `admin` logs in first to add resources into the system (like conference rooms, projectors, or guest speakers).
2. **Booking:** An `organizer` logs in, picks a date and time, and tries to book a room for an event.
3. **The Conflict Check:** Before saving, the app double-checks if that room or equipment is already taken. If it is, it throws an error and makes the user pick another time. If it's free, the event is saved to the database.
4. **Viewing the Schedule:** Users can pull up the weekly calendar view to easily see what is booked and what is available.
5. **Admin Tracking:** Admins can download CSV reports to see how often certain rooms are being used, or check the audit logs to see exactly who did what.

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
git clone [https://github.com/Sachin1043/event-scheduling-system.git](https://github.com/Sachin1043/event-scheduling-system.git)
cd event-scheduling-system

python -m venv venv
venv\Scripts\activate # On Mac/Linux use: source venv/bin/activate

pip install -r requirements.txt
