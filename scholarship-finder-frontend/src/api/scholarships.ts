import type { Scholarship,ScholarshipFilters } from "../types/scholarship";


const API_BASE = (
    import.meta.env.VITE_API_BASE_URL || "/api"
).replace(/\/$/, "");

async function request<T>(path:string): Promise<T>{
    let response:Response;
    try{
        response = await fetch(`${API_BASE}${path}`, {
            headers:{Accept: "application/json"},
        });
    }
    catch{
        throw new Error(`Cannot connect to ${API_BASE}. Check that FastAPI is running.`);
    }
    if(!response.ok){
        throw new Error(`API request failed: ${response.status}`);
    }
    return response.json() as Promise<T>;
}

function buildQuery(values:Record<string, string | number | undefined>): string{
    const params = new URLSearchParams();

    for (const [key,value] of Object.entries(values)){
        if(value !== undefined && String(value).trim() !== ""){
            params.set(key,String(value));
        }
    }

    const query = params.toString();
    return query ? `?${query}` : "";
}

export const scholarshipApi = {
    list(filters:ScholarshipFilters= {}){
        return request<Scholarship[]>(`/scholarships${buildQuery({ ...filters })}`);
    },
    search(query:string, limit=100){
        return request<Scholarship[]>(`/scholarships/search${buildQuery({
        q: query,
        limit,
      })}`
     );
    },

    get(id:number){
        return request<Scholarship>(`/scholarships/${id}`);
    },
};
