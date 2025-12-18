<div align="center">
  <img src="https://drive.google.com/uc?export=view&id=1ntZlsr9E4f3jc56B20muTQDw_T14db3Q" alt="UIA SmartTour Header" width="100%"/>
</div>

# UIA SmartTour - Intelligent Food Recommendation Web Application

**Computational Thinking Course Project**  
**Class: 24C08**  
**VNUHCM - University of Science**  
**Faculty of Information Technology**

---

## Table of Contents

- [About The Project](#about-the-project)
- [Team Members](#team-members)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)
- [Acknowledgments](#acknowledgments)

---

## About The Project

**UIA SmartTour** is an intelligent web-based food recommendation system designed to help first-time travelers discover authentic local restaurants in Vietnam. Guided by the principle "Cuisine is not only about taste — it's about emotion and connection", our platform enhances travel experiences through personalized dining recommendations.

### Problem Statement

Travelers visiting new destinations often struggle to:
- Find authentic local restaurants without prior knowledge
- Navigate through overwhelming options with limited time
- Balance personal preferences (taste, budget) with local specialties
- Discover regional delicacies and popular food areas

### Our Solution

UIA SmartTour provides AI-powered restaurant recommendations using a six-step filtering algorithm that considers: Open/Closed status → Budget → Taste preferences → User ratings → Location proximity → Weather conditions. The system combines computational thinking principles (Decomposition, Abstraction, Pattern Recognition, and Algorithmic Design) to deliver accurate, context-aware dining suggestions.

---

## Team Members

**Group: U I A**
<table>
  <tr>
    <th>Name</th>
    <th>Student ID</th>
    <th>Role</th>
  </tr>
  <tr>
    <td>Mai Khánh Băng</td>
    <td>24127147</td>
    <td>Project Manager, Frontend Developer</td>
  </tr>
  <tr>
    <td>Nguyễn Ngọc Minh</td>
    <td>24127204</td>
    <td>Frontend Developer</td>
  </tr>
  <tr>
    <td>Trần Minh Hiển</td>
    <td>24127037</td>
    <td>Tech Lead, Backend Developer, Tester Engineer</td>
  </tr>
  <tr>
    <td>Đoàn Võ Ngọc Lâm</td>
    <td>24127435</td>
    <td>Frontend, Backend Developer</td>
  </tr>
  <tr>
    <td>Trần Thuận Khang</td>
    <td>24127054</td>
    <td>Backend Developer</td>
  </tr>
  <tr>
    <td>Võ Tấn An</td>
    <td>24127318</td>
    <td>Backend Developer, Frontend Developer, Tester Engineer</td>
  </tr>
  <tr>
    <td>Nguyễn Thanh Nguyên</td>
    <td>24127468</td>
    <td>Backend Developer, Tester Engineer</td>
  </tr>
</table>

**Instructors:**
- TS. Trương Phước Hưng
- Teacher Đỗ Đức Hào
- Teacher Trần Hoàng Quân

---

## Features

### Core Features
- **User Authentication** - Google OAuth & Traditional Login/Signup with OTP verification
- **AI Chatbot** - Gemini-powered conversational assistant with automatic API key rotation
- **Smart Search** - Fuzzy search with autocomplete and keyword suggestions
- **Interactive 2D Map** - Leaflet.js with marker clustering and routing capabilities
- **Multi-criteria Filtering** - Budget, search radius, opening hours
- **Restaurant Details** - Comprehensive information including reviews, ratings, menus, photos
- **Favorite & History Management** - Save and track visited restaurants
- **User Reviews** - Rate and comment on dining experiences
- **Food Plan Generator** - AI-powered daily dining itinerary creation
- **Real-time Notifications** - SSE-based notification system for social interactions
- **Multi-language Support** - Vietnamese and English interface with real-time switching

### Additional Features
- **Mini Puzzle Game** - Vietnamese food-themed jigsaw puzzles with achievements
- **Music Player** - Background music while browsing
- **Achievement System** - Gamification with daily streaks and unlockable badges
- **Social Features** - Friend system, share food plans, view friends' favorites
- **Weather Integration** - Real-time weather-based recommendations
- **GPS Location** - Automatic location detection for proximity-based search

---

## Technology Stack

### Backend Technologies
- **Flask 2.3+** - Main web framework for restaurant data and map services
- **Django 4.2+** - User management, authentication, and social features
- **Python 3.8+** - Core programming language
- **SQLite** - Database management (development)
- **PostgreSQL** - Production database (optional)
- **Google Gemini AI** - Chatbot intelligence with multi-key load balancing
- **SSE (Server-Sent Events)** - Real-time notifications

### Frontend Technologies
- **HTML5** - Semantic markup structure
- **CSS3** - Modern styling with custom animations and transitions
- **JavaScript (ES6+)** - Interactive functionality and API integration
- **Leaflet.js v1.9.4** - Interactive maps
- **Leaflet Routing Machine** - Navigation and directions
- **Leaflet MarkerCluster v1.4.1** - Efficient marker grouping
- **SweetAlert2** - Beautiful alert modals
- **Fuse.js v7.0.0** - Client-side fuzzy search

### External APIs
- **Geoapify** - Restaurant data and geocoding services
- **OpenWeather** - Weather information for context-aware recommendations
- **Google OAuth 2.0** - Social authentication

### DevOps & Deployment
- **Docker** - Application containerization
- **Docker Compose** - Multi-container orchestration
- **Nginx** - Reverse proxy and load balancing
- **Git** - Version control system

---

## System Architecture

```
System/
│
├── Nginx (Port 80) - Reverse Proxy & Load Balancer
│   ├── Routes /api/places → Flask Backend
│   ├── Routes /api/accounts/ → Django Backend
│   ├── Routes /api/food-plan → Flask Backend
│   ├── Routes /accounts/ → Django Backend (OAuth)
│   ├── Routes /api/accounts/notifications/stream/ → Django Backend (SSE)
│   └── Routes / → Flask Backend (Main App)
│
├── Flask Backend (Internal Port 5000)
│   ├── Restaurant Data API
│   ├── Map Services
│   ├── Food Planner Generator
│   ├── Chatbot UI Component
│   ├── Music Player Component
│   ├── Language Toggle Component
│   └── Main Web Application
│
├── Django Backend (Internal Port 8000)
│   ├── User Authentication (Google OAuth + Traditional)
│   ├── OTP Verification System
│   ├── Social Features (Friends, Sharing)
│   ├── Real-time Notifications (SSE)
│   ├── Review & Favorite Management
│   ├── Preference Storage
│   ├── Achievement System
│   ├── Mini Game Progress
│   └── Admin Panel
│
├── Database Layer (SQLite)
│   ├── User Accounts & Profiles
│   ├── Restaurant Information
│   ├── User Reviews & Ratings
│   ├── Food Plans
│   ├── Notifications
│   ├── Friend Relationships
│   ├── Achievements & Streaks
│   └── Game Progress
│
└── External Services
    ├── Google Gemini AI (Chatbot)
    ├── Geoapify API (Restaurant Data)
    ├── OpenWeather API (Weather Data)
    └── Google OAuth 2.0 (Authentication)
```

### Data Flow

1. User interacts with the frontend interface (HTML/CSS/JavaScript)
2. All requests are routed through Nginx reverse proxy (Port 80)
3. Flask handles restaurant data, search, map services, and food planner
4. Django manages user authentication, social features, and real-time notifications via SSE
5. External APIs provide real-time data (weather, geocoding, AI chatbot)
6. Results are filtered through the six-step algorithm (Open/Closed → Budget → Taste → Rating → Location → Weather)
7. Recommendations are displayed on interactive Leaflet map with clustering

---

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker** (version 20.10 or higher)
- **Docker Compose** (version 1.29 or higher)
- **Git**

### Required API Keys

You'll need to obtain the following API keys:

1. **Google Gemini AI API Key(s)** - For chatbot functionality
   - Get it from: https://makersuite.google.com/app/apikey
   - **Recommended:** Create multiple keys for load balancing
   - Free tier: 60 requests per minute per key

2. **Gmail App Password** - For OTP email verification
   - Enable 2FA on your Google account
   - Generate at: https://myaccount.google.com/apppasswords
   - Use 16-character App Password (not regular password)

3. **Geoapify API Key** - For restaurant data (optional if using CSV data)
   - Get it from: https://www.geoapify.com/

4. **Google OAuth Credentials** - For social login (optional)
   - Configure at: https://console.cloud.google.com/
   - Set up OAuth consent screen
   - Create OAuth 2.0 Client ID

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/mkbang2411-oss/TDTT---U-I-A.git
cd TDTT---U-I-A
```

### 2. Configure API Keys

#### Flask Backend Configuration

Create `backend/config.json`:

```json
{
  "GEMINI_API_KEYS": [
    "your_gemini_api_key_1",
    "your_gemini_api_key_2",
    "your_gemini_api_key_3"
  ],
  "CURRENT_KEY_INDEX": 0
}
```

**Note:** The system supports multiple Gemini API keys for load balancing and automatic switching when rate limits are reached.

#### Django Backend Configuration

Create `user_management/.env`:

```env
# Django Secret Key
DJANGO_SECRET_KEY='your-django-secret-key-here'

# Gemini AI API Key
GEMINI_API_KEY="your_gemini_api_key_here"

# Email Configuration (for OTP)
EMAIL_HOST_USER="your_email@gmail.com"
EMAIL_HOST_PASSWORD="your_app_password"

# Cloudflare Tunnel (optional - for external access)
CLOUDFLARE_URL="your_cloudflare_tunnel_url"
```

**Email Setup for OTP:**
1. Use Gmail with App Password (not regular password)
2. Enable 2-Factor Authentication on your Google account
3. Generate App Password at: https://myaccount.google.com/apppasswords
4. Use the 16-character App Password in EMAIL_HOST_PASSWORD

### 3. Prepare Required Files

#### Backend Data Files

Ensure the following files exist in the `backend/` directory:

**Required:**
- `config.json` - Gemini API keys configuration (see step 2)
- `Data_with_flavor.csv` - Restaurant database with flavor profiles
- `reviews.json` - Initial restaurant reviews data
- `languages.json` - Translation files for multi-language support

**Optional:**
- `food_stories.json` - Stories about Vietnamese food for mini game

#### Django Configuration

Ensure `.env` file exists in `user_management/` directory (see step 2)

**Sample data structure:**

`reviews.json` format:
```json
{
  "place_id_1": {
    "google": [],
    "user": [
      {
        "author": "User Name",
        "rating": 5,
        "text": "Great food!",
        "time": "2024-01-01"
      }
    ]
  }
}
```

### 4. Build and Run with Docker

#### First Time Setup

```bash
# Build all containers
docker-compose down
docker-compose up -d --build

# Check if containers are running
docker ps
```

You should see three containers:
- `nginx` (Port 80)
- `flask-backend` (Internal Port 5000)
- `django-backend` (Internal Port 8000)

#### Subsequent Runs

```bash
# Start all services
docker-compose up

# Or run in detached mode
docker-compose up -d

# Stop all services
docker-compose down
```

### 5. Access the Application

Open your web browser and navigate to:

```
http://localhost
```

#### Optional: External Access via Cloudflare Tunnel

If you want to access the application from outside your local network:

1. Install Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/
2. Run tunnel pointing to localhost:80
3. Update CLOUDFLARE_URL in `user_management/.env` with your tunnel URL
4. Access via the provided Cloudflare URL

**Note:** This is optional and mainly used for testing on mobile devices or sharing with team members.

---

## Usage

### For First-Time Users

1. **Homepage** - Browse the interactive map showing restaurants in Saigon
2. **Sign Up** - Create an account or use Google OAuth
3. **Set Preferences** - Configure your taste preferences and budget
4. **Search** - Use the search bar or AI chatbot to find restaurants
5. **Filter** - Apply budget, radius, and other filters
6. **View Details** - Click map markers to see restaurant information
7. **Save Favorites** - Add restaurants to your favorites list
8. **Leave Reviews** - Share your dining experiences

### AI Chatbot Usage

1. Click the chatbot button (bottom right)
2. Ask questions like:
   - "Recommend me some Vietnamese restaurants"
   - "Where can I find good pho?"
3. The chatbot will suggest keywords and restaurant types
4. Click suggested keywords to initiate searches

**Note:** The system automatically rotates between multiple Gemini API keys to handle rate limits. If one key reaches its limit, the system switches to the next available key automatically.

### Food Plan Generator

1. Click the food planner button
2. Set your preferences:
   - Start time and end time
   - Theme (Traditional, Fusion, Street Food, etc.)
   - Search radius
3. Generate plan
4. View AI-generated daily dining itinerary
5. Share plans with friends

### Mini Game

1. Click the puzzle game button
2. Select a Vietnamese food image (Banh Mi, Com Tam, Bun Bo Hue)
3. Solve the jigsaw puzzle
4. Unlock achievements and view food stories

---

## API Endpoints

### Flask Backend (Port 5000)

#### Restaurant APIs
- `GET /api/places` - Get restaurant list with optional query parameter
- `GET /api/reviews/<place_id>` - Get reviews for a specific restaurant
- `GET /api/food-plan` - Generate food plan based on parameters

#### Frontend Pages
- `GET /` - Main application page
- `GET /account` - User account page
- `GET /accounts/<path>` - User management pages
- `GET /languages.json` - Get translation data

### Django Backend (Port 8000)

#### Authentication APIs
- `GET /accounts/login/` - Login page
- `POST /accounts/login/` - Process login
- `GET /accounts/signup/` - Signup page
- `POST /accounts/signup/` - Process registration
- `GET /accounts/logout/` - Logout user
- `GET /accounts/google/login/` - Google OAuth login

#### User APIs
- `GET /api/check-auth/` - Check authentication status
- `GET /api/user-info/` - Get current user information
- `POST /api/upload-avatar/` - Upload user avatar
- `POST /api/change-password/` - Change password

#### Notification APIs (SSE)
- `GET /api/accounts/notifications/stream/` - SSE real-time notification stream
- `GET /api/accounts/notifications/` - Get all notifications
- `POST /api/accounts/notifications/<id>/read/` - Mark notification as read
- `POST /api/accounts/notifications/read-all/` - Mark all as read
- `POST /api/accounts/notifications/<id>/delete/` - Delete notification
- `POST /api/accounts/notifications/clear-all/` - Delete all notifications

#### Social APIs
- `POST /api/favorite/` - Add/remove favorite restaurant
- `GET /api/get-favorites/` - Get user's favorite restaurants
- `POST /api/reviews/` - Submit restaurant review

#### Game APIs
- `GET /api/puzzle/` - Get puzzle game data
- `POST /api/puzzle/` - Save puzzle completion
- `GET /api/food-story/<map_name>` - Get food story for completed puzzle

#### Preference APIs
- `GET /api/accounts/preferences/` - Get user preferences
- `POST /api/accounts/preferences/save/` - Save preferences
- `DELETE /api/accounts/preferences/delete/` - Delete preference

#### API Key Management
- `GET /api/get-current-api-key/` - Get current active Gemini API key index
- `POST /api/switch-api-key/` - Switch to different API key (for rate limit handling)

#### OTP APIs
- `POST /api/send-otp/` - Send OTP code
- `POST /api/verify-otp/` - Verify OTP code
- `POST /api/resend-otp/` - Resend OTP code

---

## Project Structure

```
uia-smarttour/
│
├── backend/                          # Flask backend
│   ├── main_web.py                   # Main Flask application
│   ├── config.json                   # API keys configuration
│   ├── Data_with_flavor.csv          # Restaurant database
│   ├── reviews.json                  # User reviews
│   ├── languages.json                # Translation files
│   ├── food_planner_v2.py            # Food plan generator
│   ├── chatbot_component_v2.py       # Chatbot component
│   ├── music_player_component.py     # Music player
│   ├── language_toggle_component.py  # Language switcher
│   ├── Dockerfile                    # Flask container config
│   └── requirements.txt              # Python dependencies
│
├── user_management/                  # Django backend
│   ├── manage.py                     # Django management
│   ├── settings.py                   # Django settings
│   ├── urls.py                       # URL routing
│   ├── models.py                     # Database models
│   ├── views.py                      # View functions
│   ├── templates/                    # HTML templates
│   ├── static/                       # Static files
│   ├── Dockerfile                    # Django container config
│   └── requirements.txt              # Python dependencies
│
├── frontend/                         # Frontend assets
│   ├── main_web.html                 # Main page
│   ├── Account.html                  # Account page
│   ├── style.css                     # Main stylesheet
│   ├── banner.css                    # Header styles
│   ├── button.css                    # Button styles
│   ├── minigame.css                  # Game styles
│   ├── script.js                     # Main JavaScript
│   ├── minigame.js                   # Game logic
│   └── Picture/                      # Images and assets
│
├── docker-compose.yml                # Docker orchestration
├── nginx.conf                        # Nginx configuration
└── README.md                         # This file
```

---

## Docker Commands Reference

### Basic Operations

```bash
# Start all services
docker-compose up

# Start in background (detached mode)
docker-compose up -d

# Stop all services
docker-compose down

# View running containers
docker ps

# View logs
docker-compose logs

# View logs for specific service
docker-compose logs flask-backend
docker-compose logs django-backend
docker-compose logs nginx
```

### Build & Rebuild

```bash
# Rebuild all containers (after code changes)
docker-compose down
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build flask-backend
```

### Troubleshooting Commands

```bash
# Remove all containers and volumes (CAUTION: Deletes data)
docker-compose down -v

# Access container shell
docker exec -it <container_name> /bin/bash
docker exec -it <container_name> /bin/sh

# View container resource usage
docker stats

# Clean up unused Docker resources
docker system prune -a
```

### Database Management (Django)

```bash
# Access Django container
docker exec -it <django_container_id> /bin/bash

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic
```

---

## Troubleshooting

### Common Issues and Solutions

#### 1. Port Already in Use

**Error:** `Port 80 is already in use`

**Solution:**
```bash
# Find process using port 80
sudo lsof -i :80

# Kill the process
sudo kill -9 <PID>

# Or change nginx port in docker-compose.yml
ports:
  - "8080:80"  # Use port 8080 instead
```

#### 2. Containers Not Starting

**Solution:**
```bash
# Check logs for errors
docker-compose logs

# Restart Docker service
sudo systemctl restart docker

# Rebuild containers
docker-compose down
docker-compose up -d --build
```

#### 3. Database Connection Error

**Solution:**
```bash
# Ensure Django migrations are run
docker exec -it <django_container> python manage.py migrate

# Check database file permissions
ls -l user_management/db.sqlite3
```

#### 4. API Key Not Working

**Solution:**
- Verify `backend/config.json` exists and contains valid Gemini API keys array
- Ensure CURRENT_KEY_INDEX is within valid range (0 to number of keys - 1)
- Check `user_management/.env` has correct email credentials for OTP
- Verify EMAIL_HOST_PASSWORD is an App Password (not regular Gmail password)
- Restart containers after updating keys:
  ```bash
  docker-compose restart
  ```

**To switch to a different API key:**
- Access the web application and use the API key switcher feature
- Or manually edit CURRENT_KEY_INDEX in `backend/config.json`

#### 5. SSE Notifications Not Working

**Solution:**
- Check browser console for SSE connection errors
- Verify nginx.conf SSE configuration is correct
- Ensure user is logged in (SSE only works for authenticated users)
- Check Django logs:
  ```bash
  docker-compose logs django-backend
  ```

#### 6. Hard Refresh Page (Clear Browser Cache)

**Windows/Linux:** `Ctrl + Shift + R`  
**Mac:** `Cmd + Shift + R`

#### 7. OTP Email Not Received

**Solution:**
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in `user_management/.env`
- Ensure you're using Gmail App Password (not regular password)
- Check spam/junk folder
- Verify 2FA is enabled on your Google account
- Test email settings:
  ```bash
  docker exec -it <django_container> python manage.py shell
  >>> from django.core.mail import send_mail
  >>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
  ```

#### 8. Rate Limit Exceeded for Gemini API

**Solution:**
- The system automatically switches between API keys
- Add more API keys to `backend/config.json` GEMINI_API_KEYS array
- Monitor usage at: https://makersuite.google.com/app/apikey
- Wait for rate limit to reset (usually 1 minute)

---

## Future Improvements

Based on the midterm report, planned enhancements include:

### Short-term (Week 7)
- Expand restaurant database to multiple cities
- Complete remaining UI screens and error notifications
- Fix timestamp display issues in reviews
- Improve data synchronization between services

### Mid-term (Week 8)
- Comprehensive testing and bug fixes
- Performance optimization
- Enhanced filtering algorithm accuracy
- UI/UX improvements based on user feedback

### Long-term (Week 9+)
- Multi-language support expansion
- Friend list and social interactions
- Show friends' favorite spots
- Mobile-responsive design improvements
- Advanced food plan suggestions with ML
- Integration with more restaurant data sources
- Real-time collaborative trip planning

---

## Known Limitations

As documented in the project report:

1. **API Access Limitation** - Limited request rate resulted in incomplete restaurant database (currently only one city)
2. **Database Incompleteness** - Some restaurants lack detailed information
3. **GPS Accuracy** - Occasional issues with location detection
4. **Manual Data Collection** - Time-consuming process limiting coverage
5. **Error Handling** - Some edge cases not yet covered with proper notifications

---

## Computational Thinking Principles Applied

This project demonstrates the following computational thinking concepts:

1. **Decomposition** - Breaking down the complex restaurant recommendation problem into manageable modules (User Interaction, Data Collection, Filtering, Display)

2. **Abstraction** - Creating simplified models of real-world entities (User, Restaurant, Review, Recommendation Engine)

3. **Pattern Recognition** - Identifying recurring user behavior patterns to improve recommendations

4. **Algorithmic Design** - Implementing the six-step filtering algorithm with clear logic flow and optimization

---

## Acknowledgments

- **VNUHCM - University of Science** - For providing the platform to develop this project
- **Instructors** - TS. Trương Phước Hưng, Teacher Đỗ Đức Hào, Teacher Trần Hoàng Quân for guidance
- **Geoapify** - For restaurant data API
- **Google** - For Gemini AI and OAuth services
- **OpenWeather** - For weather data integration
- **Open Source Community** - For the amazing libraries and tools used in this project

---

## License

This project is developed as an academic assignment for the Computational Thinking course at VNUHCM - University of Science.

---

## Contact

For questions or feedback, please contact:

**Email:** contact.uiafood@gmail.com

**Project Repository:** [\[GitHub Repository Link\]](https://github.com/mkbang2411-oss/TDTT---U-I-A.git)

**Demo Video:** [YouTube Demo Link]

---

**Last Updated:** 18 December 2025

**Version:** 1.0.0 (Final Release)
