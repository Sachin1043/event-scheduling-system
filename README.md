# Event Scheduling & Resource Allocation System

A web application built with Python, Flask, and MySQL to manage events, allocate resources, and automatically detect scheduling conflicts. It includes a dark-themed UI and role-based access for different types of users.

[Watch the Demo Video](https://drive.google.com/file/d/154w41FlCGjsuzQDUIkQSH6DgRGflfgLw/view?usp=drive_link)

## ✨ Features

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

## 🔄 System Workflow

Here is how the application works step-by-step:

1. **System Setup:** The `admin` logs in and adds resources to the system (e.g., Conference Rooms, Projectors, Instructors).
2. **User Authentication:** Users log in. Their access level determines what they can see and do (`admin`, `organizer`, or `viewer`).
3. **Event Creation:** An `organizer` selects a date, time, and resource, then submits a request to schedule an event.
4. **Conflict Checking:** The system instantly checks if the requested room or resource is already booked for that specific time.
   * *If clear:* The event is scheduled successfully and added to the database.
   * *If double-booked:* The system stops the booking, shows a conflict error, and prompts the user to pick a different time or room.
5. **Tracking & Viewing:** Users can check the weekly calendar to see a visual layout of all scheduled events and available slots. 
6. **Reporting:** Admins and organizers can generate CSV reports of how often resources are used, and admins can check the audit logs to track user activity.

## 📸 Screenshots

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

## 🚀 Getting Started

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
