import streamlit as st
import streamlit.components.v1 as components
import uuid,html
from engine import SPECIES,CAPSULES,EVOLUTIONS,capture_rate,encounter
import storage
st.set_page_config(page_title='LUMION | 달빛 숲',page_icon='🌙',layout='wide')
st.markdown('''<style>.stApp{background:linear-gradient(145deg,#11172c,#211c3c 65%,#151f32);color:#f4f1ff}.block-container{max-width:1050px}.stButton>button{border-radius:14px;min-height:46px}.hero{padding:25px;border-radius:22px;background:linear-gradient(120deg,#302650,#172b48);border:1px solid #655c88;text-align:center}.glow{font-size:105px;display:inline-block;animation:float 3.8s ease-in-out infinite,shine 5s ease-in-out infinite;filter:drop-shadow(0 0 20px #d6b6ff)}@keyframes float{0%,100%{transform:translateY(0) rotate(-2deg)}50%{transform:translateY(-15px) rotate(2deg)}}@keyframes shine{0%,100%{filter:drop-shadow(0 0 12px #a2aaff)}50%{filter:drop-shadow(0 0 28px #ffdbac)}}.aurora{color:#9efde5;font-weight:800}</style>''',unsafe_allow_html=True)
if 'player' not in st.session_state:st.session_state.player=str(uuid.uuid4())
# For this local demo, the player ID is persisted in the URL and can be bookmarked.
try:
    existing=st.query_params.get('player')
    if existing:st.session_state.player=str(uuid.UUID(existing))
    else:st.query_params['player']=st.session_state.player
except (ValueError,TypeError):st.query_params['player']=st.session_state.player
player=st.session_state.player
storage.init(player)
def notify(msg):st.session_state['notice']=msg
p=storage.snapshot(player)
st.title('🌙 LUMION')
st.caption('루미나리아의 달빛 숲 · 독립 실행 데모')
if 'notice' in st.session_state:st.info(st.session_state.pop('notice'))
st.warning('이 버전은 개인용 로컬 데모입니다. URL의 player 값이 계정 식별자이므로 공유하지 마세요. 공개 서비스에는 인증과 서버 권한 검증이 필요합니다.',icon='🔒')
a,b,c=st.columns(3)
a.metric('루미 코인',f"{p['coins']:,} 🪙")
b.metric('보유 루미온',len(p['creatures']))
c.metric('발견 도감',f"{len(p['discovered'])}/{len(SPECIES)}")
page=st.radio('메뉴',['🌲 탐험','🛒 상점','📚 도감','🎒 보관함','🌙 수면 기록'],horizontal=True)
if page=='🌲 탐험':
    e=p['active']
    if e:
        st.markdown(f'''<div class="hero"><div class="glow">{html.escape(e['icon'])}</div><h2>{'✨ 오로라 ' if e['aurora'] else ''}{html.escape(e['name'])}</h2><p>{html.escape(e['element'])} · {html.escape(e['rarity'])} · Lv.{e['level']}</p><p>남은 포획 시도: {2-e['attempts']}</p></div>''',unsafe_allow_html=True)
        available=[n for n,q in p['capsules'].items() if q>0]
        if available:
            cap=st.selectbox('캡슐 선택',available,format_func=lambda n:f'{n} ({p["capsules"][n]}개)')
            st.progress(capture_rate(e['rarity'],e['level'],cap),text=f'포획 성공 확률 {capture_rate(e["rarity"],e["level"],cap)*100:.1f}%')
            if st.button('✨ 포획하기',type='primary',use_container_width=True):
                notify(storage.capture(player,cap,capture_rate));st.rerun()
        else:st.info('캡슐이 없어요. 상점에서 구매할 수 있어요.')
        if st.button('탐험 종료 (도망가기)'):
            storage.flee(player);st.rerun()
    else:
        st.markdown('<div class="hero"><div class="glow">🌲</div><h2>달빛 숲</h2><p>별빛이 내려앉은 숲에서 새로운 루미온을 발견해 보세요.</p></div>',unsafe_allow_html=True)
        if st.button('🔍 탐험 시작 · 10코인',type='primary',use_container_width=True,disabled=p['coins']<10):
            notify(storage.start(player,encounter));st.rerun()
        if p['coins']<10:st.info('코인이 부족해요. 기록 보상으로 코인을 얻을 수 있어요.')
elif page=='🛒 상점':
    st.subheader('루미 캡슐 상점')
    for name,(price,mult) in CAPSULES.items():
        left,right=st.columns([3,1]);left.write(f'**{name}** · {price}코인 · 포획 배율 ×{mult} · 보유 {p["capsules"].get(name,0)}개')
        if right.button('구매',key='buy_'+name,disabled=p['coins']<price):
            notify(storage.buy(player,name,price));st.rerun()
elif page=='📚 도감':
    st.subheader('달빛 숲 도감 · 20종')
    for name,element,rarity,weight,icon in SPECIES:
        known=name in p['discovered'];st.write(f'{icon if known else "❔"} **{name if known else "???"}** · {element if known else "미발견"} · {rarity if known else ""}')
elif page=='🎒 보관함':
    st.subheader('내 루미온')
    if not p['creatures']:st.info('아직 포획한 루미온이 없어요.')
    for c in p['creatures']:
        with st.container(border=True):
            st.write(f"{c['icon']} **{'✨ 오로라 ' if c['aurora'] else ''}{c['name']}** · Lv.{c['level']} · {c['rarity']}")
            if c['name'] in EVOLUTIONS:
                target,lv=EVOLUTIONS[c['name']]
                if st.button(f'{target} 진화 (Lv.{lv} 필요)',key='evo_'+c['id'],disabled=c['level']<lv):
                    notify(storage.evolve(player,c['id'],EVOLUTIONS));st.rerun()
else:
    st.subheader('오늘의 수면 기록')
    st.caption('연구용 측정 기능은 아직 연결되지 않았습니다. 현재는 하루 한 번 기록 참여 보상만 제공해요.')
    hours=st.number_input('수면 시간 (시간)',0.0,24.0,8.0,0.5)
    quality=st.slider('주관적 수면 만족도',1,5,3)
    st.caption('현재 데모에서는 이 값들을 저장하거나 분석하지 않습니다.')
    if st.button('오늘의 기록 보상 받기 · 20코인',type='primary'):
        notify(storage.reward(player));st.rerun()
st.divider()
st.caption('이미지는 아직 제작 중이므로 이 버전에서는 이모지와 CSS 연출을 사용합니다. 24프레임 이상의 실제 애니메이션은 이미지 제작 후 연결할 수 있습니다.')
