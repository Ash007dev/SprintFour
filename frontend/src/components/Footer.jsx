import FlipTitle from './FlipTitle';

export default function Footer({ onDocsClick }) {
  return (
    <footer className="bg-background w-full border-t-4 border-primary flex flex-col md:flex-row justify-between items-center px-8 py-6 gap-6 mt-auto">
      <FlipTitle className="text-2xl uppercase" />
      <div className="flex gap-6 font-[var(--font-mono)] text-sm uppercase">
        <a href="#" className="text-secondary hover:text-primary transition-colors">Privacy</a>
        <a href="#" className="text-secondary hover:text-primary transition-colors">Terms</a>
        <button
          onClick={onDocsClick}
          className="text-secondary hover:text-primary transition-colors cursor-pointer uppercase"
        >
          API Docs
        </button>
      </div>
      <div className="font-[var(--font-mono)] text-sm uppercase text-secondary flex items-center gap-2">
        <span>&copy; 2026</span>
        <FlipTitle className="text-sm uppercase" />
      </div>
    </footer>
  );
}
