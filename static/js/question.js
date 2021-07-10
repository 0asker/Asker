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
    			response_button_dom_el.parentElement.parentElement.parentElement.remove();
    		}
    	})
    }
}

function delete_comment(comment_id) {
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
	
	formData = $(form).serialize();
	
	$.ajax({
		url: '/comment',
		type: 'post',
		data: formData,
		complete: function() {
			
			new_comment = `
		<li class="list-group-item c no-horiz-padding">
				<div class="comm-card">
						<div class="poster-container">
								<a class="poster-info" href="/user/`+current_user['username']+`">
										<div class="poster-profile-pic-container">
												<img src="`+current_user['profile_picture_url']+`" width="40px">
										</div>
										<div class="poster-text-container">
												<span>`+current_user['username']+`</span>
												&nbsp;|&nbsp;
												<span class="post-pub-date">agora</span>
										</div>
								</a>
						</div>
						<p>`+form.text.value+`</p>
				</div>
		</li>
`
			
			form.parentElement.getElementsByTagName('ul')[0].innerHTML += new_comment;
			form.text.value = '';
		}
	});
}


/* Linkify */
$(".q-description").linkify({
	target: "_blank"
});
