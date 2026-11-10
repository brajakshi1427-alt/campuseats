# CampusEats — Securing the API (Assignment 9)

**Course:** CS543 Web Services  
**Institute:** Indian Institute of Information Technology Vadodara (IIIT Vadodara)  
**Faculty:** Dr. Pramit Mazumdar  
**Service Secured:** Menu / Catalogue (Same service as Assignment 8)  
**Technology Stack:** Node.js, Express.js, JSON Web Token (JWT), bcryptjs, dotenv

## Team Members

| S. No. | Name | Roll Number |
|---|---|---|
| 1 | Brajakshi Mandloi | 20252651016 |
| 2 | Vaishnavi Tiwari | 20252651061 |

**GitHub Repository:** https://github.com/brajakshi1427-alt/campuseats

**Demo Video and Screenshots (Google Drive):**  
https://drive.google.com/drive/folders/1DKcAehqyIdNjKUugZAlQ3eXbqZVwu3zE?usp=sharing

---

## 1. How to Run the Project

### Windows

1. Open the Assignment 9 project folder.
2. Double-click `RUN.bat`.
3. The script installs the required packages if they are not already installed.
4. It creates a `.env` file with a random `JWT_SECRET` if one does not exist.
5. The server starts at:

`http://localhost:4009`

### Mac/Linux

Run the following command:

```bash
bash RUN.sh
```

### Manual Setup

```bash
npm install
```

Copy `.env.example` to `.env` and add a long, random secret value:

```env
PORT=4009
JWT_SECRET=your_long_random_secret_key_here
JWT_EXPIRES_IN=1h
```

Then start the application:

```bash
npm start
```

**Important:** Never upload `.env` to GitHub. Only upload `.env.example`.

---

## 2. Demo User Accounts

The application contains three demonstration users. Their passwords are stored as bcrypt hashes, not as plain-text passwords.

| Username | Password | Role |
|---|---|---|
| customer | customer123 | customer |
| restaurant | restaurant123 | restaurant |
| admin | admin123 | admin |

---

## 3. API Routes

| HTTP Method | Endpoint | Authentication / Authorization | Expected Response |
|---|---|---|---|
| POST | `/login` | Public route | 200 OK or 401 Unauthorized |
| GET | `/items` | Valid JWT required | 200 OK or 401 Unauthorized |
| GET | `/items/:id` | Valid JWT required | 200 OK, 404 Not Found or 401 Unauthorized |
| POST | `/items` | Valid JWT + restaurant/admin role | 201 Created, 422 Validation Error, 401 Unauthorized or 403 Forbidden |

---

## 4. Testing the Secured API

The following five test cases demonstrate authentication and role-based authorization.

### Test Case 1: Access without a token

```bash
curl -i http://localhost:4009/items
```

**Expected result:** `401 Unauthorized`

The server rejects the request because no authentication token is provided.

### Test Case 2: User Login

```bash
curl -i -X POST http://localhost:4009/login -H "Content-Type: application/json" -d "{\"username\":\"customer\",\"password\":\"customer123\"}"
```

**Expected result:** `200 OK`

The server verifies the credentials and returns a JWT access token.

### Test Case 3: Access menu using a valid token

Replace `<TOKEN>` with the token received after login.

```bash
curl -i http://localhost:4009/items -H "Authorization: Bearer <TOKEN>"
```

**Expected result:** `200 OK`

The authenticated customer can successfully view the menu items.

### Test Case 4: Restaurant creates a new menu item

First log in as a restaurant:

```bash
curl -i -X POST http://localhost:4009/login -H "Content-Type: application/json" -d "{\"username\":\"restaurant\",\"password\":\"restaurant123\"}"
```

Use the returned restaurant token:

```bash
curl -i -X POST http://localhost:4009/items -H "Authorization: Bearer <RESTAURANT_TOKEN>" -H "Content-Type: application/json" -d "{\"name\":\"Veg Sandwich\",\"price\":75}"
```

**Expected result:** `201 Created`

The restaurant user is authorized to add a new menu item.

### Test Case 5: Customer tries to create a menu item

Use the customer token:

```bash
curl -i -X POST http://localhost:4009/items -H "Authorization: Bearer <TOKEN>" -H "Content-Type: application/json" -d "{\"name\":\"Test\",\"price\":10}"
```

**Expected result:** `403 Forbidden`

The customer is authenticated but does not have permission to create menu items.

---

## 5. Answers to Assignment Questions

### Q1. Which routes need only authentication, and which also need a role?

The `GET /items` and `GET /items/:id` routes require only authentication. Any user with a valid JWT token can access these routes, regardless of whether their role is customer, restaurant or admin.

The `POST /items` route requires both authentication and role-based authorization. Only users with the restaurant or admin role are allowed to create new menu items.

The `POST /login` route is public because users must be able to log in before receiving an authentication token.

### Q2. Give one example of a 401 response and one example of a 403 response. Why are they different?

**401 Unauthorized:**

When a user tries to access `GET /items` without providing an authentication token, the server returns:

```json
{
  "error": "Missing token. Send Authorization: Bearer <token>"
}
```

HTTP 401 is returned because the server cannot authenticate the user. No valid identity has been provided.

**403 Forbidden:**

When a customer tries to create a menu item using a valid JWT token, the server returns:

```json
{
  "error": "Forbidden: your role may not do this"
}
```

HTTP 403 is returned because authentication is successful, but the customer role does not have permission to perform this operation.

**Difference:** 401 means the user is not successfully authenticated, whereas 403 means the user is authenticated but does not have the required permission.

### Q3. What is inside the JWT payload? Why can the role claim be trusted? Why should the secret be kept out of the source code?

The JWT payload contains the following information:

```json
{
  "id": 1,
  "role": "customer",
  "iat": 1794300000,
  "exp": 1794303600
}
```

Here:

- `id` represents the user's unique ID.
- `role` represents the user's assigned role.
- `iat` represents the token issue time.
- `exp` represents the token expiry time.

The role claim can be trusted after successful verification because the JWT is digitally signed using the HS256 algorithm and the server's secret key.

If an attacker changes the role from customer to admin, the token signature becomes invalid. The `jwt.verify()` function rejects the modified token.

The secret key should not be hard-coded in the source code because anyone who obtains it could create forged tokens. Therefore, the application reads the secret using `process.env.JWT_SECRET` from the `.env` file.

The `.env` file is included in `.gitignore`, so it is not uploaded to GitHub. Only `.env.example`, containing a blank secret placeholder, is committed.

---

## 6. Security Implementation Details

The following security features are implemented in the application:

1. **Password Hashing:** Passwords are hashed using `bcryptjs` before being stored.
2. **Password Verification:** `bcrypt.compare()` verifies the password during login.
3. **JWT Authentication:** `jsonwebtoken` generates and verifies authentication tokens.
4. **Token Expiration:** Tokens expire after the configured duration, which is one hour by default.
5. **Role-Based Authorization:** The `requireRole()` middleware restricts menu creation to restaurant and admin users.
6. **Authentication Middleware:** The `auth` middleware checks whether the request contains a valid Bearer token.
7. **Input Validation:** Invalid menu item data is rejected with HTTP 422.
8. **Secure Secret Management:** The JWT secret is stored in `.env`, not in the source code.
9. **Generic Login Error:** Incorrect usernames and passwords return the same error message to avoid revealing which usernames exist.
10. **Middleware Order:** The authentication middleware executes before the role authorization middleware.

### Middleware Execution

```text
Client Request
      |
      v
Authentication Middleware
      |
      v
Is JWT valid?
   /       \
 No         Yes
 |           |
401       Role Check
              |
              v
       Is role allowed?
          /       \
        No         Yes
        |           |
       403       Execute Route
                    |
                    v
                API Response
```

---

## 7. Demo Video and Screenshots

The following five screenshots should be captured as proof of the implementation:

1. API request without a token showing `401 Unauthorized`.
2. Successful customer login showing `200 OK` and JWT response.
3. Authenticated menu request showing `200 OK`.
4. Restaurant adding a menu item showing `201 Created`.
5. Customer attempting to add a menu item showing `403 Forbidden`.

The browser interface is available at:

`http://localhost:4009`

The five demonstration cases can also be executed using `DEMO.bat` on Windows or `bash DEMO.sh` on Mac/Linux. The output is saved in `demo-output.txt`.

Upload the screenshots and demonstration video to the Google Drive folder provided above.

---

## 8. Submission Checklist

- [ ] Complete the implementation of JWT authentication.
- [ ] Implement bcrypt password hashing.
- [ ] Implement authentication and role-based authorization middleware.
- [ ] Test all five required security cases.
- [ ] Capture screenshots of the API responses.
- [ ] Record a short demonstration video.
- [ ] Upload the video and screenshots to Google Drive.
- [ ] Upload the Assignment 9 project folder to the CampusEats GitHub repository.
- [ ] Ensure `.env` is not committed to GitHub.
- [ ] Include `.env.example` in the repository.

---

## Conclusion

In this assignment, the CampusEats Menu/Catalogue REST API from Assignment 8 is secured using JWT-based authentication and role-based authorization.

Password hashing using bcryptjs protects user credentials, while JWT tokens allow the server to authenticate requests. Role-based middleware ensures that only authorized restaurant and admin users can create menu items.

The implementation demonstrates the difference between HTTP 401 Unauthorized and HTTP 403 Forbidden responses and shows how environment variables help protect sensitive application secrets.

**Submitted by:**  
Brajakshi Mandloi — 20252651016  
Vaishnavi Tiwari — 20252651061  

**Submitted to:** Dr. Pramit Mazumdar  
**Course:** CS543 Web Services  
**Institute:** IIIT Vadodara
