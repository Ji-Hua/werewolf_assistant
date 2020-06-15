export function playerFetchSeats(url_base, user_id) {
  var user_seat = 0;
  $.ajax({
    url: url_base + "/seat",
    type: 'get',
    success: function(response){
      user_seat = response.seat;
    }
  });

  $.ajax({
    url: url_base + "/seats",
    type: 'GET',
    success: function(response) {
      console.log(response);
      let survivals = [];
      var data = response.results;
      var current_stage = null;

      $.ajax({
        url: url_base + "/game_status",
        type: 'get',
        success: function(response){
          current_stage = response.status;
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
        if (user_seat == 0 && row.name == undefined) {
          var action = "<input type='submit' id='player-action-button-" + seat + "'>"
          $("#player-status-table-action-" + seat).html(action);
          $("#player-action-button-" + seat)
            .attr('value', "坐下")
            .attr('data-seat', seat)
            .attr('class', "action-sit");
        } else {
          
          if (row.death == "存活") {
            survivals.push(seat);
            if (seat == user_seat) {
              var action = "<input type='submit' id='player-action-button-" + seat + "'>"
              $("#player-status-table-action-" + seat).html(action);
              if (current_stage == "警长竞选") {
                if (row.in_campaign) {
                  var action_value = "退选";
                  var action_class = "action-quit";
                  var sheriff_value = "警上";
                } else {
                  var action_value = "竞选";
                  var action_class = "action-campaign";
                  var sheriff_value = (row.campaigned) ? "退水" : "警下" 
                }
              } else {
                var action_value = "站起";
                var action_class = "action-stand";
                var sheriff_value = (row.is_sheriff) ? '👮' : ''
              }
              $("#player-action-button-" + seat).attr('value', action_value).attr('data-seat', seat).attr('class', action_class);
              $("#player-status-table-sheriff-" + seat).text(sheriff_value);
              if (sheriff_value == "退水") {
                $("#player-action-button-" + seat).hide()
              };
            }
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
        console.log(data);
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
        console.log(data);
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

    }
  })
}