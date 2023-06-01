# Discord Bots

This folder contains scripts for running our discord bot(s).


## TL;DR

    cd discord_bots
    conda activate discord
    python db/setup_db.py
    python discord_registration_bot.py


## Getting started
Run all scripts from the `discord_bots` folder:

    cd discord_bots


### Create a conda env

    conda create -n discord python=3.10
    conda activate discord
    pip install -r requirements.txt


### Create the DB
To initialize the sqlite database, run the `db/setup_db.py` script:

    python db/setup_db.py

This script will create the `registration` table in the `db/registration_bot.db` database.

### Reset the DB
If you want to reset the sqlite database, run the `reset_db.py` script:

    python db/reset_db.py

This script will drop the `registration` table in the `db/registration_bot.db` database. You need to run the `db/setup_db.py` script afterwards.

### Reading the DB
If you want to print the content of the `registration` table to the console, you can run the `db/read_db.py` script:

    python db/read_db.py

This script also has a csv option, that will save the content of the `registration` table as csv file to `db/registration.csv`. In order to save a csv file, run the script with the csv option:

    python db/read_db.py csv

## Discord registration bot
This bot assigns the 'Attendee' role to all discord users that enter their ticket ID and name.

### Update config
Update the bot_token value in the `discord_registration_bot_config.yaml` config file with the token provided by the discord developers portal at `https://discord.com/developers/applications/1088106290997379104/information`.


### Run the bot
For starting the discord registration bot, run the following script:

    python discord_registration_bot.py

As long as the script runs, the discord bot will assign the 'Attendee' role to the discord users that verify themselves using their ticket ID (booking reference) and their name (that is printed on the badge, usually 'Firstname Lastname').

The verification is done using the API provided at `http://78.94.223.124:15748/docs`.


## Discord job bot
This bot posts links to job offers by the sponsors automatically in discord.

    python discord_jobs_bot.py


# Deployment on EC2
The deployment config can be found in `deploy_discord_bot.yml`.

Follow the instructions at:
https://github.com/easingthemes/ssh-deploy/tree/v4
* create new ssh pair in ec2 instance
* copy private key to gitlab variables


* add discord bot tokens to `.bashrc` file
```
vim .bashrc
```

* add the following lines:
```
export DISCORD_REGISTRATION_BOT_TOKEN="..."
export DISCORD_JOB_BOT_TOKEN="..."
```
* close the `.bashrc` file
* install miniconda
```
wget https://repo.anaconda.com/miniconda/Miniconda3-py37_23.1.0-1-Linux-x86_64.sh
bash Miniconda3-py37_23.1.0-1-Linux-x86_64.sh
```
* update `.bashrc` to make discord bot tokens and conda available
```
source .bashrc
```

* created conda env (discord with python 3.10 and installed the requirements.txt)
```
conda create -n discord python=3.10
conda activate discord
pip install -r requirements.txt
```
* run `db/setup_db.py` script to create DB
```
python db/setup.py
```

* the following steps are run automatically by the deployment
    * run the scripts with `nohup` in the background
```
nohup python discord_registration_bot.py > discord_registration_bot.log 2>&1 &
   nohup python discord_jobs_bot.py > discord_jobs_bot.log 2>&1 &
```

* useful commands to see the scripts
```
ps ax | grep python
pgrep python
```
