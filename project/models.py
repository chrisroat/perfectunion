"""Database models for the Net Neutrality Comments."""

from project import db


class Comments(db.Model):
  id = db.Column(db.Integer, primary_key=True, autoincrement=True)
  state_fips = db.Column(db.Integer)
  district_fips = db.Column(db.Integer)
  name = db.Column(db.String)
  city = db.Column(db.String)
  comment = db.Column(db.String)
