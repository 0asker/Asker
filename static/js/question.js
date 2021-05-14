function like(likeElement, response_id) {
	
	/* alterna a imagem do like (se coração vermelho, então fica coração branco, e vice-versa) */
	like_image = likeElement.getElementsByTagName('img')[0]
	if (like_image.src.includes('white-heart.png')) { /* se o coração for branco */
		like_image.src = '/static/images/red-heart.png'
		
		/* aumenta o total de likes do contador */
		span_like_counter = likeElement.getElementsByTagName('span')[0]
		span_like_counter.innerHTML = Number(span_like_counter.innerHTML) + 1
	}
	else {
		like_image.src = '/static/images/white-heart.png'
		
		/* diminuí o total de likes do contador */
		span_like_counter = likeElement.getElementsByTagName('span')[0]
		span_like_counter.innerHTML = Number(span_like_counter.innerHTML) - 1
	}
	
	$.ajax({
		url: '/answer/like',
		data: {
			answer_id: response_id,
		},
		complete: function() {
			return
		}
	})
}



function show_comments(commentsDiv, response_id, commentsIcon, csrf_token, user_logged, question_id) {

	commentsSection = commentsDiv.getElementsByClassName("comments")[0]
	commentsUl = commentsDiv.getElementsByClassName("comments-ul")[0]
	commentsSection.style.display = "block";
	
	if (commentsSection.getElementsByTagName('form')[0] != undefined) {
		commentsSection.getElementsByTagName('form')[0].remove()
	}
	
	if (commentsSection.getElementsByClassName('load-more')[0] != undefined) {
		commentsSection.getElementsByClassName('load-more')[0].remove()
	}
	
	$.ajax({
		url: '/comments',
		data: {
			id: response_id,
			page: commentsUl.id,
		},
		complete: function(data) {
			data = JSON.parse(data.responseText)
			$.each(data.comments, function(index, value) {
				if(user_logged != value.username) {
					commentsUl.innerHTML += '<li class="list-group-item c"><div class="comm-card"><div class="poster-container"><a class="poster-info '+textcolor+'" href="/user/'+value.username+'"><div class="poster-profile-pic-container"><img src="'+value.avatar+'" width="40px"></div><div class="poster-text-container"><span>'+value.username+'</span></div></a></div><p>'+value.text+'</p></div></li>'
				} else {
					commentsUl.innerHTML += '<li class="list-group-item c"><div class="comm-card"><div class="poster-container"><a class="poster-info '+textcolor+'" href="/user/'+value.username+'"><div class="poster-profile-pic-container"><img src="'+value.avatar+'" width="40px"></div><div class="poster-text-container"><span>'+value.username+'</span></div></a><img onclick="delete_comment('+value.comment_id+'); this.parentElement.remove()" style="float: right; cursor: pointer;" width="20px" src="/static/images/trash.png"></div><p>'+value.text+'</p></div></li>'
				}
			})
			
			if(data.has_next) {
				commentsUl.id = Number(commentsUl.id) + 1
				
				/* Adiciona elemento para clicar e carregar mais comentários */
				commentsSection.innerHTML += `<p class="btn btn-outline-primary load-more" onclick="show_comments(this.parentElement.parentElement, ${response_id}, this.parentElement.getElementsByTagName('img')[0], '${csrf_token}', '`+user_logged+`', `+question_id+`)">Carregar mais</p>`
			}
			
			/* Adiciona o formulário para comentar */
			commentsSection.innerHTML += '<form class="form-inline comm-form" method="post" action="/comment"><input type="hidden" name="csrfmiddlewaretoken" value="'+csrf_token+'"><input type="hidden" name="response_id" value="'+response_id+'">  <input type="hidden" name="question_id" value="'+question_id+'">  <input type="text" maxlength="300" autocomplete="off" class="form-control '+commentformbgcolor+' '+textcolor+'" name="text" placeholder="Escreva seu comentário"></input><input class="btn btn-primary" type="submit" value="Comentar" onclick="this.style.display=`none`"></form>'
		}
	})
	
	commentsIcon.onclick = function() {
		var el = commentsDiv.getElementsByClassName('comments')[0]
		var styleObj;

		if (typeof window.getComputedStyle != "undefined") {
			styleObj = window.getComputedStyle(el, null);
		} else if (el.currentStyle != "undefined") {
			styleObj = el.currentStyle;
		}

		if (styleObj) {
		   if(styleObj.display == 'block') {
			   el.style.display = 'none'
		   } else {
			   el.style.display = 'block'
		   }
		}
	}
}
function delete_response(response_button_dom_el, response_id) {
    if (confirm('Opa! Você tem certeza que deseja apagar sua resposta?')) {
	    $.ajax({
    		url: '/delete_response',
    		data: {
    			response_id: response_id,
    		},
    		complete: function() {
    			response_button_dom_el.parentElement.parentElement.parentElement.parentElement.remove();
    		}
    	})
    }
}

function delete_comment(comment_id, csrf_token) {
	$.ajax({
		url: '/delete_comment',
		type: 'get',
		data: {
			comment_id: comment_id,
		},
		complete: function() {
			alert('Comentário deletado.')
		}
	})
}

function report_question(question_id, obj) {
	// quando a denuncia tiver sido feita, a funcao abaixo é executada:
	function ok() {
		obj.parentElement.innerHTML = '<p>Pergunta denunciada com sucesso <i class="far fa-check-circle"></i></p>'
		obj.remove()
	}
	
	$.ajax({
		type: 'get',
		url: '/report',
		data: {
			type: 'question',
			id: question_id,
		},
		
		complete: function () {
			ok()
		}
	})
}

$(function () {
	$('[data-toggle="popover"]').popover({
		container: 'body',
		html: true,
		title: 'Denunciar abuso',
	})
})

function chooseAnswer(id) {
	$.ajax({
		url: '/answer/choose',
		data: {
			answer_id: id,
		},
		complete: function() {
		    btns = document.getElementsByClassName('choose-answer-btn');
    		for (i = btns.length-1; i >= 0; i--) {
    		    console.log('removed ' + i)
                btns[i].remove();
                location.reload();
    		}
		}
	})
}

function toggleDarkMode() {
    var formbgcolor='bg-dark'; var bgcolor='bg-dark'; var textcolor='text-light';
    var commentformbgcolor='bg-darkish'; var commentbgcolor='bg-darkerish';

    document.body.style = "background: #222";
    document.getElementsByClassName('navbar')[0].classList.add("bg-dark");
    document.getElementsByClassName('navbar')[0].classList.add("navbar-dark");
    document.getElementsByClassName('navbar')[0].classList.remove("bg-light");
    document.getElementsByClassName('navbar')[0].classList.remove("navbar-light");
    editResponseTextarea = document.getElementsByClassName('edit-response-textarea');
    if (editResponseTextarea.length > 0) { editResponseTextarea[0].classList.add(commentbgcolor); }

    cards = document.getElementsByClassName('card')
    for (i = 0; i < cards.length; i++) {
        cards[i].classList.add('bg-dark');
        cards[i].classList.add('text-light');
    }
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
    posterinfos = document.getElementsByClassName('poster-info')
    for (i = 0; i < posterinfos.length; i++) {
        posterinfos[i].classList.add(textcolor);
    }
    commentscards = document.getElementsByClassName('comments')
    for (i = 0; i < commentscards.length; i++) {
        commentscards[i].classList.add(commentbgcolor);
        commentscards[i].classList.remove(bgcolor);
    }
    dropdownmenus = document.getElementsByClassName('dropdown-menu')
    for (i = 0; i < dropdownmenus.length; i++) {
        dropdownmenus[i].classList.add(bgcolor);
    }
    dropdownitems = document.getElementsByClassName('dropdown-item')
    for (i = 0; i < dropdownitems.length; i++) {
        dropdownitems[i].classList.add(bgcolor);
        dropdownitems[i].classList.add(textcolor);
    }
}