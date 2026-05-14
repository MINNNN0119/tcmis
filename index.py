import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request
from datetime import datetime
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore

# --- 1. Firebase 初始化 ---
if os.path.exists('serviceAccountKey.json'):
    # 本地環境
    cred = credentials.Certificate('serviceAccountKey.json')
else:
    # 雲端環境 (Vercel)
    firebase_config = os.getenv('FIREBASE_CONFIG')
    cred_dict = json.loads(firebase_config)
    cred = credentials.Certificate(cred_dict)

# 避免重複初始化
if not firebase_admin._apps:
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
    link += "<a href=/spiderMovie>查看日期以及爬取即將上映電影</a><hr>"
    link += "<a href=/searchMovie>透過資料庫搜尋即將上映電影</a><hr>"
    link += "<a href=/road>台中市十大肇事路口</a><hr>"
    link += "<a href=/weather>讀取各縣市天氣</a><hr>"
    link += "<a href=/rate>本周新片進DB</a><hr>"
    return link


@app.route("/rate")
def rate():
    #本週新片
    url = "https://www.atmovies.com.tw/movie/new/"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    sp = BeautifulSoup(Data.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text[5:]
    print(lastUpdate)
    print()

    result=sp.select(".filmList")

    for x in result:
        title = x.find("a").text
        introduce = x.find("p").text

        movie_id = x.find("a").get("href").replace("/", "").replace("movie", "")
        hyperlink = "http://www.atmovies.com.tw/movie/" + movie_id
        picture = "https://www.atmovies.com.tw/photo101/" + movie_id + "/pm_" + movie_id + ".jpg"

        r = x.find(class_="runtime").find("img")
        rate = ""
        if r != None:
            rr = r.get("src").replace("/images/cer_", "").replace(".gif", "")
            if rr == "G":
                rate = "普遍級"
            elif rr == "P":
                rate = "保護級"
            elif rr == "F2":
                rate = "輔12級"
            elif rr == "F5":
                rate = "輔15級"
            else:
                rate = "限制級"

        t = x.find(class_="runtime").text

        t1 = t.find("片長")
        t2 = t.find("分")
        showLength = t[t1+3:t2]

        t1 = t.find("上映日期")
        t2 = t.find("上映廳數")
        showDate = t[t1+5:t2-8]

        doc = {
            "title": title,
            "introduce": introduce,
            "picture": picture,
            "hyperlink": hyperlink,
            "showDate": showDate,
            "showLength": int(showLength),
            "rate": rate,
            "lastUpdate": lastUpdate
        }

        db = firestore.client()
        doc_ref = db.collection("本週新片含分級").document(movie_id)
        doc_ref.set(doc)
    return "本週新片已爬蟲及存檔完畢，網站最近更新日期為：" + lastUpdate

@app.route("/road")
def road():
    R = "<h1>台中市十大肇事路口 (113年10月)作者:陳彥閔</h1><br>"
    
    url = "https://taichung.gov.tw"
    
    # 1. 加上 headers 避免被網站封鎖 (這是你之前遇到 Connection aborted 的主因)
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    
    try:
        Data = requests.get(url, headers=headers)
        JsonData = Data.json() # 直接用 .json() 更方便
        
        for item in JsonData:
            # 2. 改用 .get() 取值。如果名稱不對，會顯示 "無資料" 而不會報 500 錯誤
            # 同時確認你的 JSON 欄位名稱是否正確 (可先用 print(item) 檢查)
            location = item.get("路口名稱", "未知路口")
            reason = item.get("主要肇因", item.get("肇因", "原因不明")) # 嘗試抓取可能的名字
            count = item.get("總件數", item.get("件數", "0"))
            
            R += f"{location}，原因：{reason}，件數：{count}<br>"
            
    except Exception as e:
        return f"讀取資料發生錯誤：{e}"

    return R

# --- 3. 天氣查詢功能 ---
@app.route("/weather")
def weather_query():
    city = request.args.get("city", "")
    ui = """
    <h2>各縣市天氣查詢</h2>
    <form action="/weather" method="get">
        請輸入縣市名稱：<input type="text" name="city" placeholder="例如：臺中市">
        <input type="submit" value="查詢">
    </form>
    <br><a href="/">回首頁</a><hr>
    """
    if city:
        city_fixed = city.replace("台", "臺")
        url = f"https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-C0032-001?Authorization=rdec-key-123-45678-011121314&format=JSON&locationName={city_fixed}"
        try:
            res = requests.get(url).json()
            if res.get("records") and res["records"].get("location"):
                loc = res["records"]["location"][0]
                wx = loc["weatherElement"][0]["time"][0]["parameter"]["parameterName"]
                pop = loc["weatherElement"][1]["time"][0]["parameter"]["parameterName"]
                ui += f"<h3>{city_fixed} 的預報結果：</h3>"
                ui += f"目前天氣：{wx}<br>"
                ui += f"降雨機率：{pop}%"
            else:
                ui += f"<p style='color:red;'>找不到「{city}」的資料，請輸入完整名稱（如：臺中市）。</p>"
        except Exception as e:
            ui += f"<p style='color:red;'>連線錯誤：{str(e)}</p>"
    return ui

# --- 4. 電影搜尋與爬蟲功能 ---
@app.route("/searchMovie", methods=["GET", "POST"])
def searchMovie():
    R = "<h1>搜尋資料庫電影</h1><form method='POST' action='/searchMovie'><p>請輸入片名關鍵字：<input type='text' name='keyword'></p><button type='submit'>從資料庫查詢</button></form><hr>"
    if request.method == "POST":
        keyword = request.form.get("keyword")
        db = firestore.client()
        docs = db.collection("電影2B").get()
        found, count = False, 0
        for doc in docs:
            movie = doc.to_dict()
            if keyword in movie.get("title", ""):
                found, count = True, count + 1
                R += f"<b>編號：</b>{doc.id}<br><b>片名：</b>{movie.get('title')}<br><b>上映日期：</b>{movie.get('showDate')}<br><a href='{movie.get('hyperlink')}' target='_blank'>查看介紹</a><br><img src='{movie.get('picture')}' width='200'><br><hr>"
        if not found: R += f"<p>找不到「{keyword}」相關電影</p>"
        else: R += f"<p>共找到 {count} 部電影</p>"
    R += '<a href="/">返回首頁</a>'
    return R

@app.route("/spiderMovie")
def spiderMovie():
    db = firestore.client()
    url = "http://www.atmovies.com.tw/movie/next/"
    res = requests.get(url)
    res.encoding = "utf-8"
    sp = BeautifulSoup(res.text, "html.parser")
    lastUpdate = sp.find(class_="smaller09").text.replace("更新時間：", "")
    result = sp.select(".filmListAllX li")
    total = 0
    for item in result:
        total += 1
        movie_id = item.find("a").get("href").replace("/movie/", "").replace("/", "")
        title = item.find(class_="filmtitle").text
        picture = "http://www.atmovies.com.tw" + item.find("img").get("src")
        hyperlink = "http://www.atmovies.com.tw" + item.find("a").get("href")
        showDate = item.find(class_="runtime").text[5:15]
        db.collection("電影2B").document(movie_id).set({
            "title": title, "picture": picture, "hyperlink": hyperlink, "showDate": showDate, "lastUpdate": lastUpdate
        })
    return f"網站更新日期：{lastUpdate}<br>總共爬取 {total} 部電影到資料庫"

# --- 5. 其他輔助功能 (Firestore 讀取、計算機等) ---
@app.route("/read2", methods=["GET", "POST"])
def read2():
    Result = "請輸入關鍵字<br><form method='POST' action='/read2'><input type='text' name='keyword'><input type='submit' value='查詢'></form><br>"
    keyword = request.form.get("keyword")
    if keyword:
        db = firestore.client()
        docs = db.collection("靜宜資管").get()
        found = False
        for doc in docs:
            teacher = doc.to_dict()
            if keyword in teacher["name"]:
                Result += str(teacher) + "<br>"
                found = True
        if not found: Result += "查無老師資料"
    Result += '<br><a href="/">返回首頁</a>'
    return Result

@app.route("/calculate", methods=["GET", "POST"])
def calculate():
    if request.method == "POST":
        x, y = float(request.form.get("x")), float(request.form.get("y"))
        opt = request.form.get("opt")
        if opt == "次方": res = x ** y
        else: res = "錯誤" if x < 0 and y % 2 == 0 else x ** (1/y)
        return f"<h1>計算結果：{res}</h1><br><a href='/calculate'>重新計算</a>"
    return """<h1>次方與根號計算</h1><form method="post">x: <input type="number" step="any" name="x"><select name="opt"><option value="次方">次方</option><option value="根號">根號</option></select>y: <input type="number" step="any" name="y"><button type="submit">計算</button></form><br><a href="/">返回首頁</a>"""

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime=str(now))

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/me")
def me():
    return render_template("mis2026B.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    user, d, c = request.values.get("u"), request.values.get("d"), request.values.get("c")
    return render_template("welcome.html", name=user, dep=d, course=c)

# --- 6. 啟動伺服器 ---
if __name__ == "__main__":
    app.run(debug=True)