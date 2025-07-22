import React from 'react';

const SearchInput = ({ query, setQuery, loading }) => {
  return (
    <div className="max-w-xl mx-auto">
      <div className="flex flex-col sm:flex-row gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter product name (e.g., iPhone 13)"
          className="flex-grow px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={loading}
        />
      </div>
      <p className="mt-2 text-sm text-gray-500 text-center">
        Search across Allegro, Amazon, and Aliexpress
      </p>
    </div>
  );
};

export default SearchInput;
