const links = document.querySelectorAll(".lazy-link")

links.forEach(link => {
    link.addEventListener("click", () => {

        document.querySelector("main").innerHTML = "<h1>Loading data ...</h1><h3>This could take a second.</h3>"

    })
})