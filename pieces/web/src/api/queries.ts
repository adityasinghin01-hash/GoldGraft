import { useQuery } from '@tanstack/react-query';
import { api, ApiError } from './client';

const retry = (n: number, e: unknown) => n < 1 && !(e instanceof ApiError && e.status >= 400 && e.status < 500);

export const useGraft = (id: string) => useQuery({ queryKey: ['graft', id], queryFn: () => api.graft(id), retry });
export const useRootMap = (id: string) => useQuery({ queryKey: ['rootmap', id], queryFn: () => api.rootmap(id), retry });
export const useScenarios = (id: string) => useQuery({ queryKey: ['scenarios', id], queryFn: () => api.scenarios(id), retry });
export const useCmel = (id: string, scenario: string | null) =>
  useQuery({ queryKey: ['cmel', id, scenario], queryFn: () => api.cmel(id, scenario!), enabled: !!scenario, retry, staleTime: Infinity });
export const useProof = (id: string) => useQuery({ queryKey: ['proof', id], queryFn: () => api.proof(id), retry });
export const useConnected = (id: string) => useQuery({ queryKey: ['connected', id], queryFn: () => api.connected(id), retry: false });
export const useCertificate = (id: string) => useQuery({ queryKey: ['cert', id], queryFn: () => api.certificate(id), retry });
export const useHealSnapshot = (id: string) => useQuery({ queryKey: ['heal', id], queryFn: () => api.heal(id), retry });
export const useRecipes = () => useQuery({ queryKey: ['recipes'], queryFn: () => api.recipes(), retry });
export const useLearningCurve = () => useQuery({ queryKey: ['curve'], queryFn: () => api.learningCurve(), retry });
export const useOrchard = () => useQuery({ queryKey: ['orchard'], queryFn: () => api.orchard(), retry });
export const useGauntlet = (runId: string) => useQuery({ queryKey: ['gauntlet', runId], queryFn: () => api.gauntlet(runId), retry });
export const useComparison = () => useQuery({ queryKey: ['comparison'], queryFn: () => api.comparison(), retry });
