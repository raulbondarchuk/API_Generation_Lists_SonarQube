# API_Generation_Lists_SonarQube
API Generation Lists (Python + SonarQube API).
La idea de este API es obtener la información de los proyectos sin acceso a BDD, usando SonarQube API.

## Master.py - Toda la funcionalidad principal está aquí.

### imports - bibliotecas

``` python
import requests
import base64
import json
import pandas as pd
import openpyxl
from openpyxl import load_workbook
import os
import time # test tiempo de ejecución 
```
Siguiente import sirve para obtener la conexión con SonarQube API (Hay dos tipos de conexión, el código esta escrito en archivos connection.py y connectionToken.py).
``` python
from connectionToken import url, session, headers
```

### Funciones para comprobar el tiempo de ejecución.
``` python
def start_timer():
    start_time = time.time()  # start_time
    return start_time

def stop_timer(start_time):
    end_time = time.time()  # end_time
    elapsed_time = end_time - start_time  # Tiempo de ejecución
    return elapsed_time
```

### Esta función sirve para obtener todos los proyectos existentes en nuestra SonarQube API.

``` python
def get_all_projects():
    page = 1
    projects = []

    while True:
        response = session.get(f"{url}/api/projects/search?", params={"ps": 100, "p": page}, verify=False, timeout=10)
        print(response)
        data = json.loads(response.content.decode('utf-8'))
        projects += data['components']
        if len(data['components']) < 100:
            break
        page += 1
    return projects

projects = get_all_projects() # List of all projects 
```
### Aquí podemos configurar el formato del archivo Excel & poder crear un archivo Excel, hacemos esto para dar una vista adecuada al contenido del archivo.

``` python
# Format Excel file
def auto_size_cells(file_name):
    wb = load_workbook(file_name) 
    for sheet_name in wb.sheetnames:
        sheet = wb[sheet_name]
        for col in sheet.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = max_length
            sheet.column_dimensions[column].width = adjusted_width

    wb.save(file_name)

# Write DataFrame to Excel file
def writer_save_excel(df, file_name):
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Obtenemos directorio de script
    file_path = os.path.join(current_dir, file_name)  # formamos la ruta completa
    writer = pd.ExcelWriter(file_path)
    df.to_excel(writer, index=False)
    writer._save()
    return writer
```
### Función para obtener los tags y versión del proyecto concreto depende de su key.
``` python
# Get tags and version from project (True - la respuesta con version, false - la respuesta sin version)
def get_project_tag_and_version(kee, boolVersion):
    if boolVersion:
        project_response = session.get(f"{url}/api/components/show", params={"component": kee}, headers=headers, verify=False, timeout=10)
        project_data = json.loads(project_response.content.decode('utf-8'))
        tags = project_data.get('component', {}).get('tags', [])
        version = project_data.get('component', {}).get('version', '')
        return tags, version
    else:
        project_response = session.get(f"{url}/api/components/show", params={"component": kee}, headers=headers, verify=False, timeout=10)
        project_data = json.loads(project_response.content.decode('utf-8'))
        tags = project_data.get('component', {}).get('tags', [])
        return tags
```

### Esta función simplemente devuelva un variable (un tag) sin "-aplic".
``` python
# Get app_from_tags from project
def get_app_from_tags(tags):
    for tag in tags:
        if tag.startswith('aplic-'):
            app_name = tag[6:].upper().replace('-', '_')
            return f"{app_name}"
    return ''
```
### Función para crear una lista con todos los proyectos sin analisis.

``` python
def get_unanalyzed_projects():

    response = session.get(f"{url}/api/projects/search?",params={"onProvisionedOnly": "true","s": "analysisDate","asc": "true"},headers=headers,verify=False,timeout=10)
    projects = json.loads(response.content.decode('utf-8'))['components'] # Una lista de todos los proyectos que tienen ProvisionedOnly
    
    results = []
    for project in projects:
        name = project.get('name', '')
        kee = project.get('key', '')
        tags = get_project_tag_and_version(kee, False) # Get tags from project (sin version)
        app_from_tags = get_app_from_tags(tags) # Get app_from_tags from project
        results.append({'AppFromTags': app_from_tags, 'Name': name, 'kee': kee, 'tags': ', '.join(tags), })

    df = pd.DataFrame(results, columns=['AppFromTags', 'Name', 'kee', 'tags', ])
    df = df.sort_values(['AppFromTags', 'Name', 'kee'], ascending=True, na_position='last')
    
    file_name = 'unanalyzed_projects.xlsx' # File Name
    writer_save_excel(df,file_name) 
    auto_size_cells(file_name)
```
### Función para crear una lista de proyectos, cuales no contienen "aplic-" dentro de tags
``` python
def get_projects_without_tag_aplic(projects):
    results = []
    for project in projects:
        name = project.get('name', '')
        kee = project.get('key', '')
        tags, version = get_project_tag_and_version(kee, True)
        last_analisys = project.get('lastAnalysisDate')

        if any(tag.lower().strip().startswith('aplic-') for tag in tags):
            continue 
 
        results.append({'Name': name, 'kee': kee, 'tags': ', '.join(tags),  'last_analisys': last_analisys, 'version': version})

    df = pd.DataFrame(results, columns=['Name', 'kee', 'tags', 'last_analisys', 'version'])
    df = df.sort_values(['Name', 'kee'], ascending=True)

    file_name = 'projects_without_tag_-aplic.xlsx' 
    writer_save_excel(df,file_name) 
    auto_size_cells(file_name)
```
### Función para crear una lista de proyectos con los nombres duplicados
``` python
def get_projects_with_duplicate_name(projects):
    project_names = {}
    for project in projects:
        name = project.get('name', '')  
        if name in project_names:
            project_names[name] += 1
        else:
            project_names[name] = 1

    duplicate_projects = []
    for project in projects:
        name = project.get('name', '')
        kee = project.get('key', '')
        tags, version = get_project_tag_and_version(kee, True)
        app_from_tags = get_app_from_tags(tags)
        last_analisys = project.get('lastAnalysisDate')

        if project_names[name] > 1:
            duplicate_projects.append({'AppFromTags': app_from_tags, 'Name': name, 'kee': kee, 'tags': ', '.join(tags), 'last_analisys': last_analisys, 'version': version})

    df = pd.DataFrame(duplicate_projects, columns=['AppFromTags', 'Name', 'kee', 'tags', 'last_analisys', 'version'])
    df = df.sort_values(['AppFromTags', 'Name', 'kee'], ascending=True)

    file_name = 'projects_with_duplicate_names.xlsx'
    writer_save_excel(df,file_name)
    auto_size_cells(file_name)
```

# El código para la ejecución y comprobación del tiempo de ejecución

``` python
# Execute
timer_start = start_timer()
get_unanalyzed_projects()
elapsed_time1 = stop_timer(timer_start) # tiempo de ejecución

timer_start = start_timer()
get_projects_without_tag_aplic(projects)
elapsed_time2 = stop_timer(timer_start) # tiempo de ejecución

timer_start = start_timer()
get_projects_with_duplicate_name(projects)
elapsed_time3 = stop_timer(timer_start) # tiempo de ejecución

print("get_unanalyzed_projects ",elapsed_time1)
print("get_projects_without_tag_aplic", elapsed_time2)
print("get_projects_with_duplicate_name", elapsed_time3)
```


# Establecer la conexión usando LOGIN y PASSWORD

``` python
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
```
# Establecer la conexión usando TOKEN (Más seguro)

``` python
import requests
import base64
import json
import os 

# Config con passwd y login 
url = 'url_sonarqube' # url of your dev.sonarqube
username = 'your_token'
password = '' 
session = requests.Session()

# Iniciar sesion en SonarQube con el nombre de usuario y la contrasena (en este caso con usuario porque es token)
session.auth = (username, password)

auth = username+":"+password
auth = str(base64.b64encode(auth.encode("utf-8")))[2:-1]
headers = {'authorization': "Bearer "+auth}
# Error 403 - Error de autorización
```

# Ejecutar nuestros scripts
``` python
# projects with duplicate name
from master import get_projects_without_tag_aplic, projects
get_projects_without_tag_aplic(projects)

# projects without tag aplic
from master import get_projects_with_duplicate_name, projects
get_projects_with_duplicate_name(projects)

# ununulized projects
from master import get_unanalyzed_projects
get_unanalyzed_projects()
```

