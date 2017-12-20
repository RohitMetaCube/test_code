<b>Step 1:</b> Install the required softwares.<br>
1. Python 2.7<br>
<br>

<b>Step 2:</b> Get the source code repository form github.<br>
<b>2.1:</b> <i>git clone https://github.com/RohitMetaCube/test_code.git</i><br><br>


I am assuming that the directory of the source code will be called <i>$TEST_HOME</i><br><br>

<b>Step 3:</b> Installing pip (Version 8.1.1) (I have done it through apt-get other package managers can also be used)<br>
<b>3.1:</b> <i>sudo apt-get install python-pip python-dev gfortran libatlas-base-dev build-essential libxml2-dev libxslt1-dev zlib1g-dev</i><br>
<b>3.2:</b> <i>sudo pip install --upgrade pip</i><br> 
<b>3.3:</b> <i>sudo pip install --upgrade virtualenv</i><br><br>

Test it using <i>pip -V</i> which shows the version of the pip installation<br><br>

<b>Step 4:</b> Installing pip-tools for dependency management<br>
<b>4.1:</b> <i>sudo pip install pip-tools</i><br><br>

<b>Step 5:</b> Downgrade PIP to 8.1.1<br>
<b>5.1:</b> <i>sudo pip install --upgrade pip==8.1.1</i><br><br> 

<b>Step 6:</b> Install test specific requirements<br>

<b>6.1:</b><i>cd $TEST_HOME/NashVenture</i><br>

<b>6.2:</b> <i>sudo pip install -r requirements.in</i><br><br>



<b>Step 7:</b> Run Specific python files individually <br>
1 - "python -u random_number_generator.py"
2 - "python -u read_file_and_change_grams.py"