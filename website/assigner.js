function getHashtags(){
    let text = document.getElementById("tweet").value
    fetch(`/api/probability?text=${encodeURIComponent(text)}`).then(function (response) {
        let hashtags = response.json()["hashtags"]
        document.getElementById("hashtags").children.forEach(
           function (child) {
               child.innerHTML = hashtags[index];
           }
         );
      })
}