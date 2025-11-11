import React from 'react';

const SplashScreen: React.FC = () => {
  return (
    <div className="flex flex-col items-center justify-center h-full text-center p-8 bg-black">
      <style>{`
        @keyframes open-eye {
          0% {
            stroke-dasharray: 0 100;
            opacity: 0;
          }
          30% {
            stroke-dasharray: 50 50;
            opacity: 1;
          }
          60%, 100% {
            stroke-dasharray: 100 0;
            opacity: 1;
          }
        }
        @keyframes fade-in {
          0%, 50% {
            opacity: 0;
            transform: translateY(10px);
          }
          100% {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-open-eye {
          animation: open-eye 2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        .animate-fade-in-logo {
          animation: fade-in 2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `}</style>
      
      <div className="relative flex flex-col items-center">
        <svg
          width="120"
          height="120"
          viewBox="0 0 100 100"
          className="mb-4"
        >
          <path
            d="M10 50 C 30 20, 70 20, 90 50"
            stroke="rgb(34 211 238)"
            strokeWidth="4"
            fill="transparent"
            strokeLinecap="round"
            className="animate-open-eye"
            style={{ strokeDasharray: '100 0' }}
          />
          <path
            d="M10 50 C 30 80, 70 80, 90 50"
            stroke="rgb(34 211 238)"
            strokeWidth="4"
            fill="transparent"
            strokeLinecap="round"
            className="animate-open-eye"
            style={{ strokeDasharray: '100 0', animationDelay: '0.1s' }}
          />
          <circle
            cx="50"
            cy="50"
            r="12"
            fill="rgb(34 211 238)"
            className="animate-fade-in-logo"
            style={{ opacity: 0 }}
          />
        </svg>

        <h1
          className="text-4xl font-bold text-white animate-fade-in-logo"
          style={{ opacity: 0 }}
        >
          SnapEyes
        </h1>
      </div>
    </div>
  );
};

export default SplashScreen;