# Library Service API


## Overview
The Library Service API is a backend system built 
with Django REST Framework to manage a library's 
operations. The system allows users to browse books, 
borrow them, manage borrowings, and handle payments 
using Stripe. Additionally, it integrates with 
Telegram for sending notifications about borrowings 
and overdue items.

## Features

### Books Management: 
* Allows users to view available books in the library.

### Borrowing System:
* Users can borrow books, and the system automatically calculates
borrowing duration and fees.

### User Authentication: 
Users can register, log in, and manage their profiles.

### Payments Integration: 
* Supports payments through Stripe, including creating payment 
sessions and handling fines for overdue borrowings.

### Notifications: 
* Sends notifications to users via Telegram when a borrowing is 
created, overdue, or returned.

### Admin Management: 
* Admins can manage books, users, and borrowings.

## API Endpoints

### Authentication:
- POST /api/user/login/: Log in with credentials to receive JWT tokens.
- POST /api/user/register/: Register a new user

### Users:
- POST /api/user/register/: Register a new user.
- POST /api/user/token/: Obtain a JWT token by providing valid credentials (login).
- POST /api/user/token/refresh/: Refresh the JWT token.
- POST /api/user/token/verify/: Verify the validity of a JWT token.
- GET /api/user/me/: Retrieve or update the authenticated user's profile.

### Books:
- GET /api/books/: List all available books.
- GET /api/books/{id}/: Get details of a specific book.
- POST /api/books/: Create a new book (admin only).
- PATCH /api/books/{id}/: Update book details (admin only).
- DELETE /api/books/{id}/: Delete a book (admin only)

### Borrowings:
- GET /api/borrowings/: List all borrowings (for admin) or borrowings by a specific user.
- POST /api/borrowings/: Create a new borrowing.
- GET /api/borrowings/{id}/: Retrieve details of a specific borrowing.
- PATCH /api/borrowings/{id}/: Update borrowing details (e.g., return date).
- DELETE /api/borrowings/{id}/: Delete a borrowing (admin only).

### Payments:
- POST /api/payments/checkout/: Create a Stripe payment session for a borrowing.
- POST /api/payments/webhook/: Stripe webhook to handle payment confirmation.

### Debugging:
GET /__debug__/: Django Debug Toolbar (only available in development mode).

## Installation
Python3 must be already installed
* git clone https://github.com/romanshupak/library-service.git
* stripe account
* telegram bot token
* cd library-service
* python -m venv venv
* venv\Scripts\activate (on Windows)
* source venv/bin/activate (on macOS)
* pip install -r requirements.txt
* python manage.py migrate
* python manage.py runserver

### Running with Docker
To run the project using Docker, ensure that Docker is installed on your system.

1. Build the containers:
   ```bash
   docker-compose build
2. Run the containers:
    ```bash
   docker-compose up
3. To run Redis (used for Celery task queue):
    ```bash
    docker run -d -p 6379:6379 redis

### Environment Variables
To configure the application, you need to set up the following environment variables in your .env file:

* DJANGO_SECRET_KEY: The secret key used by Django for security purposes. This should be a long, random string.
* TELEGRAM_BOT_TOKEN=Your_bot_token
* TELEGRAM_CHAT_ID=Your_chat_id

* CELERY_BROKER_URL=CELERY_BROKER_URL
* CELERY_RESULT_BACKEND=CELERY_RESULT_BACKEND

* STRIPE_SECRET_KEY=STRIPE_SECRET_KEY
* STRIPE_PUBLISHABLE_KEY=STRIPE_PUBLISHABLE_KEY
* STRIPE_ENDPOINT_SECRET_KEY=STRIPE_ENDPOINT_SECRET_KEY

Make sure to replace the placeholder values with your actual configuration settings before running the application.

### Technologies Used
* Backend: Django, Django REST Framework
* Database: SQLite
* Asynchronous Tasks: Celery, Redis
* Payments: Stripe
* Notifications: Telegram API
* Containerization: Docker

## Getting access
* create user via /api/user/register/
* get access token via /api/user/token/

## Additional Info
For demonstration purposes, you can use the following token credentials:
1) Email: library_admin@admin.com, Password: libraryadmin
2) Email: library_user1@user.com, Password: libraryuser1
3) Email: library_user2@user.com, Password: libraryuser2
4) Email: library_user3@user.com, Password: libraryuser3

#### These credentials provide access, allowing you to explore the application's features.
