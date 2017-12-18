# Demo OAuth Client for Freelancer.com API

The Identity Demo Application is a demonstration web application writting in Python.
It authenticates against accounts.freelancer-sandbox.com to allow a user to post projects 
via the Freelancer.com API sandbox.

See https://developers.freelancer.com/ to learn more.


## Getting Started ##

Create a virtualenv for your application

```
$ virtualenv freelancer-oauth-demo-app
source freelancer-oauth-demo-app/bin/activate
```

### Get the code ###
```
$ git clone https://github.com/freelancer/freelancer-oauth-demo-app.git
$ pip install -e .
```

### Setting up your client ###
In order to run your server, you need to register a client application with 
[accounts.freelancer-sandbox.com](https://account.freelancer-sandbox.com).

For the purposes of testing, this code runs a server on localhost, and therefore uses a 
redirect_uri of http://127.0.0.1:8080/authorized. If you want to use this behaviour, you must register your 
client application with this redirect_uri. If you use another redirect_uri when 
registering your application, ensure that the variable 'client_redirect' in client.py is set 
to your redirect_uri. Also set the variable client_name to the name you choose for your application.

Once you have registered the application, you will be given a client_id and a client_secret. Set the variables of the same name defined in client.py to be these two values.

### Running the server ###

```
$ cd freelancer_oauth_demo_app
$ python client.py
 * Running on http://0.0.0.0:8080/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger pin code: 184-916-923
```

Congratulations, you now have an OAuth client application running on your machine!

Navigate to http://127.0.0.1:8080/ to view your OAuth client application.
