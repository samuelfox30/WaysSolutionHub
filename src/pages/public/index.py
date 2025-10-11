from flask import Flask, Blueprint, render_template, url_for, redirect, request, session

app_index = Blueprint('index', __name__)

#------------------FUNÇÃO PRINCIPAL------------------#
@app_index.route('/')
def index():
    """ if 'user' in session:
        return redirect(url_for('profile.profile'))
    return render_template('pages/public/index.html') """
    return render_template('public/index.html')


#------------------LOGAR------------------#
@app_index.route('/login', methods=['POST', 'GET'])
def login():

    if request.method == 'POST':
        user_type = request.form.get('user_type')
        email = request.form.get('email')
        senha = request.form.get('password')

        print(user_type, email, senha)
        
        
        
        if result['Status'] == False:
            mensagem_error = result['Message']
            return render_template('pages/public/index.html', mensagem_error=mensagem_error)
        elif result['Status'] == True:
            session['user'] = email
            return redirect(url_for('profile.profile'))
        
    return render_template('public/logar.html')


