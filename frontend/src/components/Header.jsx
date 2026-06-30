import FlipTitle from './FlipTitle';

export default function Header({ onLogoClick }) {
  return (
    <header className="bg-background w-full border-b-4 border-primary flex justify-between items-center px-8 py-6 relative z-50">
      <FlipTitle onClick={onLogoClick} />
      <span className="font-[var(--font-mono)] text-xs uppercase tracking-wider text-secondary hidden sm:block">
        A Pseudonymization Approach to Trust
      </span>
    </header>
  );
}
