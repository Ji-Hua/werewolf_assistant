export function playerFetchSeats(url_base, user_id) {
  // unbind functions
  $(".action-vote").off("click");
  $(".action-stand").off("click");
  $(".action-sit").off("click");
  $(".action-campaign").off("click");
  $(".action-quit").off("click");

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

          if (response.in_vote) {
            if(response.capabale_for_vote) {
              for(var i = 0; i < data.length; i++) {
                var seat = response.candidates[i];
                var btn_id = "player-action-button-" + seat + "-vote"
                if ($("#" + btn_id).length == 0) {
                  var vote_action = "<input type='submit' id='" + btn_id + "'>"
                  $("#player-status-table-votefor-" + seat).html(vote_action);
                  $("#" + btn_id)
                    .attr('value', "投票")
                    .attr('data-seat', seat)
                    .attr('class', "action-vote");
                }
              }
              $(".action-vote").show()
            }
          } else {
            fetchVoteResult(url_base, current_stage);
          }
          

          for(var i = 0; i < data.length; i++) {
            var row = data[i];
            var seat = row.seat;
            
            // refresh the table
            $("#player-status-table-action-" + seat).html('');
            $("#player-status-table-name-" + seat).text('');
            $("#player-status-table-character-" + seat).text('');
            $("#player-status-table-death-" + seat).text('');
            $("#player-status-table-sheriff-" + seat).text('');
            
            // write new values
            var player_name = row.name;
            if (seat == user_seat) {
              $('#player-status-table-row-' + seat).css("font-weight", "600");
              player_name += " (自己)"
            } else {
              $('#player-status-table-row-' + seat).css("font-weight", "400");
            }

            if ((row.death != "存活") && (row.name != undefined)) {
              $('#player-status-table-row-' + seat).css("background-color", "#545454");
            } else {
              $('#player-status-table-row-' + seat).css("background-color", "white");
            }
            $("#player-status-table-name-" + seat).text(player_name);
            $("#player-status-table-character-" + seat).text(row.character);
            $("#player-status-table-death-" + seat).text(row.death);

            if (current_stage == "准备阶段") {

              if (user_seat == 0 && row.name == undefined) {
                var action = "<input type='submit' id='player-action-button-" + seat + "-sit' value='坐下' class='action-sit' data-seat=" + seat +">"
                $("#player-status-table-action-" + seat).html(action);
              } else {
                if (seat == user_seat) {
                  var action = "<input type='submit' id='player-action-button-" + seat + "-sit' value='站起' class='action-stand' data-seat=" + seat +">"
                  $("#player-status-table-action-" + seat).html(action);
                } else {
                  $("#player-status-table-action-" + seat).html('');
                }
              }
            } else if (current_stage == "警长竞选") {
              if (row.death == "存活") {
                survivals.push(seat);
                
                if (row.in_campaign) {
                  var sheriff_value = "警上";
                  if (seat == user_seat) {
                    var action = "<input type='submit' id='player-action-button-" + seat + "-quit'>"
                    $("#player-status-table-action-" + seat).html(action);
                    var action_value = "退选";
                    var action_class = "action-quit";
                    $("#player-action-button-" + seat + "-quit")
                      .attr('value', action_value)
                      .attr('data-seat', seat)
                      .attr('class', action_class);
                  }
                } else {
                  var sheriff_value = (row.campaigned) ? "退水" : "-";
                  if (seat == user_seat) {
                    var action = "<input type='submit' id='player-action-button-" + seat + "-campaign'>"
                    $("#player-status-table-action-" + seat).html(action);
                    var action_value = "竞选";
                    var action_class = "action-campaign";
                    $("#player-action-button-" + seat + "-campaign")
                      .attr('value', action_value)
                      .attr('data-seat', seat)
                      .attr('class', action_class);
                  }
                }
                $("#player-status-table-sheriff-" + seat).text(sheriff_value);
                if (sheriff_value == "退水") {
                  $("#player-action-button-" + seat + "-campaign").hide()
                };
              }
            } else if(current_stage == "分发身份") {
              // TODO: add character chage card
              
            } else {
              if (row.death == "存活") {
                survivals.push(seat);
                var sheriff_value = (row.is_sheriff) ? '👮' : ''
                $("#player-status-table-sheriff-" + seat).text(sheriff_value);
              }
            }

          }

          // 警长竞选-上警
          $(".action-campaign").click(function() {
            var data = {
                seat: $(this).data('seat'),
                campaign: 1,
            };
            $.ajax({
              type: "POST",
              url: url_base + "/campaign",
              data: data,
              success: function(response) {
                if (response.campaign) {
                  console.log('上警成功')
                } else {
                  console.log('退选成功')
                }
              }
            })
          });

          // 警长竞选-退水
          $(".action-quit").click(function() {
            var data = {
              seat: $(this).data('seat'),
              campaign: 0,
            };
            $.ajax({
              type: "POST",
              url: url_base + "/campaign",
              data: data,
              success: function(response) {
                if (response.campaign) {
                  console.log('上警成功')
                } else {
                  console.log('退选成功')
                }
              }
            })
          });

          // 落座
          $(".action-sit").click(function() {
            var seat = $(this).data('seat');
            var data = {
              seat: seat
            };
            $.ajax({
              type: "POST",
              url: url_base + "/seat",
              data: data,
              success: function(response) {
                if (response.seat == seat) {
                  console.log('落座成功')
                } else {
                  console.log('落座失败')
                }
              }
            })
          });

          // 站起
          $(".action-stand").click(function() {
            var data = {
              seat: 0
            };
            $.ajax({
              type: "POST",
              url: url_base + "/seat",
              data: data,
              success: function(response) {
                if (response.seat == 0) {
                  console.log('站起成功')
                } else {
                  console.log('站起失败')
                }
              }
            })
          });

          // Vote
          $(".action-vote").click(function() {
            var vote_for = $(this).data('seat');
            var data = {
              vote_for: vote_for,
              round_name: current_stage
            };
            $.ajax({
              type: "POST",
              url: url_base + "/vote",
              data: data,
              success: function(response) {
                console.log(response)
                if (response.vote == vote_for) {
                  alert("成功投票给: " + vote_for)
                  $(".action-vote").hide()
                } else if(response.vote_for == -1) {
                  alert("本回合不可投票")
                }
              }
            })
          });

        }
      });
    }
  })
}


export function fetchCharacter(url_base, old_name) {
  $.ajax({
      type: "GET",
      url: url_base + "/character",
      success: function(response) {
          if (response) {
            if (response.character != old_name) {
              $("#player-character-img").attr('src', response.image_url);
              $("#player-character-text").text(response.character);
            }
          }
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