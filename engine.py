"""Original LUMION game rules. No Pokémon APIs or artwork."""
import random, math, uuid

SPECIES = [
('루루','달빛','일반',22),('모리','자연','일반',22),('몽글','꿈','일반',20),('아쿠리','물결','일반',20),
('반짝이','별','일반',17),('도토리','자연','일반',17),('파르','전기','일반',17),('설몽','서리','일반',15),
('해리','태양','일반',15),('이슬비','물결','일반',15),('실피','달빛','희귀',9),('루나엘','달빛','희귀',8),
('별콩','별','희귀',9),('포레온','자연','희귀',8),('꿈나비','꿈','희귀',8),('프리즈','서리','희귀',7),
('스파키','전기','희귀',7),('솔라핀','태양','영웅',3),('루나리스','달빛','영웅',2),('셀레노스','별','전설',0.5)]
CATALOG={name:{'name':name,'element':element,'rarity':rarity,'weight':weight} for name,element,rarity,weight in SPECIES}
AREAS={'달빛 숲':['달빛','자연','꿈'],'꿈구름 계곡':['꿈','물결','전기'],'서리 동굴':['서리','별','물결'],'별빛 성역':['별','태양','달빛']}
CAPSULES={'기본 캡슐':(20,1.0),'슈퍼 캡슐':(50,1.5),'하이퍼 캡슐':(100,2.0),'스타 캡슐':(250,3.0)}
ITEMS={'루미 사탕':(35,'대상에게 경험치 25 획득'),'진화석':(120,'진화 시 소모'),'수면 회복제':(45,'전투 후 HP 40 회복'),'집중의 물약':(60,'전투 중 포획 보정')}
EVOLUTIONS={'루루':('루나엘',12),'루나엘':('루나리스',28),'모리':('포레온',15),'설몽':('프리즈',18),'파르':('스파키',18),'몽글':('꿈나비',18),'해리':('솔라핀',24)}
STRONG={'달빛':'꿈','꿈':'별','별':'태양','태양':'서리','서리':'자연','자연':'물결','물결':'전기','전기':'달빛'}
RARITY_RATE={'일반':.65,'희귀':.42,'영웅':.22,'전설':.09,'신화':.035}
RARITY_BONUS={'일반':0,'희귀':5,'영웅':12,'전설':25,'신화':35}
MOVES={'빛의 파동':('달빛',45,100),'꿈의 속삭임':('꿈',40,100),'새싹 타격':('자연',45,100),
'물결 일격':('물결',45,100),'태양 섬광':('태양',50,95),'전광석':('전기',50,95),
'서리 바람':('서리',45,100),'별빛 폭발':('별',55,90),'기본 공격':('무속성',35,100),
'수면의 안개':('꿈',22,95),'치유의 빛':('달빛',0,100)}
DEFAULT_MOVES={'달빛':['빛의 파동','기본 공격','치유의 빛'],'꿈':['꿈의 속삭임','기본 공격','수면의 안개'],
'자연':['새싹 타격','기본 공격'],'물결':['물결 일격','기본 공격'],
'태양':['태양 섬광','기본 공격'],'전기':['전광석','기본 공격'],
'서리':['서리 바람','기본 공격'],'별':['별빛 폭발','기본 공격']}

def new_mon(name,level=1,aurora=False):
    info=CATALOG[name]; hp=max_hp(level,info['rarity'])
    return {**{k:info[k] for k in ('name','element','rarity')},'uid':str(uuid.uuid4()),'level':level,
            'xp':0,'aurora':aurora,'hp':hp,'moves':DEFAULT_MOVES[info['element']][:2]}

def max_hp(level,rarity):return 48+level*4+RARITY_BONUS[rarity]
def xp_needed(level):return 18+level*7

def add_xp(mon,amount):
    mon['xp']+=max(0,int(amount)); gained=0
    while mon['level']<100 and mon['xp']>=xp_needed(mon['level']):
        mon['xp']-=xp_needed(mon['level']);mon['level']+=1;gained+=1
    if mon['level']==100:mon['xp']=0
    mon['hp']=min(max_hp(mon['level'],mon['rarity']),mon['hp']+gained*4)
    return gained

def encounter(area):
    allowed=AREAS[area]
    pool=[CATALOG[name] for name in CATALOG if CATALOG[name]['element'] in allowed]
    chosen=random.choices(pool,weights=[s['weight'] for s in pool],k=1)[0]
    low,high=(18,35) if chosen['rarity']=='전설' else (6,22) if chosen['rarity']=='영웅' else (2,16)
    return new_mon(chosen['name'],random.randint(low,high),random.randrange(500)==0)

def effectiveness(move_type,target_type):
    if move_type=='무속성':return 1.0
    if STRONG.get(move_type)==target_type:return 1.5
    if STRONG.get(target_type)==move_type:return .75
    return 1.0

def attack(attacker,defender,move):
    if move not in MOVES or move not in attacker['moves']:return '사용할 수 없는 기술입니다.',0
    typ,power,accuracy=MOVES[move]
    if random.randrange(100)>=accuracy:return f'{move}이(가) 빗나갔어요.',0
    if move=='치유의 빛':
        heal=min(max_hp(attacker['level'],attacker['rarity'])-attacker['hp'],18+attacker['level'])
        attacker['hp']+=heal;return f'{attacker["name"]}의 HP가 {heal} 회복됐어요.',0
    mult=effectiveness(typ,defender['element'])
    damage=max(1,round((power/10+attacker['level']*.72)*mult*random.uniform(.85,1.15)))
    defender['hp']=max(0,defender['hp']-damage)
    message=f'{attacker["name"]}의 {move}! {damage} 피해.'
    if mult>1:message+=' 효과가 뛰어나요!'
    if mult<1:message+=' 효과가 약해요.'
    return message,damage

def catch_chance(wild,capsule,focused=False):
    base=RARITY_RATE[wild['rarity']]*CAPSULES[capsule][1]
    hp_fraction=wild['hp']/max_hp(wild['level'],wild['rarity'])
    bonus=1+.9*(1-hp_fraction)+(0.35 if focused else 0)
    level_penalty=max(.5,1-.011*(wild['level']-1))
    return min(.96,max(.01,base*bonus*level_penalty))

def fresh():
    starter=new_mon('루루',5)
    return {'version':2,'coins':250,'capsules':{'기본 캡슐':8,'슈퍼 캡슐':2,'하이퍼 캡슐':0,'스타 캡슐':0},
            'items':{k:0 for k in ITEMS},'creatures':[starter],'partner':starter['uid'],
            'seen':['루루'],'active':None,'area':'달빛 숲','battle_log':[],'focused':False,
            'sleep_records':[],'reward_days':[],'test_claimed':False}
