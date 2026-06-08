# app.py
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'scriptura_sacred_secret_key_2026'

# SQLite 데이터베이스 설정
db_path = os.path.join(os.path.dirname(__file__), 'scriptura.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------------------------------------------------------
# KJV 성경 데이터 로드 (en_kjv.json)
# ------------------------------------------------------------------
import json
BIBLE_DATA = []
BIBLE_BOOKS_MAP = {}
bible_json_path = os.path.join(os.path.dirname(__file__), 'en_kjv.json')
try:
    with open(bible_json_path, 'r', encoding='utf-8') as f:
        BIBLE_DATA = json.load(f)
        for idx, book in enumerate(BIBLE_DATA):
            BIBLE_BOOKS_MAP[book['name'].lower()] = {
                'index': idx,
                'name': book['name'],
                'abbrev': book['abbrev'],
                'chapters': book['chapters']
            }
except Exception as e:
    print(f"Error loading en_kjv.json: {e}")

def get_proverbs_for_day(day):
    if 'proverbs' in BIBLE_BOOKS_MAP:
        prov_chapters = BIBLE_BOOKS_MAP['proverbs']['chapters']
        if 1 <= day <= len(prov_chapters):
            return [{"num": i + 1, "text": text} for i, text in enumerate(prov_chapters[day - 1])]
    return []

# ------------------------------------------------------------------
# 데이터베이스 모델 정의
# ------------------------------------------------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    records = db.relationship('DailyRecord', backref='user', lazy=True)

class DailyRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False) # YYYY-MM-DD 포맷
    
    # 성독 여부
    read_completed = db.Column(db.Boolean, default=False)
    
    # 말씀 암송 필사 및 적용
    verse_accuracy = db.Column(db.Integer, default=0)
    verse_application = db.Column(db.Text, default="")
    
    # 기도 제목 3선
    prayer_1 = db.Column(db.Text, default="")
    prayer_2 = db.Column(db.Text, default="")
    prayer_3 = db.Column(db.Text, default="")
    
    # 감사 일기 5선
    gratitude_1 = db.Column(db.Text, default="")
    gratitude_2 = db.Column(db.Text, default="")
    gratitude_3 = db.Column(db.Text, default="")
    gratitude_4 = db.Column(db.Text, default="")
    gratitude_5 = db.Column(db.Text, default="")

# ------------------------------------------------------------------
# 성경 데이터 로드 완료
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# 글로벌 컨텍스트 데이터 선언
# ------------------------------------------------------------------
CONTEXT_DATA = {
    "hero_verse": {
        "text": "Thy word is a lamp unto my feet, and a light unto my path.",
        "reference": "Psalm 119:105"
    },
    "mission_verse": {
        "text": "And he said unto them, Go ye into all the world, and preach the gospel to every creature.",
        "reference": "Mark 16:15"
    },
    "verse_of_the_day": {
        "text": "For the earth shall be filled with the knowledge of the glory of the Lord, as the waters cover the sea.",
        "reference": "Habakkuk 2:14"
    },
    "gratitude_verse": {
        "text": "O give thanks unto the LORD, for he is good: for his mercy endureth for ever.",
        "reference": "Psalm 107:1"
    }
}

def get_today_str():
    return datetime.now().strftime("%Y-%m-%d")

def get_daily_verse(date_str):
    return CONTEXT_DATA["verse_of_the_day"]

def get_or_create_record(user_id, date_str):
    record = DailyRecord.query.filter_by(user_id=user_id, date=date_str).first()
    if not record:
        record = DailyRecord(user_id=user_id, date=date_str)
        db.session.add(record)
        db.session.commit()
    return record

# ------------------------------------------------------------------
# 라우팅 제어부
# ------------------------------------------------------------------
@app.route('/')
def index():
    completed_dates = []
    if 'user_id' in session:
        records = DailyRecord.query.filter_by(user_id=session['user_id'], read_completed=True).all()
        completed_dates = [r.date for r in records]
    
    return render_template('index.html', completed_dates=completed_dates, today_day=datetime.now().day, **CONTEXT_DATA)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('This email is already registered.', 'error')
            return redirect(url_for('register'))
        
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('mypage'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    today_str = get_today_str()
    
    completed_records = DailyRecord.query.filter_by(user_id=user_id, read_completed=True).all()
    completed_dates = [r.date for r in completed_records]
    
    today_record = get_or_create_record(user_id, today_str)
    today_verse = get_daily_verse(today_str)
    
    return render_template('mypage.html',
                           completed_dates=completed_dates,
                           today_record=today_record,
                           today_verse=today_verse,
                           today_day=datetime.now().day)

@app.route('/read', methods=['GET', 'POST'])
def read():
    if 'user_id' not in session:
        flash('Please login to read scripture.', 'error')
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    today_str = get_today_str()
    record = get_or_create_record(user_id, today_str)
    
    if request.method == 'POST':
        record.read_completed = True
        db.session.commit()
        flash('Praise God! You have completed today\'s Scripture reading.', 'success')
        return redirect(url_for('mypage'))

    now = datetime.now()
    today_day = now.day
    today_label = f"{now.strftime('%B')} {today_day}"
    return render_template('read.html', record=record, verses=get_proverbs_for_day(today_day), chapter_num=today_day, today_label=today_label)

@app.route('/verse', methods=['GET', 'POST'])
def verse():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    today_str = get_today_str()
    record = get_or_create_record(user_id, today_str)
    today_verse = get_daily_verse(today_str)
    
    if request.method == 'POST':
        accuracy = request.form.get('accuracy', 0)
        application = request.form.get('application', '')
        
        record.verse_accuracy = int(accuracy)
        record.verse_application = application
        db.session.commit()
        flash('Your memorization and application have been recorded.', 'success')
        return redirect(url_for('mypage'))
        
    # [해결 1] verse.html 내부의 'verse_of_the_day' 변수 바인딩 누락 해결
    return render_template('verse.html', record=record, verse_of_the_day=today_verse)

@app.route('/prayer', methods=['GET', 'POST'])
def prayer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    today_str = get_today_str()
    record = get_or_create_record(user_id, today_str)
    
    if request.method == 'POST':
        record.prayer_1 = request.form.get('prayer_1')
        record.prayer_2 = request.form.get('prayer_2')
        record.prayer_3 = request.form.get('prayer_3')
        db.session.commit()
        flash('Prayer request submitted successfully.', 'success')
        return redirect(url_for('mypage'))
        
    # [해결 2] prayer.html 내부의 'prayers' 사전형 변수 바인딩 누락 해결
    prayers = {
        'p1': record.prayer_1 or '',
        'p2': record.prayer_2 or '',
        'p3': record.prayer_3 or ''
    }
    return render_template('prayer.html', record=record, prayers=prayers)

@app.route('/gratitude', methods=['GET', 'POST'])
def gratitude():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    today_str = get_today_str()
    record = get_or_create_record(user_id, today_str)
    
    if request.method == 'POST':
        record.gratitude_1 = request.form.get('gratitude_1')
        record.gratitude_2 = request.form.get('gratitude_2')
        record.gratitude_3 = request.form.get('gratitude_3')
        record.gratitude_4 = request.form.get('gratitude_4')
        record.gratitude_5 = request.form.get('gratitude_5')
        db.session.commit()
        flash('Gratitude journal entry saved.', 'success')
        return redirect(url_for('mypage'))
        
    # [해결 3] gratitude.html 내부의 'entries' 리스트형 변수 바인딩 누락 해결
    entries = [
        record.gratitude_1 or '',
        record.gratitude_2 or '',
        record.gratitude_3 or '',
        record.gratitude_4 or '',
        record.gratitude_5 or ''
    ]
    return render_template('gratitude.html', record=record, entries=entries, **CONTEXT_DATA)

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user_id = session['user_id']
    records = DailyRecord.query.filter_by(user_id=user_id).order_by(DailyRecord.date.desc()).all()
    return render_template('history.html', records=records)

@app.route('/bible')
@app.route('/bible/<book_name>/<int:chapter_num>')
def bible_reader(book_name="Genesis", chapter_num=1):
    book_key = book_name.lower()
    
    # Try abbreviation match or name match
    if book_key not in BIBLE_BOOKS_MAP:
        found = False
        for name, b_data in BIBLE_BOOKS_MAP.items():
            if b_data['abbrev'].lower() == book_key:
                book_name = b_data['name']
                book_key = name
                found = True
                break
        if not found:
            flash("Book not found.", "error")
            return redirect(url_for('bible_reader', book_name="Genesis", chapter_num=1))
            
    book_data = BIBLE_BOOKS_MAP[book_key]
    total_chapters = len(book_data['chapters'])
    
    if chapter_num < 1 or chapter_num > total_chapters:
        flash(f"Invalid chapter. {book_data['name']} has {total_chapters} chapters.", "error")
        return redirect(url_for('bible_reader', book_name=book_data['name'], chapter_num=1))
        
    verses_list = book_data['chapters'][chapter_num - 1]
    verses = [{"num": i + 1, "text": text} for i, text in enumerate(verses_list)]
    
    books_list = [{"name": b['name'], "abbrev": b['abbrev'], "chapters_count": len(b['chapters'])} for b in BIBLE_DATA]
    
    return render_template('bible.html', 
                           current_book=book_data['name'],
                           current_chapter=chapter_num,
                           total_chapters=total_chapters,
                           verses=verses,
                           books=books_list)

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    results = []
    capped = False
    if query:
        needle = query.lower()
        for book in BIBLE_DATA:
            for ci, chapter in enumerate(book['chapters']):
                for vi, text in enumerate(chapter):
                    if needle in text.lower():
                        results.append({
                            'book': book['name'],
                            'chapter': ci + 1,
                            'verse': vi + 1,
                            'text': text,
                        })
                        if len(results) >= 200:
                            capped = True
                            break
                if capped:
                    break
            if capped:
                break
    return render_template('search.html', query=query, results=results, capped=capped)

# DB 스키마 자동 생성
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)