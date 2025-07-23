'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { CreateProjectForm } from '@/components/projects/create-project-form';
import { EditProjectForm } from '@/components/projects/edit-project-form';
import { ProjectList } from '@/components/projects/project-list';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

type ViewMode = 'list' | 'create' | 'edit';

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

export default function ProjectsPage() {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [editingProject, setEditingProject] = useState<Project | null>(null);

  const handleCreateProject = () => {
    setViewMode('create');
  };

  const handleProjectCreated = (project: Project) => {
    setViewMode('list');
    // The ProjectList component will refresh automatically
  };

  const handleProjectUpdated = (project: Project) => {
    setViewMode('list');
    setEditingProject(null);
    // The ProjectList component will refresh automatically
  };

  const handleSelectProject = (project: Project) => {
    // Navigate to individual project page
    router.push(`/dashboard/projects/${project.id}`);
  };

  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    setViewMode('edit');
  };

  const handleBackToList = () => {
    setViewMode('list');
    setEditingProject(null);
  };

  return (
    <div>
      {/* Navigation Header */}
      {viewMode !== 'list' && (
        <div className="mb-6 flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBackToList}
            className="flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </Button>
          <h1 className="text-2xl font-bold">
            {viewMode === 'create' ? 'Create Project' : 'Edit Project'}
          </h1>
        </div>
      )}

      {/* Main Content */}
      <div>
        {viewMode === 'list' && (
          <ProjectList
            onCreateProject={handleCreateProject}
            onSelectProject={handleSelectProject}
            onEditProject={handleEditProject}
            onDeleteProject={(project) => {
              console.log(`Deleted project: ${project.name}`);
            }}
          />
        )}

        {viewMode === 'create' && (
          <CreateProjectForm
            onProjectCreated={handleProjectCreated}
            onCancel={handleBackToList}
          />
        )}

        {viewMode === 'edit' && editingProject && (
          <EditProjectForm
            project={editingProject}
            onProjectUpdated={handleProjectUpdated}
            onCancel={handleBackToList}
          />
        )}
      </div>
    </div>
  );
}