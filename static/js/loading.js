const links = document.querySelectorAll(".lazy-link")

links.forEach(link => {
    link.addEventListener("click", () => {

        document.querySelector("main").innerHTML = "<h1>We currently read and analyse the papers ...</h1><h3>This could take a second.</h3><div><img src='https://i.giphy.com/media/WoWm8YzFQJg5i/giphy.webp'></div>"

    })
})