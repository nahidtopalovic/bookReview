window.addEventListener("load", function(){
    // Add a keyup event listener to our input element
    let title = document.getElementById('title');
    title.addEventListener("keyup", function(event){hinter(event)});

    // create one global XHR object
    // so we can abort old request when a new one is made
    window.hinterXHR = new XMLHttpRequest();
});

// Autocomplete for form

function hinter(event){

    // retrieve the input element
    let input = event.target;

    // retrieve the datalist element
    let book_list = document.getElementById("book_list");

    // minimum num of characters before we start to generate suggestions
    let min_characters = 2;

    if (input.value.length < min_characters){
        return
    } else {
        // abort any pending requests
        window.hinterXHR.abort();

        window.hinterXHR.onreadystatechange = function (){
            if (this.readyState == 4 && this.status == 200){
                // we're expecting a json response so we convert it to an object
                let response = JSON.parse(this.responseText);

                console.log(response)

                // clear any previously loaded options in the datalist
                book_list.innerHTML = "";

                response.forEach(function(item){
                    // Create a new <option> element
                    let option = document.createElement('option');
                    option.value = item;

                    // attach the option to the datalist element
                    book_list.appendChild(option);

                })
            }
        }
        console.log(input.value);
        window.hinterXHR.open("GET", "/autocomplete?title=" + input.value, true);
        window.hinterXHR.send();
    }

}