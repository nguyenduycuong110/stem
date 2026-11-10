import sqlite3
from datetime import datetime

from flask import (Flask, abort, g, redirect, render_template_string,
                   request, session, url_for)

app = Flask(__name__)
app.secret_key = "doi-chuoi-bi-mat-nay-truoc-khi-dung-that"
DB = "diendan.db"
SUBJECTS = ["Toán", "Lập trình", "Tiếng Anh", "Vật lý", "Hóa học", "Khác"]


# ---------- Database ----------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(_):
    db = g.pop("db", None)
    if db:
        db.close()


def now():
    return datetime.now().strftime("%d/%m/%Y %H:%M")


def init_db():
    db = sqlite3.connect(DB)
    db.executescript("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT, title TEXT, body TEXT, author TEXT, created TEXT
        );
        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER, author TEXT, body TEXT, created TEXT
        );
    """)
    db.commit()
    db.close()


# ---------- Giao diện (HTML) ----------
PAGE = """
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Góc học tập</title>
<style>
 body{font-family:system-ui,"Segoe UI",sans-serif;background:#f6f7fb;color:#1d2433;margin:0}
 .wrap{max-width:860px;margin:0 auto;padding:16px}
 header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
 h1{font-size:22px;margin:0}
 a{color:#4f46e5;text-decoration:none}
 .card{background:#fff;border:1px solid #e3e6ef;border-radius:12px;padding:14px;margin:12px 0}
 .meta{font-size:13px;color:#6b7488}
 .tag{background:#eef0ff;color:#4f46e5;border-radius:6px;padding:1px 8px;font-size:12px;margin-right:6px}
 .chips a{display:inline-block;border:1px solid #e3e6ef;background:#fff;border-radius:99px;padding:5px 14px;margin:0 6px 6px 0;color:#1d2433;font-size:14px}
 .chips a.on{background:#4f46e5;color:#fff;border-color:#4f46e5}
 input,textarea,select{width:100%;box-sizing:border-box;font:inherit;padding:9px;border:1px solid #e3e6ef;border-radius:8px;margin-bottom:8px}
 textarea{min-height:90px}
 button{font:inherit;cursor:pointer;border-radius:8px;border:1px solid #e3e6ef;background:#fff;padding:7px 14px}
 button.p{background:#4f46e5;color:#fff;border-color:#4f46e5}
 .body{white-space:pre-wrap;word-break:break-word;margin:8px 0}
 .reply{border-left:3px solid #e3e6ef;padding-left:12px;margin:12px 0}
</style>
</head>
<body>
<div class="wrap">
<header>
  <h1><a href="{{ url_for('home') }}">📚 Góc học tập</a></h1>
  {% if user %}
  <form method="post" action="{{ url_for('logout') }}" style="margin:0">
    Xin chào, <b>{{ user }}</b> <button>Đăng xuất</button>
  </form>
  {% endif %}
</header>

{% if not user %}
  <div class="card">
    <h3>Nhập tên để tham gia</h3>
    <form method="post" action="{{ url_for('login') }}">
      <input name="name" maxlength="30" placeholder="Tên hiển thị của bạn" required>
      <button class="p">Vào diễn đàn</button>
    </form>
  </div>

{% elif post %}
  <a href="{{ url_for('home') }}">← Quay lại</a>
  <div class="card">
    <h2 style="margin:0 0 4px">{{ post.title }}</h2>
    <div class="meta"><span class="tag">{{ post.subject }}</span>{{ post.author }} · {{ post.created }}</div>
    <div class="body">{{ post.body }}</div>
    {% if post.author == user %}
    <form method="post" action="{{ url_for('delete_post', post_id=post.id) }}"
          onsubmit="return confirm('Xóa bài viết này?')"><button>Xóa bài</button></form>
    {% endif %}
  </div>
  <h3>{{ replies|length }} trả lời</h3>
  {% for r in replies %}
    <div class="reply">
      <div class="meta"><b>{{ r.author }}</b> · {{ r.created }}</div>
      <div class="body">{{ r.body }}</div>
    </div>
  {% endfor %}
  <div class="card">
    <form method="post" action="{{ url_for('reply', post_id=post.id) }}">
      <textarea name="body" placeholder="Viết câu trả lời của bạn..." required></textarea>
      <button class="p">Gửi trả lời</button>
    </form>
  </div>

{% else %}
  <div class="chips">
    <a href="{{ url_for('home') }}" class="{{ 'on' if not subject }}">Tất cả</a>
    {% for s in subjects %}
      <a href="{{ url_for('home', s=s) }}" class="{{ 'on' if s == subject }}">{{ s }}</a>
    {% endfor %}
  </div>

  <div class="card">
    <h3 style="margin-top:0">Đặt câu hỏi mới</h3>
    <form method="post" action="{{ url_for('new_post') }}">
      <input name="title" maxlength="120" placeholder="Tiêu đề câu hỏi" required>
      <select name="subject">
        {% for s in subjects %}<option>{{ s }}</option>{% endfor %}
      </select>
      <textarea name="body" placeholder="Mô tả chi tiết vấn đề bạn đang gặp..." required></textarea>
      <button class="p">Đăng bài</button>
    </form>
  </div>

  <form method="get">
    {% if subject %}<input type="hidden" name="s" value="{{ subject }}">{% endif %}
    <input name="q" value="{{ q }}" placeholder="🔍 Tìm bài viết rồi nhấn Enter">
  </form>

  {% for p in posts %}
    <div class="card">
      <h3 style="margin:0 0 4px"><a href="{{ url_for('view_post', post_id=p.id) }}">{{ p.title }}</a></h3>
      <div class="meta"><span class="tag">{{ p.subject }}</span>{{ p.author }} · {{ p.created }} · 💬 {{ p.n }}</div>
    </div>
  {% else %}
    <p class="meta" style="text-align:center">Chưa có bài viết nào. Hãy là người đầu tiên đặt câu hỏi!</p>
  {% endfor %}
{% endif %}
</div>
</body>
</html>
"""


def page(**kw):
    return render_template_string(PAGE, user=session.get("user"),
                                  subjects=SUBJECTS, post=None, **kw)


def need_login():
    if not session.get("user"):
        abort(403)


# ---------- Các trang ----------
@app.route("/")
def home():
    subject = request.args.get("s", "")
    q = request.args.get("q", "").strip()
    sql = ("SELECT p.*, (SELECT COUNT(*) FROM replies r WHERE r.post_id = p.id) AS n "
           "FROM posts p WHERE 1=1")
    args = []
    if subject in SUBJECTS:
        sql += " AND p.subject = ?"
        args.append(subject)
    else:
        subject = ""
    if q:
        sql += " AND (p.title LIKE ? OR p.body LIKE ?)"
        args += [f"%{q}%", f"%{q}%"]
    sql += " ORDER BY p.id DESC"
    posts = get_db().execute(sql, args).fetchall()
    return page(posts=posts, subject=subject, q=q)


@app.route("/post/<int:post_id>")
def view_post(post_id):
    db = get_db()
    post = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post is None:
        abort(404)
    replies = db.execute("SELECT * FROM replies WHERE post_id = ? ORDER BY id",
                         (post_id,)).fetchall()
    return render_template_string(PAGE, user=session.get("user"),
                                  subjects=SUBJECTS, post=post, replies=replies)


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("name", "").strip()[:30]
    if name:
        session["user"] = name
    return redirect(url_for("home"))


@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


@app.route("/new", methods=["POST"])
def new_post():
    need_login()
    title = request.form.get("title", "").strip()
    body = request.form.get("body", "").strip()
    subject = request.form.get("subject", "Khác")
    if title and body and subject in SUBJECTS:
        db = get_db()
        cur = db.execute(
            "INSERT INTO posts (subject,title,body,author,created) VALUES (?,?,?,?,?)",
            (subject, title, body, session["user"], now()))
        db.commit()
        return redirect(url_for("view_post", post_id=cur.lastrowid))
    return redirect(url_for("home"))


@app.route("/post/<int:post_id>/reply", methods=["POST"])
def reply(post_id):
    need_login()
    body = request.form.get("body", "").strip()
    if body:
        db = get_db()
        db.execute("INSERT INTO replies (post_id,author,body,created) VALUES (?,?,?,?)",
                   (post_id, session["user"], body, now()))
        db.commit()
    return redirect(url_for("view_post", post_id=post_id))


@app.route("/post/<int:post_id>/delete", methods=["POST"])
def delete_post(post_id):
    need_login()
    db = get_db()
    db.execute("DELETE FROM replies WHERE post_id = ? AND post_id IN "
               "(SELECT id FROM posts WHERE id = ? AND author = ?)",
               (post_id, post_id, session["user"]))
    db.execute("DELETE FROM posts WHERE id = ? AND author = ?",
               (post_id, session["user"]))
    db.commit()
    return redirect(url_for("home"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)