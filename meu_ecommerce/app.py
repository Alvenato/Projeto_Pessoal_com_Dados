from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import datetime
import os
import random

app = Flask(__name__)
app.secret_key = 'chave_secreta_padrao'

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Criação das tabelas caso não existam
    conn.execute('CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, valor REAL, data TEXT, chave_nfce TEXT, forma_pagamento TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, email TEXT, telefone TEXT, whatsapp TEXT, cep TEXT, logradouro TEXT, numero TEXT, complemento TEXT, bairro TEXT, cidade TEXT, uf TEXT, data_nasc TEXT, genero TEXT)')
    conn.execute('CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, preco REAL, quantidade INTEGER, cor_primaria TEXT, cor_secundaria TEXT)')
    
    # NOVA TABELA: Vincula os itens vendidos à tabela principal de vendas
    conn.execute('''
        CREATE TABLE IF NOT EXISTS venda_itens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venda_id INTEGER,
            produto_nome TEXT,
            quantidade INTEGER,
            preco_unitario REAL,
            FOREIGN KEY(venda_id) REFERENCES vendas(id)
        )
    ''')
    
    # Popula dados iniciais padrão se a tabela de clientes estiver vazia
    if not conn.execute("SELECT 1 FROM clientes LIMIT 1").fetchone():
        conn.execute("INSERT INTO clientes (nome) VALUES ('CONSUMIDOR NÃO IDENTIFICADO')")
        conn.execute("INSERT INTO produtos (nome, preco, quantidade, cor_primaria, cor_secundaria) VALUES ('Camiseta Preta Basica', 49.90, 20, '#000000', '#ffffff')")
        conn.execute("INSERT INTO produtos (nome, preco, quantidade, cor_primaria, cor_secundaria) VALUES ('Bone Aba Curva Azul', 89.90, 5, '#0000ff', '')")
    
    conn.commit()
    conn.close()

# --- ROTAS ---

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form.get('username') == 'admin' and request.form.get('password') == 'admin':
            return redirect(url_for('alterar_senha'))
        
        session['logged_in'] = True
        return redirect(url_for('admin'))
    return render_template('login.html')

@app.route('/admin')
def admin():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    dia = request.args.get('dia')
    mes = request.args.get('mes')
    annot = request.args.get('ano')
    
    conn = get_db_connection()
    query = "SELECT * FROM vendas WHERE 1=1"
    params = []

    if dia:
        query += " AND strftime('%d', data) = ?"
        params.append(dia.zfill(2))
    if mes:
        query += " AND strftime('%m', data) = ?"
        params.append(mes.zfill(2))
    if annot:
        query += " AND strftime('%Y', data) = ?"
        params.append(annot)
        
    query += " ORDER BY id DESC"
    vendas = conn.execute(query, params).fetchall()

    total_vendas = len(vendas)
    faturamento_total = sum(v['valor'] for v in vendas)
    faturamento_dinheiro = sum(v['valor'] for v in vendas if v['forma_pagamento'] == 'Dinheiro')
    faturamento_pix = sum(v['valor'] for v in vendas if v['forma_pagamento'] == 'Pix')
    faturamento_credito = sum(v['valor'] for v in vendas if v['forma_pagamento'] == 'Credito')
    faturamento_debito = sum(v['valor'] for v in vendas if v['forma_pagamento'] == 'Debito')
    
    conn.close()
    
    return render_template('admin.html', 
                           vendas=vendas, 
                           total_vendas=total_vendas,
                           faturamento_total=faturamento_total,
                           faturamento_dinheiro=faturamento_dinheiro,
                           faturamento_pix=faturamento_pix,
                           faturamento_credito=faturamento_credito,
                           faturamento_debito=faturamento_debito,
                           active_page='admin')

# --- EMITIR CUPOM (VISÃO DO ADMIN) ---
@app.route('/emitir_cupom/<int:venda_id>')
def emitir_cupom(venda_id):
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    venda_row = conn.execute("SELECT * FROM vendas WHERE id = ?", (venda_id,)).fetchone()
    
    if not venda_row:
        conn.close()
        return "Venda não encontrada.", 404
    
    cliente = conn.execute("SELECT whatsapp FROM clientes WHERE nome = ?", (venda_row['cliente'],)).fetchone()
    whatsapp = cliente['whatsapp'] if cliente and cliente['whatsapp'] else ""
    
    venda_dados = list(venda_row) + [whatsapp]
    
    # Coleta os itens reais salvos no banco mapeando os índices para o HTML atual
    itens = conn.execute("SELECT id, venda_id, produto_nome, quantidade, preco_unitario FROM venda_itens WHERE venda_id = ?", (venda_id,)).fetchall()
    
    conn.close()
    return render_template('modelo_nf.html', venda=venda_dados, itens=itens, modo_publico=False)

# --- ACESSO PÚBLICO AO CUPOM (USADO NO WHATSAPP) ---
@app.route('/cupom/<chave_nfce>')
def cupom_publico(chave_nfce):
    conn = get_db_connection()
    venda_row = conn.execute("SELECT * FROM vendas WHERE chave_nfce = ?", (chave_nfce,)).fetchone()
    
    if not venda_row:
        conn.close()
        return "Cupom não encontrado.", 404
        
    cliente = conn.execute("SELECT whatsapp FROM clientes WHERE nome = ?", (venda_row['cliente'],)).fetchone()
    whatsapp = cliente['whatsapp'] if cliente and cliente['whatsapp'] else ""
    
    venda_dados = list(venda_row) + [whatsapp]
    
    # Coleta os itens reais salvos no banco vinculados a esta venda
    itens = conn.execute("SELECT id, venda_id, produto_nome, quantidade, preco_unitario FROM venda_itens WHERE venda_id = ?", (venda_row['id'],)).fetchall()
    
    conn.close()
    return render_template('modelo_nf.html', venda=venda_dados, itens=itens, modo_publico=True)

@app.route('/caixa')
def caixa():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    conn = get_db_connection()
    clientes = conn.execute("SELECT nome FROM clientes ORDER BY nome ASC").fetchall()
    produtos = conn.execute("SELECT id, nome, preco, quantidade, cor_primaria, cor_secundaria FROM produtos ORDER BY nome ASC").fetchall()
    conn.close()
    
    return render_template('caixa.html', clientes=clientes, produtos=produtos, active_page='caixa')

@app.route('/registrar_venda', methods=['POST'])
def registrar_venda():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    nome_cliente = request.form.get('nome_cliente')
    forma_pagamento = request.form.get('forma_pagamento')
    
    lista_produtos = request.form.getlist('produtos[]')
    lista_qtds = request.form.getlist('qtd[]')
    lista_precos = request.form.getlist('preco[]')
    
    if not lista_produtos or lista_produtos[0] == "":
        return render_template('caixa.html', error="Não é possível processar uma venda sem itens.", active_page='caixa')
        
    conn = get_db_connection()
    
    try:
        # Calcular valor total consolidado primeiro
        valor_total = 0.0
        for i in range(len(lista_produtos)):
            if not lista_produtos[i]: continue
            qtd = int(lista_qtds[i])
            preco_unit = float(lista_precos[i])
            valor_total += (qtd * preco_unit)
            
        chave_nfce = "".join([str(random.randint(0, 9)) for _ in range(44)])
        data_venda = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Cria o registro da Venda principal
        cursor = conn.execute("INSERT INTO vendas (cliente, valor, data, chave_nfce, forma_pagamento) VALUES (?, ?, ?, ?, ?)",
                     (nome_cliente, valor_total, data_venda, chave_nfce, forma_pagamento))
        venda_id = cursor.lastrowid
        
        # 2. Insere os itens individuais associados a essa venda e atualiza o estoque
        for i in range(len(lista_produtos)):
            if not lista_produtos[i]: continue
            
            nome_prod = lista_produtos[i]
            qtd = int(lista_qtds[i])
            preco_unit = float(lista_precos[i])
            
            conn.execute("INSERT INTO venda_itens (venda_id, produto_nome, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                                 (venda_id, nome_prod, qtd, preco_unit))
            conn.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE nome = ?", (qtd, nome_prod))
            
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f"Erro ao registrar venda: {e}", 500
    finally:
        conn.close()
        
    return redirect(url_for('admin'))

@app.route('/cliente')
def cliente():
    if 'logged_in' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    clientes = conn.execute("SELECT * FROM clientes").fetchall()
    conn.close()
    return render_template('cliente.html', clientes=clientes, active_page='cliente')

@app.route('/add_cliente', methods=['POST'])
def add_cliente():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    nome = request.form.get('nome')
    email = request.form.get('email')
    telefone = request.form.get('telefone')
    whatsapp = request.form.get('whatsapp')
    cep = request.form.get('cep')
    logradouro = request.form.get('logradouro')
    numero = request.form.get('numero')
    complemento = request.form.get('complemento')
    bairro = request.form.get('bairro')
    city = request.form.get('cidade')
    uf = request.form.get('uf')
    data_nasc = request.form.get('data_nasc')
    genero = request.form.get('genero')
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO clientes (nome, email, telefone, whatsapp, cep, logradouro, numero, complemento, bairro, cidade, uf, data_nasc, genero)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nome, email, telefone, whatsapp, cep, logradouro, numero, complemento, bairro, city, uf, data_nasc, genero))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f"Erro ao cadastrar cliente: {e}", 500
    finally:
        conn.close()
        
    return redirect(url_for('cliente'))

# --- ROTAS DE PRODUTOS ---

@app.route('/produto')
def produto():
    if 'logged_in' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    produtos = conn.execute("SELECT * FROM produtos").fetchall()
    conn.close()
    return render_template('produto.html', produtos=produtos, active_page='produto')

@app.route('/add_produto', methods=['POST'])
def add_produto():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    nome = request.form.get('nome')
    preco = float(request.form.get('preco'))
    quantidade = int(request.form.get('quantidade'))
    cor_primaria = request.form.get('cor_primaria')
    cor_secundaria = request.form.get('cor_secundaria')
    
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO produtos (nome, preco, quantidade, cor_primaria, cor_secundaria)
            VALUES (?, ?, ?, ?, ?)
        ''', (nome, preco, quantidade, cor_primaria, cor_secundaria))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f"Erro ao adicionar produto: {e}", 500
    finally:
        conn.close()
        
    return redirect(url_for('produto'))

@app.route('/remover_produto', methods=['POST'])
def remover_produto():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    produto_id = request.form.get('produto_id')
    
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return f"Erro ao remover produto: {e}", 500
    finally:
        conn.close()
        
    return redirect(url_for('produto'))

# --- OUTRAS ROTAS ---

@app.route('/alterar_senha', methods=['GET', 'POST'])
def alterar_senha():
    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')
        
        if nova_senha != confirmar_senha:
            return render_template('alterar_senha.html', error="As senhas informadas não coincidem!")
            
        session['logged_in'] = True
        return redirect(url_for('admin'))
    return render_template('alterar_senha.html')

@app.route('/remover_venda/<int:venda_id>', methods=['POST'])
def remover_venda(venda_id):
    if 'logged_in' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    conn.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
    conn.execute("DELETE FROM venda_itens WHERE venda_id = ?", (venda_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)