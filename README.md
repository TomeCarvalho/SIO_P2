## Authors

| NMEC   | Name            |
| ------ | --------------- |
| 96123  | Lucius Vinicius |
| 97939  | Tomé Carvalho   |
| 98452  | Dinis Lei       |
| 100055 | Afonso Campos   |

## Project Description



### UAP Features

The UAP was developed as a Flask application. 

It features its own web interface. 

The vault file that stores the usernames and passwords (servers_encrypted) is an entirely encrypted JSON file. **Fernet**, from the `cryptography` library, is used to implement symmetric encryption. The password is ran through the PKBDF2HMAC key derivation function, using the SHA-256 algorithm and a salt. Using the resulting key, a `Fernet` instance able to encrypt and decrypt the vault file is created.

- Vault unlocking using master password (`master`, for demonstration purposes)
- Log in to the application by clicking on the desired account
- Delete existing accounts from the vault
- Add accounts to the vault (or replace, in the case of existing ones)
- Randomly generate passwords (JavaScript function), automatically copying them to the clipboard



### Communication

The communication between UAP - Webapp follows the E-CHAP protocol, which runs the authentication N times, providing minimum information (1-bit) for each response.

The N value that was adequate was 32, because a chance of a random user get the same bit for each iteration with a wrong password is 0.5^32 ~= 2e-8 % chance. Values greater than 32 would require more time to process the requests.

#### First step

When logging in to the Web App, the client is redirected to UAP's home page through HTTP Protocols and they choose a Server (DNS)/Username combination. At that instant, the UAP sends an identifier request to the server, identifying the client through the _username_ and _token_ cookies. _username_ is a string that identifies which username the client is trying to log in as and the _token_ is a random generated _uuid_ that the server uses to store the communication session between this client.

When the server then receives the request it checks the _username_. If it exists, the server will send the first challenge to the client. Challenges are composed of the _val_ field, that indicates the integer that should be used as a key to the hash function that will return a 1-bit result. 

#### Iterations

After receiving a challenge, the client responds with a 1-bit result. If the iteration number is lower than _N_, it sends the next challenge to the server, because the client must also assess if the attempted server is suspicious or not. The same operation is done with the server as well, so both sides will trade challenges and responses so that no side has the advantage of receiving all the contents first.

If one side replies with an incorrect answer, the other will notice and start to generate random bits for the next responses, so that the suspicious agent doesn't obtain information about the password.

#### Ending

If the client received the Nth response and the server doesn't seem suspicious, it sends a conclusion HTTP request to the server, that informs it that N responses have already been completed. The server will then determine if the client will be allowed to log in (if it has passed all the previous challenges). If it's allowed, the server creates another random _uuid_ token and sends it to the client, that will perform the final redirect using this token as cookies. 

Finally, the server receives that redirect and validates the used token. If it exists and the associated authentication attempt is not suspicious, the server logs the user in.



## How to Run

### Linux (With Bash Scripts)

Open two terminal tabs/windows.

Run the Django application (app_sec)

`./run_app.sh`

Run the Flask application (uap)

`./run_uap.sh`

The desired port for each application can be input as a command line argument.
If not specified, the default ports (Django: 8000, Flask: 5000) will be used.
Note: If you wish to run the applications using non-default ports, the variables SERVER_URL (app) and BASE_URL (UAP) .env files must be changed accordingly.


### Linux (Manual)

##### Virtual Environment and Requirements

Create Virtual Environment

`python3 -m venv venv`

Activate Virtual Environment

`source venv/bin/activate`

Install Requirements

`pip install -r requirements.txt`

##### **Django Application**

Run the Application

`python3 app_sec/manage.py runserver {port}`

If not specified, the default port 8000 will be used.

##### Flask Application

Move to the application directory

`cd uap`

Run the Application

`flask run`



### Windows (Manual, no Virtual Environment)

##### Requirements

Install Requirements

`python -m pip install -r requirements.txt`

##### **Django Application**

Run the Application

`python app_sec/manage.py runserver {port}`

If not specified, the default port 8000 will be used.

##### Flask Application

Move to the application directory

`cd uap`

Set the FLASK_APP environment variable
`$env:FLASK_APP = "uap"`

Run the Application

`python -m flask run`
