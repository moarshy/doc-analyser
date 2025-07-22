import json
import os
from pathlib import Path
from typing import Dict, Any, List

from backend.worker.logger import tasks_logger


class AnalysisPipeline:
    """Main analysis pipeline for processing repository documentation."""
    
    def __init__(self, job_id: str, repo_path: str, include_folders: List[str], data_dir: str = None):
        self.job_id = job_id
        self.repo_path = Path(repo_path)
        self.include_folders = include_folders
        
        # Use the data directory structure: ../data/job_id/
        if data_dir is None:
            data_dir = os.path.join("..", "data", job_id)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def run(self) -> Dict[str, Any]:
        """Run the complete analysis pipeline."""
        try:
            tasks_logger.info(f"Starting analysis for job {self.job_id}")
            tasks_logger.info(f"Results path: {self.results_path}")
            
            # Step 1: Extract use cases from documentation
            tasks_logger.info("Extracting use cases...")
            use_cases = self._extract_use_cases()
            
            if not use_cases:
                tasks_logger.info("No use cases found in documentation")
                return {
                    "status": "completed",
                    "use_cases": [],
                    "analysis_results": {},
                    "message": "No use cases found in documentation"
                }
            
            # Step 2: Execute use cases
            tasks_logger.info(f"Executing {len(use_cases)} use cases...")
            results = self._execute_use_cases(use_cases)
            
            # Step 3: Generate final report
            report = self._generate_report(use_cases, results)
            
            # Step 4: Save results
            self._save_results(report)
            
            return report
            
        except Exception as e:
            tasks_logger.error(f"Analysis failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
                "use_cases": [],
                "analysis_results": {}
            }
    
    def _extract_use_cases(self) -> List[Dict[str, Any]]:
        """Extract use cases from documentation using Docker runner."""
        # This should be handled by Docker runner's two-phase execution
        # Phase 1: Extract use cases
        use_cases_path = self.data_dir / "data" / "use_cases.json"
        if use_cases_path.exists():
            with open(use_cases_path) as f:
                data = json.load(f)
                return data.get("use_cases", [])
        return []
    
    def _execute_use_cases(self, use_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute use cases - handled by Docker runner."""
        # The Docker runner handles both extraction and execution phases
        # This method is now a placeholder as the actual execution happens in Docker
        return {}
    
    def _generate_report(self, use_cases: List[Dict], results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        
        successful_executions = sum(1 for r in results.values() if r.get("status") == "success")
        failed_executions = len(results) - successful_executions
        
        report = {
            "job_id": self.job_id,
            "status": "completed",
            "summary": {
                "total_use_cases": len(use_cases),
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "success_rate": successful_executions / len(use_cases) if use_cases else 0
            },
            "use_cases": use_cases,
            "analysis_results": results,
            "documentation_quality": self._assess_documentation_quality(use_cases, results),
            "recommendations": self._generate_recommendations(use_cases, results)
        }
        
        return report
    
    def _assess_documentation_quality(self, use_cases: List[Dict], results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of the documentation."""
        
        score = 0
        max_score = 0
        
        for use_case in use_cases:
            max_score += 10
            
            # Check if use case has clear description
            if use_case.get("description"):
                score += 2
            
            # Check if use case has success criteria
            if use_case.get("success_criteria"):
                score += 2
            
            # Check if use case has been successfully executed
            use_case_name = use_case.get("name")
            if use_case_name in results and results[use_case_name].get("status") == "success":
                score += 3
            
            # Check if documentation source is provided
            if use_case.get("documentation_source"):
                score += 1
            
            # Check if difficulty level is specified
            if use_case.get("difficulty_level"):
                score += 2
        
        quality_score = (score / max_score) * 100 if max_score > 0 else 0
        
        return {
            "quality_score": quality_score,
            "grade": "A" if quality_score >= 90 else 
                     "B" if quality_score >= 80 else 
                     "C" if quality_score >= 70 else 
                     "D" if quality_score >= 60 else "F",
            "issues": self._identify_issues(use_cases, results)
        }
    
    def _identify_issues(self, use_cases: List[Dict], results: Dict[str, Any]) -> List[str]:
        """Identify issues in documentation and execution."""
        issues = []
        
        for use_case in use_cases:
            use_case_name = use_case.get("name")
            
            if not use_case.get("description"):
                issues.append(f"Use case '{use_case_name}' lacks clear description")
            
            if not use_case.get("success_criteria"):
                issues.append(f"Use case '{use_case_name}' lacks success criteria")
            
            if use_case_name in results and results[use_case_name].get("status") == "failed":
                issues.append(f"Use case '{use_case_name}' failed execution")
        
        return issues
    
    def _generate_recommendations(self, use_cases: List[Dict], results: Dict[str, Any]) -> List[str]:
        """Generate recommendations for improving documentation."""
        recommendations = []
        
        failed_count = sum(1 for r in results.values() if r.get("status") == "failed")
        
        if failed_count > 0:
            recommendations.append(
                f"{failed_count} use case(s) failed execution. Review the implementation "
                f"and ensure the documentation provides accurate code examples."
            )
        
        for use_case in use_cases:
            if not use_case.get("description"):
                recommendations.append(
                    f"Add clear description to use case '{use_case.get('name')}'"
                )
            
            if not use_case.get("success_criteria"):
                recommendations.append(
                    f"Define clear success criteria for use case '{use_case.get('name')}'"
                )
        
        return recommendations
    
    def _save_results(self, report: Dict[str, Any]):
        """Save analysis results to file."""
        results_file = self.data_dir / "results.json"
        
        with open(results_file, "w") as f:
            json.dump(report, f, indent=2)
        
        tasks_logger.info(f"Results saved to {results_file}")


if __name__ == "__main__":
    # For testing
    job_id = os.getenv("JOB_ID", "test")
    repo_path = os.getenv("REPO_PATH", "/workspace/repo")
    include_folders = json.loads(os.getenv("INCLUDE_FOLDERS", '["docs"]'))
    
    pipeline = AnalysisPipeline(job_id, repo_path, include_folders)
    results = pipeline.run()
    tasks_logger.info(json.dumps(results, indent=2))