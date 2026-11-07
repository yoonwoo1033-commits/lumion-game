import sqlite3,json,datetime,uuid
from pathlib import Path
DB=Path(__file__).with_name('lumion.db')
def connect():
    db=sqlite3.connect(DB,timeout=30,isolation_level=None)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA busy_timeout=30000')
    db.execute('PRAGMA journal_mode=WAL')
    db.executescript('''CREATE TABLE IF NOT EXISTS players(id TEXT PRIMARY KEY, coins INTEGER NOT NULL DEFAULT 100, active TEXT, state TEXT NOT NULL DEFAULT 'idle', last_reward TEXT);
    CREATE TABLE IF NOT EXISTS capsules(player TEXT NOT NULL,name TEXT NOT NULL,qty INTEGER NOT NULL,PRIMARY KEY(player,name));
    CREATE TABLE IF NOT EXISTS creatures(id TEXT PRIMARY KEY,player TEXT NOT NULL,name TEXT NOT NULL,rarity TEXT NOT NULL,element TEXT NOT NULL,level INTEGER NOT NULL,aurora INTEGER NOT NULL,icon TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS discoveries(player TEXT NOT NULL,name TEXT NOT NULL,PRIMARY KEY(player,name));
    CREATE TABLE IF NOT EXISTS ledger(id TEXT PRIMARY KEY,player TEXT NOT NULL,delta INTEGER NOT NULL,reason TEXT NOT NULL,created TEXT NOT NULL);''')
    return db
def init(player):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if not db.execute('SELECT 1 FROM players WHERE id=?',(player,)).fetchone():
            db.execute('INSERT INTO players(id) VALUES(?)',(player,))
            for name,qty in [('기본 캡슐',5),('슈퍼 캡슐',0),('하이퍼 캡슐',0),('스타 캡슐',0)]:db.execute('INSERT INTO capsules VALUES(?,?,?)',(player,name,qty))
        db.commit()
def snapshot(player):
    with connect() as db:
        p=dict(db.execute('SELECT * FROM players WHERE id=?',(player,)).fetchone())
        p['active']=json.loads(p['active']) if p['active'] else None
        p['capsules']={r['name']:r['qty'] for r in db.execute('SELECT * FROM capsules WHERE player=?',(player,))}
        p['creatures']=[dict(r) for r in db.execute('SELECT * FROM creatures WHERE player=? ORDER BY rowid DESC',(player,))]
        p['discovered']={r['name'] for r in db.execute('SELECT name FROM discoveries WHERE player=?',(player,))}
        return p
def ledger(db,player,delta,reason):
    db.execute('INSERT INTO ledger VALUES(?,?,?,?,?)',(str(uuid.uuid4()),player,delta,reason,datetime.datetime.now().isoformat()))
def start(player,make_encounter):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        p=db.execute('SELECT coins,state FROM players WHERE id=?',(player,)).fetchone()
        if p['state']!='idle':db.rollback();return '진행 중인 탐험이 있어요.'
        if p['coins']<10:db.rollback();return '코인이 부족해요.'
        e=make_encounter()
        db.execute('UPDATE players SET coins=coins-10,active=?,state=? WHERE id=?',(json.dumps(e,ensure_ascii=False),'encounter',player))
        db.execute('INSERT OR IGNORE INTO discoveries VALUES(?,?)',(player,e['name']))
        ledger(db,player,-10,'탐험')
        db.commit();return '새로운 루미온을 발견했어요!'
def buy(player,name,price):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        p=db.execute('SELECT coins FROM players WHERE id=?',(player,)).fetchone()
        if p['coins']<price:db.rollback();return '코인이 부족해요.'
        db.execute('UPDATE players SET coins=coins-? WHERE id=?',(price,player))
        db.execute('UPDATE capsules SET qty=qty+1 WHERE player=? AND name=?',(player,name))
        ledger(db,player,-price,name+' 구매');db.commit();return name+' 구매 완료!'
def capture(player,capsule,rate_fn):
    import random
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        p=db.execute('SELECT active,state FROM players WHERE id=?',(player,)).fetchone()
        if p['state']!='encounter' or not p['active']:db.rollback();return '포획할 루미온이 없어요.'
        q=db.execute('SELECT qty FROM capsules WHERE player=? AND name=?',(player,capsule)).fetchone()
        if not q or q['qty']<1:db.rollback();return '캡슐이 부족해요.'
        e=json.loads(p['active']);success=random.random()<rate_fn(e['rarity'],e['level'],capsule)
        db.execute('UPDATE capsules SET qty=qty-1 WHERE player=? AND name=?',(player,capsule))
        if success:
            db.execute('INSERT INTO creatures VALUES(?,?,?,?,?,?,?,?)',(str(uuid.uuid4()),player,e['name'],e['rarity'],e['element'],e['level'],int(e['aurora']),e['icon']))
            db.execute("UPDATE players SET active=NULL,state='idle' WHERE id=?",(player,))
            message='🎉 포획 성공! '+e['name']+'이(가) 보관함에 등록되었어요.'
        else:
            e['attempts']+=1
            if e['attempts']>=2:
                db.execute("UPDATE players SET active=NULL,state='idle' WHERE id=?",(player,))
                message='💨 캡슐에서 빠져나온 루미온이 숲으로 도망갔어요.'
            else:
                db.execute('UPDATE players SET active=? WHERE id=?',(json.dumps(e,ensure_ascii=False),player))
                message='💫 캡슐에서 빠져나왔어요! 한 번 더 시도할 수 있어요.'
        db.commit();return message
def flee(player):
    with connect() as db:
        db.execute("UPDATE players SET active=NULL,state='idle' WHERE id=?",(player,))
def reward(player):
    today=datetime.date.today().isoformat()
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        p=db.execute('SELECT last_reward FROM players WHERE id=?',(player,)).fetchone()
        if p['last_reward']==today:db.rollback();return '오늘의 기록 보상은 이미 받았어요.'
        db.execute('UPDATE players SET coins=coins+20,last_reward=? WHERE id=?',(today,player))
        ledger(db,player,20,'일일 기록 보상');db.commit();return '기록 보상 20코인을 받았어요!'
def evolve(player,creature_id,evolutions):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        c=db.execute('SELECT name,level FROM creatures WHERE id=? AND player=?',(creature_id,player)).fetchone()
        if not c or c['name'] not in evolutions:db.rollback();return '진화할 수 없어요.'
        target,minimum=evolutions[c['name']]
        if c['level']<minimum:db.rollback();return f'레벨 {minimum}부터 진화할 수 있어요.'
        db.execute('UPDATE creatures SET name=? WHERE id=? AND player=?',(target,creature_id,player))
        db.execute('INSERT OR IGNORE INTO discoveries VALUES(?,?)',(player,target))
        db.commit();return f'{target}(으)로 진화했어요!'
