# HTTP Log

## Request 1
Command:
curl.exe -i https://jsonplaceholder.typicode.com/posts/1

Status Code: 200 OK
Content-Type: application/json

Meaning:
Request successful.

---

## Request 2
Command:
curl.exe -i https://jsonplaceholder.typicode.com/posts/2

Status Code: 200 OK
Content-Type: application/json

Meaning:
Request successful.

---

## Request 3
Command:
curl.exe -i https://jsonplaceholder.typicode.com/users/1

Status Code: 200 OK
Content-Type: application/json

Meaning:
User data returned successfully.

---

## Request 4
Command:
curl.exe -i https://jsonplaceholder.typicode.com/comments/1

Status Code: 200 OK
Content-Type: application/json

Meaning:
Comment data returned successfully.

---

## Request 5
Command:
curl.exe -i https://jsonplaceholder.typicode.com/posts/999999

Status Code: 404 Not Found
Content-Type: application/json

Meaning:
Requested resource does not exist.
