from urllib.request import urlopen
import re
import sys
import json
import argparse
import os

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
                    apostas.append(r)
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


def sorteio(apostas, resultado):
    output = 'Resultado: ' + '-'.join(resultado) + '\n\n'
    resultados = []
    for aposta in apostas:
        aposta_list = aposta.split('-')
        total = 0
        for i in resultado:
            for j in aposta_list:
                if i == j:
                    total += 1
        resultados.append((total, aposta))

    # Ordenar por acertos crescente
    # resultados.sort(key=lambda x: x[0], reverse=False)

    output += '[ ACERTOS ] | APOSTADO\n'
    for total, aposta in resultados:
        if total == 6:
            output += f'[{total}] | {aposta} >>> GANHOU A SENA!!! <<<\n'
        elif total == 5:
            output += f'[{total}] | {aposta} >>> QUINA\n'
        elif total == 4:
            output += f'[{total}] | {aposta} >>> QUADRA\n'
        else:
            output += f'[{total}] | {aposta}\n'

    # Resumo
    quadras = [r for r in resultados if r[0] == 4]
    quinas = [r for r in resultados if r[0] == 5]
    senas = [r for r in resultados if r[0] == 6]

    output += '\nRESUMO:\n'
    output += f'Quadras (4 acertos): {len(quadras)}\n'
    if quadras:
        output += '  Jogos: ' + ', '.join([f'{aposta} ({total})' for total, aposta in quadras]) + '\n'

    output += f'Quinas (5 acertos).: {len(quinas)}\n'
    if quinas:
        output += '  Jogos: ' + ', '.join([f'{aposta} ({total})' for total, aposta in quinas]) + '\n'

    output += f'Senas (6 acertos)..: {len(senas)}\n'
    if senas:
        output += '  Jogos: ' + ', '.join([f'{aposta} ({total})' for total, aposta in senas]) + '\n'

    output += '\n'

    return output


def main(concurso):
    apostas = getApostas()
    resultado = getResultado(concurso)

    output = sorteio(apostas, resultado)
    print(output)

    # Salvar o output em historico/historico_<concurso>.txt
    filename = f'historico/historico_{concurso}.txt'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(output)

    # Salvar o número do concurso em concurso.txt
    with open(FILE_CONCURSO, 'w') as f:
        f.write(str(concurso))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verificar resultados da Mega Sena.')
    parser.add_argument('concurso', type=int, nargs='?', help='Número do concurso a verificar (opcional)')
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
    main(concurso)
