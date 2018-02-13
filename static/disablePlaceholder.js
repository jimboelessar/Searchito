document.getElementById("typeCheck").addEventListener("change", function(){
    if (document.getElementById("typeCheck").checked) {
        document.getElementById("querybox").placeholder = "";
    } else {
        document.getElementById("querybox").placeholder = "(Metallica and not Beyonce) or Manowar";
    }
});