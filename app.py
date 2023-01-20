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
import pickle
from collections import Counter
import sklearn
import numpy as np
import copy
import pandas as pd
import itertools
from fpdf import FPDF
import matplotlib.pyplot as plt

app = Flask(__name__)

load_dotenv(find_dotenv())
app.config['SECRET_KEY'] = os.getenv("APP_PWD")

from forms import SearchForm

# Database
MONGO_PWD = os.getenv("MONGO_PWD")
MONGO2_PWD = os.getenv("MONGO2_PWD")

myclient = pymongo.MongoClient(f"mongodb+srv://mar_ai:{MONGO_PWD}@cluster0.h3jd8u4.mongodb.net/?retryWrites=true&w=majority")
mydb = myclient["mydatabase"]
papers_col = mydb["papers_ai"]

# Prediction database
new_client = pymongo.MongoClient(f"mongodb+srv://mar_ai:{MONGO2_PWD}@cluster0.hmw3nfx.mongodb.net/?retryWrites=true&w=majority")
db_predictions = new_client["mydatabase"]
predictions_col = db_predictions["predictions"]

# Routes
@app.route("/")
def home():
    prior_researcher_list = request.cookies.get("prior_researchers")
    prior_inst_years = request.cookies.get("last_inst_years")
    prior_inst_numbers = request.cookies.get("last_inst_numbers")
    prior_inst_name = request.cookies.get("last_inst_name")

    tracklist = request.cookies.get("tracking_list")
    if tracklist == None:
        tracked_exists = False
    else:
        tracklist = json.loads(tracklist)
        if len(tracklist) == 0:
            tracked_exists = False
        elif len(tracklist) > 0:
            tracked_exists = True

    if prior_researcher_list == None:
        if prior_inst_years == None:
            return render_template("index.html", tracklist=tracklist, tracked_exists=tracked_exists)
        else:
            return render_template("index.html", tracklist=tracklist, tracked_exists=tracked_exists, prior_inst_name=prior_inst_name, prior_inst_years=json.loads(prior_inst_years), prior_inst_numbers=json.loads(prior_inst_numbers))
    else:
        prior_researcher_list = json.loads(prior_researcher_list) 
        if prior_inst_years == None:
            return render_template("index.html", tracklist=tracklist, tracked_exists=tracked_exists, prior_researcher_list=list(reversed(prior_researcher_list)))
        return render_template("index.html", tracklist=tracklist, tracked_exists=tracked_exists, prior_inst_name=prior_inst_name, prior_researcher_list=list(reversed(prior_researcher_list)), prior_inst_years=json.loads(prior_inst_years), prior_inst_numbers=json.loads(prior_inst_numbers))

def get_request(url):
    r = requests.get(url)
    return r.json()

async def asyncr_get_req(url):
    return await asyncio.to_thread(get_request, url)

async def get_coauthor_names(coauthor):
    url = f"https://api.openalex.org/people/{coauthor}"
    author_data = await asyncr_get_req(url)
    return author_data.get("display_name") 

async def get_coauthor_names_and_link(coauthor):
    url = f"https://api.openalex.org/people/{coauthor}"
    author_data = await asyncr_get_req(url)
    item = {
        "name": author_data.get("display_name"),
        "link": coauthor
    }
    return item

@app.route("/search", methods=["GET", "POST"])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        start_time = perf_counter()
        chosen_inst = form.institution.data

        this_inst_entries = papers_col.find({
            "institution_name": chosen_inst,
            "dropout_year": {"$exists": True}
        })
        dropouts = []
        for entry in this_inst_entries:
            entry_ = {
                "author": entry["author_id"],
                "dropout_year": entry["dropout_year"]
            }
            if entry_ not in dropouts:
                dropouts.append(entry_)

        years = [year_entry["dropout_year"] for year_entry in dropouts]
        years_counted = Counter(years)
        years_counted = dict(sorted(years_counted.items()))

        # Get the dropout numbers for the institution
        dropouts_numbers = [num for num in years_counted.values()]
        dropouts_years = [int(num) for num in years_counted.keys()]
        len_dropouts = len(dropouts_numbers)

        # Get researchers at institution
        this_inst_authors_entries = papers_col.find({
            "institution_name": chosen_inst,
            "dropout_year": {"$exists": False}
        })

        inst_author_names = []
        for entry in this_inst_authors_entries:
            if entry.get("data_for_pred") == None:
                pred_data = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
            elif entry.get("data_for_pred") != None:
                pred_data = entry.get("data_for_pred")
            entry_ = {
                "author_id": entry["author_id"].replace("https://openalex.org/", ""),
                "author_name": entry["author_name"],
                "pred_data": pred_data
            }

            author_last_entry = papers_col.find({
                "author_id": entry["author_id"]
            }).sort("year", -1)
            if author_last_entry[0].get("institution_name") == chosen_inst:
                if entry_ not in inst_author_names:
                    inst_author_names.append(entry_)
        
        print(inst_author_names)
        length_inst_auths = len(inst_author_names)

        # inst_authors = list(set([auth["author_id"].replace("https://openalex.org/", "") for auth in this_inst_authors_entries]))
        # length_inst_auths = len(inst_authors)

        # async def main(coauthors):
        #     author_names = await asyncio.gather(*[get_coauthor_names_and_link(coauthor) for coauthor in coauthors])
        #     return author_names

        # inst_author_names = []
        # if length_inst_auths > 6:
        #     for i in range(math.ceil(length_inst_auths / 6)):
        #         print(f"Round: {i}")
        #         current_coauthor_list = inst_authors[:6]
        #         del inst_authors[:6]
        #         inst_author_names_part = asyncio.run(main(current_coauthor_list))
        #         for auth_item in inst_author_names_part: inst_author_names.append(auth_item)
        #         time.sleep(2)
        # else:
        #     inst_author_names = asyncio.run(main(inst_authors))


        # add machine learning model here
        model = pickle.load(open('final_model.pkl', 'rb'))

        def make_prediction(auth_vals):
            auth_vals = np.array([auth_vals])
            print("AUTH_VALS", auth_vals)
            y_pred = model.predict_proba(auth_vals)
            pred = y_pred[:, 1][0] * 100
            
            return pred

        async def asyncr_prediction(auth_vals):
            return await asyncio.to_thread(make_prediction, auth_vals)

        async def get_author_pred(auth_to_pred):
            author_pred = await asyncr_prediction(auth_to_pred)
            return author_pred

        async def main(auths_to_pred):
            author_preds = await asyncio.gather(*[get_author_pred(auth_to_pred.get("pred_data")) for auth_to_pred in auths_to_pred])
            return author_preds

        # df = pd.read_csv("x.csv")
        # for auth in inst_author_names:
            # authors_pred_vals = df[df["author_id"] == auth.get("author_id")].iloc[:1, 2:]
        #     auth.update({"pred_data": authors_pred_vals})

        author_predictions = asyncio.run(main(inst_author_names))
        authors_zip = list(zip(inst_author_names, author_predictions))
        authors_zip = sorted(authors_zip, key=lambda d: d[1], reverse=True) 
        print(authors_zip)

        res = make_response(render_template("search.html", len_dropouts=len_dropouts, search_results=authors_zip, form=form, dropout_numbers=dropouts_numbers, dropout_years=json.dumps(dropouts_years)))
        if len(dropouts_years) > 0:
            res.set_cookie("last_inst_years", json.dumps(dropouts_years))
            res.set_cookie("last_inst_numbers", json.dumps(dropouts_numbers))
            res.set_cookie("last_inst_name", chosen_inst)

        print(f"Loading time: {perf_counter() - start_time}")
        return res

    else:
        print(form.errors)
        return render_template("search.html", form=form)

@app.route("/help")
def help():
    return render_template("help.html")

@app.route("/about")
def about():
    return render_template("about.html")

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
    total_amount_citations = r.json().get("cited_by_count")

    average_citations = {
        "2000": 0,
        "2001": 0,
        "2002": 0,
        "2003": 0,
        "2004": 0,
        "2005": 0,
        "2006": 0,
        "2007": 0,
        "2008": 0,
        "2009": 0,
        "2010": 0,
        "2011": 0,
        "2012": 39.11,
        "2013": 43.66,
        "2014": 46.86,
        "2015": 50.09,
        "2016": 51.82,
        "2017": 54.57,
        "2018": 63.57,
        "2019": 80.84,
        "2020": 98.41,
        "2021": 109.98,
        "2022": 74.14,
        "2023": 74.14
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

    # researcher_data = papers_col.find({
    #     "author_id": full_query_str
    # }).sort("year", 1)
    # # Get number of citations
    # citation_data = [paper["citations"] for paper in researcher_data]
    # citation_counts = []
    # all_years_list = []
    # for paper_entry in citation_data:
    #     num_citations_paper = (year_entry["cited_by_count"] for year_entry in paper_entry)
    #     citation_this_paper = sum(num_citations_paper)
    #     citation_counts.append(citation_this_paper)
    #     for year_entry in paper_entry:
    #         all_years_list.append(year_entry["year"])

    # #  List of years for x axis
    # all_years_list = set(all_years_list)
    # all_years_list = list(all_years_list)
    # all_years_list.sort()


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
    
    drop_out_year = 2024
    print(all_institutions, inst_country_list)

    # researcher_data = papers_col.find({
    #     "author_id": full_query_str
    # }).sort("year", 1)

    # last_inst_of_author = researcher_data[0].get("last_inst")
    # last_inst_of_author = last_inst_of_author.replace("https://openalex.org/", "")
    # r_last_inst = requests.get(f"https://api.openalex.org/institutions/{last_inst_of_author}")
    # last_inst_of_author = r_last_inst.json().get("display_name")

    if all_institutions[-1] != None and all_institutions[-1] != "":
        last_inst_of_author = all_institutions[-1]
    else:
        last_inst_of_author[-2]

    if inst_country_list[-1] != None and inst_country_list[-1] != "":
        current_country = inst_country_list[-1]
    elif inst_country_list[-1] == None or inst_country_list[-1] == "":
        if inst_country_list[-2] != None or inst_country_list[-2] != "":
            current_country = inst_country_list[-2]
        else:
            current_country = "-"

    personal_stats = {
        "author_name": authors_name,
        "author_surname": authors_surname,
        "list_institutions": list_institutions,
        "last_inst": last_inst_of_author,
        "author_location": current_country,
        # "total_cits": sum(citation_counts),
        "total_cits": total_amount_citations,
        "drop_out_year": drop_out_year
    }


    # Get data prepared for the network visualization
    all_papers_list = papers_col.distinct("paper_id", {"author_id": full_query_str})
    coauthor_list = papers_col.distinct("author_id", {
        "paper_id": { "$in": all_papers_list}
    })
    coauthor_list.remove(full_query_str)
    length_coauthor = len(coauthor_list)
    coauthor_list = [coauthor.replace("https://openalex.org/", "") for coauthor in coauthor_list]
    # coauthor_list_complex = []
    # coauthor_list = []
    # nodes = []
    # edges = []
    # for coauthor in coauthors_list:
    #     coauthor_id = coauthor.get("author_id").replace("https://openalex.org/", "")
    #     _ = {
    #         "coauthor_name": coauthor.get("author_name"),
    #         "coauthor_id": coauthor_id
    #     }
    #     if _ not in coauthor_list:
    #         coauthor_list_complex.append(_)
    #         coauthor_list.append(coauthor_id)
    #         node = {
    #             "color": "#c4c4c4",
    #             "id": coauthor_id,
    #             "label": _.get("coauthor_name"),
    #             "shape": "dot",
    #             "size": 10
    #         }
    #         edge = {
    #             "from": researcher_id,  
    #             "to": coauthor_id,  
    #             "width": 1,  
    #         }
    #         nodes.append(node)
    #         edges.append(edge)

    copied_coauthor_list = copy.copy(coauthor_list)
    
    # coauthor_list = list(set(coauthor_list))
    # # length_coauthor = len(coauthor_list)
    # print(coauthor_list)
   
    # ASYNC

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

    # Get connections between coauthors
    def get_connection(author_url):
        coauthors_paper_ids = papers_col.distinct("paper_id", {"author_id": author_url})
        co_coauthor_list = papers_col.distinct("author_id",{
            "paper_id": { "$in": coauthors_paper_ids}
        })
        co_coauthor_list.remove(author_url)
        co_coauthor_list = [coauthor.replace("https://openalex.org/", "") for coauthor in co_coauthor_list]
        return co_coauthor_list

    async def asyncr_connection(author_url):
        return await asyncio.to_thread(get_connection, author_url)

    async def get_author_cocoauthors(author_url):
        author_url = f"https://openalex.org/{author_url}"
        author_pred = await asyncr_connection(author_url)
        return author_pred

    async def main(auths_to_connect):
        author_preds = await asyncio.gather(*[get_author_cocoauthors(auth_to_connect) for auth_to_connect in auths_to_connect])
        # print("AUTHOR_PREDS:", author_preds)
        return author_preds

    # author_cocoauthors = asyncio.run(main(coauthor_list))
    final_author_cocoauthors = []
    print("LENGTH COAUTHOR", length_coauthor)
    if length_coauthor < 6:
        for i in range(math.ceil(length_coauthor / 6)):
            print(f"Round: {i}")
            current_coauthor_list = coauthor_list[:6]
            del coauthor_list[:6]
            author_cocoauthors = asyncio.run(main(current_coauthor_list))
            for auth_item in author_cocoauthors: final_author_cocoauthors.append(auth_item)
            time.sleep(1)
    else:
        for coauth in copied_coauthor_list:
            coauth = f"https://openalex.org/{coauth}"
            coauthors_paper_ids = papers_col.distinct("paper_id", {"author_id": coauth})
            co_coauthor_list = papers_col.distinct("author_id",{
                "paper_id": { "$in": coauthors_paper_ids}
            })
            # print("AUTHORS", co_coauthor_list)
            co_coauthor_list.remove(coauth)
            co_coauthor_list = [coauthor.replace("https://openalex.org/", "") for coauthor in co_coauthor_list]
            final_author_cocoauthors.append(co_coauthor_list)

    zipped_coauthors = list(zip(copied_coauthor_list, final_author_cocoauthors))
    for zip_coauth in zipped_coauthors:
        for cocoauth in zip_coauth[1]:
            if cocoauth in copied_coauthor_list:
                edge =  {
                    "from": zip_coauth[0],
                    "to": cocoauth,
                    "width": 1
                }
                other_way_around = {
                "from": cocoauth,
                "to": zip_coauth[0],
                "width": 1
                }
                if other_way_around not in edges:
                    edges.append(edge)
    # ASYNC ENDE

    # Calculate switching probability
    model = pickle.load(open('final_model.pkl', 'rb'))

    researcher_data = papers_col.find({
        "author_id": full_query_str
    }).sort("year", 1)
    queried_researcher = researcher_data[0].get("data_for_pred")
    if queried_researcher != None:
        queried_researcher = np.array([queried_researcher])
    elif queried_researcher == None:
        queried_researcher = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]])
    print("This resaerchers data:", queried_researcher)

    # df = pd.read_csv("x.csv")
    # queried_researcher = df[df["author_id"] == researcher_id].iloc[:1, 2:]

    y_pred = model.predict_proba(queried_researcher)
    prediction = y_pred[:, 1][0]

    print("MODEL:", model.predict(queried_researcher))

    switching_prob = "%.0f" % round((prediction * 100), 0)
    prob_circle = 252 - (252*prediction)

    # Model to predict after how many years the researcher might leave
    model_years = pickle.load(open("final_model_2.pkl", "rb"))
    years_from_first_paper = model_years.predict(queried_researcher)
    years_from_first_paper = years_from_first_paper[0]
    if years_from_first_paper < 4:
        soon_var = "very soon"
    elif years_from_first_paper >= 4 and years_from_first_paper < 7:
        soon_var = "soon"
    elif years_from_first_paper >= 7:
        soon_var = "not soon"

    print("PAPER YEAR", all_papers[0].get("year"))

    # Checking whether researcher is on tracklist
    current_researcher_info = {
        "token": researcher_id,
        "name": authors_name
    }
    prior_tracking_list = request.cookies.get("tracking_list")
    print("THIS HERE ****************************", prior_tracking_list)
    if prior_tracking_list == None:
        on_tracklist = "false"
    else:
        prior_tracking_list = json.loads(prior_tracking_list)
        if len(prior_tracking_list) == 0:
            on_tracklist = "false"
        else:
            for saved_researcher in prior_tracking_list:
                saved_token = saved_researcher.get("token")
                if researcher_id == saved_token:
                    on_tracklist = "true"
                else:
                    on_tracklist = "false"

    # print("NODES", nodes)
    # print("EDGES", edges)
    res = make_response(render_template("profile.html", on_tracklist=on_tracklist, soon_var=soon_var, prob_circle=prob_circle, switching_prob=switching_prob, node_list=json.dumps(nodes), edge_list=json.dumps(edges), length_coauthor=length_coauthor, profile_exists=True, num_papers=num_papers, all_papers=all_papers, personal_info=personal_stats, all_citation_counts=all_citations, all_years_list=all_citation_years, average_citations=average_citations))
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

@app.route("/download-profile", methods=["POST"])
def download_profile():
    if request.method == "POST":
        data = request.get_json()
        current_name = data.get('researcher_name')
        current_inst = data.get('current_inst')
        total_cits = data.get('total_cits')
        estimated_location = data.get('estimated_location')
        list_institutions = data.get('list_institutions')
        switching_prob = data.get('switching_prob')
        soon_var = data.get('soon_var')
        citations_per_year = data.get('citations_per_year')
        graph_years = data.get('years')
        current_token = data.get('current_token')
        # Create the PDF 
        WIDTH = 210
        HEIGHT = 297

        def create_profile_pdf(author_name, current_inst, total_citations, est_location, all_insts, prob_switching, timing, years, cits_per_year, current_token):
            pdf = FPDF(orientation = 'P', unit = 'mm', format='A4')
            pdf.add_page()
            # Author name as title
            pdf.set_font('Helvetica', 'B', 28)
            pdf.ln(8)
            pdf.write(10, f'{author_name}')

            pdf.set_font("Helvetica", '', 12)
            pdf.ln(15)
            pdf.write(10, f"Current institution: {current_inst}")
            pdf.ln(8)
            pdf.write(10, f"Total citation count: {total_citations}")
            pdf.ln(8)
            pdf.write(10, f"Estimated location: {est_location}")
            pdf.ln(8)
            pdf.write(10, f"Associated institutions: {all_insts}")
            pdf.ln(20)

            # Prediction score
            pdf.set_font('Helvetica', 'B', 20)
            pdf.write(10, "Predictions")
            pdf.ln(15)
            pdf.set_font("Helvetica", '', 12)
            pdf.write(10, f"Probability of switching: {prob_switching}%")
            pdf.ln(8)
            pdf.write(10, f"Timing of switching: {timing}")
            pdf.ln(20)

            # Citations per year
            plt.bar(years, height=cits_per_year, color="#23B08F")
            plt.savefig(f"./static/pdfs/{author_name}_citations.png")
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('Helvetica', 'B', 20)
            pdf.write(10, "Citations per year")
            pdf.ln(15)
            pdf.image(f"./static/pdfs/{author_name}_citations.png", w=WIDTH/1.5)
            
            pdf.set_font("Helvetica", '', 12)  
            pdf.cell(0, 0, f"https://switcher.herokuapp.com/profile/{current_token}")
            pdf.link(0, 0, 100, 10, f"https://switcher.herokuapp.com/profile/{current_token}")

            pdf.output(f'./static/pdfs/{author_name}.pdf', 'F')

        create_profile_pdf(current_name, current_inst, total_cits, estimated_location, list_institutions, switching_prob, soon_var, graph_years, citations_per_year, current_token)

        return jsonify({
            "message": "success",
            "pdf_link": f"../static/pdfs/{current_name}.pdf"
        })
    else:
        return jsonify({"message": "error: wrong http method"})

@app.route("/remove-pdf", methods=["POST"])
def remove_pdf():
    if request.method == "POST":
        to_be_removed = request.get_json().get("researcher_name")
        os.remove(os.path.join(os.curdir, "static", "pdfs", f"{to_be_removed}.pdf"))
        os.remove(os.path.join(os.curdir, "static", "pdfs", f"{to_be_removed}_citations.png"))

        return jsonify({"message": f"removed {to_be_removed}"})

@app.route("/add-to-tracklist", methods=["POST"])
def add_to_tracklist():
    if request.method == "POST":
        current_researcher = request.get_json().get("researcher")
        current_researcher_token = request.get_json().get("token")

        res = make_response(jsonify({"message": "success added"}))
        current_researcher_info = {
            "token": current_researcher_token,
            "name": current_researcher
        }
        prior_tracking_list = request.cookies.get("tracking_list")
        if prior_tracking_list == None:
            prior_tracking_list = []
        else:
            prior_tracking_list = json.loads(prior_tracking_list)
            for saved_researcher in prior_tracking_list:
                saved_token = saved_researcher.get("token")
                if current_researcher_token == saved_token:
                    prior_tracking_list.remove(saved_researcher)
        prior_tracking_list.append(current_researcher_info)
        res.set_cookie("tracking_list", json.dumps(prior_tracking_list))

        return res

@app.route("/remove_from_tracklist", methods=["POST"])
def remove_from_tracklist():
    if request.method == "POST":
        current_researcher_token = request.get_json().get("token")

        res = make_response(jsonify({"message": "success removed"}))

        prior_tracking_list = request.cookies.get("tracking_list")
        if prior_tracking_list == None:
            pass
        else:
            prior_tracking_list = json.loads(prior_tracking_list)
            for saved_researcher in prior_tracking_list:
                saved_token = saved_researcher.get("token")
                if current_researcher_token == saved_token:
                    prior_tracking_list.remove(saved_researcher)
                    res.set_cookie("tracking_list", json.dumps(prior_tracking_list))
        return res

@app.route("/fetch-network", methods=["POST"])
def fetch_network():
    if request.method == "POST":
        sent_nodes = request.get_json().get("current_nodes")

        profile_node = sent_nodes[0]
        new_nodes = []
        new_nodes.append(profile_node)

        def pick_node_color(prob_score):
            if prob_score <= 10:
                color = "#F3E6DA"
            elif prob_score <= 20 and prob_score > 10:
                color = "#F9DDC4"
            elif prob_score <= 30 and prob_score > 20:
                color = "#F4CAA2"
            elif prob_score <= 40 and prob_score > 30:
                color = "#EFB987"
            elif prob_score <= 50 and prob_score > 40:
                color = "#E9A76A"
            elif prob_score <= 60 and prob_score > 50:
                color = "#EB9D55"
            elif prob_score <= 70 and prob_score > 60:
                color = "#E1934A"
            elif prob_score <= 80 and prob_score > 70:
                color = "#DB883B"
            elif prob_score <= 90 and prob_score > 80:
                color = "#EE821F"
            elif prob_score <= 100 and prob_score > 90:
                color = "#E56E00"

            return color

        requested_authors = [node.get("id") for node in sent_nodes]
        del requested_authors[0]
        
        for requested_author in requested_authors:
            # try:
            author = predictions_col.find({
                "author_id": requested_author
            })
            color = pick_node_color(author[0].get("prediction"))
            new_node = {
                "color": color,
                "id": requested_author,
                "label": author[0].get("author_name"),
                "shape": "dot",
                "size": 10
            }
            new_nodes.append(new_node)
            # except:
            #     print(f"This author is not given: {requested_author}")

        new_nodes_static = [{"color": "#23B08F", "id": "A2102965651", "label": "Fisher Yu", "shape": "square", "size": 10}, {"color": "#990000", "id": "A3215289805", "label": "Jiashi Feng", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A3206266945", "label": "Yang Gao", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A3043071695", "label": "Varun Agrawal", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A3015769185", "label": "Haofeng Chen", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2969332786", "label": "Wenqi Xian", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2902866982", "label": "Fangchen Liu", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2902440875", "label": "Bingyi Kang", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2891126297", "label": "Zi-Yi Dou", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2800964704", "label": "Yingying Chen", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2798407434", "label": "Amit Raj", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2778599308", "label": "Vashisht Madhavan", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2658800667", "label": "Xin Wang", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2650877479", "label": "Jingwan Lu", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2566736780", "label": "Zhuang Liu", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2514427603", "label": "Andy Zeng", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2483816572", "label": "Patsorn Sangkloy", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2396181419", "label": "Jianxiong Xiao", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2304177752", "label": "Linguang Zhang", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2252171364", "label": "Joseph E. Gonzalez", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2223720701", "label": "Huazhe Xu", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2174985400", "label": "Trevor Darrell", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2166284823", "label": "Xiaoou Tang", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2161412237", "label": "James Hays", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2138701653", "label": "Zhirong Wu", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2136189631", "label": "Thomas Funkhouser", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2114560125", "label": "Chen Fang", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2111957820", "label": "Angel X. Chang", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2095742376", "label": "Shuran Song", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A2011491954", "label": "Aditya Khosla", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A1951833338", "label": "Manolis Savva", "shape": "dot", "size": 10}, {"color": "#990000", "id": "A1809196549", "label": "Vladlen Koltun", "shape": "dot", "size": 10}]

        return jsonify({"sent_data": new_nodes})

if __name__ == "__main__":
    app.run(debug=True)