import React, { useState, useEffect } from 'react';
import axios from 'axios';
import SearchInput from './components/SearchInput';
import ResultCard from './components/ResultCard';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Автоматический поиск с задержкой (debounce)
  useEffect(() => {
    const delayedSearch = setTimeout(() => {
      if (query.trim().length > 4) { // Поиск только если больше 2 символов
        performSearch();
      } else {
        setResults(null); // Очистить результаты если запрос короткий
      }
    }, 500); // Задержка 500ms

    return () => clearTimeout(delayedSearch); // Очистка таймера
  }, [query]); // Запускается при изменении query

  const performSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
   //api/search
      const response = await axios.post('http://127.0.0.1:5001/api/search', {
        query: query.trim()
      }, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 0
      });

      setResults(response.data);
    } catch (err) {
      console.error('Error searching products:', err);
      if (err.code === 'ECONNREFUSED') {
        setError('Cannot connect to server. Make sure Flask server is running on port 5001.');
      } else if (err.code === 'ERR_NETWORK') {
        setError('Network error. Check CORS configuration on server.');
      } else {
        setError('Failed to search products. Please try again later.');
      }
    } finally {
      setLoading(false);
    }
  };


  return (
      <div className="min-h-screen bg-gray-100">
        <div className="container mx-auto px-4 py-8">
          <h1 className="text-3xl font-bold text-center mb-8 text-blue-600">
            Product Search Tool
          </h1>

          <SearchInput
              query={query}
              setQuery={setQuery}
              loading={loading}
          />

          <div className="mt-2 text-sm text-gray-500 text-center">
            {query.length > 2 ? 'Searching automatically...' : 'Type at least 3 characters to search'}
          </div>

          {error && (
              <div className="mt-4 p-4 bg-red-100 text-red-700 rounded-md">
                {error}
              </div>
          )}

          {loading && (
              <div className="mt-8 flex justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
              </div>
          )}

          {results && !loading && (
              <div className="mt-8">
                <h2 className="text-2xl font-semibold mb-4">Search Results for "{query}"</h2>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <h3 className="text-xl font-medium mb-3 text-blue-500">Allegro</h3>
                    {results.allegro && results.allegro.length > 0 ? (
                        results.allegro.map((product, index) => (
                            <ResultCard key={`allegro-${index}`} product={product} />
                        ))
                    ) : (
                        <p className="text-gray-500">No products found on Allegro</p>
                    )}
                  </div>

                  <div>
                    <h3 className="text-xl font-medium mb-3 text-blue-500">Amazon</h3>
                    {results.amazon && results.amazon.length > 0 ? (
                        results.amazon.map((product, index) => (
                            <ResultCard key={`amazon-${index}`} product={product} />
                        ))
                    ) : (
                        <p className="text-gray-500">No products found on Amazon</p>
                    )}
                  </div>

                  <div>
                    <h3 className="text-xl font-medium mb-3 text-blue-500">Aliexpress</h3>
                    {results.aliexpress && results.aliexpress.length > 0 ? (
                        results.aliexpress.map((product, index) => (
                            <ResultCard key={`aliexpress-${index}`} product={product} />
                        ))
                    ) : (
                        <p className="text-gray-500">No products found on Aliexpress</p>
                    )}
                  </div>
                </div>
              </div>
          )}
        </div>
      </div>
  );
}

export default App;
