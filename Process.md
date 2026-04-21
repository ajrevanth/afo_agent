Architecture
- backend
- frontend
- deployment
- genai api creds
- db design & set up
- gmail api set up
- langgraapg design
- api design
- communication and security

Gmail set up
1. Create a Google Cloud Project
Go to the Google Cloud Console.
Click Select a project at the top and choose New Project.
Give it a name (e.g., "My Gmail App") and click Create. 
EmailEngine Email API
EmailEngine Email API
 +3
2. Enable the Gmail API
In the left sidebar, go to APIs & Services > Library.
Search for "Gmail API" and click on it.
Click the Enable button. 
Mailtrap
Mailtrap
 +3
3. Configure the OAuth Consent Screen 
Go back to the sidebar and select APIs & Services > OAuth consent screen.
Choose User Type:
Internal: Only for users within your own Google Workspace organization.
External: For any @gmail.com user (choose this for personal use).
Fill in required fields like App name, User support email, and Developer contact info, then click Save and Continue.
Add Scopes: Click Add or Remove Scopes and select https://www.googleapis.com/auth/gmail.readonly (to read mail) or https://www.googleapis.com/auth/gmail.send (to send mail).
Test Users: If your app is "External," add your own Gmail address as a Test User so you can authorize it before verification. 
Google for Developers
Google for Developers
 +7
4. Create Credentials
Go to the Credentials tab on the left.
Click Create Credentials > OAuth client ID.
Select Application type:
Desktop App: Best for local scripts (Python, Node.js).
Web Application: For websites.
Click Create, then click the Download JSON icon next to your new Client ID.
Rename this file to credentials.json and keep it in your project folder. 
Mailtrap
Mailtrap
 +6
5. Authenticate and Get Your Token
The first time you run a script using these credentials, a browser window will open asking you to Allow access. 
Mailtrap
Mailtrap
 +1
Note: You might see a "Google hasn't verified this app" warning. Since it's your own app, click Advanced > Go to [App Name] (unsafe) to proceed.
Once authorized, a token.json file will be created in your directory. This file is your "key" for future API calls