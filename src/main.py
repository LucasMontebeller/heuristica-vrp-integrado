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
        # if arquivo != 'exp0_inicial.json':
        #     continue

        modelo = Modelo(dados)
        heuristica = Heuristica(modelo)
        max_exec = 2000
        
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

def salvar_resultados_sheets(solucoes: dict[str, dict], nome_planilha="resultados_rodadas_otimizacao"):
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

    for arquivo, resultados_heuristica in solucoes.items():
        for nome_heuristica, resultados in resultados_heuristica.items():
            df = pd.DataFrame({
                'Solução': resultados['solucoes'],
                'Tempo de Execução': resultados['media_tempos_execucao'],
                'Iterações': resultados['media_iteracoes'],
                'Iterações Convergencia': resultados['media_iteracoes_convergencia']
            })

            metrics_df = pd.DataFrame({
                'Métrica': ['Melhor Solução', 'Média da Solução', 'Desvio Padrão da Solução',
                            'Média Tempo Execução', 'Desvio Padrão Tempo Execução',
                            'Média Iterações', 'Desvio Padrão Iterações',
                            'Média Iterações Convergencia', 'Desvio Padrão Iterações Convergencia'],
                'Valor': [resultados['melhor_solucao'], resultados['media_solucao'], resultados['desvio_padrao_solucao'],
                          resultados['media_tempos_execucao'], resultados['desvio_padrao_tempos_execucao'],
                          resultados['media_iteracoes'], resultados['desvio_padrao_iteracoes'],
                          resultados['media_iteracoes_convergencia'], resultados['desvio_padrao_iteracoes_convergencia']]
            })
            df = pd.concat([df, metrics_df.set_index('Métrica').T.reset_index(drop=True)], ignore_index=True)
            df = df.replace({np.nan: ''})

            nome_aba = f"{arquivo[:30]}_{nome_heuristica[:30]}"
            try:
                aba = planilha.worksheet(nome_aba)
                aba.clear()
            except gspread.WorksheetNotFound:
                aba = planilha.add_worksheet(title=nome_aba, rows=df.shape[0], cols=df.shape[1])

            aba.update([df.columns.values.tolist()] + df.values.tolist())

    print(f"Resultados salvos na planilha '{nome_planilha}' do Google Sheets.")

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