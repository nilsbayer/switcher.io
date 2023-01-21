window.addEventListener("load", () => {

    fetch("/fetch-network", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            current_nodes: node_list
        })
    })
    .then(response => response.json())
    .then(data => {
        new_nodes = data.sent_data
    })

    fetch("/fetch-network-collaboration", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            current_nodes: node_list
        })
    })
    .then(response => response.json())
    .then(data => {
        col_nodes = data.sent_data
        latest_year = data.max_year
        earliest_year = data.min_year
    })

})