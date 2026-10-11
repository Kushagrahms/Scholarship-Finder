
import { ArrowUpRight, CalendarDays, MapPin } from "lucide-react";
import type { Scholarship } from "../types/scholarship";
import { displayAmount, displayDate, humanize } from "../utils/format";

interface ScholarshipCardProps {
  scholarship: Scholarship;
  onClick: (id: number) => void;
}

export default function ScholarshipCard({
  scholarship,
  onClick,
}: ScholarshipCardProps) {
  const location = scholarship.location?.trim();
  const category = scholarship.category?.trim();
  const educationLevel = scholarship.education_level?.trim();

  return (
    <article className="scholarship-card">
      <div className="scholarship-card-top">
        <span className="scholarship-provider">
          {scholarship.provider || "Provider not specified"}
        </span>

        {category && (
          <span className="scholarship-category">
            {humanize(category)}
          </span>
        )}
      </div>

      <h3 className="scholarship-title">{scholarship.title}</h3>

      <p className="scholarship-description">
        {scholarship.description?.trim() ||
          scholarship.objective?.trim() ||
          "A detailed description is not available for this scholarship yet."}
      </p>

      <div className="scholarship-meta">
        {location && (
          <span>
            <MapPin size={15} aria-hidden="true" />
            {location}
          </span>
        )}

        {educationLevel && (
          <span>{humanize(educationLevel)}</span>
        )}

        <span>
          <CalendarDays size={15} aria-hidden="true" />
          {displayDate(scholarship.deadline)}
        </span>
      </div>

      <div className="scholarship-card-footer">
        <div className="scholarship-amount">
          <span>Funding</span>
          <strong>
            {displayAmount(scholarship.amount, scholarship.amount_text)}
          </strong>
        </div>

        <button
          type="button"
          className="card-details-button"
          onClick={() => onClick(scholarship.id)}
          aria-label={`View details for ${scholarship.title}`}
        >
          View details
          <ArrowUpRight size={16} aria-hidden="true" />
        </button>
      </div>
    </article>
  );
}
