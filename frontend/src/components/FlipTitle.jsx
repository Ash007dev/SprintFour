import { useState, useEffect, useRef } from 'react';

const WORDS = ['Conseal', 'Glass Box'];
const HOLD_MS = 3500;
const STAGGER_MS = 50;

export default function FlipTitle({ onClick, className = '' }) {
  const [currentWord, setCurrentWord] = useState(WORDS[0]);
  const [animatingIndices, setAnimatingIndices] = useState(new Set());
  const wordIndexRef = useRef(0);
  const timeoutsRef = useRef([]);

  useEffect(() => {
    const cycle = () => {
      const nextIdx = (wordIndexRef.current + 1) % WORDS.length;
      const nextWord = WORDS[nextIdx];
      const maxLen = Math.max(currentWord.length, nextWord.length);

      // Stagger each letter: fade out current, fade in next
      for (let i = 0; i < maxLen; i++) {
        const t = setTimeout(() => {
          // Mark letter as animating (fade out)
          setAnimatingIndices(prev => new Set([...prev, i]));

          // After fade out, swap the character and fade in
          const swapT = setTimeout(() => {
            setCurrentWord(prev => {
              const padded = prev.padEnd(maxLen);
              const chars = padded.split('');
              chars[i] = nextWord[i] || '';
              return chars.join('');
            });
            // Remove from animating (triggers fade in)
            setAnimatingIndices(prev => {
              const next = new Set(prev);
              next.delete(i);
              return next;
            });
          }, 150);
          timeoutsRef.current.push(swapT);
        }, i * STAGGER_MS);
        timeoutsRef.current.push(t);
      }

      // Trim trailing spaces after animation completes
      const cleanupT = setTimeout(() => {
        setCurrentWord(nextWord);
        wordIndexRef.current = nextIdx;
      }, maxLen * STAGGER_MS + 300);
      timeoutsRef.current.push(cleanupT);
    };

    const interval = setInterval(cycle, HOLD_MS);
    return () => {
      clearInterval(interval);
      timeoutsRef.current.forEach(clearTimeout);
      timeoutsRef.current = [];
    };
  }, []);

  const chars = currentWord.split('');

  return (
    <button
      onClick={onClick}
      className={`font-[var(--font-headline)] font-black tracking-tighter text-primary hover:opacity-80 transition-opacity cursor-pointer inline-flex items-baseline ${className}`}
      aria-label="Conseal / Glass Box"
    >
      {chars.map((char, i) => (
        <span
          key={i}
          className="inline-block transition-all duration-150 ease-in-out"
          style={{
            opacity: animatingIndices.has(i) ? 0 : 1,
            transform: animatingIndices.has(i) ? 'translateY(-8px)' : 'translateY(0)',
            minWidth: char === ' ' ? '0.25em' : undefined,
          }}
        >
          {char === ' ' ? '\u00A0' : char}
        </span>
      ))}
    </button>
  );
}
