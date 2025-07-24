'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, Clock, CheckCircle, AlertCircle, Activity, Globe, ChevronRight } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface AnalysisJob {
  job_id: string;
  status: string;
  repository: string;
  branch: string;
  include_folders: string[];
  use_cases: any[];
  results?: any;
  error?: string;
  created_at: string;
  updated_at: string;
  project_id?: string;
}

interface DemoAnalysis {
  job_id: string;
  name: string;
  repository: string;
  branch: string;
  status: 'completed';
  use_cases_count: number;
  created_at: string;
  is_demo: boolean;
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

export default function AnalysesListPage() {
  const router = useRouter();
  const { apiClient, isAuthenticated } = useAuth();
  const [analyses, setAnalyses] = useState<AnalysisJob[]>([]);
  const [demoAnalysis, setDemoAnalysis] = useState<DemoAnalysis | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAnalyses = async () => {
      setIsLoading(true);
      
      try {
        // Load demo analysis
        const demoResponse = await fetch('/demo/job.json');
        const demoData = await demoResponse.json();
        
        setDemoAnalysis({
          job_id: 'demo-guardrails-project',
          name: 'Guardrails AI Demo',
          repository: 'https://github.com/guardrails-ai/guardrails',
          branch: 'main',
          status: 'completed',
          use_cases_count: demoData.total_use_cases,
          created_at: new Date().toISOString(),
          is_demo: true
        });

        // Load user's analyses if authenticated
        if (isAuthenticated && apiClient) {
          try {
            const response = await apiClient.client.get('/analysis/jobs');
            setAnalyses(response.data || []);
          } catch (err) {
            console.error('Failed to load user analyses:', err);
          }
        }
      } catch (err) {
        console.error('Failed to load analyses:', err);
        setError('Failed to load analyses');
      } finally {
        setIsLoading(false);
      }
    };

    loadAnalyses();
  }, [apiClient, isAuthenticated]);

  const handleBack = () => {
    router.push('/dashboard');
  };

  const handleAnalysisClick = (jobId: string) => {
    if (jobId === 'demo-guardrails-project') {
      router.push('/dashboard/analyses/demo-guardrails-project');
    } else {
      router.push(`/dashboard/analyses/${jobId}`);
    }
  };

  const allAnalyses = [
    ...(demoAnalysis ? [demoAnalysis] : []),
    ...analyses
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h3 className="text-lg font-medium mb-2">Loading Analyses...</h3>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg shadow-sm border dark:border-slate-700 p-4 mb-6 bg-white dark:bg-slate-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              onClick={handleBack}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
            <div>
              <h1 className="text-xl font-bold">Analysis History</h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                View all your documentation analyses and the demo project
              </p>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 dark:border-red-700 bg-red-50 dark:bg-red-900/20">
          <CardContent className="flex items-center gap-3 py-4">
            <AlertCircle className="h-5 w-5 text-red-500" />
            <span className="text-red-800 dark:text-red-200">{error}</span>
          </CardContent>
        </Card>
      )}

      {allAnalyses.length === 0 ? (
        <Card className="dark:bg-slate-800 dark:border-slate-700">
          <CardContent className="flex flex-col items-center justify-center py-12 text-slate-500 dark:text-slate-400">
            <div className="text-center max-w-md">
              <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <h3 className="text-lg font-medium mb-2">No analyses yet</h3>
              <p className="mb-4">
                Start by creating a project or explore the demo analysis to see how the system works.
              </p>
              <div className="flex gap-3 justify-center">
                <Button 
                  onClick={() => router.push('/dashboard/projects')}
                  className="bg-blue-600 hover:bg-blue-700 text-white"
                >
                  Create Project
                </Button>
                {demoAnalysis && (
                  <Button 
                    onClick={() => handleAnalysisClick('demo-guardrails-project')}
                    variant="outline"
                  >
                    View Demo
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {allAnalyses.map((analysis) => (
            <div 
              key={analysis.job_id}
              onClick={() => handleAnalysisClick(analysis.job_id)}
              className="border rounded-lg p-4 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors cursor-pointer"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  {getStatusIcon(analysis.status)}
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="font-medium text-lg">
                        {analysis.name || analysis.repository}
                      </h3>
                      {analysis.is_demo && (
                        <Badge variant="outline" className="text-xs bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400">
                          Demo
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {analysis.repository} • {analysis.branch}
                    </p>
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {analysis.use_cases_count || (analysis as any).use_cases?.length || 0} use cases
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <div className="flex items-center gap-2">
                      <Badge 
                        variant={
                          analysis.status === 'completed' ? 'default' : 
                          analysis.status === 'failed' ? 'destructive' :
                          'secondary'
                        }
                        className={`text-sm ${
                          analysis.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' :
                          analysis.status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400' :
                          'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
                        }`}
                      >
                        {analysis.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                      {formatDistanceToNow(new Date(analysis.created_at), { addSuffix: true })}
                    </p>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-400" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}