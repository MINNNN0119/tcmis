import requests
from bs4 import BeautifulSoup

from flask import Flask, render_template, request
from datetime import datetime

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# 判斷是在 Vercel 還是本地
if os.path.exists('serviceAccountKey.json'):
    # 本地環境：讀取檔案
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境：從環境變數讀取 JSON 字串
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

firebase_admin.initialize_app(cred)


app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入陳彥閔的網站20260409</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=彥閔&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/calculate>次方與根號計算</a><hr>"
    link += "<a href=/read>讀取Firestore資料</a><hr>"
    link += "<a href=/read2>讀取Firestore資料(根據姓名關鍵字)</a><hr>"
    link += "<a href=/spider1>爬取子青老師本學期課程</a><hr>"
    link += "<a href=/movie1>爬取即將上映電影</a><hr>"
    return link

@app.route("/search", methods=["GET", "POST"])
def search():
    # 1. 建立搜尋表單介面
    html_form = """
    <form method="POST" action="/search">
        <h2>電影搜尋系統</h2>
        請輸入片名關鍵字：<input type="text" name="keyword">
        <input type="submit" value="開始搜尋">
    </form>
    <hr>
    """
    
    if request.method == "POST":
        keyword = request.form.get("keyword")
        R = f"<h3>「{keyword}」的搜尋結果：</h3>"
        
        # 2. 開始爬蟲
        url = "http://www.atmovies.com.tw/movie/next/"
        Data = requests.get(url)
        Data.encoding = "utf-8"
        sp = BeautifulSoup(Data.text, "html.parser")
        result = sp.select(".filmListAllX li")
        
        found_count = 0
        for item in result:
            try:
                img_tag = item.find("img")
                name = img_tag.get("alt") # 取得片名
                
                # 3. 關鍵字過濾判斷
                if keyword in name:
                    found_count += 1
                    # 取得介紹頁連結
                    intro_link = "https://www.atmovies.com.tw" + item.find("a").get("href")
                    # 取得海報圖片網址
                    img_src = "https://www.atmovies.com.tw" + img_tag.get("src")
                    
                    # 4. 組合 HTML：包含超連結與圖片標籤
                    R += f'<div>'
                    R += f'  <h4><a href="{intro_link}" target="_blank">{name}</a></h4>'
                    R += f'  <img src="{img_src}" width="150" style="border:1px solid #ccc;"><br>'
                    R += f'</div><hr>'
            except:
                continue
        
        if found_count == 0:
            R += "<p>找不到相關電影，請換個關鍵字試試看！</p>"
            
        return html_form + R

    # GET 請求時只顯示搜尋框
    return html_form


@app.route("/spider1")
def spider1():
    R = ""
    url = "https://www1.pu.edu.tw/~tcyang/course.html"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    #print(Data.text)
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select(".team-box a")

    for i in result:
        R += i.text + i.get("href") + "<br>"
    return R

@app.route("/read2", methods=["GET", "POST"])
def read2():
    Result = "請輸入關鍵字<br>"
    Result += """
    <form method="POST" action="/read2">
        <input type="text" name="keyword">
        <input type="submit" value="查詢">
    </form><br>
    """
    
    keyword = request.form.get("keyword")
    db = firestore.client()
    collection_ref = db.collection("靜宜資管")
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).get()
    
    found = False
    
    if keyword:
        for doc in docs:
            teacher = doc.to_dict()
            if keyword in teacher["name"]:
                Result += str(teacher) + "<br>"
                found = True
        
        if not found:
            Result += "抱歉，查無此關鍵字相關之老師資料"

    Result += '<br><a href="/">返回首頁</a>'
            
    return Result


@app.route("/read")
def read():
    Result = ""
    db = firestore.client()
    collection_ref = db.collection("靜宜資管") 
    docs = collection_ref.order_by("lab",direction=firestore.Query.DESCENDING).get()
    for doc in docs:         
        Result += str(doc.to_dict()) + "<br>"    
    return Result

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime=str(now))

@app.route("/me")
def me():
    return render_template("mis2026B.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user = request.values.get("u")
    d = request.values.get("d")
    c = request.values.get("c")
    return render_template("welcome.html", name=user, dep=d, course=c)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "；密碼為：" + pwd
        return result
    else:
        return render_template("account.html")

@app.route("/calculate", methods=["GET", "POST"])
def calculate():
    if request.method == "POST":
        x = float(request.form.get("x"))
        opt = request.form.get("opt")
        y = float(request.form.get("y"))
        
        if opt == "次方":
            res = x ** y
            result_str = f"{x} 的 {y} 次方 = {res}"
        elif opt == "根號":
            if x < 0 and y % 2 == 0:
                result_str = "錯誤：負數不能開偶數次方根"
            else:
                res = x ** (1/y)
                result_str = f"{x} 的 {y} 次方根 = {res}"
        else:
            result_str = "無效的運算"
            
        return f"<h1>計算結果</h1><p>{result_str}</p><a href='/calculate'>重新計算</a>"

    html_form = """
    <h1>次方與根號計算</h1>
    <form method="post">
        x: <input type="number" step="any" name="x" required><br>
        運算: 
        <select name="opt">
            <option value="次方">次方</option>
            <option value="根號">根號</option>
        </select><br>
        y: <input type="number" step="any" name="y" required><br>
        <button type="submit">計算</button>
    </form>
    <br><a href="/">返回首頁</a>
    """
    return html_form

if __name__ == "__main__":
    app.run(debug=True)
