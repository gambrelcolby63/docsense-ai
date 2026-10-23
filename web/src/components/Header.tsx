import Link from "next/link";

export function Header() {
  return (
    <header className="sticky top-0 z-20 border-b border-line/80 bg-paper/85 backdrop-blur">
      <div className="mx-auto flex max-w-3xl items-center justify-between gap-3 px-4 py-3">
        <Link href="/" className="flex items-center gap-2.5 rounded-lg focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal">
          <Mark />
          <span className="font-serif text-xl tracking-tight">DocSense</span>
        </Link>
        <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-muted">Document Q&A</p>
      </div>
    </header>
  );
}

function Mark() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" aria-hidden="true" className="shrink-0">
      <rect x="3" y="3" width="22" height="22" rx="6" fill="#0d6b56" />
      <path d="M8 9.5h8.5M8 14h12M8 18.5h7" stroke="#f4efe6" strokeWidth="1.6" strokeLinecap="round" />
      <path d="M17 8.5l3.2 3.2-3.2 3.2" fill="none" stroke="#f4c7a4" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
