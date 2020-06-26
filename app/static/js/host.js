export function updateRound(url_base, round_name, vote) {
    var data = {
        round_name: round_name,
        allow_vote: vote,
    };
    console.log(data)
    $.ajax({
        type: "POST",
        url: url_base + "/round",
        data: data,
        success: function(response) {
            if (response.round_name) {
                console.log(response.round_name)
            } else {
                alert('回合设置失败')
            }
        }
    })
}

export function assignCharacters(url_base) {
    var data = {
      assign_characters: true
    };
    console.log(data);
    $.ajax({
        type: "POST",
        url: url_base + "/character",
        data: data,
        success: function(response) {
            if (response.data) {
                console.log(response.data)
            }
        }
    })
}

export function hostFetchSeats(url_base, user_id) {
  var user_seat = 0;
  $.ajax({
    url: url_base + "/seat",
    type: 'GET',
    success: function(response){
      user_seat = response.seat;
    }
  });

  $.ajax({
    url: url_base + "/seats",
    type: 'GET',
    success: function(response) {
      var data = response.results;
      $.ajax({
        url: url_base + "/round",
        type: 'GET',
        success: function(response){
          let survivals = [];
          var current_stage = response.round_name;

          fetchVoteResult(url_base, current_stage);

          for(var i = 0; i < data.length; i++) {
            var row = data[i];
            var seat = row.seat;

            if ((row.death != "存活") && (row.name != undefined)) {
              $('#player-status-table-row-' + seat).css("background-color", "#545454");
            }

            // refresh the table
            $("#player-status-table-action-" + seat).html('');
            $("#player-status-table-name-" + seat).text('');
            $("#player-status-table-character-" + seat).text('');
            $("#player-status-table-death-" + seat).text('');
            $("#player-status-table-sheriff-" + seat).text('');

            // write new values
            $("#player-status-table-name-" + seat).text(row.name);
            $("#player-status-table-character-" + seat).text(row.character);
            $("#player-status-table-death-" + seat).text(row.death);
            if (row.death == "存活") {
              survivals.push(seat);
              var action_death = "<input type='submit' id='player-action-button-" + seat + "-death' value='死亡' class='action-kill' data-seat=" + seat +">";
              var action_sheriff = "<input type='submit' id='player-action-button-" + seat + "-death' value='警徽' class='action-badge' data-seat=" + seat +">";
              var action = action_death + action_sheriff;
              if (current_stage == "警长竞选") {
                if (row.in_campaign) {
                  action += "<input type='submit' id='player-action-button-" + seat + "-quit'>"
                  $("#player-status-table-action-" + seat).html(action);
                  var action_value = "退选";
                  var action_class = "action-quit";
                  var sheriff_value = "警上";
                  $("#player-action-button-" + seat + "-quit")
                    .attr('value', action_value)
                    .attr('data-seat', seat)
                    .attr('class', action_class);
                } else {
                  action += "<input type='submit' id='player-action-button-" + seat + "-campaign'>"
                  $("#player-status-table-action-" + seat).html(action);
                  var action_value = "竞选";
                  var action_class = "action-campaign";
                  var sheriff_value = (row.campaigned) ? "退水" : "警下";
                  $("#player-action-button-" + seat + "-campaign")
                    .attr('value', action_value)
                    .attr('data-seat', seat)
                    .attr('class', action_class);
                }
              } else {
                $("#player-status-table-action-" + seat).html(action);
                var sheriff_value = (row.is_sheriff) ? '👮' : '';
              }
              $("#player-status-table-sheriff-" + seat).text(sheriff_value);
            }

            $(".action-kill").off("click");
            $(".action-badge").off("click");

            $(".action-kill").click(function(){
                var seat = $(this).data('seat');
                var data = {
                  seat: seat
                };
                $.ajax({
                  type: "POST",
                  url: url_base + '/kill',
                  data: data,
                  success: function(response) {
                    if (response.death == seat) {
                        console.log('死亡')
                    }
                  }
                })
            })

            $(".action-badge").click(function(){
              var seat = $(this).data('seat');
              var data = {
                seat: seat
              };
              $.ajax({
                type: "POST",
                url: url_base + '/sheriff',
                data: data,
                success: function(response) {
                  if (response.death == seat) {
                      console.log('警徽')
                  }
                }
              })
          })
          }

        }
      });

      
    }
  })
}


export function fetchVoteResult(url_base, stage) {
  $.ajax({
    type: "GET",
    url: url_base + "/vote",
    success: function(response) {
      if (response.vote_stage == null)
      {
        $("#vote-stage-span").text('');
      } else {
        $("#vote-stage-span").text(response.vote_stage);
      }
      $("#vote-max-span").text(response.most_voted);

      var invalid_round = ["准备阶段", "分发身份", "等待上帝指令"];
      for (var i = 0; i < response.results.length; i++) {
        if (invalid_round.includes(stage)) {
          $("#player-status-table-votefor-" + i).text('');
        } else {
          var row = response.results[i];
          var vote_for = row.vote_for;
          if (vote_for == 0) {
            vote_for = "未投票"
          }
          $("#player-status-table-votefor-" + row.vote_from).text(vote_for);
        }
      }
    }
  })
}
