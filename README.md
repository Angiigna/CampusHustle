# Papido — Campus Bike-Taxi Mobility Platform 🛵💨

[![Google for Developers](https://img.shields.io/badge/Google%20for%20Developers-Hackathon%20Project-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://developers.google.com/)
[![Pondicherry University](https://img.shields.io/badge/Pondicherry%20University-PromptWars%20x%20The%20Prompt%20Arena-D97706?style=for-the-badge)](https://www.pondiuni.edu.in/)
[![Python Flask](https://img.shields.io/badge/Flask-3.0+-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Google Cloud Run](https://img.shields.io/badge/Google%20Cloud%20Run-Containerized-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/run)

---

## 🏆 Hackathon Context & Problem Statement

**Papido** was created for **PromptWars x The Prompt Arena**, a hackathon hosted with **Google for Developers** at **Pondicherry University**.

### 📌 Problem Statement: *Campus Hustle: Give a campus WhatsApp business its own app*

> *"Campus life runs on WhatsApp groups: buy and sell, laundry, late-night food, rentals, tutoring. They work until messages get buried, prices get lost, and every deal begins with 'is this still available?'"*
>
> **Your mission**: Pick one campus business (existing, or one that should exist) and give it a proper home on the web.

### 💡 The Real-World Campus Initiative Behind Papido

At Pondicherry University, a popular student-run bike-taxi initiative operates entirely via chaotic WhatsApp groups. Students needing quick transport across the sprawling 800-acre campus send messages into busy chat groups, where bike-owning students manually negotiate fares and pick up passengers.

**What the WhatsApp version gets wrong:**
- **Buried Messages**: During peak morning class hours and hostel curfews, messages get lost instantly.
- **Price Uncertainty**: Every ride starts with awkward price bargaining.
- **Trust & Safety Concerns**: No verification of who is picking up the student or whether the rider is authorized.
- **No Real-Time Tracking**: Students wait at campus gates with zero visibility on rider arrival time.

**Papido** addresses these exact pain points by giving this real campus initiative a dedicated, web-first platform: fixed upfront pricing, 1-click dispatch, verbal OTP verification, live GPS map tracking, and admin authorization.

---

## 🔑 Hackathon Jury / Evaluator Access (Admin Credentials)

To allow the **PromptWars Hackathon Jury & Panel** to evaluate the complete end-to-end service—including rider authorization controls, operational monitoring, and dispatch oversight—a dedicated Admin account is pre-configured.

### 🛡️ Admin Panel Login Credentials

| Field | Credentials |
|---|---|
| **Login URL** | [https://papidocampus.loca.lt/login](https://papidocampus.loca.lt/login) |
| **Email ID** | `sivangisankar12a@gmail.com` |
| **Password** | `admin123` |
| **Role** | `ADMIN` (Campus Dispatch & Rider Operations Manager) |

> **Note for Jury**: These credentials are provided exclusively for the hackathon evaluation panel to test the Admin Console (`/admin`). Upon actual production deployment with campus operations, administrator credentials will be updated and secured confidentially.

---

## ✨ Features & Capability Breakdown

### 🎓 1. Student Customer Portal
- **Instant Upfront Fare Engine**: Selects pickup and drop-off points across 39 mapped Pondicherry University campus location nodes (Gates, Academic Departments, Boys & Girls Hostels, Messes).
- **1,482 Fixed Fare Routes**: Pre-calculated transparent pricing eliminating awkward price bargaining.
- **4-Digit Verbal OTP Security Handshake**: Generates a unique 4-digit code per ride; rider must enter the correct OTP before ride starts.
- **Live Leaflet OpenStreetMap Tracking**: Real-time rider motorcycle marker animation on an interactive map using browser Geolocation (`navigator.geolocation.watchPosition()`) with freshness indicators.
- **Post-Ride Rating Modal**: 5-star rating and feedback system for rider quality assurance.

### 🛵 2. Partner Rider Portal
- **Rider Application Workflow**: Simple registration asking for vehicle type (Motorbike, Scooter, EV) and vehicle registration number.
- **Admin Authorization Barrier**: Unapproved rider applicants receive a pending authorization notice and are blocked from going online or receiving broadcasts until approved.
- **Online / Offline Availability Toggle**: Instant status toggle for riders between classes or free hours.
- **Live Dispatch Broadcast Modal**: Socket.IO real-time notification with sound alert (`requestChime`) when a nearby ride is requested.
- **GPS Location Streaming**: Automated background GPS position updates throttled to ~2.5s intervals for student tracking.

### 📊 3. Admin Operations Console
- **1-Click Rider Approval Workflow**: Review pending rider registration applications with 1-click `[Approve]` or `[Reject]` actions.
- **Live Operational KPIs**: Real-time stats counting Today's Revenue, Available Riders, Active Dispatches, and Completed Rides.
- **Full Ride Feed**: Complete oversight of all active, assigned, and completed trips across campus.

---

## 🛠️ Tech Stack & Architecture

- **Backend**: Python 3.13, Flask 3.0+, Flask-SQLAlchemy (SQLite / PostgreSQL ready), Flask-Login
- **Real-Time Communication**: Flask-SocketIO + Gevent / Gevent-WebSocket WSGI worker for non-blocking asynchronous event handling.
- **Frontend**: HTML5, Tailwind CSS (Custom Papido Yellow & Flame Red Palette), FontAwesome, Leaflet OpenStreetMap JS SDK.
- **Containerization & Cloud**: Docker, Gunicorn, Google Cloud Run (`gcloud run deploy`).

---

## 🚀 Local Setup & Cloud Run Deployment

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/Angiigna/CampusHustle.git
cd CampusHustle

# 2. Create virtual environment & install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\activate
pip install -r requirements.txt

# 3. Seed database with campus nodes, fare matrix, and admin user
python seed.py

# 4. Run application
python run.py
```

### ☁️ Deploying to Google Cloud Run

```bash
gcloud run deploy papido \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080
```

---

## 📄 License & Attribution

Developed for **PromptWars x The Prompt Arena Hackathon** (Google for Developers x Pondicherry University).
All rights reserved by team **Papido**.
