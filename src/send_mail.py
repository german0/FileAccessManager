import smtplib
import config 
import string
import random
import json
import os
import time
import webbrowser

def redirect(userid):
    url = 'http://localhost:5000/register?uid={}'.format(str(userid))
    webbrowser.open(url)

def add_file_access(uid,path):
    fd = open("users.reg","r")
    data = json.load(fd)
    contact = data[str(uid)]
    fd.close()
    fd = open("activation.json")
    users = json.load(fd)
    info = users[str(contact)]
    fd.close()
    files = info["files"]
    files.append(path)
    info["files"] = files
    users[str(contact)] = info
    fd = open("activation.json","w")
    users.update(users)
    json.dump(users,fd)
    fd.close()

def check_code(user, passwd):
    fd = open("activation.json")
    data = json.load(fd)
    fd.close()
    info = data[str(user)]
    time_now = time.time()
    time_diff = int(time_now) - info["timestamp"]
    print(time_diff)
    if info["code"] == str(passwd) and time_diff <= 30:
        files = info["files"]
        files.append(str(info["tmp"]))
        info["files"] = files
        info["code"] = None
        info["timestamp"] = 0
        info["tmp"] = ''
        info["success"] = True
        data[str(user)] = info
        data.update(data)
        fd = open("activation.json","w")
        json.dump(data,fd)
        fd.close()
        return 0
    if (info["code"] != str(passwd)):
        return 1
    if (time_diff > 30):
        return 2
    return False

def update_user_reg(userid,contact):
    fd = open("users.reg")
    data = json.load(fd)
    fd.close()
    fd = open("users.reg","w")
    data[userid] = contact
    data.update(data)
    json.dump(data,fd)
    fd.close()

def register(uid,user,passwd):
    if os.path.exists("activation.json"):
        fd = open("activation.json")
        data = json.load(fd)
        fd.close()
        if user in data:
            return False
        fd = open("activation.json","w")
        info = {}
        info["passwd"] = passwd
        info["code"] = None
        info["success"] = False
        info["timestamp"] = 0
        info["files"] = []
        info["tmp"] = ""
        data[user] = info
        data.update(data)
        json.dump(data,fd)
        fd.close()
    return True

def is_user_valid(user):
    fd = open("activation.json","r")
    print(fd)
    data = json.load(fd)
    fd.close()
    if user not in data:
        return False
    return True

def is_pw_valid(user,code):
    fd = open("activation.json","r")
    data = json.load(fd)
    info = data[user]
    
    if info["passwd"] == code:
        return True
    return False

def is_valid(user,code):
    print(user,code)
    if (is_user_valid(user)):
        if (is_pw_valid(user,code)):
            return True
    return False

def start_log():
    fd = open("activation.json","w")
    info = {}
    info["passwd"] = "admin"
    info["files"] = ['*']
    info["code"] = None
    info["tmp"] = ""
    info["timestamp"] = 0
    info["success"] = False
    data = {}
    data[config.EMAIL_ADDRESS] = info 
    json.dump(data,fd)
    fd.close()

def code_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def write_json(dest,msg):
    #if file already exists, update json
    if os.path.exists("activation.json"):
        fd = open("activation.json")
        data = json.load(fd)
        fd.close()
        fd = open("activation.json","w")
        data = {}
        register_info = {} 
        register_info["code"] = msg
        register_info["success"] = False
        data[dest] = register_info
        data.update(data)
        json.dump(data,fd)
        fd.close()
    #if not create file and add credentials
    else:
        fd = open("activation.json", "w")
        data = {}
        register_info = {}
        register_info["code"] = msg
        register_info["success"] = False
        data[dest] = register_info
        json.dump(data,fd)
        fd.close()

def send_email(dest,path):
    msg = code_generator()
    #write_json(dest,msg)
    subject = "Activation code"
    fd = open("activation.json")
    data = json.load(fd)
    fd.close()
    info = data[str(dest)]
    time_now = time.time()
    time_diff = int(time_now) - int(info["timestamp"])

    if (time_diff >= 30):
        try:
            #send email
            '''server = smtplib.SMTP('smtp.gmail.com:587')
            server.ehlo()
            server.starttls()
            server.login(config.EMAIL_ADDRESS,config.PASSWORD)
            message = 'Subject: {}\n\nYour activation code is {}\nHead to http://localhost:5000/ and login.'.format(subject,msg)
            server.sendmail(dest,dest, message)
            server.quit()
            print("Success: Email sent!")'''
    
            #update timestamp
            fd = open("activation.json","w")
            info["timestamp"] = int(time_now)
            info["code"] = msg
            info["tmp"] = str(path)
            data[str(dest)] = info
            data.update(data)
            json.dump(data,fd)
            fd.close()
        except:
            print("Email failed to send.")

#dest = config.EMAIL_ADDRESS
#code = code_generator()
#write_json(dest,code)
#send_email("andre","/root")
#is_valid("andre","1")
#check_code("andre","KZDQKU")