'use client';

import { useEffect, useState, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { AlertCircle, CheckCircle, Clock, GitBranch, Loader2, Play, Terminal } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/use-auth';

interface JobStatus {
  status: string;
  total_use_cases: number;
  completed: number;
  failed: number;
  pending: number;
  use_cases: any[];
  current_stage: string;
  logs: string[];
  start_time?: string;
  end_time?: string;
  error?: string;
}

interface JobProgressProps {
  jobId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

const STAGE_CONFIG = {
  pending: { icon: Clock, label: 'Initializing', color: 'text-yellow-600' },
  cloning: { icon: GitBranch, label: 'Cloning Repository', color: 'text-blue-600' },
  extracting: { icon: Play, label: 'Extracting Use Cases', color: 'text-purple-600' },
  executing: { icon: Loader2, label: 'Executing Use Cases', color: 'text-green-600' },
  completed: { icon: CheckCircle, label: 'Completed', color: 'text-green-600' },
  failed: { icon: AlertCircle, label: 'Failed', color: 'text-red-600' },
};

export function JobProgress({ jobId, onComplete, onError }: JobProgressProps) {
  const { apiClient } = useAuth();
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [isPolling, setIsPolling] = useState(true);
  const [logs, setLogs] = useState<string[]>([]);

  const fetchJobStatus = useCallback(async () => {
    if (!apiClient) return;
    
    try {
      const response = await apiClient.getAnalysisStatus(jobId);
      const data = response.data;
      setJobStatus(data);
      
      // Update logs if available
      if (data.logs) {
        setLogs(prev => [...prev, ...data.logs.filter((log: string) => !prev.includes(log))]);
      }
      
      // Stop polling when job is complete or failed
      if (data.status === 'completed' || data.status === 'failed') {
        setIsPolling(false);
        if (data.status === 'completed') {
          onComplete?.();
        } else if (data.error) {
          onError?.(data.error);
        }
      }
    } catch (error) {
      console.error('Error fetching job status:', error);
      setIsPolling(false);
      onError?.('Failed to fetch job status');
    }
  }, [jobId, apiClient, onComplete, onError]);

  useEffect(() => {
    if (!isPolling || !apiClient) return;

    // Initial fetch
    fetchJobStatus();

    // Poll every 2 seconds
    const interval = setInterval(fetchJobStatus, 2000);

    return () => clearInterval(interval);
  }, [fetchJobStatus, isPolling]);

  const getProgressPercentage = () => {
    if (!jobStatus) return 0;
    if (jobStatus.total_use_cases === 0) return 0;
    
    return Math.round((jobStatus.completed + jobStatus.failed) / jobStatus.total_use_cases * 100);
  };

  const getStageInfo = () => {
    const currentStage = jobStatus?.status || 'pending';
    return STAGE_CONFIG[currentStage as keyof typeof STAGE_CONFIG] || STAGE_CONFIG.pending;
  };

  const stageInfo = getStageInfo();
  const StageIcon = stageInfo.icon;

  if (!jobStatus) {
    return (
      <div className="flex items-center justify-center p-8">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Current Stage */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <StageIcon className={cn("h-8 w-8", stageInfo.color)} />
            <div>
              <h3 className="text-lg font-semibold">{stageInfo.label}</h3>
              <p className="text-sm text-muted-foreground">
                Job ID: {jobId}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Progress Bar */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Overall Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <Progress value={getProgressPercentage()} className="w-full" />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>{jobStatus.completed + jobStatus.failed} / {jobStatus.total_use_cases} use cases</span>
              <span>{getProgressPercentage()}%</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Use Case Status */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Use Case Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-blue-600">{jobStatus.pending}</div>
              <div className="text-xs text-muted-foreground">Pending</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">{jobStatus.completed}</div>
              <div className="text-xs text-muted-foreground">Completed</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-red-600">{jobStatus.failed}</div>
              <div className="text-xs text-muted-foreground">Failed</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Live Logs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Terminal className="h-4 w-4" />
            Live Logs
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-slate-900 text-slate-100 p-4 rounded-lg max-h-96 overflow-y-auto font-mono text-sm">
            {logs.length === 0 ? (
              <div className="text-slate-400">Waiting for logs...</div>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="whitespace-pre-wrap">
                  {log}
                </div>
              ))
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}