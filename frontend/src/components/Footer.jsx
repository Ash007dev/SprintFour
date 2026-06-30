export default function Footer({ onDocsClick }) {
  return (
    <footer className="bg-background w-full border-t-4 border-primary flex justify-center items-center px-8 py-6 mt-auto">
      <button
        onClick={onDocsClick}
        className="font-[var(--font-mono)] text-sm uppercase text-secondary hover:text-primary transition-colors cursor-pointer"
      >
        API Docs
      </button>
    </footer>
  );
}
