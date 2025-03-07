import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
from datetime import datetime, timedelta

# Connexion à la base de données
engine = create_engine("mysql+pymysql://laura:wRnCeNuwja7FKK#nJD&4@tadiplus-kpis.cxkqmacg4kk3.eu-central-1.rds.amazonaws.com/support_kpis")

# Requête SQL
query = '''
    SELECT
        t.*,
        a.agent,
        g.group AS group_name
    FROM
        v3_tickets_distribution_by_group_and_agent t
    LEFT JOIN
        fd_agent_id a ON t.agent_id = a.agent_id
    LEFT JOIN
        fd_group_id g ON t.group_id = g.group_id
'''
df = pd.read_sql(query, engine)

# Convertir la colonne 'date' en type datetime
df['date'] = pd.to_datetime(df['date'])

# Liste des agents à afficher
agents_to_display = [
    "Lisette Hapke", "Kerstin Rosskamp", "Sebastian Grund", "David Priemer",
    "Daniela Kolb", "Mario Krieger", "Christopher Loehr", "Jochen Wittmann",
    "Marion Nebrich", "Andreas Hombergs", "Michael Doodt", "Gabi Tiedtke",
    "Kayleigh Perkins", "Jacqueline Forstner", "Samuel Siegle", "Barbara Habermann",
    "Sandra Bulka", "Holger Koepff"
]

# Filtrer les données pour n'afficher que ces agents
df = df[df['agent'].isin(agents_to_display)]

# Sélection des dates - Par défaut la semaine en cours
today = datetime.today()
start_date = today - timedelta(days=today.weekday())  # Lundi de la semaine en cours
end_date = start_date + timedelta(days=6)  # Dimanche de la semaine en cours

# Sélection des dates via Streamlit
start_date_input = st.sidebar.date_input('Start Date', start_date)
end_date_input = st.sidebar.date_input('End Date', end_date)

# Sélection des agents
select_all_agents = st.sidebar.button("Select All Agents")
if select_all_agents:
    selected_agents = df['agent'].unique()
else:
    selected_agents = st.sidebar.multiselect('Select Agents', options=df['agent'].unique(), default=df['agent'].unique())

# Sélection des groupes
select_all_groups = st.sidebar.button("Select All Groups")
if select_all_groups:
    selected_groups = df['group_name'].unique()
else:
    selected_groups = st.sidebar.multiselect('Select Groups', options=df['group_name'].unique(), default=df['group_name'].unique())

# Filtrer les données selon les sélections
df_filtered = df[(df['date'] >= pd.to_datetime(start_date_input)) & (df['date'] <= pd.to_datetime(end_date_input))]
df_filtered = df_filtered[df_filtered['agent'].isin(selected_agents)]
df_filtered = df_filtered[df_filtered['group_name'].isin(selected_groups)]

# Calculer le total des tickets traités
total_tickets = df_filtered['occurrences'].sum()

# Affichage du total de tickets en haut du dashboard
st.markdown(f"### Total Tickets Processed: {total_tickets:,}")

# Filtrer les données pour Total Tadiplus (agents totaux)
total_agents = [
    "Lisette Hapke", "Kerstin Rosskamp", "Sebastian Grund", "David Priemer",
    "Daniela Kolb", "Mario Krieger", "Christopher Loehr", "Jochen Wittmann",
    "Marion Nebrich", "Andreas Hombergs", "Michael Doodt", "Gabi Tiedtke",
    "Kayleigh Perkins", "Jacqueline Forstner", "Samuel Siegle", "Barbara Habermann",
    "Sandra Bulka", "Holger Koepff"
]

# Appliquer également le filtre de date sur Total Tadiplus
df_total_tadiplus = df[(df['agent'].isin(total_agents)) & (df['date'] >= pd.to_datetime(start_date_input)) & (df['date'] <= pd.to_datetime(end_date_input))]
df_total_tadiplus_group = df_total_tadiplus.groupby('group_name')['occurrences'].sum().reset_index()

# Graphique 1 : Tickets par groupe (Total Tadiplus)
group_data = df_filtered.groupby('group_name')['occurrences'].sum().reset_index()
group_data = group_data.sort_values(by='occurrences', ascending=False)  # Ordre décroissant

fig_group = px.bar(group_data, x='group_name', y='occurrences', title="🎟️ Tickets by Group", text='occurrences')
fig_group.update_traces(textposition='outside', marker=dict(color='rgb(6, 47, 104)'))  # Couleur Total Tadiplus
fig_group.update_layout(
    xaxis_title="Groups",
    yaxis_title="Number of Tickets",
    yaxis=dict(
        autorange=True,  # Permet d'ajuster automatiquement les limites de l'axe Y
        showgrid=True,
        showline=True,
        ticks='outside',
        tickangle=45
    ),
    height=600,  # Ajuste la hauteur du graphique
    margin=dict(l=50, r=50, t=50, b=100)  # Ajuste les marges pour les axes
)

# Graphique 2 : Tickets par agent et groupe + Total Tadiplus
df_agents_group = df_filtered.groupby(['group_name', 'agent'])['occurrences'].sum().reset_index()
df_agents_group = df_agents_group.sort_values(by='occurrences', ascending=False)  # Tri par ordre décroissant

# Créer une couleur pour chaque agent
color_map = {agent: px.colors.qualitative.Set1[i % len(px.colors.qualitative.Set1)] for i, agent in enumerate(df_agents_group['agent'].unique())}

# Ajouter Total Tadiplus dans le graphique 2
df_total_tadiplus_group['agent'] = 'Total Tadiplus'
df_total_tadiplus_group['occurrences'] = df_total_tadiplus_group['occurrences']

# Fusionner Total Tadiplus avec les agents
df_combined = pd.concat([df_agents_group, df_total_tadiplus_group[['group_name', 'agent', 'occurrences']]])

# Forcer la couleur "Total Tadiplus" à être la couleur définie : rgb(6, 47, 104)
color_map['Total Tadiplus'] = 'rgb(6, 47, 104)'

# S'assurer que "Total Tadiplus" soit toujours en première position
df_combined['sort_order'] = df_combined['agent'].apply(lambda x: 0 if x == 'Total Tadiplus' else 1)
df_combined = df_combined.sort_values(by=['group_name', 'sort_order', 'occurrences'], ascending=[True, True, False])

# Triez les groupes en fonction des occurrences de Total Tadiplus
total_tadiplus_order = df_total_tadiplus_group.sort_values(by='occurrences', ascending=False)['group_name'].tolist()
df_combined['group_name'] = pd.Categorical(df_combined['group_name'], categories=total_tadiplus_order, ordered=True)
df_combined = df_combined.sort_values('group_name')

fig_agent = px.bar(
    df_combined,
    x='group_name',
    y='occurrences',
    color='agent',
    title="🎟️ Tickets by Agent and Group + Total Tadiplus",
    text='occurrences',
    barmode='group',  # Barres groupées (Total vs agents)
    color_discrete_map=color_map  # Appliquer la carte de couleurs
)
fig_agent.update_traces(textposition='outside')
fig_agent.update_layout(
    xaxis_title="Groups",
    yaxis_title="Number of Tickets",
    yaxis=dict(
        autorange=True,  # Permet d'ajuster automatiquement les limites de l'axe Y
        showgrid=True,
        showline=True,
        ticks='outside',
        tickangle=45
    ),
    height=600,  # Ajuste la hauteur du graphique
    margin=dict(l=50, r=50, t=50, b=100)  # Ajuste les marges pour les axes
)

# Affichage des graphiques
st.plotly_chart(fig_group)
st.plotly_chart(fig_agent)
