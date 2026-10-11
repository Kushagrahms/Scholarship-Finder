
import { GraduationCap } from "lucide-react";

interface BrandProps {
  onClick?: () => void;
}

export default function Brand({ onClick }: BrandProps) {
  return (
    <button
      type="button"
      className="brand"
      onClick={onClick}
      aria-label="Scholarship Finder home"
    >
      <span className="brand-icon">
        <GraduationCap size={25} strokeWidth={2.2} />
      </span>

      <span className="brand-text">
        <span className="brand-name">Scholarship Finder</span>
        <span className="brand-tagline">Your future, funded.</span>
      </span>
    </button>
  );
}
