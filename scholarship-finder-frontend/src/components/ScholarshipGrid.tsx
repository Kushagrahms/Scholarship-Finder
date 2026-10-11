
import { AlertCircle, LoaderCircle, Search } from "lucide-react";
import type { Scholarship } from "../types/scholarship";
import ScholarshipCard from "./ScholarshipCard";

interface ScholarshipGridProps {
  scholarships: Scholarship[];
  loading: boolean;
  error: string | null;
  onScholarshipClick: (id: number) => void;
  onRetry: () => void;
}

export default function ScholarshipGrid({
  scholarships,
  loading,
  error,
  onScholarshipClick,
  onRetry,
}: ScholarshipGridProps) {
  if (loading) {
    return (
      <div className="grid-message" role="status">
        <LoaderCircle className="loading-spinner" size={30} />
        <h3>Finding scholarships for you</h3>
        <p>Loading the latest available records...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="grid-message grid-error" role="alert">
        <AlertCircle size={32} />
        <h3>We couldn't load scholarships</h3>
        <p>{error}</p>
        <button
          type="button"
          className="primary-button"
          onClick={onRetry}
        >
          Try again
        </button>
      </div>
    );
  }

  if (scholarships.length === 0) {
    return (
      <div className="grid-message">
        <Search size={32} />
        <h3>No scholarships found</h3>
        <p>
          Try another search term or adjust your filters to see available
          results.
        </p>
      </div>
    );
  }

  return (
    <div className="scholarship-grid">
      {scholarships.map((scholarship) => (
        <ScholarshipCard
          key={scholarship.id}
          scholarship={scholarship}
          onClick={onScholarshipClick}
        />
      ))}
    </div>
  );
}
