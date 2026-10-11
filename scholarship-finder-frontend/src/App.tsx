import { useCallback,useEffect,useState } from "react";
import { BrowserRouter,Link,Route,Routes,useNavigate,useParams } from "react-router-dom";
import { ArrowLeft,ArrowRight,Search } from "lucide-react";

import Header from "./components/Header";
import ScholarshipGrid from "./components/ScholarshipGrid";
import { scholarshipApi } from "./api/scholarships";
import type{Scholarship,ScholarshipFilters} from "./types/scholarship";
import { displayAmount,displayDate,humanize,safeExternalUrl } from "./utils/format";
import "./App.css";
import heroBackground from "./assets/scholarship-hero.png";

const PAGE_SIZE = 20;
function HomePage(){
  const navigate = useNavigate();
  const[query,setQuery] = useState("");
  const[scholarships,setScholarships] = useState<Scholarship[]>([]);
  const[loading,setLoading] = useState(true);
  const[error,setError] = useState<string |null>(null);
  const loadScholarships = useCallback(async()=>{
    setLoading(true);
    setError(null);

    try{
      const data = query.trim()
      ?await scholarshipApi.search(query.trim(),PAGE_SIZE)
      :await scholarshipApi.list({limit:PAGE_SIZE,offset:0});

      setScholarships(data);
    }catch(err){
      setError(
        err instanceof Error ?err.message:"Something went wrong"
      );
    }
    finally{
      setLoading(false);
    }
  }, [query]);

  useEffect(()=>{
    void loadScholarships();
  }, [loadScholarships]);

  function handleSearch(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    navigate(`/scholarships?q=${encodeURIComponent(query.trim())}`);
  }

  return (
    <>
      <Header
        onHomeClick={() => navigate("/")}
        onBrowseClick={() => navigate("/scholarships")}
      />

      <main>

<section
  className="hero-section"
  style={{ backgroundImage: `url(${heroBackground})` }}
>
  <div className="hero-content">
    <span className="eyebrow">
      YOUR NEXT OPPORTUNITY STARTS HERE
    </span>

    <h1>
      Find the right scholarship.
      <span> Focus on your future.</span>
    </h1>

    <p>
      Explore scholarship opportunities and find the information you
      need to take your next step in education.
    </p>

    <form className="hero-search" onSubmit={handleSearch}>
      <Search size={21} aria-hidden="true" />

      <input
        aria-label="Search scholarships"
        placeholder="Search by scholarship or provider..."
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />

      <button type="submit">
        Search <ArrowRight size={17} />
      </button>
    </form>

    <p className="hero-note">
      Browse available records without creating an account.
    </p>
  </div>
</section>

        <section className="home-scholarships section-container">
          <div className="section-heading">
            <div>
              <span className="eyebrow">EXPLORE OPPORTUNITIES</span>
              <h2>Scholarships to explore</h2>
              <p>Browse records currently available in our database.</p>
            </div>

            <button
              type="button"
              className="text-button"
              onClick={() => navigate("/scholarships")}
            >
              View all <ArrowRight size={17} />
            </button>
          </div>

          <ScholarshipGrid
            scholarships={scholarships.slice(0, 6)}
            loading={loading}
            error={error}
            onScholarshipClick={(id) => navigate(`/scholarships/${id}`)}
            onRetry={() => void loadScholarships()}
          />
        </section>
      </main>
    </>
  );
}

function CataloguePage() {
  const navigate = useNavigate();
  const [searchParams] = [
    new URLSearchParams(window.location.search),
  ];
  const initialQuery = searchParams.get("q") ?? "";

  
const [query, setQuery] = useState(initialQuery);

// Values currently selected in the controls
const [educationLevel, setEducationLevel] = useState("");
const [category, setCategory] = useState("");
const [location, setLocation] = useState("");

// Values actually used to filter results
const [appliedEducationLevel, setAppliedEducationLevel] = useState("");
const [appliedCategory, setAppliedCategory] = useState("");
const [appliedLocation, setAppliedLocation] = useState("");

const [scholarships, setScholarships] = useState<Scholarship[]>([]);
const [loading, setLoading] = useState(true);
const [error, setError] = useState<string | null>(null);


const loadScholarships = useCallback(async () => {
  setLoading(true);
  setError(null);

  try {
    let data: Scholarship[];

    if (query.trim()) {
      data = await scholarshipApi.search(query.trim(), 100);
    } else {
      const filters: ScholarshipFilters = {
        limit: 100,
        offset: 0,
      };

      if (appliedEducationLevel) {
        filters.education_level = appliedEducationLevel;
      }

      if (appliedCategory) {
        filters.category = appliedCategory;
      }

      if (appliedLocation) {
        filters.location = appliedLocation;
      }

      data = await scholarshipApi.list(filters);
    }

    setScholarships(data);
  } catch (err) {
    setError(
      err instanceof Error ? err.message : "Something went wrong."
    );
  } finally {
    setLoading(false);
  }
}, [
  query,
  appliedEducationLevel,
  appliedCategory,
  appliedLocation,
]);

useEffect(() => {
  void loadScholarships();
}, [loadScholarships]);

function handleSearch(event: React.FormEvent<HTMLFormElement>) {
  event.preventDefault();
  void loadScholarships();
}

function handleApplyFilters() {
  setAppliedEducationLevel(educationLevel);
  setAppliedCategory(category);
  setAppliedLocation(location);
}

function handleResetFilters() {
  setEducationLevel("");
  setCategory("");
  setLocation("");

  setAppliedEducationLevel("");
  setAppliedCategory("");
  setAppliedLocation("");
}


  return (
    <>
      <Header
        onHomeClick={() => navigate("/")}
        onBrowseClick={() => navigate("/scholarships")}
      />

      <main className="section-container catalogue-page">
        <div className="breadcrumb">
          <Link to="/">Home</Link>
          <span>/</span>
          <span>Scholarships</span>
        </div>

        <div className="catalogue-heading">
          <span className="eyebrow">THE SCHOLARSHIP DIRECTORY</span>
          <h1>Explore scholarships</h1>
          <p>Search available records and narrow your results.</p>
        </div>

        <form className="catalogue-search" onSubmit={handleSearch}>
          <Search size={20} aria-hidden="true" />
          <input
            aria-label="Search scholarships"
            placeholder="Search scholarship titles or providers..."
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <button type="submit" className="primary-button">
            Search
          </button>
        </form>

        <div className="filter-row">
          <label>
            <span>Education level</span>
            <select
              value={educationLevel}
              onChange={(event) => setEducationLevel(event.target.value)}
            >
              <option value="">All education levels</option>
              <option value="school">School</option>
              <option value="undergraduate">Undergraduate</option>
              <option value="postgraduate">Postgraduate</option>
              <option value="doctoral">Doctoral</option>
            </select>
          </label>


<label>
  <span>Category</span>
  <select
    value={category}
    onChange={(event) => setCategory(event.target.value)}
  >
    <option value="">All categories</option>
    <option value="Merit">Merit</option>
    <option value="Need-Based">Need-Based</option>
    <option value="Means-Based">Means-Based</option>
    <option value="Welfare">Welfare</option>
    <option value="Minority">Minority</option>
    <option value="SC/ST/OBC">SC/ST/OBC</option>
  </select>
</label>

<label>
  <span>Location</span>
  <select
    value={location}
    onChange={(event) => setLocation(event.target.value)}
  >
    <option value="">All locations</option>
    <option value="India">India</option>
    <option value="Madhya Pradesh">Madhya Pradesh</option>
    <option value="North Eastern Region">North Eastern Region</option>
    <option value="Delhi">Delhi</option>
    <option value="Maharashtra">Maharashtra</option>
    <option value="Uttar Pradesh">Uttar Pradesh</option>
  </select>
</label>


<button
  type="button"
  className="filter-apply"
  onClick={handleApplyFilters}
>
  Apply filters
</button>

<button
  type="button"
  className="filter-reset"
  onClick={handleResetFilters}
>
  Reset
</button>

        </div>

        <div className="results-heading">
          <h2>Available records</h2>
          {!loading && !error && (
            <span>{scholarships.length} results returned</span>
          )}
        </div>

        {query.trim() && (educationLevel || category || location) && (
          <p className="filter-note">
            Search and filters are applied separately because the current API
            does not support combining them in one request.
          </p>
        )}

        <ScholarshipGrid
          scholarships={scholarships}
          loading={loading}
          error={error}
          onScholarshipClick={(id) => navigate(`/scholarships/${id}`)}
          onRetry={() => void loadScholarships()}
        />
      </main>
    </>
  );
}

function ScholarshipDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [scholarship, setScholarship] = useState<Scholarship | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadScholarship = useCallback(async () => {
    if (!id || !/^\d+$/.test(id)) {
      setError("Invalid scholarship ID.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      setScholarship(await scholarshipApi.get(Number(id)));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Unable to load this scholarship."
      );
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    void loadScholarship();
  }, [loadScholarship]);

  return (
    <>
      <Header
        onHomeClick={() => navigate("/")}
        onBrowseClick={() => navigate("/scholarships")}
      />

      <main className="section-container detail-page">
        <button
          type="button"
          className="back-button"
          onClick={() => navigate("/scholarships")}
        >
          <ArrowLeft size={17} /> Back to scholarships
        </button>

        {loading ? (
          <div className="grid-message">Loading scholarship details...</div>
        ) : error || !scholarship ? (
          <div className="grid-message grid-error" role="alert">
            <h2>Scholarship details unavailable</h2>
            <p>{error ?? "This scholarship could not be found."}</p>
            <button
              type="button"
              className="primary-button"
              onClick={() => void loadScholarship()}
            >
              Try again
            </button>
          </div>
        ) : (
          <>
            <section className="detail-hero">
              <span className="detail-provider">
                {scholarship.provider || "Provider not specified"}
              </span>
              <h1>{scholarship.title}</h1>
              {scholarship.category && (
                <span className="scholarship-category">
                  {humanize(scholarship.category)}
                </span>
              )}
            </section>

            <div className="detail-layout">
              <div className="detail-main">
                <section className="detail-panel">
                  <h2>About this scholarship</h2>
                  <p>
                    {scholarship.description ||
                      scholarship.objective ||
                      "A detailed description is not available for this scholarship yet."}
                  </p>
                </section>

                <section className="detail-panel">
                  <h2>Eligibility</h2>
                  <p>
                    {scholarship.eligibility ||
                      "Eligibility details are not specified in the available record."}
                  </p>
                  {scholarship.education_level && (
                    <p>
                      <strong>Education level:</strong>{" "}
                      {humanize(scholarship.education_level)}
                    </p>
                  )}
                  {scholarship.location && (
                    <p>
                      <strong>Location:</strong> {scholarship.location}
                    </p>
                  )}
                  {scholarship.income_requirement && (
                    <p>
                      <strong>Income requirement:</strong>{" "}
                      {scholarship.income_requirement}
                    </p>
                  )}
                </section>

                <section className="detail-panel">
                  <h2>Funding and duration</h2>
                  <p>
                    <strong>Funding:</strong>{" "}
                    {displayAmount(scholarship.amount, scholarship.amount_text)}
                  </p>
                  {scholarship.slots != null && (
                    <p>
                      <strong>Number of slots:</strong> {scholarship.slots}
                    </p>
                  )}
                  {scholarship.tenure && (
                    <p>
                      <strong>Duration:</strong> {scholarship.tenure}
                    </p>
                  )}
                </section>

                <section className="detail-panel">
                  <h2>Important dates</h2>
                  <p>
                    <strong>Opening date:</strong>{" "}
                    {scholarship.opening_date
                      ? displayDate(scholarship.opening_date)
                      : "Not specified"}
                  </p>
                  <p>
                    <strong>Application deadline:</strong>{" "}
                    {displayDate(scholarship.deadline)}
                  </p>
                </section>
              </div>

              <aside className="detail-sidebar">
                <h2>Application links</h2>
                {[
                  ["Apply / Official page", scholarship.application_url],
                  ["Source page", scholarship.source_url],
                  ["Detailed information", scholarship.detail_url],
                  ["Guidelines", scholarship.guidelines_url],
                  ["Frequently asked questions", scholarship.faq_url],
                ].map(([label, value]) => {
                  const url = safeExternalUrl(value);

                  return url ? (
                    <a
                      key={label}
                      className="official-link"
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      {label} <ArrowRight size={16} />
                    </a>
                  ) : null;
                })}
                {![
                  scholarship.application_url,
                  scholarship.source_url,
                  scholarship.detail_url,
                  scholarship.guidelines_url,
                  scholarship.faq_url,
                ].some((value) => safeExternalUrl(value)) && (
                  <p>No official links are available in this record.</p>
                )}
              </aside>
            </div>
          </>
        )}
      </main>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/scholarships" element={<CataloguePage />} />
        <Route path="/scholarships/:id" element={<ScholarshipDetailPage />} />
        <Route path="*" element={<HomePage />} />
      </Routes>
    </BrowserRouter>
  );
}