function like(likeElement, response_id) {
	like_image = likeElement.getElementsByTagName('img')[0];
	if (like_image.src.includes('white-heart.png')) {
		like_image.src = '/static/images/red-heart.png?version=3';
		span_like_counter = likeElement.getElementsByTagName('span')[0];
		span_like_counter.innerHTML = Number(span_like_counter.innerHTML) + 1;
	}
	else {
		like_image.src = '/static/images/white-heart.png?version=3';
		span_like_counter = likeElement.getElementsByTagName('span')[0];
		span_like_counter.innerHTML = Number(span_like_counter.innerHTML) - 1;
	}
	$.ajax({
		url: '/answer/like',
		data: {
			answer_id: response_id,
		},
		complete: function() {
			return;
		}
	});
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
    	});
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
			alert('Comentário deletado.');
		}
	});
}


function report_question(question_id, obj) {
	function ok() {
		obj.parentElement.innerHTML = '<p>Pergunta denunciada <i class="far fa-check-circle"></i></p>';
		obj.remove();
	}
	$.ajax({
		type: 'get',
		url: '/report',
		data: {
			type: 'question',
			id: question_id,
		},
		complete: function () {
			ok();
		}
	});
}


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
	});
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
        progressBar.style = 'width: ' + percentageString + ';';
    }
}
setPollPercentages();

if (document.getElementsByClassName('poll-chooser').length == 1) {
   openChooser();
}


function make_comment(form) {
	$(form.previousElementSibling).toggle(0);
	formData = $(form).serialize();
	$.ajax({
		url: '/comment',
		type: 'post',
		dataType: 'json',
		data: formData,
		complete: function(data) {
			new_comment = data.responseText;
			form.parentElement.getElementsByTagName('ul')[0].innerHTML += new_comment;
			form.text.value = '';
			$(form.previousElementSibling).toggle(0);
		}
	});
}


/* Linkify */
$(".q-description").linkify({
	target: "_blank"
});


/* Renderizando a parte "Responda também" da página. */
document.getElementsByTagName("main")[0].innerHTML += '<div><header><hr><h3 class="mb-3 text-center text-secondary">— Responda também —</h3><hr></header><div id="questoes_recomendadas"></div></div>';


function shuffle(array) {
  var currentIndex = array.length,  randomIndex;
  while (0 !== currentIndex) {
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex--;
    [array[currentIndex], array[randomIndex]] = [
      array[randomIndex], array[currentIndex]];
  }
  return array;
}

questoes_recomendadas_json = shuffle(questoes_recomendadas_json);

questoes_recomendadas = document.getElementById("questoes_recomendadas");

for (let index in questoes_recomendadas_json) {
	var new_html = `
	<div class="r-question">
		<a href="/question/${questoes_recomendadas_json[index]["id"]}"><b>${questoes_recomendadas_json[index]["text"]}</b></a>
		<br>
		<small class="text-muted">perguntado ${questoes_recomendadas_json[index]["pub_date"]} por <a href="/user/${questoes_recomendadas_json[index]["creator_username"]}">${questoes_recomendadas_json[index]["creator_username"]}</a></small>
		<hr>
	</div>
	`;
	questoes_recomendadas.innerHTML += new_html;
}

/* Js p/ upload de imagem em respostas */
document.getElementById('upload-photo').onchange = function () {
	text = document.getElementById('upload-photo-text');
	delete_photo_icon = document.getElementById('delete-photo-icon');
	input = document.getElementById('upload-photo');
	text.innerText = input.value.slice(12);
	delete_photo_icon.style.display = 'inline';
};

document.getElementById('delete-photo-icon').onclick = function () {
	delete_photo_icon = document.getElementById('delete-photo-icon');
	input = document.getElementById('upload-photo');
	text = document.getElementById('upload-photo-text');
	delete_photo_icon.style.display = 'none';
	text.innerText = '';
	input.value = null;
};
/* Fim: Js p/ upload de imagem em respostas */


function delete_question(id) {
    if (confirm('Opa! Tem certeza que deseja apagar sua resposta?')) {
		$.ajax({
			url: '/delete_question',
			type: 'post',
			data: {
				csrfmiddlewaretoken: csrf_token,
				question_id: id,
			},
			complete: function() {
				window.location = window.location.href.match(/^https?\:\/\/([^\/?#]+)(?:[\/?#]|$)/i)[0] + 'news';
			}
		});
	}
}


var formbgcolor='bg-white'; var bgcolor='bg-white'; var textcolor='text-dark';
var commentformbgcolor='bg-white'; var commentbgcolor='bg-light';
if (getDarkCookie() == 'true') {
	document.getElementsByClassName('navbar')[0].classList.remove("navbar-light");
	document.getElementsByClassName('navbar')[0].classList.add("navbar-dark");
}
