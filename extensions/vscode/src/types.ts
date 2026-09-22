export type Mode = 'ask' | 'debug' | 'feature' | 'summary';
export interface Source { id: string; path: string; text: string; sha256: string; start_line?: number; end_line?: number; unit?: string; start_unit?: number; end_unit?: number; }
export interface FileChange { path: string; before: string | null; after: string; }
export interface Proposal { id: string; root: string; files: FileChange[]; dependencies: Record<string, string>; }
export interface Result {
  mode: Mode; prompt: string; model: string; root: string; status: string;
  answer: { claims: { text: string; source_ids: string[] }[]; uncertainties: string[]; suggested_checks: string[] };
  sources: Source[]; coverage: Record<string, unknown>; proposal: Proposal | null;
  decision: 'pending' | 'applying' | 'applied' | 'cancelled' | 'uncertain'; trace: unknown[];
}
