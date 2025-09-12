import React from 'react';
import { usePageContext } from '../../contexts/PageContext';

const LandingPage: React.FC = () => {
  const { setCurrentPage } = usePageContext();

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-purple-800 to-indigo-900">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center text-white mb-16">
          <h1 className="text-6xl font-bold mb-6 animate-float">
            Welcome to WeedGo
          </h1>
          <p className="text-2xl mb-8 opacity-90">
            Your Premium Cannabis Experience
          </p>
          <button
            onClick={() => setCurrentPage('chat')}
            className="px-8 py-4 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-bold rounded-full shadow-xl transform hover:scale-105 transition-all duration-200"
          >
            Start Shopping
          </button>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mt-16">
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 text-white text-center hover:bg-white/20 transition-all duration-300">
            <div className="text-5xl mb-4">🌿</div>
            <h3 className="text-xl font-bold mb-2">Premium Products</h3>
            <p className="opacity-80">Curated selection of top-quality cannabis products</p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 text-white text-center hover:bg-white/20 transition-all duration-300">
            <div className="text-5xl mb-4">🤖</div>
            <h3 className="text-xl font-bold mb-2">AI Assistant</h3>
            <p className="opacity-80">Get personalized recommendations from our smart AI</p>
          </div>
          
          <div className="bg-white/10 backdrop-blur-sm rounded-xl p-8 text-white text-center hover:bg-white/20 transition-all duration-300">
            <div className="text-5xl mb-4">🚀</div>
            <h3 className="text-xl font-bold mb-2">Fast Delivery</h3>
            <p className="opacity-80">Quick and discreet delivery to your door</p>
          </div>
        </div>

        {/* Call to Action */}
        <div className="text-center mt-16">
          <div className="bg-gradient-to-r from-purple-600/20 to-indigo-600/20 backdrop-blur-sm rounded-2xl p-12 border border-white/20">
            <h2 className="text-4xl font-bold text-white mb-6">
              Ready to explore?
            </h2>
            <p className="text-xl text-white/90 mb-8">
              Chat with our AI assistant to find the perfect products for you
            </p>
            <button
              onClick={() => setCurrentPage('chat')}
              className="px-10 py-4 bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white font-bold rounded-full shadow-xl transform hover:scale-105 transition-all duration-200 text-lg"
            >
              Launch Chat Assistant
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LandingPage;