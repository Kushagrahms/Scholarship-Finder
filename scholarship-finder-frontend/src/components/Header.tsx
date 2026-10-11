
import Brand from "./Brand";

interface HeaderProps {
  onHomeClick: () => void;
  onBrowseClick: () => void;
}

export default function Header({
  onHomeClick,
  onBrowseClick,
}: HeaderProps) {
  return (
    <header className="site-header">
      <div className="header-inner">
        <Brand onClick={onHomeClick} />

        <nav className="header-nav" aria-label="Main navigation">
          <button
            type="button"
            className="nav-link"
            onClick={onHomeClick}
          >
            Home
          </button>

          <button
            type="button"
            className="nav-link"
            onClick={onBrowseClick}
          >
            Browse Scholarships
          </button>

          <button
            type="button"
            className="nav-cta"
            onClick={onBrowseClick}
          >
            Explore Scholarships
          </button>
        </nav>
      </div>
    </header>
  );
}
