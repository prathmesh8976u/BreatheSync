from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from textblob import TextBlob
import os
import re
import csv

# Setup Flask
app = Flask(__name__, instance_relative_config=True)
app.secret_key = 'your_secret_key'

# Make sure instance folder exists
os.makedirs(app.instance_path, exist_ok=True)

# Use SQLite DB inside instance folder
db_path = os.path.join(app.instance_path, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------ MODELS ------------------ #
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), default="Anonymous")
    email = db.Column(db.String(20))
    rating = db.Column(db.Integer)
    service_quality = db.Column(db.String(20))
    website_usability = db.Column(db.String(20))
    content_satisfaction = db.Column(db.String(20))
    recommendation = db.Column(db.String(20))
    suggestions = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ------------------ ROUTES ------------------ #
@app.route('/')
def home():
    return render_template('BreatheSync.html', user=session.get('user'), email=session.get('email'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user'] = user.username
            session['email'] = user.email
            flash('welcome_back', 'special')  # ✅ Correct flash for login
            return redirect(url_for('home'))
        else:
            flash("Invalid email or password", "error")
    return render_template('Login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        agree = request.form.get('terms')

        if not username or not email or not password:
            flash("All fields are required", "error")
        elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Enter a valid email address", "error")
        elif agree != "on":
            flash("You must agree to the terms and conditions", "error")
        elif User.query.filter_by(email=email).first():
            flash("Email already registered", "error")
        else:
            hashed_pw = generate_password_hash(password)
            new_user = User(username=username, email=email, password=hashed_pw)
            db.session.add(new_user)
            db.session.commit()

            # Save user info in CSV
            csv_file = os.path.join(app.instance_path, 'users.csv')
            file_exists = os.path.isfile(csv_file)
            with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Username', 'Email', 'Timestamp']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerow({'Username': username, 'Email': email, 'Timestamp': datetime.utcnow()})

            session['user'] = new_user.username
            session['email'] = new_user.email
            flash('signup_success', 'special')  # ✅ Correct flash for signup
            return redirect(url_for('home'))
    return render_template('Signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(email=session['email']).first()

    if request.method == 'POST':
        new_username = request.form.get('username')
        new_email = request.form.get('email')
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        action = request.form.get('action')

        if action == 'delete':
            db.session.delete(user)
            db.session.commit()
            session.clear()
            flash("Account deleted successfully!", "success")
            return redirect(url_for('home'))

        if not re.match(r"[^@]+@[^@]+\.[^@]+", new_email):
            flash("Enter a valid email address", "error")
            return redirect(url_for('edit_profile'))

        user.username = new_username
        user.email = new_email

        if new_password:
            if not old_password:
                flash("Please enter your old password to change password.", "error")
                return redirect(url_for('edit_profile'))
            if not check_password_hash(user.password, old_password):
                flash("Old password is incorrect.", "error")
                return redirect(url_for('edit_profile'))
            user.password = generate_password_hash(new_password)
            flash("Password updated successfully!", "success")

        db.session.commit()
        session['user'] = user.username
        session['email'] = user.email
        flash("Profile updated successfully!", "success")
        return redirect(url_for('home'))

    return render_template('EditProfile.html', user=user)

# ------------------ PROTECTED ROUTES ------------------ #
def login_required(view):
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return view(*args, **kwargs)
    wrapper.__name__ = view.__name__
    return wrapper

@app.route('/Relaxation')
@login_required
def relaxation():
    return render_template('Relaxation.html', user=session.get('user'))

@app.route('/Meditation')
@login_required
def meditation():
    return render_template('Meditation.html', user=session.get('user'))

@app.route('/Yoga')
@login_required
def yoga():
    return render_template('Yoga.html', user=session.get('user'))

@app.route('/Spiritual')
@login_required
def spiritual():
    return render_template('Spiritual.html', user=session.get('user'))

@app.route('/Motivation')
@login_required
def motivation():
    return render_template('Motivational Speaker.html', user=session.get('user'))

@app.route('/Blog')
@login_required
def blog():
    return render_template('Blog.html', user=session.get('user'))

@app.route('/feedback', methods=['GET'])
def feedback():
    page = request.args.get('page', 1, type=int)
    per_page = 5
    total_feedback = Feedback.query.order_by(Feedback.timestamp.desc()).paginate(page=page, per_page=per_page)
    return render_template("Feedback.html", feedback=total_feedback.items, page=page, total_pages=total_feedback.pages)

@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    feedback = Feedback(
        name=request.form.get('name') or "Anonymous",
        email=request.form.get('email'),
        rating=int(request.form.get('rating')),
        service_quality=request.form.get('service_quality'),
        website_usability=request.form.get('website_usability'),
        content_satisfaction=request.form.get('content_satisfaction'),
        recommendation=request.form.get('recommendation'),
        suggestions=request.form.get('suggestions')
    )
    db.session.add(feedback)
    db.session.commit()

    # Save feedback in CSV
    csv_file = os.path.join(app.instance_path, 'feedback.csv')
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Name', 'Email', 'Rating', 'Service Quality', 'Website Usability', 'Content Satisfaction', 'Recommendation', 'Suggestions', 'Timestamp']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'Name': feedback.name,
            'Email': feedback.email,
            'Rating': feedback.rating,
            'Service Quality': feedback.service_quality,
            'Website Usability': feedback.website_usability,
            'Content Satisfaction': feedback.content_satisfaction,
            'Recommendation': feedback.recommendation,
            'Suggestions': feedback.suggestions,
            'Timestamp': feedback.timestamp
        })

    flash("Thank you for your valuable feedback!", "success")
    return redirect(url_for('feedback', page=1))

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json()
    user_input = data.get('message', '').strip()
    lowered = user_input.lower()
    blob = TextBlob(user_input)
    sentiment = blob.sentiment.polarity

    # Core feelings/emotion detection
    stress_keywords = ['stress', 'stressed', 'pressure', 'overwhelmed', 'tired', 'tense']
    anxiety_keywords = ['anxious', 'anxiety', 'panic', 'nervous']
    sadness_keywords = ['depressed', 'sad', 'empty', 'hopeless', 'lonely', 'down']
    motivation_keywords = ['no energy', 'unmotivated', 'lost hope', 'can’t do this']

    if "talk more" in lowered or "say more" in lowered:
        reply = (
            "Of course! Let's keep talking 🌟\n\n"
            "You're doing better than you think.\n"
            "If you'd like, I can share a short breathing tip or suggest something uplifting from our website 💚\n"
            "Would you prefer a motivational video or a calming breathing session?"
        )
    elif any(word in lowered for word in stress_keywords):
        reply = (
            "I'm here for you 💙 It sounds like you're feeling stressed.\n\n"
            "✅ Try this short breathing exercise:\n"
            "🔹 Inhale deeply for 4 seconds\n"
            "🔹 Hold for 4 seconds\n"
            "🔹 Exhale slowly for 6 seconds\n\n"
            "Repeat 5 times. You'll feel a bit lighter.\n\n"
            "🎧 You can also watch our calming videos in the [Relaxation section](/Relaxation) or [Meditation section](/Meditation)."
        )
    elif any(word in lowered for word in anxiety_keywords):
        reply = (
            "Anxiety can be tough. Let's work through it together 🫶\n\n"
            "Try this grounding technique:\n"
            "🌿 Name 3 things you can see\n"
            "👂 2 things you can hear\n"
            "💨 1 deep breath right now\n\n"
            "🧘 Visit our [Meditation](/Meditation) or [Yoga](/Yoga) section to find peace."
        )
    elif any(word in lowered for word in sadness_keywords):
        reply = (
            "You are not alone. 💛 It’s okay to feel this way.\n\n"
            "Would you like to talk more or try a breathing technique?\n"
            "You might also enjoy watching something uplifting in our [Motivational Speakers](/Motivation) section."
        )
    elif any(word in lowered for word in motivation_keywords):
        reply = (
            "Feeling low is normal. 🌥️\n\n"
            "Maybe take a moment for yourself.\n"
            "💪 Watch motivational talks in the [Motivational Speakers](/Motivation) section to recharge.\n"
            "Or gently move with some [Yoga](/Yoga) to reconnect with your energy."
        )
    elif "help" in lowered:
        reply = (
            "I'm always here to help 🤝\n\n"
            "Are you:\n"
            "1️⃣ Feeling stressed or anxious?\n"
            "2️⃣ Low on energy or motivation?\n"
            "3️⃣ Looking to relax or meditate?\n\n"
            "Let me know, and I’ll suggest the right section from our website 💡"
        )
    elif any(word in lowered for word in ['yoga', 'meditation', 'relax', 'motivation']):
        if 'yoga' in lowered:
            reply = "🧘 Explore the [Yoga section](/Yoga) to practice calming routines and gentle poses."
        elif 'meditation' in lowered:
            reply = "🧠 Clear your mind with guided sessions in the [Meditation section](/Meditation)."
        elif 'relax' in lowered:
            reply = "🎵 Enjoy peaceful music and guided breathing in the [Relaxation section](/Relaxation)."
        elif 'motivation' in lowered:
            reply = "💬 Get inspired by Gaur Gopal Das, Sadhguru, and others in [Motivational Speakers](/Motivation)."
    elif sentiment < -0.3:
        reply = (
            "I'm really sorry you're feeling this way 💔\n\n"
            "Please take a deep breath... you're doing your best.\n"
            "Maybe visit our [Relaxation](/Relaxation) or [Motivational](/Motivation) sections for support.\n"
            "You're not alone 🌱"
        )
    elif sentiment > 0.5:
        reply = "You sound great! 😊 Keep that positivity alive. Would you like to explore a new yoga or meditation session?"
    else:
        reply = (
            "Hi there! 👋 I'm BreatheBot.\n\n"
            "How can I support you today?\n"
            "👉 You can say things like:\n"
            "- I'm stressed\n"
            "- I want to relax\n"
            "- I feel anxious\n"
            "- I need motivation\n\n"
            "I'll guide you to the right section 💚"
        )

    return jsonify({"response": reply})


# ------------------ MAIN ------------------ #
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
