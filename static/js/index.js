popular = document.getElementById('popular')
news = document.getElementById('news')
logo = document.getElementById('logo')

p_tab = document.getElementById('p_questions')
n_tab = document.getElementById('n_questions')

if (window.location.href.indexOf('news') == -1) {
	popular.classList.add('active')
	logo.href = '/popular'
	p_tab.style.display = 'block'
	n_tab.style.display = 'none'
} else {
	news.classList.add('active')
	logo.href = '/news'
	p_tab.style.display = 'none'
	n_tab.style.display = 'block'
}


// controlando cliques em <li> da <ul> de ID = tabs
popular.onclick = function () {
	popular.classList.add('active')
	news.classList.remove('active')
	window.history.pushState("object or string", "Title", "/popular");
	logo.href = '/popular'
	p_tab.style.display = 'block'
	n_tab.style.display = 'none'
}

news.onclick = function () {
	news.classList.add('active')
	popular.classList.remove('active')
	window.history.pushState("object or string", "Title", "/news");
	logo.href = '/news'
	p_tab.style.display = 'none'
	n_tab.style.display = 'block'
}


function hide_form_buttons(form) {
	form.getElementsByClassName('form-button')[0].style.display = 'none'
	form.getElementsByClassName('form-button')[1].style.display = 'none'
	return false
}

function show_form_buttons(form) {
	form.getElementsByClassName('form-button')[0].style.display = 'inline'
	form.getElementsByClassName('form-button')[1].style.display = 'inline'
	return false
}

function make_answer(qid) {
	form = document.getElementById('form-' + qid);
	div = form.parentElement;
	modal = document.getElementById('modal-' + qid);
	
	form.style.display = 'none';
	modal.style.display = 'block';
	
	$.ajax({
		url: '/',
		type: 'post',
		data: $('#form-' + qid).serialize(),
		complete: function() {
			modal.style.display = 'none';
			div.innerHTML += '<span style="display: block"><b>Sua resposta:</b></span> ' + form.text.value;
		},
	});
}

function darkenLiEls() {
	lis = document.getElementsByClassName('list-group-item')
	for (i = 0; i < lis.length; i++) {
	    lis[i].classList.add('bg-dark');
	    lis[i].classList.add('text-light');
	}
	texts = document.getElementsByClassName('form-control')
	for (i = 0; i < texts.length; i++) {
	    texts[i].classList.add(formbgcolor);
	    texts[i].classList.add(textcolor);
	}
}

function toggleDarkMode() {
	darkmode=true;
	formbgcolor='bg-darkerish'; bgcolor='bg-dark'; textcolor='text-light';
	inactivetextcolor='text-secondary';
	document.body.style = "background: #222";
	document.getElementsByClassName('navbar')[0].classList.add("bg-dark");
	document.getElementsByClassName('navbar')[0].classList.add("navbar-dark");
	document.getElementsByClassName('navbar')[0].classList.remove("bg-light");
	document.getElementsByClassName('navbar')[0].classList.remove("navbar-light");
	document.getElementById('tabs').classList.add("dark");

	darkenLiEls();
	cards = document.getElementsByClassName('card');
	for (i = 0; i < cards.length; i++) {
		cards[i].classList.add('bg-dark');
		cards[i].classList.add('text-light');
	}
	maintabs = document.getElementsByClassName('main-tab')
	for (i = 0; i < maintabs.length; i++) {
		maintabs[i].classList.add(bgcolor);
		maintabs[i].classList.add(inactivetextcolor);
	}
}
