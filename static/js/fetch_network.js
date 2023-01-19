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

})