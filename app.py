"""LUMION — original creature collecting sleep companion, Streamlit edition."""
import json, html, random
from datetime import datetime, timezone, timedelta
from pathlib import Path
import streamlit as st
from engine import (CATALOG,AREAS,CAPSULES,ITEMS,EVOLUTIONS,MOVES,DEFAULT_MOVES,
                    new_mon,max_hp,xp_needed,add_xp,encounter,attack,catch_chance,fresh)

st.set_page_config(page_title='LUMION | 루미온',page_icon='🌙',layout='wide')
BASE=Path(__file__).resolve().parent
KST=timezone(timedelta(hours=9))

def img(kind,name,width=None):
    path=BASE/'assets'/kind/(name+'.webp')
    if path.is_file():st.image(str(path),width=width,use_container_width=width is None)
    else:st.info('이미지 준비 중: '+name)

def notice(msg):st.session_state.notice=msg

def get_mon(uid):return next((m for m in p['creatures'] if m['uid']==uid),None)

def pay(amount):
    if p['coins']<amount:return False
    p['coins']-=amount;return True

def render_mon(mon,width=220):
    img('creatures',mon['name'],width)
    st.markdown(f"**{'🌈 오로라 ' if mon['aurora'] else ''}{mon['name']}** · Lv.{mon['level']} · {mon['element']} · {mon['rarity']}")
    st.progress(mon['hp']/max_hp(mon['level'],mon['rarity']),text=f"HP {mon['hp']}/{max_hp(mon['level'],mon['rarity'])}")

def rerun(msg=None):
    if msg:notice(msg)
    st.rerun()

st.markdown('''<style>
.stApp{background:radial-gradient(ellipse at 25% 0%,#28375c 0%,#11172d 48%,#090e1f 100%);color:#f3efff}
.block-container{max-width:1180px;padding-top:1.2rem}
.stButton button{border-radius:13px;min-height:42px}
[data-testid="stMetric"]{background:#1b2543;padding:14px;border:1px solid #465780;border-radius:14px}
[data-testid="stImage"] img{border-radius:18px;filter:drop-shadow(0 0 12px rgba(161,166,255,.22));animation:arrive .8s ease-out both}
@keyframes arrive{from{opacity:.1;transform:translateY(15px) scale(.92)}to{opacity:1;transform:translateY(0) scale(1)}}
.lumion-brand{font-size:40px;letter-spacing:4px;font-weight:850;color:#f1eaff;text-shadow:0 0 26px #8a83ff}
.subtle{color:#b9c6e8}.scene{padding:15px 22px;border-radius:18px;background:#1d2848;border:1px solid #4c5b87}
</style>''',unsafe_allow_html=True)
if 'lumion_save' not in st.session_state:st.session_state.lumion_save=fresh()
p=st.session_state.lumion_save
st.markdown('<div class="lumion-brand">✦ LUMION</div><div class="subtle">빛의 생명체와 함께하는 꿈의 세계</div>',unsafe_allow_html=True)
st.caption('개발용 플레이 버전 · 이미지 20종 및 아이템·지역 이미지 포함')
if 'notice' in st.session_state:st.info(st.session_state.pop('notice'))
cols=st.columns(3)
cols[0].metric('🪙 루미 코인',f"{p['coins']:,}")
cols[1].metric('✨ 보유 루미온',len(p['creatures']))
cols[2].metric('📚 발견한 루미온',f"{len(p['seen'])}/{len(CATALOG)}")
page=st.radio('메뉴',['🏠 홈','🌲 탐험·전투','🛒 상점','🎒 보관함','📚 도감','🌙 수면 연구','⚙️ 저장·설정'],horizontal=True)
st.divider()

if page=='🏠 홈':
    st.subheader('나의 대표 루미온')
    partner=get_mon(p['partner']) or p['creatures'][0]
    a,b=st.columns([1,2],vertical_alignment='center')
    with a:render_mon(partner,280)
    with b:
        st.write('대표 루미온은 탐험에서 야생 루미온과 싸우고 경험치를 얻습니다.')
        st.write(f"경험치: {partner['xp']} / {xp_needed(partner['level']) if partner['level']<100 else 'MAX'}")
        choices={m['uid']:f"{m['name']} · Lv.{m['level']}" for m in p['creatures']}
        chosen=st.selectbox('대표 루미온 선택',list(choices),index=list(choices).index(partner['uid']),format_func=lambda x:choices[x])
        if chosen!=p['partner'] and st.button('대표 변경'):p['partner']=chosen;rerun('대표 루미온을 변경했어요.')
        qty=p['items']['루미 사탕']
        if st.button(f'🍬 루미 사탕 사용 (+25 XP) · 보유 {qty}',disabled=qty<1):
            p['items']['루미 사탕']-=1;levels=add_xp(partner,25);rerun(f'경험치 +25! '+(f'{levels}레벨 상승!' if levels else ''))
        if st.button('🧴 수면 회복제 사용 · HP +40',disabled=p['items']['수면 회복제']<1 or partner['hp']>=max_hp(partner['level'],partner['rarity'])):
            p['items']['수면 회복제']-=1;partner['hp']=min(max_hp(partner['level'],partner['rarity']),partner['hp']+40);rerun('HP를 회복했어요.')
    banner=BASE/'assets'/'scenes'/'타이틀.webp'
    if banner.is_file():st.image(str(banner),use_container_width=True)

elif page=='🌲 탐험·전투':
    st.subheader('루미온 탐험')
    wild=p['active']
    if wild is None:
        area=st.selectbox('탐험 지역',list(AREAS),index=list(AREAS).index(p['area']))
        p['area']=area
        img('scenes',area)
        st.caption('지역마다 주로 등장하는 속성이 달라요. 탐험에는 10코인이 필요합니다.')
        if st.button('🔍 탐험 시작 · 10코인',type='primary',disabled=p['coins']<10):
            if pay(10):
                p['active']=encounter(area);p['battle_log']=['야생 루미온이 등장했어요!'];p['focused']=False
                if p['active']['name'] not in p['seen']:p['seen'].append(p['active']['name'])
                rerun('✨ '+p['active']['name']+' 등장!')
    else:
        partner=get_mon(p['partner']) or p['creatures'][0]
        a,b=st.columns(2)
        with a:
            st.markdown('#### 나의 루미온')
            render_mon(partner,220)
        with b:
            st.markdown('#### 야생 루미온')
            render_mon(wild,220)
        st.caption('전투에서 상대 HP가 낮아질수록 포획 확률이 올라갑니다. 속성 상성도 적용돼요.')
        if wild['hp']>0 and partner['hp']>0:
            move=st.selectbox('기술 선택',partner['moves'])
            if st.button('⚔️ 기술 사용',type='primary'):
                message,_=attack(partner,wild,move);p['battle_log'].append(message)
                if wild['hp']>0:
                    enemy_move=random.choice(wild['moves'])
                    reply,_=attack(wild,partner,enemy_move);p['battle_log'].append(reply)
                else:
                    p['battle_log'].append('승리! 야생 루미온이 지쳐서 포획하기 쉬워졌어요.')
                    add_xp(partner,12)
                if partner['hp']<=0:p['battle_log'].append('대표 루미온이 지쳤어요. 회복 후 다시 도전하세요.')
                st.rerun()
        available=[k for k,v in p['capsules'].items() if v>0]
        if available:
            cap=st.selectbox('캡슐',available,format_func=lambda c:f'{c} ({p["capsules"][c]}개)')
            chance=catch_chance(wild,cap,p['focused'])
            st.progress(chance,text=f'포획 확률 {chance*100:.1f}%')
            if st.button('✨ 캡슐 던지기',disabled=partner['hp']<=0):
                p['capsules'][cap]-=1
                if random.random()<chance:
                    p['creatures'].append(wild);p['active']=None
                    rerun('🎉 포획 성공! '+wild['name']+'이(가) 동료가 되었어요.')
                else:
                    p['battle_log'].append('포획 실패! 야생 루미온이 캡슐에서 빠져나왔어요.')
                    if wild['hp']>0:
                        reply,_=attack(wild,partner,random.choice(wild['moves']));p['battle_log'].append(reply)
                    st.rerun()
        if st.button(f'🧪 집중의 물약 사용 · 보유 {p["items"]["집중의 물약"]}',disabled=p['items']['집중의 물약']<1 or p['focused']):
            p['items']['집중의 물약']-=1;p['focused']=True;rerun('이번 만남의 포획 확률이 상승했어요.')
        if st.button('↩️ 탐험 종료'):p['active']=None;rerun('탐험을 종료했어요.')
        with st.expander('전투 기록',expanded=True):
            for line in p['battle_log'][-12:]:st.write('• '+line)

elif page=='🛒 상점':
    st.subheader('루미온 상점')
    for name,(price,mult) in CAPSULES.items():
        with st.container(border=True):
            a,b,c=st.columns([1,3,1],vertical_alignment='center')
            with a:img('items',name,100)
            b.write(f'**{name}** · {price}코인 · 포획 배율 ×{mult} · 보유 {p["capsules"][name]}개')
            if c.button('구매',key='cap_'+name,disabled=p['coins']<price):
                p['coins']-=price;p['capsules'][name]+=1;rerun(name+' 구매 완료!')
    st.subheader('성장과 전투 아이템')
    for name,(price,desc) in ITEMS.items():
        with st.container(border=True):
            a,b,c=st.columns([1,3,1],vertical_alignment='center')
            with a:img('items',name,100)
            b.write(f'**{name}** · {price}코인 · {desc} · 보유 {p["items"][name]}개')
            if c.button('구매',key='item_'+name,disabled=p['coins']<price):
                p['coins']-=price;p['items'][name]+=1;rerun(name+' 구매 완료!')

elif page=='🎒 보관함':
    st.subheader('내 루미온')
    for i in range(0,len(p['creatures']),3):
        cols=st.columns(3)
        for col,mon in zip(cols,p['creatures'][i:i+3]):
            with col:
                with st.container(border=True):
                    render_mon(mon,170)
                    if st.button('대표로 선택',key='partner_'+mon['uid'],disabled=p['partner']==mon['uid']):
                        p['partner']=mon['uid'];rerun('대표 변경 완료!')
                    if mon['name'] in EVOLUTIONS:
                        target,level=EVOLUTIONS[mon['name']]
                        ready=mon['level']>=level and p['items']['진화석']>0
                        if st.button(f'✨ {target} 진화 · Lv.{level} / 진화석 1개',key='evo_'+mon['uid'],disabled=not ready):
                            p['items']['진화석']-=1;mon['name']=target
                            mon.update({k:CATALOG[target][k] for k in ('element','rarity')})
                            mon['hp']=max_hp(mon['level'],mon['rarity'])
                            if target not in p['seen']:p['seen'].append(target)
                            rerun(target+'(으)로 진화했어요!')
                    with st.expander('기술 배치'):
                        options=DEFAULT_MOVES[mon['element']]
                        selection=st.multiselect('기술 최대 2개',options,default=[m for m in mon['moves'] if m in options],max_selections=2,key='moves_'+mon['uid'])
                        if st.button('기술 저장',key='save_moves_'+mon['uid'],disabled=not selection):
                            mon['moves']=selection;rerun('기술 배치를 저장했어요.')

elif page=='📚 도감':
    st.subheader('루미온 도감 · 20종')
    st.caption('아직 만나지 못한 루미온은 실루엣 대신 물음표로 표시합니다.')
    names=list(CATALOG)
    for i in range(0,len(names),5):
        cols=st.columns(5)
        for col,name in zip(cols,names[i:i+5]):
            with col:
                with st.container(border=True):
                    if name in p['seen']:
                        img('creatures',name)
                        st.write('**'+name+'**')
                        st.caption(CATALOG[name]['element']+' · '+CATALOG[name]['rarity'])
                    else:st.markdown('### ❔');st.caption('미발견')

elif page=='🌙 수면 연구':
    st.subheader('수면 기록과 루미 코인')
    st.caption('자가 보고 기록용입니다. 의료적 진단이나 수면 단계의 정확한 측정을 제공하지 않습니다.')
    with st.form('sleep_form'):
        day=st.date_input('기상한 날짜',datetime.now(KST).date())
        duration=st.number_input('수면 시간(시간)',min_value=0.0,max_value=24.0,value=8.0,step=.25)
        quality=st.slider('수면의 질 점수',0,100,75)
        deep=st.number_input('앱에 표시된 깊은 수면(분, 선택)',min_value=0,max_value=1440,value=0)
        rem=st.number_input('앱에 표시된 REM 수면(분, 선택)',min_value=0,max_value=1440,value=0)
        awake=st.number_input('앱에 표시된 깨어 있음(분, 선택)',min_value=0,max_value=1440,value=0)
        rt=st.number_input('PVT 평균 반응시간(ms, 선택)',min_value=0,max_value=5000,value=0)
        memo=st.text_input('메모(선택)',max_chars=160)
        submitted=st.form_submit_button('기록 저장 및 일일 보상',type='primary')
    if submitted:
        key=day.isoformat()
        if key in p['reward_days']:st.warning('해당 날짜의 보상은 이미 받았어요. 기록은 중복 저장하지 않았습니다.')
        elif day>datetime.now(KST).date():st.warning('미래 날짜는 기록할 수 없어요.')
        else:
            p['sleep_records'].append({'date':key,'duration_hours':duration,'quality':quality,'deep_min':deep,
                                       'rem_min':rem,'awake_min':awake,'pvt_rt_ms':rt,'memo':memo})
            p['reward_days'].append(key)
            # Reward participation and quality, not excessive duration.
            reward=40+round(quality*.6)
            p['coins']+=reward
            add_xp(get_mon(p['partner']) or p['creatures'][0],10+round(quality*.15))
            rerun(f'기록 저장 완료! +{reward}코인, 대표 루미온 경험치 획득!')
    if p['sleep_records']:
        st.subheader('내 기록')
        st.dataframe(list(reversed(p['sleep_records'])),use_container_width=True,hide_index=True)

else:
    st.subheader('저장 및 개발 설정')
    st.warning('현재는 로그인 없는 개발용 버전입니다. Streamlit Cloud에서 새로고침하거나 서버가 재시작되면 진행 기록이 사라질 수 있습니다. JSON 백업을 사용하세요.')
    data=json.dumps(p,ensure_ascii=False,indent=2)
    st.download_button('💾 진행 기록 JSON 다운로드',data,file_name='lumion_save.json',mime='application/json')
    upload=st.file_uploader('이전에 다운로드한 JSON 저장 파일 복원',type=['json'])
    if upload and st.button('저장 파일 불러오기'):
        try:
            restored=json.load(upload)
            assert isinstance(restored,dict) and restored.get('version')==2
            assert isinstance(restored.get('creatures'),list) and restored['creatures']
            assert isinstance(restored.get('coins'),int) and 0<=restored['coins']<=10**9
            assert all(m.get('name') in CATALOG for m in restored['creatures'])
            assert isinstance(restored.get('items'),dict) and isinstance(restored.get('capsules'),dict)
            assert all(isinstance(restored['items'].get(k),int) and 0<=restored['items'][k]<=10**6 for k in ITEMS)
            assert all(isinstance(restored['capsules'].get(k),int) and 0<=restored['capsules'][k]<=10**6 for k in CAPSULES)
            restored['active']=None
            st.session_state.lumion_save=restored;rerun('저장 파일을 불러왔어요!')
        except (ValueError,TypeError,KeyError,AssertionError):st.error('올바른 루미온 v2 저장 파일이 아닙니다.')
    st.divider()
    st.write('**테스트 모드**: 코인이 부족해서 기능을 시험할 수 없을 때 한 번만 지급합니다.')
    if st.button('🧪 개발용 코인 10,000개 지급 (1회)',disabled=p['test_claimed']):
        p['coins']+=10000;p['test_claimed']=True;rerun('테스트 코인 10,000개를 받았어요.')
    st.caption('실제 공개용 서비스로 전환하려면 Supabase 로그인·RLS 기반 영구 저장과 서버 측 게임 규칙 검증이 필요합니다.')

st.divider()
st.caption('LUMION v1 · 자체 캐릭터 20종 · 기존 포켓몬 파일과 분리된 독립 게임')
