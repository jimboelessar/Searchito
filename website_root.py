# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from searcheengine import SearchEngine
from werkzeug.utils import secure_filename
import os
import aidkit as kit

engine = SearchEngine()
app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/query')
def results():
    global engine
    query = request.args.get('search')
    top = request.args.get('top')
    if request.args.get('mode'): boolean = False
    else: boolean = True
    results = engine.execute_query(query, boolean, int(top))

    return render_template("results.html", query=query, results=results, boolean=boolean, top=top)

@app.route('/crawl', methods=['POST'])
def crawl():
    url = request.form['crawl-link']
    no_sites = request.form['crawl-number']
    engine.crawl(url, int(no_sites))
    return render_template("index.html", message="Crawling completed.")

@app.route('/uploader', methods = ['POST'])
def upload_files():
   if request.method == 'POST':
      kit.create_dicrectory(engine.uploads_folder)
      for f in request.files.getlist('files'):
        filename = kit.resolve_conflict(engine.uploads_folder, secure_filename(f.filename))
        f.save(engine.uploads_folder + filename)
      engine.update_from_uploaded()
      return render_template("index.html", message="All files were uploaded succesfully!")

@app.route('/save')
def save():
    global engine
    engine.restart()
    return render_template("index.html", message="Server state is saved.")

if __name__ == "__main__":
    app.run(debug=True,threaded=True)
