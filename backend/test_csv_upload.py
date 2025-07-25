import requests
import pandas as pd
import os
import time

def create_test_csv(filename="test_products.csv", num_products=5):

    products = [
        "iPhone 13",
        "MacBook Air",
        "Samsung Galaxy S21",
        "Sony WH-1000XM4",
        "Nintendo Switch",
        "iPad Pro",
        "Logitech MX Master 3",
        "Amazon Echo Dot",
        "Dyson V11",
        "Bose QuietComfort 35"
        "Mac mini M4 PRO"
    ]


    products = products[:num_products]


    df = pd.DataFrame({"product_name": products})
    df.to_csv(filename, index=False)
    print(f"Created test CSV file '{filename}' with {num_products} products")
    return filename

def test_csv_upload(file_path="test_products.csv", url="http://127.0.0.1:5001/api/upload-csv"):
    """Test the CSV upload endpoint"""
    if not os.path.exists(file_path):
        print(f"File {file_path} does not exist. Creating it...")
        file_path = create_test_csv(file_path)

    print(f"Uploading file {file_path} to {url}...")

    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'text/csv')}
        response = requests.post(url, files=files)

    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.json()}")

    if response.status_code == 200:
        print("Upload successful! Waiting for processing to complete...")
        # Wait a bit for processing to start
        time.sleep(5)

        # Check if results.json exists
        results_path = "results.json"
        max_wait = 60  # Maximum wait time in seconds
        wait_time = 0

        while not os.path.exists(results_path) and wait_time < max_wait:
            print(f"Waiting for results... ({wait_time}s)")
            time.sleep(5)
            wait_time += 5

        if os.path.exists(results_path):
            print(f"Results file found at {results_path}")
            # You could add code here to read and display the results
        else:
            print(f"Results file not found after waiting {max_wait} seconds.")
            print("Processing might still be ongoing in the background.")

    return response.status_code == 200

if __name__ == "__main__":
    # Create a small test CSV file and upload it
    success = test_csv_upload(file_path="test_products.csv", )
    print("Test completed successfully" if success else "Test failed")
