# Frontend Architecture Plan

## Overview

This document outlines the complete architecture for the Doc Analyser frontend - a modern Next.js application with Auth0 authentication, project management, and real-time analysis monitoring.

## 🏗️ Project Structure & Tech Stack

### Directory Structure
```
frontend/
├── src/
│   ├── app/                    # App Router (Next.js 13+)
│   │   ├── (auth)/            # Auth group routes
│   │   │   ├── login/         # Login page
│   │   │   └── signup/        # Signup page
│   │   ├── dashboard/         # Protected dashboard routes
│   │   │   ├── page.tsx       # Dashboard home
│   │   │   ├── projects/      # Project management
│   │   │   │   ├── page.tsx   # Projects list
│   │   │   │   ├── new/       # Create new project
│   │   │   │   └── [id]/      # Project details
│   │   │   └── analysis/      # Analysis results
│   │   │       ├── page.tsx   # Analysis list
│   │   │       └── [id]/      # Analysis details
│   │   ├── api/              # API routes
│   │   │   ├── auth/         # Auth endpoints
│   │   │   └── projects/     # Project API routes
│   │   ├── globals.css       # Global styles
│   │   ├── layout.tsx        # Root layout
│   │   └── page.tsx          # Landing page
│   ├── components/
│   │   ├── ui/               # Reusable UI components
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── card.tsx
│   │   │   └── modal.tsx
│   │   ├── auth/            # Authentication components
│   │   │   ├── login-button.tsx
│   │   │   ├── logout-button.tsx
│   │   │   └── profile.tsx
│   │   ├── dashboard/       # Dashboard components
│   │   │   ├── sidebar.tsx
│   │   │   ├── header.tsx
│   │   │   ├── project-card.tsx
│   │   │   └── analysis-progress.tsx
│   │   └── landing/         # Landing page components
│   │       ├── hero.tsx
│   │       ├── features.tsx
│   │       ├── how-it-works.tsx
│   │       └── cta.tsx
│   ├── lib/
│   │   ├── auth0.ts         # Auth0 configuration
│   │   ├── api.ts           # Backend API client
│   │   ├── types.ts         # TypeScript definitions
│   │   └── utils.ts         # Utility functions
│   ├── hooks/               # Custom React hooks
│   │   ├── use-auth.ts      # Auth state management
│   │   ├── use-projects.ts  # Project data fetching
│   │   └── use-analysis.ts  # Analysis status polling
│   └── store/               # State management
│       ├── auth-store.ts    # Auth state
│       └── project-store.ts # Project state
├── public/
│   ├── images/              # Static images
│   ├── icons/               # Icon assets
│   └── favicon.ico
├── package.json
├── next.config.js
├── tailwind.config.js
└── tsconfig.json
```

### Technology Stack
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Authentication**: Auth0 React SDK
- **Data Fetching**: TanStack Query (React Query)
- **State Management**: Zustand
- **UI Components**: Custom components with Headless UI
- **Icons**: Lucide React
- **Deployment**: Vercel

## 🔐 Authentication Strategy

### Auth0 Configuration
```typescript
// lib/auth0.ts
import { UserProvider } from '@auth0/auth0-react';

export const auth0Config = {
  domain: process.env.NEXT_PUBLIC_AUTH0_DOMAIN!,
  clientId: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID!,
  authorizationParams: {
    redirect_uri: typeof window !== 'undefined' ? window.location.origin : '',
    audience: process.env.NEXT_PUBLIC_AUTH0_AUDIENCE, // Backend API identifier
    scope: 'openid profile email'
  }
};
```

### Authentication Flow
1. **Landing Page** → Login/Signup buttons trigger Auth0 Universal Login
2. **Auth0 Redirect** → User completes authentication
3. **Token Storage** → JWT tokens stored securely in memory/httpOnly cookies
4. **Protected Routes** → Middleware checks authentication status
5. **API Calls** → Include Bearer token for backend communication

### Route Protection
```typescript
// middleware.ts
import { withAuth } from "next-auth/middleware";

export default withAuth({
  pages: {
    signIn: "/login",
  },
});

export const config = {
  matcher: ["/dashboard/:path*"]
};
```

## 🎨 User Interface Design

### Landing Page Sections

#### 1. Hero Section
- **Headline**: "Analyze Your Documentation Quality with AI"
- **Subheadline**: "Automatically extract use cases, validate examples, and improve your docs"
- **CTA**: "Start Analyzing" → Auth0 signup
- **Visual**: Dashboard preview or code analysis visualization

#### 2. Features Section
- **Use Case Extraction**: AI-powered identification of practical scenarios
- **Code Validation**: Automatic testing of documentation examples
- **Quality Reports**: Comprehensive analysis with improvement suggestions
- **Multi-Repository**: Support for various project types and languages

#### 3. How It Works
- **Step 1**: Connect your repository
- **Step 2**: AI analyzes documentation
- **Step 3**: Get actionable insights

#### 4. Call to Action
- **Primary**: "Get Started for Free"
- **Secondary**: "View Sample Report"

### Dashboard Layout

#### Sidebar Navigation
- Dashboard (overview)
- Projects (list/manage)
- Analysis (results)
- Settings (user preferences)

#### Main Content Areas
- **Overview**: Recent activity, analysis stats
- **Projects**: Grid of project cards with status
- **Analysis**: Detailed results with metrics and reports

## 📁 Project Management Workflow

### Project Creation Form
```typescript
interface ProjectFormData {
  name: string;
  description?: string;
  repository_url: string;
  branch: string;
  include_folders: string[];
  analysis_frequency?: 'manual' | 'weekly' | 'monthly';
}
```

### Form Fields
- **Project Name**: User-friendly identifier
- **Repository URL**: GitHub/GitLab repository
- **Branch**: Target branch (default: main)
- **Include Folders**: Multi-select (docs, README, guides, etc.)
- **Description**: Optional project description

### Project Card Display
```typescript
interface ProjectCard {
  id: string;
  name: string;
  repository_url: string;
  last_analysis: Date | null;
  analysis_status: 'pending' | 'running' | 'completed' | 'failed';
  documentation_score?: number;
  use_cases_count?: number;
}
```

## 🔗 Backend Integration

### API Client Architecture
```typescript
// lib/api.ts
class ApiClient {
  private baseURL = process.env.NEXT_PUBLIC_API_URL;
  
  constructor(private getAccessToken: () => Promise<string>) {}
  
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = await this.getAccessToken();
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      throw new ApiError(response.status, response.statusText);
    }
    
    return response.json();
  }
  
  // Project endpoints
  async createProject(data: ProjectFormData): Promise<Project> {
    return this.request('/api/projects', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
  
  async getProjects(): Promise<Project[]> {
    return this.request('/api/projects');
  }
  
  async getProject(id: string): Promise<Project> {
    return this.request(`/api/projects/${id}`);
  }
  
  // Analysis endpoints
  async startAnalysis(projectId: string): Promise<AnalysisJob> {
    return this.request('/api/analyze', {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId }),
    });
  }
  
  async getAnalysisStatus(jobId: string): Promise<AnalysisJob> {
    return this.request(`/api/jobs/${jobId}/status`);
  }
  
  async getAnalysisResults(jobId: string): Promise<AnalysisResults> {
    return this.request(`/api/jobs/${jobId}/results`);
  }
}
```

### Real-time Updates
```typescript
// hooks/use-analysis-polling.ts
export function useAnalysisPolling(jobId: string) {
  return useQuery({
    queryKey: ['analysis', jobId],
    queryFn: () => apiClient.getAnalysisStatus(jobId),
    refetchInterval: (data) => {
      // Poll every 5 seconds if analysis is running
      return data?.status === 'running' ? 5000 : false;
    },
    enabled: !!jobId,
  });
}
```

## 🛡️ Security & Performance

### Security Measures
- **JWT Validation**: All API calls include verified tokens
- **CSRF Protection**: Built-in Next.js CSRF protection
- **Input Validation**: Client and server-side validation
- **Rate Limiting**: API rate limits for abuse prevention
- **Secure Storage**: No sensitive data in localStorage

### Performance Optimizations
- **Server-Side Rendering**: Landing page for SEO
- **Code Splitting**: Dynamic imports for dashboard components
- **Image Optimization**: Next.js automatic image optimization
- **Caching**: TanStack Query for intelligent data caching
- **Bundle Analysis**: Regular bundle size monitoring

### Error Handling
```typescript
// lib/error-handler.ts
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public details?: any
  ) {
    super(`API Error: ${status} ${statusText}`);
  }
}

export function handleApiError(error: ApiError) {
  switch (error.status) {
    case 401:
      // Redirect to login
      window.location.href = '/login';
      break;
    case 403:
      // Show unauthorized message
      toast.error('You are not authorized to perform this action');
      break;
    case 500:
      // Show generic error
      toast.error('Something went wrong. Please try again.');
      break;
    default:
      toast.error(error.message);
  }
}
```

## 🚀 Deployment & Production

### Environment Configuration
```bash
# .env.local
NEXT_PUBLIC_AUTH0_DOMAIN=your-auth0-domain.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID=your-client-id
NEXT_PUBLIC_AUTH0_AUDIENCE=https://your-api-identifier
NEXT_PUBLIC_API_URL=https://your-backend-api.com
```

### Vercel Deployment
- **Automatic Deployments**: GitHub integration
- **Environment Variables**: Secure configuration management
- **Preview Deployments**: Branch-based previews
- **Analytics**: Built-in performance monitoring

### CI/CD Pipeline
```yaml
# .github/workflows/frontend.yml
name: Frontend CI/CD
on:
  push:
    branches: [main]
    paths: ['frontend/**']
  pull_request:
    paths: ['frontend/**']

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: cd frontend && npm ci
      
      - name: Run tests
        run: cd frontend && npm test
      
      - name: Run build
        run: cd frontend && npm run build
```

## 📊 Analytics & Monitoring

### User Analytics
- **Page Views**: Track popular features
- **User Journey**: Funnel analysis from landing to analysis
- **Feature Usage**: Monitor project creation and analysis frequency

### Performance Monitoring
- **Core Web Vitals**: Lighthouse metrics
- **Bundle Size**: Track JavaScript bundle growth
- **API Response Times**: Monitor backend integration performance

### Error Tracking
- **Sentry Integration**: Real-time error reporting
- **User Feedback**: In-app feedback collection
- **Performance Issues**: Slow query detection

## 🔄 Complete User Journey

### New User Flow
1. **Landing Page** → Learn about documentation analysis
2. **Sign Up** → Auth0 registration with email verification
3. **Onboarding** → Welcome screen with quick tutorial
4. **First Project** → Guided project creation flow
5. **Analysis Start** → Trigger first documentation analysis
6. **Results** → View comprehensive analysis report

### Returning User Flow
1. **Login** → Auth0 authentication
2. **Dashboard** → Overview of projects and recent activity
3. **Project Management** → Create, edit, or analyze projects
4. **Analysis Monitoring** → Real-time progress tracking
5. **Results Review** → Detailed reports and insights

### Project Lifecycle
1. **Creation** → Repository connection and configuration
2. **Analysis** → Automated documentation processing
3. **Results** → Quality metrics and improvement suggestions
4. **Iteration** → Re-analysis after documentation updates
5. **Sharing** → Export reports or share insights

## 🎯 Success Metrics

### User Engagement
- **User Registration Rate**: Landing page to signup conversion
- **Project Creation Rate**: Users who create their first project
- **Analysis Completion Rate**: Projects that complete analysis
- **Return User Rate**: Users who return within 30 days

### Product Metrics
- **Analysis Success Rate**: Percentage of successful analyses
- **Documentation Improvement**: Before/after quality scores
- **User Satisfaction**: NPS scores and feedback ratings
- **Feature Adoption**: Usage of advanced features

This architecture provides a solid foundation for a production-ready frontend that scales with user needs while maintaining excellent performance and user experience.