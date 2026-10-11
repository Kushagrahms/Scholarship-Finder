export interface Scholarship{
    id:number;
    title:string;
    provider:string;
    description:string | null;
    objective: string | null;
    eligibility: string | null;
    amount: string | number | null;
    amount_text: string | null;
    slots: string | number | null;
    tenure: string | null;
    education_level: string | null;
    category: string | null;
    location: string | null;
    income_requirement: string | null;
    opening_date: string | null;
    deadline: string | null;
    application_url: string | null;
    source: string | null;
    source_url: string | null;
    detail_url: string | null;
    guidelines_url: string | null;
    faq_url: string | null;
    scraped_at: string | null;
    raw_metadata: Record<string, unknown> | null;
    status: string;
    first_seen: string | null;
    last_seen: string | null;
    updated_at: string | null;
}

export interface ScholarshipFilters{
    education_level?:string;
    category?:string;
    location?:string;
    deadline_before?:string;
    deadline_after?:string;
    limit?:number;
    offset?:number;
}