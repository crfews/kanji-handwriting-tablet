# kanji-handwriting-tablet

# Setting Up Your Development Environment
## Setting Up the Virtual Environment
### Create and enter your virtual environment
Run the following in terminal:
  python -m venv .venv

Then run the following:
  source ./.venv/bin/activate

You should activate your venv every time you work on the code to ensure that your environment is the same as everybody else.

### Create 'requirements.txt' to Share Your Packages
_Only perform this if you have added a new package_

Run the following in terminal after activating your venv:
  pip freeze > requirements.txt

## Update Your Venv Using 'requirements.txt'

Once you have a venv setup, you can make it identical by entering your venv and running the following:
  pip install -r requirements.txt
