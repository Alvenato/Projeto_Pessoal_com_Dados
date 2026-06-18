import sqlite3

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Criar tabelas necessárias
    cursor.execute('''CREATE TABLE IF NOT EXISTS vendas 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       cliente TEXT, 
                       valor REAL, 
                       data TEXT, 
                       chave_nfce TEXT, 
                       forma_pagamento TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS clientes 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       nome TEXT, email TEXT, telefone TEXT, whatsapp TEXT, 
                       cep TEXT, logradouro TEXT, numero TEXT, complemento TEXT, 
                       bairro TEXT, cidade TEXT, uf TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       nome TEXT, preco REAL, quantidade INTEGER, 
                       cor_primaria TEXT, cor_secundaria TEXT)''')
    
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    init_db()