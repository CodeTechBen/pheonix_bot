
sudo sed -i "s/^#\?listen_addresses.*/listen_addresses = '*'/" /etc/postgresql/9.5/main/postgresql.conf

echo "host    all             all             0.0.0.0/0            md5" | sudo tee -a /etc/postgresql/9.5/main/pg_hba.conf

sudo systemctl restart postgresql

echo "converted psql database to global"