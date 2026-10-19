import sqlite3
from datetime import date,timedelta
from pathlib import Path

STATUSES=('Lead','Quote','Order','Production','Delivered','Paid')
STATUS_LABELS={'Lead':'Contacto inicial','Quote':'Cotización','Order':'Pedido confirmado','Production':'En producción','Delivered':'Entregado, por cobrar','Paid':'Marcado como pagado'}
NEXT_ACTIONS={'Lead':'Preparar cotización','Quote':'Confirmar pedido','Order':'Iniciar producción','Production':'Registrar entrega','Delivered':'Registrar pago','Paid':'Flujo completado'}
TASK_STATUSES=('Pending','In Progress','Done')
TASK_LABELS={'Pending':'Pendiente','In Progress':'En curso','Done':'Hecha'}
OWNERS=('Equipo demo A','Equipo demo B','Sin asignar')
SCHEMA='''
CREATE TABLE clients(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL COLLATE NOCASE UNIQUE CHECK(length(name) BETWEEN 1 AND 60),
 email TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_DATE
);
CREATE TABLE orders(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 client_id INTEGER NOT NULL REFERENCES clients(id),
 description TEXT NOT NULL CHECK(length(description) BETWEEN 1 AND 100),
 amount_cents INTEGER NOT NULL CHECK(typeof(amount_cents)='integer' AND amount_cents BETWEEN 0 AND 100000000),
 status TEXT NOT NULL DEFAULT 'Lead' CHECK(status IN ('Lead','Quote','Order','Production','Delivered','Paid')),
 created_at TEXT NOT NULL DEFAULT CURRENT_DATE
);
CREATE TABLE inventory(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 sku TEXT NOT NULL COLLATE NOCASE UNIQUE,
 name TEXT NOT NULL CHECK(length(name) BETWEEN 1 AND 80),
 stock INTEGER NOT NULL CHECK(typeof(stock)='integer' AND stock BETWEEN 0 AND 100000),
 min_stock INTEGER NOT NULL CHECK(typeof(min_stock)='integer' AND min_stock BETWEEN 0 AND 100000)
);
CREATE TABLE tasks(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 title TEXT NOT NULL CHECK(length(title) BETWEEN 1 AND 100),
 owner TEXT NOT NULL CHECK(owner IN ('Equipo demo A','Equipo demo B','Sin asignar')),
 due_date TEXT,
 status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending','In Progress','Done')),
 order_id INTEGER REFERENCES orders(id)
);
CREATE INDEX orders_status_idx ON orders(status);
CREATE INDEX tasks_due_idx ON tasks(status,due_date);
'''

def connect(path):
    con=sqlite3.connect(path,timeout=5)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    con.execute('PRAGMA busy_timeout=5000')
    return con

def seed(con):
    con.executescript(SCHEMA)
    today=date.today()
    with con:
        con.executemany('INSERT INTO clients(name,email) VALUES(?,?)', [('Demo Alfa','alfa@example.test'),('Demo Beta','beta@example.test'),('Demo Gamma','')])
        con.executemany('INSERT INTO inventory(sku,name,stock,min_stock) VALUES(?,?,?,?)', [('DEMO-MAT-A','Material ficticio A',24,10),('DEMO-MAT-B','Material ficticio B',7,8),('DEMO-PKG','Empaque ficticio',20,20)])
        con.executemany('INSERT INTO orders(client_id,description,amount_cents,status) VALUES(?,?,?,?)',[(i%3+1,'Ejemplo '+str(i+1)+' · '+status,amount,status) for i,(status,amount) in enumerate(zip(STATUSES,[80000,120000,95000,180000,65000,110000]))])
        con.executemany('INSERT INTO tasks(title,owner,due_date,status,order_id) VALUES(?,?,?,?,?)', [
            ('Confirmar cotización demo','Equipo demo A',(today-timedelta(days=1)).isoformat(),'Pending',2),
            ('Reponer material demo B','Equipo demo B',today.isoformat(),'Pending',None),
            ('Revisar avance de producción','Equipo demo A',(today+timedelta(days=1)).isoformat(),'In Progress',4)])
