import React, { useState, useRef } from 'react';
import axios from 'axios';

const ResultCard = ({ product }) => {
  const [copySuccess, setCopySuccess] = useState(false);
  const [showDescription, setShowDescription] = useState(false);
  const [generatedImage, setGeneratedImage] = useState(null);
  const [generatingImage, setGeneratingImage] = useState(false);
  const [imageError, setImageError] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const fileInputRef = useRef(null);

  const copyDescription = () => {
    // Use the dedicated description field if available, otherwise create one from name, price, and URL
    const description = product.description 
      ? product.description 
      : `${product.name}\nPrice: ${product.price}\nLink: ${product.url}`;

    navigator.clipboard.writeText(description)
      .then(() => {
        setCopySuccess(true);
        setTimeout(() => setCopySuccess(false), 2000);
      })
      .catch(err => {
        console.error('Failed to copy text: ', err);
      });
  };

  const generateAIImage = async () => {
    // Reset states
    setGeneratingImage(true);
    setImageError(null);

    // Get description for image generation
    const description = product.description 
      ? product.description 
      : `${product.name}, ${product.price}`;

    try {
      const response = await axios.post('http://127.0.0.1:5001/api/generate-image', {
        description: description
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      setGeneratedImage(response.data.image_url);
    } catch (err) {
      console.error('Error generating AI image:', err);
      if (err.response && err.response.data && err.response.data.error) {
        setImageError(err.response.data.error);
      } else {
        setImageError('Failed to generate image. Please try again later.');
      }
    } finally {
      setGeneratingImage(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Reset any previous errors
      setImageError(null);

      // Create a URL for the uploaded image
      const imageUrl = URL.createObjectURL(file);
      setUploadedImage(imageUrl);
    }
  };

  const triggerFileInput = () => {
    // Programmatically click the hidden file input
    fileInputRef.current.click();
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

        {product.description && (
          <div className="mb-3">
            <button 
              onClick={() => setShowDescription(!showDescription)}
              className="text-sm text-blue-600 hover:text-blue-800 mb-1 flex items-center"
            >
              {showDescription ? 'Hide Description' : 'Show Description'}
              <svg 
                className={`ml-1 w-4 h-4 transition-transform ${showDescription ? 'transform rotate-180' : ''}`} 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24" 
                xmlns="http://www.w3.org/2000/svg"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"></path>
              </svg>
            </button>

            {showDescription && (
              <div className="text-sm text-gray-700 bg-gray-50 p-2 rounded border border-gray-200 mt-1 max-h-40 overflow-y-auto">
                {product.description}
              </div>
            )}
          </div>
        )}

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

          <div className="flex space-x-2">
            <button 
              onClick={generateAIImage}
              disabled={generatingImage}
              className={`flex-1 text-center py-2 px-4 rounded transition-colors duration-200 ${
                generatingImage 
                  ? 'bg-blue-100 text-blue-700 cursor-not-allowed' 
                  : 'bg-purple-50 hover:bg-purple-100 text-purple-700'
              }`}
            >
              {generatingImage ? 'Generating...' : 'Generate AI Image'}
            </button>

            <button 
              onClick={triggerFileInput}
              className="flex items-center justify-center bg-green-50 hover:bg-green-100 text-green-700 rounded p-2 transition-colors duration-200"
              title="Upload Photo"
            >
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-6 w-6" 
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

          {/* Display error message if there is one */}
          {imageError && (
            <div className="mt-2 p-2 bg-red-100 text-red-700 rounded text-sm">
              {imageError}
            </div>
          )}

          {/* Display generated image if available */}
          {generatedImage && !imageError && (
            <div className="mt-3">
              <p className="text-sm font-medium text-gray-700 mb-2">AI Generated Image:</p>
              <img 
                src={generatedImage} 
                alt="AI Generated" 
                className="w-full h-auto rounded border border-gray-200"
                onError={() => setImageError('Failed to load generated image.')}
              />
            </div>
          )}

          {/* Display uploaded image if available */}
          {uploadedImage && (
            <div className="mt-3">
              <p className="text-sm font-medium text-gray-700 mb-2">Uploaded Image:</p>
              <img 
                src={uploadedImage} 
                alt="Uploaded" 
                className="w-full h-auto rounded border border-gray-200"
                onError={() => setImageError('Failed to load uploaded image.')}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ResultCard;
