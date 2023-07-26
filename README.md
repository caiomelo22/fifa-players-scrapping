# Intro
Project developed to scrap fifa players from a futbin and save them into your MySQL server.

## Setup
To run the project, just create a `.env` file with the following variables. They represent the credentials to insert data in your MySQL server, and a directory path to save the assets (players, teams, nations, leagues) images.

```
DB_HOST=localhost
DB_DATABASE=fifa-db
DB_USER=root
DB_PASSWORD=pwd
IMAGE_DIR_PATH=C:\default_path
```

After that, install the requirements and run the project.

```
>> pip install -r requirements.txt
>> python ./src/main.py
```
