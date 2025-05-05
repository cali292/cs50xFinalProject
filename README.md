# SMART TROCK
#### Video Demo:  <URL https://youtu.be/fpCN0HOogcE>
#### Description:
At my job in a pharmaceutical delivery and distribution company, we used to manage medication exchanges between pharmacists manually. This process required identifying the sender, recipient, and the sender’s delivery round, making it inefficient and error-prone.

The goal of this project is to automate these tasks by generating exchange forms for our pharmacist clients and customer service team.

For testing purposes, here are three test accounts:

    pharmatest1@gmail.com
    pharmatest2@gmail.com
    serviceclienttest@gmail.com
    All test accounts share the same password: fp50test

##### database: 
For the presentation he application runs on a database with randomly generated client names and addresses to simulate real data.

##### Register route :
The registration form includes five fields:
    Email
    Pharmacy Name
    Client Number (specific to my company)
    Password
    Password Confirmation
To ensure only legitimate customers can register, I implemented specific validations:
    The pharmacy name must be selected from a pre-populated datalist sourced from the database.
    The client number must match the one associated with the selected pharmacy.
If these two fields don’t match, registration is denied. The rest of the form functions like a standard registration page, including password confirmation to prevent errors.

##### Log-in route :
Users must log in to access the application. To prevent brute-force attacks, a user is locked out for 5 minutes after 3 failed login attempts.

This feature is supported by two additional database columns:
failed_attempts: Tracks incorrect login attempts.
lockout_until: Stores the time until the account is unlocked.
##### Index route :
The index page is designed to ensure that all key features are accessible within three clicks maximum.

The navigation bar adapts to the type of user:

Pharmacists: Access options to generate and manage exchanges:
    New Exchange
    Shipment
    Reception
    History
Customer Service Users: Access tools to manage pharmacist exchanges:
    Scan
    Research

##### Exchange route :
Pharmacists can create an exchange on this route. They select a pharmacy from a datalist and submit the form. When the form is submitted:

The app queries the database to retrieve sender and recipient details.
A function (generator_qr) generates:
    A daily-reset order number.
    A QR code in the format: date # order_number # sender_number # recipient_number.
A PDF is generated, containing:
    Sender and recipient details.
    Delivery rounds.
    The generated QR code.
The PDF is displayed in a new browser window and is ready for printing.

The QR code is generated using the qrcode library.
The io library converts the QR code image to binary data.

##### Sending, Reception and history route :
These routes display exchange details in tables styled with Bootstrap. Each table contains:
    Date
    Recipient Name
    Status
    Order Number
Statuses are color-coded:
    Green (Processed): The processing column in the database is set to 1.
    Red (In Progress): The processing column remains 0.

##### Scan route :
This route is restricted to customer service users.

When a package arrives, the service team scans the QR code, which updates the processing column in the database.
Pharmacists can then track the package’s progress on their Shipment or Reception pages.
##### Research route :
This route is also restricted to customer service users. It allows them to search for packages using various fields:
    Client Number
    Client Name
    Date
The search results are displayed in a dynamic table with detailed information about the exchanges.
##### Things to change : 
Error Handling:
Currently, I use both apology messages and flash messages to handle user errors. In the future, I will standardize error handling by exclusively using flash messages for consistency.

README Updates:
For this project, I wrote the README after completing the entire application. In future projects, I plan to update the README incrementally as I implement each route or feature.


