'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Plus, Folder, Calendar, Activity, MoreVertical, Edit, Trash2 } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useAuth } from '@/hooks/use-auth';
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from '@/components/ui/dropdown-menu';
import { ConfirmationDialog } from '@/components/ui/confirmation-dialog';

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

interface ProjectListProps {
  onCreateProject?: () => void;
  onSelectProject?: (project: Project) => void;
  onEditProject?: (project: Project) => void;
  onDeleteProject?: (project: Project) => void;
}

export function ProjectList({ onCreateProject, onSelectProject, onEditProject, onDeleteProject }: ProjectListProps) {
  const { apiClient } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    project: Project | null;
    isDeleting: boolean;
  }>({
    isOpen: false,
    project: null,
    isDeleting: false
  });

  const fetchProjects = async () => {
    if (!apiClient) {
      setError('Authentication required');
      setIsLoading(false);
      return;
    }

    try {
      const response = await apiClient.getProjects();
      setProjects(response.data.projects || []);
    } catch (err: any) {
      setError('Failed to load projects');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (apiClient) {
      fetchProjects();
    }
  }, [apiClient]);

  const handleProjectCreated = (newProject: Project) => {
    setProjects(prev => [newProject, ...prev]);
  };

  const handleDeleteClick = (project: Project) => {
    setDeleteDialog({
      isOpen: true,
      project,
      isDeleting: false
    });
  };

  const handleDeleteConfirm = async () => {
    if (!apiClient || !deleteDialog.project) return;
    
    setDeleteDialog(prev => ({ ...prev, isDeleting: true }));
    
    try {
      await apiClient.deleteProject(deleteDialog.project.id);
      setProjects(prev => prev.filter(p => p.id !== deleteDialog.project!.id));
      onDeleteProject?.(deleteDialog.project);
      setDeleteDialog({ isOpen: false, project: null, isDeleting: false });
    } catch (err: any) {
      alert('Failed to delete project. Please try again.');
      setDeleteDialog(prev => ({ ...prev, isDeleting: false }));
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialog({ isOpen: false, project: null, isDeleting: false });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-10 w-32" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-full" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-4 w-1/2" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="text-center">
          <h3 className="text-lg font-medium text-gray-900 mb-2">Failed to load projects</h3>
          <p className="text-gray-500 mb-4">{error}</p>
          <Button 
            onClick={fetchProjects}
            className="bg-red-600 hover:bg-red-700 text-white font-medium px-6 py-2 rounded-lg shadow-sm border border-red-600 hover:border-red-700 transition-all duration-200 hover:shadow-md"
          >
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Projects</h1>
          <p className="text-gray-600 mt-1">Manage your documentation analysis projects</p>
        </div>
        <Button 
          onClick={onCreateProject}
          className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2 rounded-lg shadow-sm border border-blue-600 hover:border-blue-700 transition-all duration-200 hover:shadow-md"
        >
          <Plus className="mr-2 h-4 w-4" />
          New Project
        </Button>
      </div>

      {projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12">
          <Folder className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
          <p className="text-gray-500 mb-4">Create your first project to get started</p>
          <Button 
            onClick={onCreateProject}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-8 py-3 rounded-lg shadow-sm border border-blue-600 hover:border-blue-700 transition-all duration-200 hover:shadow-md hover:scale-105"
          >
            <Plus className="mr-2 h-4 w-4" />
            Create Project
          </Button>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <Card 
              key={project.id} 
              className="hover:shadow-md transition-shadow relative cursor-pointer"
              onClick={() => onSelectProject?.(project)}
            >
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <CardTitle className="text-lg">{project.name}</CardTitle>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>
                      {project.status}
                    </Badge>
                    <DropdownMenu>
                      <DropdownMenuTrigger 
                        className="p-1 hover:bg-gray-100 rounded"
                        onClick={(e: React.MouseEvent) => e.stopPropagation()}
                      >
                        <MoreVertical className="h-4 w-4 text-gray-500" />
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        <DropdownMenuItem 
                          onClick={(e: React.MouseEvent) => {
                            e.stopPropagation();
                            onEditProject?.(project);
                          }}
                        >
                          <Edit className="mr-2 h-4 w-4" />
                          Edit Project
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={(e: React.MouseEvent) => {
                            e.stopPropagation();
                            handleDeleteClick(project);
                          }}
                          className="text-red-600 hover:bg-red-50"
                        >
                          <Trash2 className="mr-2 h-4 w-4" />
                          Delete Project
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
                {project.description && (
                  <CardDescription className="line-clamp-2">
                    {project.description}
                  </CardDescription>
                )}
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    <span>{project.job_count} analyses</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4" />
                    <span>
                      Created {formatDistanceToNow(new Date(project.created_at), { addSuffix: true })}
                    </span>
                  </div>
                  {project.last_analysis_at && (
                    <div className="flex items-center gap-2">
                      <Activity className="h-4 w-4" />
                      <span>
                        Last analysis {formatDistanceToNow(new Date(project.last_analysis_at), { addSuffix: true })}
                      </span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Delete Confirmation Dialog */}
      <ConfirmationDialog
        isOpen={deleteDialog.isOpen}
        onClose={handleDeleteCancel}
        onConfirm={handleDeleteConfirm}
        title="Delete Project"
        description={`Are you sure you want to delete "${deleteDialog.project?.name}"? This action cannot be undone and will permanently remove all associated data.`}
        confirmText="Delete Project"
        cancelText="Cancel"
        variant="danger"
        isLoading={deleteDialog.isDeleting}
      />
    </div>
  );
}