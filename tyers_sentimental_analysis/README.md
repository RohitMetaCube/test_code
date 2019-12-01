<b>Step 1:</b> Get the source code repository form github.<br>
<b>2.1:</b> <i>git clone https://github.com/RohitMetaCube/test_code.git</i><br>

I am assuming that the directory of the source code will be called <i>$REPOSITORY_HOME</i><br>

<b>Step 2:</b> Installing pip (Version 8.1.1) (I have done it through apt-get other package managers can also be used). Not i have installed sci-py library here manually before installing scikit-learn in the requirements.txt file.<br>
<b>2.1:</b> <i>sudo apt-get install python-pip python-dev gfortran libatlas-base-dev build-essential libxml2-dev libxslt1-dev zlib1g-dev python-scipy python-enchant</i><br>
<b>2.2:</b> <i>sudo pip install --upgrade pip</i><br> 
<b>2.3:</b> <i>sudo pip install --upgrade virtualenv</i><br>

Test it using <i>pip -V</i> which shows the version of the pip installation<br>

<b>Step 3:</b> Installing pip-tools for dependency management<br>
<b>3.1:</b> <i>sudo pip install pip-tools</i><br>

<b>Step 4:</b> Downgrade PIP to 8.1.1<br>
<b>4.1:</b> <i>sudo pip install --upgrade pip==8.1.1</i><br> 

<b>Step 5:</b> Installing dependencies for different Components<br><br>
<b>5.1: For tyers sentimental model </b><br>
<i>cd $REPOSITORY_HOME/tyers_sentimental_analysis</i><br>

<b>5.2:</b> <i>sudo pip install -r requirements.in</i><br>

<b>Step 6:</b> Downloading nltk and model data for norm-job API. I am downloading all the data present in nltk and not specific files. Storing the data in /usr/local/share so that it's globally available and does not hinder starting the normalization server through upstart.<br>
<b>6.1:</b> <i>sudo python -m nltk.downloader -d /usr/local/share/nltk_data -e all</i><br>
<i>-e</i> flag ensures that nltk downloader doesn't stop downloading the packages because of any error i.e. if there are errors in downloading any particular package it would proceed with next package.<br>
<b>6.2:</b> Ask Vladimir to provide the <i>model</i> tarball and unpack it into <i>dataNormalization/python/LayTitleMappingProcesses/model/</i>. It is configurable and can be modified in lib/commons.py file using MODEL_PATH variable<br>

<b>Step 7:</b> Model building and testing<br>
<i>python -u build_model.py</i><br>
