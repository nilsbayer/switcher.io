const tracklist_btn = document.getElementById("add-to-tracklist")

if (on_tracklist == false) {
    tracklist_btn.style.backgroundColor = "#23B08F"
}
else if (on_tracklist == true) {
    tracklist_btn.style.backgroundColor = "#858585"
    tracklist_btn.innerText = "Remove again"
}

tracklist_btn.addEventListener("click", () => {

    let url_array = location.href.split("/")
    let current_token = url_array[url_array.length -1]

    if (on_tracklist == false) {
        fetch("/add-to-tracklist", {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                researcher: document.querySelector("h1").innerText,
                token: current_token
            })
        })
        .then(response => response.json())
        .then(data => {
            tracklist_btn.style.backgroundColor = "#858585"
            tracklist_btn.innerText = "Remove again"
            on_tracklist = true
        })
    }
    else if (on_tracklist == true) {
        fetch("/remove_from_tracklist", {
            method: "POST",
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                token: current_token
            })
        })
        .then(response => response.json())
        .then(data => {
            tracklist_btn.style.backgroundColor = "#23B08F"
            tracklist_btn.innerText = "Add to tracklist"
            on_tracklist = false
        })
    }

})