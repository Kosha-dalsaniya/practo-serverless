# Practo on AWS: Serverless Appointment Booking

Course project for IT-457 Cloud Computing 

Theme - Serverless and Startups

We studied how Practo uses AWS and built a small serverless booking API of our own
to measure the cold start effect. The API is our own design, not Practo's system.

## Architecture

Client script -> Amazon API Gateway (HTTP API) -> AWS Lambda (Python, 128 MB) -> Amazon DynamoDB

## Main results

- Cold start: 1678 ms on average, against 63.5 ms for a warm request (about 26x slower)
- Scaling: Lambda scaled out automatically up to the account limit of 10 concurrent executions
- Estimated cost: about $0.0020 per 1,000 warm requests at list prices

## Contents

- `lambda/` - the Lambda handler
- `scripts/` - `measure_practo.py` (cold vs warm test) and `scale_practo.py` (concurrency test)
- `data/` - raw measurements as CSV
- `results/` - spreadsheet and graphs
- `report/` - Week 2 report (PDF)

## Running the scripts

Set `API_URL` in each script to your own API Gateway invoke URL, then run
`python3 scripts/measure.py` or `python3 scripts/scale.py`.
