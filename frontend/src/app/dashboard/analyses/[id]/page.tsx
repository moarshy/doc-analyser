'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ArrowLeft, Clock, CheckCircle, AlertCircle, FileCode, Activity, Globe, ChevronRight, FileText, Container, Loader2 } from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';

interface UseCase {
  name: string;
  description: string;
  success_criteria: string[];
  difficulty_level: string;
  documentation_source: string[];
  status?: string;
  execution_time_seconds?: number;
  container_logs?: string;
  start_time?: number;
  end_time?: number;
  data?: {
    name: string;
    description: string;
    success_criteria: string[];
    difficulty_level: string;
    documentation_source: string[];
  };
}

interface AnalysisJob {
  job_id: string;
  status: string;
  repository: string;
  branch: string;
  include_folders: string[];
  use_cases: UseCase[];
  results?: any;
  error?: string;
  created_at: string;
  updated_at: string;
  project_id?: string;
  data_path?: string;
  repo_path?: string;
}

interface UseCaseResult {
  execution_status?: string;
  execution_results?: string;
  documentation_sources_used?: string[];
  documentation_usefulness?: string[];
  documentation_weaknesses?: string[];
  documentation_improvements?: string[];
  code_file_path?: string;
  execution_time?: string;
  success_criteria_met?: string[];
  challenges_encountered?: string[];
  use_case_name?: string;
  use_case_index?: number;
  error?: string;
  success?: boolean;
  timestamp?: string;
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

const getDifficultyColor = (level: string) => {
  switch (level?.toLowerCase()) {
    case 'beginner':
      return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
    case 'intermediate':
      return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
    case 'advanced':
      return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
    default:
      return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
  }
};

export default function AnalysisDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { apiClient } = useAuth();
  const [analysis, setAnalysis] = useState<AnalysisJob | null>(null);
  const [selectedUseCaseIndex, setSelectedUseCaseIndex] = useState(0);
  const [useCaseFiles, setUseCaseFiles] = useState<{[key: number]: {code: string, results: UseCaseResult | null}}>({});
  const [isLoading, setIsLoading] = useState(true);
  const [jobStatus, setJobStatus] = useState<string>('loading');
  const [isPolling, setIsPolling] = useState(true);
  const [jobLogs, setJobLogs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('details');

  const jobId = params.id as string;

  useEffect(() => {
    const fetchAnalysis = async () => {
      if (!apiClient || !jobId) return;

      try {
        // Always fetch full analysis details
        const response = await apiClient.getAnalysisDetail(jobId);
        console.log('🔍 Analysis Response:', response.data);
        
        setAnalysis(response.data);
        setJobStatus(response.data.status || 'completed');
        
        // If job is still running, continue polling
        const activeStatuses = ['pending', 'cloning', 'extracting', 'executing'];
        if (activeStatuses.includes(response.data.status)) {
          setIsPolling(true);
          console.log('🔄 Job is active, will continue polling. Status:', response.data.status);
        } else {
          setIsPolling(false);
          console.log('✅ Job is complete. Status:', response.data.status);
        }
      } catch (err: any) {
        if (err.response?.status === 404) {
          setError('Analysis not found');
          setJobStatus('not_found');
        } else {
          setError('Failed to load analysis');
          setJobStatus('error');
        }
        setIsPolling(false);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnalysis();
  }, [apiClient, jobId]);

  // Auto-refresh for active jobs
  useEffect(() => {
    if (!isPolling || !apiClient || !jobId) return;

    const refreshData = async () => {
      try {
        const response = await apiClient.getAnalysisDetail(jobId);
        setAnalysis(response.data);
        setJobStatus(response.data.status);
        
        // Stop polling when job is complete
        const finalStatuses = ['completed', 'failed', 'completed_with_errors'];
        if (finalStatuses.includes(response.data.status)) {
          setIsPolling(false);
          console.log('✅ Job completed, stopped polling');
        }
      } catch (error) {
        console.error('Auto-refresh error:', error);
        setIsPolling(false);
      }
    };

    const interval = setInterval(refreshData, 3000);
    return () => clearInterval(interval);
  }, [isPolling, apiClient, jobId]);

  const fetchUseCaseFiles = async (index: number) => {
    if (!apiClient || !jobId) return;
    
    // Skip if files already fetched
    if (useCaseFiles[index]) {
      console.log(`⏭️ Files for use case ${index} already cached`);
      return;
    }

    try {
      console.log(`🔍 Fetching files for use case ${index} in job ${jobId}`);
      
      // Try to fetch the code file (could be .py, .js, .ts, etc.)
      const codeExtensions = ['py', 'js', 'ts', 'java', 'cpp', 'c', 'go'];
      let codeContent = '';
      
      for (const ext of codeExtensions) {
        try {
          console.log(`🔍 Trying to fetch: use_case_${index}.${ext}`);
          const codeResponse = await apiClient.getAnalysisFile(jobId, `use_case_${index}.${ext}`);
          codeContent = codeResponse.data;
          console.log(`✅ Found code file: use_case_${index}.${ext}`, codeContent.substring(0, 100) + '...');
          break;
        } catch (e) {
          console.log(`❌ Code file not found: use_case_${index}.${ext}`, e);
        }
      }

      // Fetch the results JSON
      let resultsContent = null;
      try {
        const resultsResponse = await apiClient.getAnalysisFile(jobId, `use_case_results_${index}.json`);
        // Clean the JSON to handle bad control characters
        const cleanJson = resultsResponse.data
          .replace(/[\u0000-\u001F\u007F-\u009F]/g, '') // Remove control characters
          .replace(/\t/g, '  ') // Replace tabs with spaces
          .replace(/\r\n/g, '\n') // Normalize line endings
          .replace(/\r/g, '\n');
        resultsContent = JSON.parse(cleanJson);
        console.log('✅ Results JSON found:', resultsContent);
      } catch (e) {
        console.error('❌ Results file not found or invalid JSON:', e);
        // Try to display the raw content if JSON parsing fails
        try {
          const resultsResponse = await apiClient.getAnalysisFile(jobId, `use_case_results_${index}.json`);
          resultsContent = {
            execution_status: 'error',
            execution_results: `Error parsing JSON: ${e.message}\n\nRaw content:\n${resultsResponse.data.substring(0, 500)}...`,
            documentation_sources_used: [],
            documentation_usefulness: [],
            documentation_weaknesses: [],
            documentation_improvements: [],
            success_criteria_met: [],
            challenges_encountered: [`JSON parsing error: ${e.message}`]
          };
        } catch (fallbackError) {
          console.error('❌ Fallback also failed:', fallbackError);
        }
      }

      setUseCaseFiles(prev => ({
        ...prev,
        [index]: {
          code: codeContent,
          results: resultsContent
        }
      }));
    } catch (error) {
      console.error('Failed to fetch use case files:', error);
    }
  };

  useEffect(() => {
    // Fetch files for individual completed use cases (even if job is still executing)
    console.log('🔍 Checking for completed use cases to fetch files:', {
      hasAnalysis: !!analysis,
      useCasesCount: analysis?.use_cases?.length || 0,
      jobStatus: analysis?.status
    });
    
    if (analysis && analysis.use_cases?.length > 0) {
      // Fetch files for any completed use cases, regardless of overall job status
      console.log('🚀 Starting to fetch files for completed use cases...');
      analysis.use_cases.forEach((useCase, index) => {
        console.log(`📋 Use case ${index}: ${useCase.name} - Status: ${useCase.status} - Files cached: ${!!useCaseFiles[index]}`);
        if (useCase.status === 'completed' && !useCaseFiles[index]) {
          console.log(`🔥 Fetching files for completed use case ${index}: ${useCase.name}`);
          fetchUseCaseFiles(index);
        }
      });
    }
  }, [analysis]);

  // Also fetch files when selecting a use case (for immediate display)
  useEffect(() => {
    if (analysis && analysis.use_cases?.length > 0) {
      const selectedUseCase = analysis.use_cases[selectedUseCaseIndex];
      if (selectedUseCase?.status === 'completed' && !useCaseFiles[selectedUseCaseIndex]) {
        console.log(`🎯 Selected use case ${selectedUseCaseIndex} is completed, fetching files...`);
        fetchUseCaseFiles(selectedUseCaseIndex);
      }
    }
  }, [selectedUseCaseIndex, analysis]);

  const handleBack = () => {
    if (analysis?.project_id) {
      router.push(`/dashboard/projects/${analysis.project_id}`);
    } else {
      router.push('/dashboard/analyses');
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-screen">
        <div className="w-80 border-r bg-slate-50 p-4">
          <Skeleton className="h-8 w-32 mb-4" />
          <div className="space-y-2">
            {[1, 2, 3].map(i => (
              <Skeleton key={i} className="h-16 w-full" />
            ))}
          </div>
        </div>
        <div className="flex-1 p-6">
          <Skeleton className="h-8 w-48 mb-6" />
          <Skeleton className="h-96 w-full" />
        </div>
      </div>
    );
  }


  if (error || !analysis) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <div className="text-center">
          <h3 className="text-lg font-medium mb-2">
            {error || 'Analysis not found'}
          </h3>
          <Button onClick={handleBack}>
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back
          </Button>
        </div>
      </div>
    );
  }

  const selectedUseCase = analysis.use_cases?.[selectedUseCaseIndex];
  const selectedFiles = useCaseFiles[selectedUseCaseIndex];

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
            <Globe className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <div>
              <h1 className="text-xl font-bold">{analysis.repository}</h1>
              <p className="text-sm text-slate-600 dark:text-slate-400">{analysis.branch} branch</p>
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {getStatusIcon(analysis.status)}
              <Badge variant={analysis.status === 'completed' ? 'default' : 'secondary'}>
                {analysis.status}
              </Badge>
              {isPolling && (
                <div className="flex items-center gap-1 text-xs text-slate-500 dark:text-slate-400">
                  <Loader2 className="h-3 w-3 animate-spin" />
                  <span>Live updates</span>
                </div>
              )}
            </div>
            
            {/* Progress Stats */}
            {analysis.use_cases && analysis.use_cases.length > 0 && (
              <div className="flex flex-col gap-2 text-sm">
              <div className="flex items-center gap-4 text-slate-600 dark:text-slate-400">
                <div className="flex items-center gap-1">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span>{analysis.use_cases.filter(uc => uc.status === 'completed').length} completed</span>
                </div>
                <div className="flex items-center gap-1">
                  <Clock className="h-4 w-4 text-yellow-500" />
                  <span>{analysis.use_cases.filter(uc => uc.status === 'running' || uc.status === 'pending').length} pending</span>
                </div>
                <div className="flex items-center gap-1">
                  <AlertCircle className="h-4 w-4 text-red-500" />
                  <span>{analysis.use_cases.filter(uc => uc.status === 'failed').length} failed</span>
                </div>
                <span className="text-slate-400">•</span>
                <span>{analysis.use_cases.length} total use cases</span>
              </div>
              <div className="mt-2">
                {analysis.status === 'cloning' && (
                  <div className="flex items-center gap-2 text-blue-600 dark:text-blue-400">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Cloning repository from GitHub...</span>
                  </div>
                )}
                {analysis.status === 'extracting' && (
                  <div className="flex items-center gap-2 text-purple-600 dark:text-purple-400">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Extracting use cases from documentation...</span>
                  </div>
                )}
                {analysis.status === 'executing' && (
                  <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span>Executing {analysis.use_cases?.length || 0} use cases...</span>
                  </div>
                )}
                {analysis.status === 'completed' && (
                  <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
                    <CheckCircle className="h-4 w-4" />
                    <span>All use cases executed successfully</span>
                  </div>
                )}
                {analysis.status === 'failed' && (
                  <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
                    <AlertCircle className="h-4 w-4" />
                    <span>Analysis failed - check error details</span>
                  </div>
                )}
              </div>
            </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-6">
        {/* Sidebar */}
        <div className="col-span-4">
          <Card className="dark:bg-slate-800 dark:border-slate-700">
            <CardHeader>
              <CardTitle className="text-lg">Use Cases ({analysis.use_cases?.length || 0})</CardTitle>
            </CardHeader>
            <CardContent className="p-3">
              <div className="space-y-2 max-h-[800px] overflow-y-auto">
                {analysis.use_cases?.filter(useCase => useCase != null).map((useCase, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedUseCaseIndex(index)}
                    className={`w-full text-left p-3 rounded-lg border transition-colors ${
                      selectedUseCaseIndex === index
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700'
                        : 'bg-white dark:bg-slate-700 border-slate-200 dark:border-slate-600 hover:bg-slate-50 dark:hover:bg-slate-600'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          {getStatusIcon(useCase.status || 'pending')}
                          <span className="text-sm font-medium truncate">
                            {useCase.name || `Use Case ${index + 1}`}
                          </span>
                        </div>
                        
                        {/* Status Details */}
                        <div className="mb-2">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge 
                              variant={
                                useCase.status === 'completed' ? 'default' : 
                                useCase.status === 'failed' ? 'destructive' : 
                                useCase.status === 'running' ? 'outline' :
                                'secondary'
                              }
                              className={`text-xs font-medium ${
                                useCase.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400' :
                                useCase.status === 'failed' ? 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400' :
                                useCase.status === 'running' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400 border-blue-300' :
                                'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400'
                              }`}
                            >
                              {useCase.status === 'running' && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
                              {useCase.status || 'pending'}
                            </Badge>
                            {useCase.execution_time_seconds && (
                              <Badge variant="outline" className="text-xs bg-slate-50 dark:bg-slate-800">
                                {useCase.execution_time_seconds.toFixed(1)}s
                              </Badge>
                            )}
                            {/* File availability indicators */}
                            {useCase.status === 'completed' && useCaseFiles[index] && (
                              <div className="flex gap-1">
                                {useCaseFiles[index]?.code && (
                                  <Badge variant="outline" className="text-xs bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400 border-blue-200">
                                    <FileCode className="h-3 w-3 mr-1" />
                                    Code
                                  </Badge>
                                )}
                                {useCaseFiles[index]?.results && (
                                  <Badge variant="outline" className="text-xs bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400 border-purple-200">
                                    <Activity className="h-3 w-3 mr-1" />
                                    Results
                                  </Badge>
                                )}
                              </div>
                            )}
                          </div>
                          
                          {/* Running indicator with elapsed time */}
                          {useCase.status === 'running' && useCase.start_time && (
                            <div className="flex items-center gap-1 text-xs text-blue-600 dark:text-blue-400 mt-1">
                              <span>Running for {Math.floor((Date.now() / 1000 - useCase.start_time) / 60)}m {Math.floor((Date.now() / 1000 - useCase.start_time) % 60)}s</span>
                            </div>
                          )}
                        </div>
                        
                        <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2 mb-2">
                          {useCase.description || 'No description'}
                        </p>
                        
                        <div className="flex items-center justify-between">
                          {useCase.difficulty_level && (
                            <Badge className={`text-xs ${getDifficultyColor(useCase.difficulty_level)}`}>
                              {useCase.difficulty_level}
                            </Badge>
                          )}
                        </div>
                      </div>
                      <ChevronRight className="h-4 w-4 text-slate-400 ml-2 flex-shrink-0" />
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="col-span-8">
          {selectedUseCase ? (
            <Card className="dark:bg-slate-800 dark:border-slate-700">
              <CardHeader>
                <CardTitle className="text-xl">
                  {selectedUseCase.name || `Use Case ${selectedUseCaseIndex + 1}`}
                </CardTitle>
                <p className="text-slate-600 dark:text-slate-400">
                  {selectedUseCase.description || 'No description available'}
                </p>
                
                {/* Difficulty Level */}
                {(selectedUseCase.data?.difficulty_level || selectedUseCase.difficulty_level) && (
                  <Badge className={`text-sm mt-2 ${getDifficultyColor(selectedUseCase.data?.difficulty_level || selectedUseCase.difficulty_level)}`}>
                    {selectedUseCase.data?.difficulty_level || selectedUseCase.difficulty_level}
                  </Badge>
                )}
              </CardHeader>
              <CardContent>
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  <TabsList className="grid w-full grid-cols-3 mb-6">
                    <TabsTrigger value="details" className="flex items-center gap-2">
                      <FileText className="h-4 w-4" />
                      Details
                    </TabsTrigger>
                    <TabsTrigger value="code" className="flex items-center gap-2">
                      <FileCode className="h-4 w-4" />
                      Code
                    </TabsTrigger>
                    <TabsTrigger value="results" className="flex items-center gap-2">
                      <Activity className="h-4 w-4" />
                      Results
                    </TabsTrigger>
                  </TabsList>

                  <TabsContent value="details">
                    <div className="space-y-6">
                      {/* Success Criteria */}
                      {selectedUseCase.success_criteria && (
                        <Card className="dark:bg-slate-700 dark:border-slate-600">
                          <CardHeader>
                            <CardTitle className="text-lg">Success Criteria</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <ul className="list-disc list-inside space-y-2">
                              {selectedUseCase.success_criteria.map((criteria: string, idx: number) => (
                                <li key={idx} className="text-sm">{criteria}</li>
                              ))}
                            </ul>
                          </CardContent>
                        </Card>
                      )}

                      {/* Documentation Sources */}
                      {selectedUseCase.documentation_source && (
                        <Card className="dark:bg-slate-700 dark:border-slate-600">
                          <CardHeader>
                            <CardTitle className="text-lg">Documentation Sources</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <ul className="space-y-2">
                              {selectedUseCase.documentation_source.map((source: string, idx: number) => (
                                <li key={idx} className="flex items-center gap-2 text-sm">
                                  <FileText className="h-4 w-4 text-slate-400" />
                                  <code className="bg-slate-100 dark:bg-slate-600 px-2 py-1 rounded text-xs">
                                    {source.replace('/workspace/repo/', '')}
                                  </code>
                                </li>
                              ))}
                            </ul>
                          </CardContent>
                        </Card>
                      )}

                      {/* Execution Info */}
                      {selectedUseCase.execution_time_seconds && (
                        <Card className="dark:bg-slate-700 dark:border-slate-600">
                          <CardHeader>
                            <CardTitle className="text-lg">Execution Information</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Execution Time</p>
                                <p className="text-lg font-semibold">{selectedUseCase.execution_time_seconds.toFixed(2)}s</p>
                              </div>
                              <div>
                                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Status</p>
                                <div className="flex items-center gap-2">
                                  {getStatusIcon(selectedUseCase.status || 'pending')}
                                  <span className="font-medium">{selectedUseCase.status || 'Pending'}</span>
                                </div>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="code">
                    <div className="space-y-6">
                      {/* Generated Code */}
                      {selectedFiles?.code && (
                        <Card className="dark:bg-slate-700 dark:border-slate-600">
                          <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                              <FileCode className="h-5 w-5" />
                              Generated Code
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-sm">
                              <code>{selectedFiles.code}</code>
                            </pre>
                          </CardContent>
                        </Card>
                      )}

                      {/* Container Logs */}
                      {selectedUseCase.container_logs && (
                        <Card className="dark:bg-slate-700 dark:border-slate-600">
                          <CardHeader>
                            <CardTitle className="text-lg flex items-center gap-2">
                              <Container className="h-5 w-5" />
                              Container Logs
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-xs max-h-96 overflow-y-auto">
                              <code>{selectedUseCase.container_logs}</code>
                            </pre>
                          </CardContent>
                        </Card>
                      )}
                    </div>
                  </TabsContent>

                  <TabsContent value="results">
                    <div className="space-y-6">
                      {selectedFiles?.results && (
                        <>
                          {/* Error Case */}
                          {selectedFiles.results.error && (
                            <Card className="dark:bg-red-900/20 border-red-200 dark:border-red-700">
                              <CardHeader>
                                <CardTitle className="text-lg text-red-800 dark:text-red-200">Execution Failed</CardTitle>
                              </CardHeader>
                              <CardContent>
                                <div className="flex items-center gap-2 mb-3">
                                  <AlertCircle className="h-5 w-5 text-red-500" />
                                  <Badge variant="destructive">Failed</Badge>
                                </div>
                                <pre className="bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200 p-3 rounded text-sm whitespace-pre-wrap font-mono">
                                  {typeof selectedFiles.results.error === 'object' 
                                    ? JSON.stringify(selectedFiles.results.error, null, 2)
                                    : selectedFiles.results.error}
                                </pre>
                                {selectedFiles.results.timestamp && (
                                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                                    Failed at: {new Date(selectedFiles.results.timestamp).toLocaleString()}
                                  </p>
                                )}
                              </CardContent>
                            </Card>
                          )}

                          {/* Success Case */}
                          {!selectedFiles.results.error && selectedFiles.results.success !== false && (
                            <>
                              {/* Execution Status */}
                              <Card className="dark:bg-slate-700 dark:border-slate-600">
                                <CardHeader>
                                  <CardTitle className="text-lg">Execution Status</CardTitle>
                                </CardHeader>
                                <CardContent>
                                  <Badge className={selectedFiles.results.execution_status === 'success' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'}>
                                    {selectedFiles.results.execution_status || 'Unknown'}
                                  </Badge>
                                  {selectedFiles.results.execution_time && (
                                    <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
                                      Completed in: {selectedFiles.results.execution_time}
                                    </p>
                                  )}
                                </CardContent>
                              </Card>

                              {/* Execution Results */}
                              {selectedFiles.results.execution_results && (
                                <Card className="dark:bg-slate-700 dark:border-slate-600">
                                  <CardHeader>
                                    <CardTitle className="text-lg">Execution Results</CardTitle>
                                  </CardHeader>
                                  <CardContent>
                                    <div className="bg-slate-50 dark:bg-slate-600 p-4 rounded border text-sm whitespace-pre-wrap">
                                      {typeof selectedFiles.results.execution_results === 'object' 
                                        ? JSON.stringify(selectedFiles.results.execution_results, null, 2)
                                        : selectedFiles.results.execution_results}
                                    </div>
                                  </CardContent>
                                </Card>
                              )}

                              {/* Success Criteria */}
                              {selectedFiles.results.success_criteria_met?.length > 0 && (
                                <Card className="dark:bg-slate-700 dark:border-slate-600">
                                  <CardHeader>
                                    <CardTitle className="text-lg">Success Criteria Met</CardTitle>
                                  </CardHeader>
                                  <CardContent>
                                    <ul className="list-disc list-inside space-y-2">
                                      {selectedFiles.results.success_criteria_met.map((criteria: string, idx: number) => (
                                        <li key={idx} className="text-sm">{criteria}</li>
                                      ))}
                                    </ul>
                                  </CardContent>
                                </Card>
                              )}

                              {/* Documentation Sources */}
                              {selectedFiles.results.documentation_sources_used?.length > 0 && (
                                <Card className="dark:bg-slate-700 dark:border-slate-600">
                                  <CardHeader>
                                    <CardTitle className="text-lg">Documentation Sources Used</CardTitle>
                                  </CardHeader>
                                  <CardContent>
                                    <ul className="space-y-2">
                                      {selectedFiles.results.documentation_sources_used.map((source: string, idx: number) => (
                                        <li key={idx} className="flex items-center gap-2 text-sm">
                                          <FileText className="h-4 w-4 text-slate-400" />
                                          <code className="bg-slate-100 dark:bg-slate-600 px-2 py-1 rounded text-xs">
                                            {source.replace('/workspace/repo/', '')}
                                          </code>
                                        </li>
                                      ))}
                                    </ul>
                                  </CardContent>
                                </Card>
                              )}

                              {/* Documentation Usefulness */}
                              {selectedFiles.results.documentation_usefulness?.length > 0 && (
                                <Card className="dark:bg-slate-700 dark:border-slate-600">
                                  <CardHeader>
                                    <CardTitle className="text-lg">Documentation Usefulness</CardTitle>
                                  </CardHeader>
                                  <CardContent>
                                    <ul className="list-disc list-inside space-y-2">
                                      {selectedFiles.results.documentation_usefulness.map((item: string, idx: number) => (
                                        <li key={idx} className="text-sm">{item}</li>
                                      ))}
                                    </ul>
                                  </CardContent>
                                </Card>
                              )}

                              {/* Documentation Weaknesses */}
                              {selectedFiles.results.documentation_weaknesses?.length > 0 && (
                                <Card className="dark:bg-slate-700 dark:border-slate-600">
                                  <CardHeader>
                                    <CardTitle className="text-lg">Documentation Weaknesses</CardTitle>
                                  </CardHeader>
                                  <CardContent>
                                    <ul className="list-disc list-inside space-y-2">
                                      {selectedFiles.results.documentation_weaknesses.map((item: string, idx: number) => (
                                        <li key={idx} className="text-sm">{item}</li>
                                      ))}
                                    </ul>
                                  </CardContent>
                                </Card>
                              )}

                              {/* Documentation Improvements */}
                              {selectedFiles.results.documentation_improvements?.length > 0 && (
                                <Card className="dark:bg-slate-700 dark:border-slate-600">
                                  <CardHeader>
                                    <CardTitle className="text-lg">Suggested Improvements</CardTitle>
                                  </CardHeader>
                                  <CardContent>
                                    <ul className="list-disc list-inside space-y-2">
                                      {selectedFiles.results.documentation_improvements.map((item: string, idx: number) => (
                                        <li key={idx} className="text-sm">{item}</li>
                                      ))}
                                    </ul>
                                  </CardContent>
                                </Card>
                              )}

                              {/* Challenges Encountered */}
                              {selectedFiles.results.challenges_encountered?.length > 0 && (
                                <Card className="dark:bg-slate-700 dark:border-slate-600">
                                  <CardHeader>
                                    <CardTitle className="text-lg">Challenges & Solutions</CardTitle>
                                  </CardHeader>
                                  <CardContent>
                                    <ul className="list-disc list-inside space-y-2">
                                      {selectedFiles.results.challenges_encountered.map((item: string, idx: number) => (
                                        <li key={idx} className="text-sm">{item}</li>
                                      ))}
                                    </ul>
                                  </CardContent>
                                </Card>
                              )}
                            </>
                          )}
                        </>
                      )}
                    </div>
                  </TabsContent>
                </Tabs>
              </CardContent>
            </Card>
          ) : (
            <Card className="dark:bg-slate-800 dark:border-slate-700">
              <CardContent className="flex items-center justify-center py-12 text-slate-500 dark:text-slate-400">
                <div className="text-center">
                  <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No use cases found</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}

