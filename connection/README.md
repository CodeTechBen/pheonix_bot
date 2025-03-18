# Postgres DB
connect to the DB using the bash connect_db.sh
sudo apt update
sudo apt upgrade
install postgres with `sudo apt install postgresql postgresql-contrib`
sudo -u postgres psql
CREATE USER yourusername WITH PASSWORD 'yourpassword';
CREATE DATABASE yourdatabase;
GRANT ALL PRIVILEGES ON DATABASE yourdatabase TO yourusername;
Then git clone this repository using `git clone https://github.com/CodeTechBen/pheonix_bot.git`
Use the bash script in `connection` run `bash convert-db-to-global.sh`.
or 
sudo nano /etc/postgresql/<version>/main/postgresql.conf
replace # listen_addresses = 'localhost' to listen_addresses = '*'

sudo nano /etc/postgresql/<version>/main/pg_hba.conf
add `host    all             all             0.0.0.0/0            md5` to the end.
sudo service postgresql restart

# bot
Connect to the bot using the bash connect_bot.sh
git clone this repository using `git clone https://github.com/CodeTechBen/pheonix_bot.git`
cd pheonix_bot
sudo apt-get update && sudo apt-get install -y python3-venv
python3 -m venv .venv
source .venv/bin/activate
cd bot
pip install -r requirements
cd ..
bash /connection/start_bot.sh
