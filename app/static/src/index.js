import $ from "jquery";

function searchFormSubmit(event) {
    event.preventDefault();

    const $resultsContainer = $('.results__container');
    $resultsContainer.empty();

    $.ajax({
      type: "GET",
      url: "/search",
      data: $(event.delegateTarget).serialize(),
      processData: false
    }).done(function (data) {
      $resultsContainer.append(data)
    });
};

$(document).ready(function() {
    $('form.search').submit(searchFormSubmit);
});
