from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

@app.route("/")
def index():
    link = "<h1>歡迎進入陳彥閔的網站20260409</h1>"
    link += "<a href=/mis>課程</a><hr>"
    link += "<a href=/today>現在日期時間</a><hr>"
    link += "<a href=/me>關於我</a><hr>"
    link += "<a href=/welcome?u=彥閔&d=靜宜資管&c=資訊管理導論>Get傳值</a><hr>"
    link += "<a href=/calculate>次方與根號計算</a><hr>"
    return link

@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>返回首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime=str(now))

@app.route("/me")
def me():
    return render_template("mis2026b.html")

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