# CampusEats — REST API (CS543 Assignment 8)

**Course:** CS543 — Web Services  
**Assignment:** 8 of 12 — Build One CampusEats Service as a REST API  
**Instructor:** Dr. Pramit Mazumdar  
**Selected service:** Menu / Catalogue  
**Technology:** Node.js, Express, HTML, CSS and browser `fetch()`  
**Data source:** In-memory JavaScript array.

## 1. Project overview

This project exposes the CampusEats Menu / Catalogue service through a REST API. Users can view all menu items, retrieve one item by its ID, and create a new menu item through a simple web page.

## 2. Technologies used

- Node.js
- Express.js
- HTML5 and CSS3
- JavaScript and browser Fetch API
- JSON

## 3. Data

The application uses an in-memory JavaScript array containing four seed records:

| ID | Item | Price | Available |
|---:|---|---:|---|
| 1 | Masala Dosa | ₹60 | Yes |
| 2 | Veg Burger | ₹80 | Yes |
| 3 | Paneer Roll | ₹90 | Yes |
| 4 | Cold Coffee | ₹50 | No |

New records are added to this array. A database is not required for this assignment.

## 4. REST API routes

| HTTP method | Path | Purpose |
|---|---|---|
| GET | `/items` | Get all menu items |
| GET | `/items/:id` | Get one menu item by ID |
| POST | `/items` | Create a new menu item |

## 5. HTTP status codes

- **200 OK:** A GET request successfully returns the item list or one item.
- **201 Created:** A new menu item is successfully created.
- **404 Not Found:** The requested item ID does not exist.
- **422 Unprocessable Content:** Required or submitted data is invalid, such as a missing name or invalid price.

## 6. Answers to the assignment questions

### Q1. Which CampusEats service did you pick, and what are its routes (method + path)?

We selected the **Menu / Catalogue** service. Its routes are `GET /items`, `GET /items/:id`, and `POST /items`.

### Q2. Which status codes did you return, and for which outcomes (200 / 201 / 404 / 422)?

`200` is returned when a GET request succeeds. `201` is returned when a new menu item is created. `404` is returned when the requested item ID is not found. `422` is returned when POST input is invalid, for example when the item name is missing or the price is not a positive number.

### Q3. Where did you use req.params and where req.body? Why does POST need express.json()?

`req.params.id` is used in `GET /items/:id` to read the item ID from the URL. `req.body` is used in `POST /items` to read the submitted item's name, price, and availability. `express.json()` parses incoming JSON request data and makes it available in `req.body`; without this middleware, Express does not automatically parse the JSON body.

## 7. Front-end

The HTML/CSS/JavaScript page fetches and displays the menu list. Its form sends a POST request to create a menu item and refreshes the displayed list after a successful response. Express serves the page using static middleware.

## 8. How to run the project

1. Install Node.js (LTS).
2. Open a terminal in the project folder (the folder containing `package.json`).
3. Run `npm install`.
4. Run `npm start`.
5. Open `http://localhost:4008` in a browser.

On Windows, `RUN.bat` can also be used. On macOS/Linux, run `bash RUN.sh`.

## 9. Screenshots and demonstration video

The Google Drive folder below contains the demonstration video and the before-POST and after-POST screenshots:

**[Open Assignment 8 Demonstration Video and Screenshots (Google Drive)](https://drive.google.com/drive/folders/1RwpLPbsQ6ZnQAOwYE6WpudW9VSzY3KNk?usp=sharing)**

## 10. Team members

- **Brajakshi Mandloi** — Roll Number: [20252651016]
- **Vaishnavi Tiwari** — Roll Number: [20252651061]

## 11. Conclusion

This assignment demonstrates a basic REST API using Node.js and Express, including GET and POST routes, URL parameters, JSON body parsing, input validation, HTTP status codes, and a simple front-end.
