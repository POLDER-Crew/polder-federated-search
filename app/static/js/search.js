import $ from "jquery";

const $resultsContainer = $(".results__container");
const $searchButton = $(".search__button");
var load = document.getElementById("load");

// A helper method to clear away existing search
// results and disable the
// search form while a search is being done
function showSearchPending() {
  $resultsContainer.empty();
  $searchButton.prop("disabled", true);
  load.style.display ="block";
}

// A helper method to handle the chain of events that
// needs to happen after either a new search or a
// pagination
function handleSearchResults($ajaxPromise) {
  $ajaxPromise
    .done(function (data) {
      $resultsContainer.append(data);

      // Need to add event handlers for these after inserting them on the page
      $(".abstract--truncated").click(showFullAbstract);
      $(".abstract--full").click(hideFullAbstract);
      $(".pagination").click(paginate);
    })
    .fail(function (error) {
      $resultsContainer.append(error.responseText);
    })
    .always(function () {
      $searchButton.prop("disabled", false);
      $resultsContainer.focus();
      load.style.display = "none";
    });
}

// Search form event handlers
function searchFormSubmit(event) {
  event.preventDefault();
  showSearchPending();

  const $form = $(event.delegateTarget);

  handleSearchResults(
    $.ajax({
      type: "GET",
      url: $form.data("api-url"),
      data: $form.find("input[value!='']").serialize(),
      processData: false,
    })
  );
}

// Search result UI; show and hide the full abstract
function showFullAbstract(event) {
  $(event.delegateTarget)
    .removeAttr("aria-expanded")
    .attr("aria-hidden", true)
    .hide();
  $(event.delegateTarget)
    .siblings(".abstract--full")
    .removeAttr("aria-hidden")
    .attr("aria-expanded", true)
    .show();
}

function hideFullAbstract(event) {
  $(event.delegateTarget)
    .removeAttr("aria-expanded")
    .attr("aria-hidden", true)
    .hide();
  $(event.delegateTarget)
    .siblings(".abstract--truncated")
    .removeAttr("aria-hidden")
    .attr("aria-expanded", false)
    .show();
}

// When js is enabled, paginate and show results in the
// results container
function paginate(event) {
  event.preventDefault();
  showSearchPending();

  const url = $(event.delegateTarget).attr("href");

  handleSearchResults(
    $.ajax({
      type: "GET",
      url: url,
    })
  );
}

$(document).ready(function () {
  $("form.search").submit(searchFormSubmit);
  $(".abstract--truncated").click(showFullAbstract);
  $(".abstract--full").click(hideFullAbstract);
  $(".pagination").click(paginate);
});