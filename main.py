import requests
from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from sqlalchemy import desc
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

API_KEY = "76157a4c1da64272bbc9f7690cd2520c"
MOVIE_DB_ENDPOINT = "https://api.themoviedb.org/3/search/movie"
MOVIE_ID_ENDPOINT = "https://api.themoviedb.org/3/movie/"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

db = SQLAlchemy()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///top-movies.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), unique=True, nullable=False)
    rating = db.Column(db.Float, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), unique=True, nullable=False)


with app.app_context():
    db.create_all()


class RateMovieForm(FlaskForm):
    rating = StringField("Your New Rating Out of 10 e.g. '5.4'", validators=[DataRequired()])
    review = StringField('Your New Review', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddMovieForm(FlaskForm):
    movie = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    rank_counter = 0
    films = db.session.execute(db.select(Movies).order_by(desc(Movies.rating))).all()
    for film in films:
        rank_counter += 1
        film[0].ranking = rank_counter
    db.session.commit()
    return render_template(
        "index.html",
        films=db.session.execute(db.select(Movies).order_by(Movies.ranking)).all()
    )


@app.route("/edit/<movie_id>", methods=('GET', 'POST'))
def edit(movie_id):
    form = RateMovieForm()
    if form.validate_on_submit():
        movie_to_update = Movies.query.get(movie_id)
        movie_to_update.rating = form.rating.data
        movie_to_update.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", film=Movies.query.get(movie_id), form=form)


@app.route("/<movie_id>")
def delete(movie_id):
    db.session.delete(Movies.query.get(movie_id))
    db.session.commit()
    return redirect(url_for('home'))


@app.route("/add_movie", methods=('GET', 'POST'))
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        parameters = {
            "api_key": API_KEY,
            "language": "en-US",
            "query": form.movie.data,
            "page": "1",
            "include_adult": "false",
        }
        films = requests.get(url=MOVIE_DB_ENDPOINT, params=parameters).json()['results']
        return render_template("select.html", films=films)
    return render_template("add.html", form=form)


@app.route('/movie_id/<film_id>')
def adding(film_id):
    parameters = {
        "api_key": API_KEY,
        "language": "en-US",
    }
    film = requests.get(url=f"{MOVIE_ID_ENDPOINT}{film_id}", params=parameters).json()
    new_film = Movies(
        title=film['original_title'],
        year=film['release_date'].split('-')[0],
        description=film['overview'],
        img_url=f"https://image.tmdb.org/t/p/w500{film['poster_path']}",
        rating=0,
        ranking=0,
        review=""
    )
    db.session.add(new_film)
    db.session.commit()
    new_film_id = Movies.query.filter_by(title=film['original_title']).first().id
    return redirect(url_for('edit', movie_id=new_film_id))


if __name__ == '__main__':
    app.run(debug=True)
