# CampusEats - Orders service (REST) - Assignment 6

Flask service: resources + OpenAPI contract (A4), HTTP methods + headers + caching (A5),
honest status codes + Problem Details + validation (A6). The same code satisfies all three.

```
openapi.yaml  app.py  models.py  store.py  errors.py     contract, routes, validate(), one error shape
payments_client.py  payments_stub.py                     hardened outbound call + fake Payments service
make_transcript.py  run_evidence.py                      evidence generators
tests/                                                   pytest
NOTES.md                                                 answers for this assignment
```

## Run (Windows CMD, inside this folder)

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run_evidence.py
```

`run_evidence.py` runs the tests, validates `openapi.yaml`, starts both services, records the real
curl transcript and stops everything. To try the service by hand instead:

```
:: terminal 1
python payments_stub.py
:: terminal 2
set PAYMENTS_URL=http://127.0.0.1:5001
python app.py
```

Every `/orders` call needs `Authorization: Bearer <anything>`, and a body needs
`Content-Type: application/json`. Menu items: dosa, samosa, tea, thali, sandwich (pizza is sold out on purpose).
