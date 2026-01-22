import argparse
import os
import sys
from urllib.request import urlopen
import subprocess
from dotenv import load_dotenv
import os

load_dotenv()  # Carrega o .env
login = os.getenv('EMAIL_LOGIN')
password = os.getenv('EMAIL_PASSWORD')

FILE_CONCURSO = 'concurso.txt'
URL_CONCURSO = 'https://servicebus2.caixa.gov.br/portaldeloterias/api/megasena/'  # + concurso


def concurso_existe(concurso):
    url = URL_CONCURSO + str(concurso)
    try:
        with urlopen(url) as resp:
            return True
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description='Verificar concursos da Mega Sena sequencialmente.')
    parser.add_argument('concurso_inicial', type=int, nargs='?', help='Número do concurso inicial (opcional)')
    parser.add_argument('--email', type=str, action='append', help='Endereço de email para enviar o resultado (pode ser usado múltiplas vezes)')
    parser.add_argument('--login', type=str, help='Login do email do Gmail (ex: seuemail@gmail.com)')
    parser.add_argument('--senha', type=str, help='Senha do email do Gmail')
    args = parser.parse_args()

    # Se não fornecidos via argumentos, usar valores do .env
    if args.login is None:
        args.login = login
    if args.senha is None:
        args.senha = password

    concurso = args.concurso_inicial
    if concurso is None:
        # Tentar ler do arquivo concurso.txt
        if os.path.exists(FILE_CONCURSO):
            try:
                with open(FILE_CONCURSO, 'r') as f:
                    ultimo_concurso = int(f.read().strip())
                    concurso = ultimo_concurso + 1
            except (ValueError, IOError):
                print('Erro ao ler o arquivo concurso.txt. Forneça o número do concurso inicial.')
                sys.exit(1)
        else:
            print('Arquivo concurso.txt não encontrado. Forneça o número do concurso inicial.')
            sys.exit(1)

    print(f'Iniciando verificação a partir do concurso: {concurso}')

    while True:
        if not concurso_existe(concurso):
            print(f'Concurso {concurso} não encontrado. Finalizando verificação.')
            break

        print(f'Processando concurso {concurso}...')
        # Chamar mega.py com o concurso e parâmetros opcionais
        cmd = [sys.executable, 'mega.py', str(concurso)]
        if args.email:
            for e in args.email:
                cmd.extend(['--email', e])
        if args.login:
            cmd.extend(['--login', args.login])
        if args.senha:
            cmd.extend(['--senha', args.senha])
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print('Erro:', result.stderr)

        concurso += 1


if __name__ == '__main__':
    main()