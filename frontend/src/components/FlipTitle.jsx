import { useState, useEffect, useRef } from 'react';

const WORDS = ['Conseal', 'Glass Box'];
const HOLD_MS = 3500;
const FLIP_MS = 620;
const STAGGER_MS = 45;
const MAX_CHARS = Math.max(...WORDS.map(word => word.length));

export default function FlipTitle({ onClick, className = '' }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [flipping, setFlipping] = useState(false);
  const timeoutsRef = useRef([]);

  useEffect(() => {
    const cycle = () => {
      setFlipping(true);

      const commitTimer = setTimeout(() => {
        setActiveIndex(index => (index + 1) % WORDS.length);
        setFlipping(false);
      }, FLIP_MS + MAX_CHARS * STAGGER_MS);

      timeoutsRef.current.push(commitTimer);
    };

    const interval = setInterval(cycle, HOLD_MS);
    return () => {
      clearInterval(interval);
      timeoutsRef.current.forEach(clearTimeout);
      timeoutsRef.current = [];
    };
  }, []);

  const nextIndex = (activeIndex + 1) % WORDS.length;

  const renderWord = (word, mode) => (
    <span className={`flip-title-word flip-title-word-${mode}`}>
      {Array.from(word).map((char, index) => (
        <span
          key={`${word}-${index}`}
          className={`flip-title-letter ${char === ' ' ? 'flip-title-space' : ''}`}
          style={{ transitionDelay: `${index * STAGGER_MS}ms` }}
        >
          {char === ' ' ? '\u00A0' : char}
        </span>
      ))}
    </span>
  );

  return (
    <button
      onClick={onClick}
      className={`font-[var(--font-headline)] font-black tracking-tighter text-primary hover:opacity-80 transition-opacity cursor-pointer inline-flex items-baseline ${className}`}
      aria-label="Conseal / Glass Box"
    >
      <span className={`flip-title-shell ${flipping ? 'is-flipping' : ''}`} style={{ '--flip-chars': MAX_CHARS }}>
        {renderWord(WORDS[activeIndex], 'current')}
        {flipping && renderWord(WORDS[nextIndex], 'next')}
      </span>
    </button>
  );
}
