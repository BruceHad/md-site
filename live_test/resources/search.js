function set_search_data(page_list){
    this.pages = page_list;
    // console.log(this.pages);
}

function create_element(type, attributes, contents) {
    var node = document.createElement(type);
    for (i in attributes){
        node[i] = attributes[i];
    }
    if(typeof contents == "string")
        contents = document.createTextNode(contents);
    node.appendChild(contents);
    return node;
}


window.addEventListener("load", function(){
    
    function search(search_string){
        var results = []; // default
        for (var i in this.pages){
            if(i.toUpperCase() == search_string.toUpperCase()){
                results = this.pages[i];
            }
        }
        return results;
    }

    function update_search(results){
        // console.log(results);
        var search_results = document.getElementById("search-results");
        search_results.innerHTML = "";
        if(results.length > 0){
            for(var i=0; i < results.length; i++){
                search_results.appendChild(
                    create_element("li", 
                        {className: "search-result"}, 
                        create_element("a", {href: 'posts/'+results[i]+'/index.html'}, results[i])
                    )
                );
            }
        } else{
            search_results.appendChild(create_element("p", 
                {className: "search-result"}, "Nothing found"));
        }
        search_results.style.visibility = 'visible';
    }
    
    var search_input = document.querySelector("input");
    search_input.addEventListener("keydown", function(event) {
        if(event.keyCode == 13){
            var search_results = [];
            var search_strings = this.value.split(' ')
            for(var i in search_strings){
                var results = search(search_strings[i]);
                // console.log(search_strings[i]);
                // console.log(results);
                for(var j in results){
                    if(search_results.indexOf(results[j]) == -1)
                    search_results.push(results[j]);
                }
            }
            // console.log(search_results);
            update_search(search_results);
        }
    });
});
