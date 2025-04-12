# FastAPI Example Project

Perhaps, use as boilerplate / template for further work

## Setup Instructions

Create a Virtual Environment.  You should only have to do this once

```
python -m venv env
```

Activate it

```
source env/bin/activate
```

Install Dependencies

```
pip install -r REQUIREMENTS.txt
```

## Usage

  1. Activate the virtual environment
  
     ```
     source env/bin/activate
     ```
     
  2. Start Fast API In Development Mode
  
     ```
     fastapi dev webapp/main.py
     ```
     
## Testing

Run tests using Pytest

```
pytest -vs
```

### Testing with Coverage


```
pytest --cov=webapp
```

or with a HTML report

```
pytest --cov=webapp --cov-report html
```
