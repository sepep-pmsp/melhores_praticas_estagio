import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as mtick
from utils.load_csv import load_csv
from utils.load_shp import load_shp


# Configuração da página #

st.set_page_config(layout = "wide")

# Título
st.markdown("<h1 style='text-align: center;'>Dashboard do Orçamento Aberto</h1>", unsafe_allow_html = True)

# Subtítulo
st.markdown("<p style='text-align: center; font-size: 1.5rem; color: black;'>Prefeitura Municipal de São Paulo</p>", unsafe_allow_html = True)


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

st.markdown("## Previsão de recursos regionalizáveis no PPA por subprefeitura")

# Interação dos anos
anos_disponiveis = [2022, 2023, 2024, 2025]

anos_selecionados = st.multiselect("Selecione os anos", anos_disponiveis, default = 2022)

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
                 "SANTANA-TUCURUVI": (500, 500),}

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

# Mapa e gráfico de rosca
def gerar_figura():
    fig, (ax_map, ax_pie) = plt.subplots(1, 2, figsize = (12, 7), gridspec_kw = {"width_ratios": [2, 1]}, constrained_layout = True)

    fig.patch.set_facecolor("none")

    gdf.plot(color = gdf["cor"], edgecolor = "black", linewidth = 0.2, ax = ax_map)

    for _, row in gdf.iterrows():

        nome = "\n".join(row["nm_subpref"].replace("-", " ").split())

        ax_map.text(row["desloc_x"], row["desloc_y"], nome, fontsize = 5,
                    ha = "center", va = "center", fontweight = "bold", color = "black")
        
    plt.figtext(0.15, 0.01, "Fonte: PPA 2022 - 2025, dados da SEPLAN/SP", ha = "center", fontsize = 8)

    ax_map.axis("off")


    wedges, _ = ax_pie.pie(plot_df["valor_total"],
                           labels = None,
                           startangle = 90,
                           colors = [color_map[n] for n in plot_df["nm_subpref"]],
                           wedgeprops = dict(width = 0.4))
    
    legend_labels = [f"{row['nm_subpref'].title()}: {row['percentual']:.1f}%" for _, row in plot_df.iterrows()]

    leg = ax_pie.legend(wedges,
                        legend_labels,
                        title = f"Participação das subprefeituras\nno orçamento ({', '.join(map(str, anos_selecionados))}):",
                        loc = "center left",
                        bbox_to_anchor = (1, 0.5),
                        fontsize = 10)
    
    leg.get_frame().set_linewidth(0)

    ax_pie.axis("equal")

    return fig

# Exibe
fig = gerar_figura()

st.pyplot(fig)

# Tabela dos valores orçados
anos_str = ", ".join(map(str, anos_selecionados))

coluna_valor_formatada = f"Valor orçado regionalizável ({anos_str})"

gdf_sorted[coluna_valor_formatada] = gdf_sorted["valor_total"].map(lambda x: f"R$ {x:,.0f}".replace(",", "."))

table_display = gdf_sorted[["nm_subpref", coluna_valor_formatada]].rename(columns = {"nm_subpref": "Subprefeitura"})

st.markdown("#### Tabela de valores orçados por subprefeitura")

st.dataframe(table_display.style.format({coluna_valor_formatada: "{:>}"}), height = 300)


# Visualização 2 #

st.markdown("---")
st.markdown("## Previsão de recursos regionalizáveis por função governamental (2022 - 2025)")
st.caption("Destaque para as 3 funções com maior volume de despesas previstas no período")

def gerar_figura_funcoes():
    deslocamentos = {
        "FREGUESIA-BRASILANDIA": (500, 500),
        "CASA VERDE-CACHOEIRINHA": (500, -500),
        "SANTANA-TUCURUVI": (500, 500)
    }

    anos = ["2022", "2023", "2024", "2025"]
    colunas_valores = [f"valor {ano}" for ano in anos]

    df = gdf_merged.copy()

    df["valor_total"] = df[colunas_valores].sum(axis=1)

    df_total = df[["nm_subpref", "descrica_2", "valor_total", "geometry"]].copy()

    top_funcoes = (df_total.groupby("descrica_2")[["valor_total"]]
                   .sum()
                   .reset_index()
                   .sort_values("valor_total", ascending=False)
                   .head(3)["descrica_2"]
                   .tolist())

    df_top3 = df_total[df_total["descrica_2"].isin(top_funcoes)]

    escalas_colorbar = {
        "Educação": (0, 5.6e9),
        "Assistência Social": (0, 1.0e9),
        "Urbanismo": (0, 3.6e9)
    }

    intervalos_colorbar = {
        "Educação": 4e8,
        "Assistência Social": 1e8,
        "Urbanismo": 4e8
    }

    fig, axs = plt.subplots(1, 3, figsize=(28, 16))

    for i, funcao in enumerate(top_funcoes):
        ax = axs[i]

        gdf_plot = df_top3[df_top3["descrica_2"] == funcao]
        gdf_plot = gdf_plot.groupby(["nm_subpref", "geometry"])[["valor_total"]].sum().reset_index()
        gdf_plot = gpd.GeoDataFrame(gdf_plot, geometry="geometry", crs=gdf_subprefs.crs)

        gdf_plot["centroid"] = gdf_plot.geometry.centroid
        gdf_plot["desloc_x"] = gdf_plot.apply(lambda row: row["centroid"].x + deslocamentos.get(row["nm_subpref"], (0, 0))[0], axis=1)
        gdf_plot["desloc_y"] = gdf_plot.apply(lambda row: row["centroid"].y + deslocamentos.get(row["nm_subpref"], (0, 0))[1], axis=1)

        vmin_funcao, vmax_funcao = escalas_colorbar.get(funcao, (0, gdf_plot["valor_total"].max()))
        step = intervalos_colorbar.get(funcao, 1e8)
        ticks = np.arange(vmin_funcao, vmax_funcao + step, step)

        gdf_plot.plot(column="valor_total", cmap="BuGn", linewidth=0.5, edgecolor="black", ax=ax,
                      vmin=vmin_funcao, vmax=vmax_funcao)

        for _, row in gdf_plot.iterrows():
            nome = "\n".join(row["nm_subpref"].replace("-", " ").split())
            ax.text(row["desloc_x"], row["desloc_y"], nome,
                    fontsize=8, ha="center", va="center", fontweight="bold", color="black")

        ax.set_title(funcao, fontsize=16)
        ax.axis("off")

        sm = plt.cm.ScalarMappable(cmap="BuGn", norm=plt.Normalize(vmin=vmin_funcao, vmax=vmax_funcao))
        sm._A = []
        cbar = fig.colorbar(sm, ax=ax, orientation="vertical", fraction=0.045, pad=0.08)
        cbar.set_label("Planejamento orçamentário regionalizável (R$)", fontsize=14, labelpad=8)
        cbar.ax.tick_params(labelsize=12)
        cbar.set_ticks(ticks)
        cbar.ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'{x/1e9:.1f} bi'))

    fig.suptitle("Previsão de recursos regionalizáveis por subprefeitura e função governamental (2022 - 2025)",
                 fontsize=18, y=0.95)
    fig.text(0.5, 0.91, "Destaque para as 3 funções governamentais com maior volume de despesas previstas no período",
             ha="center", fontsize=14)
    plt.figtext(0.06, 0.01, "Fonte: PPA 2022 - 2025, dados da SEPLAN/SP", ha="center", fontsize=12)
    plt.tight_layout(rect=[0, 0.05, 1, 0.93])

    return fig

# Exibe segunda figura
fig2 = gerar_figura_funcoes()
st.pyplot(fig2)