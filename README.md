# Installation Instructions #

There's no need to install - the whole application is running live here:

## https://bake.ardmillan.ie ##

Log in using the following test credentials:

Username: **user@ardmillan.ie**

Password: **Bake123!**

if you'd rather interact with the API directly, you can have a look at the Swagger UI here:

## https://api.ardmillan.ie/docs ##

or, the ReDoc UI here:

## https://api.ardmillan.ie/redoc ##

You won't however, be able to *interact* with the API directly using the Swagger UI or ReDoc UI (beyond the hello world endpoint),
as a JWT from Cognito is required to access the API and no manual process is in place to retrieve this.


## To install locally ##

For security the **.env** file has been omitted from the source files as it contains API keys and AWS credentials.  

If you need it, please contact me directly:

**07841903012**

**pa1983@gmail.com**


To install the Bake API FastAPI backend from the provided source files: 

First make sure you have a working Python 3.13 installation.

CD into the BakeAPI directory ( the one containing this README.md file)

Create a new virtual environment:
    
    `python3.13 -m venv venv`

Activate the virtual environment:

    `source venv/bin/activate`

Install dependencies from requirements.txt:

    `pip install -r requirements.txt``

Start the application server:

    `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

Go to:
    http://localhost:8000

