# CS543 – Web Services
## Assignment 09 of 12: Securing the API

**Project Title:** CampusEats – Secured Menu Catalogue API

**Submitted To:** Dr. Pramit Mazumdar  
**Email:** pramit.mazumdar@iiitvadodara.ac.in

**Institute:** Indian Institute of Information Technology Vadodara  
**Department:** Master of Computer Applications (MCA)

---

## 1. Team Members

| Name | Roll Number |
|---|---|
| Brajakshi Mandloi | 20252651016 |
| Vaishnavi Tiwari | 20252651061 |

## 2. Project Overview

This project extends the REST API developed in Assignment 08. The existing CampusEats REST API is secured using JSON Web Token (JWT) authentication and role-based authorization.

Authenticated users can view menu items, while only users with an authorized restaurant or admin role can add menu items.

## 3. Technologies Used

- Node.js
- Express.js
- JavaScript
- jsonwebtoken
- bcryptjs
- dotenv
- HTML and CSS

## 4. Users and Roles

The application uses demo users with different roles. Use the credentials configured in the project.

| User | Role |
|---|---|
| Customer account | customer |
| Restaurant account | restaurant |
| Admin account (if implemented) | admin |

Passwords must be stored as bcrypt hashes, never as plain text.

## 5. API Routes and Permissions

| HTTP Method | Route | Permission |
|---|---|---|
| POST | `/login` | Public |
| GET | `/items` | Authentication required |
| POST | `/items` | Authentication + restaurant/admin role |

### Authentication

The authentication middleware reads the `Authorization` header, extracts the Bearer token, and verifies it using `jwt.verify()`. It returns HTTP 401 if the token is missing, invalid, or expired.

### Authorization

The `requireRole()` middleware checks the authenticated user's role. Only permitted roles can add menu items. It returns HTTP 403 when an authenticated user does not have the required role.

Authentication must run before authorization.

## 6. Answers to Assignment Questions

### Q1. Which routes require only authentication, and which also require a role?

- `POST /login` – Public route; no authentication is required.
- `GET /items` – Requires authentication only. Any user with a valid JWT can view menu items.
- `POST /items` – Requires authentication and the `restaurant` or `admin` role. Only permitted roles can add menu items.

### Q2. Show one 401 and one 403 from your demo. Why did the server return these codes?

**401 Unauthorized:** When a request is sent to `GET /items` without a valid token, the server returns 401 because the user's identity cannot be authenticated.

**403 Forbidden:** When an authenticated customer tries to add a menu item using `POST /items`, the server returns 403 because the customer does not have the required restaurant/admin role.

**Difference:** 401 means authentication is missing or invalid. 403 means the user is authenticated but does not have permission to perform the requested action.

### Q3. What is inside your JWT payload? Why is it safe to trust the role claim on the server, and why must the secret stay out of your code?

The JWT payload contains the user ID and role. A JWT may also contain standard claims such as `iat` (issued-at time) and `exp` (expiration time).

Example payload (illustrative only; use the actual property names from `server.js`):

```json
{
  "id": 1,
  "role": "restaurant"
}
```

The server should trust the role claim only after verifying the token's signature with `jwt.verify()` and the server-side secret. A JWT payload is encoded, not encrypted, so it should not contain passwords or other secrets.

The JWT secret must not be exposed in source code. It should be read from `process.env.JWT_SECRET` and stored in a local `.env` file. The `.env` file must be listed in `.gitignore`; commit a `.env.example` with a blank value.

## 7. Project Setup and Execution

1. Open the `assignment9` project folder in a terminal.
2. Install dependencies:

```bash
npm install
```

3. Create a local `.env` file:

```env
JWT_SECRET=
```

Set a strong local secret value after the equals sign. Do not commit the real `.env` file.

4. Start the server using the command configured for your project, for example:

```bash
node server.js
```

5. Open the frontend using the local URL configured by your project.

## 8. Testing and Expected Results

| No. | Test Case | Expected Result |
|---|---|---|
| 1 | Request without token | 401 Unauthorized |
| 2 | Successful login | Login succeeds and JWT is returned |
| 3 | `GET /items` with valid token | 200 OK |
| 4 | `POST /items` with restaurant role | 201 Created |
| 5 | `POST /items` with customer role | 403 Forbidden |

## 9. Screenshots

Upload the actual screenshots into the `screenshots` folder using the filenames below. The images will appear here on GitHub once those files are committed.

### 9.1 – 401 Unauthorized

![401 Unauthorized](screenshots/01-401.jpg)

### 9.2 – Successful Login

![Successful Login](screenshots/02-login.jpg)

### 9.3 – GET /items (200 OK)

![GET items - 200 OK](screenshots/03-get-items.jpg)

### 9.4 – POST /items (201 Created)

![POST items - 201 Created](screenshots/04-201-created.jpg)

### 9.5 – POST /items (403 Forbidden)

![POST items - 403 Forbidden](screenshots/05-403-forbidden.jpg)

## 10. Demo Video and Google Drive

**Google Drive Folder – Assignment 09: Securing the API**

[Click here to view the Assignment 09 demo video and screenshots](https://drive.google.com/drive/folders/1DKcAehqyIdNjKUugZAlQ3eXbqZVwu3zE?usp=sharing)

The folder is intended to contain:

1. 401 Unauthorized screenshot
2. Successful login and JWT screenshot
3. 200 OK – `GET /items` screenshot
4. 201 Created – `POST /items` screenshot
5. 403 Forbidden – customer role screenshot
6. Short demo video

## 11. Conclusion

This assignment secures the existing CampusEats REST API using JWT-based authentication and role-based authorization. Bcrypt hashing protects user passwords, JWT verification authenticates users, and middleware restricts access to protected routes. The implementation demonstrates how authentication and authorization help prevent unauthorized access and data modification.

---

**Course:** CS543 – Web Services  
**Assignment:** 09 of 12 – Securing the API  
**Submitted To:** Dr. Pramit Mazumdar  
**Institute:** IIIT Vadodara
