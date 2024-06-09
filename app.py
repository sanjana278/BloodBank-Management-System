from flask import Flask, render_template, request, redirect, url_for, g
import sqlite3
import os

app = Flask(__name__)

DATABASE = 'bloodbank.db'

def get_db_connection():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'db'):
        g.db.close()

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute('PRAGMA foreign_keys = ON;')  # Enable foreign key support
        with app.open_resource('schema.sql', mode='r') as f:
            conn.cursor().executescript(f.read())
        conn.commit()

@app.route('/')
def index():
    with get_db_connection() as db:
        donors = db.execute('SELECT * FROM donors').fetchall()
    return render_template('index.html', donors=donors)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        blood_type = request.form['blood_type']
        email = request.form['email']

        with get_db_connection() as db:
            db.execute('INSERT INTO donors (name, blood_type, email) VALUES (?, ?, ?)',
                       (name, blood_type, email))
            db.commit()

        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/donations', methods=['GET', 'POST'])
def donations():
    with get_db_connection() as db:
        if request.method == 'POST':
            donor_id = request.form['donor_id']
            date = request.form['date']
            volume = request.form['volume']
            db.execute('INSERT INTO donations (donor_id, date, volume) VALUES (?, ?, ?)',
                       (donor_id, date, volume))
            db.commit()

        # Fetch donations data along with donor names
        donations_query = '''SELECT donations.date, donations.volume, donors.name 
                             FROM donations 
                             INNER JOIN donors ON donations.donor_id = donors.id'''
        donations = db.execute(donations_query).fetchall()

        # Fetch donors for the dropdown list
        donors = db.execute('SELECT * FROM donors').fetchall()

    return render_template('donations.html', donations=donations, donors=donors)


@app.route('/request_blood', methods=['GET', 'POST'])
def request_blood():
    if request.method == 'POST':
        patient_name = request.form['patient_name']
        required_blood_type = request.form['required_blood_type']
        volume = request.form['volume']

        with get_db_connection() as db:
            db.execute('INSERT INTO blood_requests (patient_name, required_blood_type, volume) VALUES (?, ?, ?)',
                       (patient_name, required_blood_type, volume))
            db.commit()

        return redirect(url_for('index'))
    else:
        with get_db_connection() as db:
            blood_requests = db.execute('SELECT * FROM blood_requests').fetchall()

        return render_template('request_blood.html', blood_requests=blood_requests)

@app.route('/inventory')
def inventory():
    with get_db_connection() as db:
        inventory = db.execute('SELECT * FROM donors').fetchall()

    return render_template('inventory.html', inventory=inventory)

if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        init_db()
    app.run(debug=True)
