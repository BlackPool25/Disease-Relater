/**
 * Axios API Client Configuration
 * 
 * Centralized HTTP client with error handling interceptors.
 * All API requests should use this client for consistency.
 */
import axios, { AxiosError } from 'axios';

// API base URL from environment or default to localhost
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

/**
 * Configured axios instance with defaults for the Disease-Relater API
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout for risk calculations
});

/**
 * Response interceptor for centralized error handling
 * Logs errors and provides consistent error messages
 */
apiClient.interceptors.response.use(
  // Success - pass through
  (response) => response,
  
  // Error - log and transform
  (error: AxiosError<{ message?: string; detail?: string }>) => {
    // Extract error message from various possible locations
    const message = 
      error.response?.data?.message ||
      error.response?.data?.detail ||
      error.message ||
      'An unexpected error occurred';
    
    // Log for debugging (remove in production if needed)
    console.error(`API Error [${error.response?.status || 'NETWORK'}]:`, message);
    
    return Promise.reject(error);
  }
);

export default apiClient;
