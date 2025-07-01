import json
import os
import numpy as np
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from solver import Dados, Modelo, Heuristica
import gc

cplex_optimal = {
    "exp08_01.json": 16.238,
    "exp08_02.json": 12.185,
    "exp08_03.json": 14.238,
    "exp08_04.json": 14.222,
    "exp08_05.json": 11.170,
    "exp08_06.json": 10.014,
    "exp08_07.json": 6.677,

    "exp10_01.json": 18.238,
    "exp10_02.json": 14.185,
    "exp10_03.json": 15.238,
    "exp10_04.json": 16.223,
    "exp10_05.json": 13.170,
    "exp10_06.json": 11.930,
    "exp10_07.json": 8.107,

    "exp12_01.json": 23.290,
    "exp12_02.json": 17.561,
    "exp12_03.json": 20.290,
    "exp12_04.json": 18.890,
    "exp12_05.json": 16.545,
    "exp12_06.json": 15.406,
    "exp12_07.json": 10.402,

    "Mutz_G1_01.json": 32.2,
    "Mutz_G2_08": 17,
    "Mutz_G3_14": 10.9499,
    "Mutz_G4_16": 20.8249,
    "Mutz_G5_20": 32.5
    }

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

def execucao_heuristica_multiple_times(heuristica, valor_otimo, n_execucoes=10):
    solucoes = []
    tempos = []
    iteracoes_list = []

    for _ in range(n_execucoes):
        solucao, iteracoes, tempo_execucao = heuristica(valor_otimo=valor_otimo)

        solucoes.append(solucao.M)
        tempos.append(tempo_execucao)
        iteracoes_list.append(iteracoes)

    return {
        "solucoes": solucoes,
        "melhor_solucao": np.min(solucoes),
        "media_solucao": np.mean(solucoes),
        "desvio_padrao_solucao": np.std(solucoes),
        "media_tempos_execucao": np.mean(tempos),
        "desvio_padrao_tempos_execucao": np.std(tempos),
        "media_iteracoes": np.mean(iteracoes_list),
        "desvio_padrao_iteracoes": np.std(iteracoes_list),
    }

def executa_instancias(instancias: list[tuple[str, Dados]], n_execucoes=10) -> dict[str, dict]:
    solucoes = {}
    for arquivo, dados in instancias:
        if arquivo not in ('Mutz_G1_01.json'):
            continue
                
        tempo_limite = 10 # verificar
        modelo = Modelo(dados)
        valor_otimo = cplex_optimal[arquivo]
        
        print(f"Executando arquivo {arquivo} em até {tempo_limite} segundos")

        # Random Search
        heuristica_random  = Heuristica(modelo, tempo_limite)
        gc.collect()
        solucoes_random = execucao_heuristica_multiple_times(heuristica_random.random_search, n_execucoes=n_execucoes, valor_otimo=valor_otimo)

        # Simulated Annealing
        heuristica_annealing = Heuristica(modelo, tempo_limite)
        gc.collect()  # força coleta de lixo
        solucoes_annealing = execucao_heuristica_multiple_times(heuristica_annealing.simulated_annealing, n_execucoes=n_execucoes, valor_otimo=valor_otimo)

        solucoes[arquivo] = {
            "random_search": solucoes_random,
            "simulated_annealing": solucoes_annealing
            # "tabu_search": solucoes_tabu
        }

    return solucoes

def salvar_resultados(solucoes: dict[str, dict], nome_arquivo="resultados.json"):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(solucoes, f, ensure_ascii=False, indent=4)

def salvar_resultados_sheets(solucoes: dict[str, dict], nome_planilha="rs_sa_mutz_10seg"):
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
                "Desvio Padrão Iterações": resultados.get('desvio_padrao_iteracoes', '')
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
    solucoes = executa_instancias(dados, n_execucoes=10)
    salvar_resultados_sheets(solucoes)

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