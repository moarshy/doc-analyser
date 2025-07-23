'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Loader2 } from 'lucide-react';
import { useAuth } from '@/hooks/use-auth';

interface CreateProjectFormProps {
  onProjectCreated?: (project: any) => void;
  onCancel?: () => void;
}

export function CreateProjectForm({ onProjectCreated, onCancel }: CreateProjectFormProps) {
  const { apiClient } = useAuth();
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    repository_url: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      setError('Project name is required');
      return;
    }

    if (!apiClient) {
      setError('Authentication required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.createProject({
        name: formData.name.trim(),
        description: formData.description.trim() || undefined,
        repository_url: formData.repository_url.trim() || undefined,
        settings: {}
      });

      if (response.data) {
        onProjectCreated?.(response.data);
        
        // Reset form
        setFormData({
          name: '',
          description: '',
          repository_url: ''
        });
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 'Failed to create project';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (field: keyof typeof formData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (error) setError(null); // Clear error when user starts typing
  };

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Create New Project</CardTitle>
        <CardDescription>
          Create a project to organize your documentation analyses
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="p-3 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md">
              {error}
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="name">Project Name *</Label>
            <Input
              id="name"
              type="text"
              placeholder="My Documentation Project"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              maxLength={100}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="description">Description</Label>
            <Textarea
              id="description"
              placeholder="Optional description of your project..."
              value={formData.description}
              onChange={(e) => handleChange('description', e.target.value)}
              maxLength={500}
              rows={3}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="repository_url">Repository URL</Label>
            <Input
              id="repository_url"
              type="url"
              placeholder="https://github.com/username/repo (optional)"
              value={formData.repository_url}
              onChange={(e) => handleChange('repository_url', e.target.value)}
            />
          </div>

          <div className="flex gap-3 pt-4">
            <Button 
              type="submit" 
              disabled={isLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium px-8 py-2 rounded-lg shadow-sm border border-blue-600 hover:border-blue-700 disabled:border-blue-400 transition-all duration-200 hover:shadow-md disabled:cursor-not-allowed"
            >
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              Create Project
            </Button>
            {onCancel && (
              <Button 
                type="button" 
                onClick={onCancel}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-6 py-2 rounded-lg shadow-sm border border-gray-300 hover:border-gray-400 transition-all duration-200 hover:shadow-md"
              >
                Cancel
              </Button>
            )}
          </div>
        </form>
      </CardContent>
    </Card>
  );
}