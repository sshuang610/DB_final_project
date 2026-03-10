from flask import Flask, request, jsonify, session, render_template, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
import hashlib
import uuid

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 記得換成自己安全的金鑰

# ---------------------------------------------------------
# 資料庫連線配置
# ---------------------------------------------------------
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'fp',
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------------------------------------------------
# 首頁路由處理：動態跳轉
# ---------------------------------------------------------
@app.route('/')
def index():
    """
    根據使用者是否登入，跳轉到對應頁面
    """
    if 'username' in session:
        # 如果已登入，跳轉到首頁(homepage)
        return redirect(url_for('homepage'))
    else:
        # 如果未登入，跳轉到登入頁面
        return redirect(url_for('database_login'))

# ---------------------------------------------------------
# 登入頁面 + 處理登入 (GET/POST)
# ---------------------------------------------------------
@app.route('/database', methods=['GET', 'POST'])
def database_login():
    """
    GET -> 顯示 login.html
    POST -> 處理表單登入
    """
    if request.method == 'GET':
        return render_template('login.html')  # 顯示登入頁面
    else:
        # POST: 處理表單提交
        user_id = request.form.get('user_id')
        username = request.form.get('username')
        password = request.form.get('password', '')

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT user_id, password FROM customers WHERE name = %s", (username,))
            result = cursor.fetchone()
            cursor.close()
            conn.close()

            if result and result['password'] == hash_password(password):
                # 登入成功
                session['username'] = username
                # 建議也把 user_id 加進 session，後續如果要查詢 meals, profile 會很方便
                session['user_id'] = result['user_id']
                flash("Login successful.")
                return redirect(url_for('homepage'))  # 跳轉到首頁
            else:
                flash("Invalid username or password.")
                return redirect(url_for('database_login'))  # 登入失敗回到登入頁面
        except Error as e:
            flash(f"Database error: {str(e)}")
            return redirect(url_for('database_login'))

# ---------------------------------------------------------
# 首頁 (Homepage)
# ---------------------------------------------------------
@app.route('/homepage', methods=['GET'])
def homepage():
    """
    登入後的首頁，顯示 homepage.html
    """
    if 'username' not in session:
        flash("Please log in first.")
        return redirect(url_for('database_login'))  # 未登入跳轉到登入頁面

    # 如果已登入，顯示首頁
    return render_template('homepage.html', username=session['username'])

# ---------------------------------------------------------
# 登出功能
# ---------------------------------------------------------
@app.route('/logout', methods=['GET'])
def logout():
    """
    登出功能：清除 session 並跳轉到登入頁面
    """
    session.clear()  # 清除 session 資訊
    flash("You have been logged out.")
    return redirect(url_for('database_login'))

# ---------------------------------------------------------
# (A) Signup (同時支援 GET/POST)
# ---------------------------------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    - GET: 顯示 signup.html
    - POST: 接收表單提交，處理帳號註冊
    """
    if request.method == 'GET':
        return render_template('signup.html')
    else:
        # 從表單中取得資料
        username = request.form.get('username')
        password = request.form.get('password')

        # 檢查表單資料是否完整
        if not username or not password:
            flash("Please enter both username and password.")
            return redirect(url_for('signup'))

        # 將密碼進行哈希處理
        hashed_password = hash_password(password)

        # 插入資料庫
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO customers (name, password) VALUES (%s, %s)", (username, hashed_password))
            conn.commit()
            cursor.close()
            conn.close()
            flash("Account created successfully.")
            return redirect(url_for('database_login'))  # 註冊成功後跳轉到登入頁面
        except Error as e:
            flash(f"Database error: {str(e)}")
            return redirect(url_for('signup'))

# ---------------------------------------------------------
# (B) Profile 相關
#   1) 提供 JSON API (GET / PUT) => /profile
#   2) 提供 HTML 頁面 (GET) => /profile_view
# ---------------------------------------------------------

@app.route('/profile_view', methods=['GET'])
def profile_view():
    """
    - GET: 顯示 profile.html
    (顯示使用者個人頁，可能前端可以用 Ajax 再去打 /profile 拿 JSON)
    """
    if 'username' not in session:
        flash("Please log in first.")
        return redirect(url_for('database_login'))

    # 你可以選擇在後端就把 user 資料查出來帶進模板，
    # 或者只渲染空的 profile.html，讓前端自己透過 Ajax 拿 /profile 的 JSON。
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM customers WHERE name = %s", (session['username'],))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user:
            return render_template('profile.html', user=user)
        else:
            flash("User not found.")
            return redirect(url_for('homepage'))
    except Error as e:
        flash(f"Database error: {str(e)}")
        return redirect(url_for('homepage'))

@app.route('/profile', methods=['GET'])
def profile():
    """顯示使用者的個人資料頁面。"""
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in first.")
        return redirect(url_for('database_login'))

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute("SELECT * FROM customers WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    # 處理資料不足時的預設值
    if not user:
        user = {
            "name": "",
            "weight": None,
            "height": None,
            "age": None,
            "workout_frequency": None,
            "bmi": "N/A",
            "bmr": "N/A",
            "tdee": "N/A"
        }
    else:
        # 確保資料完整性
        weight = user['weight'] if user['weight'] else None
        height = user['height'] if user['height'] else None
        age = user['age'] if user['age'] else None
        workout_frequency = user['workout_frequency'] if user['workout_frequency'] else 0

        if weight and height and age:
            user['bmi'] = round(weight / ((height / 100) ** 2), 2)
            user['bmr'] = round(10 * weight + 6.25 * height - 5 * age + 5, 2)
            user['tdee'] = round(user['bmr'] * (1.2 + 0.1 * workout_frequency), 2)
        else:
            user['bmi'] = "N/A"
            user['bmr'] = "N/A"
            user['tdee'] = "N/A"

    return render_template('profile.html', user=user)

@app.route('/profile/save', methods=['POST'])
def save_profile():
    """保存或更新使用者的個人資料。"""
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in first.")
        return redirect(url_for('database_login'))

    name = request.form.get('username', "").strip()
    weight = request.form.get('weight')
    height = request.form.get('height')
    age = request.form.get('age')
    workout_frequency = request.form.get('exercise')

    # 若欄位為空，設為 None
    weight = float(weight) if weight else None
    height = float(height) if height else None
    age = int(age) if age else None
    workout_frequency = int(workout_frequency) if workout_frequency else 0

    connection = get_db_connection()
    cursor = connection.cursor()
    query = """
        INSERT INTO customers (user_id, name, weight, height, age, workout_frequency)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        name = VALUES(name), weight = VALUES(weight), height = VALUES(height),
        age = VALUES(age), workout_frequency = VALUES(workout_frequency)
    """
    cursor.execute(query, (user_id, name, weight, height, age, workout_frequency))
    connection.commit()
    cursor.close()
    connection.close()

    flash("Profile updated successfully.")
    return redirect('/profile')
# ---------------------------------------------------------
# (C) 食物搜尋
#   1) 提供 JSON API => /food/search (GET)
#   2) 顯示搜索頁面 => /search_food_view (GET)
# ---------------------------------------------------------
@app.route('/food-search', methods=['GET'])
def food_search():
    """
    提供符合關鍵字的食物建議。
    """
    keyword = request.args.get('keyword', '').strip()
    if not keyword:
        return jsonify([])  # 如果沒有輸入關鍵字，返回空清單

    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT food
            FROM foods
            WHERE food LIKE %s
            ORDER BY food
        """
        cursor.execute(query, (f"%{keyword}%",))
        results = cursor.fetchall()
        return jsonify([row['food'] for row in results])
    finally:
        connection.close()

@app.route('/food-info/details', methods=['GET'])
def food_details():
    """
    提供選中食物的詳細資訊。
    """
    food = request.args.get('food', '').strip()
    if not food:
        return jsonify({"error": "Invalid food name."})

    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT food, Caloric_Value, Protein, Fat, Carbohydrates, Sugars, Dietary_Fiber, Cholesterol,  Saturated_Fats, Monounsaturated_Fats, Polyunsaturated_Fats, Sodium, Calcium, Copper, Iron, Magnesium, Manganese, Phosphorus, Potassium, Selenium, Zinc, Nutrition_Density, Vitamin_A,Vitamin_B1,Vitamin_B2,Vitamin_B3,Vitamin_B5,Vitamin_B6,Vitamin_B11,Vitamin_B12,Vitamin_C,Vitamin_D,Vitamin_E,Vitamin_K,Water
            FROM foods
            WHERE food = %s
        """
        cursor.execute(query, (food,))
        result = cursor.fetchone()
        return jsonify(result or {"error": "Food not found."})
    finally:
        connection.close()

@app.route('/search_food_view', methods=['GET'])
def search_food_view():
    """
    - GET: 顯示一個搜食物的頁面 (search_food.html)
    """
    if 'username' not in session:
        flash("Please log in first.")
        return redirect(url_for('database_login'))
    return render_template('foofinfo.html')

# ---------------------------------------------------------
# (D) 新增飲食紀錄
#   1) 提供 JSON API => POST /diet
#   2) 顯示頁面 => GET /diet_view
# ---------------------------------------------------------
@app.route('/diet-record', methods=['GET', 'POST', 'DELETE'])
def diet_record():
    if request.method == 'GET':
        date = request.args.get('date')
        user_id = session.get('user_id')
        if not date or not user_id:
            return jsonify({}), 400

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        query = """
            SELECT time, GROUP_CONCAT(food) AS foods
            FROM meals
            WHERE user_id = %s AND date = %s
            GROUP BY time
        """
        cursor.execute(query, (user_id, date))
        records = cursor.fetchall()
        connection.close()

        result = {record['time']: record['foods'].split(',') for record in records if record['foods']}
        return jsonify(result)

    elif request.method == 'POST':
        data = request.json
        user_id = session.get('user_id')
        if not data or not user_id:
            return jsonify({'error': 'Invalid request'}), 400

        meal_time = data['meal']
        date = data['date']
        food = data['food']

        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
            INSERT INTO meals (user_id, date, time, food)
            VALUES (%s, %s, %s, %s)
        """
        try:
            cursor.execute(query, (user_id, date, meal_time, food))
            fetch_calories_query = "SELECT Caloric_Value FROM foods WHERE food = %s"
            cursor.execute(fetch_calories_query, (food,))
            calories = cursor.fetchone()
            connection.commit()
        except mysql.connector.IntegrityError:
            return jsonify({'error': 'Food already exists in the meal'}), 400
        finally:
            connection.close()

        return '', 201

    elif request.method == 'DELETE':
        data = request.json
        user_id = session.get('user_id')
        if not data or not user_id:
            return jsonify({'error': 'Invalid request'}), 400

        meal_time = data['meal']
        date = data['date']
        food = data['food']

        connection = get_db_connection()
        cursor = connection.cursor()
        query = """
            DELETE FROM meals
            WHERE user_id = %s AND date = %s AND time = %s AND food = %s
        """
        cursor.execute(query, (user_id, date, meal_time, food))
        connection.commit()
        connection.close()
        return '', 204

@app.route('/food-calories', methods=['GET'])
def food_calories():
    food_name = request.args.get('food', '').strip()
    if not food_name:
        return jsonify({'calories': 'N/A'}), 400

    connection = get_db_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT Caloric_Value FROM foods WHERE food = %s"
        cursor.execute(query, (food_name,))
        result = cursor.fetchone()
        if result:
            return jsonify({'calories': result['Caloric_Value']})
        return jsonify({'calories': 'N/A'}), 404
    finally:
        connection.close()


@app.route('/diet_view', methods=['GET'])
def diet_view():
    """
    - GET: 顯示新增飲食紀錄的頁面 (diet.html)
    """
    if 'username' not in session:
        flash("Please log in first.")
        return redirect(url_for('database_login'))
    return render_template('diet.html')

# ---------------------------------------------------------
# (E) 每日總結
#   1) 提供 JSON => GET /suggestion/daily
#   2) 如果要顯示「每日總結」頁面 => GET /daily_summary_view
# ---------------------------------------------------------
@app.route('/suggestion/<view_type>', methods=['GET'])
def suggestion(view_type):
    """
    返回每日或每週的建議資料，格式為 JSON。
    """
    if 'username' not in session:
        return jsonify({"error": "Unauthorized."}), 403

    user_id = session.get('user_id')
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        if view_type == 'daily':
            date = request.args.get('date', None) or "CURDATE()"
            query = f"""
                SELECT meals.time AS meal, 
                       GROUP_CONCAT(meals.food) AS foods,
                       SUM(foods.Caloric_Value) AS calories,
                       SUM(foods.Protein) AS protein,
                       SUM(foods.Fat) AS fat,
                       SUM(foods.Carbohydrates) AS carbs
                FROM meals
                LEFT JOIN foods ON meals.food = foods.food
                WHERE meals.user_id = %s AND meals.date = {date}
                GROUP BY meals.time
                ORDER BY FIELD(meals.time, 'Breakfast', 'Lunch', 'Snacks', 'Dinner', 'Late Night')
            """
            cursor.execute(query, (user_id,))
        elif view_type == 'weekly':
            query = """
                SELECT DATE(meals.date) AS day,
                       SUM(foods.Caloric_Value) AS calories,
                       SUM(foods.Protein) AS protein,
                       SUM(foods.Fat) AS fat,
                       SUM(foods.Carbohydrates) AS carbs
                FROM meals
                LEFT JOIN foods ON meals.food = foods.food
                WHERE meals.user_id = %s
                  AND YEARWEEK(meals.date, 1) = YEARWEEK(CURDATE(), 1)
                GROUP BY DATE(meals.date)
            """
            cursor.execute(query, (user_id,))
        else:
            return jsonify({"error": "Invalid view type."}), 400

        data = cursor.fetchall()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        connection.close()

@app.route('/daily_summary_view', methods=['GET'])
def daily_summary_view():
    """
    - GET: 顯示每日總結頁面 (daily_summary.html)
    """
    if 'username' not in session:
        flash("Please log in first.")
        return redirect(url_for('database_login'))
    return render_template('suggestion.html')

# ---------------------------------------------------------
# 主程式入口
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

