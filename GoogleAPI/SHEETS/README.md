<H1>HOW TO LAUNCH TIMESHEET API</H1><br><br>

<b>Step 1:</b> <i>Upgrade apt-get Module</i><br>
<i>sudo apt-get upgrade</i><br><br>

<b>Step 2:</b> <i>Install Git</i><br>
<i>sudo apt-get install git</i><br><br>

<b>Step 3:</b> <i>Install Python  2.7</i><br>
<i></i><br><br>

<b>Step 4:</b> <i>Install Python-pip</i><br>
<i>sudo apt-get install python-pip</i><br><br>

<b>Step 5:</b> <i>Install MongoDB</i><br>
<i>sudo apt-get install mongodb</i><br><br>

<b>Step 6:</b> <i>Clone from  Git</i><br>
<i>git clone https://github.com/RohitMetaCube/test_code.git</i>
<br><br>

<b>Step 7:</b> <i>Move in Google Sheets Dir</i><br>
<i>cd ~TIMESHEET_HOME/test_code/GoogleAPI/SHEETS/</i><br><br>

<b>Step 8:</b> <i>Install Internal Dependencies</i><br>
<i>sudo pip install -r requirements.in</i><br><br>

<b>Step 9:</b> <i>Start Timesheet Server</i><br>
<i>sudo python time_sheet_api.py --noauth_local_webserver</i><br><br>

<b>Step 10:</b> <i>Test Server via heartbeat cheking</i><br>
<i>http://localhost:8080/heartbeat</i> <br><br>
<br>

<H2>YOU CAN USE OUR TIMESHEET API:</H2><br><br>
<b>Heartbeat Request:</b> <b><i>GET/POST</i></b> http://35.190.168.196:8080/heartbeat <br>
<b>Create Request:</b> <i><b>POST</i></b> http://35.190.168.196:8080/timeSheet/create <br>
<b>Mark Entry Request:</b> <i><b>POST</i></b> http://35.190.168.196:8080/timeSheet/mark_entry <br>
<br>
<br>


<H2>SAMPLE REQUEST AND RESPONSES</H2>
<br>
<br>
<h4>ADD USER BY ADMIN(required authenticated Admin account)</h4><br>
<br>
<b>URL:</b> http://localhost:5000/webhook
<br>
<b>Request:</b>
<i>{
  	"queryResult":{"intent":{"displayName":"Add User"}},
  	"parameters":{
        "month":12,
        "year":2018,
        "projectName":"Xxxxx",
        "adminName":"Xxxxx Xxxxx",
        "adminEmailAddr": "xxxxxxxxx@gmail.com",          
        "userName":"Rohit Kumar", 
        "userEmailAddr":"xxxx.xxx@xxxxxxxx.xxxx",
        "userID":"Xdd/dddd"
	}
}</i>
<br>
<b>Response:</b><br>
<i>{
"fulfillmentText": "Cheers! User added successfully."
}</i><br><br>

<h4>REMOVE USER BY ADMIN(required authenticated Admin account)</h4><br>
<br>
<b>URL:</b> http://localhost:5000/webhook
<br>
<b>Request:</b>
<i>{
  	"queryResult":{"intent":{"displayName":"Remove User"}},
  	"parameters":{
        "month":12,
        "year":2018,
        "projectName":"Xxxxx",
        "adminName":"Xxxxx Xxxxx",
        "adminEmailAddr": "xxxxxxxxx@gmail.com",          
        "userName":"Rohit Kumar", 
        "userEmailAddr":"xxxx.xxx@xxxxxxxx.xxxx",
        "userID":"Xdd/dddd"
	}
}</i>
<br>
<b>Response:</b><br>
<i>{
"fulfillmentText": "Removed user with email xxxxxxxxx@xxxx.com, employeeID Xdd/dddd from project "Xxxxx""
}</i><br><br>


<h4>CREATE API</h4><br>
<br>
<b>URL:</b> http://localhost:5000/webhook
<br>
<b>Request:</b>
<i>{
  	"queryResult":{"intent":{"displayName":"Create Projects Sheets"}},
  	"parameters":{
        "month":12,
        "year":2018,
        "projects":["Xxxxxx", "Xxxxx Xxxxxx"],
        "adminName":"Xxxxxx Xxxxxxx",
        "adminEmailAddr": "xxxxxxx@xxx.xxx"
	}
}</i>
<br>
<b>Response:</b><br>
<i>{
"fulfillmentText": "Hey Buddy Say Thanks to me! Your spreadsheetIDs are projectName: Zippia, spreadsheetID: 1_L6GTbpdfsygU94lGqNIZrgEzqsNO7X1EYm5EW6MUw0"
}</i><br><br>


<h4>MARK SPECIAL ENTRY API</h4><br><br>

<b>URL:</b> http://localhost:5000/webhook
<br>
<b>Request 1 (LEAVE):</b><br>
<i>{
  "queryResult": {
    "intent": {
      "displayName": "Mark Entry"
    }
  },
  "parameters": {
    "month": 12,
    "year": 2018,
    "adminEmailAddr": "xxxxxx@xxxx.xxx",
    "markingType":"leave",
  	"markingDates":[8,12],
    "userEmailAddr":"xxxxxxxx@xxx.xxx",
    "workDetails":"Going to Home"
  }
}</i><br><br>

<b>Request 2 (HOLIDAY):</b><br>
<i>{
  "queryResult": {
    "intent": {
      "displayName": "Mark Entry"
    }
  },
  "parameters": {
    "month": 12,
    "year": 2018,
    "adminEmailAddr": "xxxxxx@xxxx.xxx",
    "markingType":"holiday",
  	"markingDates":[6,7,11],
    "userEmailAddr":"xxxxxx@xxxx.xxx",
    "workDetails":"Going to Home"
  }
}</i><br><br>

<b>Request 3 (WORKING):</b><br>
<i>{
  "queryResult": {
    "intent": {
      "displayName": "Mark Entry"
    }
  },
  "parameters": {
    "month": 12,
    "year": 2018,
    "adminEmailAddr": "xxxxxx@xxxx.xxx",
    "markingType":"working",
  	"markingDates":[3],
    "userEmailAddr":"xxxxxx@xxxx.xxx",
    "workDetails":"Going to Home"
  }
}</i><br><br>

<b>Response:</b><br>
<i>{
"processingTime": 1.96983003616333,
"spreadsheetID": "xxxxxxxxxxxxxx-xxxxXXXX-XXXDDDDDDdddd",
"Message": {
"spreadsheetId": "xxxxxxxxxxxxxx-xxxxXXXX-XXXDDDDDDdddd",
"replies": [
  {},
  {}
],
},
"status": true,
"fulfillmentText": "Congratulation!!! Your Entry marked in spreadsheetID: xxxxxxxxxxxxxx-xxxxXXXX-XXXDDDDDDdddd"
}</i><br><br>
