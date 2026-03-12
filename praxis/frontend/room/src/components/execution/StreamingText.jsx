import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';

export default function StreamingText({ text, isStreaming }) {
  const [displayedLength, setDisplayedLength] = useState(text.length);
  const prevLengthRef = useRef(text.length);
  const containerRef = useRef(null);

  useEffect(() => {
    if (!isStreaming) {
      setDisplayedLength(text.length);
      return;
    }

    // Animate new characters
    const prevLen = prevLengthRef.current;
    if (text.length > prevLen) {
      let current = prevLen;
      const isCode = text.slice(prevLen).includes('```');
      const charDelay = isCode ? 8 : 18;

      const interval = setInterval(() => {
        current++;
        setDisplayedLength(current);
        if (current >= text.length) clearInterval(interval);
      }, charDelay);

      prevLengthRef.current = text.length;
      return () => clearInterval(interval);
    }
    prevLengthRef.current = text.length;
  }, [text, isStreaming]);

  // Auto-scroll
  useEffect(() => {
    if (containerRef.current && isStreaming) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [displayedLength, isStreaming]);

  const displayed = text.slice(0, displayedLength);

  return (
    <div ref={containerRef} className="text-sm text-white/70 leading-relaxed whitespace-pre-wrap font-mono">
      {displayed}
      {isStreaming && (
        <motion.span
          className="inline-block w-[2px] h-[14px] bg-[#6366f1] ml-0.5 align-middle"
          animate={{ opacity: [1, 0, 1] }}
          transition={{ duration: 0.8, repeat: Infinity }}
        />
      )}
    </div>
  );
}
