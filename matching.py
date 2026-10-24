"""
Job Mitra - Transparent Rule-Based Job Matching Engine
Computes explainable recommendation scores between candidates and vacancies.
Matches based on verified candidate profile fields:
1. Technical skills (45%)
2. Academic stream & qualification (25%)
3. Location preference (15%)
4. Graduation-year eligibility & experience (15%)
Provides full transparency with human-readable match breakdowns.
"""
import re

def compute_job_match(candidate: dict, job: dict) -> dict:
    """
    Computes a transparent 0-100% match score with explainable reasons.
    """
    if not candidate:
        return {
            "score": 50,
            "reasons": ["Base match (sign in or complete profile for personalized score)"],
            "matched_skills": [],
            "missing_skills": [s.strip() for s in (job.get('skills_required') or '').split(',') if s.strip()]
        }

    score = 0
    reasons = []

    # 1. Technical Skills (Max 45 points)
    candidate_skills_str = candidate.get('skills') or ''
    c_skills = {s.strip().lower() for s in candidate_skills_str.split(',') if s.strip()}
    
    job_skills_str = job.get('skills_required') or ''
    j_skills = [s.strip() for s in job_skills_str.split(',') if s.strip()]
    j_skills_lower = [s.lower() for s in j_skills]

    matched_skills = []
    missing_skills = []
    for s_orig, s_low in zip(j_skills, j_skills_lower):
        if s_low in c_skills or any(c in s_low or s_low in c for c in c_skills):
            matched_skills.append(s_orig)
        else:
            missing_skills.append(s_orig)

    if j_skills:
        skill_pct = len(matched_skills) / len(j_skills)
        skill_points = int(skill_pct * 45)
        score += skill_points
        if matched_skills:
            reasons.append(f"Matched {len(matched_skills)} of {len(j_skills)} required skills: {', '.join(matched_skills[:4])}")
    else:
        score += 25

    # 2. Engineering & Graduate Stream Match (Max 25 points)
    c_stream = (candidate.get('stream') or '').lower().strip()
    j_stream = (job.get('stream') or '').lower().strip()

    if 'any graduate' in j_stream or c_stream == j_stream:
        score += 25
        reasons.append(f"Direct stream match for {job.get('stream')}")
    elif any(token in j_stream for token in c_stream.split()) and len(c_stream) > 3:
        score += 18
        reasons.append(f"Related field match ({candidate.get('stream')})")
    else:
        score += 5

    # 3. Location Preference (Max 15 points)
    c_city = (candidate.get('city') or '').lower().strip()
    j_city = (job.get('city') or '').lower().strip()
    j_work_mode = (job.get('work_mode') or 'onsite').lower()

    if j_work_mode == 'remote':
        score += 15
        reasons.append("Remote role matching pan-India applicants")
    elif c_city and (c_city in j_city or j_city in c_city):
        score += 15
        reasons.append(f"Preferred location match ({job.get('city')})")
    else:
        score += 5

    # 4. Graduation Year & Experience Match (Max 15 points)
    c_grad_year = str(candidate.get('graduation_year') or '2026').strip()
    j_grad_years = str(job.get('graduation_year') or '2025, 2026').strip()

    if c_grad_year in j_grad_years:
        score += 15
        reasons.append(f"Graduation year eligibility ({c_grad_year} Batch)")
    else:
        score += 10
        reasons.append("Open to freshers & immediate joiners")

    # Clamp score to 10 - 100
    final_score = min(100, max(10, score))

    return {
        "score": final_score,
        "reasons": reasons,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills
    }
