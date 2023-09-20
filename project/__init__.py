import os

import flask
import flask_limiter
import num2words
import pandas as pd
from flask_limiter import util

os.environ["DC_STATEHOOD"] = "1"  # Allow DC to have comments
from us import states

dir_path = os.path.dirname(os.path.realpath(__file__))
data_path = os.path.join(dir_path, "comment_data.pq")
df = pd.read_parquet(data_path)

app = flask.Flask(__name__)

limiter = flask_limiter.Limiter(
    util.get_remote_address,
    app=app,
    default_limits=["200 per day", "60 per hour", "10 per minute", "2 per second"],
    storage_uri="memory://",
)


@app.route("/")
def index():
    return flask.render_template("index.html")


@app.route("/about")
def about():
    return flask.render_template("about.html")


@app.route("/counts")
def counts():
    def fips_key(idx):
        return "%d%s" % (int(idx[0]), idx[1])

    def text(idx, size):
        state = states.lookup(idx[0]).name
        district = district_name(idx[1])
        return "%s's %s District\n%d comments" % (state, district, size)

    df_size = df.groupby(["state_fips", "district_fips"]).size()
    result = {fips_key(idx): text(idx, row) for (idx, row) in df_size.items()}
    return flask.jsonify({"title": result})


@app.route("/data")
@limiter.limit("2000/day;200/hour;20/minute;2/second")
def data():
    fips = flask.request.args.get("fips")
    if not fips:
        flask.abort(400)

    fips = fips.zfill(4)

    state_fips = fips[:2]
    state = states.lookup(state_fips)
    state_name = state.name
    state_abbr = state.abbr

    district_fips = fips[2:]
    result = {
        "state_name": state_name,
        "state_abbr": state_abbr,
        "district": district_name(district_fips),
    }

    df_fips = df[
        (df["state_fips"] == state_fips) & (df["district_fips"] == district_fips)
    ]

    if df_fips.shape[0] > 0:
        comment_data = df_fips.sample(1).iloc[0]
        result.update(
            {
                "fcc_link": "https://www.fcc.gov/ecfs/filing/{}".format(
                    comment_data["id"]
                ),
                "name": comment_data["name"].title(),
                "city": comment_data["city"].title(),
                "comment": comment_data["comment"].replace("\n", "<br>"),
            }
        )

    return flask.jsonify(result)


def district_name(district_fips):
    district_num = int(district_fips)
    if district_num:
        return num2words.num2words(district_num, to="ordinal_num")
    return "At-Large"


@app.errorhandler(429)
def ratelimit_handler(e):
    return "Take it easy!  You exceeded the rate limit: %s" % e.description
