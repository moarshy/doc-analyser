'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { EditProjectForm } from '@/components/projects/edit-project-form';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

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

export default function EditProjectPage() {
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

  const handleProjectUpdated = (updatedProject: Project) => {
    setProject(updatedProject);
    // Redirect back to project details after successful update
    router.push(`/dashboard/projects/${projectId}`);
  };

  const handleCancel = () => {
    router.push(`/dashboard/projects/${projectId}`);
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
          <Button onClick={() => router.push('/dashboard/projects')}>
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
      <div className="flex items-center gap-4 mb-6">
        <Button
          variant="ghost"
          onClick={handleCancel}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Project
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Edit Project</h1>
          <p className="text-gray-600 mt-1">Update your project information</p>
        </div>
      </div>

      {/* Edit Form */}
      <EditProjectForm
        project={project}
        onProjectUpdated={handleProjectUpdated}
        onCancel={handleCancel}
      />
    </div>
  );
}