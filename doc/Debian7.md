# Debin 7 (wheezy) notes

To install moebius for Debian 7, please use following steps:

1. Add ```deb http://http.debian.net/debian wheezy-backports main``` to /etc/apt/sources.list
2. Do ```apt-get update && apt-get install git python-tornado libzmq3 python-dev python-pip build-essential```
3. Install pyzmq using pip: ```pip install pyzmq```
4. Clone Moebius sources to Your dev directory: ```git clone https://github.com/bwsw/moebius.git```
