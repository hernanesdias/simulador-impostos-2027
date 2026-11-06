import streamlit as st
import pandas as pd

# Configuração da página
st.set_page_config(
    page_title="Simulador de Impostos 2027",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Simulador Tributário comparativo (Cenário 2027)")
st.markdown("Compare a carga tributária entre **Simples Nacional**, **Lucro Presumido** e **Lucro Real** com base nas suas receitas, despesas e créditos.")

# --- BARRA LATERAL (ENTRADAS DE DADOS) ---
st.sidebar.header("⚙️ Parâmetros da Empresa")

faturamento_mensal = st.sidebar.number_input(
    "Faturamento Bruto Mensal (R$)", min_value=0.0, value=100000.0, step=5000.0
)
despesas_mensais = st.sidebar.number_input(
    "Despesas Operacionais / Dedutíveis (R$)", min_value=0.0, value=40000.0, step=2000.0
)
folha_pagamento = st.sidebar.number_input(
    "Folha de Pagamento Mensal (R$)", min_value=0.0, value=20000.0, step=1000.0
)
creditos_tributarios = st.sidebar.number_input(
    "Créditos de PIS/COFINS / Insumos (R$)", min_value=0.0, value=2000.0, step=500.0
)

tipo_atividade = st.sidebar.selectbox(
    "Setor de Atuação",
    ["Comércio", "Serviços (Geral)", "Indústria"]
)

# Botão de cálculo
executar_calculo = st.sidebar.button("Calcular e Comparar Regimes")

# --- MOTOR DE CÁLKULO ---
def calcular_impostos(faturamento, despesas, folha, creditos, atividade):
    faturamento_anual = faturamento * 12
    
    # 1. Simples Nacional (Estimativa simplificada por Anexo/Fator R)
    # Definindo aliquota média aproximada baseada na atividade
    if atividade == "Comércio":
        aliquota_simples = 0.06  # Média inicial Anexo I
    elif atividade == "Indústria":
        aliquota_simples = 0.08  # Média inicial Anexo II
    else:  # Serviços
        # Exemplo simples de Fator R (se folha for >= 28% do faturamento, cai no Anexo III, senão V)
        fator_r = folha / faturamento if faturamento > 0 else 0
        aliquota_simples = 0.155 if fator_r < 0.28 else 0.06
        
    imposto_simples = faturamento * aliquota_simples

    # 2. Lucro Presumido
    # Presunção de IRPJ e CSLL conforme atividade
    if atividade == "Serviços (Geral)":
        base_irpj, base_csll = 0.32, 0.32
    else: # Comércio/Indústria
        base_irpj, base_csll = 0.08, 0.12
        
    irpj_lp = (faturamento * base_irpj) * 0.15
    csll_lp = (faturamento * base_csll) * 0.09
    pis_cofins_lp = faturamento * 0.0365  cume cumulatividade padrão
    imposto_presumido = irpj_lp + csll_lp + pis_cofins_lp

    # 3. Lucro Real (Não-cumulativo)
    lucro_contabil = max(0, faturamento - despesas)
    irpj_lr = lucro_contabil * 0.15
    if lucro_contabil > 20000: # Adicional de IRPJ
        irpj_lr += (lucro_contabil - 20000) * 0.10
    
    csll_lr = lucro_contabil * 0.09
    
    # PIS/COFINS Não-cumulativo (9,25% bruto menos créditos)
    pis_cofins_bruto = faturamento * 0.0925
    pis_cofins_lr = max(0, pis_cofins_bruto - creditos)
    
    imposto_real = irpj_lr + csll_lr + pis_cofins_lr

    return [
        {
            "Regime": "Simples Nacional",
            "Imposto Mensal (R$)": imposto_simples,
            "Alíquota Efetiva": (imposto_simples / faturamento) * 100 if faturamento > 0 else 0
        },
        {
            "Regime": "Lucro Presumido",
            "Imposto Mensal (R$)": imposto_presumido,
            "Alíquota Efetiva": (imposto_presumido / faturamento) * 100 if faturamento > 0 else 0
        },
        {
            "Regime": "Lucro Real",
            "Imposto Mensal (R$)": imposto_real,
            "Alíquota Efetiva": (imposto_real / faturamento) * 100 if faturamento > 0 else 0
        }
    ]

# --- EXIBIÇÃO NA TELA ---
if executar_calculo:
    resultados = calcular_impostos(faturamento_mensal, despesas_mensais, folha_pagamento, creditos_tributarios, tipo_atividade)
    df_resultados = pd.DataFrame(resultados)
    
    # Descobrir o mais econômico
    mais_economico = min(resultados, key=lambda x: x["Imposto Mensal (R$)"])

    st.success(f"💡 **Recomendação Inicial:** O regime mais vantajoso para o seu perfil é o **{mais_economico['Regime']}** com uma carga tributária estimada de **R$ {mais_economico['Imposto Mensal (R$)']:,.2f}** mensais.")

    # Exibição em Métricas Lado a Lado
    col1, col2, col3 = st.columns(3)
    for i, col in enumerate([col1, col2, col3]):
        reg = resultados[i]
        col.metric(
            label=reg["Regime"],
            value=f"R$ {reg['Imposto Mensal (R$)']:,.2f}",
            delta=f"{reg['Alíquota Efetiva']:.2f}% efetivos",
            delta_color="inverse"
        )

    st.markdown("---")
    st.subheader("📋 Detalhamento Comparativo")
    
    # Formatando tabela para exibição amigável em Reais
    df_exibicao = df_resultados.copy()
    df_exibicao["Imposto Mensal (R$)"] = df_exibicao["Imposto Mensal (R$)"].map("R$ {:,.2f}".format)
    df_exibicao["Alíquota Efetiva"] = df_exibicao["Alíquota Efetiva"].map("{:.2f}%".format)
    
    st.table(df_exibicao)

    # Gráfico comparativo
    st.subheader("📊 Comparativo Visual de Carga Tributária")
    df_chart = pd.DataFrame({
        "Regime": [r["Regime"] for r in resultados],
        "Imposto Mensal": [r["Imposto Mensal (R$)"] for r in resultados]
    }).set_index("Regime")
    
    st.bar_chart(df_chart)

else:
    st.info("👈 Preencha os dados da empresa na barra lateral à esquerda e clique em **Calcular e Comparar Regimes** para ver a simulação.")
