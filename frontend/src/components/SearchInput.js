import React, { useRef, useState } from 'react';
import axios from 'axios';

const SearchInput = ({ query, setQuery, loading }) => {
  const fileInputRef = useRef(null);
  const [imageLoading, setImageLoading] = useState(false);
  const [imageError, setImageError] = useState(null);

  const triggerFileInput = () => {
    // Programmatically click the hidden file input
    fileInputRef.current.click();
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (file) {
      console.log('File uploaded:', file);

      setImageLoading(true);
      setImageError(null);

      // Create FormData object to send the file
      const formData = new FormData();
      formData.append('image', file);

      try {
        // Send the image to the backend for analysis
        const response = await axios.post('http://127.0.0.1:5001/api/analyze-image', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        if (response.data.success) {
          // Set the query to the analysis result
          setQuery(response.data.analysis);
        } else {
          setImageError(response.data.error || 'Failed to analyze image');
        }
      } catch (error) {
        console.error('Error analyzing image:', error);

        // Extract the error message from the response if available
        let errorMessage = 'Error analyzing image. Please try again.';

        if (error.response && error.response.data) {
          errorMessage = error.response.data.error || errorMessage;
        }

        // Handle specific HTTP status codes
        if (error.response) {
          switch (error.response.status) {
            case 400:
              // Bad request - likely an issue with the image
              console.log('Bad request error:', error.response.data);
              break;
            case 429:
              // Rate limit exceeded
              errorMessage = 'Rate limit exceeded. Please try again later.';
              break;
            case 504:
              // Gateway timeout
              errorMessage = 'The request timed out. Please try again later.';
              break;
            default:
              // Other errors
              console.log(`Server error (${error.response.status}):`, error.response.data);
          }
        }

        setImageError(errorMessage);
      } finally {
        setImageLoading(false);
      }
    }
  };

  return (
    <div className="max-w-xl mx-auto">
      <div className="flex flex-col sm:flex-row gap-2 relative">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter product name (e.g., iPhone 13)"
          className="flex-grow px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
        <button 
          onClick={triggerFileInput}
          className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center justify-center bg-green-50 hover:bg-green-100 text-green-700 rounded p-2 transition-colors duration-200"
          title="Upload Photo"
        >
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-5 w-5" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" 
            />
          </svg>
        </button>
        {/* Hidden file input */}
        <input 
          type="file" 
          ref={fileInputRef} 
          onChange={handleFileUpload} 
          accept="image/*" 
          className="hidden" 
        />
      </div>
      <p className="mt-2 text-sm text-gray-500 text-center">
        Search across Allegro, Amazon, and Aliexpress
      </p>

      {imageLoading && (
        <div className="mt-2 flex justify-center">
          <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-green-500"></div>
          <span className="ml-2 text-sm text-green-600">Analyzing image...</span>
        </div>
      )}

      {imageError && (
        <div className="mt-2 p-2 bg-red-100 text-red-700 rounded-md text-sm text-center">
          {imageError}
        </div>
      )}
    </div>
  );
};

export default SearchInput;
