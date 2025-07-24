'use client';

import { useAuth } from '@/hooks/use-auth';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Plus, FolderOpen, Activity, BarChart3, Clock } from 'lucide-react';
import Link from 'next/link';
import { useState, useEffect } from 'react';

interface DashboardStats {
  totalProjects: number;
  completedAnalyses: number;
  pendingJobs: number;
  issuesFound: number;
}

export default function DashboardOverview() {
  const { user, isLoading, apiClient } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    totalProjects: 0,
    completedAnalyses: 0,
    pendingJobs: 0,
    issuesFound: 0
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
        
        // For now, set pending jobs and issues to 0 since we don't have that data yet
        setStats({
          totalProjects,
          completedAnalyses,
          pendingJobs: 0,
          issuesFound: 0
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
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

        <Card className="border-yellow-500 border-opacity-30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-yellow-400 mb-1">Pending Jobs</p>
                <p className="text-3xl font-bold">{statsLoading ? '...' : stats.pendingJobs}</p>
                <p className="text-xs opacity-70 mt-1">In queue</p>
              </div>
              <div className="p-3 bg-yellow-500 bg-opacity-20 rounded-full">
                <Clock className="h-8 w-8 text-yellow-400" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="border-purple-500 border-opacity-30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-400 mb-1">Issues Found</p>
                <p className="text-3xl font-bold">{statsLoading ? '...' : stats.issuesFound}</p>
                <p className="text-xs opacity-70 mt-1">Documentation issues</p>
              </div>
              <div className="p-3 bg-purple-500 bg-opacity-20 rounded-full">
                <BarChart3 className="h-8 w-8 text-purple-400" />
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
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>
              Your latest project activities and analysis results
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8 opacity-60">
              <Activity className="h-12 w-12 opacity-40 mx-auto mb-4" />
              <p>No recent activity</p>
              <p className="text-sm">Start your first analysis to see activity here</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Navigation Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Link href="/dashboard/projects">
          <Card className="cursor-pointer hover:shadow-md transition-shadow">
            <CardContent className="p-6 text-center">
              <FolderOpen className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">Projects</h3>
              <p className="opacity-70">Manage your documentation projects</p>
            </CardContent>
          </Card>
        </Link>

        <Card className="cursor-pointer hover:shadow-md transition-shadow opacity-50">
          <CardContent className="p-6 text-center">
            <Activity className="h-12 w-12 text-green-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Analyses</h3>
            <p className="opacity-70">View analysis results and reports</p>
            <p className="text-xs opacity-50 mt-2">Coming soon</p>
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:shadow-md transition-shadow opacity-50">
          <CardContent className="p-6 text-center">
            <BarChart3 className="h-12 w-12 text-purple-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Reports</h3>
            <p className="opacity-70">Export and share analysis reports</p>
            <p className="text-xs opacity-50 mt-2">Coming soon</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}