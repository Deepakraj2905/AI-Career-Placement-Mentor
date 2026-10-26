import os, re, sqlite3, json
from pathlib import Path
from datetime import datetime
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

ROOT=Path(__file__).resolve().parent; UPLOADS=ROOT/'uploads'; UPLOADS.mkdir(exist_ok=True)
app=Flask(__name__); app.secret_key=os.getenv('FLASK_SECRET_KEY','change-this-before-deployment'); app.config['MAX_CONTENT_LENGTH']=8*1024*1024
DB=ROOT/'career_mentor.db'
ROLES={
 'Python Developer':['python','sql','git','api','data structures'],
 'AI/ML Engineer':['python','machine learning','statistics','pandas','scikit-learn','nlp'],
 'Data Analyst':['sql','python','excel','statistics','data visualization','pandas'],
 'Web Developer':['html','css','javascript','api','git'],
 'Backend Developer':['python','sql','api','database','git','testing'],
 'Software Engineer':['programming','data structures','algorithms','sql','git','testing'],
 'Java Developer':['java','oop','sql','spring boot','rest api','git']}
SKILLS=sorted(set(s for v in ROLES.values() for s in v)|{'html','css','javascript','java','react','c','c++','communication','aptitude'})
def db():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init_db():
 with db() as c:
  c.execute('CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL)')
  c.execute('CREATE TABLE IF NOT EXISTS profiles(user_id INTEGER PRIMARY KEY,education TEXT DEFAULT "",skills TEXT DEFAULT "",interests TEXT DEFAULT "",target_role TEXT DEFAULT "")')
  c.execute('CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY,user_id INTEGER,filename TEXT,skills TEXT,score INTEGER,suggestions TEXT,created_at TEXT)')
  c.execute('CREATE TABLE IF NOT EXISTS activity(id INTEGER PRIMARY KEY,user_id INTEGER,kind TEXT,created_at TEXT)')
init_db()
def auth(f):
 @wraps(f)
 def w(*a,**k):
  if not session.get('uid'):
   if request.path.startswith('/api/'): return jsonify(error='Please log in first.'),401
   return redirect(url_for('login'))
  return f(*a,**k)
 return w
def get_skills(text):
 t=text.lower(); return sorted(s for s in SKILLS if re.search(r'(?<![a-z0-9])'+re.escape(s)+r'(?![a-z0-9])',t))
def extract_text(path):
 if path.suffix.lower()=='.txt': return path.read_text(errors='ignore')
 if path.suffix.lower()=='.pdf':
  from pypdf import PdfReader
  return '\n'.join(p.extract_text() or '' for p in PdfReader(str(path)).pages)
 if path.suffix.lower()=='.docx':
  from docx import Document
  return '\n'.join(p.text for p in Document(str(path)).paragraphs)
 raise ValueError('Upload PDF, DOCX, or TXT only.')
def resume_analysis(text):
 skills=get_skills(text); score=min(100,25+len(skills)*7+15*bool(re.search(r'projects?',text,re.I))+10*bool(re.search(r'education|degree|college|university',text,re.I)))
 suggestions=[]
 if not re.search(r'projects?',text,re.I): suggestions.append('Add relevant projects and explain your contribution.')
 if not re.search(r'education|degree|college|university',text,re.I): suggestions.append('Add education details and graduation year.')
 if len(skills)<5: suggestions.append('Add relevant technical skills that you can confidently explain.')
 suggestions.append('Keep all claims truthful and tailor the resume to each role.')
 return skills,score,suggestions
def llm(prompt,system):
 key=os.getenv('OPENAI_API_KEY')
 if not key:return None
 try:
  from openai import OpenAI
  c=OpenAI(api_key=key); r=c.chat.completions.create(model=os.getenv('OPENAI_MODEL','gpt-4o-mini'),messages=[{'role':'system','content':system},{'role':'user','content':prompt}],temperature=.4)
  return r.choices[0].message.content.strip()
 except Exception: app.logger.exception('AI request failed'); return None
@app.route('/')
@auth
def home(): return render_template('index.html',name=session.get('name','Student'))
@app.route('/register',methods=['GET','POST'])
def register():
 if request.method=='POST':
  name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); pw=request.form.get('password','')
  if not name or not email or len(pw)<8: flash('Enter name, valid email, and password of at least 8 characters.'); return render_template('auth.html',mode='register')
  try:
   with db() as c:
    cur=c.execute('INSERT INTO users(name,email,password_hash) VALUES(?,?,?)',(name,email,generate_password_hash(pw))); c.execute('INSERT INTO profiles(user_id) VALUES(?)',(cur.lastrowid,))
   return redirect(url_for('login'))
  except sqlite3.IntegrityError: flash('Email already registered.')
 return render_template('auth.html',mode='register')
@app.route('/login',methods=['GET','POST'])
def login():
 if request.method=='POST':
  with db() as c:u=c.execute('SELECT * FROM users WHERE email=?',(request.form.get('email','').lower().strip(),)).fetchone()
  if u and check_password_hash(u['password_hash'],request.form.get('password','')): session['uid']=u['id'];session['name']=u['name'];return redirect(url_for('home'))
  flash('Email or password is incorrect.')
 return render_template('auth.html',mode='login')
@app.route('/logout')
def logout():session.clear();return redirect(url_for('login'))
@app.route('/api/profile',methods=['GET','POST'])
@auth
def profile():
 with db() as c:
  if request.method=='POST':
   d=request.get_json() or {};c.execute('UPDATE profiles SET education=?,skills=?,interests=?,target_role=? WHERE user_id=?',(d.get('education',''),d.get('skills',''),d.get('interests',''),d.get('target_role',''),session['uid']));return jsonify(message='Profile saved.')
  r=c.execute('SELECT * FROM profiles WHERE user_id=?',(session['uid'],)).fetchone();return jsonify(dict(r) if r else {})
@app.route('/api/resume',methods=['POST'])
@auth
def resume():
 f=request.files.get('resume')
 if not f or not f.filename:return jsonify(error='Choose a resume file first.'),400
 if Path(f.filename).suffix.lower() not in {'.pdf','.docx','.txt'}:return jsonify(error='Upload PDF, DOCX, or TXT only.'),400
 name=secure_filename(f.filename); p=UPLOADS/f'u{session["uid"]}_{datetime.utcnow().strftime("%Y%m%d%H%M%S")}_{name}';f.save(p)
 try: text=extract_text(p); skills,score,suggestions=resume_analysis(text)
 except Exception as e:p.unlink(missing_ok=True);return jsonify(error=str(e) if isinstance(e,ValueError) else 'Could not read the file. Try a text-based PDF, DOCX, or TXT.'),400
 with db() as c:c.execute('INSERT INTO reports(user_id,filename,skills,score,suggestions,created_at) VALUES(?,?,?,?,?,?)',(session['uid'],name,json.dumps(skills),score,json.dumps(suggestions),datetime.utcnow().isoformat()))
 return jsonify(filename=name,skills=skills,score=score,suggestions=suggestions,note='Keyword-based analysis; please review results manually.')
@app.route('/api/recommend',methods=['POST'])
@auth
def recommend():
 d=request.get_json() or {}
 with db() as c:p=c.execute('SELECT * FROM profiles WHERE user_id=?',(session['uid'],)).fetchone()
 skills=[x.strip().lower() for x in re.split(r'[,;\n]',d.get('skills') or (p['skills'] if p else '')) if x.strip()]; interests=(d.get('interests') or (p['interests'] if p else '')).lower()
 out=[]
 for role,req in ROLES.items():
  matched=sorted(set(skills)&set(req)); missing=sorted(set(req)-set(skills)); score=round(100*len(matched)/len(req));
  if any(x in role.lower() for x in interests.split()):score=min(100,score+5)
  out.append(dict(role=role,match_score=score,matched_skills=matched,missing_skills=missing))
 return jsonify(recommendations=sorted(out,key=lambda x:x['match_score'],reverse=True))
@app.route('/api/roadmap',methods=['POST'])
@auth
def roadmap():
 d=request.get_json() or {}; role=d.get('role','Software Engineer'); req=ROLES.get(role,ROLES['Software Engineer']); skills=[x.strip().lower() for x in re.split(r'[,;\n]',d.get('skills','')) if x.strip()]; missing=[x for x in req if x not in skills]
 steps=[f'Learn and practise {x} with a small exercise.' for x in missing] or ['Revise your current core skills.']
 steps += ['Build a project combining these skills.','Update your resume and practise explaining your project.','Complete a mock interview and review your feedback.']
 return jsonify(role=role,roadmap=steps)
@app.route('/api/chat',methods=['POST'])
@auth
def chat():
 d=request.get_json() or {}; msg=d.get('message','').strip()
 if not msg:return jsonify(error='Type a question first.'),400
 answer=llm(msg,'You are a helpful AI Career and Placement Mentor for engineering students. Give clear practical advice about careers, resumes, skills, and placement preparation. Never guarantee a job or salary.')
 connected=bool(answer)
 if not answer:answer='AI is not connected yet. Configure OPENAI_API_KEY on the server for AI-generated answers. Meanwhile, set a weekly goal, practise the required skills, build a project, and review your progress.'
 return jsonify(answer=answer,ai_connected=connected)
@app.route('/api/interview',methods=['POST'])
@auth
def interview():
 d=request.get_json() or {};q=d.get('question','').strip();a=d.get('answer','').strip();role=d.get('role','Software Engineer')
 if not q or not a:return jsonify(error='Enter both the question and your answer.'),400
 feedback=llm(f'Role: {role}\nQuestion: {q}\nStudent answer: {a}\nGive one strength, two improvements, and a sample better answer.','You are a supportive mock interviewer. Give constructive specific feedback; do not present it as an official hiring result.')
 if not feedback:feedback='Basic feedback: answer the question directly, include a concrete example, explain your own contribution, and state the result. Configure OPENAI_API_KEY for detailed AI feedback.'
 with db() as c:c.execute('INSERT INTO activity(user_id,kind,created_at) VALUES(?,?,?)',(session['uid'],'mock_interview',datetime.utcnow().isoformat()))
 return jsonify(feedback=feedback)
@app.route('/api/dashboard')
@auth
def dashboard():
 with db() as c:
  r=c.execute('SELECT * FROM reports WHERE user_id=? ORDER BY id DESC LIMIT 1',(session['uid'],)).fetchone();p=c.execute('SELECT * FROM profiles WHERE user_id=?',(session['uid'],)).fetchone();n=c.execute('SELECT COUNT(*) n FROM activity WHERE user_id=?',(session['uid'],)).fetchone()['n']
 skills=json.loads(r['skills']) if r else ([x.strip() for x in p['skills'].split(',') if x.strip()] if p else []); rs=r['score'] if r else 0;ready=min(100,round(rs*.4+min(40,len(skills)*5)+min(20,n*5)))
 return jsonify(resume_score=rs,skills_count=len(skills),practice_sessions=n,readiness_score=ready,note='Illustrative score only; not a prediction of hiring outcomes.')
if __name__=='__main__':app.run(host='0.0.0.0',port=int(os.getenv('PORT','5000')))
