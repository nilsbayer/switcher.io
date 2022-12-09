from flask import Flask, render_template, jsonify, request, url_for, abort, make_response
import pymongo
import os
from dotenv import load_dotenv, find_dotenv
from datetime import date
import json
import requests
import asyncio
import time
from time import perf_counter
import math

app = Flask(__name__)

load_dotenv(find_dotenv())
app.config['SECRET_KEY'] = os.getenv("APP_PWD")

from forms import SearchForm

# Database
MONGO_PWD = os.getenv("MONGO_PWD")

myclient = pymongo.MongoClient(f"mongodb+srv://mar_ai:{MONGO_PWD}@cluster0.h3jd8u4.mongodb.net/?retryWrites=true&w=majority")
mydb = myclient["mydatabase"]
papers_col = mydb["papers_ai"]

# Routes
@app.route("/")
def home():
    prior_researcher_list = request.cookies.get("prior_researchers")
    if prior_researcher_list == None:
        return render_template("index.html")
    else:
        prior_researcher_list = json.loads(prior_researcher_list) 
        return render_template("index.html", prior_researcher_list=list(reversed(prior_researcher_list)))
    

@app.route("/search", methods=["GET", "POST"])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        # add machine learning model here
        # model =
        authors_list_from_model = [
            {
                "name": "Roman Jurowetzki",
                "prob_score": "98%",
                "link": "A2164292938"
            },
            {
                "name": "Yasmine Sarraj",
                "prob_score": "98%",
                "link": "A2160074034"
            }
        ]
        form.institution.choices = [form.institution.data]
        dropouts_numbers = [3, 5, 5, 7]
        dropouts_years = [2017, 2018, 2019, 2020]

        return render_template("search.html", search_results=authors_list_from_model, form=form, dropout_numbers=dropouts_numbers, dropout_years=dropouts_years)
    
    else:
        print(form.errors)
        # Get all institutions
        form.institution.choices = ["A", "B", "C"]
        
        return render_template("search.html", form=form)

@app.route("/help")
def help():
    return render_template("help.html")

@app.route("/profile/<string:researcher_id>", methods=["GET"])
def researcher(researcher_id):
    start_time = perf_counter()
    full_query_str = f"https://openalex.org/{researcher_id}"

    if papers_col.count_documents({ "author_id": full_query_str }) < 1:
        return render_template("profile.html", profile_exists=False)

    r = requests.get(f"https://api.openalex.org/people/{researcher_id}")
    authors_name = r.json().get("display_name")
    authors_surname = authors_name.split(" ")[-1]
    all_citations = list(reversed([work.get("cited_by_count") for work in r.json().get("counts_by_year")]))
    all_citation_years = list(reversed([work.get("year") for work in r.json().get("counts_by_year")]))

    average_citations = {
        "2000": 1000,
        "2001": 1200,
        "2002": 1400,
        "2003": 1600,
        "2004": 1800,
        "2005": 2000,
        "2006": 2200,
        "2007": 2400,
        "2008": 2600,
        "2009": 2800,
        "2010": 3000,
        "2011": 3200,
        "2012": 3400,
        "2013": 3600,
        "2014": 3800,
        "2015": 4000,
        "2016": 4200,
        "2017": 4400,
        "2018": 4600,
        "2019": 4800,
        "2020": 5000,
        "2021": 5200,
        "2022": 5400
    }

    average_citations = [average_citations.get(str(y)) for y in all_citation_years]

    researcher_data = papers_col.find({
        "author_id": full_query_str
    }).sort("year", 1)

    # Get title and year of all papers
    all_papers = []
    for entry in researcher_data:
        paper_info = {
            "title": entry["paper_title"],
            "year": entry["year"][:4],
            "link": entry["paper_id"]
        }
        if paper_info not in all_papers:
            all_papers.append(paper_info)

    num_papers = len(all_papers)

    researcher_data = papers_col.find({
        "author_id": full_query_str
    }).sort("year", 1)
    # Get number of citations
    citation_data = [paper["citations"] for paper in researcher_data]
    citation_counts = []
    all_years_list = []
    for paper_entry in citation_data:
        num_citations_paper = (year_entry["cited_by_count"] for year_entry in paper_entry)
        citation_this_paper = sum(num_citations_paper)
        citation_counts.append(citation_this_paper)
        for year_entry in paper_entry:
            all_years_list.append(year_entry["year"])

    # Dictionary of years and citations
    

    #  List of years for x axis
    all_years_list = set(all_years_list)
    all_years_list = list(all_years_list)
    all_years_list.sort()


    # Get list of institutions 
    researcher_data = papers_col.find({
        "author_id": full_query_str
    }).sort("year", 1)
    all_institutions = [paper.get("institution_name") for paper in researcher_data]
    all_institutions = set(all_institutions)
    all_institutions = list(all_institutions)
    list_institutions = " | ".join(all_institutions)

    researcher_data = papers_col.find({
        "author_id": full_query_str
    }).sort("year", 1)
    inst_country_list = [paper.get("institution_country") for paper in researcher_data]
    current_country = inst_country_list[-1]

    personal_stats = {
        "author_name": authors_name,
        "author_surname": authors_surname,
        "list_institutions": list_institutions,
        "last_inst": all_institutions[-1],
        "author_location": current_country,
        "total_cits": sum(citation_counts)
    }

    # Get data prepared for the network visualization
    all_papers_list = papers_col.distinct("paper_id", {"author_id": full_query_str})
    coauthor_list = papers_col.distinct("author_id",{
        "paper_id": { "$in": all_papers_list}
    })
    coauthor_list.remove(full_query_str)
    length_coauthor = len(coauthor_list)
    coauthor_list = [coauthor.replace("https://openalex.org/", "") for coauthor in coauthor_list]
   
    # ASYNC
    def get_request(url):
        r = requests.get(url)
        return r.json()

    async def asyncr_get_req(url):
        return await asyncio.to_thread(get_request, url)

    async def get_coauthor_names(coauthor):
        url = f"https://api.openalex.org/people/{coauthor}"
        author_data = await asyncr_get_req(url)
        return author_data.get("display_name")

    async def get_nodes_and_edges(coauthor_name_id, researcher_id):
        node_list = []
        edge_list = []
        for coauthor in list(coauthor_name_id):
            node = {
                "color": "#c4c4c4",
                "id": coauthor[1],
                "label": coauthor[0],
                "shape": "dot",
                "size": 10
            }
            node_list.append(node)
            edge = {
                "from": researcher_id,  
                "to": coauthor[1],  
                "width": 1,  
            }
            edge_list.append(edge)
        return node_list, edge_list

    # running the functions
    async def main(coauthors):
        author_names = await asyncio.gather(*[get_coauthor_names(coauthor) for coauthor in coauthors])
        coauthor_name_id = zip(author_names, coauthors)
        node_list, edge_list = await get_nodes_and_edges(coauthor_name_id, researcher_id)
        return node_list, edge_list

    first_node = {
        "color": "#23B08F",
        "id": researcher_id,
        "label": authors_name,
        "shape": "square",
        "size": 10
    }
    nodes = []
    edges = []

    if length_coauthor > 6:
        for i in range(math.ceil(length_coauthor / 6)):
            current_coauthor_list =  coauthor_list[:6]
            del coauthor_list[:6]
            node_list, edge_list = asyncio.run(main(current_coauthor_list))
            for node_list_item in node_list: nodes.append(node_list_item) 
            for edge_list_item in edge_list: edges.append(edge_list_item)
            time.sleep(1)
    else:
        nodes, edges = asyncio.run(main(coauthor_list))

    nodes.append(first_node)
    nodes = list(reversed(nodes))
    # ASYNC ENDE

    res = make_response(render_template("profile.html", node_list=json.dumps(nodes), edge_list=json.dumps(edges), length_coauthor=length_coauthor, profile_exists=True, num_papers=num_papers, all_papers=all_papers, personal_info=personal_stats, all_citation_counts=all_citations, all_years_list=all_citation_years, average_citations=average_citations))
    this_researcher = {
        "token": researcher_id,
        "name": authors_name,
        "date": date.today().strftime("%d.%m.%Y")
    }
    prior_researcher_list = request.cookies.get("prior_researchers")
    if prior_researcher_list == None:
        prior_researcher_list = []
    else:
        prior_researcher_list = json.loads(prior_researcher_list)
        for saved_researcher in prior_researcher_list:
            saved_token = saved_researcher.get("token")
            if researcher_id == saved_token:
                prior_researcher_list.remove(saved_researcher)
    prior_researcher_list.append(this_researcher)
    res.set_cookie("prior_researchers", json.dumps(prior_researcher_list))

    print(f"*********** Load time: {perf_counter() - start_time} *****************")
    return res



if __name__ == "__main__":
    app.run(debug=True)