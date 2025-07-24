#!/usr/bin/env python3
"""
Script to link an analysis job to a user and project in Redis.
This manually updates Redis records to associate completed jobs with projects.
"""

import redis
import json
from datetime import datetime, timezone

# Redis connection
client = redis.Redis(host='localhost', port=6379, db=0)

def link_job_to_project(job_id: str, user_id: str, project_id: str):
    """
    Link an analysis job to a user and project by updating Redis records.
    
    Args:
        job_id: The job ID (e.g., "5e2d97dc-3435-49c5-842c-18e5dadb6505")
        user_id: The user ID (e.g., "google-oauth2|111962411139153579092") 
        project_id: The project ID (e.g., "ec974726-2c96-4638-9bdb-1b96e43c54cb")
    """
    
    print("=== BEFORE LINKING ===")
    
    # Check current job data
    job_key = f"job:{job_id}"
    job_data = client.get(job_key)
    if job_data:
        job_info = json.loads(job_data)
        print(f"Job status: {job_info.get('status')}")
        print(f"Job params: {job_info.get('job_params', {})}")
    else:
        print("❌ Job not found!")
        return False

    # Check project data
    project_key = f"project:{project_id}"
    project_data = client.hgetall(project_key)
    if project_data:
        # Convert bytes to strings
        project_info = {k.decode(): v.decode() for k, v in project_data.items()}
        print(f"Project name: {project_info.get('name')}")
        print(f"Project job_count: {project_info.get('job_count')}")
        print(f"Project last_analysis_at: {project_info.get('last_analysis_at')}")
    else:
        print("❌ Project not found!")
        return False

    # Check user data
    user_key = f"user:{user_id}"
    user_data = client.hgetall(user_key)
    if user_data:
        user_info = {k.decode(): v.decode() for k, v in user_data.items()}
        print(f"User: {user_info.get('name', 'Unknown')}")
    else:
        print("❌ User not found!")
        return False

    print("\n=== LINKING JOB TO PROJECT ===")

    # Update job data to include project_id and user_id
    job_info['project_id'] = project_id
    job_info['user_id'] = user_id
    
    # Update job in Redis
    client.set(job_key, json.dumps(job_info))
    print(f"✓ Updated job {job_id} with project_id and user_id")

    # Update project data
    project_info = {k.decode(): v.decode() for k, v in project_data.items()}
    
    # Increment job count
    current_job_count = int(project_info.get('job_count', 0))
    new_job_count = current_job_count + 1
    
    # Update last_analysis_at
    current_time = datetime.now(timezone.utc).isoformat()
    
    # Update project fields
    client.hset(project_key, mapping={
        'job_count': str(new_job_count),
        'last_analysis_at': current_time,
        'updated_at': current_time
    })
    
    print(f"✓ Updated project {project_id}:")
    print(f"  - job_count: {current_job_count} → {new_job_count}")
    print(f"  - last_analysis_at: {current_time}")

    # Create project-job index
    project_jobs_key = f"project_jobs:{project_id}"
    timestamp = datetime.now(timezone.utc).timestamp()
    client.zadd(project_jobs_key, {job_id: timestamp})
    client.expire(project_jobs_key, 30 * 24 * 60 * 60)  # 30 day TTL
    print(f"✓ Added job to project jobs index: {project_jobs_key}")

    # Create user-job index  
    user_jobs_key = f"user_jobs:{user_id}"
    client.zadd(user_jobs_key, {job_id: timestamp})
    client.expire(user_jobs_key, 30 * 24 * 60 * 60)  # 30 day TTL
    print(f"✓ Added job to user jobs index: {user_jobs_key}")

    print("\n=== LINKING COMPLETE ===")
    return True

def verify_linking(job_id: str, user_id: str, project_id: str):
    """Verify that the linking was successful"""
    print("\n=== VERIFICATION ===")
    
    # Check job has project_id and user_id
    job_key = f"job:{job_id}"
    job_data = client.get(job_key)
    if job_data:
        job_info = json.loads(job_data)
        print(f"✓ Job project_id: {job_info.get('project_id')}")
        print(f"✓ Job user_id: {job_info.get('user_id')}")
    
    # Check project job count updated
    project_key = f"project:{project_id}"
    project_data = client.hgetall(project_key)
    if project_data:
        project_info = {k.decode(): v.decode() for k, v in project_data.items()}
        print(f"✓ Project job_count: {project_info.get('job_count')}")
        print(f"✓ Project last_analysis_at: {project_info.get('last_analysis_at')}")
    
    # Check indexes exist
    project_jobs_key = f"project_jobs:{project_id}"
    jobs = client.zrange(project_jobs_key, 0, -1)
    print(f"✓ Project jobs index: {[j.decode() for j in jobs]}")
    
    user_jobs_key = f"user_jobs:{user_id}"
    jobs = client.zrange(user_jobs_key, 0, -1)
    print(f"✓ User jobs index: {[j.decode() for j in jobs]}")

if __name__ == "__main__":
    # Example usage with the provided IDs
    job_id = "5e2d97dc-3435-49c5-842c-18e5dadb6505"
    user_id = "google-oauth2|111962411139153579092"
    project_id = "ec974726-2c96-4638-9bdb-1b96e43c54cb"
    
    success = link_job_to_project(job_id, user_id, project_id)
    
    if success:
        verify_linking(job_id, user_id, project_id)
    else:
        print("❌ Linking failed - missing required data in Redis")