# VA QC App - Valve Tracking System

Phase 1: Foundation Complete

## Features
- Login system (rob/lerato/gideon/demo - password: vulcan123)
- Dashboard with valve list
- Valve detail view with stages
- Google Sheets integration
- Mobile-responsive design

## Run Locally
```bash
cd va-qc-app
./run.sh dev
```

## Deploy to VPS
```bash
cd va-qc-app
docker build -t va-qc-app .
docker run -d -p 8000:8000 va-qc-app
```

## Access
- URL: http://localhost:8000
- Login with demo credentials above

## Next Phases
- Phase 2: Receiving workflow with photo upload
- Phase 3: Stripped workflow
- Phase 4: Before Assembly + Final workflows
- Phase 5: PDF generation + photo zipping
- Phase 6: Client portal + notifications