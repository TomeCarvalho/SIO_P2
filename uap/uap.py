import json, requests, hashlib, random, uuid, os

from requests.models import Response
from flask import Flask, request, render_template, redirect, url_for, make_response, flash, jsonify
from bitstring import BitArray
from encryption import encrypt, encrypt_dict, decrypt

app = Flask(__name__)
dic = {} # Information about every auth attempt

N = int(os.environ['N'])  # Number of iterations
RANDOM_LIMIT = int(os.environ['RANDOM_LIMIT'])  # Challenge random int limit
MASTER_PW = os.environ['MASTER_PW']
BASE_URL = f"{os.environ['BASE_URL']}echapsend"

servers = None # Servers on the UAP's DB

@app.route("/", methods=['GET', 'POST'])
def vault():
    """Show the vault if unlocked, otherwise redirect to unlock page."""
    if request.cookies.get('unlocked') == MASTER_PW:
        global servers
        servers = json.loads(decrypt('servers_encrypted'))
        return render_template('vault.html', servers=servers)
    return redirect(url_for('unlock'))
        
@app.route('/unlockpage', methods=['GET', 'POST'])
def unlock():
    """Unlock the vault using the master password."""
    if request.method == 'POST':
        if request.form.get('password') == MASTER_PW:
            resp = make_response(redirect(url_for('vault')))
            resp.set_cookie('unlocked', MASTER_PW)
            return resp
    return render_template('unlock.html')

@app.route('/echapsend', methods=['POST', 'GET'])
def echapsend():
    form = request.form
    global dic 

    if request.method == 'POST':
        if 'val' not in request.form:
            form = request.form
            dns = form.get('dns')
            username = form.get('username')
            password = form.get('password')
            token = str(uuid.uuid1())

            hash_pass = hashlib.md5(password.encode('utf-8'))
            bit_pass = BitArray(hash_pass.digest())
            dic[token] = [bit_pass, True, 0, 0, '', '', '', 0] # (password, serverStillValid, N, current_challenge, loginToken, serverbits, different_bitIdx)

            response = requests.post(dns, data={
                'username': username
            }, cookies={'identifier': token,'client_url': BASE_URL}) # identifier

            # If not a valid server/password, show the message to the end user.
            if not dic[token][1]:
                return make_response(jsonify({"message":f"Authentication failed on iteration Nº {dic[token][7]}. Please confirm the passsword or the server and try again."}))
            
            # If is valid, go to the server page and profit
            red = redirect(dns)
            red.set_cookie('login_token', dic[token][4])
            red.set_cookie('user_id', username)
            red.set_cookie('identifier', token)

            return red

            
        elif 'type' in form:
            cookies = request.cookies
            uap_bit = dic[cookies.get('identifier')]

            server_url = cookies.get('server_url')
            server_identifier = cookies.get('identifier')
            server_val = int(form.get('val'))

            # Replying to server's challenge
            if form.get('type') == 'challenge':
                
                solved_challenge = solve_challenge(server_val, uap_bit[0]) if uap_bit[1] else random.randint(0,1)
                requests.post(server_url, data={
                        'val': solved_challenge,
                        'type': 'response'
                }, cookies={'identifier': server_identifier, 'client_url': BASE_URL})

                # After replying a challenge, create one to the server if < N iteration.
                if uap_bit[2] < N:
                    uap_bit[3] = random.randint(1, RANDOM_LIMIT)

                    uap_bit[2] += 1

                    requests.post(server_url, data={
                        'val': uap_bit[3],
                        'type': 'challenge'
                    }, cookies={'identifier': server_identifier, 'client_url': BASE_URL})

                return make_response(jsonify({"message":'Challenge replied'}))
            
            elif form.get('type') == 'response':

                uap_bit[5] += str(server_val)
                uap_bit[6] += str(solve_challenge(uap_bit[3], uap_bit[0]))
                temp = uap_bit[1]

                # Changes if the server is valid or not accordling to its response
                uap_bit[1] &= solve_challenge(uap_bit[3], uap_bit[0]) == server_val
                

                if temp and not uap_bit[1]: # First different bit
                    uap_bit[7] = uap_bit[2]

                # When the N iteration arrives and the server is a valid one.
                if uap_bit[2] == N and uap_bit[1]:

                    response = requests.post(server_url, data={
                        'val': int(uap_bit[1]),
                        'type': 'conclusion'
                    }, cookies={'identifier': server_identifier, 'client_url': BASE_URL})

                    uap_bit[4] = response.cookies.get("login_token")
                    return "Valid server/password"

                return make_response(jsonify({"message":'Response checked'}))

            elif form.get('type') == 'conclusion':
                print(f'received conclusion from server: {server_val}')

                return make_response(jsonify({"message":"You are in server"})) if server_val else make_response(jsonify({"message":"You are not in a server"}))
        else:
            return make_response(jsonify({"message":"Something went wrong."}))


def solve_challenge(challenge, passw):
    
    # hash challenge (seed) --> int
    # hash password --> ArrayBit
    # or both --> ArrayBit
    # n1%2 == 0 --> 0/1
    # If it's wrong, 50% chance of being the correct bit.

    hash_challenge = BitArray(hashlib.md5(bin(challenge).encode('utf-8')).digest())
    return sum(hash_challenge | passw) % 2


@app.route('/additem', methods=['POST'])
def additem():
    """Add (or replace) an item to the vault."""
    if not request.cookies.get('unlocked') == MASTER_PW:
        return redirect(url_for('unlock'))
    global servers
    if not servers:
        servers = json.loads(decrypt('servers_encrypted'))
    if request.method == 'POST':
        form = request.form
        dns = form.get('dns')
        if dns not in servers:
            servers[dns] = {}
        servers[dns][form.get('username')] = form.get('password')
        with open('servers_encrypted', 'wb') as servers_encrypted:
            servers_encrypted.write(encrypt_dict(servers))
    return redirect(url_for('vault'))

@app.route('/delitem', methods=['POST'])
def delitem():
    """Delete an item from the vault."""
    if not request.cookies.get('unlocked') == MASTER_PW:
        return redirect(url_for('unlock'))
    global servers
    if not servers:
        servers = json.loads(decrypt('servers_encrypted'))
    if request.method == 'POST':
        form = request.form
        dns = form.get('dns')
        username = form.get('username')
        if dns in servers:
            if username in servers[dns]:
                del servers[dns][username]
                if not servers[dns]:
                    del servers[dns]
        with open('servers_encrypted', 'wb') as servers_encrypted:
            servers_encrypted.write(encrypt_dict(servers))
    return redirect(url_for('vault'))
