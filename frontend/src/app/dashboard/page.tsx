'use client';

import { useAuth } from '@/hooks/use-auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, FolderOpen, Activity } from 'lucide-react';
import Link from 'next/link';
import { useState, useEffect } from 'react';

interface DashboardStats {
  totalProjects: number;
  completedAnalyses: number;
}

export default function DashboardOverview() {
  const { user, isLoading, apiClient } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalProjects: 0,
    completedAnalyses: 0,
  });
  const [statsLoading, setStatsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      if (!apiClient || !user) return;
      
      try {
        const projectsResponse = await apiClient.getProjects();
        const projects = projectsResponse.data.projects || [];
        
        // Calculate stats from projects
        const totalProjects = projects.length;
        const completedAnalyses = projects.reduce((sum: number, project: any) => sum + (project.job_count || 0), 0);
        
        setStats({
          totalProjects,
          completedAnalyses,
        });
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
      } finally {
        setStatsLoading(false);
      }
    };

    fetchStats();
  }, [apiClient, user]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Please log in</h1>
          <p className="text-gray-600">You need to be logged in to access the dashboard.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="mb-8 p-6 rounded-lg border border-opacity-20">
        <h1 className="text-4xl font-bold mb-2">
          Welcome back, {user.name}! 👋
        </h1>
        <p className="text-lg font-medium opacity-80">
          Ready to analyze your documentation? Here's what's happening with your projects.
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="border-blue-500 border-opacity-30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-blue-400 mb-1">Total Projects</p>
                <p className="text-3xl font-bold">{statsLoading ? '...' : stats.totalProjects}</p>
                <p className="text-xs opacity-70 mt-1">Active projects</p>
              </div>
              <div className="p-3 bg-blue-500 bg-opacity-20 rounded-full">
                <FolderOpen className="h-8 w-8 text-blue-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-green-500 border-opacity-30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-400 mb-1">Completed Analyses</p>
                <p className="text-3xl font-bold">{statsLoading ? '...' : stats.completedAnalyses}</p>
                <p className="text-xs opacity-70 mt-1">Successfully finished</p>
              </div>
              <div className="p-3 bg-green-500 bg-opacity-20 rounded-full">
                <Activity className="h-8 w-8 text-green-400" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Get Started</CardTitle>
            <CardDescription>
              Create your first project to start analyzing documentation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Link href="/dashboard/projects">
                <Button className="w-full" size="lg">
                  <Plus className="mr-2 h-5 w-5" />
                  Create New Project
                </Button>
              </Link>
              <p className="text-sm text-gray-500 text-center">
                Or browse your existing projects
              </p>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>How to Analyze Your Docs</CardTitle>
            <CardDescription>
              Follow these steps to get insights into your documentation quality
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-sm font-semibold">
                  1
                </div>
                <div>
                  <h4 className="font-medium text-sm">Create a Project</h4>
                  <p className="text-xs text-slate-600 dark:text-slate-400">Set up a new project to organize your documentation analysis</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400 rounded-full flex items-center justify-center text-sm font-semibold">
                  2
                </div>
                <div>
                  <h4 className="font-medium text-sm">Run Analysis</h4>
                  <p className="text-xs text-slate-600 dark:text-slate-400">Start the automated analysis process on your repository</p>
                </div>
              </div>
              
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 w-6 h-6 bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-400 rounded-full flex items-center justify-center text-sm font-semibold">
                  3
                </div>
                <div>
                  <h4 className="font-medium text-sm">What Happens During Analysis</h4>
                  <div className="text-xs text-slate-600 dark:text-slate-400 space-y-1 mt-1">
                    <p>• Clone the repo and set to your selected branch</p>
                    <p>• Use coding agent to extract use cases from docs</p>
                    <p>• Execute all different extracted use cases</p>
                    <p>• Agent learns strengths and weak points of docs</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

    </div>
  );
}