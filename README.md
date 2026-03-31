# Company Outreach AI

Company Outreach AI is a FastAPI service that analyzes a company website and returns:

- business summary
- positioning
- target customer
- likely bottleneck
- messaging / conversion gaps
- best offer angle
- final outreach-ready brief

## Live API
Deployed on Vercel.

## Main Endpoint
`POST /analyze`

### Example Request
```json
{
  "url": "https://acquire.com/",
  "debug": false
}