# Nutrition Tracker Web App

A simple Flask + MySQL web app for user login, profile management, food search, meal logging, and nutrition summaries.

## Features

- User signup, login, and logout
- Profile page with BMI, BMR, and TDEE calculation
- Food search and food nutrition details
- Daily meal record (add, view, delete)
- Daily and weekly nutrition suggestion data

## Tech Stack

- Python 3
- Flask
- MySQL
- HTML templates (Jinja)

## Project Structure

- `main.py` - Flask backend and routes
- `templates/` - Frontend HTML pages

## Requirements

Install dependencies:

```bash
pip install flask mysql-connector-python
```

Set up MySQL:

- Create a database named `fp`
- Update `db_config` in `main.py` if needed (`host`, `user`, `password`, `database`)
- Prepare required tables, such as `customers`, `foods`, and `meals`

## Run

```bash
python main.py
```

Then open:

- `http://127.0.0.1:5000`

## Main Routes

- `/` - Redirect based on login state
- `/database` - Login page
- `/signup` - Signup page
- `/homepage` - Home page after login
- `/profile` - Profile page
- `/search_food_view` - Food search page
- `/diet_view` - Diet record page
- `/daily_summary_view` - Daily summary page

## Note

- This project currently runs with `debug=True`.
- Replace `app.secret_key` with a secure value before production.
