from urllib.request import urlopen
import re
import sys
import json
import argparse
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

FILE_APOSTAS = 'mega.txt'
FILE_CONCURSO = 'concurso.txt'
URL_CONCURSO = 'https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena/'  # + concurso

# https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena/2962
# https://loterias.caixa.gov.br/Paginas/Mega-Sena.aspx
# https://pt.stackoverflow.com/questions/47597/como-posso-pegar-os-resultados-das-loterias


def getApostas():
    apostas = []
    try:
        with open(FILE_APOSTAS, 'r', encoding='utf-8') as f:
            for r in f:
                r = r.strip()
                if r:
                    parts = r.split(' ', 1)
                    if len(parts) == 2:
                        aposta, nome = parts
                        apostas.append((aposta, nome))
                    else:
                        print(f'Linha inválida no arquivo {FILE_APOSTAS}: {r}')
    except FileNotFoundError:
        print(f'Arquivo {FILE_APOSTAS} não encontrado.')
        sys.exit(1)

    return apostas


def getResultado(concurso):
    url = URL_CONCURSO + str(concurso)
    try:
        with urlopen(url) as resp:
            raw = resp.read()
    except Exception as e:
        print('Erro ao acessar a URL:', e)
        sys.exit(1)
    # Resposta esperada em JSON; decodifica como UTF-8 e parseia
    try:
        text = raw.decode('utf-8')
    except Exception:
        try:
            text = raw.decode('iso-8859-1')
        except Exception as e:
            print('Erro ao decodificar resposta:', e)
            sys.exit(1)

    try:
        obj = json.loads(text)
    except Exception as e:
        print('Erro ao parsear JSON:', e)
        sys.exit(1)

    # Extrai as dezenas da chave 'listaDezenas'
    if not isinstance(obj, dict) or 'listaDezenas' not in obj:
        print("Formato JSON inesperado: chave 'listaDezenas' ausente.")
        sys.exit(1)

    lista = obj.get('listaDezenas')
    if not lista or not isinstance(lista, list):
        print("Nenhuma dezena encontrada em 'listaDezenas'.")
        sys.exit(0)

    # Garante strings com dois dígitos
    resultado = [str(d).zfill(2) for d in lista]

    return resultado


def enviar_email(remetente, senha, destinatario, assunto, corpo):
    try:
        # Configurar o servidor SMTP do Gmail
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(remetente, senha)

        # Criar a mensagem
        msg = MIMEMultipart()
        msg['From'] = remetente
        msg['To'] = destinatario
        msg['Subject'] = assunto

        # Anexar o corpo
        msg.attach(MIMEText(corpo, 'plain'))

        # Enviar o email
        servidor.sendmail(remetente, destinatario, msg.as_string())
        servidor.quit()
        print('Email enviado com sucesso!')
    except Exception as e:
        print(f'Erro ao enviar email: {e}')


def sorteio(apostas, resultado):
    output = 'Resultado: ' + '-'.join(resultado) + '\n\n'
    resultados = []
    for aposta, nome in apostas:
        aposta_list = aposta.split('-')
        total = 0
        for i in resultado:
            for j in aposta_list:
                if i == j:
                    total += 1
        resultados.append((total, aposta, nome))

    # Ordenar por acertos crescente
    # resultados.sort(key=lambda x: x[0], reverse=False)

    output += '[ACERTOS] | JOGOS\n'
    for total, aposta, nome in resultados:
        if total == 6:
            output += f'[{total}] | {aposta} ** MEGA-SENA ** ({nome})\n'
        elif total == 5:
            output += f'[{total}] | {aposta} ** QUINA ** ({nome})\n'
        elif total == 4:
            output += f'[{total}] | {aposta} ** QUADRA ** ({nome})\n'
        else:
            output += f'[{total}] | {aposta} ({nome})\n'

    # Resumo
    quadras = [r for r in resultados if r[0] == 4]
    quinas = [r for r in resultados if r[0] == 5]
    senas = [r for r in resultados if r[0] == 6]
    tres_acertos = [r for r in resultados if r[0] == 3]
    dois_acertos = [r for r in resultados if r[0] == 2]
    um_acerto = [r for r in resultados if r[0] == 1]

    output += '\nRESUMO:\n'
    output += f'[6] acertos (SENA)...: {len(senas)}'
    # output += f'Senas (6 acertos)..: {len(senas)}\n'
    # if senas:
    #     output += '  Jogos: ' + ', '.join([f'{aposta} ({total})' for total, aposta in senas]) + '\n'
    if len(senas) > 0:
        output += ' <<< Premiado!!!'

    output += f'\n[5] acertos (QUINA)..: {len(quinas)}'
    # if quinas:
    #     output += '  Jogos: ' + ', '.join([f'{aposta} ({total})' for total, aposta in quinas]) + '\n'
    if len(quinas) > 0:
        output += ' <<< Premiado!!!'

    output += f'\n[4] acertos (QUADRA).: {len(quadras)}'
    # if quadras:
    #     output += '  Jogos: ' + ', '.join([f'{aposta} ({total})' for total, aposta in quadras]) + '\n'
    if len(quadras) > 0:
        output += ' <<< Premiado!!!'

    output += f'\n[3] acertos..........: {len(tres_acertos)}'
    output += f'\n[2] acertos..........: {len(dois_acertos)}'
    output += f'\n[1] acerto...........: {len(um_acerto)}'
    output += '\n'

    premiado = len(quadras) > 0 or len(quinas) > 0 or len(senas) > 0

    return output, premiado


def main(concurso, email=None, senha=None, login=None):
    apostas = getApostas()
    resultado = getResultado(concurso)

    output, premiado = sorteio(apostas, resultado)
    print(output)

    # Salvar o output em historico/historico_<concurso>.txt
    filename = f'historico/historico_{concurso}.txt'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(output)

    # Se email fornecido, enviar email
    if email:
        print('Enviando resultado por e-mail para:', ', '.join(email))
        if not senha:
            print('Senha do email não fornecida.')
            sys.exit(1)
        if not login:
            print('Login do email não fornecido.')
            sys.exit(1)
        assunto_base = f'Resultado Mega-Sena: {concurso}'
        if premiado:
            assunto = f'>>PREMIADO<< {assunto_base}'
        else:
            assunto = assunto_base
        # Usar o output como corpo do email e usar senha de app do Gmail
        for destinatario in email:
            enviar_email(login, senha, destinatario, assunto, output)

    # Salvar o número do concurso em concurso.txt
    with open(FILE_CONCURSO, 'w') as f:
        f.write(str(concurso))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verificar resultados da Mega Sena.')
    parser.add_argument('concurso', type=int, nargs='?', help='Número do concurso a verificar (opcional)')
    parser.add_argument('--email', type=str, action='append', help='Endereço de email para enviar o resultado (pode ser usado múltiplas vezes)')
    parser.add_argument('--login', type=str, help='Login do email do Gmail (ex: seuemail@gmail.com)')
    parser.add_argument('--senha', type=str, help='Senha do email do Gmail')
    args = parser.parse_args()

    concurso = args.concurso
    if concurso is None:
        # Tentar ler do arquivo concurso.txt
        if os.path.exists(FILE_CONCURSO):
            try:
                with open(FILE_CONCURSO, 'r') as f:
                    ultimo_concurso = int(f.read().strip())
                    concurso = ultimo_concurso + 1
            except (ValueError, IOError):
                print('Erro ao ler o arquivo concurso.txt. Forneça o número do concurso.')
                sys.exit(1)
        else:
            print('Arquivo concurso.txt não encontrado. Forneça o número do concurso.')
            sys.exit(1)

    print('\nVerificar resultados do concurso:', concurso)
    main(concurso, args.email, args.senha, args.login)
