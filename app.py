# Store this code in 'app.py' file

from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import yfinance as yf


app = Flask(__name__)


app.secret_key = 'your secret key'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mySQL@2022'
app.config['MYSQL_DB'] = 'stockit'

mysql = MySQL(app)

@app.route("/")
def index():
	return render_template('root.html')

@app.route('/login', methods =['GET', 'POST'])
def login():
	msg = ''
	if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
		username = request.form['username']
		password = request.form['password']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE username = % s AND password = % s', (username, password, ))
		account = cursor.fetchone()
		if account:
			session['loggedin'] = True
			session['username'] = account['username']
			session['name'] = account['name']
			msg = 'Logged in successfully !'
			return render_template('profile.html')
		else:
			msg = 'Incorrect username / password !'
			mysql.connection.rollback()
	return render_template('login.html', msg = msg)

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('username', None)
	return redirect(url_for('login'))

@app.route('/register', methods =['GET', 'POST'])
def register():
	msg = ''
	if request.method == 'POST' and 'name' in request.form and 'password' in request.form and 'email' in request.form and 'username' in request.form :
		name = request.form['name']
		username = request.form['username']
		password = request.form['password']
		email = request.form['email']

		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute('SELECT * FROM user WHERE username = % s', (username, ))
		account = cursor.fetchone()
		if account:
			msg = 'Account already exists !'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address !'
		elif not re.match(r'[A-Za-z0-9]+', username):
			msg = 'Username must contain only characters and numbers !'
		elif not username or not password or not email:
			msg = 'Please fill out the form !'
		else:
			cursor.execute('INSERT INTO user VALUES (%s, % s, % s, % s, 500000, 0 )', ( username, name, password, email ))
			mysql.connection.commit()
			msg = 'You have successfully registered !'
			session['loggedin'] = True
			session['username'] = username
			cursor.execute('INSERT INTO user_transactions values(%s,%s,%s,%s,%s',(username,0,0,0,0))
			mysql.connection.commit()
			return render_template('profile.html')
	elif request.method == 'POST':
		msg = 'Please fill out the form !'
		mysql.connection.rollback()
	return render_template('register.html', msg = msg)

@app.route("/stocks")
def Stocklist():
    stock =  ['SAPPHIRE.NS','DATAPATTNS.NS','INDIAMART.NS','NESTLEIND.NS','IRCTC.NS','BSOFT.NS','BATAINDIA.NS','INDHOTEL.NS','POLYCAB.NS','IRFC.NS','HAVELLS.NS','JETAIRWAYS.NS','WHIRLPOOL.NS','IOB.NS','RELIANCE.NS','ONGC.NS','CIPLA.NS','HDFCLIFE.NS','BRITANNIA.NS','WIPRO.NS'] 

    for id in stock:
        data = yf.download(tickers=id, period='1d', interval='30m')
        r = data.shape[0]
        row = data.iloc[-1]
        row2 = data.iloc[0]
        
        op = round(float(row[0]),3)
        hg = round(float(row[1]),3)
        lw = round(float(row[2]),3)
        cl = round(float(row[3]),3)
        vl = round(float(row[5]),3)
        pr = round(float(row2[3]),3)
        mycursor = mysql.connection.cursor()
    #insert_data_stock = (id, op, hg, lw, cl, vl)
        update_data_stock = (op, hg, lw, cl, vl, pr, id)

    #mycursor.execute("INSERT INTO stockPrice values (%s, %s, %s, %s, %s, %s) ", insert_data_stock)
        mycursor.execute("UPDATE STOCKPRICE"
                   " SET open_val = %s, high_val = %s, low_val = %s, close_val = %s, volume = %s, prev_day = %s where id = %s", update_data_stock)

        mysql.connection.commit()

    cur = mysql.connection.cursor()
    result = cur.execute("SELECT *, (CLOSE_VAL - PREV_DAY) * 0.01 AS PROFIT FROM STOCKPRICE;")
    if result > 0:
        stockList = cur.fetchall()
        return render_template('Stocks.html',stockList = stockList)

@app.route("/movers")
def moverslist():
    cur = mysql.connection.cursor()
    result = cur.execute("SELECT * FROM STOCKPRICE ORDER BY VOLUME DESC LIMIT 5")
    if result > 0:
        moversList = cur.fetchall()
        return render_template('movers.html',moversList = moversList)

@app.route("/gainers")
def gainerlist():
    cur = mysql.connection.cursor()
	#("CREATE VIEW GAINERS AS SELECT ID, (CLOSE_VAL-PREV_DAY)*0.01 AS PROFIT FROM STOCKPRICE ORDER BY LOSS LIMIT 5")
    result = cur.execute("SELECT *, (CLOSE_VAL - PREV_DAY) * 0.01 AS PROFIT FROM STOCKPRICE ORDER BY PROFIT DESC LIMIT 5;")
    if result > 0:
        gainersList = cur.fetchall()
        return render_template('gainers.html',gainersList = gainersList)

@app.route("/losers")
def loserlist():
    cur = mysql.connection.cursor()
	#("CREATE VIEW LOSERS AS SELECT ID, (CLOSE_VAL-PREV_DAY)*0.01 AS LOSS FROM STOCKPRICE ORDER BY PROFIT LIMIT 5")
    result = cur.execute("SELECT *, (CLOSE_VAL - PREV_DAY) * 0.01 AS PROFIT FROM STOCKPRICE ORDER BY PROFIT LIMIT 5")
    if result > 0:
        losersList = cur.fetchall()
        return render_template('losers.html',losersList = losersList)

@app.route('/profile')
def profile():
	cur = mysql.connection.cursor()
	cur.execute("SELECT * from user where username=%s",(session['username'],))
	amount = cur.fetchone()
	cur.execute("SELECT * from user_transactions where username=%s",(session['username'],))
	transactions = cur.fetchone()
	cur.execute("SELECT CURRENT_DATE()")
	date=cur.fetchone()
	cur.execute("SELECT CURRENT_TIME()")
	time=cur.fetchone()
	cur.execute("SELECT DAYNAME(CURRENT_DATE())")
	day=cur.fetchone()
	return render_template('profile.html', amount=amount, transactions=transactions,date=date, time=time, day=day)

@app.route('/stockinfo/<variable>')
def stockinfo(variable):
	cursor = mysql.connection.cursor()
	cursor.execute('SELECT * FROM stockprice WHERE id = % s', (variable, ))
	stockdetails = cursor.fetchone()
	session['ticker'] = stockdetails[0]
	return render_template('stockinfo.html', stockdetails=stockdetails)

@app.route('/buy', methods =['GET', 'POST'])
def buy():
	stockid = session['ticker']
	if request.method == 'POST' and 'quantity' in request.form :
		qty = request.form['quantity']
		cursor = mysql.connection.cursor()
		cursor.execute('SELECT open_val FROM stockprice WHERE id = % s',(stockid, ))
		stockprice = cursor.fetchone()
		tot_price = (float(stockprice[0])) * (int(qty))
		cursor.execute('SELECT amount,amount_inv FROM user WHERE username = % s', (session['username'],))
		useramt = cursor.fetchone()
		cursor.execute('select * from portfolio where stockid = %s and userid = %s',(stockid,session['username']))
		exist = cursor.fetchone()
		amt = (float(useramt[0]))

		if (amt < tot_price) :
			return render_template('insufficient.html')
		
		elif exist is not None :
			tot_qty = (int(qty))+ (int(exist[2]))
			current_price = (float(exist[2]))*(float(exist[3]))
			new_avg = (tot_price + current_price) / tot_qty
			update_portfolio_data = (tot_qty, new_avg, session['username'],stockid)
			cursor.execute("update portfolio set quantity = %s, amountspent = %s where userid = %s and stockid = %s",update_portfolio_data)
			mysql.connection.commit()
			amt_inv = tot_price + (float(useramt[1]))
			amt = amt - tot_price
			cursor.execute("UPDATE USER SET AMOUNT =%s, AMOUNT_INV = %s where username = %s",(amt,amt_inv,session['username']))
			mysql.connection.commit()
			return "success"

		else:
			amt = amt - tot_price
			cursor = mysql.connection.cursor()
			insert_portfolio_data = (session['username'],stockid,qty,stockprice[0])
			cursor.execute("INSERT into portfolio values(%s,%s,%s,%s)",insert_portfolio_data)
			mysql.connection.commit()
			amt_inv = tot_price + (float(useramt[1]))
			cursor.execute("UPDATE USER SET AMOUNT =%s, AMOUNT_INV = %s where username = %s",(amt,amt_inv,session['username']))
			mysql.connection.commit()
			return "success"

	return render_template('buy.html')

@app.route('/sell', methods =['GET', 'POST'])
def sell():
	stockid = session['ticker']
	if request.method == 'POST' and 'quantity' in request.form :
		new_qty = request.form['quantity']
		cursor = mysql.connection.cursor()
		cursor.execute('SELECT * FROM portfolio WHERE stockid = % s and userid = %s',(stockid, session['username'] ))
		exist = cursor.fetchone()
		if exist is None:
			return "You do not own this stock"
		if int(new_qty) > int(exist[2]):
			return "Check the quantity"
		else :
			qty = int(exist[2])
			new_qty = int(qty) - int(new_qty) #decreasing stock qty
			if (new_qty == 0):
				cursor.execute('DELETE FROM portfolio where stockid=%s and userid=%s',(stockid,session['username']))
				mysql.connection.commit()
			else :
				cursor.execute('UPDATE portfolio set quantity=%s where stockid=%s and userid=%s',(new_qty,stockid,session['username'],))
				mysql.connection.commit()

			cursor.execute('SELECT * FROM stockprice where id=%s',(stockid,))
			res = cursor.fetchone()
			curr_price = float(res[1])
			new_amt = int(new_qty) * curr_price
			new_amt_inv = int(new_qty) * float(exist[3])
			cursor.execute('UPDATE user set amount=amount+%s, amount_inv=amount_inv-%s where username=%s ',(new_amt,new_amt_inv,session['username'],))
			mysql.connection.commit()
			if(new_amt > new_amt_inv): #positive transactions
				pr = new_amt - new_amt_inv
				cursor.execute("update user_transactions set profit = profit+%s, positive=positive+1 where username=%s",(pr,session['username'],))
				mysql.connection.commit()
			else:
				ls = new_amt - new_amt_inv
				cursor.execute("update user_transactions set loss = loss-%s, negative=negative+1 where username=%s",(ls,session['username'],))
				mysql.connection.commit()
			return "success-sell"
	return render_template('sell.html')
		
@app.route('/portfolio')
def portfolio():
	cursor = mysql.connection.cursor()
	cursor.execute('SELECT * FROM portfolio where userid=%s',(session['username'],))
	portfoliodata = cursor.fetchall()
	cursor.execute('SELECT * FROM user where username=%s',(session['username'],))
	userdata = cursor.fetchone()
	cursor.execute('SELECT id, quantity, amountspent, amountspent*quantity, open_val, quantity*open_val from stockprice inner join portfolio where(userid=%s and portfolio.stockid=stockprice.id)',(session['username'],))
	stockdata = cursor.fetchall()
	cursor.execute('SELECT SUM(quantity*open_val) as new_price from portfolio inner join stockprice where (portfolio.stockid=stockprice.id and portfolio.userid=%s)',(session['username'],))
	curr_holding = cursor.fetchone()
	return render_template('portfolio.html', portfoliodata=portfoliodata, stockdata = stockdata, userdata=userdata, curr_holding=curr_holding)

if __name__ == "__main__":
    app.run(debug=True)