"""Local governance demonstrator. Actor strings are attributed, not authenticated."""
import json
import sqlite3
from dataclasses import asdict
from pathlib import Path

from .common import now
from .rules import Engine, Rule, qualify

TRANSITIONS = {
    'PROPOSED': {'REJECTED', 'NEEDS_REVIEW'},
    'NEEDS_REVIEW': {'REJECTED', 'DISABLED'},
    'VALIDATED': {'APPROVED', 'REJECTED', 'DISABLED'},
    'APPROVED': {'ACTIVE', 'DISABLED'},
    'ACTIVE': {'DISABLED'},
    'DISABLED': {'APPROVED'},
    'REJECTED': set(),
}


class Service:
    def __init__(self, database):
        Path(database).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(database)
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS rules(id TEXT PRIMARY KEY, specification TEXT, state TEXT, source TEXT);
        CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, timestamp TEXT, actor TEXT, action TEXT,
                                         subject TEXT, detail TEXT);
        CREATE TABLE IF NOT EXISTS batches(id INTEGER PRIMARY KEY, source TEXT, timestamp TEXT, rows INT);
        CREATE TABLE IF NOT EXISTS findings(id INTEGER PRIMARY KEY, batch INT, rule_id TEXT, row_idx INT,
                          column_name TEXT, context TEXT, decision TEXT DEFAULT 'OPEN');
        CREATE TABLE IF NOT EXISTS profiles(batch INT, column_name TEXT, missing INT, distinct_count INT,
                                           numeric_mean REAL);
        ''')

    def event(self, actor, action, subject, detail):
        if not actor or not actor.strip():
            raise ValueError('Actor attribution required')
        self.db.execute('INSERT INTO events(timestamp,actor,action,subject,detail) VALUES(?,?,?,?,?)',
                        (now(), actor, action, str(subject), json.dumps(detail)))

    def propose(self, rule, source, actor):
        Rule.parse(asdict(rule))
        with self.db:
            self.event(actor, 'PROPOSE', rule.id, {'source': source})
            self.db.execute('INSERT INTO rules VALUES(?,?,?,?)',
                            (rule.id, json.dumps(asdict(rule)), 'PROPOSED', source))

    def validate(self, rule_id, development, actor):
        row = self.db.execute('SELECT specification,state,source FROM rules WHERE id=?', (rule_id,)).fetchone()
        if row is None or row[1] != 'PROPOSED':
            raise ValueError('Only proposed rules can be qualified')
        existing = self.db.execute("SELECT specification FROM rules WHERE source=? AND id!=? AND state IN ('VALIDATED','APPROVED','ACTIVE')",
                                   (row[2], rule_id)).fetchall()
        decision = qualify([json.loads(r[0]) for r in existing] + [json.loads(row[0])], development)[-1]
        with self.db:
            self.event(actor, 'QUALIFY', rule_id, decision)
            self.db.execute('UPDATE rules SET state=? WHERE id=?', (decision['state'], rule_id))
        return decision

    def transition(self, rule_id, state, actor, reason):
        row = self.db.execute('SELECT state FROM rules WHERE id=?', (rule_id,)).fetchone()
        if row is None or state not in TRANSITIONS[row[0]] or not reason.strip():
            raise ValueError('Invalid lifecycle transition or absent reason')
        with self.db:
            self.event(actor, 'TRANSITION', rule_id, {'from': row[0], 'to': state, 'reason': reason})
            self.db.execute('UPDATE rules SET state=? WHERE id=?', (state, rule_id))

    def scan(self, source, frame):
        from .rules import missing, number
        with self.db:
            batch = self.db.execute('INSERT INTO batches(source,timestamp,rows) VALUES(?,?,?)',
                                    (source, now(), len(frame))).lastrowid
            with Engine(frame) as engine:
                rows = self.db.execute("SELECT specification FROM rules WHERE source=? AND state='ACTIVE'",
                                       (source,)).fetchall()
                count = 0
                for row in rows:
                    rule = Rule.parse(json.loads(row[0]))
                    for i, column in sorted(engine.execute(rule)):
                        context = {'value': str(frame.iloc[i][column]), 'evidence': rule.evidence,
                                   'rule': asdict(rule), 'interpretation': 'review finding, not verified error'}
                        self.db.execute('INSERT INTO findings(batch,rule_id,row_idx,column_name,context) VALUES(?,?,?,?,?)',
                                        (batch, rule.id, i, column, json.dumps(context)))
                        count += 1
            for column in frame:
                vals = frame[column].tolist()
                nums = [v for x in vals if (v := number(x)) is not None]
                self.db.execute('INSERT INTO profiles VALUES(?,?,?,?,?)',
                                (batch, column, sum(missing(v) for v in vals), frame[column].nunique(),
                                 sum(nums) / len(nums) if nums else None))
            self.event('service', 'SCAN', batch, {'source': source, 'findings': count})
        return {'batch': batch, 'source': source, 'rows': len(frame), 'findings': count}

    def review(self, finding, decision, actor, reason):
        if decision not in {'ACCEPTED', 'INVESTIGATING', 'DISMISSED'} or not reason.strip():
            raise ValueError('Invalid finding decision')
        with self.db:
            if not self.db.execute('SELECT id FROM findings WHERE id=?', (finding,)).fetchone():
                raise ValueError('Unknown finding')
            self.event(actor, 'REVIEW', finding, {'decision': decision, 'reason': reason})
            self.db.execute('UPDATE findings SET decision=? WHERE id=?', (decision, finding))

    def monitoring(self, source):
        rows = self.db.execute('''SELECT b.id,b.rows,p.column_name,p.missing,p.distinct_count,p.numeric_mean
            FROM batches b JOIN profiles p ON b.id=p.batch WHERE b.source=? ORDER BY b.id,p.column_name''',
                               (source,)).fetchall()
        return [dict(zip(['batch', 'rows', 'column', 'missing', 'distinct', 'numeric_mean'], r)) for r in rows]

    def close(self):
        self.db.close()
