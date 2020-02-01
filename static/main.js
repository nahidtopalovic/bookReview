window.addEventListener("load", function(){
    // Add a keyup event listener to our input element
    let title = document.getElementById('title');
    title.addEventListener("keyup", function(event){hinter(event, "book_list", "title=")});
  
    // create one global XHR object
    // so we can abort old request when a new one is made
    window.hinterXHR = new XMLHttpRequest();
    
});

// Autocomplete for form

function hinter(event, className, arg ){

    // retrieve the input element
    let input = event.target;

    // retrieve the datalist element
    let prime_list = document.getElementById(className);

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

                // clear any previously loaded options in the datalist
                prime_list.innerHTML = "";

                response["results"].forEach(function(item){
                    // Create a new <option> element
                    let option = document.createElement('option');
                    option.value = item;

                    // attach the option to the datalist element
                    prime_list.appendChild(option);

                })

            }
        }
        window.hinterXHR.open("GET", "/autocomplete?"+arg + input.value, true);
        window.hinterXHR.send();
    }

}

// fix validation of form
// validation of from

function validateForm(){
    // Get the input element
    let input = document.getElementById("title");
    // get the datalist
    let book_list = document.getElementById("book_list");

    // if we find the input inside our list, we submit the form
    for (let element of book_list.children){
        if(element.value == input.value){
            return true;
        }
    }

    // we send an error message
    alert("input is invalid")
    return false

}