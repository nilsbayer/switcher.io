const download_btn = document.getElementById("download-btn")

download_btn.addEventListener("click", () => {

    fetch("/download-profile", {
        method: "POST",
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            researcher_name: document.querySelector("h1").innerText
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