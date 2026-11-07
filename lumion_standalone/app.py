"""LUMION visual update — compatible with the existing engine.py and storage.py."""
import html
import uuid
from pathlib import Path
import streamlit as st
from engine import SPECIES, CAPSULES, EVOLUTIONS, capture_rate, encounter
import storage

st.set_page_config(page_title='LUMION | 빛의 생명체', page_icon='🌙', layout='wide')
BASE = Path(__file__).resolve().parent
ASSETS = BASE / 'assets'

def asset(group, name):
    p = ASSETS / group / f'{name}.webp'
    return str(p) if p.is_file() else None

def creature_image(name, width=180):
    path = asset('creatures', name)
    if path:
        st.image(path, width=width)
    else:
        st.markdown('✨')

def notify(msg):
    st.session_state.notice = msg

st.markdown('''<style>
.stApp {background: radial-gradient(ellipse at 25% 0%, #26345b 0%, #11162c 45%, #090e20 100%);color:#f5f2ff}
.block-container {max-width:1150px;padding-top:1.5rem}
h1,h2,h3 {color:#f3ecff}
[data-testid="stMetric"] {background:rgba(35,47,84,.55);padding:14px;border:1px solid #485b86;border-radius:15px}
.stButton>button {border-radius:14px;min-height:44px;border:1px solid #7883bb}
.stButton>button[kind="primary"] {background:linear-gradient(100deg,#6553bd,#3184c7)}
.lumi-card {background:linear-gradient(120deg,rgba(43,43,83,.92),rgba(22,45,75,.9));border:1px solid #57679d;border-radius:22px;padding:19px;margin:10px 0}
.lumi-title {font-size:36px;font-weight:800;letter-spacing:4px;text-shadow:0 0 25px #8e8aff}
.lumi-caption {color:#c4c6ed}
@keyframes fadefloat {0%{transform:translateY(5px);opacity:.5}55%{transform:translateY(-4px);opacity:1}100%{transform:translateY(0);opacity:1}}
[data-testid="stImage"] img {border-radius:18px;animation:fadefloat 1s ease-out both;filter:drop-shadow(0 0 9px rgba(122,156,250,.25))}
</style>''', unsafe_allow_html=True)

if 'player' not in st.session_state:
    st.session_state.player = str(uuid.uuid4())
try:
    existing = st.query_params.get('player')
    if existing:
        st.session_state.player = str(uuid.UUID(existing))
    else:
        st.query_params['player'] = st.session_state.player
except (ValueError, TypeError):
    st.query_params['player'] = st.session_state.player
player = st.session_state.player
storage.init(player)
p = storage.snapshot(player)

st.markdown('<div class="lumi-title">✦ LUMION</div><div class="lumi-caption">수면으로 만나는 빛의 생명체 · 비주얼 업데이트</div>',unsafe_allow_html=True)
st.warning('현재는 테스트용 버전입니다. URL의 player 식별자로 기록을 구분하므로 링크를 다른 사람에게 공유하지 마세요. 공개 서비스에는 Supabase 인증 및 서버 권한 검증이 필요합니다.',icon='🔒')
if 'notice' in st.session_state:
    st.info(st.session_state.pop('notice'))
col1,col2,col3 = st.columns(3)
col1.metric('루미 코인',f"{p['coins']:,} 🪙")
col2.metric('보유 루미온',len(p['creatures']))
col3.metric('발견 도감',f"{len(p['discovered'])}/{len(SPECIES)}")
page=st.radio('메뉴',['🌲 탐험','🛒 상점','📚 도감','🎒 보관함','🌙 수면 기록'],horizontal=True)

if page=='🌲 탐험':
    e=p['active']
    if e:
        st.subheader('✨ 야생의 루미온을 만났어요!')
        a,b=st.columns([1,2],vertical_alignment='center')
        with a: creature_image(e['name'],320)
        with b:
            st.markdown(f"### {'🌈 오로라 ' if e['aurora'] else ''}{html.escape(e['name'])}")
            st.write(f"{e['element']} · {e['rarity']} · Lv.{e['level']}")
            st.write(f"남은 포획 시도: {2-e['attempts']}")
            available=[n for n,q in p['capsules'].items() if q>0]
            if available:
                cap=st.selectbox('캡슐 선택',available,format_func=lambda n:f'{n} ({p["capsules"][n]}개)')
                cimg=asset('items',cap)
                if cimg:st.image(cimg,width=88)
                chance=capture_rate(e['rarity'],e['level'],cap)
                st.progress(chance,text=f'포획 확률 {chance*100:.1f}%')
                if st.button('✨ 포획하기',type='primary',use_container_width=True):
                    notify(storage.capture(player,cap,capture_rate));st.rerun()
            else: st.info('캡슐이 없어요. 상점에서 구매하세요.')
            if st.button('탐험 종료 (도망가기)'):
                storage.flee(player);st.rerun()
    else:
        banner=asset('scenes','타이틀')
        if banner: st.image(banner,use_container_width=True)
        st.subheader('🌲 달빛 숲')
        scene=asset('scenes','달빛 숲')
        if scene:st.image(scene,use_container_width=True)
        if st.button('🔍 탐험 시작 · 10코인',type='primary',use_container_width=True,disabled=p['coins']<10):
            notify(storage.start(player,encounter));st.rerun()
        if p['coins']<10:st.info('코인이 부족해요. 일일 기록 보상을 받을 수 있어요.')
        st.caption('다른 탐험 지역은 이미지 미리보기만 제공하며, 지역별 등장 확률은 후속 버전에서 적용됩니다.')
        places=['꿈구름 계곡','서리 동굴','별빛 성역']
        cs=st.columns(3)
        for c,name in zip(cs,places):
            with c:
                pic=asset('scenes',name)
                if pic:st.image(pic,use_container_width=True)
                st.caption(name)

elif page=='🛒 상점':
    st.subheader('🛒 루미 캡슐 상점')
    for name,(price,mult) in CAPSULES.items():
        with st.container(border=True):
            a,b,c=st.columns([1,3,1],vertical_alignment='center')
            with a:
                pic=asset('items',name)
                if pic:st.image(pic,width=94)
            b.markdown(f'**{name}** · {price}코인 · 포획 배율 ×{mult} · 보유 {p["capsules"].get(name,0)}개')
            if c.button('구매',key='buy_'+name,disabled=p['coins']<price):
                notify(storage.buy(player,name,price));st.rerun()
    st.caption('경험치 사탕·진화석·회복제 이미지는 제작했지만, 구매 및 사용 기능은 아직 연결되지 않았습니다.')
    st.subheader('추가 아이템 디자인')
    cols=st.columns(4)
    for c,name in zip(cols,['루미 사탕','진화석','수면 회복제','집중의 물약']):
        with c:
            pic=asset('items',name)
            if pic:st.image(pic,use_container_width=True)
            st.caption(name)

elif page=='📚 도감':
    st.subheader('📚 루미온 도감 · 20종')
    rows=[SPECIES[i:i+5] for i in range(0,len(SPECIES),5)]
    for group in rows:
        cols=st.columns(5)
        for c,(name,element,rarity,weight,icon) in zip(cols,group):
            with c:
                known=name in p['discovered']
                if known:creature_image(name,165)
                else:st.markdown('### ❔')
                st.markdown(f'**{name if known else "???"}**')
                st.caption(f'{element} · {rarity}' if known else '미발견')

elif page=='🎒 보관함':
    st.subheader('🎒 내 루미온')
    if not p['creatures']:st.info('아직 포획한 루미온이 없어요.')
    for mon in p['creatures']:
        with st.container(border=True):
            a,b=st.columns([1,3],vertical_alignment='center')
            with a:creature_image(mon['name'],165)
            with b:
                st.markdown(f"**{'🌈 오로라 ' if mon['aurora'] else ''}{mon['name']}** · Lv.{mon['level']} · {mon['rarity']}")
                if mon['name'] in EVOLUTIONS:
                    target,lv=EVOLUTIONS[mon['name']]
                    if st.button(f'{target} 진화 (Lv.{lv} 필요)',key='evo_'+mon['id'],disabled=mon['level']<lv):
                        notify(storage.evolve(player,mon['id'],EVOLUTIONS));st.rerun()

else:
    st.subheader('🌙 오늘의 수면 기록')
    st.caption('연구용 수면 측정 기능은 아직 연결되지 않았습니다. 이 버전은 하루 한 번 기록 참여 보상만 제공합니다.')
    st.number_input('수면 시간 (시간)',0.0,24.0,8.0,0.5)
    st.slider('주관적 수면 만족도',1,5,3)
    st.caption('입력값은 아직 저장되거나 분석되지 않습니다. 보상은 수면 시간을 늘리는 것과 관계없이 하루 한 번만 지급됩니다.')
    if st.button('오늘의 기록 보상 받기 · 20코인',type='primary'):
        notify(storage.reward(player));st.rerun()
st.divider()
st.caption('오리지널 콘셉트 아트에서 잘라낸 게임용 이미지 시안입니다. 일부 이미지는 기존 캐릭터 이름과 임시 매칭되어 있습니다. 전투·실제 프레임 애니메이션·100종 완성은 후속 작업입니다.')
