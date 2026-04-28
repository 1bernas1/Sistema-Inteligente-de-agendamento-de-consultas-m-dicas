import mysql.connector
import hashlib

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="base_de_dados_medica"
)

cursor = db.cursor(dictionary=True)

def encriptar(palavra):
    return hashlib.sha256(palavra.encode()).hexdigest()

def input_ou_voltar(msg):
    valor = input(msg).strip()
    return None if valor in ("0", "") else valor

#__________Registo Utilizador__________
def registar():
    print("\nRegisto (0 para voltar)")
    nome  = input_ou_voltar("Nome: ")
    if nome  is None: return
    email = input_ou_voltar("Email: ")
    if email is None: return
    idade = input_ou_voltar("Idade: ")
    if idade is None or not idade.isdigit():
        print("Idade inválida!")
        return
    senha = input_ou_voltar("Senha: ")
    if senha is None: return
    try:
        cursor.execute(
            "INSERT INTO utilizadores (nome, email, idade, password) VALUES (%s,%s,%s,%s)",
            (nome, email, int(idade), encriptar(senha))
        )
        db.commit()
        print("Utilizador registado!")
    except Exception as e:
        print("Erro ao registar:", e)

#__________Login Utilizador / Médico / Admin__________
def login():
    print("\nLogin (0 para voltar)")
    nome  = input_ou_voltar("Nome: ")
    if nome  is None: return None
    senha = input_ou_voltar("Senha: ")
    if senha is None: return None
    h = encriptar(senha)

    cursor.execute("SELECT * FROM utilizadores WHERE nome=%s AND password=%s", (nome, h))
    u = cursor.fetchone()
    if u:
        u["tipo"] = "admin" if u["nome"].lower() == "admin" else "utilizador"
        print("Login efetuado!")
        return u

    cursor.execute("SELECT * FROM medicos WHERE nome=%s AND password=%s", (nome, h))
    m = cursor.fetchone()
    if m:
        m["tipo"] = "medico"
        print("Login médico!")
        return m

    print("Login falhou! Verifique nome ou senha")
    return None

#__________Menu Principal__________
def principal():
    while True:
        print("\n1 Registar")
        print("2 Login")
        print("3 Sair")
        op = input("Escolha: ").strip()
        if   op == "1": registar()
        elif op == "2":
            usuario = login()
            if usuario:
                print(f"Bem-vindo {usuario['nome']} ({usuario['tipo']})")
        elif op == "3": break
        else: print("Opção inválida!")

if __name__ == "__main__":
    principal()