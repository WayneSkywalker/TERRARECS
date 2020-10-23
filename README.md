# TERRARECS
[![Python Version](https://img.shields.io/badge/python-3.7.6-brightgreen.svg)](https://python.org)
[![Django Version](https://img.shields.io/badge/django-3.1.1-brightgreen.svg)](https://djangoproject.com)

TERRARECS is the property post recommendation system.
This project is a part of CSS 495 INDUSTRIAL COORPERATIVE LEARNING, which cooperate between King Mongkut's University of Technology Thonburi and TERRA media and Consulting Co., Ltd. 

## Installation
1. Clone this repository to location that you want.
```bash
git clone https://github.com/WayneSkywalker/TERRARECS.git
```
2. Install python environment called 'pipenv'
```bash
pip install pipenv
```
3. Create python environment at your root project location.
```bash
pipenv shell
```
4. Install all libraries required
```bash
pip install -r requirements.txt
```
## Usage
### Local server 
#### First time usage
1. Open your python environment that was created at your root project location.
```bash
pipenv shell
```
2. move to QFSci folder
```bash
cd TERRARECS
```
3. then, check if manage.py exists.
```bash
dir
```
you will see...
```bash
05/22/2020  04:48 PM    <DIR>          .
05/22/2020  04:48 PM    <DIR>          ..
03/08/2020  10:00 AM               646 manage.py
03/08/2020  10:00 AM    <DIR>          TERRARECS
05/04/2020  07:57 PM    <DIR>          recommender
05/04/2020  07:57 PM    <DIR>          DEMO
               1 File(s)            646 bytes
               4 Dir(s)  911,458,639,872 bytes free
```
4. setup database using these commands
```bash
python manage.py makemigrations
python manage.py migrate
```
5. To run server, run this command...
```bash
python manage.py runserver
```
This will be run on http://localhost:8000.
#### Non-first time usage
1. Open your python environment that was created at your root project location.
```bash
pipenv shell
```
2. Run this command...
```bash
cd TERRARECS
```
3. To run server, run this command...
```bash
python manage.py runserver
```
This will be run on http://localhost:8000.
### Production
In settings.py (which is in TERRARECS/TERRARECS), please..
```python
DEBUG = False
``` 
and set the database before runserver.
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'terrarecs',
        'USER': 'root',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}
```
## Lisence
