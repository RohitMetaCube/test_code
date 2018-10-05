<H2>SAMPLE REQUEST AND RESPONSES</H2>
<br>
<br>
<h4>CREATE API</h4><br>
<br>
<b>URL:</b> http://localhost:8080/timeSheet/create
<br>
<b>Request:</b>
<i>{
  "month":11,
  "year":2018,
  "projectName":"Zippia",
  "adminEmailAddr": "rohitkumar1800@gmail.com",
  "usersList": [{
    			 	"userName":"Rohit Kumar", 
                 	"userEmailAddr":"rohit.kumar@metacube.com",
                 	"userID":"E15/0642"
                }, {
                  	"userName":"Piyush Beli",
                  	"userEmailAddr":"piyush.beli@metacube.com",
                    "userID":"E14/0541"
  }]
}</i>
<br>
<b>Response:</b><br>
<i>{
"processingTime": 46.750060081481934,
"spreadsheetID": "1kZ0DMsmCQnZ6n3Y4_BnFtPLk4klvv94dLaImlc690Lo"
}</i><br><br>


<h4>MARK SPECIAL ENTRY API</h4><br><br>

<b>URL:</b> http://localhost:8080/timeSheet/mark_entry
<br>
<b>Request 1 (LEAVE):</b><br>
<i>{
  "markingSheetIndex":1,
  "markingType":"leave",
  "markingDates":[5,6],
  "spreadsheetID":"1_dG5DgaPM0VTZCQedo9EyjJFUpSQwGuoBBHr19C62XA"
}</i><br><br>

<b>Request 2 (HOLIDAY):</b><br>
<i>{
  "markingSheetIndex":1,
  "markingType":"holiday",
  "markingDates":[7,8,9],
  "spreadsheetID":"1_dG5DgaPM0VTZCQedo9EyjJFUpSQwGuoBBHr19C62XA"
}</i><br><br>

<b>Request 3 (WORKING):</b><br>
<i>{
  "markingSheetIndex":1,
  "markingType":"working",
  "markingDates":[3],
  "spreadsheetID":"1_dG5DgaPM0VTZCQedo9EyjJFUpSQwGuoBBHr19C62XA"
}</i><br><br>

<b>Response:</b><br>
<i>{
  "processingTime": 0.841331958770752, 
  "spreadsheetID": "1_dG5DgaPM0VTZCQedo9EyjJFUpSQwGuoBBHr19C62XA", 
  "Message": {"spreadsheetId": "1_dG5DgaPM0VTZCQedo9EyjJFUpSQwGuoBBHr19C62XA", "replies": [{}]}, 
  "status": true
}</i><br><br>



<h3>Some Sample Requests for Leave with Distinct Parameters</h3>
<br><br>
<b>If Current Month</b><br>
<i>{
  "adminEmailAddr": "rohitkumar1800@gmail.com",
  "markingType":"leave",
  "markingDates":[5,6],
  "markingSheetName":"Rohit Kumar",
}</i><br><br>


<b>If Specified Month</b><br>
<i>{
  "month":11,
  "adminEmailAddr": "rohitkumar1800@gmail.com",
  "markingType":"leave",
  "markingDates":[5,6],
  "markingSheetName":"Rohit Kumar",
}</i><br><br>

<b>If An Admin have multiple project sheets then project name is mendatory to fetch exact spreadsheetID</b><br>
<i>{
  "adminEmailAddr": "rohitkumar1800@gmail.com",
  "projectName":"Zippia"
  "markingType":"leave",
  "markingDates":[5,6],
  "markingSheetName":"Rohit Kumar",
}</i><br><br>

<b>If Know SpreadsheetID</b><br>
<i>{
  "spreadsheetID": "1kZ0DMsmCQnZ6n3Y4_BnFtPLk4klvv94dLaImlc690Lo",
  "markingType":"leave",
  "markingDates":[5,6],
  "markingSheetName":"Rohit Kumar",
}</i><br><br>


<b>If Know sheetIndex</b><br>
<i>{
  "spreadsheetID": "1kZ0DMsmCQnZ6n3Y4_BnFtPLk4klvv94dLaImlc690Lo",
  "markingType":"leave",
  "markingDates":[5,6],
  "markingSheetIndex":1,
}</i>




