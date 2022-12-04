import asyncio
import requests

def get_request(url):
    r = requests.get(url)
    print(r)
    return r.json()

async def asyncr_get_req(url):
    return await asyncio.to_thread(get_request, url)

async def get_coauthor_names(coauthor):
    url = f"https://api.openalex.org/people/{coauthor}"
    author_data = await asyncr_get_req(url)
    return author_data.get("display_name")

async def get_nodes_and_edges(coauthor_name_id, researcher_id):
    node_list = [
        {
            "color": "#23B08F",
            "id": researcher_id,
            "label": authors_name,
            "shape": "square",
            "size": 10
        }
    ]
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

authors_name = "Herr Anfang"
researcher_id = "ABCDE"

coauthors = ["A2164292938", "A2499063207", "A2119543935", "A2200192130", "A2164292938", "A2499063207", "A2119543935", "A2200192130"]

node_list, edge_list = asyncio.run(main(coauthors))
