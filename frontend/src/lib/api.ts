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

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function getRecommendations(
  query: string,
  profile?: UserProfile
): Promise<RecommendationResponse> {
  const res = await fetch(`${API_URL}/recommendations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, profile, max_results: 10 }),
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || "Failed to get recommendations");
  }

  return res.json();
}

export async function listSchemes(search?: string): Promise<SchemeSummary[]> {
  const params = new URLSearchParams();
  if (search) params.set("search", search);

  const res = await fetch(`${API_URL}/schemes?${params}`);
  if (!res.ok) throw new Error("Failed to fetch schemes");

  const data = await res.json();
  return data.schemes;
}

export async function checkHealth(): Promise<{ status: string; llm_available: boolean }> {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error("API unavailable");
  return res.json();
}
