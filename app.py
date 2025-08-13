from flask import Flask, request, redirect, url_for, render_template, flash, session, send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime
import sqlite3
import os
import io

# Cria a instância do Flask
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Necessário para usar sessões de flash

altura_da_pagina = letter[1]  # letter[1] é a altura em pontos

def check_login(username, password):
    conn = sqlite3.connect('databases/main.db')
    c = conn.cursor()
    c.execute('SELECT password, user_db FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    if user and user[0] == password:
        return user[1]
    return None

# Função para verificar se o banco de dados do usuário existe
def user_db_exists(user_db):
    return os.path.exists(os.path.join('databases/user_databases', user_db))

# Função para criar o banco de dados do usuário se não existir
def create_user_db(user_db):
    os.makedirs('databases/user_databases', exist_ok=True)
    conn = sqlite3.connect(os.path.join('databases/user_databases', user_db))
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            rg TEXT,
            endereco TEXT,
            whatsapp TEXT,
            usuario_cadastro TEXT
        )
    ''')
    conn.commit()
    conn.close()



def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Função de logout
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Você foi desconectado com sucesso!', 'success')
    return redirect(url_for('login'))

# Roteamento
@app.route('/')
def index():
    return render_template('default/login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_db = check_login(username, password)
        
        if user_db:
            if not user_db_exists(user_db):
                create_user_db(user_db)
            session['username'] = username  # Armazenar o nome do usuário na sessão
            return redirect(url_for('user_page', user_db=user_db))
        return 'Login Failed', 401
    return render_template('default/login.html')


@app.route('/<user_db>/dashboard', methods=['GET', 'POST'])
@login_required
def user_page(user_db):
    template_folder = {
        'autocentercarioca.db': 'autocentercarioca',
        'modasmilgrau.db': 'modasmilgrau',
        'espetocarioca.db': 'espetocarioca'
    }.get(user_db, 'default')
    
    template_path = os.path.join('templates', template_folder, 'dashboard.html')
    
    if not os.path.exists(template_path):
        return 'Template folder or file not found', 404
    
    conn = sqlite3.connect('databases/main.db')
    c = conn.cursor()
    c.execute('SELECT username, user_db FROM users')
    users = c.fetchall()
    conn.close()
    
    username = session.get('username')  # Obter o nome do usuário logado da sessão
    
    if request.method == 'POST':
        # Processamento de formulários...
        return redirect(url_for('user_page', user_db=user_db))
    
    return render_template(f'{template_folder}/dashboard.html', users=users, username=username)


def obter_usuario_logado():
    return session.get('username', 'Administrador')


#ESPETTO CARIOCA FUNÇOES

@app.route('/espettocarioca/inicio')
@login_required
def espettocarioca_inicio():
    username = obter_usuario_logado()
    return render_template('espetocarioca/dashboard.html', username=username)


@app.route('/espetocarioca/cardapio', methods=['GET', 'POST'])
@login_required
def espettocarioca_cardapio():
    username = obter_usuario_logado()
    conn = sqlite3.connect('databases/user_databases/espetocarioca.db')
    cur = conn.cursor()

    search_query = request.args.get('search', '')

    if request.method == 'POST':
        if 'adicionar' in request.form:
            nome = request.form['nome']
            valor_de_entrada = request.form['valor_de_entrada']

            if not nome or not valor_de_entrada:
                flash('Nome e valor de entrada são obrigatórios!', 'error')
                return redirect(url_for('espettocarioca_cardapio'))

            # Verificar se o item já existe
            cur.execute('SELECT * FROM cardapio WHERE nome = ?', (nome,))
            existing_item = cur.fetchone()
            
            if existing_item:
                flash('Item já existe no cardápio!', 'error')
                return redirect(url_for('espettocarioca_cardapio'))

            # Adicionar novo item
            cur.execute('INSERT INTO cardapio (nome, valor_de_entrada) VALUES (?, ?)',
                         (nome, valor_de_entrada))
            conn.commit()
            flash('Item adicionado ao cardápio com sucesso!', 'success')

        elif 'editar' in request.form:
            item_id = request.form['item_id']
            nome = request.form['nome']
            valor_de_entrada = request.form['valor_de_entrada']

            if not nome or not valor_de_entrada:
                flash('Nome e valor de entrada são obrigatórios!', 'error')
                return redirect(url_for('espettocarioca_cardapio'))

            cur.execute('UPDATE cardapio SET nome = ?, valor_de_entrada = ? WHERE id = ?',
                         (nome, valor_de_entrada, item_id))
            conn.commit()
            flash('Item editado com sucesso!', 'success')

        elif 'excluir' in request.form:
            item_id = request.form['item_id']

            cur.execute('DELETE FROM cardapio WHERE id = ?', (item_id,))
            conn.commit()
            flash('Item excluído com sucesso!', 'success')

    # Consulta com filtro de pesquisa, se houver
    if search_query:
        cur.execute('SELECT * FROM cardapio WHERE nome LIKE ?', ('%' + search_query + '%',))
    else:
        cur.execute('SELECT * FROM cardapio')

    itens = cur.fetchall()
    conn.close()

    return render_template('espetocarioca/cardapio.html', itens=itens, username=username)


@app.route('/espettocarioca/mesa<int:mesa_numero>', methods=['GET', 'POST'])
@login_required
def espettocarioca_mesa(mesa_numero):
    username = obter_usuario_logado()
    nome_tabela = f"mesa{mesa_numero:02d}"

    with sqlite3.connect('databases/user_databases/espetocarioca.db') as conn:
        cursor = conn.cursor()

        # Buscar cardápio para mostrar
        cursor.execute("SELECT nome, valor_de_entrada FROM cardapio")
        cardapio_itens = cursor.fetchall()

        if request.method == 'POST':
            # Adicionar item
            if 'item_nome' in request.form:
                item_nome = request.form['item_nome']
                quantidade = int(request.form['quantidade'])

                cursor.execute("SELECT valor_de_entrada FROM cardapio WHERE nome = ?", (item_nome,))
                valor_result = cursor.fetchone()

                if not valor_result:
                    flash('Item não encontrado no cardápio.', 'error')
                    return redirect(url_for('espettocarioca_mesa', mesa_numero=mesa_numero))

                valor = valor_result[0]
                if valor is None:
                    flash('Valor do item não encontrado. Verifique o cadastro do item.', 'error')
                    return redirect(url_for('espettocarioca_mesa', mesa_numero=mesa_numero))

                cursor.execute(
                    f"INSERT INTO {nome_tabela} (item_nome, valor_de_entrada, quantidade) VALUES (?, ?, ?)",
                    (item_nome, valor, quantidade)
                )
                conn.commit()
                flash('Item adicionado com sucesso!', 'success')
                return redirect(url_for('espettocarioca_mesa', mesa_numero=mesa_numero))

            # Remover item
            elif 'remover_item_nome' in request.form:
                item_nome = request.form['remover_item_nome']

                # Verifica a quantidade atual do item
                cursor.execute(f"SELECT rowid, quantidade FROM {nome_tabela} WHERE item_nome = ? LIMIT 1", (item_nome,))
                resultado = cursor.fetchone()

                if resultado:
                    rowid, quantidade = resultado
                    if quantidade > 1:
                        # Diminui a quantidade em 1
                        cursor.execute(f"UPDATE {nome_tabela} SET quantidade = quantidade - 1 WHERE rowid = ?", (rowid,))
                    else:
                        # Remove o registro se quantidade for 1
                        cursor.execute(f"DELETE FROM {nome_tabela} WHERE rowid = ?", (rowid,))
                    conn.commit()
                    flash(f'1 unidade de "{item_nome}" removida com sucesso!', 'success')
                else:
                    flash(f'Item "{item_nome}" não encontrado.', 'error')

                return redirect(url_for('espettocarioca_mesa', mesa_numero=mesa_numero))

            # Finalizar comanda (apaga tudo da mesa)
            elif 'finalizar_comanda' in request.form:
                cursor.execute(f"DELETE FROM {nome_tabela}")
                conn.commit()
                flash('Comanda finalizada com sucesso!', 'success')
                return redirect(url_for('espettocarioca_mesa', mesa_numero=mesa_numero))

            # Gerar PDF
            elif 'salvar_pdf' in request.form:
                return gerar_pdf_comanda(cursor, username, mesa_numero, nome_tabela)

        # Mostrar os itens da mesa
        cursor.execute(f"SELECT item_nome, valor_de_entrada, quantidade FROM {nome_tabela}")
        itens_adicionados = cursor.fetchall()

        total = sum((item[1] or 0) * (item[2] or 0) for item in itens_adicionados)
        total_com_taxa = round(total * 1.10, 2)

    return render_template(
        'espetocarioca/mesa.html',
        cardapio_itens=cardapio_itens,
        itens_adicionados=itens_adicionados,
        total=total,
        total_com_taxa=total_com_taxa,
        username=username,
        mesa_numero=mesa_numero
    )

def gerar_pdf_comanda(cursor, username, mesa_numero, nome_tabela, modelo='80mm'):
    buffer = io.BytesIO()

    # Buscar itens da mesa dinâmica antes de definir altura
    cursor.execute(f"SELECT item_nome, valor_de_entrada, quantidade FROM {nome_tabela}")
    itens_adicionados = cursor.fetchall()
    total_itens = len(itens_adicionados)

    # Define largura fixo para 80mm
    page_width = 227  # 80mm em points

    # Define altura baseada na quantidade de itens
    page_height = max(600, 200 + total_itens * 15)

    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))
    width, height = page_width, page_height

    # Cabeçalho
    c.setFont("Helvetica-Bold", 10)
    c.drawString(5, height - 20, "Espeto Carioca")
    c.setFont("Helvetica", 8)
    c.drawString(5, height - 35, "Rua Brasilino Alves da Nóbrega, 274")

    now = datetime.now()
    data_hora_formatada = now.strftime("%d/%m/%Y %H:%M")
    c.drawString(5, height - 50, f"Garçon: {username}")
    c.drawString(5, height - 65, f"Data/Hora: {data_hora_formatada}")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(5, height - 80, f"Comanda Mesa {mesa_numero:02d}")
    c.drawString(5, height - 95, "Item")
    c.drawString(width / 2, height - 95, "Qtd")
    c.drawString(width - 50, height - 95, "Valor")

    # Conteúdo
    y = height - 110
    total = 0
    for item in itens_adicionados:
        c.setFont("Helvetica", 7)
        c.drawString(5, y, item[0][:15])  # limita nome a 15 chars
        c.drawString(width / 2, y, str(item[2]))
        c.drawString(width - 50, y, f"R${item[1]:.2f}")
        total += (item[1] or 0) * (item[2] or 0)
        y -= 15

    # Totais
    c.setFont("Helvetica-Bold", 8)
    c.drawString(5, y, "Total sem taxa")
    c.drawString(width - 50, y, f"R${total:.2f}")

    total_com_taxa = total * 1.10
    c.drawString(5, y - 15, "Total com taxa (10%)")
    c.drawString(width - 50, y - 15, f"R${total_com_taxa:.2f}")

    c.setFont("Helvetica", 7)
    c.drawString(5, 10, "Obrigado pela preferência. Volte sempre!")

    c.save()
    buffer.seek(0)

    nome_arquivo = f"comanda_mesa{mesa_numero:02d}_{now.strftime('%Y%m%d_%H%M%S')}.pdf"
    return send_file(buffer, as_attachment=True, download_name=nome_arquivo, mimetype='application/pdf')


@app.route('/imprimir_comanda', methods=['POST'])
def imprimir_comanda():
    mesa_numero = int(request.form.get('mesa_numero'))
    username = session['username']
    nome_tabela = f"mesa{mesa_numero:02d}"

    conn = sqlite3.connect('databases/user_databases/espetocarioca.db')
    cursor = conn.cursor()

    # Modelo fixo para 80mm, ignora o banco
    modelo = '80mm'

    return gerar_pdf_comanda(cursor, username, mesa_numero, nome_tabela, modelo)


@app.route('/espettocarioca/configuracoes', methods=['GET', 'POST'])
@login_required
def espettocarioca_configuracoes():
    conn = sqlite3.connect('databases/user_databases/espetocarioca.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        # Salva número de mesas no banco
        numero_de_mesas = int(request.form['numero_de_mesas'])
        cursor.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)",
                       ('numero_de_mesas', str(numero_de_mesas)))

        # Salva modelo de impressão fixo como 80mm
        modelo = '80mm'
        cursor.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)",
                       ('modelo_impressao', modelo))

        conn.commit()
        flash(f'Configurações atualizadas: {numero_de_mesas} mesas e modelo {modelo}', 'success')
        return redirect(url_for('espettocarioca_configuracoes'))

    # Se for GET, busca número de mesas e fixa modelo 80mm
    cursor.execute("SELECT valor FROM configuracoes WHERE chave = 'numero_de_mesas'")
    resultado = cursor.fetchone()
    numero_de_mesas = int(resultado[0]) if resultado else 10  # padrão 10 mesas

    modelo_impressao = '80mm'  # fixa 80mm

    username = session.get('username', 'Usuário')  # pega username da sessão, ou valor padrão

    conn.close()
    return render_template('espetocarioca/configuracoes.html',
                           numero_de_mesas=numero_de_mesas,
                           modelo_impressao=modelo_impressao,
                           username=username)
@app.context_processor
def inject_numero_de_mesas():
    conn = sqlite3.connect('databases/user_databases/espetocarioca.db')
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracoes WHERE chave = 'numero_de_mesas'")
    result = cursor.fetchone()
    conn.close()
    numero_de_mesas = int(result[0]) if result else 0
    return dict(numero_de_mesas=numero_de_mesas)


def get_numero_de_mesas():
    conn = sqlite3.connect('databases/user_databases/espetocarioca.db')
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM configuracoes WHERE chave = 'numero_de_mesas'")
    result = cursor.fetchone()
    conn.close()
    return int(result[0]) if result else 0

# Registra a função para usar no template Jinja
app.jinja_env.globals.update(get_numero_de_mesas=get_numero_de_mesas)

def jinja_min(a, b):
    return min(a, b)

app.jinja_env.globals.update(jinja_min=jinja_min)


# ... o resto do seu código ...

from app import app  # Importa a instância do Flask do app.py

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
