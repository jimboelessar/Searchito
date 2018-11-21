document.getElementById("typeCheck").addEventListener("change", function(){
    if (document.getElementById("typeCheck").checked) {
        if (document.getElementById("querybox")) {
            document.getElementById("querybox").placeholder = "";
        } else {
            document.getElementById("queryboxMini").placeholder = "";
        }
    } else {
        if (document.getElementById("querybox")) {
            document.getElementById("querybox").placeholder = "(Metallica and not Beyonce) or Manowar";
        } else {
            document.getElementById("queryboxMini").placeholder = "(Metallica and not Beyonce) or Manowar";
        }
    }
});