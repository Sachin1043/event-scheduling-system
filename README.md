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

## Screenshots

* [Login Screen](screenshots/login.jpeg)
* [Dashboard](screenshots/dashboard.jpeg)
* [Events](screenshots/events.jpeg) | [Event Detail](event_detail.jpeg)
* [Resources](screenshots/resources.jpeg)
* [Calendar](screenshots/calendar.jpeg)
* [Reports](screenshots/reports.jpeg)
* [Audit Logs](screenshots/audit.jpeg)
* [Settings](screenshots/settings.jpeg)

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
