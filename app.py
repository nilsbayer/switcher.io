from flask import Flask, render_template, jsonify, request
import pymongo
import os
from dotenv import load_dotenv, find_dotenv

app = Flask(__name__)

# Database
load_dotenv(find_dotenv())
MONGO_PWD = os.getenv("MONGO_PWD")

myclient = pymongo.MongoClient(f"mongodb+srv://mar_ai:{MONGO_PWD}@cluster0.h3jd8u4.mongodb.net/?retryWrites=true&w=majority")
mydb = myclient["mydatabase"]
papers_col = mydb["papers_ai"]

# Routes
@app.route("/")
def home():
    authors_papers = papers_col.find({
        "author_id": "https://openalex.org/A2164292938"
    })
    papers = authors_papers[0]["paper_id"]
    return render_template("home.html", papers=papers)

@app.route("/researcher/<string:researcher_id>", methods=["GET"])
def researcher(researcher_id):
    full_query_str = f"https://openalex.org/{researcher_id}"
    researcher_data = papers_col.find({
        "author_id": full_query_str
    })
    all_papers = []
    for entry in researcher_data:
        paper_info = {
            "paper_id": entry["paper_id"],
            "year": entry["year"][:4]
        }
        all_papers.append(paper_info)
    return render_template("researcher.html", all_papers)


if __name__ == "__main__":
    app.run(debug=True)