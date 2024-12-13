sudo sh -c 'echo "[Match]" > /etc/systemd/network/eth0.network'
sudo sh -c 'echo "Name=eth0" >> /etc/systemd/network/eth0.network'
sudo sh -c 'echo "[Network]" >> /etc/systemd/network/eth0.network'
sudo sh -c 'echo "Address=192.168.0.20/24" >> /etc/systemd/network/eth0.network'
sudo systemctl enable systemd-networkd
sudo systemctl start systemd-networkd
sudo systemctl restart systemd-networkd