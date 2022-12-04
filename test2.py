import requests
from time import perf_counter

def get_author_names(coauthors):
    return [requests.get(f"https://api.openalex.org/people/{coauthor}").json().get("display_name") for coauthor in coauthors]

def main(coauthors):
    start_time = perf_counter()
    result = get_author_names(coauthors)
    print(result)
    print(f"This took sync: {perf_counter() - start_time}")

coauthors = ["A2164292938", "A2499063207", "A2119543935", "A2200192130", "A2164292938", "A2499063207", "A2119543935", "A2200192130"]

main(coauthors)