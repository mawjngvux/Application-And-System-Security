# Flask Web Application

This is a simple web application built using Flask. It serves as a starting point for developing web applications with Python.

## Project Structure

```
flask-web-app
├── app
│   ├── __init__.py
│   ├── routes.py
│   └── templates
│       └── index.html
├── requirements.txt
├── run.py
└── README.md
```

## Setup Instructions

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd flask-web-app
   ```

2. **Create a virtual environment:**
   ```
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```

4. **Install the required dependencies:**
   ```
   pip install -r requirements.txt
   ```

## Running the Application

To run the application, execute the following command:

```
python run.py
```

The application will be available at `http://127.0.0.1:5000/`.

## Usage

Visit the home page to see the application in action. You can modify the templates and routes to customize the application as needed.