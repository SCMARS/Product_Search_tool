import React, { useRef } from 'react';

const SearchInput = ({ query, setQuery, loading }) => {
  const fileInputRef = useRef(null);

  const triggerFileInput = () => {
    // Programmatically click the hidden file input
    fileInputRef.current.click();
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Here you can handle the file upload
      console.log('File uploaded:', file);
      // You might want to add additional functionality here
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
    </div>
  );
};

export default SearchInput;
