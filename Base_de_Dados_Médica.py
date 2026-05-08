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

cursor = db.cursor(dictionary=True, buffered=True)

#__________Configuração Email___________


email_remetente = "alexandre.bernardo.santos@gmail.com"
email_senha  = "gafp jhan mtoy qeud"

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
        if hora is None:
            return None

        if not validar_hora(hora):
            print("Hora inválida! Use o formato HH:MM.")
            continue

        hora_obj = datetime.strptime(hora, "%H:%M").time()
        hora_min = datetime.strptime("09:00", "%H:%M").time()
        hora_max = datetime.strptime("18:00", "%H:%M").time()

        #________Verificar horário permitido_________

        if not (hora_min <= hora_obj <= hora_max):
            print("Só é possível marcar consultas entre as 09:00 e as 18:00.")
            continue

        #________Verificar se a hora já passou (apenas se a data for hoje)_________

        if data:
            data_obj = datetime.strptime(data, "%d/%m/%Y").date()
            agora = datetime.now()

            if data_obj == agora.date() and hora_obj <= agora.time():
                print(
                    f"Não é possível marcar em horas passadas! "
                    f"Hora atual: {agora.strftime('%H:%M')}"
                )
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
    while True:
        cursor.execute("SELECT * FROM utilizadores WHERE nome=%s", (nome,))
        if cursor.fetchone():
            print("Nome já cadastrado! Digite outro nome.")
            nome = input_ou_voltar("Nome: ")
            if nome is None: return
            continue
        break
    while True:
         idade = input_ou_voltar("Idade: ")
         if idade is None: return
         if not idade.isdigit():
             print("Idade inválida! Digite novamente.")
             idade = input_ou_voltar("Idade: ")
             continue
         break
    while True:
            genero = input_ou_voltar("Genero (M/F): ")
            if genero is None: return
            if genero.upper() not in ("M", "F"):
                print("Gênero inválido! Digite 'M' para masculino ou 'F' para feminino.")
                genero = input_ou_voltar("Genero (M/F): ")
                continue
            break
    while True:
        email = input_ou_voltar("Email: ")
        if email is None: return
        if "@" not in email or "." not in email:
            print("Email inválido! Digite um email válido.")
            email = input_ou_voltar("Email: ")
            continue
        break
    while True:
        cursor.execute("SELECT * FROM utilizadores WHERE email=%s", (email,))
        if cursor.fetchone():
            print("Email já cadastrado! Digite outro email.")
            email = input_ou_voltar("Email: ")
            if email is None: return
            continue
        break
    while True:
        cursor.execute("SELECT * FROM medicos WHERE email=%s", (email,))
        if cursor.fetchone():
            print("Email já cadastrado para um médico! Digite outro email.")
            email = input_ou_voltar("Email: ")
            if email is None: return
            continue
        break
    senha = input_ou_voltar("Senha: ")
    if senha is None: return
    try:
        cursor.execute(
            "INSERT INTO utilizadores (nome, idade, email, genero, password) VALUES (%s,%s,%s,%s,%s)",
            (nome, int(idade), email, genero, encriptar(senha))
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
    while True:
        idade = input_ou_voltar("Idade (idade entre 25 e 100): ")
        if idade is None: return
        if not idade.isdigit() or int(idade) < 25 or int(idade) > 100:
            print("Idade inválida! Digite novamente.")
            continue
        break
    while True:
        genero = input_ou_voltar("Genero (M/F): ")
        if genero is None: return
        if genero.upper() not in ("M", "F"):
            print("Gênero inválido! Digite 'M' para masculino ou 'F' para feminino.")
            continue
        break
    esp   = input_ou_voltar("Especialidade: ")
    if esp   is None: return
    genero = genero.upper()
    while True:
        email = input_ou_voltar("Email: ")
        if email is None: return
        if "@" not in email or "." not in email:
            print("Email inválido! Digite um email válido.")
            continue
        break
    senha = input_ou_voltar("Senha: ")
    if senha is None: return
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

    while True:
        nova_idade = input("Nova idade (idade entre 25 e 100): ").strip()
        if not nova_idade.isdigit() or int(nova_idade) < 25 or int(nova_idade) > 100:
            print("Digite uma idade válida ou deixe em branco para não alterar.")
            continue
        break
    
    novo_genero = input("Novo gênero (M/F): ").strip()
    while True:
        if novo_genero.upper() not in ("M", "F", ""):
            print("Gênero inválido! Digite 'M' para masculino, 'F' para feminino ou deixe em branco para não alterar.")
            novo_genero = input("Novo gênero (M/F): ").strip()
            continue
        break
    
    novo_email = input("Novo email (deve conter @): ").strip()
    while True:
        if novo_email and ("@" not in novo_email or "." not in novo_email):
            print("Email inválido! Digite um email válido ou deixe em branco para não alterar.")
            novo_email = input("Novo email: ").strip()
            continue
        break
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


#__________Listar Consultas Utilizador__________
def listar_consultas(usuario, estado=None):
    query = """
        SELECT c.*, m.nome AS medico
        FROM consultas c
        JOIN medicos m ON c.id_medico = m.id_medico
        WHERE c.id_utilizador=%s
    """
    params = [usuario["id_utilizador"]]
    if estado:
        query += " AND c.estado_consulta=%s"
        params.append(estado)
    cursor.execute(query, params)
    consultas = cursor.fetchall()
    if not consultas:
        print("Nenhuma consulta encontrada!")
        return []
    for c in consultas:
        data = datetime.strptime(str(c["data_consulta"]), "%Y-%m-%d").strftime("%d/%m/%Y")
        print(f"{c['id_consulta']} | {c['medico']} | {data} {c['hora_consulta']} "
              f"| {c['motivo_consulta']} | [{c['estado_consulta'].upper()}]")
    return consultas

#__________Menu Listar Consultas Utilizador por Estado__________

def menu_listar_consultas(usuario):
    while True:
        print("\nListar consultas por estado:")
        print("1 Agendadas")
        print("2 Realizadas")
        print("3 Canceladas")
        print("4 Todas")
        print("0 Voltar")
        op = input("Escolha: ").strip()
        estados = {"1": "agendada", "2": "realizada", "3": "cancelada", "4": None}
        if op in estados:
            listar_consultas(usuario, estados[op])
        elif op == "0":
            break
        else:
            print("Opção inválida!")

#__________Marcar Consulta__________

def marcar_consulta(usuario):
    if not listar_medicos():
        print("Não há médicos disponíveis para agendamento.")
        return
    medico = pedir_medico("ID do médico: ")
    if medico is None: return
    data = pedir_data("Data DD/MM/AAAA com horário entre 09:00 e 18:00: ")
    if data is None: return
    hora = pedir_hora("Hora HH:MM: ", data)
    if hora is None: return
    motivo = input_ou_voltar("Motivo: ") or ""

    data_mysql = datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")

    #________Verifica se médico está livre (apenas consultas agendadas ocupam o horário)_________

    cursor.execute("""
        SELECT * FROM consultas
        WHERE id_medico=%s AND data_consulta=%s AND hora_consulta=%s AND estado_consulta='agendada'
    """, (medico["id_medico"], data_mysql, hora))
    if cursor.fetchone():
        print("Médico ocupado neste horário! Escolha outro horário ou médico.")
        return

    try:
        cursor.execute("""
            INSERT INTO consultas (id_utilizador, id_medico, data_consulta, hora_consulta, motivo_consulta, estado_consulta)
            VALUES (%s,%s,%s,%s,%s,'agendada')
        """, (usuario["id_utilizador"], medico["id_medico"], data_mysql, hora, motivo))
        db.commit()
        consulta_id = cursor.lastrowid
        print(f"Consulta marcada com sucesso! (ID: {consulta_id})")
    except Exception as e:
        print("Erro ao marcar consulta:", e)
        return
    mensagem = f"Consulta marcada com Dr(a) {medico['nome']} em {data} às {hora}. Motivo: {motivo}"

    #________Envia email de confirmação ao utilizador_________

    try:
        msg = MIMEText(
            f"Olá {usuario['nome']},\n\n"
            f"A sua consulta foi marcada com sucesso!\n\n"
            f"Médico  : Dr(a) {medico['nome']}\n"
            f"Data    : {data}\n"
            f"Hora    : {hora}\n"
            f"Motivo  : {motivo}\n\n"
            f"Caso precise de cancelar ou alterar, aceda ao sistema.\n\n"
            f"Cumprimentos,\nSistema de Agendamento Médico", "plain"
        )
        msg["From"] = email_remetente
        msg["To"] = usuario["email"]
        msg["Subject"] = "Confirmação de Consulta Médica"
        servidor = smtplib.SMTP("smtp.gmail.com", 587)
        servidor.starttls()
        servidor.login(email_remetente, email_senha)
        servidor.sendmail(email_remetente, usuario["email"], msg.as_string())
        servidor.quit()
        print("Email de confirmação enviado!")
    except Exception as e:
        print("Erro ao enviar email:", e)

    #________Regista notificação na tabela notificacoes_________

    try:
        cursor.execute("""
            INSERT INTO notificacoes (id_utilizador, id_notificacao, mensagem, data_notificacao)
            VALUES (%s,%s,%s,%s)
        """, (usuario["id_utilizador"], consulta_id, mensagem, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        db.commit()
        print("Notificação registrada com sucesso!")
    except Exception as e:
        print("Erro ao registrar notificação:", e)

#__________Cancelar Consulta__________

def cancelar_consulta(usuario):
    # Mostra apenas consultas agendadas (as únicas que podem ser canceladas)
    if not listar_consultas(usuario, "agendada"):
        return
    consulta = pedir_id_consulta("ID da consulta para cancelar: ",
                                  id_utilizador=usuario["id_utilizador"], estado="agendada")
    if consulta is None: return
    try:
        cursor.execute(
            "UPDATE consultas SET estado_consulta='cancelada' WHERE id_consulta=%s",
            (consulta["id_consulta"],)
        )
        db.commit()
        print("Consulta cancelada com sucesso!")
    except Exception as e:
        print("Erro ao cancelar consulta:", e)

#__________Alterar Consulta__________

def alterar_consulta(usuario):
    # Só faz sentido alterar consultas agendadas
    if not listar_consultas(usuario, "agendada"):
        return
    consulta = pedir_id_consulta("ID da consulta para alterar: ",
                                  id_utilizador=usuario["id_utilizador"], estado="agendada")
    if consulta is None: return
    data = pedir_data("Nova data DD/MM/AAAA: ")
    if data is None: return
    hora = pedir_hora("Nova hora HH:MM: ", data)
    if hora is None: return

    data_mysql = datetime.strptime(data, "%d/%m/%Y").strftime("%Y-%m-%d")

    #________Verifica disponibilidade do médico no novo horário (ignora a própria consulta)_________

    cursor.execute("""
        SELECT * FROM consultas
        WHERE id_medico=%s AND data_consulta=%s AND hora_consulta=%s
          AND estado_consulta='agendada' AND id_consulta!=%s
    """, (consulta["id_medico"], data_mysql, hora, consulta["id_consulta"]))
    if cursor.fetchone():
        print("Médico ocupado neste horário! Escolha outro horário.")
        return
    try:
        cursor.execute("""
            UPDATE consultas SET data_consulta=%s, hora_consulta=%s
            WHERE id_consulta=%s
        """, (data_mysql, hora, consulta["id_consulta"]))
        db.commit()
        print("Consulta alterada com sucesso!")
    except Exception as e:
        print("Erro ao alterar consulta:", e)

#__________Disponibilidade Médico__________

def disponibilidade_medico():
    if not listar_medicos():
        print("Não há médicos cadastrados.")
        return
    medico = pedir_medico("ID do médico para verificar disponibilidade: ")
    if medico is None: return

    #________Apenas consultas agendadas representam horários ocupados___________

    cursor.execute(
        "SELECT data_consulta, hora_consulta FROM consultas WHERE id_medico=%s AND estado_consulta='agendada'",
        (medico["id_medico"],)
    )
    consultas = cursor.fetchall()
    if not consultas:
        print(f"O médico {medico['nome']} não tem consultas agendadas.")
        return
    print(f"Consultas agendadas de Dr(a) {medico['nome']}:")
    for c in consultas:
        data = datetime.strptime(str(c["data_consulta"]), "%Y-%m-%d").strftime("%d/%m/%Y")
        print(f"  - {data} às {c['hora_consulta']}")


#__________Listar Consultas Médico__________

def listar_consultas_medico(medico, estado=None):
    query = """
        SELECT c.*, u.nome AS paciente
        FROM consultas c
        JOIN utilizadores u ON c.id_utilizador = u.id_utilizador
        WHERE c.id_medico=%s
    """
    params = [medico["id_medico"]]
    if estado:
        query += " AND c.estado_consulta=%s"
        params.append(estado)
    cursor.execute(query, params)
    consultas = cursor.fetchall()
    if not consultas:
        print("Nenhuma consulta encontrada!")
        return []
    for c in consultas:
        data = datetime.strptime(str(c["data_consulta"]), "%Y-%m-%d").strftime("%d/%m/%Y")
        print(f"{c['id_consulta']} | {c['paciente']} | {data} {c['hora_consulta']} "
              f"| {c['motivo_consulta']} | [{c['estado_consulta'].upper()}]")
    return consultas

#__________Menu Listar Consultas Médico por Estado__________

def menu_listar_consultas_medico(medico):
    while True:
        print("\nListar consultas por estado:")
        print("1 Agendadas")
        print("2 Realizadas")
        print("3 Canceladas")
        print("4 Todas")
        print("0 Voltar")
        op = input("Escolha: ").strip()
        estados = {"1": "agendada", "2": "realizada", "3": "cancelada", "4": None}
        if op in estados:
            listar_consultas_medico(medico, estados[op])
        elif op == "0":
            break
        else:
            print("Opção inválida!")

#__________Ver Relatórios__________

def ver_relatorios(medico):
    cursor.execute("""
        SELECT r.*, u.nome AS paciente
        FROM relatorios r
        JOIN consultas c ON r.id_consulta = c.id_consulta
        JOIN utilizadores u ON c.id_utilizador = u.id_utilizador
        WHERE c.id_medico=%s
    """, (medico["id_medico"],))
    relatorios = cursor.fetchall()
    if not relatorios:
        print("Nenhum relatório encontrado!")
        return []
    for r in relatorios:
        data = datetime.strptime(str(r["data_relatorio"]), "%Y-%m-%d").strftime("%d/%m/%Y")
        print(f"{r['id_relatorio']} | {r['paciente']} | {data} | {r['descricao']}")
    return relatorios

#__________Adicionar Relatório__________

def adicionar_relatorio(medico):
    if not listar_consultas_medico(medico):
        print("Você não tem consultas para adicionar relatório.")
        return
    consulta = pedir_id_consulta("ID da consulta para adicionar relatório: ",
                                  id_medico=medico["id_medico"])
    if consulta is None: return

    #________Verifica se já existe relatório para esta consulta_________
    cursor.execute(
        "SELECT * FROM relatorios WHERE id_consulta=%s",
        (consulta["id_consulta"],)
    )
    if cursor.fetchone():
        print("Esta consulta já tem um relatório! Use a opção Alterar Relatório para o editar.")
        return

    descricao = input_ou_voltar("Descrição do relatório: ") or ""
    try:
        cursor.execute(
            "INSERT INTO relatorios (id_consulta, descricao, data_relatorio) VALUES (%s,%s,%s)",
            (consulta["id_consulta"], descricao, datetime.now().strftime("%Y-%m-%d"))
        )
        db.commit()
        print("Relatório adicionado com sucesso!")
    except Exception as e:
        print("Erro ao adicionar relatório:", e)

#__________Alterar Relatório__________

def alterar_relatorio(medico):
    if not ver_relatorios(medico):
        return
    while True:
        val = input_ou_voltar("ID do relatório para alterar: ")
        if val is None: return
        if not val.isdigit():
            print("ID inválido! Digite novamente.")
            continue
        cursor.execute(
            "SELECT r.* FROM relatorios r JOIN consultas c ON r.id_consulta=c.id_consulta "
            "WHERE r.id_relatorio=%s AND c.id_medico=%s", (val, medico["id_medico"])
        )
        relatorio = cursor.fetchone()
        if not relatorio:
            print("Relatório não encontrado! Digite novamente.")
            continue
        break
    descricao = input_ou_voltar("Nova descrição do relatório: ") or ""
    try:
        cursor.execute(
            "UPDATE relatorios SET descricao=%s WHERE id_relatorio=%s",
            (descricao, relatorio["id_relatorio"])
        )
        db.commit()
        print("Relatório alterado com sucesso!")
    except Exception as e:
        print("Erro ao alterar relatório:", e)

#__________Marcar Consulta como Realizada__________

def marcar_consulta_realizada(medico):
    if not listar_consultas_medico(medico, "agendada"):
        return
    consulta = pedir_id_consulta("ID da consulta para marcar como realizada: ",
                                  id_medico=medico["id_medico"], estado="agendada")
    if consulta is None: return
    try:
        cursor.execute(
            "UPDATE consultas SET estado_consulta='realizada' WHERE id_consulta=%s",
            (consulta["id_consulta"],)
        )
        db.commit()
        print("Consulta marcada como realizada com sucesso!")
    except Exception as e:
        print("Erro ao atualizar consulta:", e)


#__________Menu Utilizador__________

def menu_utilizador(usuario):
    while True:
        print(f"\nBem-vindo {usuario['nome']}")
        print("1 Marcar consulta")
        print("2 Listar consultas")
        print("3 Cancelar consulta")
        print("4 Alterar consulta")
        print("5 Disponibilidade médico")
        print("0 Sair")
        op = input("Escolha: ").strip()
        if   op == "1": marcar_consulta(usuario)
        elif op == "2": menu_listar_consultas(usuario)
        elif op == "3": cancelar_consulta(usuario)
        elif op == "4": alterar_consulta(usuario)
        elif op == "5": disponibilidade_medico()
        elif op == "0": break
        else: print("Opção inválida!")

#__________Menu Médico__________

def menu_medico(medico):
    while True:
        print(f"\nDr(a) {medico['nome']}")
        print("1 Ver consultas")
        print("2 Marcar consulta como realizada")
        print("3 Ver relatórios")
        print("4 Adicionar relatório")
        print("5 Alterar relatório")
        print("0 Sair")
        op = input("Escolha: ").strip()
        if   op == "1": menu_listar_consultas_medico(medico)
        elif op == "2": marcar_consulta_realizada(medico)
        elif op == "3": ver_relatorios(medico)
        elif op == "4": adicionar_relatorio(medico)
        elif op == "5": alterar_relatorio(medico)
        elif op == "0": break
        else: print("Opção inválida!")

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
                if   usuario["tipo"] == "admin":  menu_admin(usuario)
                elif usuario["tipo"] == "medico": menu_medico(usuario)
                else:                             menu_utilizador(usuario)
        elif op == "3": break
        else: print("Opção inválida!")

if __name__ == "__main__":
    principal()  