# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, flash, redirect, url_for
from searcheengine import SearchEngine
from werkzeug.utils import secure_filename
import os
import aidkit as kit

engine = SearchEngine()
app = Flask(__name__)

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/query')
def results():
    global engine
    query = request.args.get('search')
    if request.args.get('boolean-model'): boolean = True
    else: boolean = False
    print("Boolean: ", boolean)
    results = engine.execute_query(query, boolean)

    return render_template("index.html", query=query, results=results, boolean=boolean)

@app.route('/crawl', methods=['POST'])
def crawl():
    url = request.form['crawl-link']
    no_sites = request.form['crawl-number']
    engine.crawl(url, int(no_sites))
    return redirect(url_for('index'))

@app.route('/uploader', methods = ['POST'])
def upload_files():
   if request.method == 'POST':
      for f in request.files.getlist('files'):
        filename = kit.resolve_conflict(engine.uploads_folder, secure_filename(f.filename))
        f.save(engine.uploads_folder + filename)
      engine.update_from_uploaded()
      return redirect(url_for('index'))

@app.route('/admin/shutdown')
def shutdown():
    global engine
    engine.stop()
    shutdown_server()
    os._exit(0)

if __name__ == "__main__":
    app.run(debug=True,threaded=True)
