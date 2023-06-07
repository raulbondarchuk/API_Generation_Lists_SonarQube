import requests
#import base64
import json
import os 

# Config con passwd y login 
url = 'url_sonarqube' # url of your dev.sonarqube
username = 'your_username'
password = 'your_passwd'
session = requests.Session()

# Iniciar sesion en SonarQube con el nombre de usuario y la contrasena
session.auth = (username, password)

auth = username+":"+password
#auth = str(base64.b64encode(auth.encode("utf-8")))[2:-1]
headers = {'authorization': "Basic "+auth}
