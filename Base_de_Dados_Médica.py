import mysql.connector
import hashlib
import smtplib
from datetime import datetime
from email.mime.text import MIMEText


#__________Conexão MySQL___________

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="base_de_dados_medica"
)

cursor = db.cursor(dictionary=True)

#__________Encriptar Senha__________
def encriptar(palavra):
    return hashlib.sha256(palavra.encode()).hexdigest()

#__________Input ou Voltar__________
def input_ou_voltar(msg):
    valor = input(msg).strip()
    return None if valor in ("0", "") else valor

#__________Validar Data__________
def validar_data(data):
    try:
        datetime.strptime(data, "%d/%m/%Y")
        return True
    except ValueError:
        return False

#__________Validar Hora__________
def validar_hora(hora):
    try:
        datetime.strptime(hora, "%H:%M")
        return True
    except ValueError:
        return False

#__________Pedir Data Válida__________
def pedir_data(msg):
    while True:
        data = input_ou_voltar(msg)
        if data is None: return None
        if not validar_data(data):
            print("Data inválida! Use o formato DD/MM/AAAA.")
            continue
        data_obj = datetime.strptime(data, "%d/%m/%Y").date()
        if data_obj < datetime.now().date():
            print(f"Não é possível marcar consultas nesta data! Escolha uma data futura. Data atual: {datetime.now().strftime('%d/%m/%Y')}")
            continue
        return data

#__________Pedir Hora Válida__________
def pedir_hora(msg, data=None):
    while True:
        hora = input_ou_voltar(msg)
        if hora is None: return None
        if not validar_hora(hora):
            print("Hora inválida! Use o formato HH:MM (00:00 a 23:59).")
            continue
        if data:
            data_obj = datetime.strptime(data, "%d/%m/%Y").date()
            hora_obj = datetime.strptime(hora, "%H:%M").time()
            if data_obj == datetime.now().date() and hora_obj <= datetime.now().time():
                print(f"Não é possível marcar consultas nesta hora!Escolha uma hora entre (09:00-18:00) Hora atual: {datetime.now().strftime('%H:%M')}")
                continue
        return hora

#__________Pedir ID de Consulta Válido__________
def pedir_id_consulta(msg, id_utilizador=None, id_medico=None, estado=None):
    while True:
        val = input_ou_voltar(msg)
        if val is None: return None
        if not val.isdigit():
            print("ID inválido! Digite novamente.")
            continue
        query = "SELECT * FROM consultas WHERE id_consulta=%s"
        params = [val]
        if id_utilizador: query += " AND id_utilizador=%s";  params.append(id_utilizador)
        if id_medico:     query += " AND id_medico=%s";      params.append(id_medico)
        if estado:        query += " AND estado_consulta=%s"; params.append(estado)
        cursor.execute(query, params)
        consulta = cursor.fetchone()
        if not consulta:
            print("Consulta não encontrada ou inválida! Digite novamente.")
            continue
        return consulta


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


#__________Criar Médico__________
def criar_medico():
    print("\nCriar Médico (0 para voltar)")
    nome  = input_ou_voltar("Nome: ")
    if nome  is None: return
    email = input_ou_voltar("Email: ")
    if email is None: return
    idade = input_ou_voltar("Idade: ")
    if idade is None: return
    senha = input_ou_voltar("Senha: ")
    if senha is None: return
    esp   = input_ou_voltar("Especialidade: ")
    if esp   is None: return
    genero = input_ou_voltar("Genero (M/F): ")
    if genero is None: return
    genero = genero.upper()
    try:
        cursor.execute(
            "INSERT INTO medicos (nome,email,idade,password,especialidade,genero) VALUES (%s,%s,%s,%s,%s,%s)",
            (nome, email, int(idade), encriptar(senha), esp, genero)
        )
        db.commit()
        print("Médico criado!")
    except Exception as e:
        print("Erro ao criar médico:", e)

#__________Listar Médicos__________
def listar_medicos():
    cursor.execute("SELECT * FROM medicos")
    medicos = cursor.fetchall()
    if not medicos:
        print("Nenhum médico cadastrado!")
        return []
    for m in medicos:
        titulo = "Dra" if m.get("genero") == "F" else "Dr"
        print(f"{m['id_medico']} - {titulo} {m['nome']} ({m['especialidade']})")
    return medicos

#__________Pedir ID de Médico Válido__________
def pedir_medico(msg):
    while True:
        val = input_ou_voltar(msg)
        if val is None: return None
        if not val.isdigit():
            print("ID inválido! Digite novamente.")
            continue
        cursor.execute("SELECT * FROM medicos WHERE id_medico=%s", (val,))
        medico = cursor.fetchone()
        if not medico:
            print("Médico não encontrado! Digite novamente.")
            continue
        return medico

#__________Alterar Médico__________
def alterar_medico():
    if not listar_medicos():
        print("Nenhum médico cadastrado para alterar.")
        return
    medico = pedir_medico("ID do médico para alterar: ")
    if medico is None: return

    novo_nome  = input("Novo nome: ").strip()
    nova_idade = input("Nova idade: ").strip()
    novo_genero = input("Novo gênero (M/F): ").strip()
    novo_email = input("Novo email: ").strip()
    nova_senha = input("Nova senha: ").strip()
    nova_esp   = input("Nova especialidade: ").strip()

    if novo_nome:  medico["nome"]         = novo_nome
    if nova_idade: medico["idade"]        = int(nova_idade)
    if novo_genero: medico["genero"]      = novo_genero.upper()
    if novo_email: medico["email"]       = novo_email
    if nova_senha: medico["password"]     = encriptar(nova_senha)
    if nova_esp:   medico["especialidade"] = nova_esp

    try:
        cursor.execute("""
            UPDATE medicos SET nome=%s, idade=%s, genero=%s, email=%s, password=%s, especialidade=%s
            WHERE id_medico=%s
        """, (medico["nome"], medico["idade"], medico["genero"], medico["email"],
              medico["password"], medico["especialidade"], medico["id_medico"]))
        db.commit()
        print("Médico alterado com sucesso!")
    except Exception as e:
        print("Erro ao alterar médico:", e)

#__________Apagar Médico__________
def apagar_medico():
    if not listar_medicos():
        print("Nenhum médico cadastrado para apagar.")
        return
    medico = pedir_medico("ID do médico para apagar: ")
    if medico is None: return
    if input(f"Apagar o médico {medico['nome']}? (s/n): ").strip().lower() != "s":
        print("Operação cancelada.")
        return
    try:
        cursor.execute("DELETE FROM medicos WHERE id_medico=%s", (medico["id_medico"],))
        db.commit()
        print("Médico apagado com sucesso!")
    except Exception as e:
        print("Erro ao apagar médico:", e)

#__________Menu Admin__________
def menu_admin(admin):
    while True:
        print("\nMenu ADMIN")
        print("1 Criar médico")
        print("2 Listar médicos")
        print("3 Alterar médico")
        print("4 Apagar médico")
        print("0 Sair")
        op = input("Escolha: ").strip()
        if   op == "1": criar_medico()
        elif op == "2": listar_medicos()
        elif op == "3": alterar_medico()
        elif op == "4": apagar_medico()
        elif op == "0": break
        else: print("Opção inválida!")

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
                if   usuario["tipo"] == "admin":  menu_admin(usuario)
                elif usuario["tipo"] == "medico": menu_medico(usuario)
                else:                             menu_utilizador(usuario)
        elif op == "3": break
        else: print("Opção inválida!")

if __name__ == "__main__":
    principal()  