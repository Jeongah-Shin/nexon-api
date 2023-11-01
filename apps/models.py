"""
models.py

"""
from apps import db

class Stranger(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    phone = db.Column(db.String(255))
    position = db.Column(db.String(255))
    privacy_agree = db.Column(db.DateTime())
    email = db.Column(db.String(255))
    attendance = db.Column(db.String(255))
    color = db.Column(db.String(255))
    notion_url = db.Column(db.Text())
    date_edited = db.Column(db.DateTime())
    password = db.Column(db.String(255))


class Ca(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    date = db.Column(db.DateTime())
    people = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text())
    stranger_id = db.Column(db.Integer, db.ForeignKey('stranger.id',ondelete='cascade'))
    stranger = db.relationship('Stranger', backref=db.backref('Ca', cascade='all, delete'))
    date_created = db.Column(db.DateTime())
    date_edited = db.Column(db.DateTime())


class Rel_participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stranger_id = db.Column(db.Integer, db.ForeignKey('stranger.id',ondelete='cascade'))
    stranger = db.relationship('Stranger', backref=db.backref('Rel_participant', cascade='all, delete'))
    ca_id = db.Column(db.Integer, db.ForeignKey('ca.id',ondelete='cascade'))
    ca = db.relationship('Ca', backref=db.backref('Rel_participant', cascade='all, delete'))
    date_created = db.Column(db.DateTime())
