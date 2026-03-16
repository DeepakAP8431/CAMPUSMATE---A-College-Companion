# CAMPUSMATE – A College Companion
A centralized web platform designed to simplify academic communication between students, faculty, and administrators.
CampusMate eliminates fragmented communication channels like notice boards, WhatsApp groups, and scattered emails by providing a **single digital platform** for sharing notices, assignments, notes, timetables, and events.

## Problem Statement
In many colleges, academic information is distributed across multiple sources such as physical notice boards, emails, and messaging groups. This fragmented system leads to:
* Missed deadlines
* Confusion about schedules
* Difficulty in accessing important resources
CampusMate solves this by creating a **centralized digital system** that becomes the single source of academic information.

## Objectives
* Centralize academic resources in one platform
* Provide easy access to notices, notes, assignments, and timetables
* Reduce information overload and missed deadlines
* Simplify resource sharing for faculty
* Improve communication between students and faculty

## System Architecture
The application follows the **MVC (Model-View-Controller) architecture**.
* **Model** → Database and business logic
* **View** → User interface built with HTML, CSS, Bootstrap
* **Controller** → Flask routes handling requests and responses
This architecture helps maintain clean and organized code.

##  User Roles
### Student
* No login required
* Select semester and division
* View notices, notes, assignments, timetable, and events
* Download learning materials

### Faculty
* Secure login
* Upload notes, assignments, and notices
* Manage uploaded resources
* Update profile information

### Admin
* Manage faculty/admin users
* Monitor system activity
* Full control over the platform

## Features
* Digital Notice Board
* Notes and Learning Resources
* Assignment Management
* Timetable Access
* Event Announcements
* Faculty Upload System
* Role-Based Access Control
* Deadline tracking with IST timezone
* Automatic deletion of outdated content

## Technologies Used
### Backend
* Python
* Flask
* Flask-Login
* SQLAlchemy
* Werkzeug Security
* Pytz

### Frontend
* HTML5
* CSS3
* Bootstrap 5
* JavaScript
* Jinja2 Templating

### Database
* SQLite (Development)

### Development Tools
* Visual Studio Code
* Git & GitHub

## System Requirements
### Hardware
* Processor: Intel i3 / Ryzen 3 or higher
* RAM: 4GB minimum (8GB recommended)
* Storage: 256GB SSD
* Internet connection

### Software
* Python 3.10+
* Flask
* Git
* Web browser (Chrome / Firefox / Edge)

## Project Structure
**CampusMate**
->app.py
->templates
->static
    ->css  
    ->images
->uploads
->database
->requirements.txt
->README.md

##  Installation

### 1 Clone the repository
git clone https://github.com/yourusername/campusmate.git

### 2 Navigate to project folder
cd campusmate

### 3 Create virtual environment
python -m venv venv

### 4 Activate virtual environment

Windows
venv\Scripts\activate

Linux / Mac
source venv/bin/activate

### 5 Install dependencies
pip install -r requirements.txt

### 6 Run the application
python app.py

Open browser and go to
http://127.0.0.1:5000

##  Future Improvements
* Push notifications
* Student discussion forum
* Cloud storage integration
* Real-time messaging
* 
## Team Members
* Abhishek Salunke
* Aftab Faniband
* Deepak Appayya Patil
* Prashanth Basappa Pujari

Basaveshwar Engineering College, Bagalkote
Department of Computer Science and Engineering

## License

This project is developed for academic purposes as part of a mini project for the Bachelor of Engineering (CSE).
