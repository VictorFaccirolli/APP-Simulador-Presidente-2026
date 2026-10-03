from io import BytesIO
from pathlib import Path
import json
import base64
from html import escape
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import streamlit as st
from calculo import calcular, participacao, ELEITORADO, FONTE_ELEITORADO

st.set_page_config(page_title='Simulador Presidencial 2026', page_icon='📊', layout='wide')
st.markdown("""<style>
.block-container{padding-top:2.5rem;max-width:1200px}h1{color:#153e60;font-size:clamp(1.75rem,3.2vw,2.65rem)!important;line-height:1.18!important}
div[data-testid="stMetric"]{background:#eef5fb;border-radius:12px;padding:12px}
.author-banner{background:linear-gradient(110deg,#102f49,#1c5470);border-left:5px solid #6bd0bd;border-radius:14px;padding:22px 26px;margin:0 0 24px;color:white;box-shadow:0 5px 20px #102f4910}
.author-eyebrow{font-family:Arial,sans-serif;font-size:11px;letter-spacing:2.2px;font-weight:700;color:#a9ded9;margin-bottom:5px}
.author-name{font-family:Georgia,'Times New Roman',serif;font-size:clamp(1.5rem,3vw,2.1rem);font-weight:700;line-height:1.3}
.author-detail{font-family:Arial,sans-serif;font-size:12px;color:#c7dbe5;margin-top:7px}
.candidate-card{display:flex;gap:14px;align-items:center;margin:14px 0 4px;padding:12px;border:1px solid #e0e9ef;border-radius:12px;background:#f4f8fb;color:#18354b}
.candidate-photo{width:66px;height:88px;object-fit:contain;border-radius:6px;background:white;flex-shrink:0}
.candidate-placeholder{width:66px;height:88px;display:flex;align-items:center;justify-content:center;border-radius:6px;background:#e0e9ef;font-size:28px}
.candidate-name{font-weight:700;font-size:16px}.candidate-detail{font-size:12px;color:#52697a;margin-top:4px}
@media(max-width:640px){.author-banner{padding:18px}.candidate-card{gap:10px}.candidate-name{font-size:14px}}
</style>""", unsafe_allow_html=True)
st.markdown('<div class="author-banner"><div class="author-eyebrow">SOFTWARE DESENVOLVIDO POR</div><div class="author-name">Eng. Victor Faccirolli</div><div class="author-detail">Simulador de Presidente • Eleições 2026 • Versão 1.2</div></div>', unsafe_allow_html=True)
st.title('Simulador Presidencial 2026')
st.write('Monte seu cenário com abstenção, votação dos candidatos, brancos e nulos. Veja as quantidades estimadas, os votos válidos e o resultado de primeiro ou segundo turno.')
st.caption('Simulação baseada nos valores informados pelo usuário. Não é pesquisa eleitoral nem previsão estatística.')
st.metric('Eleitorado apto — base fixa do TSE', f'{ELEITORADO:,}'.replace(',', '.'), help='Eleitorado das Eleições 2026, incluindo brasileiros inscritos no exterior. Fonte: TSE, publicada em 20/07/2026 e consultada em 02/10/2026.')
st.caption(f'[Fonte oficial do eleitorado — TSE]({FONTE_ELEITORADO}) • 918.876 eleitores no exterior já estão incluídos; não somar novamente.')
base = Path(__file__).parent
fotos = json.loads((base / 'fotos.json').read_text(encoding='utf-8'))
nomes_base = json.loads((base / 'candidatos.json').read_text(encoding='utf-8'))
with st.expander('Configurar candidatos'):
    texto = st.text_area('Um candidato por linha — você pode acrescentar, retirar ou corrigir nomes.', '\n'.join(nomes_base), height=260)
    st.caption('Fotos e identificação: base do TSE de 02/10/2026, 08:31. Lista inicial do simulador mantida. Confirme alterações de registro no DivulgaCandContas do TSE.')
nomes = [n.strip() for n in texto.splitlines() if n.strip()]
if len(nomes) < 2 or len(nomes) != len(set(nomes)):
    st.error('Informe pelo menos dois candidatos, sem nomes repetidos.'); st.stop()
modo = st.radio('Como deseja preencher?', ['Percentuais', 'Votos'], horizontal=True)
st.caption('Percentuais: candidatos + brancos + nulos devem somar 100% de quem comparece. A abstenção é informada separadamente, como percentual do eleitorado apto. Votos: a soma deve corresponder ao comparecimento estimado.')
abstencao = st.number_input('Abstenção estimada (% do eleitorado apto)', min_value=0.0, max_value=100.0, value=0.0, step=0.1, format='%.2f', help='Percentual de pessoas aptas que não irão votar. Ex.: 20% reduz o comparecimento para 80% do eleitorado. Não some este percentual aos candidatos, brancos e nulos.')
ausentes, presentes = participacao(abstencao)
c1, c2 = st.columns(2)
c1.metric('Ausentes estimados', f'{ausentes:,}'.replace(',', '.'))
c2.metric('Comparecimento estimado', f'{presentes:,}'.replace(',', '.'))
with st.form('cenario'):
    titulo = st.text_input('Nome do cenário / responsável', placeholder='Ex.: Cenário do Victor')
    cols = st.columns(2)
    entradas = {}
    for i, nome in enumerate(nomes):
        with cols[i % 2]:
            cadastro = fotos.get(nome)
            if cadastro and (base / cadastro['foto']).is_file():
                b64 = base64.b64encode((base / cadastro['foto']).read_bytes()).decode('ascii')
                retrato = f'<img class="candidate-photo" src="data:image/jpeg;base64,{b64}" alt="Foto de {escape(nome)}">'
                detalhe = f"Número {cadastro['numero']} • Foto oficial do cadastro TSE"
            else:
                retrato = '<div class="candidate-placeholder">👤</div>'
                detalhe = 'Foto não cadastrada'
            st.markdown(f'<div class="candidate-card">{retrato}<div><div class="candidate-name">{escape(nome)}</div><div class="candidate-detail">{escape(detalhe)}</div></div></div>', unsafe_allow_html=True)
            entradas[nome] = st.number_input(nome, min_value=0.0 if modo == 'Percentuais' else 0, max_value=100.0 if modo == 'Percentuais' else 1000000000, value=0.0 if modo == 'Percentuais' else 0, step=0.1 if modo == 'Percentuais' else 1000, format='%.2f' if modo == 'Percentuais' else '%d', key=f'{modo}_{nome}', help='Informe o percentual entre quem comparece, ou a quantidade de votos deste candidato. Zero significa nenhum voto neste cenário.')
    cols = st.columns(2)
    extras = []
    for col, label in zip(cols, ['Brancos', 'Nulos']):
        with col:
            extras.append(st.number_input(label, min_value=0.0 if modo == 'Percentuais' else 0, max_value=100.0 if modo == 'Percentuais' else 1000000000, value=0.0 if modo == 'Percentuais' else 0, step=0.1 if modo == 'Percentuais' else 1000, format='%.2f' if modo == 'Percentuais' else '%d', key=f'{modo}_{label}', help='Informe o percentual entre quem comparece, ou a quantidade de votos. Brancos e nulos não são votos válidos.'))
    enviar = st.form_submit_button('Calcular resultado e gerar gráficos', type='primary', width='stretch')
if enviar:
    try:
        r = calcular(entradas, *extras, modo=modo, abstencao_pct=abstencao)
        st.session_state['resultado'] = r
        st.session_state['titulo_resultado'] = titulo or 'Cenário sem nome'
    except ValueError as e:
        st.session_state.pop('resultado', None)
        st.error(str(e))
r = st.session_state.get('resultado')
if r:
    st.divider()
    st.subheader(st.session_state['titulo_resultado'])
    st.caption('Resultado do último cálculo. Após alterar os campos, clique em Calcular novamente.')
    participacao_cols = st.columns(3)
    participacao_cols[0].metric('Abstenção do cenário', f"{r['abstencao_pct']:.2f}%", f"{r['ausentes']:,} ausentes".replace(',', '.'), delta_color='off')
    participacao_cols[1].metric('Comparecimento do cenário', f"{r['comparecimento']:,}".replace(',', '.'))
    participacao_cols[2].metric('Votos válidos estimados', f"{r['validos_qtd']:,}".replace(',', '.'))
    cols = st.columns(3)
    cols[0].metric('Válidos (% de quem comparece)', f"{r['validos']/r['total']*100:.2f}%")
    cols[1].metric('Brancos e nulos (% de quem comparece)', f"{(r['brancos']+r['nulos'])/r['total']*100:.2f}%")
    cols[2].metric('Líder (% dos válidos)', f"{r['linhas'][0]['% dos válidos']:.2f}%")
    if r['vencedor']:
        mensagem = f"{r['vencedor']} venceria no primeiro turno neste cenário: mais de 50% dos votos válidos."
        st.success(mensagem)
    elif r['empate']:
        mensagem = 'Haveria segundo turno, com empate que afeta a definição das vagas: ' + ', '.join(r['empatados']) + '. A escolha exige aplicação do critério legal de desempate (maior idade).'
        st.warning(mensagem)
    else:
        mensagem = 'Haveria segundo turno neste cenário: ' + ' e '.join(r['segundo_turno']) + '.'
        st.info(mensagem)
    if r['modo'] == 'Percentuais':
        st.caption('Quantidades estimadas arredondadas por maiores restos para preservar a soma. Os percentuais e a decisão usam os percentuais originais, sem arredondamento.')
    st.caption('Exatamente 50% não garante vitória. A decisão usa os valores completos, sem arredondar; a exibição usa duas casas decimais.')
    df = pd.DataFrame(r['linhas'])
    st.dataframe(df, hide_index=True, width='stretch', column_config={'% do total': st.column_config.NumberColumn(format='%.2f%%'), '% dos válidos': st.column_config.NumberColumn(format='%.2f%%'), 'Valor informado': st.column_config.NumberColumn(format='%.2f' if r['modo'] == 'Percentuais' else '%d')})
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.spines.top': False, 'axes.spines.right': False})
    fig, ax = plt.subplots(figsize=(11, max(5, len(df)*.42)))
    ax.barh(df['Candidato'][::-1], df['% dos válidos'][::-1], color='#247a99')
    ax.axvline(50, color='#c27718', linestyle='--', label='50%: é necessário superar esta marca')
    for i, v in enumerate(df['% dos válidos'][::-1]):
        ax.text(v + .7, i, f'{v:.2f}%', va='center', fontsize=9)
    ax.set_xlim(0, 110); ax.set_xlabel('% dos votos válidos'); ax.set_title('Votação por candidato — votos válidos', loc='left', pad=18)
    ax.legend(loc='lower right', fontsize=8)
    fig.text(.99, .01, 'Simulação do usuário • Desenvolvido por Victor Faccirolli', ha='right', fontsize=8, color='#666666')
    fig.tight_layout(rect=(0,.04,1,1))
    st.pyplot(fig)
    fig2, ax2 = plt.subplots(figsize=(8,4.5))
    ax2.bar(['Válidos','Brancos','Nulos'], [r['validos']/r['total']*100,r['brancos']/r['total']*100,r['nulos']/r['total']*100], color=['#247a99','#9aabb5','#56616b'])
    for p in ax2.patches:
        ax2.annotate(f'{p.get_height():.2f}%', (p.get_x()+p.get_width()/2,p.get_height()), ha='center', va='bottom')
    ax2.set_ylim(0,110); ax2.set_ylabel('% de quem comparece'); ax2.set_title('Composição da votação', loc='left', pad=14)
    fig2.tight_layout(); st.pyplot(fig2)
    fig3, ax3 = plt.subplots(figsize=(9,5))
    valores = [r['validos_qtd'], r['brancos_qtd'], r['nulos_qtd'], r['ausentes']]
    ax3.bar(['Válidos', 'Brancos', 'Nulos', 'Abstenção'], [v/r['eleitorado']*100 for v in valores], color=['#247a99','#9aabb5','#56616b','#c27718'])
    for p, v in zip(ax3.patches, valores):
        ax3.annotate(f"{v/r['eleitorado']*100:.2f}%\n{v:,}".replace(',', '.'), (p.get_x()+p.get_width()/2, p.get_height()), ha='center', va='bottom', fontsize=9)
    ax3.set_ylim(0,115); ax3.set_ylabel('% do eleitorado apto'); ax3.set_title('Eleitorado: participação e abstenção', loc='left', pad=14)
    fig3.text(.99,.01,'Simulação do usuário • Eng. Victor Faccirolli',ha='right',fontsize=8,color='#666666')
    fig3.tight_layout(rect=(0,.04,1,1)); st.pyplot(fig3)
    for i, figura in enumerate([fig, fig2, fig3], 1):
        buffer = BytesIO(); figura.savefig(buffer, format='png', dpi=200, bbox_inches='tight')
        st.download_button(f'Baixar gráfico {i} (PNG)', buffer.getvalue(), f'grafico_{i}.png', 'image/png', key=f'png{i}')
        plt.close(figura)
    st.download_button('Baixar tabela (CSV)', df.to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig'), 'resultado.csv', 'text/csv')
    resumo = dict(cenario=st.session_state['titulo_resultado'], resultado=mensagem, **r)
    st.download_button('Baixar cenário e resultado (JSON)', json.dumps(resumo, ensure_ascii=False, indent=2), 'cenario.json', 'application/json')
with st.expander('Como o cálculo funciona'):
    st.write('Votos válidos = soma dos votos dos candidatos. Percentual válido = votos do candidato ÷ votos válidos × 100. Vitória no primeiro turno exige mais de 50% dos votos válidos. Brancos e nulos não entram no denominador. Abstenção é o não comparecimento e também não entra. Com a distribuição percentual mantida, mudar apenas a abstenção altera as quantidades estimadas, mas não altera os percentuais válidos dos candidatos.')
    st.markdown('[Regras e informações do TSE](https://www.tse.jus.br/comunicacao/noticias/2022/Outubro/votos-em-branco-ou-nulos-nao-sao-transferidos-para-o-vencedor-nem-cancelam-uma-eleicao) · [DivulgaCandContas](https://divulgacandcontas.tse.jus.br/)')
