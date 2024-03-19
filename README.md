# My Clipboard

#### Video Demo: https://youtu.be/K3fGskjN7TQ

#### Description: My Clipboard allows you to copy text seamlessly between any device.

#### Pitch:

Companies such as Apple allow you to copy text seamlessly between devices made by them - for example Macs and iPhones - but not between devices outside of the ecosystem. This app is for that use case.

You can set and read your cloud synced clipboard contents using the iPhone/iPad app, the Android app, the Google Chrome extension, or the website.

#### Projects:

I made a website using flask, a Chrome extension using javascript, and a react native app for iOS and Android phones.
The react native app was the hardest to make since I had to learn javascript more fully, react, react native, and deploying to app stores.
However, the flask server is the most complex, and provides responses and validates the API calls from the clients.

##### The website (clipboard-server):

I made the server for the website and the api endpoints for the apps in flask. It is running on a google app engine F1 instance.

The website allows for a user to signup for an account. The user must then validate their email in a link sent to their email.
I send that email using twillio sendex. Additionally, I have rate limiting by ip configured to prevent bruteforce attacks.

The website index page (when signed in) provides a form to paste clipboard contents, which are then synced to the cloud. I use google firestore becuase of the generous free tier limits. The website index page also shows the pasted contents from the cloud.

Only the most recent clipboard contents are stored as a privacy and security measure. The contents are automatically deleted after 3 days using a Google Cloud Function that runs with when a Google Cloud scheduler posts a Pub/Sub.
I also backup the users database that way. (Not the clipboards database, which is never backed up).

Users may delete their accounts, change their password, or even turn on dark mode in account settings.

The website also functions as a sort of oauth for signing in with the chrome extension.

##### The chrome extension (clipboard-chrome):

The chrome extension preforms the same functionality as the website. It just makes it easier to use the service by providing the form as a popup. It automaticlaly pastes user clipboard contents in when the popup is clicked. T

he extension uses ajax to update by making requests to the server with a token that is aquired during the sign-in.

The first time the user clicks on the extension, they are redirected to the website which presents a login form that on success redirects to the chrome extension with the token as a URL query parameter.

##### The mobile app (clipboard-mobile):

I made an app using react native to make it easier to copy and paste text from your phone.
I had to learn react and react native, so this project took the most time.
It is on the app store and google play store. See https://myclipboard.io/download/ for the links.

The user is presented with a login screen when they first open the app. I was going to use deep linking to have a website sign-in similar to the chrome extension, but after learing about the security flaws of deep linking sensitive info, I decided to make a login using react native.

On sigin, the homepage looks similar to the website. I tried to make it as similar as I could. The app saves an API token in storage, and the user can log out anytime.
