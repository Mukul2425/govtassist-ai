export type EligibilityStatus =
  | "likely_eligible"
  | "possibly_eligible"
  | "not_eligible"
  | "insufficient_info";

export interface UserProfile {
  age?: number;
  state?: string;
  education?: string;
  occupation?: string;
  annual_family_income?: number;
  gender?: string;
  caste_category?: string;
  is_bpl?: boolean;
  is_disabled?: boolean;
  is_woman?: boolean;
  has_land?: boolean;
  district?: string;
}

export interface SchemeRecommendation {
  scheme_id: string;
  scheme_name: string;
  short_description: string;
  eligibility_status: EligibilityStatus;
  eligibility_score: number;
  why_eligible: string;
  benefits: string[];
  required_documents: string[];
  application_process: string;
  application_url: string | null;
  official_source_url: string;
  missing_information: string[];
  retrieved_context: string[];
}

export interface RecommendationResponse {
  session_id: string;
  query: string;
  extracted_profile: UserProfile;
  recommendations: SchemeRecommendation[];
  follow_up_questions: string[];
  disclaimer: string;
  response_summary: string;
}

export interface SchemeSummary {
  id: string;
  name: string;
  short_description: string;
  government_level: string;
  ministry: string | null;
  category: string;
  applicable_states: string[];
  benefits: string[];
  application_url: string | null;
  official_source_url: string;
}

export interface CategoryCount {
  name: string;
  count: number;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function getRecommendations(
  query: string,
  options?: { profile?: UserProfile; sessionId?: string; maxResults?: number }
): Promise<RecommendationResponse> {
  const res = await fetch(`${API_URL}/recommendations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      query,
      profile: options?.profile,
      session_id: options?.sessionId,
      max_results: options?.maxResults ?? 10,
    }),
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || "Failed to get recommendations");
  }

  return res.json();
}

export async function listSchemes(params?: {
  search?: string;
  state?: string;
  category?: string;
  page?: number;
  pageSize?: number;
}): Promise<{ schemes: SchemeSummary[]; total: number; page: number; page_size: number }> {
  const qs = new URLSearchParams();
  if (params?.search) qs.set("search", params.search);
  if (params?.state) qs.set("state", params.state);
  if (params?.category) qs.set("category", params.category);
  if (params?.page) qs.set("page", String(params.page));
  if (params?.pageSize) qs.set("page_size", String(params.pageSize));

  const res = await fetch(`${API_URL}/schemes?${qs}`);
  if (!res.ok) throw new Error("Failed to fetch schemes");
  return res.json();
}

export async function listCategories(): Promise<{ categories: CategoryCount[]; total: number }> {
  const res = await fetch(`${API_URL}/schemes/categories/list`);
  if (!res.ok) throw new Error("Failed to fetch categories");
  return res.json();
}

export async function checkHealth(): Promise<{ status: string; llm_available: boolean }> {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error("API unavailable");
  return res.json();
}
