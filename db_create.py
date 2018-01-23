import sqlalchemy
from project import db

# Drop and recreate tables. Need to drop tables in order by foreign
# key constraints.
for t in reversed(db.metadata.sorted_tables):
  t.drop(db.engine, checkfirst=True)
db.create_all()
