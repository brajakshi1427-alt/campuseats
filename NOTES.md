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

Traditional UDDI registries are no longer used.
Their role has largely been replaced by API documentation and service URLs.

---

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
