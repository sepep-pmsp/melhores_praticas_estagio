import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

# --- Configuração da página ---
st.set_page_config(layout="wide")

# Título centralizado
st.markdown(
    "<h1 style='text-align: center;'>Dashboard do Orçamento Aberto</h1>",
    unsafe_allow_html=True
)

# Subtítulo (caption) centralizado
st.markdown(
    "<p style='text-align: center; font-size: 1.5rem; color: black;'>Prefeitura Municipal de São Paulo</p>",
    unsafe_allow_html=True
)

# --- Carregar dados ---
@st.cache_data
def carregar_dados():
    df_ppa = pd.read_csv("data/ppa_reg.csv")
    gdf = gpd.read_file("data/subprefs.shp")
    return df_ppa, gdf

df_ppa_reg, gdf_subprefs = carregar_dados()

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("## Previsão de recursos regionalizáveis no PPA por subprefeitura")

# --- Interação: anos selecionados ---
anos_disponiveis = [2022, 2023, 2024, 2025]
anos_selecionados = st.multiselect("Selecione os anos", anos_disponiveis, default=2022)

if not anos_selecionados:
    st.warning("Selecione pelo menos um ano para visualizar os dados.")
    st.stop()

colunas_valor = [f"valor {ano}" for ano in anos_selecionados]

# --- Agrupar dados por subprefeitura ---
df_grouped = df_ppa_reg.groupby("descricao prefeitura regional")[colunas_valor].sum().reset_index()
df_grouped["valor_total"] = df_grouped[colunas_valor].sum(axis=1)

# --- Merge com GeoDataFrame ---
gdf = gdf_subprefs.merge(df_grouped, how="left", left_on="nm_subpref", right_on="descricao prefeitura regional")
gdf["centroid"] = gdf.geometry.centroid

# --- Corrigir deslocamentos manuais ---
deslocamentos = {
    "FREGUESIA-BRASILANDIA": (500, 1500),
    "CASA VERDE-CACHOEIRINHA": (400, -500),
    "SANTANA-TUCURUVI": (500, 500),
}
gdf["desloc_x"] = gdf.apply(lambda row: row["centroid"].x + deslocamentos.get(row["nm_subpref"], (0, 0))[0], axis=1)
gdf["desloc_y"] = gdf.apply(lambda row: row["centroid"].y + deslocamentos.get(row["nm_subpref"], (0, 0))[1], axis=1)

# --- Cálculo dos percentuais ---
gdf["valor_total"] = gdf["valor_total"].fillna(0)
gdf["percentual"] = gdf["valor_total"] / gdf["valor_total"].sum() * 100

# --- Número fixo de subprefeituras em destaque ---
top_n = 5

gdf_sorted = gdf.sort_values("valor_total", ascending=False)
top_df = gdf_sorted.iloc[:top_n]
resto_df = gdf_sorted.iloc[top_n:]
outros = pd.DataFrame({
    "nm_subpref": ["Demais subprefeituras"],
    "valor_total": [resto_df["valor_total"].sum()],
    "percentual": [resto_df["valor_total"].sum() / gdf["valor_total"].sum() * 100]
})
plot_df = pd.concat([top_df[["nm_subpref", "valor_total", "percentual"]], outros], ignore_index=True)

# --- Definir cores fixas ---
colors = ["#B52D3D", "#303C30", "#F9DF68", "#AB9D78", "#F1EBDD"] + ["#778AA8"]
color_map = dict(zip(plot_df["nm_subpref"], colors))
gdf["grupo_cor"] = gdf["nm_subpref"].where(gdf["nm_subpref"].isin(top_df["nm_subpref"]), "Demais subprefeituras")
gdf["cor"] = gdf["grupo_cor"].map(color_map)

# --- Função para gerar figura com mapa + rosca ---
def gerar_figura():
    fig, (ax_map, ax_pie) = plt.subplots(1, 2, figsize=(12, 7), gridspec_kw={"width_ratios": [2, 1]}, constrained_layout=True) #16, 10

    fig.patch.set_facecolor("none")

    # Mapa estilizado
    gdf.plot(color=gdf["cor"], edgecolor="black", linewidth=0.2, ax=ax_map)
    for _, row in gdf.iterrows():
        nome = "\n".join(row["nm_subpref"].replace("-", " ").split())
        ax_map.text(row["desloc_x"], row["desloc_y"], nome, fontsize=5,
                    ha="center", va="center", fontweight="bold", color="black")
        
    plt.figtext(0.15, 0.01, "Fonte: PPA 2022 - 2025, dados da SEPLAN/SP", ha="center", fontsize=8)

    ax_map.axis("off")

    # Rosca
    wedges, _ = ax_pie.pie(plot_df["valor_total"],
                           labels=None,
                           startangle=90,
                           colors=[color_map[n] for n in plot_df["nm_subpref"]],
                           wedgeprops=dict(width=0.4))
    legend_labels = [f"{row['nm_subpref'].title()}: {row['percentual']:.1f}%" for _, row in plot_df.iterrows()]
    leg = ax_pie.legend(wedges,
                        legend_labels,
                        title=f"Participação das subprefeituras\nno orçamento ({', '.join(map(str, anos_selecionados))}):",
                        loc="center left",
                        bbox_to_anchor=(1, 0.5),
                        fontsize=10)
    leg.get_frame().set_linewidth(0)  # Remove a borda da legenda
    ax_pie.axis("equal")
    return fig

# --- Exibir figura ---
fig = gerar_figura()
st.pyplot(fig)

# --- Gerar tabela interativa com anos no título ---
anos_str = ", ".join(map(str, anos_selecionados))
coluna_valor_formatada = f"Valor orçado regionalizável ({anos_str})"

gdf_sorted[coluna_valor_formatada] = gdf_sorted["valor_total"].map(lambda x: f"R$ {x:,.0f}".replace(",", "."))

table_display = gdf_sorted[["nm_subpref", coluna_valor_formatada]].rename(columns={"nm_subpref": "Subprefeitura"})

st.markdown("#### Tabela de valores orçados por subprefeitura")
st.dataframe(table_display.style.format({coluna_valor_formatada: "{:>}"}), height=300)