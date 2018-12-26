import send_mail
# import the Flask class from the flask module
from flask import Flask, render_template, redirect, url_for, request

# create the application object
app = Flask(__name__)


@app.route('/')
def welcome():
    return render_template('welcome.html')  # render a template

# route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        passwd = request.form['password']
        if send_mail.is_valid(username,passwd):
            return redirect("http://localhost:5000/auth?user="+str(username))

        error = 'Invalid Credentials. Please try again.'  
    return render_template('login.html', error=error)

# route for handling the register page logic
@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    uid = request.args.get('uid')
    if request.method == 'POST':
        username = request.form['username']
        passwd = request.form['password']
        if send_mail.register(uid,username,passwd):
            send_mail.update_user_reg(uid,username)
            return redirect(url_for('welcome'))

        error = 'User already registered. Please try again.'  
    return render_template('register.html', error=error)

# route for handling the register page logic
@app.route('/auth', methods=['GET', 'POST'])
def auth():
    error = None
    if request.method == 'POST':
        passwd = request.form['password']
        user = request.args.get('user')
        switch = send_mail.check_code(user,passwd)
        if switch == 0:
            return redirect(url_for('welcome'))
        elif (switch == 1):
            error = 'Invalid Activation Code. Please try again.'
        else:
            error = 'Timeout. Please generate another activation code.'  
    return render_template('activation.html', error=error)

# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)