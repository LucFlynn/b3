from fastapi import APIRouter, Depends, HTTPException

from app.models.user import User
from app.security import get_current_user

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/run/{job_name}")
async def run_job(job_name: str, user: User = Depends(get_current_user)):
    from app.jobs.pull_google import pull_google_ads
    from app.jobs.pull_meta import pull_meta_ads
    from app.jobs.compute_comparison import compute_comparison

    jobs = {
        "pull_google": pull_google_ads,
        "pull_meta": pull_meta_ads,
        "compute_comparison": compute_comparison,
    }

    fn = jobs.get(job_name)
    if not fn:
        raise HTTPException(status_code=404, detail=f"Unknown job: {job_name}. Available: {list(jobs.keys())}")

    await fn(agency_id=str(user.agency_id))
    return {"status": "completed", "job": job_name}
