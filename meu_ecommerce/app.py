# from flask import Flask, render_template, request, redirect, url_for, session
# import sqlite3
# import datetime
# import os
# import random

# app = Flask(__name__)
# app.secret_key = 'chave_secreta_padrao'

# # --- CONFIGURAÇÃO DO BANCO DE DADOS ---
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DB_PATH = os.path.join(BASE_DIR, "database.db")

# def get_db_connection():
#     conn = sqlite3.connect(DB_PATH)
#     conn.row_factory = sqlite3.Row
#     return conn

# def init_db():
#     conn = get_db_connection()
#     # Criação das tabelas caso não existam
#     conn.execute('CREATE TABLE IF NOT EXISTS vendas (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, valor REAL, data TEXT, chave_nfce TEXT, forma_pagamento TEXT)')
#     conn.execute('CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, email TEXT, telefone TEXT, whatsapp TEXT, cep TEXT, logradouro TEXT, numero TEXT, complemento TEXT, bairro TEXT, cidade TEXT, uf TEXT, data_nasc TEXT, genero TEXT)')
#     conn.execute('CREATE TABLE IF NOT EXISTS produtos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, preco REAL, quantidade INTEGER, cor_primaria TEXT, cor_secundaria TEXT)')
    
#     # NOVA TABELA: Vincula os itens vendidos à tabela principal de vendas
#     conn.execute('''
#         CREATE TABLE IF NOT EXISTS venda_itens (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             venda_id INTEGER,
#             produto_nome TEXT,
#             quantidade INTEGER,
#             preco_unitario REAL,
#             FOREIGN KEY(venda_id) REFERENCES vendas(id)
#         )
#     ''')
    
#     # Popula dados iniciais padrão se a tabela de clientes estiver vazia
#     if not conn.execute("SELECT 1 FROM clientes LIMIT 1").fetchone():
#         conn.execute("INSERT INTO clientes (nome) VALUES ('CONSUMIDOR NÃO IDENTIFICADO')")
#         conn.execute("INSERT INTO produtos (nome, preco, quantidade, cor_primaria, cor_secundaria) VALUES ('Camiseta Preta Basica', 49.90, 20, '#000000', '#ffffff')")
#         conn.execute("INSERT INTO produtos (nome, preco, quantidade, cor_primaria, cor_secundaria) VALUES ('Bone Aba Curva Azul', 89.90, 5, '#0000ff', '')")
    
#     conn.commit()
#     conn.close()

# # --- ROTAS ---

# @app.route('/')
# def index():
#     return redirect(url_for('login'))

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         if request.form.get('username') == 'admin' and request.form.get('password') == 'admin':
#             return redirect(url_for('alterar_senha'))
        
#         session['logged_in'] = True
#         return redirect(url_for('admin'))
#     return render_template('login.html')

# @app.route('/admin')
# def admin():
#     if 'logged_in' not in session: return redirect(url_for('login'))
    
#     dia = request.args.get('dia')
#     mes = request.args.get('mes')
#     annot = request.args.get('ano')
    
#     conn = get_db_connection()
#     query = "SELECT * FROM vendas WHERE 1=1"
#     params = []

#     if dia:
#         query += " AND strftime('%d', data) = ?"
#         params.append(dia.zfill(2))
#     if mes:
#         query += " AND strftime('%m', data) = ?"
#         params.append(mes.zfill(2))
#     if annot:
#         query += " AND strftime('%Y', data) = ?"
#         params.append(annot)
        
#     query += " ORDER BY id DESC"
#     vendas = conn.execute(query, params).fetchall()

#     total_vendas = len(vendas)
#     faturamento_total = sum(v['valor'] for v in vendas)
#     faturamento_dinheiro = sum(v['valor'] for v in vendas if v['forma_pagamento'] == 'Dinheiro')
#     faturamento_pix = sum(v['valor'] for v in vendas if v['forma_pagamento'] == 'Pix')
#     faturamento_credito = sum(v['valor'] for v in vendas if v['forma_pagamento'] == 'Credito')
#     faturamento_debito = sum(v['valor'] for v in vendas if v['forma_pagamento'] == 'Debito')
    
#     conn.close()
    
#     return render_template('admin.html', 
#                            vendas=vendas, 
#                            total_vendas=total_vendas,
#                            faturamento_total=faturamento_total,
#                            faturamento_dinheiro=faturamento_dinheiro,
#                            faturamento_pix=faturamento_pix,
#                            faturamento_credito=faturamento_credito,
#                            faturamento_debito=faturamento_debito,
#                            active_page='admin')

# # --- EMITIR CUPOM (VISÃO DO ADMIN) ---
# @app.route('/emitir_cupom/<int:venda_id>')
# def emitir_cupom(venda_id):
#     if 'logged_in' not in session: return redirect(url_for('login'))
    
#     conn = get_db_connection()
#     venda_row = conn.execute("SELECT * FROM vendas WHERE id = ?", (venda_id,)).fetchone()
    
#     if not venda_row:
#         conn.close()
#         return "Venda não encontrada.", 404
    
#     cliente = conn.execute("SELECT whatsapp FROM clientes WHERE nome = ?", (venda_row['cliente'],)).fetchone()
#     whatsapp = cliente['whatsapp'] if cliente and cliente['whatsapp'] else ""
    
#     venda_dados = list(venda_row) + [whatsapp]
    
#     # Coleta os itens reais salvos no banco mapeando os índices para o HTML atual
#     itens = conn.execute("SELECT id, venda_id, produto_nome, quantidade, preco_unitario FROM venda_itens WHERE venda_id = ?", (venda_id,)).fetchall()
    
#     conn.close()
#     return render_template('modelo_nf.html', venda=venda_dados, itens=itens, modo_publico=False)

# # --- ACESSO PÚBLICO AO CUPOM (USADO NO WHATSAPP) ---
# @app.route('/cupom/<chave_nfce>')
# def cupom_publico(chave_nfce):
#     conn = get_db_connection()
#     venda_row = conn.execute("SELECT * FROM vendas WHERE chave_nfce = ?", (chave_nfce,)).fetchone()
    
#     if not venda_row:
#         conn.close()
#         return "Cupom não encontrado.", 404
        
#     cliente = conn.execute("SELECT whatsapp FROM clientes WHERE nome = ?", (venda_row['cliente'],)).fetchone()
#     whatsapp = cliente['whatsapp'] if cliente and cliente['whatsapp'] else ""
    
#     venda_dados = list(venda_row) + [whatsapp]
    
#     # Coleta os itens reais salvos no banco vinculados a esta venda
#     itens = conn.execute("SELECT id, venda_id, produto_nome, quantidade, preco_unitario FROM venda_itens WHERE venda_id = ?", (venda_row['id'],)).fetchall()
    
#     conn.close()
#     return render_template('modelo_nf.html', venda=venda_dados, itens=itens, modo_publico=True)

# @app.route('/caixa')
# def caixa():
#     if 'logged_in' not in session: return redirect(url_for('login'))
    
#     conn = get_db_connection()
#     clientes = conn.execute("SELECT nome FROM clientes ORDER BY nome ASC").fetchall()
#     produtos = conn.execute("SELECT id, nome, preco, quantidade, cor_primaria, cor_secundaria FROM produtos ORDER BY nome ASC").fetchall()
#     conn.close()
    
#     return render_template('caixa.html', clientes=clientes, produtos=produtos, active_page='caixa')

# @app.route('/registrar_venda', methods=['POST'])
# def registrar_venda():
#     if 'logged_in' not in session: return redirect(url_for('login'))
    
#     nome_cliente = request.form.get('nome_cliente')
#     forma_pagamento = request.form.get('forma_pagamento')
    
#     lista_produtos = request.form.getlist('produtos[]')
#     lista_qtds = request.form.getlist('qtd[]')
#     lista_precos = request.form.getlist('preco[]')
    
#     if not lista_produtos or lista_produtos[0] == "":
#         return render_template('caixa.html', error="Não é possível processar uma venda sem itens.", active_page='caixa')
        
#     conn = get_db_connection()
    
#     try:
#         # Calcular valor total consolidado primeiro
#         valor_total = 0.0
#         for i in range(len(lista_produtos)):
#             if not lista_produtos[i]: continue
#             qtd = int(lista_qtds[i])
#             preco_unit = float(lista_precos[i])
#             valor_total += (qtd * preco_unit)
            
#         chave_nfce = "".join([str(random.randint(0, 9)) for _ in range(44)])
#         data_venda = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
#         # 1. Cria o registro da Venda principal
#         cursor = conn.execute("INSERT INTO vendas (cliente, valor, data, chave_nfce, forma_pagamento) VALUES (?, ?, ?, ?, ?)",
#                      (nome_cliente, valor_total, data_venda, chave_nfce, forma_pagamento))
#         venda_id = cursor.lastrowid
        
#         # 2. Insere os itens individuais associados a essa venda e atualiza o estoque
#         for i in range(len(lista_produtos)):
#             if not lista_produtos[i]: continue
            
#             nome_prod = lista_produtos[i]
#             qtd = int(lista_qtds[i])
#             preco_unit = float(lista_precos[i])
            
#             conn.execute("INSERT INTO venda_itens (venda_id, produto_nome, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
#                                  (venda_id, nome_prod, qtd, preco_unit))
#             conn.execute("UPDATE produtos SET quantidade = quantidade - ? WHERE nome = ?", (qtd, nome_prod))
            
#         conn.commit()
#     except Exception as e:
#         conn.rollback()
#         return f"Erro ao registrar venda: {e}", 500
#     finally:
#         conn.close()
        
#     return redirect(url_for('admin'))

# @app.route('/cliente')
# def cliente():
#     if 'logged_in' not in session: return redirect(url_for('login'))
#     conn = get_db_connection()
#     clientes = conn.execute("SELECT * FROM clientes").fetchall()
#     conn.close()
#     return render_template('cliente.html', clientes=clientes, active_page='cliente')

# @app.route('/add_cliente', methods=['POST'])
# def add_cliente():
#     if 'logged_in' not in session: return redirect(url_for('login'))
    
#     nome = request.form.get('nome')
#     email = request.form.get('email')
#     telefone = request.form.get('telefone')
#     whatsapp = request.form.get('whatsapp')
#     cep = request.form.get('cep')
#     logradouro = request.form.get('logradouro')
#     numero = request.form.get('numero')
#     complemento = request.form.get('complemento')
#     bairro = request.form.get('bairro')
#     city = request.form.get('cidade')
#     uf = request.form.get('uf')
#     data_nasc = request.form.get('data_nasc')
#     genero = request.form.get('genero')
    
#     conn = get_db_connection()
#     try:
#         conn.execute('''
#             INSERT INTO clientes (nome, email, telefone, whatsapp, cep, logradouro, numero, complemento, bairro, cidade, uf, data_nasc, genero)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', (nome, email, telefone, whatsapp, cep, logradouro, numero, complemento, bairro, city, uf, data_nasc, genero))
#         conn.commit()
#     except Exception as e:
#         conn.rollback()
#         return f"Erro ao cadastrar cliente: {e}", 500
#     finally:
#         conn.close()
        
#     return redirect(url_for('cliente'))

# # --- ROTAS DE PRODUTOS ---

# @app.route('/produto')
# def produto():
#     if 'logged_in' not in session: return redirect(url_for('login'))
#     conn = get_db_connection()
#     produtos = conn.execute("SELECT * FROM produtos").fetchall()
#     conn.close()
#     return render_template('produto.html', produtos=produtos, active_page='produto')

# @app.route('/add_produto', methods=['POST'])
# def add_produto():
#     if 'logged_in' not in session: return redirect(url_for('login'))
    
#     nome = request.form.get('nome')
#     preco = float(request.form.get('preco'))
#     quantidade = int(request.form.get('quantidade'))
#     cor_primaria = request.form.get('cor_primaria')
#     cor_secundaria = request.form.get('cor_secundaria')
    
#     conn = get_db_connection()
#     try:
#         conn.execute('''
#             INSERT INTO produtos (nome, preco, quantidade, cor_primaria, cor_secundaria)
#             VALUES (?, ?, ?, ?, ?)
#         ''', (nome, preco, quantidade, cor_primaria, cor_secundaria))
#         conn.commit()
#     except Exception as e:
#         conn.rollback()
#         return f"Erro ao adicionar produto: {e}", 500
#     finally:
#         conn.close()
        
#     return redirect(url_for('produto'))

# @app.route('/remover_produto', methods=['POST'])
# def remover_produto():
#     if 'logged_in' not in session: return redirect(url_for('login'))
    
#     produto_id = request.form.get('produto_id')
    
#     conn = get_db_connection()
#     try:
#         conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
#         conn.commit()
#     except Exception as e:
#         conn.rollback()
#         return f"Erro ao remover produto: {e}", 500
#     finally:
#         conn.close()
        
#     return redirect(url_for('produto'))

# # --- OUTRAS ROTAS ---

# @app.route('/alterar_senha', methods=['GET', 'POST'])
# def alterar_senha():
#     if request.method == 'POST':
#         nova_senha = request.form.get('nova_senha')
#         confirmar_senha = request.form.get('confirmar_senha')
        
#         if nova_senha != confirmar_senha:
#             return render_template('alterar_senha.html', error="As senhas informadas não coincidem!")
            
#         session['logged_in'] = True
#         return redirect(url_for('admin'))
#     return render_template('alterar_senha.html')

# @app.route('/remover_venda/<int:venda_id>', methods=['POST'])
# def remover_venda(venda_id):
#     if 'logged_in' not in session: return redirect(url_for('login'))
#     conn = get_db_connection()
#     conn.execute("DELETE FROM vendas WHERE id = ?", (venda_id,))
#     conn.execute("DELETE FROM venda_itens WHERE venda_id = ?", (venda_id,))
#     conn.commit()
#     conn.close()
#     return redirect(url_for('admin'))

# @app.route('/logout')
# def logout():
#     session.pop('logged_in', None)
#     return redirect(url_for('login'))

# if __name__ == '__main__':
#     init_db()
#     app.run(debug=True)

from flask import Flask, render_template, request, redirect, url_for, session
import datetime
import os
import random
import gspread # Biblioteca para o Google Sheets

app = Flask(__name__)
app.secret_key = 'chave_secreta_padrao'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --- CONFIGURAÇÃO DO GOOGLE SHEETS ---
def get_spreadsheet():
    # Carrega o arquivo JSON de credenciais que você baixa do Google Cloud
    cred_path = os.path.join(BASE_DIR, "credentials.json")
    gc = gspread.service_account(filename=cred_path)
    
    # Abre a planilha pelo nome exato dela no seu Google Drive
    return gc.open("Nome_Da_Sua_Planilha")

def init_sheets():
    """Garante que as abas existam e tenham os cabeçalhos corretos"""
    try:
        sh = get_spreadsheet()
        
        abas_necessarias = {
            "vendas": ["id", "cliente", "valor", "data", "chave_nfce", "forma_pagamento"],
            "clientes": ["id", "nome", "email", "telefone", "whatsapp", "cep", "logradouro", "numero", "complemento", "bairro", "cidade", "uf", "data_nasc", "genero"],
            "produtos": ["id", "nome", "preco", "quantidade", "cor_primaria", "cor_secundaria"],
            "venda_itens": ["id", "venda_id", "produto_nome", "quantidade", "preco_unitario"]
        }
        
        for nome_aba, colunas in abas_necessarias.items():
            try:
                sh.worksheet(nome_aba)
            except gspread.exceptions.WorksheetNotFound:
                # Se a aba não existir, cria e adiciona a primeira linha (cabeçalho)
                ws = sh.add_worksheet(title=nome_aba, rows="100", cols=str(len(colunas)))
                ws.append_row(colunas)
                
                # Popula dados iniciais caso seja uma aba nova
                if nome_aba == "clientes":
                    ws.append_row(["1", "CONSUMIDOR NÃO IDENTIFICADO"])
                elif nome_aba == "produtos":
                    ws.append_row(["1", "Camiseta Preta Basica", "49.90", "20", "#000000", "#ffffff"])
                    ws.append_row(["2", "Bone Aba Curva Azul", "89.90", "5", "#0000ff", ""])
    except Exception as e:
        print(f"Aviso ao inicializar planilhas: {e}. Certifique-se de que o arquivo 'credentials.json' existe.")

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
    
    sh = get_spreadsheet()
    vendas_aba = sh.worksheet("vendas")
    todas_vendas = vendas_aba.get_all_records() # Retorna uma lista de dicionários

    # Filtragem dos dados usando Python puro (substituindo o SQL)
    vendas_filtradas = []
    for v in todas_vendas:
        # Exemplo de data no Sheets: "2026-06-20 15:30:00"
        data_str = str(v.get('data', ''))
        try:
            partes_data = data_str.split(" ")[0].split("-") # ['2026', '06', '20']
            ano_v, mes_v, dia_v = partes_data[0], partes_data[1], partes_data[2]
        except:
            ano_v, mes_v, dia_v = "", "", ""

        if dia and dia.zfill(2) != dia_v: continue
        if mes and mes.zfill(2) != mes_v: continue
        if annot and annot != ano_v: continue
        
        # Garante a tipagem correta para o HTML fazer as somas
        v['valor'] = float(v['valor']) if v['valor'] else 0.0
        vendas_filtradas.append(v)

    # Inverte a lista para mostrar as mais recentes primeiro (ORDER BY id DESC)
    vendas_filtradas.reverse()

    total_vendas = len(vendas_filtradas)
    faturamento_total = sum(v['valor'] for v in vendas_filtradas)
    faturamento_dinheiro = sum(v['valor'] for v in vendas_filtradas if v['forma_pagamento'] == 'Dinheiro')
    faturamento_pix = sum(v['valor'] for v in vendas_filtradas if v['forma_pagamento'] == 'Pix')
    faturamento_credito = sum(v['valor'] for v in vendas_filtradas if v['forma_pagamento'] == 'Credito')
    faturamento_debito = sum(v['valor'] for v in vendas_filtradas if v['forma_pagamento'] == 'Debito')
    
    return render_template('admin.html', 
                           vendas=vendas_filtradas, 
                           total_vendas=total_vendas,
                           faturamento_total=faturamento_total,
                           faturamento_dinheiro=faturamento_dinheiro,
                           faturamento_pix=faturamento_pix,
                           faturamento_credito=faturamento_credito,
                           faturamento_debito=faturamento_debito,
                           active_page='admin')

@app.route('/caixa')
def caixa():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    sh = get_spreadsheet()
    clientes = sh.worksheet("clientes").get_all_records()
    produtos = sh.worksheet("produtos").get_all_records()
    
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
        
    sh = get_spreadsheet()
    vendas_aba = sh.worksheet("vendas")
    itens_aba = sh.worksheet("venda_itens")
    produtos_aba = sh.worksheet("produtos")
    
    try:
        # Calcular valor total consolidado
        valor_total = 0.0
        for i in range(len(lista_produtos)):
            if not lista_produtos[i]: continue
            valor_total += int(lista_qtds[i]) * float(lista_precos[i])
            
        chave_nfce = "".join([str(random.randint(0, 9)) for _ in range(44)])
        data_venda = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Gerar ID Incremental para a Venda
        proximo_venda_id = len(vendas_aba.get_all_values()) # Total de linhas vira o próximo ID numérico
        
        # 1. Salva a Venda Principal
        vendas_aba.append_row([proximo_venda_id, nome_cliente, valor_total, data_venda, chave_nfce, forma_pagamento])
        
        # 2. Insere os itens individuais e atualiza a quantidade na aba de Produtos
        todos_produtos = produtos_aba.get_all_records()
        
        for i in range(len(lista_produtos)):
            if not lista_produtos[i]: continue
            
            nome_prod = lista_produtos[i]
            qtd = int(lista_qtds[i])
            preco_unit = float(lista_precos[i])
            proximo_item_id = len(itens_aba.get_all_values())
            
            # Salva o item vendido
            itens_aba.append_row([proximo_item_id, proximo_venda_id, nome_prod, qtd, preco_unit])
            
            # Atualiza o estoque procurando a linha do produto pelo nome
            for idx, prod in enumerate(todos_produtos, start=2): # Linha 1 é o cabeçalho, dados começam na 2
                if prod['nome'] == nome_prod:
                    estoque_atual = int(prod['quantidade'])
                    novo_estoque = estoque_atual - qtd
                    # Na tabela de produtos, 'quantidade' é a 4ª coluna (coluna D)
                    produtos_aba.update_cell(idx, 4, novo_estoque)
                    break
                    
    except Exception as e:
        return f"Erro ao registrar venda no Google Sheets: {e}", 500
        
    return redirect(url_for('admin'))

@app.route('/add_cliente', methods=['POST'])
def add_cliente():
    if 'logged_in' not in session: return redirect(url_for('login'))
    
    sh = get_spreadsheet()
    clientes_aba = sh.worksheet("clientes")
    proximo_id = len(clientes_aba.get_all_values())
    
    dados_cliente = [
        proximo_id, request.form.get('nome'), request.form.get('email'), request.form.get('telefone'),
        request.form.get('whatsapp'), request.form.get('cep'), request.form.get('logradouro'),
        request.form.get('numero'), request.form.get('complemento'), request.form.get('bairro'),
        request.form.get('cidade'), request.form.get('uf'), request.form.get('data_nasc'), request.form.get('genero')
    ]
    
    clientes_aba.append_row(dados_cliente)
    return redirect(url_for('caixa')) # Redireciona de volta para o caixa

# (As demais rotas como emitir_cupom seguem a mesma lógica de buscar com .get_all_records())

if __name__ == '__main__':
    init_sheets()
    app.run(debug=True)
