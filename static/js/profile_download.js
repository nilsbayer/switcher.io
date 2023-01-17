const download_btn = document.getElementById("download-btn")

download_btn.addEventListener("click", () => {

    let url_array = location.href.split("/")
    let current_token = url_array[url_array.length -1]

    fetch("/download-profile", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            researcher_name: document.querySelector("h1").innerText,
            current_inst: current_inst,
            total_cits: total_cits,
            estimated_location: estimated_location,
            list_institutions: list_institutions,
            switching_prob: switching_prob,
            soon_var: soon_var,
            citations_per_year: citations_per_year,
            years: years,
            current_token: current_token
        })
    })
    .then(response => response.json())
    .then(data => {
        let downloader = document.createElement("a")
        downloader.setAttribute("href", data.pdf_link)
        downloader.setAttribute("download", "file")
        document.body.append(downloader)
        downloader.click()
        downloader.remove()
    })
    .then(() => {
        setTimeout(() => {
            fetch("/remove-pdf", {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    researcher_name: document.querySelector("h1").innerText
                })
            })
        }, 2000)
        
    })
})