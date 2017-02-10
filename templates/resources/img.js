window.addEventListener("load", function(){
	var post = document.getElementById("article-main");
	var images_html = post.getElementsByTagName('img');
	var images = Array.prototype.slice.call(images_html)
	// console.log(images);
	// console.log(images.length);
	for (var i=0; i < images.length; i++){
		var p = images[i].parentNode;
		var a = document.createElement('a');
		a.href = images[i].src;
		a.className = i;
		a.appendChild(images[i]);
		p.appendChild(a);
	}
});