export type JDStruct = {
  role: string;
  skills_required: string[];
  skills_nice: string[];
  experience_min: number;
  experience_max: number;
  location: string;
  must_haves: string[];
  soft_skills: string[];
};

export type ConversationTurn = { speaker: "recruiter" | "candidate"; text: string };
export type Conversation = { turns: ConversationTurn[] };

export type MatchResult = {
  candidate_id: string;
  match_score: number;
  reasoning: string;
  matched_skills: string[];
  missing_skills: string[];
};

export type InterestResult = {
  candidate_id: string;
  interest_score: number;
  signals: string[];
  summary: string;
  conversation: Conversation;
};

export type RankedRow = {
  candidate_id: string;
  name: string;
  title: string;
  match_score: number;
  interest_score: number | null;
  final_score: number;
  match_reasoning: string;
  interest_summary: string | null;
};

export type ScoutResponse = {
  jd: JDStruct;
  ranked: RankedRow[];
  conversations: Record<string, Conversation>;
  match_details: Record<string, MatchResult>;
  interest_details: Record<string, InterestResult>;
  weights: { match: number; interest: number };
};

export type Weights = { match: number; interest: number };
