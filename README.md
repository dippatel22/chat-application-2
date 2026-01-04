Chat Application

This is a full-stack chat application built with React on the frontend and FastAPI on the backend. MongoDB is used as the database.
The frontend and backend run as separate services and communicate through APIs.

This guide explains how to set up and run the project locally.

Project Structure
chat-application/
├── frontend/
├── backend/
└── README.md

Requirements

Before running the project, make sure you have the following installed:

Node.js (v18 or above)

npm

Python (v3.9 or above)

MongoDB (local or cloud)

Frontend Setup

Move to the frontend directory:

cd frontend


Install dependencies:

npm install


Start the development server:

npm run dev


The frontend will start on the port shown in the terminal (usually http://localhost:5173).

Backend Setup

Move to the backend directory:

cd backend


Install required Python packages:

pip install -r requirements.txt

Environment Variables

Create a .env file inside the backend folder and add the following values:

MONGODB_URL=
DATABASE_NAME=
SECRET_KEY=


Example:

MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=chat_app
SECRET_KEY=your_secret_key


Make sure the .env file is not committed to the repository.

Running the Backend

Start the backend server using:

uvicorn main:app --host 0.0.0.0 --port 10000


The backend will run on:

http://localhost:10000

Running the Application

Start the backend first

Then start the frontend

Ensure MongoDB is running and accessible

Open the frontend URL in your browser

The frontend depends on the backend, so the backend must be running for the application to work properly.
