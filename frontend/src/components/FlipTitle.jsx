import { useState, useEffect } from 'react';

const WORDS = ['Conseal', 'Glass Box'];
const FLIP_STAGGER_MS = 80; // delay between each letter flip
const HOLD_MS = 4000; // how long to hold each word before flipping

export default function FlipTitle({ onClick }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [nextIndex, setNextIndex] = useState(1);
  const [flipping, setFlipping] = useState(false);
  const [flippedCount, setFlippedCount] = useState(0);

  const currentWord = WORDS[currentIndex];
  const nextWord = WORDS[nextIndex];
  const maxLen = Math.max(currentWord.length, nextWord.length);

  // Pad words to equal length
  const padded = (word) => word.padEnd(maxLen, '\u00A0');
  const currentPadded = padded(currentWord);
  const nextPadded = padded(nextWord);

  useEffect(() => {
    // Start flip after hold duration
    const holdTimer = setTimeout(() => {
      setFlipping(true);
      setFlippedCount(0);
    }, HOLD_MS);

    return () => clearTimeout(holdTimer);
  }, [currentIndex]);

  useEffect(() => {
    if (!flipping) return;

    if (flippedCount < maxLen) {
      const timer = setTimeout(() => {
        setFlippedCount((c) => c + 1);
      }, FLIP_STAGGER_MS);
      return () => clearTimeout(timer);
    }

    // All letters flipped - commit the change
    const commitTimer = setTimeout(() => {
      setCurrentIndex(nextIndex);
      setNextIndex((nextIndex + 1) % WORDS.length);
      setFlipping(false);
      setFlippedCount(0);
    }, 300);

    return () => clearTimeout(commitTimer);
  }, [flipping, flippedCount, maxLen, nextIndex]);

  return (
    <button
      onClick={onClick}
      className="font-[var(--font-headline)] text-4xl font-black tracking-tighter text-primary hover:opacity-80 transition-opacity cursor-pointer flex"
      style={{ perspective: '600px' }}
    >
      {Array.from({ length: maxLen }).map((_, i) => {
        const isFlipped = flipping && i < flippedCount;
        const currentChar = currentPadded[i] || '\u00A0';
        const nextChar = nextPadded[i] || '\u00A0';

        return (
          <span
            key={`${currentIndex}-${i}`}
            className="inline-block relative"
            style={{
              width: currentChar === '\u00A0' && nextChar === '\u00A0' ? '0.3em' : undefined,
              transformStyle: 'preserve-3d',
              transition: 'transform 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
              transform: isFlipped ? 'rotateX(180deg)' : 'rotateX(0deg)',
            }}
          >
            {/* Front face (current) */}
            <span
              style={{
                backfaceVisibility: 'hidden',
                display: 'block',
              }}
            >
              {currentChar}
            </span>
            {/* Back face (next) */}
            <span
              style={{
                backfaceVisibility: 'hidden',
                transform: 'rotateX(180deg)',
                position: 'absolute',
                top: 0,
                left: 0,
                display: 'block',
              }}
            >
              {nextChar}
            </span>
          </span>
        );
      })}
    </button>
  );
}
