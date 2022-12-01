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
    return "<h1>Hallo</h1>"

@app.route("/profile/<string:researcher_id>", methods=["GET"])
def researcher(researcher_id):
    full_query_str = f"https://openalex.org/{researcher_id}"
    researcher_data = papers_col.find({
        "author_id": full_query_str
    }).sort("year", 1)

    # Get number of citations
    citation_data = [paper["citations"] for paper in researcher_data]
    citation_counts = []
    for paper_entry in citation_data:
        num_citations_paper = (year_entry["cited_by_count"] for year_entry in paper_entry)
        citation_this_paper = sum(num_citations_paper)
        citation_counts.append(citation_this_paper)

    # Get title and year of all papers
    all_papers = []
    for entry in researcher_data:
        paper_info = {
            "title": entry["paper_title"],
            "year": entry["year"][:4],
            "link": entry["paper_id"]
        }
        all_papers.append(paper_info)

    num_papers = len(all_papers)

    # Get list of institutions 
    all_institutions = ["AAU Business School", "ESB Business School", "SDU Odense"]
    list_institutions = ", ".join(all_institutions)

    personal_stats = {
        "author_name": researcher_id,
        "list_institutions": list_institutions,
        "last_inst": all_institutions[0],
        "author_location": "Denmark",
        "total_cits": sum(citation_counts)
    }

    return render_template("profile.html", num_papers=num_papers, all_papers=all_papers, personal_info=personal_stats)


if __name__ == "__main__":
    app.run(debug=True)