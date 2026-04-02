# CI/CD Setup and Learning Guide

This document explains the CI/CD work completed so far for the AI-Based Product Decision System. It is written for both project documentation and learning/demo defense.

## 1. Scope of CI/CD in this project

This repository has two main parts:

- Backend: Python services for ingestion and analysis
- Frontend: Node.js server and dashboard pages

The pipeline automates three stages:

- Build
- Test
- Deploy (readiness and packaging artifacts)

Pipeline file used:

- .gitlab-ci.yml

## 2. Files created and updated

### 2.1 Main pipeline configuration

- .gitlab-ci.yml

What it defines:

- Stages: build, test, deploy
- Branch/MR execution rules
- Shared backend and frontend templates
- Cache for pip and npm
- Separate jobs for backend and frontend
- Artifacts from deploy-readiness jobs

### 2.2 CI-safe backend dependencies

- backend/requirements-ci.txt

Why this file was added:

- CI runner failed when building heavy native packages (specifically hdbscan)
- Build/test jobs only need lightweight dependencies for smoke validation
- This avoids flaky wheel compilation errors in CI

Current contents:

- SQLAlchemy>=2.0.0
- python-dateutil>=2.8.0
- requests>=2.31.0
- build>=1.2.0

## 3. Final pipeline design (current state)

## 3.1 Stage: Build

### Job: build_backend

Purpose:

- Validate backend source compiles
- Validate backend ingestion service import path

What it runs:

- python -m compileall -q src
- python import smoke check

### Job: build_frontend

Purpose:

- Validate frontend server script syntax
- Validate required HTML files exist

What it runs:

- node --check server.js
- file existence checks for dashboard.html and login.html

## 3.2 Stage: Test

### Job: test_backend_smoke

Purpose:

- Run backend ingestion smoke flow without heavy NLP stack

What it validates:

- CSV ingestion completes
- successful count is correct
- pending reviews are retrievable

### Job: test_frontend_smoke

Purpose:

- Validate frontend package integrity

What it validates:

- installed dependencies are resolvable
- package.json contains start script

## 3.3 Stage: Deploy

### Job: deploy_backend_readiness

Purpose:

- Simulate deployment readiness by packaging backend

What it produces:

- Python source distribution and wheel under backend/dist

Artifacts:

- backend/dist/
- expires in 1 week

### Job: deploy_frontend_readiness

Purpose:

- Simulate frontend release readiness

What it validates/artifacts:

- verifies required frontend release files
- stores frontend HTML and server/package files as artifacts
- expires in 1 week

## 4. Dependency caching and performance optimization

Caching configured:

- pip cache: .cache/pip
- npm cache: .cache/npm
- frontend modules: frontend/node_modules

Expected impact:

- second and later pipeline runs are faster
- less repeated downloading/installing

## 5. Errors encountered and fixes applied

## 5.1 Error observed

Backend build failed with:

- failed-wheel-build-for-install
- Failed to build installable wheels ... hdbscan

Root cause:

- hdbscan may require native build chain depending on runner environment
- runner lacked suitable environment for compiling/installing that package in CI path

Fix implemented:

- introduced backend/requirements-ci.txt
- configured backend CI jobs to use CI-safe dependencies
- avoided heavy optional package installation for build/test smoke path

## 5.2 Why "Tests: 0" appeared in GitLab

Reason:

- Jobs executed test logic, but no JUnit test report was published
- GitLab Tests tab shows counts only when test report artifacts are uploaded

Status:

- This is not a pipeline failure
- It is a reporting/visibility setting

How to enable test counts later:

- Add pytest-based tests
- Export JUnit XML
- Publish with artifacts:reports:junit

## 6. Current behavior you should expect

A healthy run should show six main jobs:

- build_backend
- build_frontend
- test_backend_smoke
- test_frontend_smoke
- deploy_backend_readiness
- deploy_frontend_readiness

Flow:

- Build jobs run first
- Test jobs run after their corresponding build jobs
- Deploy jobs run after corresponding test jobs

## 7. How to run and verify

## 7.1 Push latest CI files

Run from project root:

```powershell
git add .gitlab-ci.yml backend/requirements-ci.txt README-CICD.md
git commit -m "Document and finalize CI/CD pipeline setup"
git push origin main
```

## 7.2 Trigger pipeline

In GitLab:

1. CI/CD -> Pipelines
2. New pipeline
3. Select branch main
4. Run pipeline

## 7.3 Verify each stage

Check all jobs are green and logs contain expected messages:

- Backend build checks passed
- Frontend build checks passed
- Backend smoke test passed
- Frontend package validation passed
- backend dist contents printed
- frontend release files verified

## 7.4 Verify artifacts

Download artifacts from deploy jobs:

- backend dist package(s)
- frontend release files

## 8. Defense/demo explanation template

You can explain the pipeline like this:

"The project CI/CD is implemented using GitLab CI with three stages: build, test, and deploy readiness. Build validates backend compilation and frontend syntax/file integrity. Test runs backend ingestion smoke checks and frontend package validation. Deploy readiness produces backend package artifacts and frontend release artifacts. We optimized runtime by caching pip and npm dependencies and parallelizing backend/frontend jobs. We also resolved CI failures from native package builds by separating CI-safe backend dependencies from full runtime dependencies."

## 9. Learning notes

Key CI/CD concepts learned from this setup:

- Stage separation improves clarity and debugging speed
- Job templates reduce duplication
- Caching dramatically improves repeated run performance
- needs dependencies create controlled execution flow
- Smoke tests are useful when full integration tests are expensive
- Native dependency packages can break CI and should be isolated
- Artifact publishing is important for deployment readiness proof
- GitLab test counts need explicit test report artifacts

## 10. Recommended next improvements

1. Add formal pytest test suite and JUnit report publishing for GitLab Tests tab.
2. Add branch rules so deploy jobs run only on main.
3. Add manual approval for deploy stage in protected environments.
4. Add optional integration test job that boots backend service and validates API endpoints.
5. Add quality jobs (lint/format/security scan) as separate stage before deploy.

## 11. Quick troubleshooting checklist

If backend build fails:

- confirm backend/requirements-ci.txt exists in pushed commit
- confirm .gitlab-ci.yml uses requirements-ci.txt in backend template
- inspect first error line in job log

If test shows 0 in GitLab:

- no issue with stage execution
- add JUnit report publishing to populate Tests tab

If deploy artifacts missing:

- open deploy job log
- verify artifact paths exactly match generated files

---

This CI/CD setup is now structured, explainable, and suitable for project demo and iterative improvement toward production-grade DevOps.
