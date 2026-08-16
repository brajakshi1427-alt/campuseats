CampusEats

Project Description

CampusEats is a web-based food ordering system designed for students and campus users. It allows users to view available food items, place orders, and manage their food-ordering activities through different services.

Objectives

The main objective of CampusEats is to provide a simple and convenient food ordering system for a campus environment.

Main Capabilities

- User management
- Browse food catalogue
- Check food item availability
- Place food orders
- Manage orders
- Track order status
- Manage food items
- Manage payments

Services

The CampusEats system is divided into independent services. Each service owns and manages its own data and provides operations through defined contracts.

User Service

Manages user-related information and user operations.

Catalogue Service

Manages food items, menus, prices, and availability.

Order Service

Handles order creation and order-related operations.

Payment Service

Handles payment-related operations.

Technologies

- Web Services
- REST APIs
- Database
- GitHub
- Draw.io / diagrams.net

Project Documents

The repository contains the following design documents:

- "design.pdf" — Services, capabilities, contracts, placeOrder specification, and service validation
- "services.drawio" — Editable service design diagram
- "services.png" — Exported service design diagram
- "schema.drawio" — Editable database ER diagram
- "schema.png" — Exported database ER diagram
- "schema.sql" — Database CREATE TABLE statements

Team Members

- Brajakshi Mandloi 20252651016
- Vaishnavi Tiwari  20252651061

Project Structure

CampusEats/
├── README.md
├── design.pdf
├── services.drawio
├── services.png
├── schema.drawio
├── schema.png
└── schema.sql

Conclusion

CampusEats provides a service-oriented design for campus food ordering. The system separates responsibilities into independent services with clear contracts and separate data ownership. This design makes the system easier to maintain, extend, and develop.
