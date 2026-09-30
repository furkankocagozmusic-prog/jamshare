
import os, secrets
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from supabase import create_client

app = Flask(__name__)
app.secret_key = os.environ.get("JAMSHARE_SECRET", secrets.token_hex(32))

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
BUCKET = "audio"
sb = create_client(SUPABASE_URL, SUPABASE_KEY)

def current_user():
    return session.get("user")

@app.route("/")
def index():
    rows = sb.table("tracks").select("*").order("created_at", desc=True).execute().data
    return render_template("index.html", tracks=rows, user=current_user())

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username=request.form["username"].strip()
        email=request.form["email"].strip().lower()
        password=request.form["password"]
        if len(username)<2 or len(password)<8:
            flash("Kullanıcı adı en az 2, şifre en az 8 karakter olmalı.")
            return redirect(url_for("register"))
        try:
            existing=sb.table("users").select("id").or_(f"email.eq.{email},username.eq.{username}").execute().data
            if existing:
                flash("Bu kullanıcı adı veya e-posta zaten kullanılıyor.")
                return redirect(url_for("register"))
            sb.table("users").insert({
                "username":username, "email":email,
                "password_hash":generate_password_hash(password),
                "role":"user"
            }).execute()
            flash("Hesabın oluşturuldu.")
            return redirect(url_for("login"))
        except Exception:
            flash("Kayıt sırasında bir hata oluştu.")
    return render_template("auth.html", mode="register")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form["email"].strip().lower()
        password=request.form["password"]
        data=sb.table("users").select("*").eq("email",email).limit(1).execute().data
        if data and check_password_hash(data[0]["password_hash"], password):
            u=data[0]
            session["user"]={"id":u["id"],"username":u["username"],"role":u["role"]}
            return redirect(url_for("admin" if u["role"]=="admin" else "index"))
        flash("E-posta veya şifre hatalı.")
    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/upload", methods=["POST"])
def upload():
    u=current_user()
    if not u: return redirect(url_for("login"))
    f=request.files.get("audio")
    title=request.form.get("title","").strip()
    if not f or not title:
        flash("Kayıt adı ve ses dosyası gerekli."); return redirect(url_for("index"))
    ext=f.filename.rsplit(".",1)[-1].lower() if "." in f.filename else ""
    if ext not in {"mp3","wav","m4a","ogg"}:
        flash("MP3, WAV, M4A veya OGG yükleyebilirsin."); return redirect(url_for("index"))
    content=f.read()
    if len(content)>50*1024*1024:
        flash("Bu sürümde dosya boyutu 50 MB ile sınırlı."); return redirect(url_for("index"))
    path=f"{u['id']}/{secrets.token_hex(12)}.{ext}"
    sb.storage.from_(BUCKET).upload(path, content, {"content-type": f.mimetype or "audio/mpeg"})
    public_url=sb.storage.from_(BUCKET).get_public_url(path)
    sb.table("tracks").insert({
        "title":title, "username":u["username"],
        "user_id":u["id"], "storage_path":path, "audio_url":public_url
    }).execute()
    flash("Kayıt JamShare'a yüklendi.")
    return redirect(url_for("index"))

@app.route("/admin")
def admin():
    u=current_user()
    if not u or u["role"]!="admin": return "Yetkisiz erişim",403
    users=sb.table("users").select("id,username,email,role,created_at").order("created_at", desc=True).execute().data
    tracks=sb.table("tracks").select("*").order("created_at", desc=True).execute().data
    return render_template("admin.html", users=users, tracks=tracks)

@app.route("/admin/delete/<track_id>", methods=["POST"])
def delete_track(track_id):
    u=current_user()
    if not u or u["role"]!="admin": return "Yetkisiz erişim",403
    rows=sb.table("tracks").select("storage_path").eq("id",track_id).limit(1).execute().data
    if rows:
        try: sb.storage.from_(BUCKET).remove([rows[0]["storage_path"]])
        except Exception: pass
        sb.table("tracks").delete().eq("id",track_id).execute()
    return redirect(url_for("admin"))

@app.get("/health")
def health(): return {"ok":True}

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
