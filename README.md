# CampusEats — Menu Service in GraphQL (Assignment 7)

## Team Members

- **Brajakshi Mandloi** — Roll No. 20252651016
- **Vaishnavi Tiwari** — Roll No. 20252651061

## Demonstration Video and Screenshots

**Google Drive Folder:**  
https://drive.google.com/drive/folders/17vNkjCRJiTylgmmBA2pTqUqNFo6wpKXL?usp=sharing

The folder contains the demonstration video and before/after mutation screenshots.

## Project Overview

This project implements the CampusEats Menu/Dishes service using GraphQL. It demonstrates how clients can retrieve dish information and add a new dish through a GraphQL mutation.

## Technologies

- GraphQL
- Node.js
- Apollo Server
- HTML, CSS and JavaScript
- Database configured by the project

## Project Files

- `schema.graphql` — GraphQL types, queries and mutations
- `server.js` — Server and GraphQL resolvers
- `db.js` — Database connection and queries
- `schema.sql` — Table definition and sample data
- `public/index.html` — Frontend page

## Example Query

```graphql
query {
  dishes {
    id
    name
    price
    available
  }
}
```

## Example Mutation

```graphql
mutation {
  addDish(input: { name: "Paneer Roll", price: 90 }) {
    id
    name
    price
  }
}
```

## How to Run

Follow the run instructions provided in the project files. Start the server, open the frontend page in your browser, list the dishes, and add a dish such as Paneer Roll with price 90.

## Answers to Assignment Questions

### 1. Which CampusEats service did you pick?

We selected the **Menu/Dishes service**, which allows clients to retrieve dish information and add new dishes.

### 2. Name one field a client can skip and one it cannot. Why do we use `!`?

A client can omit a nullable field from its query if it does not need that information. A non-null field, marked with `!` in the schema, cannot return `null` in a valid response. However, the client does not have to request every non-null field in every query.

### 3. Map the query to SQL. Which part became the WHERE clause, and which resolver ran INSERT?

When a dish is retrieved by ID, the ID argument can be used in a SQL condition such as `WHERE id = ?`. The `addDish` mutation resolver runs the SQL `INSERT` statement to add a new dish.

## Conclusion

This project demonstrates a GraphQL API with a query for retrieving dishes and a mutation for adding a dish to the CampusEats menu.
