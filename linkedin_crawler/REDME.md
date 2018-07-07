Step 1: Install Python 2.7 version

Step 2: Verify Python 2.7 version

|python --version|

command result will be

|Python 2.7.6|


Step 3: Install Web Driver

You can pick any one of them

1 - Chrome Driver

curl -O http://chromedriver.storage.googleapis.com/2.30/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
rm chromedriver_linux64.zip
chmod +x chromedriver
cp chromedriver /usr/local/bin/

2 - Mozilla Driver

wget https://github.com/mozilla/geckodriver/releases/download/v0.11.1/geckodriver-v0.11.1-linux64.tar.gz
tar -xvzf geckodriver-v0.11.1-linux64.tar.gz
rm geckodriver-v0.11.1-linux64.tar.gz
chmod +x geckodriver
cp geckodriver /usr/local/bin/


Step 4: Install Selenium Library

Since Selenium2Library has some dependencies for selenium library, you need to install selenium library. The easy way of installing selenium library is to use pip. You can use the following command to install selenium.
pip install -U selenium