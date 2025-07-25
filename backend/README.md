# Product Search Tool Backend

This is the backend for the Product Search Tool. It provides APIs for searching products on various e-commerce platforms.

## Installation

1. Make sure you have Python 3.8+ installed
2. Install the required dependencies:

```bash
cd backend
pip install -r requirements.txt
```

**Note:** The application requires pandas for CSV processing. If you encounter a "No module named 'pandas'" error, make sure to install the dependencies as described above.

## APIs

### `/api/search` (POST)

Search for products on Amazon, Allegro, and AliExpress.

**Request:**
```json
{
  "query": "product name"
}
```

**Response:**
```json
{
  "allegro": [...],
  "amazon": [...],
  "aliexpress": [...]
}
```

### `/api/upload-csv` (POST)

Upload a CSV file with product names for batch processing. The results will be saved to `results.json` in the project root.

**Request:**
- Form data with a `file` field containing a CSV file
- The CSV file must have a column named either `product` or `product_name`

**Response:**
```json
{
  "success": true,
  "message": "Processing X products in the background",
  "products_count": X
}
```

**Error Responses:**
- 400 Bad Request: If the file is missing, empty, not a CSV, or doesn't have either a `product` or `product_name` column
- 500 Internal Server Error: If there's an error processing the file

### `/api/csv-results` (GET)

Retrieve the results of CSV processing from the `results.json` file.

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "product": "iphone 13",
      "amazon": { "name": "...", "price": "...", "url": "..." },
      "allegro": { "name": "...", "price": "...", "url": "..." },
      "aliexpress": { "name": "...", "price": "...", "url": "..." }
    },
    ...
  ]
}
```

**Error Responses:**
- 404 Not Found: If the results.json file doesn't exist
- 500 Internal Server Error: If there's an error reading the file

## CSV Processing

When a CSV file is uploaded, the backend:
1. Validates the file (must be a CSV with either a `product` or `product_name` column)
2. Starts a background thread to process the file
3. For each product in the CSV:
   - Searches on Amazon, Allegro, and AliExpress
   - Adds the results to a list
   - Waits 0.5 seconds between products to avoid rate limiting
4. Saves the results to `results.json` in the project root

## Results Format

The `results.json` file will have the following format:

```json
[
  {
    "product": "iphone 13",
    "amazon": { "name": "...", "price": "...", "url": "..." },
    "allegro": { "name": "...", "price": "...", "url": "..." },
    "aliexpress": { "name": "...", "price": "...", "url": "..." }
  },
  {
    "product": "macbook air",
    "error": "Timeout while fetching amazon"
  },
  ...
]
```

## Testing

You can test the CSV upload functionality using the provided test script:

```bash
python test_csv_upload.py
```

This script will:
1. Create a test CSV file with sample product names
2. Upload it to the `/api/upload-csv` endpoint
3. Wait for the processing to complete
4. Check if the `results.json` file is created
