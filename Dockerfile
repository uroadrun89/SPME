FROM vm/ubuntu:18.04
RUN pip3.11 install -r requirements.txt
RUN BACKGROUND python3.11 main.py
RUN BACKGROUND python3.11 -m http.server 80
EXPOSE WEBSITE http://localhost:80
