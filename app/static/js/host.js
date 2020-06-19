// export function viewResults() {
//     $("#vote-results-table tbody").html('');
//     var round_name = $( "#round-select option:selected" ).val();
//     var result_api_url = "/room/" + {{ room.name }} + "/results/" + round_name;
//     $.ajax({
//         type: "GET",
//         url: result_api_url,
//         success: function(response) {
//             var data = response.results;
//             for(var i = 0; i < data.length; i++) {
//                 var vote_for = data[i].vote_for;
//                 if (vote_for == 0) {
//                     vote_for = "弃票"
//                 };
//                 var row = "<tr><td>" + round_name + "</td><td>" + data[i].vote_from + "</td><td>" + vote_for + "</td></tr>";
//                 $('#vote-results-table tbody').append(row);
//             };
//             var most_voted = response.most_voted;
//             console.log(most_voted)
//             if (most_voted.length == 0) {
//                 var text_most_voted = "无人得票"
//             } else {
//                 var text_most_voted = "得票最多的玩家为";
//                 for(var i = 0; i < most_voted.length; i++) {
//                     text_most_voted = text_most_voted + " " + most_voted[i];
//                 }
//                 text_most_voted += " 号玩家"
//             }

//             $("#vote-results-most-voted").text(text_most_voted);
//             $("#vote-results").show();
//         }
//     })
// }


// var sheriff_api_url = "/room/" + {{ room.name }} + "/sheriff";
//             $("#sheriff-button").click(function(){
//                 var data = {
//                     seat: $( "#sheriff-select option:selected" ).val(),
//                 };
//                 console.log(data)
//                 $.ajax({
//                     type: "POST",
//                     url: sheriff_api_url,
//                     data: data,
//                     success: function(response) {
//                         if (response.sheriff) {
//                             console.log(response.sheriff)
//                         }
//                     }
//                 })
//             })

//             $("#round-button").click(function(){
//                 current_stage = $( "#round-select option:selected" ).val();
//             })




//             var current_stage = "警长竞选";
//             var round_api_url = "/room/" + {{ room.name }} + "/round";
//             $("#start-vote-button").click(function(){
//                 current_stage = $( "#round-select option:selected" ).val()
//                 var data = {
//                     round_name: current_stage,
//                     allow_vote: true,
//                 };
//                 $.ajax({
//                     type: "POST",
//                     url: round_api_url,
//                     data: data,
//                     success: function(response) {
//                         if (response.vote == 1) {
//                             $("#vote-stage").text('投票已开启')
//                         } else {
//                             $("#vote-stage").text('投票已结束')
//                         }
//                     }
//                 })
//             })

//             $("#end-vote-button").click(function(){
//                 var data = {
//                     round_name: $( "#round-select option:selected" ).val(),
//                     allow_vote: false,
//                 };
//                 $.ajax({
//                     type: "POST",
//                     url: round_api_url,
//                     data: data,
//                     success: function(response) {
//                         if (response.vote == 1) {
//                             $("#vote-stage").text('投票已开启')
//                         } else {
//                             $("#vote-stage").text('投票已结束')
//                         }
//                     }
//                 });
//                 viewResults();
//             })

//             var seat_api_url = "/room/" + {{ room.name }} + "/" + {{ current_user.id }} + "/seats";

//             $(document).ready(function(){
//                 setInterval(fetchseats, 3000);
//             });

//             var kill_api_url = "/room/" + {{ room.name }} + "/kill";
//             var campaign_api_url = "/room/" + {{ room.name }} + "/campaign";
//             function bindAction() {
//                 $(".action-campaign").click(function(){
//                     console.log($(this).data('seat'))
//                     var data = {
//                         seat: $(this).data('seat'),
//                         campaign: true,
//                     };
//                     $.ajax({
//                         type: "POST",
//                         url: campaign_api_url,
//                         data: data,
//                         success: function(response) {
//                             if (response.campaign) {
//                                 console.log('上警成功')
//                             } else {
//                                 console.log('退选成功')
//                             }
                            
//                         }
//                     })
//                 })

//                 $(".action-quit").click(function(){
//                     console.log($(this).data('seat'))
//                     var data = {
//                         seat: $(this).data('seat'),
//                         campaign: false,
//                     };
//                     $.ajax({
//                         type: "POST",
//                         url: campaign_api_url,
//                         data: data,
//                         success: function(response) {
//                             if (response.campaign) {
//                                 console.log('上警成功')
//                             } else {
//                                 console.log('退选成功')
//                             }
                            
//                         }
//                     })
//                 })

//                 $(".action-kill").click(function(){
//                     console.log($(this).data('seat'))
//                     var data = {
//                         seat: $(this).data('seat'),
//                     };
//                     $.ajax({
//                         type: "POST",
//                         url: kill_api_url,
//                         data: data,
//                         success: function(response) {
//                             if (response.campaign) {
//                                 console.log('死亡')
//                             }
//                         }
//                     })
//                 })
//             }

export function updateRound(url_base, round_name, vote) {
    var data = {
        round_name: round_name,
        allow_vote: vote,
    };
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

export function hostFetchSeats(url_base, user_id){
    $.ajax({
        url: url_base + "/seats",
        type: 'GET',
        success: function(response){
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
                $("#player-status-table-name-" + seat).text(row.name);
                $("#player-status-table-character-" + seat).text(row.character);
                $("#player-status-table-death-" + seat).text(row.death);
                if (row.death == "存活") {
                    survivals.push(seat);
                    var action = "<input type='submit' id='player-action-button-" + seat + "'>"
                    $("#player-status-table-action-" + seat).html(action);
                    if (current_stage == "警长竞选") {
                        if (row.in_campaign) {
                          var sheriff_value = "警上";
                        } else {
                          var sheriff_value = (row.campaigned) ? "退水" : "警下" 
                        }
                      } else {
                        var action_value = "死亡";
                        var action_class = "action-kill";
                        var sheriff_value = (row.is_sheriff) ? '👮' : ''
                    }
                    $("#player-action-button-" + seat).attr('value', action_value).attr('data-seat', seat).attr('class', action_class);
                    $("#player-status-table-sheriff-" + seat).text(sheriff_value);
                    if (sheriff_value == "退水") {
                        $("#player-action-button-" + seat).hide()
                    }
                $(".action-kill").click(function(){
                    var data = {
                        seat: $(this).data('seat'),
                    };
                    $.ajax({
                        type: "POST",
                        url: url_base + '/kill',
                        data: data,
                        success: function(response) {
                            if (response.campaign) {
                                console.log('死亡')
                            }
                        }
                    })
                })
                }
            }
            var sheriffOptionsAsString = "<option value='0'>销毁</option>";
            for(var i = 0; i < survivals.length; i++) {
                sheriffOptionsAsString += "<option value='" +  survivals[i] + "'>" +  survivals[i] + "</option>";
            };
            $("#sheriff-select").find('option').remove().end().append($(sheriffOptionsAsString));
        }
    });
}
