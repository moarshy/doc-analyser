import axios, { AxiosInstance } from 'axios';

class ApiClient {
  private client: AxiosInstance;
  private getAccessToken: () => Promise<string>;

  constructor(getAccessToken: () => Promise<string>) {
    this.getAccessToken = getAccessToken;
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, ''),
      timeout: 30000,
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      async (config) => {
        try {
          const token = await this.getAccessToken();
          if (token) {
            config.headers.Authorization = `Bearer ${token}`;
          }
          return config;
        } catch (error) {
          console.error('Error getting access token:', error);
          return config;
        }
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid, redirect to login
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // User management - use ID token data for user sync  
  async syncUser(userData: {
    auth0_id: string;
    email: string;
    name?: string;
    picture?: string;
  }) {
    return this.client.post('/auth/sync-user', userData);
  }

  async getCurrentUser() {
    return this.client.get('/auth/me');
  }

  async validateToken() {
    return this.client.get('/auth/validate');
  }

  // Project management
  async createProject(projectData: {
    name: string;
    description?: string;
    repository_url?: string;
    settings?: Record<string, any>;
  }) {
    return this.client.post('/projects/', projectData);
  }

  async getProjects() {
    return this.client.get('/projects/');
  }

  async getProject(id: string) {
    return this.client.get(`/projects/${id}`);
  }

  async updateProject(id: string, projectData: {
    name?: string;
    description?: string;
    repository_url?: string;
    settings?: Record<string, any>;
  }) {  
    return this.client.put(`/projects/${id}`, projectData);
  }

  async deleteProject(id: string) {
    return this.client.delete(`/projects/${id}`);
  }

  async getProjectJobs(id: string) {
    return this.client.get(`/projects/${id}/jobs`);
  }

  async getProjectAnalyses(projectId: string) {
    return this.client.get(`/analysis/project/${projectId}/jobs`);
  }

  // Analysis management
  async startAnalysis(analysisData: {
    url: string;
    branch?: string;
    include_folders?: string[];
    project_id?: string;
  }) {
    return this.client.post('/analysis/analyze', analysisData);
  }

  async getAnalysisStatus(jobId: string) {
    return this.client.get(`/analysis/status/${jobId}`);
  }

  async getAnalysisDetail(jobId: string) {
    return this.client.get(`/analysis/jobs/${jobId}/detail`);
  }

  async getAnalysisFile(jobId: string, filename: string) {
    return this.client.get(`/analysis/jobs/${jobId}/files/${filename}`, {
      responseType: 'text'
    });
  }

  async getAnalyses() {
    return this.client.get('/analysis/jobs');
  }
}

export default ApiClient;