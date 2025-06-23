# utils/data_processor.py

import pandas as pd
import re
import os

def limpar_e_converter_preco(df):
    """
    Limpa a coluna 'Preço Bruto' de um DataFrame e cria uma coluna 'Preço Numérico' (float).
    Trata formatos de moeda comuns no Brasil (ponto para milhares, vírgula para decimais).
    """
    if df.empty or 'Preço Bruto' not in df.columns:
        # Retorna o DataFrame como está se estiver vazio ou não tiver a coluna 'Preço Bruto'
        print("Aviso: DataFrame vazio ou sem a coluna 'Preço Bruto' para limpeza.")
        df['Preço Numérico'] = None # Adiciona a coluna, mas com valores nulos
        return df

    df['Preço Bruto'] = df['Preço Bruto'].astype(str)

    def _limpar_preco_individual(preco_str):
        if not isinstance(preco_str, str):
            return None
        
        # Remove símbolos de moeda e espaços extras
        preco_str = preco_str.replace('R$', '').replace('US$', '').strip()

        # Tenta detectar e padronizar separadores
        # Ex: "1.234,56" -> "1234.56"
        # Ex: "1,234.56" -> "1234.56" (menos comum no Brasil)
        if ',' in preco_str and '.' in preco_str:
            # Se tiver ambos, assume que '.' é milhar e ',' é decimal (padrão BR)
            # Remove o ponto de milhar e troca a vírgula por ponto decimal
            preco_limpo = preco_str.replace('.', '').replace(',', '.')
        elif ',' in preco_str:
            # Se tiver só vírgula, assume que é decimal
            preco_limpo = preco_str.replace(',', '.')
        else:
            # Se não tiver vírgula, assume que o ponto já é decimal ou não tem decimal
            preco_limpo = preco_str
        
        # Remove qualquer caractere não numérico restante (exceto o ponto decimal)
        preco_limpo = re.sub(r'[^\d.]', '', preco_limpo)

        try:
            return float(preco_limpo)
        except ValueError:
            print(f"Não foi possível converter o preço: '{preco_str}' para numérico.")
            return None

    df['Preço Numérico'] = df['Preço Bruto'].apply(_limpar_preco_individual)
    
    return df

def carregar_dados_raspados(diretorio_dados="data"):
    """
    Carrega todos os arquivos CSV de um diretório e os concatena em um único DataFrame.
    """
    todos_os_dfs = []
    # Verifica se o diretório existe
    if not os.path.exists(diretorio_dados):
        print(f"Diretório de dados '{diretorio_dados}' não encontrado.")
        return pd.DataFrame() # Retorna DataFrame vazio se o diretório não existir

    for filename in os.listdir(diretorio_dados):
        if filename.endswith(".csv"):
            filepath = os.path.join(diretorio_dados, filename)
            try:
                # Tenta ler o CSV, considerando a codificação padrão
                df = pd.read_csv(filepath, encoding='utf-8')
                todos_os_dfs.append(df)
            except UnicodeDecodeError:
                # Se der erro de codificação, tenta 'latin1' ou outra
                try:
                    df = pd.read_csv(filepath, encoding='latin1')
                    todos_os_dfs.append(df)
                except Exception as e:
                    print(f"Erro de decodificação ao carregar {filepath}: {e}")
            except Exception as e:
                print(f"Erro ao carregar {filepath}: {e}")
    
    if todos_os_dfs:
        df_consolidado = pd.concat(todos_os_dfs, ignore_index=True)
        return df_consolidado
    print(f"Nenhum arquivo CSV encontrado em '{diretorio_dados}'.")
    return pd.DataFrame() # Retorna um DataFrame vazio se não houver arquivos