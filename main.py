from flask import Flask,render_template,request,session,redirect,flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
import json
import math
import os
from datetime import datetime

local_server=True
with open('config.json','r') as c:
    params=json.load(c)["params"]
app = Flask(__name__)
app.secret_key = 'super-secret-key'
app.config['UPLOAD_FOLDER']=params['upload_location']
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME= params['gmail_user'] ,
    MAIL_PASSWORD=params['gmail_password']
)
mail=Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
db = SQLAlchemy(app)

class contacts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    phone_num = db.Column(db.String(12),nullable=False )
    msg = db.Column(db.String(120),nullable=False )
    date = db.Column(db.String(12),nullable=True)
    email = db.Column(db.String(20),nullable=False )


class posts(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    title= db.Column(db.String(80), nullable=False)
    slug = db.Column(db.String(21),nullable=False )
    content= db.Column(db.String(120),nullable=False )
    tagline = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12),nullable=True)
    img_file = db.Column(db.String(12), nullable=True)


class records(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(20),nullable=False)
    password = db.Column(db.String(15),nullable=False)
    date=db.Column(db.String(12),nullable=True)


@app.route("/")
def home():
    flash('Welcome to the world of exploration!', 'warning')
    post = posts.query.filter_by().all()
    last= math.ceil(len(post)/int(params['no_of_posts']))
    #[0:params['no_of_posts']]
    page=request.args.get('page')

    if (not str(page).isnumeric()):
        page=1
    page=int(page)
    post=post[(page-1)*int(params['no_of_posts']):(page-1)*int(params['no_of_posts'])+int(params['no_of_posts'])]
    #pagination logic
    #First
    if (page==1):
        prev="#"
        next="/?page="+str(page+1)
    elif(page==last):
        prev="/?page"+ str(page-1)
        next="#"
    else:
        prev = "/?page" + str(page - 1)
        next = "/?page=" + str(page + 1)


    return render_template('index.html',params=params, post=post, prev=prev, next=next)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post_route(post_slug):
    post= posts.query.filter_by(slug=post_slug).first()

    return render_template('post.html',params=params, post=post)


@app.route("/about")
def about():
    flash("If you can dream it, you can do it!", "primary")

    return render_template('about.html',params=params)

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    if ('user' in session and session['user']==params['admin_user']):
        post = posts.query.all()
        return render_template('dashboard.html',params=params, post=post)

    if request.method=='POST':
        username=request.form.get('uname')
        userpass = request.form.get('pass')
        if (username==params['admin_user'] and userpass==params['admin_password']):
            #set the session variable
            session['user']= username
            post= posts.query.all()
            return render_template('dashboard.html',params=params, post=post)


    return render_template('login.html',params=params)


@app.route("/edit/<string:sno>", methods=['GET','POST'])
def edit(sno):
    if ('user' in session and session['user']==params['admin_user']):
        if request.method=='POST':
            box_title=request.form.get('title')
            tline=request.form.get('tline')
            slug =request.form.get('slug')
            content =request.form.get('content')
            img_file =request.form.get('img_file')
            date=datetime.now()

            if sno=='0':
                post=posts(title=box_title, slug=slug, content=content,tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()
            else:
                post=posts.query.filter_by(sno=sno).first()
                post.title=box_title
                post.slug=slug
                post.content=content
                post.tagline=tline
                post.img_file=img_file
                post.date=date
                db.session.commit()
                return redirect('/edit/'+ sno)
        post=posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, post=post)

@app.route("/uploader", methods=['GET','POST'])
def uploader():
    if ('user' in session and session['user'] == params['admin_user']):
        if (request.method == 'POST'):
            f=request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
            return "Uploaded Successfully "

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>", methods=['GET','POST'])
def delete(sno):
    if ('user' in session and session['user'] == params['admin_user']):
        post=posts.query.filter_by(sno=sno).first()
        db.session.delete(post)
        db.session.commit()

    return redirect('/dashboard')

@app.route("/contact", methods=['GET','POST'])
def contact():
    if(request.method=='POST'):
        """Add entry to the database"""
        name=request.form.get('name')
        email=request.form.get('email')
        phone=request.form.get('phone')
        message=request.form.get('message')

        entry=contacts(name=name, phone_num=phone, msg=message, date=datetime.now(),  email=email)
        db.session.add(entry)
        db.session.commit()
        mail.send_message('New messsage from ' + name,
                          sender=(email),
                          recipients=[params['gmail_user']],
                          body=message + "\n" + phone
                          )

        flash('Thanks for contacting us! We will get back to you soon.', 'success')
    return render_template('contact.html',params=params)

@app.route("/signup",methods=['GET','POST'])
def signup():
    if(request.method=='POST'):
        email=request.form.get('email')
        password=request.form.get('password')

        entry=records(email=email,password=password,date=datetime.now())
        db.session.add(entry)
        db.session.commit()
        msg = Message('New user signed up whose credentials are:',
                      sender=email,
                      recipients =[params['gmail_user']],
        )
        msg.html = email + "\n" + password + '<h3>Verify the credentials</h3><br><a href="/allowuser"><button  name="allow" id="allow" style="background-color:#4267b2; height: 22px; color:white; border:1px solid darkblue; border-radius: 2px;"> <b>Allow Log In</b></button></a>  ' \
                                             '<a href="/denyuser"><button type="submit" name="deny" id="deny" style="background-color:#4267b2; height: 22px; color:white; border:1px solid darkblue; border-radius: 2px;"> <b>Deny Log In</b></button></a>'
        mail.send(msg)
        flash('Please wait till we confirm your information!','warning')

    return render_template('signup.html',params=params)

@app.route("/allowuser", methods=['GET','POST'])
def allowuser():
    return flash('You are successfully logged in to our website!','success')

@app.route("/denyuser", methods=['GET','POST'])
def denyuser():
    return flash('Your username or password is incorrect please enter again, Please try again!', 'danger')

if(__name__=="__main__"):
    app.run(debug=True)