# Product Search Tool

A full-stack web application that allows users to search for products across multiple e-commerce platforms (Allegro, Amazon, and Aliexpress) simultaneously.

## Features

- Search for products by name across three platforms
- View top 3 results from each platform
- See product details including name, price, image, and link
- Copy product description with a single click
- Clean and responsive UI built with React and Tailwind CSS
- Backend API powered by Flask

## Project Structure

```
project/
├── frontend/           # React application with Tailwind CSS
│   ├── public/         # Static files
│   └── src/            # React source code
│       ├── components/ # React components
│       └── App.js      # Main application component
├── backend/            # Flask API
│   ├── app.py          # Main Flask application
│   ├── allegro.py      # Allegro API integration
│   ├── amazon.py       # Amazon web scraping
│   ├── aliexpress.py   # Aliexpress web scraping
│   └── requirements.txt # Python dependencies
└── README.md           # This file
```

## Setup and Installation

### Option 1: Using the Automated Script

The easiest way to run the application is to use the provided shell script:

```
./run.sh
```

This script will automatically:
- Set up the Python virtual environment
- Install backend dependencies
- Install Playwright browsers
- Start the Flask server
- Install frontend dependencies
- Start the React development server

### Option 2: Manual Setup

#### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```
   playwright install
   ```

5. Create a `.env` file based on `.env.example` and add your Allegro API credentials:
   ```
   ALLEGRO_CLIENT_ID=your_client_id_here
   ALLEGRO_CLIENT_SECRET=your_client_secret_here
   ```

6. Start the Flask server:
   ```
   flask run
   ```
   The API will be available at http://localhost:5001

### Frontend Setup

1. Navigate to the frontend directory:
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
   The application will be available at http://localhost:3000

## Usage

1. Enter a product name in the search field (e.g., "iPhone 13")
2. Click the "Search" button
3. Wait for the results to load from all three platforms
4. Browse the results and click "View Product" to visit the product page on the original marketplace
5. Click "Copy Description" to copy the product details to your clipboard for easy sharing

## Technical Details

### Frontend
- React 18
- Tailwind CSS for styling
- Axios for API requests

### Backend
- Flask with Flask-CORS
- Allegro API integration using requests
- Web scraping for Amazon and Aliexpress using Playwright
- Concurrent searches using ThreadPoolExecutor

## Notes

- Web scraping is dependent on the structure of the target websites and may break if they change their layout
- The Allegro API requires registration and credentials
- For production use, consider implementing caching and rate limiting

## Future Improvements

- Add pagination for more results
- Implement sorting and filtering options
- Add price comparison features
- Support for more e-commerce platforms
- CSV upload for bulk queries
