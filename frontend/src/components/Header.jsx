export default function Header({ onLogoClick }) {
  return (
    <header className="bg-background w-full border-b-4 border-primary flex justify-between items-center px-8 py-6 relative z-50">
      <button
        onClick={onLogoClick}
        className="font-[var(--font-headline)] text-4xl font-black tracking-tighter text-primary hover:opacity-80 transition-opacity cursor-pointer"
      >
        Glass Box
      </button>
    </header>
  );
}
