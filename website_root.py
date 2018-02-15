# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from searcheengine import SearchEngine
from werkzeug.utils import secure_filename
import os
import aidkit as kit
import threading

engine = SearchEngine()
app = Flask(__name__)

def get_status():
    global engine
    return "Ready" if not engine.is_maintaining else "Updating"

@app.route('/')
def index():
    return render_template("index.html", status=get_status())

@app.route('/query')
def results():
    global engine
    query = request.args.get('search')
    top = request.args.get('top')
    if request.args.get('mode'): boolean = False
    else: boolean = True
    if not engine.is_maintaining:
        results = engine.execute_query(query, boolean, int(top))
        return render_template("results.html", query=query, results=results, boolean=boolean, top=top, updating=False)
    else:
        return render_template("results.html", query=query, boolean=boolean, top=top, updating=True)

@app.route('/crawl', methods=['POST'])
def crawl():
    if engine.is_maintaining:
        message = "Searchito is being updated. Try again later."
    else:
        url = request.form['crawl-link']
        no_sites = request.form['crawl-number']
        thread = threading.Thread(target=engine.crawl, args=[url,int(no_sites)])
        thread.start()
        message = "Crawling started.."
    return render_template("index.html", message=message, status=get_status())

@app.route('/uploader', methods = ['POST'])
def upload_files():
    if engine.is_maintaining:
         message = "Searchito is being updated. Try again later."
    else:
        if request.method == 'POST':
           kit.create_dicrectory(engine.uploads_folder)
           for f in request.files.getlist('files'):
             filename = kit.resolve_conflict(engine.uploads_folder, secure_filename(f.filename))
             f.save(engine.uploads_folder + filename)
           thread = threading.Thread(target=engine.update_from_uploaded)
           thread.start()
           message = "All files were uploaded successfully."
    return render_template("index.html", message=message, status=get_status())

@app.route('/save')
def save():
    global engine
    if engine.is_maintaining:
         message = "Searchito is being updated. Try again later."
    else:
        engine.restart()
        message = "Server state is saved."
    return render_template("index.html", message=message, status=get_status())

if __name__ == "__main__":
    app.run(debug=True,threaded=True)
