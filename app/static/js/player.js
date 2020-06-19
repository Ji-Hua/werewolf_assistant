// var status_api_url = "/room/" + {{ room.name }} + "/game_status";
// var candidates_api_url = "/room/" + {{ room.name }} + "/candidates";
// var vote_api_url = "/room/" + {{ room.name }} + "/vote";
// var prev_status = "";
// var prev_stage = "";
// function fetchstatus(){
//     $.ajax({
//         url: status_api_url,
//         type: 'get',
//         success: function(response){
//             console.log(response.status);
//             $("#vote-label").text( response.status);
//             if (response.status != prev_status) {
//                 prev_status = response.status;
//                 if (response.status != "等待上帝指令") {
//                     prev_stage = response.status;
//                     console.log(prev_stage);
//                     $("#vote-stage").text('投票已开启');
//                     $.getJSON(candidates_api_url, function(data) {
//                         var optionsAsString = "<option value='0'>弃权</option>";
//                         for(var i = 0; i < data.candidates.length; i++) {
//                             optionsAsString += "<option value='" +  data.candidates[i] + "'>" +  data.candidates[i] + "</option>";
//                         };
//                         $("#vote-select").find('option').remove().end().append($(optionsAsString));
//                     });
//                 } else {
//                     $("#vote-stage").text('投票已关闭');
//                     $("#vote-select").find('option').remove().end();
//                     viewResults();
//                 }
//             } 
//         }
//     });
// }


export function playerFetchSeats(url_base, user_id) {
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
      let survivals = [];
      var data = response.results;
      var current_stage = null;

      $.ajax({
        url: url_base + "/round",
        type: 'GET',
        success: function(response){
          current_stage = response.round;
        }
      });

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
        $("#player-status-table-name-" + seat).text(row.name);
        $("#player-status-table-character-" + seat).text(row.character);
        $("#player-status-table-death-" + seat).text(row.death);

        if (current_stage == "准备阶段") {
          var action = "<input type='submit' id='player-action-button-" + seat + "'>"
          $("#player-status-table-action-" + seat).html(action);
          if (user_seat == 0 && row.name == undefined) {
            var action_value = "坐下";
            var action_class = "action-sit";
          } else {
            if (seat == user_seat)  {
              var action_value = "站起";
              var action_class = "action-stand";
            }
          }
          $("#player-action-button-" + seat)
            .attr('value', action_value)
            .attr('data-seat', seat)
            .attr('class', action_class);
        } else if (current_stage == "警长竞选") {
          if (row.death == "存活") {
            survivals.push(seat);
            if (seat == user_seat) {
              var action = "<input type='submit' id='player-action-button-" + seat + "'>"
              $("#player-status-table-action-" + seat).html(action);
              if (row.in_campaign) {
                var action_value = "退选";
                var action_class = "action-quit";
                var sheriff_value = "警上";
              } else {
                var action_value = "竞选";
                var action_class = "action-campaign";
                var sheriff_value = (row.campaigned) ? "退水" : "警下" 
              }
            }
            $("#player-action-button-" + seat)
              .attr('value', action_value)
              .attr('data-seat', seat)
              .attr('class', action_class);
            $("#player-status-table-sheriff-" + seat).text(sheriff_value);
            if (sheriff_value == "退水") {
              $("#player-action-button-" + seat).hide()
            };
          }
        } else if(current_stage == "分发身份") {
          // TODO: add character chage card
        } else if (current_stage != "等待上帝指令") {
          if (row.death == "存活") {
            var action = "<input type='submit' id='player-action-button-" + seat + "'>"
            $("#player-status-table-action-" + seat).html(action);
            $("#player-action-button-" + seat)
              .attr('value', "投票")
              .attr('data-seat', seat)
              .attr('class', "action-vote");
          }

        }
      }

      // 警长竞选-上警
      $(".action-campaign").click(function() {
        var data = {
            seat: $(this).data('seat'),
            campaign: true,
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
          campaign: false,
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
            if (response.vote_for == vote_for) {
              console.log(response)
            } else {
              alert("当前不可投票")
            }
          }
        })
      });

    }
  })
}