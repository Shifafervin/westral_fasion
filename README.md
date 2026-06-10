# Westral Fashion

A full-featured e-commerce web application built using Django.

## Overview

Westral Fashion is an online shopping platform that allows users to browse products, manage carts, place orders, apply coupons, manage addresses, and complete secure payments. The platform also includes a dedicated admin panel for product, category, order, offer, and coupon management.

## Features

### User Features

* User Registration & Login
* Google Authentication
* Product Browsing
* Product Search & Filtering
* Shopping Cart
* Wishlist
* Address Management
* Checkout Process
* Coupon Application
* Order Management
* Order Cancellation
* Wallet Management
* User Profile

### Admin Features

* Dashboard
* Product Management
* Category Management
* Order Management
* Coupon Management
* Offer Management
* Sales Reporting

## Tech Stack

### Backend

* Python
* Django

### Database

* PostgreSQL

### Frontend

* HTML
* CSS
* JavaScript
* Bootstrap

### Third-Party Integrations

* Razorpay Payment Gateway
* Google Authentication

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd westral_fasion
```

### Create Virtual Environment

```bash
python -m venv myvenv
```

### Activate Virtual Environment

Windows:

```bash
myvenv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment Variables

Create a `.env` file and add the required configuration values.

### Run Migrations

```bash
python manage.py migrate
```

### Run Server

```bash
python manage.py runserver
```

## Project Structure

```text
user/
admin/
templates/
static/
media/
westral_fasion/
```

## Future Improvements

* Product Reviews & Ratings
* Email Notifications
* Advanced Analytics
* Product Recommendations

## Author

Munavar Salih
