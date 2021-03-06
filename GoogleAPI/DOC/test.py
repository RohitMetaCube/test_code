from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
gauth.LocalWebserverAuth()

'''
DISPLAY ::
Your browser has been opened to visit:
()
    https://accounts.google.com/o/oauth2/auth?scope=https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fdrive&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2F&response_type=code&client_id=918911773602-equaa13k3hgum8mk6oquomm99mgiodls.apps.googleusercontent.com&access_type=offline
()
Created new window in existing browser session.
Authentication successful.
'''

drive = GoogleDrive(gauth)
file1 = drive.CreateFile()
file1 = drive.CreateFile({'title': 'Hello.txt'})  # Create GoogleDriveFile instance with title 'Hello.txt'.
file1.SetContentString('Hello World!') # Set content of the file from given string.
file1.Upload()
print('Created file %s with mimeType %s' % (file1['title'],file1['mimeType']))
'''
RESULT :: Created file Hello.txt with mimeType text/plain
'''

file1.SetContentString('Again Hello World!') # Set content of the file from given string.
file1.Upload()
file1.SetContentString('Hello World\nAgain Hello World!') # Set content of the file from given string.
file1.Upload()
file1.Delete()
file1 = drive.CreateFile({'title': 'Hello.xlsx'})  # Create GoogleDriveFile instance with title 'Hello.txt'.
file1.SetContentString(['Hello World','Again Hello World!'],['new line data','row 2 column 2']) # Set content of the file from given string.
file1.SetContentString('Hello World \t Again Hello World!','new line data \t row 2 column 2') # Set content of the file from given string.
file1.SetContentString('Hello World \t Again Hello World! \n new line data \t row 2 column 2') # Set content of the file from given string.
file1.Upload()
file1.Delete()

