# Quick Start Guide

This guide provides concise instructions for running the Product Search Tool application.

## Option 1: Using the Automated Script

The easiest way to run the application is to use the provided shell script:

```
./run.sh
```

This script will automatically set up and start both the backend and frontend servers.

## Option 2: Manual Setup

## Running the Backend

1. Open a terminal and navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies and Playwright browsers:
   ```
   pip install -r requirements.txt
   playwright install
   ```

4. Edit the `.env` file to add your Allegro API credentials (if you want to use Allegro search).

5. Start the Flask server:
   ```
   flask run
   ```
   The backend will be available at http://localhost:5000

## Running the Frontend

1. Open a new terminal window and navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the development server:
   ```
   npm start
   ```
   The frontend will be available at http://localhost:3000

## Using the Application

1. Open your browser and go to http://localhost:3000
2. Enter a product name in the search field (e.g., "iPhone 13")
3. Click the "Search" button
4. View the results from Allegro, Amazon, and Aliexpress
5. Click "Copy Description" to copy the product details to your clipboard for easy sharing

For more detailed information, please refer to the README.md file.
