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
  "usersNameList": ["Rohit Kumar", "Piyush Beli"]
}</i>
<br>
<br>

<h4>MARK SPECIAL ENTRY API</h4><br><br>

<b>URL:</b> http://localhost:8080/timeSheet/mark_entry
<br>
<b>Request 1 <LEAVE>:</b><br>
<i>{
  "markingSheetIndex":1,
  "markingType":"leave",
  "markingDates":[5,6],
  "spreadsheetID":"1_dG5DgaPM0VTZCQedo9EyjJFUpSQwGuoBBHr19C62XA"
}</i><br><br>

<b>Request 2 <HOLIDAY>:</b><br>
<i>{
  "markingSheetIndex":1,
  "markingType":"holiday",
  "markingDates":[7,8,9],
  "spreadsheetID":"1_dG5DgaPM0VTZCQedo9EyjJFUpSQwGuoBBHr19C62XA"
}</i><br><br>

<b>Request 3 <WORKING>:</b><br>
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