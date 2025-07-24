'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { ArrowLeft, Calendar, Activity, Globe, Settings, Play, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface AnalysisJob {
  job_id: string;
  status: string;
  repository: string;
  use_cases: any[];
  results?: any;
  error?: string;
  created_at: string;
  updated_at: string;
}

interface Project {
  id: string;
  name: string;
  description?: string;
  repository_url?: string;
  status: 'active' | 'archived' | 'deleted';
  created_at: string;
  updated_at: string;
  job_count: number;
  last_analysis_at?: string;
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case 'failed':
      return <AlertCircle className="h-4 w-4 text-red-500" />;
    case 'pending':
    case 'processing':
      return <Clock className="h-4 w-4 text-yellow-500" />;
    default:
      return <Activity className="h-4 w-4 text-gray-500" />;
  }
};

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'text-green-600';
    case 'failed':
      return 'text-red-600';
    case 'pending':
    case 'processing':
      return 'text-yellow-600';
    default:
      return 'text-gray-600';
  }
};

export default function ProjectDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { apiClient } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [analyses, setAnalyses] = useState<AnalysisJob[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingAnalyses, setIsLoadingAnalyses] = useState(false);
  
  // Analysis form state
  const [branch, setBranch] = useState('main');
  const [includeFolders, setIncludeFolders] = useState('docs');

  const projectId = params.id as string;

  useEffect(() => {
    const fetchProject = async () => {
      if (!apiClient || !projectId) return;

      try {
        const [projectResponse, analysesResponse] = await Promise.all([
          apiClient.getProject(projectId),
          apiClient.getProjectAnalyses(projectId)
        ]);
        setProject(projectResponse.data);
        setAnalyses(analysesResponse.data);
      } catch (err: any) {
        if (err.response?.status === 404) {
          setError('Project not found');
        } else {
          setError('Failed to load project');
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchProject();
  }, [apiClient, projectId]);

  const handleBack = () => {
    router.push('/dashboard/projects');
  };

  const handleEdit = () => {
    router.push(`/dashboard/projects/${projectId}/edit`);
  };

  const handleStartAnalysis = async () => {
    if (!apiClient || !project) return;
    
    if (!project.repository_url) {
      alert('Please set a repository URL in the project settings before starting analysis.');
      return;
    }
    
    if (!branch.trim()) {
      alert('Please specify a branch name.');
      return;
    }
    
    if (!includeFolders.trim()) {
      alert('Please specify at least one folder to include.');
      return;
    }
    
    setIsLoadingAnalyses(true);
    try {
      // Parse include folders as comma-separated values
      const foldersArray = includeFolders.split(',').map(f => f.trim()).filter(f => f.length > 0);
      
      const response = await apiClient.startAnalysis({
        url: project.repository_url,
        branch: branch.trim(),
        include_folders: foldersArray,
        project_id: projectId,
      });
      
      // Redirect to the analysis progress page
      router.push(`/dashboard/analyses/${response.data.job_id}`);
    } catch (error: any) {
      console.error('Failed to start analysis:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to start analysis. Please check the repository URL and try again.';
      alert(errorMessage);
    } finally {
      setIsLoadingAnalyses(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error || !project) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="text-center">
          <h3 className="text-lg font-medium mb-2">
            {error || 'Project not found'}
          </h3>
          <Button onClick={handleBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Projects
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg shadow-sm border p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              onClick={handleBack}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Projects
            </Button>
            <div>
              <div className="flex items-center gap-3">
                <h1 className="text-4xl font-bold">{project.name}</h1>
                <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
                  {project.status}
                </Badge>
              </div>
              {project.description && (
                <p className="text-lg font-medium mt-2 opacity-80">{project.description}</p>
              )}
            </div>
          </div>
          <div className="flex gap-3">
            <Button 
              onClick={handleEdit} 
              variant="outline"
              className="flex items-center gap-2"
            >
              <Settings className="h-4 w-4" />
              Edit Project
            </Button>
          </div>
        </div>
      </div>

      {/* Project Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-blue-600" />
              <div className="ml-4">
                <p className="text-sm font-medium opacity-70">Analysis Status</p>
                <p className="text-2xl font-bold">
                  {project.job_count > 0 ? 'Active' : 'No Analysis'}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Calendar className="h-8 w-8 text-green-600" />
              <div className="ml-4">
                <p className="text-sm font-medium opacity-70">Created</p>
                <p className="text-2xl font-bold">
                  {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Activity className="h-8 w-8 text-purple-600" />
              <div className="ml-4">
                <p className="text-sm font-medium opacity-70">Last Analysis</p>
                <p className="text-2xl font-bold">
                  {project.last_analysis_at 
                    ? formatDistanceToNow(new Date(project.last_analysis_at), { addSuffix: true })
                    : 'Never'
                  }
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-6">
            <div className="flex items-center">
              <Globe className="h-8 w-8 text-orange-600" />
              <div className="ml-4">
                <p className="text-sm font-medium opacity-70">Repository</p>
                <p className="text-sm font-bold truncate">
                  {project.repository_url ? (
                    <a 
                      href={project.repository_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300 hover:underline"
                    >
                      View Repository
                    </a>
                  ) : (
                    <span className="opacity-60">Not set</span>
                  )}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Analysis Section - Show input form for starting analysis */}
      <Card>
        <CardHeader>
          <CardTitle>Start New Analysis</CardTitle>
          <CardDescription>
            Analyze your documentation to identify issues and improvements
          </CardDescription>
        </CardHeader>
        <CardContent>
          {project.repository_url ? (
            <div className="space-y-6">
              {/* Analysis Configuration Form */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="branch">Git Branch</Label>
                  <Input
                    id="branch"
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    placeholder="main"
                    className="w-full"
                    disabled={isLoadingAnalyses}
                  />
                  <p className="text-sm text-gray-500">
                    Specify which branch to analyze (e.g., main, develop)
                  </p>
                </div>
                
                <div className="space-y-2">
                  <Label htmlFor="includeFolders">Include Folders</Label>
                  <Input
                    id="includeFolders"
                    value={includeFolders}
                    onChange={(e) => setIncludeFolders(e.target.value)}
                    placeholder="docs, README.md"
                    className="w-full"
                    disabled={isLoadingAnalyses}
                  />
                  <p className="text-sm text-gray-500">
                    Comma-separated list of folders/files to analyze
                  </p>
                </div>
              </div>
              
              {/* Repository Info */}
              <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Globe className="h-4 w-4 text-gray-500" />
                  <span className="font-medium text-sm">Repository:</span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 break-all">
                  {project.repository_url}
                </p>
              </div>
              
              {/* Start Button */}
              <div className="flex justify-center">
                <Button 
                  onClick={handleStartAnalysis}
                  disabled={isLoadingAnalyses || !branch.trim() || !includeFolders.trim()}
                  className="bg-green-600 hover:bg-green-700 text-white px-8 py-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Play className="mr-2 h-4 w-4" />
                  {isLoadingAnalyses ? 'Starting Analysis...' : 'Start Analysis'}
                </Button>
              </div>
            </div>
          ) : (
            <div className="p-4 border border-dashed rounded-lg text-center opacity-70">
              <p className="mb-4 opacity-80">
                Please set a repository URL in your project settings to start analysis.
              </p>
              <Button 
                onClick={handleEdit}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                <Settings className="mr-2 h-4 w-4" />
                Edit Project Settings
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Analyses */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Analyses ({analyses.length})</CardTitle>
          <CardDescription>
            View the history and results of your documentation analyses
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingAnalyses ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
          ) : analyses.length === 0 ? (
            <div className="text-center py-8 opacity-60">
              No analyses yet. Start your first analysis to see results here.
            </div>
          ) : (
            <div className="space-y-4">
              {analyses.map((analysis) => (
                <div key={analysis.job_id} className="border rounded-lg p-4 hover:bg-slate-50/50 dark:hover:bg-slate-800/50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getStatusIcon(analysis.status)}
                      <div>
                        <p className="font-medium">{analysis.repository}</p>
                        <p className="text-sm opacity-70">
                          {analysis.use_cases?.length || 0} use cases
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant={analysis.status === 'completed' ? 'default' : 'secondary'}>
                        {analysis.status}
                      </Badge>
                      <p className="text-sm opacity-70">
                        {analysis.created_at 
                          ? formatDistanceToNow(new Date(analysis.created_at), { addSuffix: true })
                          : 'Unknown date'
                        }
                      </p>
                    </div>
                  </div>
                  <div className="mt-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => router.push(`/dashboard/analyses/${analysis.job_id}`)}
                    >
                      View Details
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}