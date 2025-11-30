# Daily Integral Challenge

## Overview

This is a web-based calculus quiz application built with Flask (Python backend) and vanilla HTML/CSS/JavaScript (frontend). The application generates daily integral problems for users to solve across three difficulty levels, with a persistent leaderboard tracking high scores. All users see the same questions on a given day (deterministic seeding), and each user gets one attempt per difficulty per day.

## Recent Changes

- **November 30, 2025**: Implemented secure expression parsing with whitelist validation to prevent code injection
- **November 30, 2025**: Fixed UI button reset on new day to properly clear "Done/Tried" badges
- **November 30, 2025**: Converted to Daily Integral Challenge with SymPy-generated calculus problems
- **November 30, 2025**: Added MathJax for rendering integral notation
- **November 30, 2025**: Implemented daily question system with deterministic seeding
- **November 30, 2025**: Added username uniqueness validation with red warning message for duplicate usernames
- **November 30, 2025**: Added difficulty levels (Easy=1pt, Medium=5pts, Hard=10pts) with persistent username storage via localStorage
- **November 30, 2025**: Added leaderboard feature with username tracking and persistent score storage

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Technology**: Vanilla HTML, CSS, and JavaScript (client-side)
- **Math Rendering**: MathJax 3.x for LaTeX-style integral notation
- **Structure**: Single-page application served as a static `index.html` file
- **UI Components**: 
  - Difficulty selection buttons with status badges (Done/Tried)
  - Question display area with MathJax-rendered integrals
  - Answer input field (supports mathematical expressions)
  - Results feedback section with correct answer display
  - Leaderboard table
- **Design Pattern**: Simple DOM manipulation for interactive quiz functionality
- **Rationale**: Minimalist approach chosen for simplicity and zero build dependencies

### Backend Architecture
- **Framework**: Flask (Python microframework)
- **Math Library**: SymPy for integral generation, symbolic computation, and answer validation
- **Structure**: Single-file application (`app.py`) with RESTful API endpoints
- **Endpoints**:
  - `GET /` - Serves the main HTML page
  - `GET /api/daily-questions` - Returns today's questions (LaTeX format, no answers)
  - `GET /api/user-attempts/<username>` - Gets user's attempts for today
  - `POST /api/check-answer` - Validates user's answer and updates scores
  - `GET /api/leaderboard` - Retrieves top 10 scores
  - `POST /api/check-username` - Validates username uniqueness (case-insensitive)
- **Question Generation**:
  - Easy: Definite integrals with integer bounds (1 point)
  - Medium: Trigonometric/exponential integrals (5 points)
  - Hard: Integration by parts, u-substitution, trig products (10 points)
- **Answer Validation**:
  - Numeric: Float comparison with 0.01 tolerance for definite integrals
  - Symbolic: Derivative verification for indefinite integrals (uses safe parsing)
- **Security**: Safe expression parsing with whitelist validation prevents code injection

### Data Storage
- **Solution**: File-based JSON storage
- **Files**:
  - `leaderboard.json` - User scores (cumulative)
  - `daily_questions.json` - Today's cached questions with answers
  - `user_attempts.json` - Tracks which users attempted which difficulties today
- **Daily Reset**: Questions and attempts reset each day based on server date

### Security Measures
- **Safe Expression Parsing**: User input is validated against an allowed character pattern and blocked dangerous keywords before SymPy parsing
- **Whitelisted Functions**: Only mathematical functions (sin, cos, tan, exp, ln, log, sqrt, pi, e, x) are allowed
- **No Direct Code Execution**: Uses local_dict and evaluate=False to prevent arbitrary code execution

### Authentication and Authorization
- **Current Implementation**: No authentication system
- **Username Handling**: Simple username input with case-insensitive matching, stored in localStorage
- **Rationale**: Casual quiz application doesn't require user accounts

## External Dependencies

### Backend Dependencies
- **Flask**: Python web microframework for HTTP server and routing
- **SymPy**: Symbolic mathematics library for integral generation and validation
- **Python Standard Library**: 
  - `json` - JSON serialization/deserialization
  - `os` - File system operations
  - `random` - Seeded random for deterministic question generation
  - `datetime` - Date handling for daily questions
  - `hashlib` - Hash generation for seeding
  - `re` - Regular expressions for input validation

### Frontend Dependencies
- **MathJax 3.x**: LaTeX rendering for mathematical notation (loaded from CDN)

### Third-Party Services
- **None**: Application runs entirely self-contained with no external API calls

### Runtime Environment
- **Python**: Requires Python 3.x runtime
- **Web Server**: Flask development server (production deployments should use WSGI server like Gunicorn)
