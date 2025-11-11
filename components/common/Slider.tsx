
import React, { useState, useRef, useEffect, useCallback } from 'react';

export const ComparisonSlider: React.FC<{ before: string; after: string; animate?: boolean }> = ({ before, after, animate = false }) => {
    const [sliderPosition, setSliderPosition] = useState(animate ? 0 : 50);
    const [isDragging, setIsDragging] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const [isAnimated, setIsAnimated] = useState(false);

    useEffect(() => {
        if (animate && !isAnimated) {
            const animationTimeout = setTimeout(() => {
                setSliderPosition(50);
                setIsAnimated(true);
            }, 300);
            return () => clearTimeout(animationTimeout);
        }
    }, [animate, isAnimated]);

    const handleMove = useCallback((clientX: number) => {
        if (containerRef.current) {
            const rect = containerRef.current.getBoundingClientRect();
            const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
            const percent = (x / rect.width) * 100;
            setSliderPosition(percent);
        }
    }, []);

    const handleMouseDown = (e: React.MouseEvent) => {
        e.preventDefault();
        setIsDragging(true);
        handleMove(e.clientX);
    };

    const handleTouchStart = (e: React.TouchEvent) => {
        setIsDragging(true);
        handleMove(e.touches[0].clientX);
    };

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            if (isDragging) handleMove(e.clientX);
        };
        const handleTouchMove = (e: TouchEvent) => {
            if (isDragging) handleMove(e.touches[0].clientX);
        };
        const handleMouseUp = () => {
            setIsDragging(false);
        };

        if (isDragging) {
            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('touchmove', handleTouchMove);
            window.addEventListener('mouseup', handleMouseUp);
            window.addEventListener('touchend', handleMouseUp);
        }

        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('touchmove', handleTouchMove);
            window.removeEventListener('mouseup', handleMouseUp);
            window.removeEventListener('touchend', handleMouseUp);
        };
    }, [isDragging, handleMove]);
    
    const transitionStyle = (animate && !isDragging) ? { transition: 'all 0.7s cubic-bezier(0.25, 1, 0.5, 1)' } : {};

    return (
        <div ref={containerRef} className="relative w-full h-full select-none cursor-ew-resize" onMouseDown={handleMouseDown} onTouchStart={handleTouchStart}>
            <img src={before} alt="Before" className="absolute top-0 left-0 w-full h-full object-cover pointer-events-none" />
            <img
                src={after}
                alt="After"
                className="absolute top-0 left-0 w-full h-full object-cover pointer-events-none"
                style={{ 
                    clipPath: `inset(0 ${100 - sliderPosition}% 0 0)`,
                    ...transitionStyle
                }}
            />
            <div
                className="absolute top-0 bottom-0 w-0.5 bg-white shadow-[0_0_10px_rgba(0,0,0,0.5)] pointer-events-none"
                style={{ 
                    left: `${sliderPosition}%`,
                     ...transitionStyle
                }}
            >
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white/20 backdrop-blur-md rounded-full border-2 border-white flex items-center justify-center">
                   <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M8 9l4-4 4 4m0 6l-4 4-4-4" transform="rotate(90 12 12)"/>
                    </svg>
                </div>
            </div>
        </div>
    );
};
