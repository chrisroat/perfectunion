import flask
import flask_limiter
import flask_sqlalchemy
import num2words

from flask_limiter import util
from sqlalchemy.sql import func
from us import states


app = flask.Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "bigquery://perfectunion/perfectunion"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = flask_sqlalchemy.SQLAlchemy(app)

limiter = flask_limiter.Limiter(
  app,
  key_func=util.get_remote_address,
  default_limits=["200 per day", "60 per hour", "10 per minute", "2 per second"],
  storage_uri="memory://",
)

class CommentData(db.Model):
  id = db.Column(db.BigInteger, primary_key=True)
  state_fips = db.Column(db.String(2), index=True)
  district_fips = db.Column(db.String(2), index=True)
  name = db.Column(db.String)
  city = db.Column(db.String)
  comment = db.Column(db.String)


@app.route('/')
def index():
  return flask.render_template('index.html')


@app.route('/about')
def about():
  return flask.render_template('about.html')


@app.route('/counts')
def counts():
  query = CommentData.query.with_entities(CommentData.state_fips, CommentData.district_fips, func.count(1))
  query = query.group_by(CommentData.state_fips, CommentData.district_fips)

  def key(state_fips, district_fips):
    return '%d%s' % (int(state_fips), district_fips)

  def title(state_fips, district_fips, count):
    state_name = states.lookup(state_fips).name
    return '%s\'s %s District\n%d comments' % (state_name, district_name(district_fips), count)
  
  result = {key(s, d): title(s, d, c) for s, d, c in query}
  return flask.jsonify({'title': result})


@app.route('/data')
@limiter.limit("2000/day;200/hour;20/minute;2/second")
def data():
  fips = flask.request.args.get('fips')
  if not fips:
    flask.abort(400)

  fips = fips.zfill(4)

  state_fips = fips[:2]
  state = states.lookup(state_fips)
  state_name = state.name
  state_abbr = state.abbr

  district_fips = fips[2:]
  result = {'state_name': state_name, 'state_abbr': state_abbr, 'district': district_name(district_fips)}

  query = CommentData.query
  query = query.filter(CommentData.state_fips == state_fips)
  query = query.filter(CommentData.district_fips == district_fips)

  query = query.order_by(func.rand())
  comment_data = query.first()

  if comment_data:
    result.update({
      'fcc_link': 'https://www.fcc.gov/ecfs/filing/{}'.format(comment_data.id),
      'name': comment_data.name.title(),
      'city': comment_data.city.title(),
      'comment': comment_data.comment.replace('\n', '<br>'),
    })

  return flask.jsonify(result)


def district_name(district_fips):
  district_num = int(district_fips)
  if district_num:
    return num2words.num2words(district_num, to='ordinal_num')
  return 'At-Large'


@app.errorhandler(429)
def ratelimit_handler(e):
  return "Take it easy!  You exceeded the rate limit: %s" % e.description

if __name__ == "__main__":
  app.run(debug=True)