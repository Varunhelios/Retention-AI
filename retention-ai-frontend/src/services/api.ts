import axios from 'axios';

// Update the base URL to point to our FastAPI backend
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with base URL and common headers
const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,  // Important for cookies, authorization headers with CORS
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Response interceptor to handle common errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Handle different HTTP status codes
      switch (error.response.status) {
        case 401:
          console.error('Unauthorized access - please login');
          break;
        case 403:
          console.error('Forbidden - insufficient permissions');
          break;
        case 404:
          console.error('Resource not found');
          break;
        case 500:
          console.error('Server error - please try again later');
          break;
        default:
          console.error('An error occurred');
      }
    } else if (error.request) {
      // The request was made but no response was received
      console.error('No response from server - please check your connection');
    } else {
      // Something happened in setting up the request
      console.error('Request setup error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Health Check API
export const healthAPI = {
  check: () => api.get('/api/health'),
};

// Data Upload API
export const uploadAPI = {
  uploadFile: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    return api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
};

// Types for our API responses
export interface User {
  user_id: string;
  churn_probability: number;
  risk_level: string;
}

export interface FeatureImportance {
  name: string;
  importance: number;
  rank: number;
}

export interface UserExplanation {
  user_id: string;
  churn_probability: number;
  risk_level: string;
  top_features: Array<{
    feature: string;
    value: number;
    shap_value: number;
    model: string;
  }>;
  recommendations: string[];
  chart_path?: string;
  model_b_used?: boolean;
}

// Churn Prediction API
export const churnAPI = {
  // Get list of all users with their churn risk
  getUsers: async (): Promise<User[]> => {
    try {
      const response = await api.get('/api/users');
      return response.data;
    } catch (error) {
      console.error('Error fetching users:', error);
      throw error;
    }
  },
  
  getUserExplanation: async (userId: string): Promise<{ data: UserExplanation }> => {
    try {
      const response = await api.get(`/api/user/${userId}/explanation`);
      
      // Transform the backend response to match the frontend's expected format
      const backendData = response.data;
      
      // Ensure top_features is an array and has the correct structure
      const topFeatures = Array.isArray(backendData.top_factors || backendData.top_features) 
        ? (backendData.top_factors || backendData.top_features).map((factor: any) => ({
            feature: factor.feature || 'Unknown',
            value: factor.value || 0,
            shap_value: factor.shap_value || factor.impact || 0,
            model: factor.model || 'Model A',
            description: factor.description || 'No description available',
            impact: Math.abs(factor.shap_value || factor.impact || 0)
          }))
        : [];
      
      // Ensure recommendations is an array
      const recommendations = Array.isArray(backendData.recommendations)
        ? backendData.recommendations
        : [];
      
      // Construct the response in the expected format
      const formattedResponse: UserExplanation = {
        user_id: String(backendData.user_id || userId),  // Ensure user_id is a string
        churn_probability: backendData.churn_probability || 0,
        risk_level: backendData.risk_level || 'unknown',
        top_features: topFeatures,
        recommendations: recommendations,
        chart_path: backendData.chart_path || '',
        model_b_used: backendData.model_b_used || false
      };
      
      return { data: formattedResponse };
    } catch (error) {
      console.error('Error fetching user explanation:', error);
      // Return a default response in case of error
      return {
        data: {
          user_id: userId,
          churn_probability: 0,
          risk_level: 'error',
          top_features: [],
          recommendations: ['Failed to load explanation. Please try again.'],
          chart_path: '',
          model_b_used: false
        }
      };
    }
  },
  
  getChurnPredictions: async () => {
    try {
      const response = await api.get<{
        data: Array<{
          userid: string;
          'churn_probability (%)': number;
          churn_risk: string;
        }>;
      }>('/api/churn-predictions');
      return { data: response.data };
    } catch (error) {
      console.error('Error fetching churn predictions:', error);
      throw error;
    }
  },
  
  // The getUserExplanation function is now defined above with proper error handling and response transformation
    
  getFeatureImportance: async () => {
    try {
      const response = await api.get<{
        features: FeatureImportance[];
        chart_path?: string;
      }>('/api/feature-importance');
      return { data: response.data };
    } catch (error) {
      console.error('Error fetching feature importance:', error);
      throw error;
    }
  },
};

// Sentiment Analysis API
export const sentimentAPI = {
  getSentimentData: () => api.get('/api/sentiment'),
  getSentimentStats: () => api.get('/sentiment/stats'),
};

// Dashboard API
export const dashboardAPI = {
  getStats: () => api.get('/api/dashboard/stats'),
};

// Retention Strategies API
export const retentionAPI = {
  sendEmail: async (emailData: {
    email: string;
    subject: string;
    message: string;
    userIds: string[];
  }) => {
    try {
      const response = await api.post('/api/send-retention-email', emailData);
      return response.data;
    } catch (error) {
      console.error('Error sending retention email:', error);
      throw error;
    }
  },
  
  createStrategy: (strategyData: any) =>
    Promise.resolve({ data: { success: true, message: 'Strategy created' } }),
  getStrategies: () =>
    Promise.resolve({ data: [] }),
  getStrategy: (id: string) =>
    Promise.resolve({ data: null }),
  updateStrategy: (id: string, updates: any) =>
    Promise.resolve({ data: { success: true, message: 'Strategy updated' } }),
  deleteStrategy: (id: string) =>
    Promise.resolve({ data: { success: true, message: 'Strategy deleted' } }),
  getSuggestedStrategies: () =>
    Promise.resolve({ data: [] }),
  getStrategyPerformance: (strategyId: string) =>
    Promise.resolve({ data: {} }),
};

// User Management API
export const userAPI = {
  getProfile: () => api.get('/users/me'),
  updateProfile: (updates: any) => api.put('/users/me', updates),
  changePassword: (currentPassword: string, newPassword: string) =>
    api.post('/users/change-password', { currentPassword, newPassword }),
};

// Analytics API
export const analyticsAPI = {
  getRetentionMetrics: (timeRange: string = '30d') =>
    api.get(`/analytics/retention?range=${timeRange}`),
  getChurnAnalysis: (timeRange: string = '30d') =>
    api.get(`/analytics/churn?range=${timeRange}`),
  getEngagementMetrics: (timeRange: string = '30d') =>
    api.get(`/analytics/engagement?range=${timeRange}`),
  getCustomerSegments: () => api.get('/analytics/segments'),
};

export default api;
