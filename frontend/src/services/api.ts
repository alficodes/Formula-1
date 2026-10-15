import type {RaceState} from '../types/race';
const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export async function getState():Promise<RaceState>{const r=await fetch(`${API}/api/v1/monaco/state`);if(!r.ok)throw new Error('API unavailable');return r.json()}
export async function action(path:string){const r=await fetch(`${API}/api/v1/monaco/replay/${path}`,{method:'POST'});if(!r.ok)throw new Error('Replay action failed');return r.json()}
export async function simulate(){const r=await fetch(`${API}/api/v1/monaco/simulate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({iterations:500})});if(!r.ok)throw new Error('Simulation failed');return r.json()}
export const websocketUrl = (raceId:string) => `${(import.meta.env.VITE_WS_URL || 'ws://localhost:8000')}/ws/monaco/replay/${raceId}`;
