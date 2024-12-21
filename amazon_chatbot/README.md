
# Amazon Product Browser

## Setup Instructions

1. **Clone the Repository**
```
git clone https://github.com/brianerd/amazon_platform_project.git
cd amazon_platform_project
```

2. **Set Up Virtual Environment**
```
# Create virtual environment
python -m venv venv

# Activate virtual environment

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. **Install Dependencies**
```
pip install -r requirements.txt
```

4. **Get Product Data**
- Unzip the data file in amazon_backend/data/amazon_data.zip

5. **Database Setup**
```
python manage.py migrate
```

6. **Run Development Server**
```
python manage.py runserver
```

7. **Access the Application**
- Open your web browser
- Visit `http://127.0.0.1:8000/`
