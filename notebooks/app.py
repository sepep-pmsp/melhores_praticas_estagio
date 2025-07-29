import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mtick
import plotly.express as px
from utils.load_csv import load_csv
from utils.load_shp import load_shp
 
 
 
# Configuração da página #
 
st.set_page_config(layout = "wide")
 
# Título
st.markdown("<h1 style='text-align: center;'>Dashboard do Orçamento Aberto</h1>", unsafe_allow_html = True)
 
# Subtítulo
st.markdown("<p style='text-align: center; font-size: 1.5rem; color: black;'>Prefeitura Municipal de São Paulo</p>", unsafe_allow_html = True)
 
# Sidebar
with st.sidebar:
    st.write("Esse é o Dashboard do Orçamento Aberto, projeto inscrito no 14º Prêmio Melhores Práticas de Estágio da Prefeitura Municipal de São Paulo.")
 
 
 
# Carregar dados #
 
@st.cache_data
 
def carregar_dados():
 
    df_ppa_reg = load_csv("ppa_reg.csv")
 
    gdf_subprefs = load_shp("subprefs.shp")
 
    gdf_merged = load_shp("gdf_merged.shp")
 
    return df_ppa_reg, gdf_subprefs, gdf_merged
 
df_ppa_reg, gdf_subprefs, gdf_merged = carregar_dados()
 
 
 
# Visualização 1 #
 
st.markdown("<br>", unsafe_allow_html = True)
 
st.markdown("## Recursos regionalizáveis no PPA por subprefeitura")
 
st.caption("#### Destaque para as 5 subprefeituras com maior volume de recursos regionalizáveis no período")
 
# Interação dos anos
anos_disponiveis = [2022, 2023, 2024, 2025]
 
anos_selecionados = st.multiselect("Selecione os anos:", anos_disponiveis, default = anos_disponiveis, key = "multiselect_anos_1")
 
if not anos_selecionados:
 
    st.warning("Selecione pelo menos um ano para visualizar os dados.")
 
    st.stop()
 
colunas_valor = [f"valor {ano}" for ano in anos_selecionados]
 
# Agrupar dados por subprefeitura
df_grouped = df_ppa_reg.groupby("descricao prefeitura regional")[colunas_valor].sum().reset_index()
 
df_grouped["valor_total"] = df_grouped[colunas_valor].sum(axis = 1)
 
# Merge
gdf = gdf_subprefs.merge(df_grouped, how = "left", left_on = "nm_subpref", right_on = "descricao prefeitura regional")
 
gdf["centroid"] = gdf.geometry.centroid
 
# Corrigir deslocamentos
deslocamentos = {"FREGUESIA-BRASILANDIA": (500, 1500),
                 "CASA VERDE-CACHOEIRINHA": (400, -500),
                 "SANTANA-TUCURUVI": (500, 500)}
 
gdf["desloc_x"] = gdf.apply(lambda row: row["centroid"].x + deslocamentos.get(row["nm_subpref"], (0, 0))[0], axis = 1)
 
gdf["desloc_y"] = gdf.apply(lambda row: row["centroid"].y + deslocamentos.get(row["nm_subpref"], (0, 0))[1], axis = 1)
 
# Cálculo dos percentuais
gdf["valor_total"] = gdf["valor_total"].fillna(0)
 
gdf["percentual"] = gdf["valor_total"] / gdf["valor_total"].sum() * 100
 
# Subprefeituras em destaque
top_n = 5
 
gdf_sorted = gdf.sort_values("valor_total", ascending = False)
 
top_df = gdf_sorted.iloc[:top_n]
 
resto_df = gdf_sorted.iloc[top_n:]
 
outros = pd.DataFrame({"nm_subpref": ["Demais subprefeituras"],
                       "valor_total": [resto_df["valor_total"].sum()],
                       "percentual": [resto_df["valor_total"].sum() / gdf["valor_total"].sum() * 100]})
 
plot_df = pd.concat([top_df[["nm_subpref", "valor_total", "percentual"]], outros], ignore_index = True)
 
# Cores
colors = ["#B52D3D", "#303C30", "#F9DF68", "#AB9D78", "#F1EBDD"] + ["#778AA8"]
 
color_map = dict(zip(plot_df["nm_subpref"], colors))
 
gdf["grupo_cor"] = gdf["nm_subpref"].where(gdf["nm_subpref"].isin(top_df["nm_subpref"]), "Demais subprefeituras")
 
gdf["cor"] = gdf["grupo_cor"].map(color_map)

# Mapa
def gerar_mapa():
    gdf_plot = gdf.copy()
 
    gdf_plot = gdf_plot.to_crs(epsg = 4326)
 
    gdf_plot["hover_text"] = gdf_plot.apply(lambda row: f"{row['nm_subpref']}<br>Valor total: R$ {row['valor_total']:,.0f}<br>Participação: {row['percentual']:.1f}%"
                                            .replace(",", "."), axis = 1)
 
    fig = px.choropleth_mapbox(gdf_plot,
                               geojson = gdf_plot.geometry.__geo_interface__,
                               locations = gdf_plot.index,
                               color = "grupo_cor",
                               hover_name = "hover_text",
                               mapbox_style = "carto-positron",
                               center = {"lat": -23.55, "lon": -46.63},
                               zoom = 8.5,
                               opacity = 0.5,
                               color_discrete_map = color_map)
 
    fig.update_layout(margin = {"r":0,"t":0,"l":0,"b":0}, showlegend = False, height = 600)
 
    return fig

# Gráfico de rosca
def gerar_grafico_rosca():
    plot_df["percentual"] = plot_df["valor_total"] / plot_df["valor_total"].sum()
 
    plot_df["hover_text"] = plot_df.apply(lambda row: f"{row['nm_subpref']}<br>Valor: R$ {row['valor_total']:,.0f}<br>Participação: {row['percentual']*100:.1f}%"
                                          .replace(",", "."), axis = 1)
 
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
                      #legend_title_text="Participação das subprefeituras<br>no orçamento regionalizável:",
                      legend = dict(font = dict(size = 14), title_font = dict(size = 16), x = 0.8, y = 0.5),
                      margin = dict(l = 20, r = 20, t = 20, b = 20),
                      height = 300)
 
    return fig
 
# Colunas
col1, col2 = st.columns([1, 1])
 
with col1:
    st.plotly_chart(gerar_mapa(), use_container_width = True)
 
with col2:
    st.markdown("<br><br><br><br><br><br>", unsafe_allow_html = True)
    st.plotly_chart(gerar_grafico_rosca(), theme = None)
 
# Tabela dos valores orçados
#st.markdown("<br>", unsafe_allow_html = True)
 
st.markdown("#### Valores regionalizáveis orçados por subprefeitura")
 
with st.expander("Veja os dados"):
    anos_str = ", ".join(map(str, anos_selecionados))
 
    coluna_valor_formatada = f"Valor regionalizável orçado"
 
    gdf_sorted[coluna_valor_formatada] = gdf_sorted["valor_total"].map(lambda x: f"R$ {x:,.0f}".replace(",", "."))
 
    table_display = gdf_sorted[["nm_subpref", coluna_valor_formatada]].rename(columns = {"nm_subpref": "Subprefeitura"})
 
    st.caption(f"Valores somados para os anos selecionados: {anos_str}")
 
    st.dataframe(table_display.style.format({coluna_valor_formatada: "{:>}"}), height = 400)
 
 
 
# Visualização 2 #
 
st.markdown("---")
 
st.markdown("## Recursos regionalizáveis no PPA por subprefeitura e função governamental")
 
st.caption("#### Destaque para as 3 funções governamentais com maior volume de recursos regionalizáveis no período")
 
# Interação dos anos
anos_disponiveis = ["2022", "2023", "2024", "2025"]
 
anos_selecionados = st.multiselect("Selecione os anos:", options = anos_disponiveis, default = anos_disponiveis, key = "multiselect_anos_2")
 
if not anos_selecionados:
    st.warning("Selecione pelo menos um ano para visualizar os dados.")
    st.stop()
 
# Figura
def gerar_figura_funcoes(anos):
 
    deslocamentos = {"FREGUESIA-BRASILANDIA": (500, 1500),
                     "CASA VERDE-CACHOEIRINHA": (500, -500),
                     "SANTANA-TUCURUVI": (500, 500)}
 
    colunas_valores = [f"valor {ano}" for ano in anos]
 
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
 
    fig, axs = plt.subplots(1, 3, figsize = (28, 16))
 
    for i, funcao in enumerate(top_funcoes):
 
        ax = axs[i]
 
        gdf_plot = df_top3[df_top3["descrica_2"] == funcao]
 
        gdf_plot = gdf_plot.groupby(["nm_subpref", "geometry"])[["valor_total"]].sum().reset_index()
 
        gdf_plot = gpd.GeoDataFrame(gdf_plot, geometry = "geometry", crs = gdf_subprefs.crs)
 
        gdf_plot["centroid"] = gdf_plot.geometry.centroid
 
        gdf_plot["desloc_x"] = gdf_plot.apply(lambda row: row["centroid"].x + deslocamentos.get(row["nm_subpref"], (0, 0))[0], axis = 1)
 
        gdf_plot["desloc_y"] = gdf_plot.apply(lambda row: row["centroid"].y + deslocamentos.get(row["nm_subpref"], (0, 0))[1], axis = 1)
 
        vmin_funcao, vmax_funcao = escalas_colorbar.get(funcao, (0, gdf_plot["valor_total"].max()))
 
        step = intervalos_colorbar.get(funcao, 1e8)
 
        ticks = np.arange(vmin_funcao, vmax_funcao + step, step)
 
        gdf_plot.plot(column = "valor_total", cmap = "BuGn", linewidth = 0.5, edgecolor = "black", ax = ax,
                      vmin = vmin_funcao, vmax = vmax_funcao)
 
        for _, row in gdf_plot.iterrows():
            nome = "\n".join(row["nm_subpref"].replace("-", " ").split())
            ax.text(row["desloc_x"], row["desloc_y"], nome,
                    fontsize = 8, ha = "center", va = "center", fontweight = "bold", color = "black")
 
        ax.set_title(funcao, fontsize = 16)
 
        ax.axis("off")
 
        sm = plt.cm.ScalarMappable(cmap = "BuGn", norm = plt.Normalize(vmin = vmin_funcao, vmax = vmax_funcao))
        sm._A = []
        cbar = fig.colorbar(sm, ax = ax, orientation = "vertical", fraction = 0.045, pad = 0.08)
        cbar.set_label("Planejamento orçamentário regionalizável (R$)", fontsize = 14, labelpad = 8)
        cbar.ax.tick_params(labelsize = 12)
        cbar.set_ticks(ticks)
        cbar.ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'{x/1e9:.1f} bi'))
 
    plt.figtext(0.06, 0.01, "Fonte: PPA 2022 - 2025, dados da SEPLAN/SP", ha = "center", fontsize = 12)
    plt.tight_layout(rect=[0, 0.05, 1, 0.8])
 
    return fig
 
fig2 = gerar_figura_funcoes(anos_selecionados)
 
st.pyplot(fig2)
 
# Tabela funções com maiores valores orçados
#st.markdown("<br>", unsafe_allow_html = True)
 
st.markdown("#### 10 funções governamentais com maior volume de valores regionalizáveis orçados")
 
with st.expander("Veja os dados"):
    st.caption(f"Valores somados para os anos selecionados: {', '.join(anos_selecionados)}")
 
    colunas_valores = [f"valor {ano}" for ano in anos_selecionados]
 
    df_funcoes = gdf_merged.copy()
 
    df_funcoes["valor_total"] = df_funcoes[colunas_valores].sum(axis = 1)
 
    df_funcoes_grouped = (df_funcoes.groupby("descrica_2")[["valor_total"]]
                          .sum()
                          .sort_values("valor_total", ascending = False)
                          .reset_index()
                          .head(10))
   
    df_funcoes_grouped["Valor regionalizável orçado"] = df_funcoes_grouped["valor_total"].map(lambda x: f"R$ {x:,.0f}".replace(",", "."))
 
    tabela_funcoes = df_funcoes_grouped[["descrica_2", "Valor regionalizável orçado"]].rename(columns = {"descrica_2": "Função governamental"})
 
    st.dataframe(tabela_funcoes.style.format({"Valor regionalizável orçado": "{:>}"}), height = 400)