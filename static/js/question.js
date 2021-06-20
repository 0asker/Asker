function like(likeElement, response_id) {
	
	/* alterna a imagem do like (se coração vermelho, então fica coração branco, e vice-versa) */
	like_image = likeElement.getElementsByTagName('img')[0]
	if (like_image.src.includes('white-heart.png')) { /* se o coração for branco */
		like_image.src = '/static/images/red-heart.png?version=3'
		
		/* aumenta o total de likes do contador */
		span_like_counter = likeElement.getElementsByTagName('span')[0]
		span_like_counter.innerHTML = Number(span_like_counter.innerHTML) + 1
	}
	else {
		like_image.src = '/static/images/white-heart.png?version=3'
		
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
                btns[i].remove();
                location.reload();
    		}
		}
	})
}

function voteOnPoll() {
    let userChoicesEls = $("input[name='poll-option']:checked");
    let userChoices = [];
    if (userChoicesEls.length < 1) { return 0; }
    for (var i = 0; i < userChoicesEls.length; i++) {
        userChoices.push(userChoicesEls[i].value);
    }
    $.ajax({
      type: "POST",
      url: '/poll/vote',
      data: {
          poll: $("input[name=qpoll]").val(),
          choices: userChoices,
          csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
      },
      success: function() {
          window.location.reload();
      }
    });
}

function undoVote() {
    $.ajax({
      type: "POST",
      url: '/poll/undovote',
      data: {
          poll: $("input[name=qpoll]").val(),
          csrfmiddlewaretoken: $("input[name=csrfmiddlewaretoken]").val(),
      },
      success: function() {
          window.location.reload();
      }
    });
}

function openChooser() {
    let chooser = document.getElementsByClassName('poll-chooser')[0];
    let shower = document.getElementsByClassName('poll-shower')[0];
    shower.style.display = 'none';
    chooser.style.display = 'block';
}

function openShower() {
    let chooser = document.getElementsByClassName('poll-chooser')[0];
    let shower = document.getElementsByClassName('poll-shower')[0];
    chooser.style.display = 'none';
    shower.style.display = 'block';
}

function setPollPercentages() {
    if (document.getElementsByClassName('poll-shower').length == 0) { return 0; }
    let els = document.getElementsByClassName('choice-show');
    var totalVotes = 0;
    var votes = [];
    for (var i=0; i < els.length; i++) {
        let choiceVotes = Number(els[i].getElementsByClassName('vote-count')[0].textContent);
        totalVotes = totalVotes + choiceVotes;
        votes.push(choiceVotes);
    }

    for (var i=0; i < els.length; i++) {
        let progressBar = els[i].getElementsByClassName('progress-bar')[0];
        let percentage = (votes[i] / totalVotes) * 100;
        let percentageString = Math.round(percentage) + '%';
        if (percentage >= 15) { progressBar.textContent = percentageString; }
        progressBar.title = percentageString;
        progressBar.style = 'width: ' + percentageString + ';'
    }
}
setPollPercentages();

if (document.getElementsByClassName('poll-chooser').length == 1) {
   openChooser();
}


/*
 * Faz um comentário.
 */
function make_comment(form) {
    
    form.parentElement.getElementsByTagName('center')[0].getElementsByTagName('img')[0].style.display = 'block';
    
    formValues = $(form).serialize();
    
    form.text.value = '';
    
    $.post("/comment", formValues, function(data) {
        
        form.parentElement.getElementsByTagName('center')[0].getElementsByTagName('img')[0].style.display = 'none';
        
        var comment_template = `
        <li class="list-group-item c">
            <div class="comm-card">
                <div class="poster-container">
                    <a class="poster-info" href="` + data['username'] + `">
                        <div class="poster-profile-pic-container">
                            <img src="` + data['profile_picture'] + `" width="40px">
                        </div>
                        <div class="poster-text-container">
                            <span>` + data['username'] + `</span>
                            &nbsp;|&nbsp;
                            <span class="post-pub-date">` + data['posted_time'] + `</span>
                        </div>
                    </a>
                    <i class="fas fa-trash" onclick="delete_comment(` + data['id'] + `); this.parentElement.parentElement.parentElement.remove()" style="float: right; cursor: pointer;"></i>
                </div>
                <p>` + data['text'] + `</p>
            </div>
        </li>
        `;
        
        var ul = form.parentElement.getElementsByTagName('ul')[0];
        ul.innerHTML += comment_template;
    });
}


function show_comments(element, response_id, jaAbriu, usuario_logado) {
    
    comments = document.getElementById('comments-response-' + response_id);
    
    if (jaAbriu) {
        if (comments.style.display == 'block') {
            comments.style.display = 'none';
        } else {
            comments.style.display = 'block';
        }
        
        return false;
    }
    
    element.getElementsByTagName('center')[0].getElementsByTagName('img')[0].style.display = 'block'; /* ícone de carregamento de comentários */
    
    if (window.getComputedStyle(comments, null).display == 'none')
        comments.style.display = 'block';
    else {
        comments.style.display = 'none';
        return false;
    }
    
    $.ajax({
        type: 'get',
        url: '/comments',
        dataType: 'json',
        data: {
            response_id: response_id,
        },
        complete: function(data) {
            element.getElementsByTagName('center')[0].getElementsByTagName('img')[0].style.display = 'none'; /* ícone de carregamento de comentários */
            
            comments = JSON.parse(data.responseText);
            
            for (comment in comments) {
                
                adminOrNot = '';
                
                if (comments[comment]['username'] == usuario_logado) {
                    adminOrNot = '<i class="fas fa-trash" onclick="delete_comment(' + comments[comment]['id'] + '); this.parentElement.parentElement.parentElement.remove()" style="float: right; cursor: pointer;"></i>';
                } else {
                    adminOrNot = '';
                }
                
                var comment_template = `
                <li class="list-group-item c">
                    <div class="comm-card">
                        <div class="poster-container">
                            <a class="poster-info" href="/user/` + comments[comment]['username'] + `">
                                <div class="poster-profile-pic-container">
                                    <img src="` + comments[comment]['profile_picture'] + `" width="40px">
                                </div>
                                <div class="poster-text-container">
                                    <span>` + comments[comment]['username'] + `</span>
                                    &nbsp;|&nbsp;
                                    <span class="post-pub-date">` + comments[comment]['posted_time'] + `</span>
                                </div>
                            </a>` +
                            adminOrNot +
                            `
                        </div>
                        <p>` + comments[comment]['text'] + `</p>
                    </div>
                </li>
                `;
                
                element.getElementsByTagName('ul')[0].innerHTML += comment_template;
            }
        }
    });
}
