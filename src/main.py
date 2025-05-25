import json
import os
import time
import numpy as np
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from solver import Dados, Modelo, Heuristica

def carregar_dados() -> list[tuple[str, Dados]]:
    pasta = "data"
    arquivos_json = [f for f in os.listdir(pasta) if f.endswith(".json")]
    
    dados_lista = []
    for arquivo in arquivos_json:
        caminho_completo = os.path.join(pasta, arquivo)
        try:
            with open(caminho_completo, "r", encoding="utf-8") as f:
                dados_json = json.load(f)
                dados_lista.append((arquivo, Dados(**dados_json)))
        except (json.JSONDecodeError, OSError, TypeError) as e:
            print(f"Erro ao carregar {arquivo}: {e}")
    
    return dados_lista

def execucao_heuristica_multiple_times(heuristica, max_exec=1000, n_execucoes=10):
    solucoes = []
    tempos = []
    iteracoes = []
    iteracoes_convergencia = []

    for _ in range(n_execucoes):
        inicio = time.time()
        solucao, iteracao, iteracao_convergencia = heuristica(max_exec=max_exec)
        tempo_execucao = time.time() - inicio

        solucoes.append(solucao.M)
        tempos.append(tempo_execucao)
        iteracoes.append(iteracao)
        iteracoes_convergencia.append(iteracao_convergencia)

    return {
        "solucoes": solucoes,
        "melhor_solucao": np.min(solucoes),
        "media_solucao": np.mean(solucoes),
        "desvio_padrao_solucao": np.std(solucoes),
        "media_tempos_execucao": np.mean(tempos),
        "desvio_padrao_tempos_execucao": np.std(tempos),
        "media_iteracoes": np.mean(iteracoes),
        "desvio_padrao_iteracoes": np.std(iteracoes),
        "media_iteracoes_convergencia": np.mean(iteracoes_convergencia),
        "desvio_padrao_iteracoes_convergencia": np.std(iteracoes_convergencia)
    }

def executa_instancias(instancias: list[tuple[str, Dados]], n_execucoes=10) -> dict[str, dict]:
    solucoes = {}
    for arquivo, dados in instancias:
        # if arquivo != 'exp08_01.json':
        #     continue
        
        modelo = Modelo(dados)
        heuristica = Heuristica(modelo)
        max_exec = 1000
        
        print(f"Executando arquivo {arquivo} {n_execucoes} vezes")
        solucoes_random = execucao_heuristica_multiple_times(heuristica.random_search, max_exec=max_exec, n_execucoes=n_execucoes)
        solucoes_annealing = execucao_heuristica_multiple_times(heuristica.simulated_annealing, max_exec=max_exec, n_execucoes=n_execucoes)
        solucoes_tabu = execucao_heuristica_multiple_times(heuristica.tabu_search, max_exec=max_exec, n_execucoes=n_execucoes)

        solucoes[arquivo] = {
            "random_search": solucoes_random,
            "simulated_annealing": solucoes_annealing,
            "tabu_search": solucoes_tabu
        }

    return solucoes

def salvar_resultados(solucoes: dict[str, dict], nome_arquivo="resultados.json"):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(solucoes, f, ensure_ascii=False, indent=4)

def salvar_resultados_sheets(solucoes: dict[str, dict], nome_planilha="resultados_100_exec"):
    credenciais_arquivo = 'googleconfig.json'
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]

    try:
        creds = Credentials.from_service_account_file(credenciais_arquivo, scopes=SCOPES)
        gc = gspread.authorize(creds)
    except Exception as e:
        print(f"Erro ao autenticar com a Google Sheets API: {e}")
        return

    try:
        try:
            planilha = gc.open(nome_planilha)
        except gspread.SpreadsheetNotFound:
            planilha = gc.create(nome_planilha)
            print(f"Planilha '{nome_planilha}' criada. Compartilhe com seu e-mail: {creds.service_account_email}")
        except Exception as e:
            print(f"Erro ao tentar abrir a planilha: {e}")
            return
        planilha.share("montebellerlucas@gmail.com", perm_type='user', role='writer')
    except Exception as e:
        print(f"Erro geral ao lidar com a planilha: {e}")
        return

    todas_linhas_resumo = []
    for arquivo, resultados_heuristica in solucoes.items():
        for nome_heuristica, resultados in resultados_heuristica.items():
            solucoes_individuais_list = resultados.get('solucoes', [])
            solucoes_individuais_str = ", ".join(map(str, solucoes_individuais_list))

            linha_resumo = {
                "Experimento": arquivo,
                "Heurística": nome_heuristica,
                "Soluções": solucoes_individuais_str,
                "Melhor Solução": resultados.get('melhor_solucao', ''),
                "Média Solução": resultados.get('media_solucao', ''),
                "Desvio Padrão Solução": resultados.get('desvio_padrao_solucao', ''),
                "Média Tempo de Execução": resultados.get('media_tempos_execucao', ''),
                "Desvio Padrão Tempo Execução": resultados.get('desvio_padrao_tempos_execucao', ''),
                "Média Iterações": resultados.get('media_iteracoes', ''),
                "Desvio Padrão Iterações": resultados.get('desvio_padrao_iteracoes', ''),
                "Média Iterações Convergência": resultados.get('media_iteracoes_convergencia', ''),
                "Desvio Padrão Iterações Convergência": resultados.get('desvio_padrao_iteracoes_convergencia', '')
            }

            todas_linhas_resumo.append(linha_resumo)

    df_final_resumo = pd.DataFrame(todas_linhas_resumo)
    df_final_resumo = df_final_resumo.replace({np.nan: '', None: ''})

    nome_aba = "Resultados"
    try:
        aba = planilha.worksheet(nome_aba)
        aba.clear()
    except gspread.WorksheetNotFound:
        aba = planilha.add_worksheet(title=nome_aba, rows=df_final_resumo.shape[0]+1, cols=df_final_resumo.shape[1])

    valores = [df_final_resumo.columns.tolist()] + df_final_resumo.values.tolist()
    aba.update(valores)

    print(f"Resultados resumidos (com lista individual) salvos na aba '{nome_aba}' da planilha '{nome_planilha}'.")


def main():
    dados = carregar_dados()
    solucoes = executa_instancias(dados, n_execucoes=1)
    # salvar_resultados_sheets(solucoes)
    print('')

    # for arquivo, resultado in solucoes.items():
    #     print(f"###### {arquivo} ######")
    #     for heuristica, resultado_heuristica in resultado.items():
    #         print(f"  {heuristica}:")
    #         print(f"    Média da solução: {resultado_heuristica['media_solucao']}")
    #         print(f"    Desvio padrão da solução: {resultado_heuristica['desvio_padrao_solucao']}")
    #         print(f"    Média das iterações: {resultado_heuristica['media_iteracoes']}")
    #         print(f"    Desvio padrão das iterações: {resultado_heuristica['desvio_padrao_iteracoes']}")
    #         print(f"    Média do tempo de execução: {resultado_heuristica['media_tempos_execucao']:.4f} segundos")
    #         print(f"    Desvio padrão do tempo de execução: {resultado_heuristica['desvio_padrao_tempos_execucao']:.4f} segundos")
    #         print(f"    Média de iterações até convergência: {resultado_heuristica['media_iteracoes_convergencia']}")
    #         print(f"    Desvio padrão de iterações até convergência: {resultado_heuristica['desvio_padrao_iteracoes_convergencia']}")
    #         print("\n")

if __name__ == "__main__":
    main()