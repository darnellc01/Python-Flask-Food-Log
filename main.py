from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import sqlite3
import datetime
import threading
import requests

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///myDB.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

dbs = db.session


def reset():
    conn = sqlite3.connect('myDB.db')
    cursor = conn.cursor()
    while True:
        date = datetime.datetime.now()
        minute = int(date.minute)
        hour = int(date.hour)
        second = int(date.second)
        if second >= 45 and minute == 59 and hour == 23:
            total_cal = 0
            for row in cursor.execute("""SELECT calories FROM Food;""").fetchall():
                row = int(row[0])
                total_cal += row
            row1 = Week(day=str(datetime.datetime.today().strftime("%A")), calories=total_cal)
            dbs.add(row1)
            dbs.commit()
            cursor.execute("""DELETE FROM Food;""")
            conn.commit()


x = threading.Thread(target=reset)
x.start()


class Week(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(30), index=True)
    calories = db.Column(db.Integer)


class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), index=True)
    calories = db.Column(db.Integer)
    protein = db.Column(db.Integer)
    fat = db.Column(db.Integer)
    carbs = db.Column(db.Integer)

    def __repr__(self):
        return f'{self.name} has {self.calories}'


@app.route('/', methods=['GET', 'POST'])
def index():
    if len(request.form) > 0:
        new_row = Food(name=request.form['food'], calories=request.form['calories'], protein=request.form['protein'],
                       fat=request.form['fat'], carbs=request.form['carbs'])
        dbs.add(new_row)
        dbs.commit()
        return render_template('index.html', complete=True)
    else:
        return render_template('index.html')


@app.route('/log')
def log():
    conn = sqlite3.connect('myDB.db')
    cursor = conn.cursor()
    entries = cursor.execute("""SELECT * FROM Food;""").fetchall()
    amount = len(entries)
    total = 0
    for row in entries:
        total += int(row[2])
    return render_template('log.html', entries=entries, amount=amount, total=total)


@app.route('/week')
def week():
    conn2 = sqlite3.connect('myDB.db')
    cursor2 = conn2.cursor()
    days = cursor2.execute("""SELECT * FROM Week;""").fetchall()
    days_total = len(days)
    return render_template('week.html', days=days, days_total=days_total)


@app.route('/auto', methods=['GET', 'POST'])
def auto():
    return render_template('auto.html')


@app.route('/find', methods=['GET', 'POST'])
def find():
    food = str(request.form['food'])
    food = food.replace(' ', '%20')
    url = "https://nutritionix-api.p.rapidapi.com/v1_1/search/" + food

    querystring = {"fields": "item_name,item_id,brand_name,nf_calories,nf_total_fat"}

    headers = {
        'x-rapidapi-key': "7d57724b76msh8db90110128ae6ap1c6ab7jsnba2455cee51a",
        'x-rapidapi-host': "nutritionix-api.p.rapidapi.com"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    choices = response.json()['hits']
    return render_template('find.html', choices=choices)


@app.route('/add', methods=['GET', 'POST'])
def add():
    item_id = str(request.form['item_type'])
    item_list = item_id.split('-')
    iname = item_list[0].strip()
    bname = item_list[1].strip()
    url = "https://nutritionix-api.p.rapidapi.com/v1_1/search/" + iname

    querystring = {"fields": "item_name,item_id,brand_name,nf_calories,nf_total_fat,nf_protein,nf_total_carbohydrate"}

    headers = {
        'x-rapidapi-key': "7d57724b76msh8db90110128ae6ap1c6ab7jsnba2455cee51a",
        'x-rapidapi-host': "nutritionix-api.p.rapidapi.com",
        'brand_name': bname
    }

    response = requests.request("GET", url, headers=headers, params=querystring)
    resp = response.json()['hits'][0]['fields']
    cals = int(resp['nf_calories'])
    fat = int(resp['nf_total_fat'])
    protein = int(resp['nf_protein'])
    carbs = int(resp['nf_total_carbohydrate'])
    new_row = Food(name=item_id, calories=cals, protein=protein, fat=fat, carbs=carbs)
    dbs.add(new_row)
    dbs.commit()
    return f"<h1>Food Log Updated</h1>"

