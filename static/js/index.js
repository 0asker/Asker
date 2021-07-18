if (getDarkCookie() == 'true') {
	document.getElementsByClassName('navbar')[0].classList.remove("navbar-light");
	document.getElementsByClassName('navbar')[0].classList.add("navbar-dark");
}

popular = document.getElementById('popular');
news = document.getElementById('news');
logo = document.getElementById('logo');

p_tab = document.getElementById('p_questions');
n_tab = document.getElementById('n_questions');

if (window.location.href.indexOf('news') == -1) {
	popular.classList.add('active');
	logo.href = '/popular';
	p_tab.style.display = 'block';
	n_tab.style.display = 'none';
} else {
	news.classList.add('active');
	logo.href = '/news';
	p_tab.style.display = 'none';
	n_tab.style.display = 'block';
}


// controlando cliques em <li> da <ul> de ID = tabs
popular.onclick = function () {
	popular.classList.add('active');
	news.classList.remove('active');
	window.history.pushState("object or string", "Title", "/popular");
	logo.href = '/popular';
	p_tab.style.display = 'block';
	n_tab.style.display = 'none';
}

news.onclick = function () {
	news.classList.add('active');
	popular.classList.remove('active');
	window.history.pushState("object or string", "Title", "/news");
	logo.href = '/news';
	p_tab.style.display = 'none';
	n_tab.style.display = 'block';
}


function enviar_resposta_pergunta(form) {
	
	form.style.opacity = 0.5;
	form.submit_btn.disabled = true;
	
	$.ajax({
		url: '/save_answer',
		type: 'post',
		data: $(form).serialize(),
		complete: function(data) {
			
			document.getElementById('response-counter-' + form.question_id.value).innerText = Number(document.getElementById('response-counter-' + form.question_id.value).innerText) + 1;
			
			form.parentElement.innerHTML = data.responseText;
		}
	});
	
	return false;
}


/* Linkify */
$('.description').linkify({
	target: "_blank"
});


/* Paginação */
var url = new URL(window.location.href);
var current_page = url.searchParams.get('page');

if (current_page == null)
	next_page = '2';
else
	next_page = Number(current_page) + 1;

document.getElementById('next_page_recent_questions').href += next_page;
