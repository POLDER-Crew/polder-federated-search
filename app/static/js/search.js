import $ from "jquery";

// Search form event handlers
function searchFormSubmit(event) {
    event.preventDefault();

    const $resultsContainer = $('.results__container');
    $resultsContainer.empty();

    const $form = $(event.delegateTarget);
    $.ajax({
      type: "GET",
      url: $form.data('api-url'),
      data: $form.find("input[value!='']").serialize(),
      processData: false
    }).done(function (data) {
      $resultsContainer.append(data);

      // Need to add event handlers for these after inserting them on the page
      $('.abstract--truncated').click(showFullAbstract);
      $('.abstract--full').click(hideFullAbstract);
    }).fail(function(error) {
      console.error(error);
    });
};

// Search result UI; show and hide the full abstract
function showFullAbstract(event) {
  $(event.delegateTarget)
    .removeAttr('aria-expanded')
    .attr('aria-hidden', true)
    .hide();
  $(event.delegateTarget)
    .siblings('.abstract--full')
    .removeAttr('aria-hidden')
    .attr('aria-expanded', true)
    .show();
};

function hideFullAbstract(event) {
  $(event.delegateTarget)
    .removeAttr('aria-expanded')
    .attr('aria-hidden', true)
    .hide();
  $(event.delegateTarget)
    .siblings('.abstract--truncated')
    .removeAttr('aria-hidden')
    .attr('aria-expanded', false)
    .show();
};

$(document).ready(function() {
    $('form.search').submit(searchFormSubmit);
    $('.abstract--truncated').click(showFullAbstract);
    $('.abstract--full').click(hideFullAbstract);
});
