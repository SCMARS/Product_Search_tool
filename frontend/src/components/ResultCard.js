import React, { useState } from 'react';

const ResultCard = ({ product }) => {
  const [copySuccess, setCopySuccess] = useState(false);

  const copyDescription = () => {
    const description = `${product.name}\nPrice: ${product.price}\nLink: ${product.url}`;
    navigator.clipboard.writeText(description)
      .then(() => {
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 2000);
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
      });
  };

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden mb-4 hover:shadow-lg transition-shadow duration-300">
      <div className="p-4">
        <div className="flex items-center mb-3">
          {product.image ? (
            <img 
              src={product.image} 
              alt={product.name} 
              className="w-20 h-20 object-contain mr-3"
              onError={(e) => {
                e.target.onerror = null;
                e.target.src = 'https://via.placeholder.com/80?text=No+Image';
              }}
            />
          ) : (
            <div className="w-20 h-20 bg-gray-200 flex items-center justify-center mr-3 text-xs text-gray-500">
              No Image
            </div>
          )}

          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-medium text-gray-900 truncate mb-1">
              {product.name}
            </h4>
            <p className="text-lg font-bold text-blue-600">
              {product.price}
            </p>
          </div>
        </div>

        <div className="flex flex-col space-y-2">
          <a 
            href={product.url} 
            target="_blank" 
            rel="noopener noreferrer"
            className="block w-full text-center bg-blue-50 hover:bg-blue-100 text-blue-700 font-medium py-2 px-4 rounded transition-colors duration-200"
          >
            View Product
          </a>

          <button 
            onClick={copyDescription}
            className={`w-full text-center py-2 px-4 rounded transition-colors duration-200 ${
              copySuccess 
                ? 'bg-green-100 text-green-700' 
                : 'bg-gray-50 hover:bg-gray-100 text-gray-700'
            }`}
          >
            {copySuccess ? 'Copied!' : 'Copy Description'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ResultCard;
