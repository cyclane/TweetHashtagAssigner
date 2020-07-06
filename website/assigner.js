function getHashtags(){
    let text = document.getElementById("tweet").value
    fetch(`/api/probability?text=${encodeURIComponent(text)}`).then(function (response) {
        let hashtags = response.json()["hashtags"]
        let children = document.getElementById("hashtags").children

        for (let index=0; index < children.length; index++) {
            children[index].innerHTML = hashtags[index];
        }
    })
}