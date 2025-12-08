// API Configuration - Single Source of Truth
// This uses Vite's environment variable system
// Values come from:
// - .env file for local development (npm run dev)
// - Docker build args for containerized deployment (docker-compose)

export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
} as const;

// Helper function to get full API endpoint
export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};
