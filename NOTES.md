# CampusEats Assignment 4 - Order Service

## Team Members

1. Brajakshi Mandloi (20252651016)
2. Vaishnavi Tiwari (20252651061)

---

# A4 Resource Table

| Method | URL | What it does | Success Code | Failure Codes |
|----------|----------|----------|----------|----------|
| POST | /orders | Create a new order | 201 | 400, 422 |
| GET | /orders/{id} | Get a specific order | 200 | 404 |
| GET | /orders?item={item} | List/filter orders | 200 | 400 |
| POST | /orders/{id}/cancellation | Cancel an order | 202 | 404, 409 |

---

# A5 Justification

The cancellation operation was the hardest to map into a REST resource.
Initially, a verb-based endpoint such as `/cancelOrder` was considered.
However, REST encourages resources rather than actions in URLs.
Therefore, cancellation was modelled as a sub-resource:
`/orders/{id}/cancellation`.

---

# D3 Fallback Reasoning

The Order Service depends on the Payment Service.
If the Payment Service is unavailable, the order request fails and an error response is returned.
This approach prevents inconsistent states where an order is created but payment has not been verified.

---

# Question 1

The WSDL file from Assignment 3 contains SOAP-specific information such as message definitions, bindings, and service ports.

The OpenAPI file focuses mainly on REST endpoints, request bodies, response codes, and schemas.

Two things declared in WSDL that OpenAPI does not require are:

1. SOAP Binding
2. SOAP Message Definitions

---

# Question 2

SOAP Fault from Assignment 3:

```xml
<soap:Fault>
   <faultcode>SOAP-ENV:Client</faultcode>
   <faultstring>card_declined</faultstring>
</soap:Fault>
```

REST Replacement:

```json
{
  "type": "payment-error",
  "title": "Payment Declined",
  "status": 422,
  "detail": "Payment was declined by the payment provider."
}
```

HTTP Status:

```http
422 Unprocessable Entity
```

Returning an error inside a 200 OK response is problematic because intermediate systems, caches, and clients may treat the request as successful even though the operation actually failed.

---

# Question 3

In the REST-based solution:

- Publish still exists through OpenAPI documentation.
- Find still exists through documentation repositories and API catalogues.
- Bind still exists when clients call the API endpoint.

  Method Map
Action	Method	URL
Create Order	POST	/orders
List Orders	GET	/orders
Get Order	GET	/orders/{id}
Update Order	PUT	/orders/{id}
Delete Order	DELETE	/orders/{id}
Cancel Order	POST	/orders/{id}/cancel

Safe and Idempotent Endpoints
Endpoint	Safe	Idempotent
GET /orders	Yes	Yes
GET /orders/{id}	Yes	Yes
PUT /orders/{id}	No	Yes
DELETE /orders/{id}	No	Yes
POST /orders	No	No
POST /orders/{id}/cancel	No	Yes
Safe Retry Plan
Endpoint	Mechanism	Reason
POST /orders	Idempotency-Key	Prevent duplicate order creation
GET /orders/{id}	If-None-Match	Avoid unnecessary data transfer
PUT /orders/{id}	If-Match	Prevent overwriting newer updates
Headers Table
Endpoint	Request Headers	Response Headers
POST /orders	Authorization, Idempotency-Key	Location
GET /orders/{id}	Authorization, If-None-Match	ETag, Cache-Control
PUT /orders/{id}	Authorization, If-Match	ETag
DELETE /orders/{id}	Authorization	-
# Question 4

The validation responsibility is now handled by the `validate()` function in the application code.

Without this validation, requests with missing required fields such as item names or quantities could enter the system and create invalid orders.

---

# Question 5

SOAP may still be preferred for payment processing.

SOAP provides stronger contracts, formal message structures, and support for enterprise-level standards such as WS-Security.

These guarantees are useful when handling sensitive financial transactions.

---

# Conclusion

The REST version of CampusEats Order Service is simpler and more lightweight than the SOAP-based design. OpenAPI replaces WSDL for API description, HTTP status codes replace SOAP faults, and REST resources replace operation-based service contracts.






## Method Map

| Action | Method | URL |
|----------|----------|----------|
| Create Order | POST | /orders |
| List Orders | GET | /orders |
| Get Order | GET | /orders/{id} |
| Update Order | PUT | /orders/{id} |
| Delete Order | DELETE | /orders/{id} |
| Cancel Order | POST | /orders/{id}/cancel |



## Safe and Idempotent Endpoints

| Endpoint | Safe | Idempotent |
|-----------|------|------------|
| GET /orders | Yes | Yes |
| GET /orders/{id} | Yes | Yes |
| PUT /orders/{id} | No | Yes |
| DELETE /orders/{id} | No | Yes |
| POST /orders | No | No |
| POST /orders/{id}/cancel | No | Yes |
Step 3: Headers Table



## Headers Table

| Endpoint | Request Headers | Response Headers |
|-----------|----------------|------------------|
| POST /orders | Authorization, Idempotency-Key | Location, Content-Type |
| GET /orders/{id} | Authorization, If-None-Match | ETag, Cache-Control |
| PUT /orders/{id} | Authorization, If-Match | ETag |
| DELETE /orders/{id} | Authorization | - |
| OPTIONS /orders/{id} | - | Allow |
Step 4: Safe Retry Plan


## Safe Retry Plan

| Endpoint | Mechanism | Reason |
|-----------|-----------|---------|
| POST /orders | Idempotency-Key | Prevent duplicate order creation |
| GET /orders/{id} | If-None-Match | Avoid unnecessary data transfer |
| PUT /orders/{id} | If-Match | Prevent overwriting newer updates |
**Headers Table**
Endpoint	Request Headers	Response Headers
POST /orders	Authorization, Idempotency-Key	Location
GET /orders/{id}	Authorization, If-None-Match	ETag, Cache-Control
PUT /orders/{id}	Authorization, If-Match	ETag
DELETE /orders/{id}	Authorization	-

## Safe Retry Plan

| Endpoint | Mechanism | Reason |
|-----------|-----------|---------|
| POST /orders | Idempotency-Key | Prevent duplicate order creation if request is retried |
| GET /orders/{id} | If-None-Match | Avoid sending unchanged data and support 304 Not Modified |
| PUT /orders/{id} | If-Match | Prevent overwriting changes made by another client |
Q1
## Q1

1. POST /orders
   - Success Status: 201 Created
   - Important Header: Location
   - Reason: It tells the client where the newly created order resource is located.

2. GET /orders/{id}
   - Success Status: 200 OK
   - Important Header: ETag
   - Reason: It supports caching and conditional requests.

3. DELETE /orders/{id}
   - Success Status: 204 No Content
   - Important Header: Authorization
   - Reason: Only authorized users should delete resources.
Q2
## Q2

Safe endpoints:
- GET /orders
- GET /orders/{id}

Idempotent endpoints:
- GET /orders
- GET /orders/{id}
- PUT /orders/{id}
- DELETE /orders/{id}
- POST /orders/{id}/cancel

Neither safe nor idempotent:
- POST /orders

POST /orders is made retry-safe using the Idempotency-Key header. Repeating the same request with the same key returns the original result instead of creating a duplicate order.
Q3
## Q3

Example ETag:
"1-PENDING"

304 Request:

GET /orders/1
If-None-Match: "1-PENDING"

Response:
304 Not Modified

This saves bandwidth because the resource has not changed.

412 Request:

PUT /orders/1
If-Match: "1-PENDING"

If the resource has changed and the ETag no longer matches:

Response:
412 Precondition Failed

This prevents one client from accidentally overwriting another client's changes.
Q4
## Q4

400 Bad Request Example:

POST /orders

{
  "studentId": "S1"
}

Reason:
Required fields are missing.

422 Unprocessable Entity Example:

POST /orders

{
  "studentId": "S1",
  "itemId": "I1",
  "quantity": -5
}

Reason:
The JSON structure is valid, but the business rule is violated because quantity cannot be negative.
