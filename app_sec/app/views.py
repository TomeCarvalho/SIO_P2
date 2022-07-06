import base64, datetime, hashlib, requests, uuid, random, environ
from bitstring import BitArray
from datetime import datetime
from django.contrib.auth.hashers import make_password, check_password
from django.db import connection
from django.http import HttpResponse
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from itertools import zip_longest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app_sec.settings import PASSWORD, KDF_LENGTH, ITERATIONS, N, RANDOM_LIMIT, SALT
from app.models import User, Page, Comment
from .forms import WikiForm, LoginForm, CreateAccountForm, CommentForm, ChangePasswordForm


# Create your views here.

@csrf_protect
def dashboard(request):
    logged = request.session.get('user_id')
    search_prompt = f"%{request.GET.get('search_prompt', '')}%"
    if User.objects.raw("SELECT * FROM app_user WHERE username = %s AND admin = True", params=[logged]):
        page_list = Page.objects.raw("SELECT * FROM app_page WHERE title LIKE %s", params=[search_prompt])
    else:
        page_list = Page.objects.raw("SELECT * FROM app_page WHERE title LIKE %s AND hidden = False",
                                     params=[search_prompt])
    pgs = zip_longest(*(iter(page_list),) * 3)  # chunky!
    tparams = {
        "three_page_group": pgs,
        "search_prompt": search_prompt[1:-1],
        # "logged": User.objects.raw("SELECT * FROM app_user WHERE username = %s", params=[logged]),
        "logged": logged,
        "dashboardPage": True,
        "user": User.objects.raw("SELECT * FROM app_user WHERE username = %s", params=[logged])
    }
    return render(request, "dashboard.html", tparams)


def create_wiki(request):
    if not request.session.get('user_id'):
        return HttpResponse("You lack permissions >:(")
    if request.method == "POST":
        form = WikiForm(request.POST)
        post = request.POST
        if form.is_valid():
            with connection.cursor() as cursor:
                title = post["title"]
                img = post["img_url"]
                content = post["content"]
                # date = form.cleaned_data['date']
                date = datetime.now()
                user = request.session.get('user_id')
                cursor.execute('INSERT INTO app_page (title, user_id, img_url, content, date, hidden) '
                               'VALUES (%s, %s, %s, %s, %s, %s)',
                               params=[title, user, img, content, date, 0])
                return redirect(dashboard)
    else:
        form = WikiForm()

    return render(request, "createWiki.html", {
        "form": form,
        "createPage": True,
        "logged": request.session.get('user_id')
    })


def wiki_page(request, i):
    logged = request.session.get('user_id')
    if logged:
        print("DEBUG Username:", logged)

    page = Page.objects.raw("SELECT * FROM app_page WHERE id=%s", params=[i])
    comments = Comment.objects.raw("SELECT * FROM app_comment WHERE page_id = %s ORDER BY date DESC", params=[i])
    for p in page:
        if p.hidden:
            if len(list(User.objects.raw("SELECT * FROM app_user WHERE username = %s", params=[logged]))) == 0:
                return redirect(dashboard)
            elif not User.objects.raw("SELECT * FROM app_user WHERE username = %s", params=[logged])[0].admin:
                return redirect(dashboard)
        params = {
            "page": {
                "title": p.title,
                "content": p.content,
                "date": p.date,
                "date_pretty": None if p.date is None else p.date.strftime('%c'),
                "img_url": p.img_url,
                "user": p.user_id,
                "comments": comments,
                "id": p.id,
                "hidden": p.hidden
            },
            "logged": logged,
            "user": User.objects.raw("SELECT * FROM app_user WHERE username = %s", params=[logged])
        }
        return render(request, "wikiPage.html", params)
    return HttpResponse("404 - Page not found :(")


KDF = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=KDF_LENGTH,
    salt=SALT,
    iterations=ITERATIONS
)
KEY = base64.urlsafe_b64encode(KDF.derive(PASSWORD))
FERNET = Fernet(KEY)


def create_account(request):
    # teste da session, se estiver login imprime no terminal a mensagem
    if request.session.get('user_id'):
        print("DID IT")

    if request.method == 'POST':
        form = CreateAccountForm(request.POST)
        if form.is_valid():
            username = request.POST['username']
            email = request.POST['email']
            password = request.POST['password']
            repeat_password = request.POST['repeat_password']

            if password != repeat_password:
                form.add_error(field='password', error="Passwords don't match")
            elif list(User.objects.raw("SELECT username FROM app_user WHERE username=%s", params=[username])):
                form.add_error(field="username", error="Username already exists")
            else:
                print("Inserting")
                password_encrypted = FERNET.encrypt(password.encode('utf-8'))
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO app_user (username, password, email, admin)"
                                   " VALUES (%s, %s, %s, %s) ",
                                   params=[username, password_encrypted, email, 0])
                return redirect(dashboard)
    else:
        form = CreateAccountForm()
    return render(request, "createAccount.html", {
        "form": form,
        "logged": request.session.get('user_id')
    })


def logout(request):
    try:
        del request.session['user_id']
    except KeyError:
        pass
    return redirect(dashboard)


def create_comment(request, _id):
    logged = request.session.get('user_id')
    for p in Page.objects.raw("SELECT * FROM app_page WHERE id=%s", params=[_id]):
        if p.hidden:
            if len(list(User.objects.raw("SELECT * FROM app_user WHERE username = %s", params=[logged]))) == 0:
                return redirect(dashboard)
            elif not User.objects.raw("SELECT * FROM app_user WHERE username = %s", params=[logged])[0].admin:
                return redirect(dashboard)
    if request.method == "POST":
        form = CommentForm(request.POST)
        post = request.POST
        if form.is_valid():
            with connection.cursor() as cursor:
                content = post["content"]
                # date = form.cleaned_data["date"]
                date = datetime.now()
                print('DEBUG: create_comment - datetime.now():', date)
                user = request.session.get('user_id')
                print('DEBUG: create_comment - user:', user)
                cursor.execute("INSERT INTO app_comment (page_id, user_id, content, date, hidden) "
                               "VALUES (%s, %s, %s, %s, %s);", params=[_id, user, content, date, 0])
                return redirect(wiki_page, i=_id)
    else:
        form = CommentForm()

    return render(request, "createWiki.html", {
        "form": form,
        "logged": request.session.get('user_id')
    })


def hide_page(request):
    logged = request.session.get('user_id')
    if not User.objects.raw("SELECT * FROM app_user WHERE username = %s AND admin = True", params=[logged]):
        return HttpResponse("You lack permissions >:(")

    if "delete-page" in request.POST:
        page_id = request.POST["delete-page"]
        with connection.cursor() as cursor:
            cursor.execute("UPDATE app_page SET hidden = 1 WHERE id=%s", params=[page_id])
        return redirect(dashboard)

    return HttpResponse("An error occurred :(")


def unhide_page(request):
    logged = request.session.get('user_id')
    if not User.objects.raw("SELECT * FROM app_user WHERE username = %s AND admin = True", params=[logged]):
        return HttpResponse("You lack permissions >:(")

    if "delete-page" in request.POST:
        page_id = request.POST["delete-page"]
        with connection.cursor() as cursor:
            cursor.execute("UPDATE app_page SET hidden = 0 WHERE id=%s", params=[page_id])
        return redirect(dashboard)

    return HttpResponse("An error occurred :(")


def hide_comment(request):
    logged = request.session.get('user_id')
    if not User.objects.raw("SELECT * FROM app_user WHERE username = %s AND admin = True", params=[logged]):
        return HttpResponse("You lack permissions >:(")
    if "delete-comment" in request.POST:
        st = request.POST["delete-comment"]
        comment_id = st.split(",")[0]
        page_id = st.split(",")[1]
        with connection.cursor() as cursor:
            cursor.execute("UPDATE app_comment SET hidden = 1 WHERE id=%s", params=[comment_id])
        return redirect(wiki_page, i=page_id)

    return HttpResponse("An error occurred :(")


def unhide_comment(request):
    logged = request.session.get('user_id')
    if not User.objects.raw("SELECT * FROM app_user WHERE username = %s AND admin = True", params=[logged]):
        return HttpResponse("You lack permissions >:(")
    if "delete-comment" in request.POST:
        st = request.POST["delete-comment"]
        comment_id = st.split(",")[0]
        page_id = st.split(",")[1]
        with connection.cursor() as cursor:
            cursor.execute("UPDATE app_comment SET hidden = 0 WHERE id=%s", params=[comment_id])
        return redirect(wiki_page, i=page_id)

    return HttpResponse("An error occurred :(")


def profile(request):
    if request.session.get('user_id'):
        data = User.objects.raw("SELECT * FROM app_user WHERE username=%s", params=[request.session.get('user_id')])
        for d in data:
            params = {
                "info": {
                    "username": d.username,
                    "email": d.email,
                },
                "logged": request.session.get('user_id')
            }
            return render(request, "profile.html", params)
    return HttpResponse("404 - Page not found :(")


def change_password(request):
    if request.session.get('user_id'):
        if request.method == 'POST':
            form = ChangePasswordForm(request.POST)
            if form.is_valid():
                username = request.POST['username']
                password = request.POST['password']
                repeat_password = request.POST['repeat_password']

                if username != request.session.get('user_id'):
                    form.add_error(field='username', error="Wrong username")
                if password != repeat_password:
                    form.add_error(field='password', error="Passwords don't match")
                else:
                    print("Inserting")
                    with connection.cursor() as cursor:
                        cursor.execute("UPDATE app_user "
                                       "SET password=%s"
                                       "WHERE username=%s",
                                       params=[make_password(password), username])
        else:
            form = ChangePasswordForm()
        return render(request, "createAccount.html", {
            "form": form,
            "logged": request.session.get('user_id')
        })
    return HttpResponse("404 - Page not found :(")


def login_page(request):
    if request.session.get("user_id"):
        return redirect(profile)
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            print("DEBUG: login_page - form is valid")
            password = request.POST['password']
            user = User.objects.raw(
                "SELECT * FROM app_user "
                "WHERE username=%s ",
                params=[request.POST['username']]
            )
            if user:
                u = list(user)[0]
                if check_password(password, u.password):
                    request.session['user_id'] = u.username
                    return redirect(dashboard)
                else:
                    form.add_error(field='password', error="Invalid password.")
            else:
                form.add_error(field='username', error="Username doesn't exist.")
    else:
        form = LoginForm()
    return render(request, "loginPage.html", {
        "form": form, "loginPage": True,
        "logged": request.session.get('user_id')
    })


dic = {}

@csrf_exempt
def uap_login(request):
    global dic
    server_port = request.META['SERVER_PORT']
    server_name = request.META['SERVER_NAME']
    server_val = f"http://{server_name}:{server_port}/"
    # If it's a valid user and it replied with the correct login_token
    if request.COOKIES.get('login_token'):
        uap_bit = dic.get(request.COOKIES.get('identifier'))

        if not uap_bit or request.COOKIES.get('login_token') != uap_bit[4]:
            # Fake login_token for selected user
            return HttpResponse("Invalid login token for this user.")

        user_id = request.COOKIES.get("user_id")

        request.session["user_id"] = user_id
        request.session.modified = True
        return redirect(dashboard)

    if request.method == 'POST':
        post = request.POST
        username = post.get('username')
        client_url = request.COOKIES.get('client_url')
        client_token = request.COOKIES.get('identifier')

        if username:
            user = User.objects.raw(
                "SELECT * FROM app_user "
                "WHERE username=%s ",
                params=[username]
            )
            if user:
                u = list(user)[0]
                password = FERNET.decrypt(u.password).decode('utf-8')
                hash_pass = hashlib.md5(password.encode('utf-8'))
                bit_pass = BitArray(hash_pass.digest())
                first_challenge = random.randint(1, RANDOM_LIMIT)
                dic[client_token] = [bit_pass, True, 0, first_challenge,
                                     '']  # (password, isStillValid, N, current_challenge, tokenForLogin)

                requests.post(client_url, data={
                    'val': first_challenge,
                    'type': 'challenge'
                }, cookies={'identifier': client_token, 'server_url': server_val})

                return HttpResponse('whatever')

        elif 'type' in post:
            cookies = request.COOKIES
            uap_bit = dic.get(cookies.get('identifier'))
            client_identifier = cookies.get('identifier')
            client_val = int(post.get('val'))

            if post.get('type') == 'challenge':
                # sever_val = challenge itself

                solved_challenge = solve_challenge(client_val, uap_bit[0]) if uap_bit[1] else random.randint(0, 1)
                requests.post(client_url, data={
                    'val': solved_challenge,
                    'type': 'response'
                }, cookies={'identifier': client_token, 'server_url': server_val})

                if uap_bit[2] < N:
                    uap_bit[3] = random.randint(1, RANDOM_LIMIT)
                    uap_bit[2] += 1
                    if uap_bit[2] == N: return 'sus'

                    requests.post(client_url, data={
                        'val': uap_bit[3],
                        'type': 'challenge'
                    }, cookies={'identifier': client_token, 'server_url': server_val})

                return HttpResponse(int(uap_bit[1]))

            elif post.get('type') == 'response':
                uap_bit[1] &= solve_challenge(uap_bit[3], uap_bit[0]) == client_val

                return 'do it'

            elif post.get('type') == 'conclusion':

                if uap_bit[1] and uap_bit[2] >= N - 1:
                    response = HttpResponse('es digno')
                    token_for_login = str(uuid.uuid1())
                    uap_bit[4] = token_for_login
                    response.set_cookie('login_token', token_for_login)
                    return response

                else:
                    return HttpResponse('es cringe. vaza.')

    return redirect(dashboard)


def solve_challenge(challenge, passw):

    # hash challenge (seed) --> int
    # hash password --> ArrayBit
    # or both --> ArrayBit
    # n1%2 == 0 --> 0/1
    # tested. If wrong, 50% chance of being the correct bit

    hash_challenge = BitArray(hashlib.md5(bin(challenge).encode('utf-8')).digest())
    return sum(hash_challenge | passw) % 2
