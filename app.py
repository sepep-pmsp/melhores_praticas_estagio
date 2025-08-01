# --- Configuração --- #
 
# Biblioteca
import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import numpy as np
from utils.load_csv import load_csv
from utils.load_shp import load_shp
 
# Layout
st.set_page_config(layout = "wide")

colors = ["#B52D3D", "#303C30", "#F9DF68", "#AB9D78", "#F1EBDD"] + ["#778AA8"]

st.markdown(f"""
<style>
    [data-testid=stSidebar] {{
        background-color: {colors[1]};
    }}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:

    st.markdown("<h3 style='color: white;'>Sobre</h3>", unsafe_allow_html = True)

    st.markdown("""<div style = 'text-align: justify; color: white;' >
                    Esse é o Dashboard do Orçamento Aberto, projeto inscrito no 14º Prêmio Melhores Práticas de Estágio da Prefeitura Municipal de São Paulo.
                    As visualizações mostram o planejamento orçamentário do município de 2022 até 2025.
                    </div> <br>""",
                    unsafe_allow_html = True)

    with st.expander("Metodologia"):

        st.markdown("""<div style = 'text-align: justify; color: white;' >
                    Este dashboard foi desenvolvido com a biblioteca Streamlit, utilizando a linguagem Python. 
                    A extração e o tratamento dos dados foram realizados com o apoio das bibliotecas Pandas e GeoPandas, 
                    a partir de três bases de dados principais: os dados do Plano Plurianual (PPA) 2022 - 2025 por fonte de recurso e por regionalização, 
                    obtidos no portal do orçamento da Prefeitura Municipal de São Paulo, e os limites administrativos das subprefeituras, extraídos do projeto GeoSampa. 
                    O processo de tratamento incluiu a padronização e agregação dos dados orçamentários por subprefeitura, 
                    possibilitando sua posterior com os polígonos georreferenciados. 
                    As visualizações interativas: mapas coropléticos e gráficos de rosca, foram elaboradas com a biblioteca Plotly, permitindo a exploração dinâmica dos dados e 
                    facilitando a análise da distribuição territorial dos orçamento público regionalizável.
                    </div> <br>""",
                    unsafe_allow_html = True)
        
    with st.expander("Fonte"):

        st.markdown("""<div style = 'text-align: justify; color: white;' >
                    Os dados são do PPA (2022 - 2025) e foram extraídos
                    do site do orçamento da PMSP.
                    </div>""",
                    unsafe_allow_html = True)

import streamlit as st

st.sidebar.markdown(
    """
    <a href="https://www.figma.com/proto/oJOJAmPbrWnvOKqxZfexhO/Or%C3%A7amento-Aberto-%7C-Melhores-Pr%C3%A1ticas-de-Est%C3%A1gio?page-id=0%3A1&node-id=101-18&viewport=247%2C368%2C0.04&t=uhXePc1EAPYBx3VI-1&scaling=scale-down-width&content-scaling=fixed&starting-point-node-id=210%3A474" 
       target="_blank">
        <button style="
            background-color: #F1EBDD;
            color: black;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
        ">
            Acesse o site
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

#4CAF50

# Carregar dados
@st.cache_data
 
def carregar_dados():
 
    df_ppa_reg = load_csv("ppa_reg.csv")
 
    gdf_subprefs = load_shp("subprefs.shp")
 
    gdf_merged = load_shp("gdf_merged.shp")
 
    return df_ppa_reg, gdf_subprefs, gdf_merged
 
df_ppa_reg, gdf_subprefs, gdf_merged = carregar_dados()
 
 
 
# --- Visualização 1 --- #

with st.container(key='conteudoPrincipal'):


     
    # Título
    with st.container(key='conteudoImgHeader'):
        st.image("assets/logo_reduzido.svg", width=90)

    with st.container(key='conteudoHeader'):
        st.markdown("<h1 style = 'text-align: center;' > Dashboard do Orçamento Aberto </h1>", unsafe_allow_html = True)
        st.markdown("<p style = 'text-align: center; font-size: 1.5rem; color: black;' > Prefeitura Municipal de São Paulo </p>", unsafe_allow_html = True)
 
    st.markdown("<br>", unsafe_allow_html = True)
    
    st.markdown("## Recursos regionalizáveis no PPA por subprefeitura")
    
    st.caption("#### Destaque para as 5 subprefeituras com maior volume de recursos regionalizáveis no período")
    
    # Interação dos anos
    anos_disponiveis = [2022, 2023, 2024, 2025]
    
    anos_selecionados = st.multiselect("Selecione os anos:",
                                    anos_disponiveis,
                                    default = anos_disponiveis,
                                    key = "multiselect_anos_1")
    
    if not anos_selecionados:
    
        st.warning("Selecione pelo menos um ano para visualizar os dados.")
    
        st.stop()
    
    colunas_valor = [f"valor {ano}" for ano in anos_selecionados]
    
    # Tratamento
    df_grouped = df_ppa_reg.groupby("descricao prefeitura regional")[colunas_valor].sum().reset_index()
    
    df_grouped["valor_total"] = df_grouped[colunas_valor].sum(axis = 1)
    
    gdf = gdf_subprefs.merge(df_grouped,
                            how = "left",
                            left_on = "nm_subpref",
                            right_on = "descricao prefeitura regional")
    
    gdf["centroid"] = gdf.geometry.centroid
    
    deslocamentos = {"FREGUESIA-BRASILANDIA": (500, 1500),
                    "CASA VERDE-CACHOEIRINHA": (400, -500),
                    "SANTANA-TUCURUVI": (500, 500)}
    
    gdf["desloc_x"] = gdf.apply(lambda row: row["centroid"].x + deslocamentos.get(row["nm_subpref"], (0, 0))[0], axis = 1)
    
    gdf["desloc_y"] = gdf.apply(lambda row: row["centroid"].y + deslocamentos.get(row["nm_subpref"], (0, 0))[1], axis = 1)
    
    gdf["valor_total"] = gdf["valor_total"].fillna(0)
    
    gdf["percentual"] = gdf["valor_total"] / gdf["valor_total"].sum() * 100
    
    top_n = 5
    
    gdf_sorted = gdf.sort_values("valor_total", ascending = False)
    
    top_df = gdf_sorted.iloc[:top_n]
    
    resto_df = gdf_sorted.iloc[top_n:]
    
    outros = pd.DataFrame({"nm_subpref": ["DEMAIS SUBPREFEITURAS"],
                        "valor_total": [resto_df["valor_total"].sum()],
                        "percentual": [resto_df["valor_total"].sum() / gdf["valor_total"].sum() * 100]})
    
    plot_df = pd.concat([top_df[["nm_subpref", "valor_total", "percentual"]], outros], ignore_index = True)
    
    
    color_map = dict(zip(plot_df["nm_subpref"], colors))
    
    gdf["grupo_cor"] = gdf["nm_subpref"].where(gdf["nm_subpref"].isin(top_df["nm_subpref"]), "DEMAIS SUBPREFEITURAS")
    
    gdf["cor"] = gdf["grupo_cor"].map(color_map)
    
    # Mapa
    def gerar_mapa():
    
        gdf_plot = gdf.copy()
    
        gdf_plot = gdf_plot.to_crs(epsg = 4326)
    
        gdf_plot["valor_formatado"] = gdf_plot["valor_total"].apply(lambda x: f"{x:,.0f}".replace(",", "."))
    
        gdf_plot["percentual_formatado"] = gdf_plot["percentual"]
    
        fig = px.choropleth_mapbox(gdf_plot,
                                geojson = gdf_plot.geometry.__geo_interface__,
                                locations = gdf_plot.index,
                                color = "grupo_cor",
                                custom_data = ["nm_subpref", "valor_formatado", "percentual_formatado"],
                                hover_data = [],
                                mapbox_style = "carto-positron",
                                center = {"lat": -23.7, "lon": -46.63},
                                zoom = 9,
                                opacity = 1,
                                color_discrete_map = color_map)
    
        fig.update_traces(hovertemplate = "<b>%{customdata[0]}</b><br>" +
                        "Valor: R$ %{customdata[1]}<br>" +
                        "Participação: %{customdata[2]:.1f}%<extra></extra>")
    
        fig.update_layout(margin = {"r": 0, "t": 0, "l": 0, "b": 0},
                        showlegend = False,
                        height = 600)
    
        return fig
    
    # Gráfico de rosca
    def gerar_grafico_rosca():
    
        plot_df["percentual"] = plot_df["valor_total"] / plot_df["valor_total"].sum()
    
        plot_df["hover_text"] = plot_df.apply(lambda row: f"{row['nm_subpref']}<br>Valor: R$ {row['valor_total']:,.0f}<br>Participação: {row['percentual']*100:.1f}%"
                                            .replace(",", "."),
                                            axis = 1)
    
        fig = px.pie(plot_df,
                    values = "valor_total",
                    names = "nm_subpref",
                    hole = 0.4,
                    color = "nm_subpref",
                    color_discrete_map = color_map,
                    hover_name = "hover_text")
    
        fig.update_traces(textinfo = "none",
                        hovertemplate = "%{hovertext}<extra></extra>",
                        marker = dict(line = dict(color  ="#000000", width = 0.5)))
    
        fig.update_layout(showlegend = True,
                        legend = dict(font = dict(size = 14), title_font = dict(size = 16), x = 0.8, y = 0.5),
                        margin = dict(l = 20, r = 20, t = 20, b = 20),
                        height = 300,
                        paper_bgcolor="#F1EBDD")
    
        return fig
    
    # Colunas
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.plotly_chart(gerar_mapa(), use_container_width = True)
    
    with col2:
        st.markdown("<br><br><br><br><br>", unsafe_allow_html = True)
        st.plotly_chart(gerar_grafico_rosca(), theme = None)
    
    # Tabela dos valores orçados
    st.markdown("#### Valores regionalizáveis orçados por subprefeitura")
    
    with st.expander("Veja os dados"):
    
        anos_str = ", ".join(map(str, anos_selecionados))
    
        coluna_valor_formatada = f"Valor regionalizável orçado"
    
        gdf_sorted[coluna_valor_formatada] = gdf_sorted["valor_total"].map(lambda x: f"R$ {x:,.0f}".replace(",", "."))
    
        table_display = gdf_sorted[["nm_subpref", coluna_valor_formatada]].rename(columns = {"nm_subpref": "Subprefeitura"})
    
        st.caption(f"Valores somados para os anos selecionados: {anos_str}")
    
        st.dataframe(table_display.style.format({coluna_valor_formatada: "{:>}"}), height = 400)
    
    
    
    # --- Visualização 2 --- #

    st.markdown("---")

    st.markdown("## Recursos regionalizáveis no PPA por subprefeitura e função governamental")

    st.caption("#### Destaque para as 3 funções governamentais com maior volume de recursos regionalizáveis no período")

    # Interação dos anos
    anos_disponiveis = ["2022", "2023", "2024", "2025"]

    anos_selecionados = st.multiselect("Selecione os anos:",
                                    options = anos_disponiveis,
                                    default = anos_disponiveis,
                                    key = "multiselect_anos_2")

    if not anos_selecionados:

        st.warning("Selecione pelo menos um ano para visualizar os dados.")

        st.stop()

    colunas_valores = [f"valor {ano}" for ano in anos_selecionados]

    # Tratamento
    df = gdf_merged.copy()

    df["valor_total"] = df[colunas_valores].sum(axis = 1)

    df_total = df[["nm_subpref", "descrica_2", "valor_total", "geometry"]].copy()

    top_funcoes = (df_total.groupby("descrica_2")[["valor_total"]]
                .sum()
                .reset_index()
                .sort_values("valor_total", ascending=False)
                .head(3)["descrica_2"]
                .tolist())

    df_top3 = df_total[df_total["descrica_2"].isin(top_funcoes)]

    escalas_colorbar = {"Educação": (0, 5.6e9),
                        "Assistência Social": (0, 1.0e9),
                        "Urbanismo": (0, 3.6e9)}

    intervalos_colorbar = {"Educação": 4e8,
                        "Assistência Social": 1e8,
                        "Urbanismo": 4e8}

    color_scales = {"Educação": "BuGn",
                    "Assistência Social": "BuGn",
                    "Urbanismo": "BuGn"}

    # Abas com os mapas
    abas = st.tabs(top_funcoes)

    for tab, funcao in zip(abas, top_funcoes):

        with tab:

            gdf_funcao = df_top3[df_top3["descrica_2"] == funcao]

            gdf_funcao = gdf_funcao.groupby(["nm_subpref", "geometry"]).sum(numeric_only = True).reset_index()

            gdf_funcao = gpd.GeoDataFrame(gdf_funcao, geometry="geometry", crs = gdf_subprefs.crs)

            gdf_funcao = gdf_funcao.to_crs(epsg = 4326)

            gdf_funcao["valor_formatado"] = gdf_funcao["valor_total"].apply(lambda x: f"{x:,.0f}".replace(",", "."))

            vmin_funcao, vmax_funcao = escalas_colorbar.get(funcao, (0, gdf_funcao["valor_total"].max()))

            step = intervalos_colorbar.get(funcao, 1e8)

            ticks = list(np.arange(vmin_funcao, vmax_funcao + step, step))

            ticktext = [f"{t / 1e9:.1f} bi" for t in ticks]

            fig_funcao = px.choropleth_mapbox(gdf_funcao,
                                            geojson = gdf_funcao.geometry.__geo_interface__,
                                            locations = gdf_funcao.index,
                                            color = "valor_total",
                                            hover_name = "nm_subpref",
                                            custom_data = ["nm_subpref", "valor_formatado"],
                                            color_continuous_scale = color_scales.get(funcao, "BuGn"),
                                            mapbox_style = "carto-positron",
                                            center = {"lat": -23.7, "lon": -46.63},
                                            zoom = 9,
                                            opacity = 1)

            fig_funcao.update_traces(hovertemplate = "<b>%{customdata[0]}</b><br>Valor: R$ %{customdata[1]}<extra></extra>")

            fig_funcao.update_layout(margin={"r": 300, "t": 0, "l": 300, "b": 0},
                                    height = 600,
                                    coloraxis = dict(
                                        cmin = vmin_funcao,
                                        cmax = vmax_funcao,
                                        colorbar = dict(
                                            title = dict(text = "Planejamento orçamentário regionalizável (R$)", side = "right", font = dict(color = "black")),
                                            tickfont = dict(color = "black"),
                                            tickvals = ticks,
                                            ticktext = ticktext,
                                            ticks = "outside",
                                            x = 1,
                                            y = 0.5,
                                            len = 0.75)))

  
            st.plotly_chart(fig_funcao, use_container_width = True)

    

    # Tabela funções com maiores valores orçados
    st.markdown("#### 10 funções governamentais com maior volume de valores regionalizáveis orçados")

    with st.expander("Veja os dados"):

        st.caption(f"Valores somados para os anos selecionados: {', '.join(anos_selecionados)}")

        df_funcoes = gdf_merged.copy()

        df_funcoes["valor_total"] = df_funcoes[[f"valor {ano}" for ano in anos_selecionados]].sum(axis = 1)

        df_funcoes_grouped = (df_funcoes.groupby("descrica_2")[["valor_total"]]
                            .sum()
                            .sort_values("valor_total", ascending = False)
                            .reset_index()
                            .head(10))

        df_funcoes_grouped["Valor regionalizável orçado"] = df_funcoes_grouped["valor_total"].map(lambda x: f"R$ {x:,.0f}".replace(",", "."))

        tabela_funcoes = df_funcoes_grouped[["descrica_2", "Valor regionalizável orçado"]].rename(
            columns = {"descrica_2": "Função governamental"})

        st.dataframe(tabela_funcoes.style.format({"Valor regionalizável orçado": "{:>}"}), height = 400)

st.markdown(f"""
    <style>
        .footer {{
            position: fixed;
            bottom: 0;
            width: 100%;
            background-color: {colors[1]};
            color: gray;
            text-align: center;
            padding: 10px;
            font-size: medium;
        }}
        .footer img {{
            height: 30px;
            vertical-align: middle;
            margin-right: 10px;
        }}
        .stMainBlockContainer {{
            padding-left: 0;
        }}
        .st-emotion-cache-zy6yx3 {{
            padding: 6rem 0rem 10rem
        }}
        .st-key-conteudoPrincipal {{
            padding: 0 6rem;
        }}

        .st-emotion-cache-f887e0 {{
            color: white;
        }}

        .st-key-conteudoHeader {{
            position: fixed;
            left: 6rem;
            top: 3rem;
            background-color: #f1ebdd;
            z-index: 4;
        }}
        .st-key-conteudoImgHeader{{
            left: 27rem;
            top: 4rem;
            position: fixed;
            z-index: 6;
        }}

    </style>
    <div class="footer">
        <img src="https://prefeitura.sp.gov.br/documents/34276/25188012/logo_PrefSP__horizontal_fundo+claro+%281%29.png">
        Copyleft 2025 | Prefeitura de São Paulo © 2025
    </div>
    """, unsafe_allow_html=True)
