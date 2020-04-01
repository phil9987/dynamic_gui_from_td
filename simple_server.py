from flask import Flask, send_from_directory
app = Flask(__name__)

@app.route('/robotarmthing')
def robot_arm_thing():
    return send_from_directory('.', 'robotArmThing.html')

@app.route('/sparql-extension/calendar')
def hello_world():
    return send_from_directory('.', 'calendar.txt')