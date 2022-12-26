import pymongo
from flask import Flask, render_template, request, redirect, session, flash

myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["mydatabase"]
table_customer_login = mydb["customer"]
product = mydb["product1"]
table_history = mydb["purchase_history1"]

cart_product_name=[]
buy_info=dict()
admin_name='admin1'
admin_pass='12345678'



app = Flask(__name__)
app.secret_key='ok'

def search_item(x):
    all_product = []
    for a in product.find():
        all_product.append(a['p_name'])
    search = ("_".join(x.split())).lower()
    splited_word = search.split("_")
    tokens = [search]
    for word in splited_word:
        tokens.append(word)

    item_list = []
    for token in tokens:
        for name in all_product:
            if (token in name.lower()) and (name not in item_list):
                item_list.append(name)
    return item_list
@app.route('/', methods = ['GET', 'POST'])
@app.route('/home', methods = ['GET', 'POST'])
def home():
    session['location']='/'
    if request.method == 'POST':
        session['search_string']=request.form["search"]
        return redirect("/search")
    return render_template("home.html", **locals())

@app.route('/registration', methods = ['GET', 'POST'])
def registration():
    all_name = []
    for x in table_customer_login.find():
        all_name.append(x['name'])

    info = dict()
    msg_name = ''
    msg_pass1 = ''
    msg_pass2 = ''
    msg_email = ''
    check = True
    if request.method == 'POST':
        name = request.form["name"]
        pass1 = request.form["pass1"]
        pass2 = request.form["pass2"]
        email = request.form["email"]

        # validating Name, Id, Password
        if (len(name) < 5):
            msg_name = 'Name must have 5 or more character'
            check = False
        for letter in name:
            if not ((letter <= '9' and letter >= '0') or (letter <= 'z' and letter >= 'A') or letter == '_'):
                msg_name = "You can only use 'A-Z,a-Z,0-9,_'"
                check = False
                break
        if (name in all_name):
            msg_name = 'This username is not available. Please try different one'
            check = False
        if (len(pass1) < 8):
            msg_pass1 = 'Password must have 8 or more character'
            check = False
        if (pass1 != pass2):
            msg_pass2 = 'Give same password'
            check = False
        if '@gmail.com' not in email[(len(email)-10):]:
            msg_email = 'Invalid email formate'
            check = False

        # Add to dataase
        if check is True:
            info['name'] = name
            info['pass'] = pass1
            info['email'] = email
            info['status'] = 'enable'
            table_customer_login.insert_one(info)
            return render_template("post_reg.html", **locals())
    return render_template("reg.html", **locals())

@app.route('/login', methods = ['GET', 'POST'])
def login():
    msg= ''
    if request.method == 'POST':
        name = request.form["name"]
        password = request.form["pass"]
        user_type = request.form.get("user")
        if (user_type == "admin"):
            if ((name == admin_name) and (password == admin_pass)):
                session['admin_name'] = admin_name
                return redirect("/admin_home")
            else:
                msg= 'Please give all the information correctly'

        elif (user_type == "customer"):
            all_name = []
            for x in table_customer_login.find():
                all_name.append(x['name'])
            if name in all_name:
                y = dict()
                y = table_customer_login.find_one({'name': name})
                # check password and account status
                if (password == y['pass']):
                    if (y['status'] == 'enable'):
                        session['name'] = name
                        return redirect(session['location'])
                    else:
                        msg = 'You account is being disabled, please contact with the admin.'
                else:
                    msg= 'Please give all the information correctly'
            else:
                msg= 'Please give all the information correctly'
        else:
            msg = 'Please give all the information correctly'
    return render_template("login.html", **locals())

@app.route('/logout', methods = ['GET', 'POST'])
def logout():
    if request.method == 'POST':
        # clear all the temporary values..
        session.pop('name', None)
        session.pop('admin_name', None)
        session.pop('location', None)
        session.pop('product', None)
        session.pop('product_name', None) # used for update or change product in admin panel
        session.pop('customer_name_for_other_operation',None)
        cart_product_name.clear()

        return redirect("/home")
    return render_template("logout.html", **locals())

@app.route('/shop', methods = ['GET', 'POST'])
def shop():
    session['location'] = '/shop'
    p_name = []
    p_price = []
    p_unit = []

    for x in product.find():
        p_name.append(x['p_name'])
        p_price.append(x['price'])
        p_unit.append(int(x['unit']))
    row = len(p_name)
    pic = []
    for i in p_name:
        pic.append('shop1/'+i + '.jpg')
    if request.method == 'POST':
        # getting search data
        if (request.form["name"]=='searching'):
            session['search_string'] = request.form["search"]
            return redirect("/search")
        # getting product data
        else:
            cart_product_name.append(request.form["name"])
            return redirect("/cart")
    return render_template("shop.html", **locals())

@app.route('/about_us', methods = ['GET', 'POST'])
def about_us():
    session['location'] = '/about_us'
    return render_template("about.html", **locals())

@app.route('/ticket', methods = ['GET', 'POST'])
def ticket():
    return render_template("ticket.html", **locals())

@app.route('/fixture', methods = ['GET', 'POST'])
def fixture():
    session['location'] = '/fixture'
    return render_template("fixture.html", **locals())

@app.route('/cart', methods = ['GET', 'POST'])
def cart():
    session['location'] = '/cart'
    p_name = []
    p_price = []
    p_unit = []

    # find info of each product available in cart
    for x in cart_product_name:
        y = dict()
        y = product.find_one({'p_name': x})
        p_name.append(y['p_name'])
        p_price.append(y['price'])
        p_unit.append(y['unit'])

    row = len(p_name)
    pic = []
    for i in p_name:
        pic.append('shop1/' + i + '.jpg')

    if request.method == 'POST':
        session['product'] = request.form["name"]
        return redirect("/buy")
    return render_template("cart2.html", **locals())

@app.route('/search', methods = ['GET', 'POST'])
def search():
    p_name = search_item(session['search_string'])
    p_price = []
    p_unit = []
    for item in p_name:
        data = product.find_one({'p_name': item})
        p_price.append(data['price'])
        p_unit.append(int(data['unit']))
    row = len(p_name)
    pic = []
    for i in p_name:
        pic.append('shop1/' + i + '.jpg')
    if 'admin_name' in session:
        return render_template("product_list.html", **locals())
    else:
        return render_template("shop.html", **locals())

@app.route('/buy', methods = ['GET', 'POST'])
def buy():
    msg='' # warning massage
    a=dict() # inserting data into history table using this dictionary
    count=0 # for single product
    count_list=[] # for all product
    p_name1=''

    # showing information in buy page
    if session['product']=='All':
        total_price=0
        p_name=cart_product_name
        for x in cart_product_name:
            p_name1 += x + ', '
            data = product.find_one({'p_name': x})
            total_price += int(data['price'])
            count_list.append(int(data['unit']))
    else:
        p_name1 = session['product']
        data = product.find_one({'p_name': p_name1})
        total_price = int(data['price'])
        count = int(data['unit'])

    # update/change in database
    if request.method == 'POST':
        ac_no=''
        ac_no=request.form["ac_no"]
        if (ac_no != ''):
            # saving purchase history
            a['customer'] = session['name']
            a['product'] = p_name1
            a['total_Price'] = total_price
            a['ac_no'] = ac_no
            table_history.insert_one(a)
            # change available unit
            if session['product'] == 'All':
                for i in range(len(cart_product_name)):
                    count_list[i] = count_list[i] - 1
                    product.update_many({'p_name': cart_product_name[i]}, {"$set": {'unit': str(count_list[i])}})
                cart_product_name.clear()
            else:
                count = count - 1
                product.update_many({'p_name': p_name1}, {"$set": {'unit': str(count)}})
                cart_product_name.remove(p_name1)
            return redirect("/buy_successful")
        else:
            msg="Sorry! you did not give your account number."

    return render_template("buy.html", **locals())

@app.route('/buy_successful', methods = ['GET', 'POST'])
def buy_successful():

    return render_template("buy_successful.html", **locals())

#@app.route('/', methods = ['GET', 'POST'])
@app.route('/admin_home', methods = ['GET', 'POST'])
def admin_home():
    return render_template("admin_home.html", **locals())

@app.route('/customer', methods = ['GET', 'POST'])
def customer():
    c_name=[]
    c_pass=[]
    c_email=[]
    c_status=[]
    for x in table_customer_login.find():
        c_name.append(x['name'])
        c_pass.append(x['pass'])
        c_email.append(x['email'])
        c_status.append(x['status'])
    l = len(c_name)
    if request.method == 'POST':
        session['customer_name_for_other_operation'] = request.form["name"]

        if (request.form["operation"]=="vew_history"):
            return redirect("/customer_history")

        elif (request.form["operation"]=='enable'):
            table_customer_login.update_many({'name': session['customer_name_for_other_operation']},
                                {"$set": {'status': 'disable'}})
            return redirect("/customer")


        elif (request.form["operation"] == 'disable'):
            table_customer_login.update_many({'name': session['customer_name_for_other_operation']},
                                {"$set": {'status': 'enable'}})
            return redirect("/customer")

    return render_template("customer.html", **locals())
'''
@app.route('/disable_account', methods = ['GET', 'POST'])
def disable_account():

    return render_template("disable_account.html", **locals())
'''
@app.route('/history', methods = ['GET', 'POST'])
def history():
    customer_name = []
    product_name = []
    ac_no = []
    total_price = []
    for x in table_history.find():
        customer_name.append(x['customer'])
        product_name.append(x['product'])
        total_price.append(x['total_Price'])
        ac_no.append(x['ac_no'])
    l = len(customer_name)

    return render_template("history.html", **locals())

@app.route('/customer_history', methods = ['GET', 'POST'])
def customer_history():
    customer_name = session['customer_name_for_other_operation']
    product_name = []
    total_price = []

    for x in table_history.find():
        if (x['customer'] == customer_name):
            product_name.append(x['product'])
            total_price.append(x['total_Price'])
    l = len(product_name)
    return render_template("customer_history.html", **locals())
@app.route('/product_list', methods = ['GET', 'POST'])
def product_list():
    p_name = []
    p_price = []
    p_unit = []

    for x in product.find():
        p_name.append(x['p_name'])
        p_price.append(x['price'])
        p_unit.append(int(x['unit']))
    row = len(p_name)
    pic = []
    for i in p_name:
        pic.append('shop1/' + i + '.jpg')

    if request.method == 'POST':
        # getting search data
        if (request.form["name"]=='searching'):
            session['search_string'] = request.form["search"]
            return redirect("/search")

        if (request.form["name"] == 'update'):
            session['product_name'] = request.form["product"]
            return redirect("/update")

    return render_template("product_list.html", **locals())

@app.route('/update', methods = ['GET', 'POST'])
def update():

    x = product.find_one({"p_name" : session['product_name']})
    p_name = x['p_name']
    price = x['price']
    unit = x['unit']
    pic = 'shop1/' + session['product_name'] + '.jpg'
    if request.method == 'POST':
        new_price = request.form["price"]
        new_unit = request.form["unit"]
        if new_price == "":
            new_price=price
        if new_unit == "":
            new_unit=unit
        product.update_many({'p_name': p_name}, {"$set": {'price': str(new_price)}})
        product.update_many({'p_name': p_name}, {"$set": {'unit': str(new_unit)}})
        return redirect("/product_list")

    return render_template("update.html", **locals())


if __name__ == '__main__':
    app.run()