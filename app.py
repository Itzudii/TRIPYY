from flask import Flask, render_template, redirect, url_for, flash, request ,session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField ,BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_bcrypt import Bcrypt
from custom import *
import random
import datetime
import wikipediaapi
import urllib.parse
import requests
from coord import get_coordinates

today = datetime.date.today()
app = Flask(__name__,static_folder="static")
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dashboard.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

USER_AGENT = "MyWikipediaBot/1.0 (udityasage2004@gmail.com)"
wiki = wikipediaapi.Wikipedia("en", headers={"User-Agent": USER_AGENT})

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"  
bcrypt = Bcrypt(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False) 
    is_valid = db.Column(db.Boolean, default=False)

class RegistrationForm(FlaskForm):
    name = StringField('Name',validators=[DataRequired(), Length(min=2, max=100)],render_kw={"class":"form-control","placeholder": "Your Name *"})
    email = StringField('Email', validators=[DataRequired(), Email()],render_kw={"class":"form-control","placeholder": "Your email *"} )
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)],render_kw={"class":"form-control","placeholder": "Your password *"})
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')],render_kw={"class":"form-control","placeholder": "confirm password *"})
    submit = SubmitField('Register', render_kw={"class":"btnSubmit"})

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()], render_kw={"class":"form-control","placeholder": "Your Email *"})
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"class":"form-control","placeholder": "Your password *"})
    is_remember = BooleanField('checkbox',render_kw={"class":"form-check-input" ,"id":"inlineCheckbox1"})
    submit = SubmitField('Login', render_kw={"class":"btnSubmit"})
# ===========================================================================\/


def getCoord(name):
    api = f'https://geocode.search.hereapi.com/v1/geocode?q=${urllib.parse.quote(name)}&apiKey={coordkey()}'
    req = requests.get(api)
    data = req.json()
    return data['items'][0]['position']



def getForcastData(lat,lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={forcastkey()}"
    response = requests.get(url)
    return response.json()



def getPointOfIntrest(lat,lon):
    req = requests.get(f"https://api.geoapify.com/v2/places?categories=tourism.attraction&filter=circle:{lon},{lat},5000&limit=10&apiKey={poikey()}")
    data = req.json()
    collected_data = []
    for i in range(len(data['features'])):
        coord = data['features'][i]['geometry']['coordinates']
        collected_data.append({'name':data['features'][i]['properties']['name'],'lat': coord[1],'lng': coord[0]})
    return {'coord':[lat,lon],'data':collected_data}


def seprateDate(data):
    # dt = data['dt']
    main = data['main']
    weather = data['weather'][0]
    wind = data['wind']
    time = data['dt_txt']
    return {'time':time,'temp':main['temp'],'min':main['temp_min'],'max':main['temp_max'],'humidity':main['humidity'],'speed':wind['speed'],'main':weather['main'],'description':weather['description'],'icon':weather['icon']}
 
def prepareData(data):
    print(data)
    temp = None
    a=[]
    b=[]
    for i in data['list']:
        date = i['dt_txt'].split(' ')[0] 
        if temp != date:
            temp = date
            b.append(a)
            a=[]
        a.append(seprateDate(i))
    b.pop(0)
    return b
# use full functions ========================
def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')

# Load user from session
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login',methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password,form.password.data):
            login_user(user,remember=form.is_remember.data)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html',form = form)


@app.route('/signup',methods=['GET', 'POST'])
def signup():
    form = RegistrationForm()
    if request.method == 'POST' and form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_valid == False:
            db.session.delete(user)
            db.session.commit()
            user = None
        if not user:
            new_user = User(name=form.name.data, email=form.email.data, password=hash_password(form.password.data),is_valid=False)
            db.session.add(new_user)
            db.session.commit()
            session['email'] = form.email.data
            session['otp'] = random.randint(1000,9999)
            return redirect(url_for('otp'))
        else:
            flash('Email already exists. try another email.', 'danger')
    return render_template('signup.html',form = form)


@app.route('/otp',methods=['GET', 'POST'])
def otp():
    email = session.get('email')
    genrateOTP = session.get('otp') 
    smtpData.send_email(smtpData,recipient_email=str(email),otp=str(genrateOTP))
    if request.method == 'POST':
        userOTP = request.form.get('otp')
        if int(genrateOTP) == int(userOTP):
            user = User.query.filter_by(email=email).first()
            user.is_valid = True
            flash('Account created! You can now log in.', 'success')
            return redirect(url_for('login'))
        else:
            flash('OTP not matched. Please try again.', 'danger')
    return render_template('otp.html')


@app.route('/dashboard',methods=['GET','POST'])
@login_required
def dashboard():
    user = current_user.name
    info = "No information found."
    if request.method == 'POST':
        search = request.form.get('search')

        page = wiki.page(search)
        if page.exists():
            info = page.summary[:2000]
        
        
        coord = get_coordinates(search)
        if not coord:
            coord = getCoord(search)
        try:

            data = getForcastData(coord['lat'],coord['lng'])
            data = prepareData(data)
            _poi = getPointOfIntrest(coord['lat'],coord['lng'])
            session['poi'] = _poi
            days = []
            for i in range(5):
                next_day = today + datetime.timedelta(days=i)
                days.append(next_day.strftime('%A'))
            return render_template('dashboard.html',display = True, username = user,  weather = data,poi = _poi , tday = days,info = info) #
        except:
            flash('location not found','danger')
    return render_template('dashboard.html',display = False, username = user , info = info )

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/map')
@login_required 
def map():
    return render_template('mapMain.html',coords_list={})

@app.route('/mapData')
@login_required 
def mapData():
    return render_template('mapMain.html',coords_list = session['poi'])

@app.route('/guide')
def guide():
    return render_template('guide.html')


# models ===================================

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True, port=5000)
