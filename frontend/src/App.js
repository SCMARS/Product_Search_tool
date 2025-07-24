import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import SearchInput from './components/SearchInput';
import ResultCard from './components/ResultCard';

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // CSV upload states
  const [csvUploading, setCsvUploading] = useState(false);
  const [csvUploadSuccess, setCsvUploadSuccess] = useState(false);
  const [csvUploadError, setCsvUploadError] = useState(null);
  const [csvProductsCount, setCsvProductsCount] = useState(0);
  const fileInputRef = useRef(null);

  // CSV results states
  const [csvResults, setCsvResults] = useState(null);
  const [csvResultsLoading, setCsvResultsLoading] = useState(false);
  const [csvResultsError, setCsvResultsError] = useState(null);

  // Force re-render function
  const [, updateState] = useState();
  const forceUpdate = useCallback(() => updateState({}), []);

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

  const fetchCsvResults = async () => {
    // Reset states
    setCsvResultsLoading(true);
    setCsvResultsError(null);
    setCsvResults(null);

    try {
      const response = await axios.get('http://127.0.0.1:5001/api/csv-results', {
        timeout: 10000 // 10 seconds timeout
      });

      if (response.data.success) {
        setCsvResults(response.data.results);
        console.log('CSV results fetched successfully:', response.data.results);
      } else {
        setCsvResultsError(response.data.message || 'Failed to fetch CSV results');
      }
    } catch (err) {
      console.error('Error fetching CSV results:', err);
      if (err.response && err.response.status === 404) {
        setCsvResultsError('No results available. Please upload a CSV file first.');
      } else if (err.code === 'ECONNREFUSED') {
        setCsvResultsError('Cannot connect to server. Make sure Flask server is running on port 5001.');
      } else {
        setCsvResultsError('Failed to fetch CSV results. Please try again later.');
      }
    } finally {
      setCsvResultsLoading(false);
    }
  };

  const handleCsvUpload = async () => {
    // Reset states
    setCsvUploading(true);
    setCsvUploadSuccess(false);
    setCsvUploadError(null);
    // Reset CSV results states
    setCsvResults(null);
    setCsvResultsError(null);

    const fileInput = fileInputRef.current;
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      setCsvUploadError('Please select a CSV file');
      setCsvUploading(false);
      return;
    }

    const file = fileInput.files[0];

    // Check if file is a CSV
    if (!file.name.toLowerCase().endsWith('.csv')) {
      setCsvUploadError('File must be a CSV');
      setCsvUploading(false);
      return;
    }

    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://127.0.0.1:5001/api/upload-csv', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 30000 // 30 seconds timeout
      });

      setCsvUploadSuccess(true);
      setCsvProductsCount(response.data.products_count || 0);
      console.log('CSV upload successful:', response.data);
    } catch (err) {
      console.error('Error uploading CSV:', err);
      if (err.response && err.response.data && err.response.data.error) {
        setCsvUploadError(err.response.data.error);
      } else if (err.code === 'ECONNREFUSED') {
        setCsvUploadError('Cannot connect to server. Make sure Flask server is running on port 5001.');
      } else {
        setCsvUploadError('Failed to upload CSV. Please try again later.');
      }
    } finally {
      setCsvUploading(false);
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
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

          {/* CSV Upload Section */}
          <div className="mt-8 p-4 bg-white rounded-lg shadow-md">
            <h2 className="text-xl font-semibold mb-3">Upload CSV File</h2>
            <p className="text-sm text-gray-600 mb-4">
              Upload a CSV file with a 'product' column to search for multiple products at once.
              Results will be saved to results.json on the server.
            </p>

            <div className="flex flex-col md:flex-row md:items-center md:space-x-4">
              <div className="relative flex items-center mb-3 md:mb-0 flex-grow">
                <label 
                  htmlFor="csv-file-input" 
                  className="flex items-center px-4 py-2 bg-blue-50 text-blue-700 rounded-l-md font-semibold text-sm cursor-pointer hover:bg-blue-100"
                >
                  Choose File
                </label>
                <span className="flex-grow px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm rounded-r-md">
                  {fileInputRef.current && fileInputRef.current.files && fileInputRef.current.files[0] 
                    ? fileInputRef.current.files[0].name 
                    : "No file selected"}
                </span>
                <input
                  id="csv-file-input"
                  type="file"
                  ref={fileInputRef}
                  accept=".csv"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  onChange={() => {
                    // Force re-render to update the displayed filename
                    setCsvUploadError(null);
                    setCsvUploadSuccess(false);
                    forceUpdate();
                  }}
                />
              </div>
              <button
                onClick={handleCsvUpload}
                disabled={csvUploading}
                className="py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700 
                  focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50
                  disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {csvUploading ? 'Uploading...' : 'Upload CSV'}
              </button>
            </div>

            {csvUploadError && (
              <div className="mt-3 p-3 bg-red-100 text-red-700 rounded-md text-sm">
                {csvUploadError}
              </div>
            )}

            {csvUploadSuccess && (
              <div className="mt-3 p-3 bg-green-100 text-green-700 rounded-md text-sm">
                Successfully uploaded CSV with {csvProductsCount} products. 
                Processing in background. Results will be saved to results.json on the server.
                <div className="mt-2">
                  <button
                    onClick={fetchCsvResults}
                    disabled={csvResultsLoading}
                    className="py-1 px-3 bg-green-600 text-white rounded-md hover:bg-green-700 
                      focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-opacity-50
                      disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                  >
                    {csvResultsLoading ? 'Loading Results...' : 'View Results'}
                  </button>
                </div>
              </div>
            )}

            {csvResultsError && (
              <div className="mt-3 p-3 bg-yellow-100 text-yellow-700 rounded-md text-sm">
                {csvResultsError}
              </div>
            )}
          </div>

          {/* CSV Results Section */}
          {csvResults && csvResults.length > 0 && (
            <div className="mt-8 p-4 bg-white rounded-lg shadow-md">
              <h2 className="text-xl font-semibold mb-3">CSV Processing Results</h2>
              <p className="text-sm text-gray-600 mb-4">
                Results from processing your CSV file with {csvResults.length} products.
              </p>

              <div className="overflow-x-auto">
                <table className="min-w-full bg-white border border-gray-200">
                  <thead>
                    <tr>
                      <th className="py-2 px-4 border-b border-gray-200 bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Product
                      </th>
                      <th className="py-2 px-4 border-b border-gray-200 bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Amazon
                      </th>
                      <th className="py-2 px-4 border-b border-gray-200 bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        Allegro
                      </th>
                      <th className="py-2 px-4 border-b border-gray-200 bg-gray-50 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
                        AliExpress
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {csvResults.map((result, index) => (
                      <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : 'bg-white'}>
                        <td className="py-2 px-4 border-b border-gray-200 text-sm">
                          {result.product}
                        </td>
                        <td className="py-2 px-4 border-b border-gray-200 text-sm">
                          {result.amazon ? (
                            <div>
                              <div>{result.amazon.name}</div>
                              <div className="text-green-600 font-semibold">{result.amazon.price}</div>
                              <a href={result.amazon.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                                View on Amazon
                              </a>
                            </div>
                          ) : result.error && result.error.includes('amazon') ? (
                            <div className="text-red-500">{result.error}</div>
                          ) : (
                            <div className="text-gray-400">No results</div>
                          )}
                        </td>
                        <td className="py-2 px-4 border-b border-gray-200 text-sm">
                          {result.allegro ? (
                            <div>
                              <div>{result.allegro.name}</div>
                              <div className="text-green-600 font-semibold">{result.allegro.price}</div>
                              <a href={result.allegro.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                                View on Allegro
                              </a>
                            </div>
                          ) : result.error && result.error.includes('allegro') ? (
                            <div className="text-red-500">{result.error}</div>
                          ) : (
                            <div className="text-gray-400">No results</div>
                          )}
                        </td>
                        <td className="py-2 px-4 border-b border-gray-200 text-sm">
                          {result.aliexpress ? (
                            <div>
                              <div>{result.aliexpress.name}</div>
                              <div className="text-green-600 font-semibold">{result.aliexpress.price}</div>
                              <a href={result.aliexpress.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">
                                View on AliExpress
                              </a>
                            </div>
                          ) : result.error && result.error.includes('aliexpress') ? (
                            <div className="text-red-500">{result.error}</div>
                          ) : (
                            <div className="text-gray-400">No results</div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {csvResultsLoading && (
            <div className="mt-8 flex justify-center">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-green-500"></div>
            </div>
          )}

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
