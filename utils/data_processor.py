# utils/data_processor.py

import pandas as pd
import re
import os
from thefuzz import fuzz
from thefuzz import process
# REMOVIDO: import matplotlib.pyplot as plt - Não é mais necessário aqui

def limpar_e_converter_preco(df):
    if df.empty or 'Preço Bruto' not in df.columns:
        print("Aviso: DataFrame vazio ou sem a coluna 'Preço Bruto' para limpeza.")
        df['Preço Numérico'] = None 
        return df

    df['Preço Bruto'] = df['Preço Bruto'].astype(str)

    def _limpar_preco_individual(preco_str):
        if not isinstance(preco_str, str): 
            return None

        preco_str = preco_str.replace('R$', '').replace('US$', '').strip()

        if ',' in preco_str and '.' in preco_str:
            preco_limpo = preco_str.replace('.', '').replace(',', '.')
        elif ',' in preco_str:
            preco_limpo = preco_str.replace(',', '.')
        else:
            preco_limpo = preco_str

        preco_limpo = re.sub(r'[^\d.]', '', preco_limpo)

        try:
            return float(preco_limpo)
        except ValueError:
            print(f"Não foi possível converter o preço: '{preco_str}' para numérico.")
            return None

    df['Preço Numérico'] = df['Preço Bruto'].apply(_limpar_preco_individual)

    return df

def carregar_dados_raspados(diretorio_dados="data"):
    todos_os_dfs = []
    if not os.path.exists(diretorio_dados):
        print(f"Diretório de dados '{diretorio_dados}' não encontrado.")
        return pd.DataFrame() 

    for filename in os.listdir(diretorio_dados):
        if filename.endswith(".csv"):
            filepath = os.path.join(diretorio_dados, filename)
            try:
                df = pd.read_csv(filepath, encoding='utf-8')
                todos_os_dfs.append(df)
            except UnicodeDecodeError:
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
    return pd.DataFrame()

def limpar_nome_produto(nome_produto_sujo):
    if not isinstance(nome_produto_sujo, str):
        return ""
    
    nome = nome_produto_sujo.lower()
    
    termos_a_remover = [
        r'\bnew\b', r'\bnovo\b', r'\bem oferta\b', r'\bcom\b', r'\bpara\b',
        r'\bavulso\b', r'\bunidade\b', r'\boferta\b', r'\bfrete grátis\b',
        r'\bpronta entrega\b', r'\bteclado\b', r'\biluminado\b', r'\bsom\b',
        r'\bem\b', r'\bde\b', r'\bnvme\b', r'\bsata\b', r'\bm.2\b',
        r'\bdiferenciada\b', r'\bpromoção\b', r'\bexclusivo\b', r'\bplus\b'
    ]
    for termo in termos_a_remover:
        nome = re.sub(termo, '', nome) # CORREÇÃO AQUI: era termo, não termos_a_remover
    
    nome = re.sub(r'(\d+)tb', r'\1 tb', nome)
    nome = re.sub(r'(\d+)gb', r'\1 gb', nome)
    nome = re.sub(r'(\d+)ghz', r'\1 ghz', nome)
    nome = re.sub(r'(\d+)hz', r'\1 hz', nome)
    nome = re.sub(r'(\d+)cm', r'\1 cm', nome)
    nome = re.sub(r'(\d+)mm', r'\1 mm', nome)
    
    nome = re.sub(r'[^\w\s]', '', nome)
    nome = re.sub(r'\s+', ' ', nome).strip()

    return nome

def agrupar_produtos_similares(df_limpo, threshold=80):
    if df_limpo.empty or 'Nome do Produto' not in df_limpo.columns:
        print("Aviso: DataFrame vazio ou sem a coluna 'Nome do Produto' para agrupamento.")
        return df_limpo

    df_limpo['Nome do Produto Limpo'] = df_limpo['Nome do Produto'].apply(limpar_nome_produto)

    nomes_unicos_limpos = [n for n in df_limpo['Nome do Produto Limpo'].dropna().unique().tolist() if n]
    
    grupos_de_produto = []
    nomes_processados_no_grupo = set()

    for nome_principal_limpo in nomes_unicos_limpos:
        if nome_principal_limpo in nomes_processados_no_grupo:
            continue
        
        matches = process.extract(nome_principal_limpo, nomes_unicos_limpos, scorer=fuzz.token_sort_ratio)
        current_group_members = [match[0] for match in matches if match[1] >= threshold]
        
        nomes_originais_do_grupo = df_limpo[df_limpo['Nome do Produto Limpo'].isin(current_group_members)]['Nome do Produto'].tolist()
        if nomes_originais_do_grupo:
            nome_representativo_do_grupo = max(set(nomes_originais_do_grupo), key=nomes_originais_do_grupo.count)
        else:
            nome_representativo_do_grupo = nome_principal_limpo

        for member_name_limpo in current_group_members:
            df_limpo.loc[df_limpo['Nome do Produto Limpo'] == member_name_limpo, 'Grupo de Produto'] = nome_representativo_do_grupo
            nomes_processados_no_grupo.add(member_name_limpo)
            
    df_limpo['Grupo de Produto'] = df_limpo['Grupo de Produto'].fillna(df_limpo['Nome do Produto Limpo'])
    return df_limpo

def gerar_grafico_linha_com_destaques(ax, df, grupo_col="Grupo de Produto", preco_col="Preço Numérico"):
    """
    Gera um gráfico de linha nos eixos (ax) fornecidos, com destaques.
    ATENÇÃO: Não cria uma nova figura/eixos. Espera receber 'ax'.
    """
    ax.clear() # Limpa o conteúdo anterior dos eixos

    if df.empty or grupo_col not in df.columns or preco_col not in df.columns:
        ax.text(0.5, 0.5, "DataFrame inválido ou colunas ausentes para gráfico de linha.",
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, color='#B0B0B0', fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_title("") # Limpa o título se não houver dados
        return

    # Certifica-se de que a coluna de preço é numérica
    df[preco_col] = pd.to_numeric(df[preco_col], errors='coerce')
    df = df.dropna(subset=[preco_col]) # Remove NAs após conversão

    if df.empty:
        ax.text(0.5, 0.5, "Nenhum dado numérico válido para exibir no gráfico de linha.",
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, color='#B0B0B0', fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_title("")
        return

    media_por_grupo = df.groupby(grupo_col)[preco_col].mean().sort_values()

    if media_por_grupo.empty:
        ax.text(0.5, 0.5, "Nenhum dado válido para exibir no gráfico de linha após agrupamento.",
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, color='#B0B0B0', fontsize=12)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.set_title("")
        return

    # Plotagem
    # media_por_grupo.plot(kind="line", marker="o", ax=ax, color="#007BFF") # ORIGINAL - removido

    # --- CORREÇÃO AQUI: Usar ax.plot() explicitamente com x e y para garantir categórico ---
    x_labels = media_por_grupo.index.astype(str) # Garante que os rótulos do eixo X são strings
    y_values = media_por_grupo.values # Os valores de preço
    
    ax.plot(x_labels, y_values, marker="o", color="#007BFF") # Plotar no ax
    # --- FIM DA CORREÇÃO ---


    # Destaques
    mais_barato = media_por_grupo.idxmin()
    mais_caro = media_por_grupo.idxmax()
    media_geral = media_por_grupo.mean()
    mais_proximo_media = (media_por_grupo - media_geral).abs().idxmin()

    # Adicionar anotações para os destaques
    ax.annotate(f'Min: R${media_por_grupo[mais_barato]:.2f}', 
                xy=(mais_barato, media_por_grupo[mais_barato]), # x,y do ponto
                xytext=(-15, 15), textcoords='offset points', # Deslocamento do texto
                arrowprops=dict(facecolor='green', shrink=0.05), fontsize=9, color='green')
    ax.annotate(f'Max: R${media_por_grupo[mais_caro]:.2f}', 
                xy=(mais_caro, media_por_grupo[mais_caro]), 
                xytext=(15, -15), textcoords='offset points', 
                arrowprops=dict(facecolor='red', shrink=0.05), fontsize=9, color='red')
    
    # Linha para a média geral
    ax.axhline(media_geral, color='gray', linestyle='--', linewidth=0.8, label=f'Média Geral: R${media_geral:.2f}')
    ax.legend(facecolor='#3A3A3A', edgecolor='#4A4A4A', labelcolor='#E0E0E0') # Estilo para a legenda

    # Estilo do gráfico
    ax.set_title("Preço Médio por Grupo de Produto (Linha)", color='#E0E0E0', fontsize=12)
    ax.set_ylabel("Preço (R$)", color='#B0B0B0')
    ax.set_xlabel("Grupo de Produto", color='#B0B0B0')
    
    # CORREÇÃO: Assegura que os labels do eixo X são rotacionados e visíveis
    ax.set_xticks(range(len(x_labels))) # Define os ticks numéricos
    ax.set_xticklabels(x_labels, rotation=45, ha='right', fontsize=10) # Define os labels textuais

    ax.tick_params(axis='x', colors='#B0B0B0')
    ax.tick_params(axis='y', colors='#B0B0B0')

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_color('#4A4A4A')
    ax.spines['left'].set_color('#4A4A4A')
    
    return