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
