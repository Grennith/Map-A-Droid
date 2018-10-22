#/bin/bash
while true; do
    read -p "Have you run raspi-config and set your timezone? (Y/N)" yn
    case $yn in
        [Yy]* ) break;;
        [Nn]* ) exit 1;;
        * ) echo "Please answer yes or no.";;
    esac
done
echo "Alright, let's start. Grab a coffee, take a long nap, go to work. This will take its time!"
sudo apt-get -y update && sudo apt-get -y upgrade
sudo apt-get install -y python-pip git cython libjpeg-dev zlib1g-dev libopenblas-base libopenblas-dev python-dev gcc gfortran tesseract-ocr
cd /opt && sudo git clone -b detectraidswithoutjson --single-branch https://github.com/Grennith/Map-A-Droid.git && sudo chown -R $USER:$USER Map-A-Droid && cd Map-A-Droid/
sudo -H pip install numpy

# increase swap
sudo /bin/dd if=/dev/zero of=/var/swap.1 bs=1M count=1024
sudo /sbin/mkswap /var/swap.1
sudo chmod 600 /var/swap.1
sudo /sbin/swapon /var/swap.1
cd ~
# compile scipy
wget https://github.com/scipy/scipy/releases/download/v1.1.0/scipy-1.1.0.tar.gz
tar xvfz scipy-1.1.0.tar.gz
cd scipy-1.1.0
python2.7 setup.py build && sudo python2.7 setup.py install
# compile openCV
wget https://raw.githubusercontent.com/milq/milq/master/scripts/bash/install-opencv.sh
sed -i 's/^cmake.*/cmake \.\./' install-opencv.sh
bash install-opencv.sh
# install MAD requirements
cd /opt && sudo git clone https://github.com/ZeChrales/PogoAssets.git && sudo chown -R $USER:$USER PogoAssets
cd /opt/Map-A-Droid/
cp config.ini.example config.ini
sed -i 's/^pogoasset:.*/pogoasset: \/opt\/PogoAssets\//' config.ini
timezone=$(python2.7 check_timezone.py | grep TIMEZONE: | grep -oEi '[-+0123456789]+')
sed -i "s/^timezone:.*/timezone: ${timezone}/" config.ini
sed -i "s/#temp_path:.*/temp_path: \/mnt\/mad_temp_ramdisk\//" config.ini
sudo -H pip install -r /opt/Map-A-Droid/setup/raspbian/requirements.txt
# setup ramdisk and stuff
sudo mkdir /mnt/mad_temp_ramdisk
sudo echo "tmpfs /mnt/mad_temp_ramdisk tmpfs nodev,nosuid,size=50M 0 0" >> /etc/fstab
sudo mount -a
sudo swapoff /var/swap.1
sudo rm /var/swap.1

echo -n ""
echo -n "Done setting it all up. Please reboot."
echo -n "If you do not run MAD as root (and you probably should not...), you may need to fix permissions on /mnt/mad_temp_ramdisk"
