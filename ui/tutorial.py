import streamlit as st


@st.cache_data()
def tutorial_loop(tutorial):
    # loop through the content and create a card for each row
    for i, each in enumerate(tutorial):
        # for each in tutorial:
        st.write(each["texto"])
        if each["imagem"]:
            st.image(each["imagem"], width="stretch")
        # show a divider between each step, except for the last one
        if i != len(tutorial) - 1:
            st.write("")


@st.cache_data()
def tutorial_expander(tutorial):
    col_tutorial_1, col_tutorial_2, col_tutorial_3 = st.columns([1, 4, 1])

    with col_tutorial_1:
        st.write("")

    with col_tutorial_2:
        tutorial_loop(tutorial)

    with col_tutorial_3:
        st.write("")


@st.cache_data()
def tutorial_bicsp():
    tutorial = [
        {
            "texto": "##### 1. Abrir o [BI CSP - Contratualização](https://bicsp.min-saude.pt/pt/contratualizacao/idg/Paginas/default.aspx)",
            "imagem": "content/tutorial_bicsp/tutorial_bicsp_1.png",
        },
        {
            "texto": "##### 2. Ir ao separador **UF - IDG - Indicadores**",
            "imagem": "content/tutorial_bicsp/tutorial_bicsp_2.png",
        },
        {
            "texto": "##### 3. Selecionar o 'Ano/Mês' e a 'Unidade'",
            "imagem": "content/tutorial_bicsp/tutorial_bicsp_3.png",
        },
        {
            "texto": "##### 4. Selecionar o **More optionss** nos ... do canto superior direito da tabela",
            "imagem": "content/tutorial_bicsp/tutorial_bicsp_4.png",
        },
        {
            "texto": "##### 5. Selecionar o botão **Export data**",
            "imagem": "content/tutorial_bicsp/tutorial_bicsp_5.png",
        },
        {
            "texto": "##### 6. Selecionar a 2ª ou 3ª opção, **Sumarized Data** ou **Underlying data** e selecionar o botão **Export**",
            "imagem": "content/tutorial_bicsp/tutorial_bicsp_6.png",
        },
        {
            "texto": "##### 7. Depois de gravar o ficheiro, arrastar (da pasta de transferencias) para o local de upload do mgfhub",
            "imagem": "content/tutorial_bicsp/tutorial_bicsp_7.png",
        },
    ]

    st.subheader("Como extrair o ficheiro excel necessário do BI-CSP?")

    tutorial_expander(tutorial)


@st.cache_data()
def tutorial_mimuf_depois_11_2025():
    tutorial = [
        {
            "texto": "##### 1. Abrir o MIM@UF e fazer login",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_1.png",
        },
        {
            "texto": "##### 2. Navegar para a pasta Indicadores",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_2.png",
        },
        {
            "texto": "##### 3. Pasta P02.01. Indicadores USF/UCSP'",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_3.png",
        },
        {
            "texto": "##### 4. Selecionar o relatório P02_01_R03. Indicadores por lista de utentes de médico",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_4.png",
        },
        # {
        #     "texto": "##### 5. ...",
        #     "imagem": "content/tutorial_mimuf/tutorial_mimuf_5.png",
        # },
        {
            "texto": "##### 5. Selecionar o Mês de Analise e o Ano de Contratualização e depois Executar Relatório",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_6.png",
        },
        {
            "texto": "##### 6. Executar Relatório",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_7.png",
        },
        {
            "texto": "##### 7. Vão ser necessários vários passos intermédios antes de exportar a tabela",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_8.png",
        },
        {
            "texto": "##### 8. Mudar para indicador Flutuante",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_9.png",
        },
        {
            "texto": "##### 9. Transformar o filtro Médico Familia para uma coluna na tabela, arrastando o filtro para a zona de colunas (drag-and-drop)",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_8_11_2025.png",
        },
        # {
        #     "texto": "##### 9. Transformar o filtro Médico Familia para uma coluna na tabela, passando com rato entre as duas colunas e clicar na lupa",
        #     "imagem": "content/tutorial_mimuf/tutorial_mimuf_10.png",
        # },
        # {
        #     "texto": "##### 10. Escrever Méd e selecionar Médico Familia",
        #     "imagem": "content/tutorial_mimuf/tutorial_mimuf_11.png",
        # },
        {
            "texto": "##### 10. Corrigir as linhas unificadas na Planilha e depois butão com colunas a amarelo",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_12_NOVO.png",
        },
        {
            "texto": "##### 11. Voltar ao Home e clicar no botão Exportar",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_13.png",
        },
        {
            "texto": '##### 12. Selecionar Excel com texto simples; MANTER ☑️ do "Exportar título do relatório"; MANTER ☑️ do "Exportar Informações de Pagina Por"; MANTER ☑️ do "Exportar detalhes do filtro"; Clicar em Exportar (permite incluir informação do médico para depois construir a equipa completa)',
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_14_NOVO.png",
        },
        {
            "texto": "##### 13. Abrir ficheiro no Excel",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_15.png",
        },
        {
            "texto": "##### 14. Exportar como Livro",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_16.png",
        },
        {
            "texto": "##### 15. Fazer o upload do ficheiro para o mgfhub",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_17.png",
        },
    ]

    st.success(
        "O tutorial do MIM@UF depois de Novembro de 2025 já inclui a funcionalidade de drag-and-drop de filtros para colunas, pelo que não é necessário fazer upload de ficheiros com apenas 1 médico. Basta extrair todos os médicos como dantes. Pode ser necessário corrigir algumas linhas unificadas na folha de cálculo, conforme explicado no tutorial."
    )
    
    tutorial_expander(tutorial)
    
    
@st.cache_data()
def tutorial_mimuf():
    tutorial = [
        {
            "texto": "##### 1. Abrir o MIM@UF e fazer login",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_1.png",
        },
        {
            "texto": "##### 2. Navegar para a pasta Indicadores",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_2.png",
        },
        {
            "texto": "##### 3. Pasta P02.01. Indicadores USF/UCSP'",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_3.png",
        },
        {
            "texto": "##### 4. Selecionar o relatório P02_01_R03. Indicadores por lista de utentes de médico",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_4.png",
        },
        # {
        #     "texto": "##### 5. ...",
        #     "imagem": "content/tutorial_mimuf/tutorial_mimuf_5.png",
        # },
        {
            "texto": "##### 5. Selecionar o Mês de Analise e o Ano de Contratualização e depois Executar Relatório",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_6.png",
        },
        {
            "texto": "##### 6. Executar Relatório",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_7.png",
        },
        {
            "texto": "##### 7. Vão ser necessários vários passos intermédios antes de exportar a tabela",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_8.png",
        },
        {
            "texto": "##### 8. Selecionar o Médico Familia (já não se faz o passo de transformar em coluna, agora é necessário fazer uma extração por cada médico)",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_8_NOVO.png",
        },
        {
            "texto": "##### 9. Mudar para indicador Flutuante",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_9.png",
        },
        # {
        #     "texto": "##### 9. Transformar o filtro Médico Familia para uma coluna na tabela, passando com rato entre as duas colunas e clicar na lupa",
        #     "imagem": "content/tutorial_mimuf/tutorial_mimuf_10.png",
        # },
        # {
        #     "texto": "##### 10. Escrever Méd e selecionar Médico Familia",
        #     "imagem": "content/tutorial_mimuf/tutorial_mimuf_11.png",
        # },
        {
            "texto": "##### 10. Corrigir as linhas unificadas na Planilha e depois butão com colunas a amarelo",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_12_NOVO.png",
        },
        {
            "texto": "##### 11. Voltar ao Home e clicar no botão Exportar",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_13.png",
        },
        {
            "texto": '##### 12. Selecionar Excel com texto simples; MANTER ☑️ do "Exportar título do relatório"; MANTER ☑️ do "Exportar Informações de Pagina Por"; MANTER ☑️ do "Exportar detalhes do filtro"; Clicar em Exportar (permite incluir informação do médico para depois construir a equipa completa)',
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_14_NOVO.png",
        },
        {
            "texto": "##### 13. Abrir ficheiro no Excel",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_15.png",
        },
        {
            "texto": "##### 14. Exportar como Livro",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_16.png",
        },
        {
            "texto": "##### 15. Fazer o upload do ficheiro para o mgfhub",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_17.png",
        },
    ]

    st.subheader(
        "Como extrair o ficheiro excel necessário do MIM@UF (nova versão depois de 10/2025)"
    )

    #     st.success(
    #         """
    # #### Resumo das alterações:
    # Já não se faz o passo da lupa para transformar o filtro Médico Familia em coluna (esta funcionalidade foi removida do MIM@UF).
    # Para ultrapassar esta limitação agora é necessário:
    # - Fazer uma extração por cada médico do mesmo relatório (P02_01_R03. Indicadores por lista de utentes de médico).
    # - Antes de exportar, garantir que estão selecionados ☑️ em "Exportar título do relatório", ☑️ "Exportar Informações de Pagina Por" e ☑️ "Exportar detalhes do filtro" (dantes eram pedidos para retirar, mas na realidade têm informação útil que permite a identificação automática do médico, particularmente útil na nova solução).
    # - No fim, fazer o upload dos ficheiros todos para o mgfhub no mesmo local, que faz a junção automática dos dados.

    # Os ficheiros antigos do MIM@UF continuam a funcionar, não é necessário voltar a extrair os que já funcionavam antes da alteração para fazer visões temporais.

    # O tutorial que se segue já contempla os novos passos para a extração correta.
    # """
    #     )

    tutorial_expander(tutorial)


@st.cache_data()
def tutorial_mimuf_antigo():
    tutorial = [
        {
            "texto": "##### 1. Abrir o MIM@UF e fazer login",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_1.png",
        },
        {
            "texto": "##### 2. Navegar para a pasta Indicadores",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_2.png",
        },
        {
            "texto": "##### 3. Pasta P02.01. Indicadores USF/UCSP'",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_3.png",
        },
        {
            "texto": "##### 4. Selecionar o relatório P02_01_R03. Indicadores por lista de utentes de médico",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_4.png",
        },
        # {
        #     "texto": "##### 5. ...",
        #     "imagem": "content/tutorial_mimuf/tutorial_mimuf_5.png",
        # },
        {
            "texto": "##### 5. Selecionar o Mês de Analise e o Ano de Contratualização e depois Executar Relatório",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_6.png",
        },
        {
            "texto": "##### 6. Executar Relatório",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_7.png",
        },
        {
            "texto": "##### 7. Vão ser necessários vários passos intermédios antes de exportar a tabela",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_8.png",
        },
        {
            "texto": "##### 8. Mudar para indicador Flutuante",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_9.png",
        },
        {
            "texto": "##### 9. Transformar o filtro Médico Familia para uma coluna na tabela, passando com rato entre as duas colunas e clicar na lupa",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_10.png",
        },
        {
            "texto": "##### 10. Escrever Méd e selecionar Médico Familia",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_11.png",
        },
        {
            "texto": "##### 11. Corrigir as linas unificadas na Planilha e depois butão com colinas a amarelo",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_12.png",
        },
        {
            "texto": "##### 12. Voltar ao Home e clicar no botão Exportar",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_13.png",
        },
        {
            "texto": '##### 13. Selecionar Excel com texto simples; Tirar ☑️ do "Exportar título do relatório"; Tirar ☑️ do "Exportar Informações de Pagina Por"; Tirar ☑️ do "Exportar detalhes do filtro"; Clicar em Exportar',
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_14.png",
        },
        {
            "texto": "##### 14. Abrir o Excel",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_15.png",
        },
        {
            "texto": "##### 16. Exportar como Livro",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_16.png",
        },
        {
            "texto": "##### 17. Fazer o upload dos ficheiros para o mgfhub",
            "imagem": "content/tutorial_mimuf/tutorial_mimuf_17.png",
        },
    ]

    st.subheader("Como extrair o ficheiro excel necessário do MIM@UF (versão Antiga)")

    # st.warning(
    #     """Neste momento não funciona porque a funcionalidade de transformar o filtro Médico Familia em coluna foi removida do MIM@UF, que permitia colocar a unidade toda num unico ficheiro. Agora é necessário fazer a extração por cada médico. Ver o tutorial do **MIM@UF depois 10/2025**."""
    # )

    tutorial_expander(tutorial)
