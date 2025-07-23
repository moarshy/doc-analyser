'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Calendar, Activity, Globe, Settings, Play } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

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

export default function ProjectDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { apiClient } = useAuth();
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const projectId = params.id as string;

  useEffect(() => {
    const fetchProject = async () => {
      if (!apiClient || !projectId) return;

      try {
        const response = await apiClient.getProject(projectId);
        setProject(response.data);
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
            <Button className="flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white">
              <Play className="h-4 w-4" />
              Start Analysis
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
                <p className="text-sm font-medium opacity-70">Total Analyses</p>
                <p className="text-2xl font-bold">{project.job_count}</p>
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

      {/* Analysis Section */}
      <Card>
        <CardHeader>
          <CardTitle>Start New Analysis</CardTitle>
          <CardDescription>
            Analyze your documentation to identify issues and improvements
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="p-4 border border-dashed rounded-lg text-center opacity-70">
              <p className="mb-4 opacity-80">
                Ready to analyze documentation for this project?
              </p>
              <Button className="bg-green-600 hover:bg-green-700 text-white">
                <Play className="mr-2 h-4 w-4" />
                Start Analysis
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Analyses */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Analyses</CardTitle>
          <CardDescription>
            View the history and results of your documentation analyses
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 opacity-60">
            No analyses yet. Start your first analysis to see results here.
          </div>
        </CardContent>
      </Card>
    </div>
  );
}