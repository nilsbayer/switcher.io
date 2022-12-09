import asyncio
import pymongo
from dotenv import load_dotenv, find_dotenv
import os

load_dotenv(find_dotenv())
MONGO_PWD = os.getenv("MONGO_PWD")

myclient = pymongo.MongoClient(f"mongodb+srv://mar_ai:{MONGO_PWD}@cluster0.h3jd8u4.mongodb.net/?retryWrites=true&w=majority")
mydb = myclient["mydatabase"]
papers_col = mydb["papers_ai"]

# Start async code
def get_request(url):
    all_papers_list = papers_col.distinct("paper_id", {"author_id": url})
    extended_coauthor_list = papers_col.distinct("author_id",{
        "paper_id": { "$in": all_papers_list}
    })
    extended_coauthor_list.remove(url)
    extended_coauthor_list.remove(researcher_id)
    extended_coauthor_list = [coauthor.replace("https://openalex.org/", "") for coauthor in coauthor_list]
    return extended_coauthor_list

async def asyncr_get_req(url):
    return await asyncio.to_thread(get_request, url)

async def get_coauthor_names(coauthor):
    url = f"https://openalex.org/{coauthor}"
    author_data = await asyncr_get_req(url)
    return author_data.get("display_name")

async def get_edges_betw_coauthors(coauthor_name_id, researcher_id):
    edge_list = []
    for coauthor in list(coauthor_name_id):
        edge = {
            "from": researcher_id,  
            "to": coauthor[1],  
            "width": 1,  
        }
        edge_list.append(edge)
    return edge_list


# running the functions
async def main(coauthors):
    author_names = await asyncio.gather(*[get_coauthor_names(coauthor) for coauthor in coauthors])
    coauthor_name_id = zip(author_names, coauthors)
    edge_list = await get_edges_betw_coauthors(coauthor_name_id, researcher_id)
    return edge_list

authors_name = "Herr Anfang"
researcher_id = "ABCDE"

coauthors = ["A808621600", "A258609416", "A2514924063", "A2233031296"]

extended_edge_list = asyncio.run(main(coauthors))
