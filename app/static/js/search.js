import $ from "jquery";
import { initializeMaps, addSearchResult } from "./map.js";

const $resultsContainer = $(".results__container");
const $searchButton = $(".search__button");

var load = document.getElementById("load");

// A helper method to clear away existing search
// results and disable the
// search form while a search is being done
function showSearchPending() {
  $resultsContainer.empty();
  $searchButton.prop("disabled", true);
  load.style.display = "block";
}

// A helper method to handle the chain of events that
// needs to happen after either a new search or a
// pagination
function handleSearchResults($ajaxPromise) {
  $ajaxPromise
    .done(function (data) {
      $resultsContainer.append(data);

      // Need to add event handlers for these after inserting them on the page
      $(".pagination").click(paginate);
      $(".show_less_button").hide();
      $(".show_more_button").click(showFullResult);
      $(".show_less_button").click(hideFullResult);
    })
    .fail(function (error) {
      $resultsContainer.append(error.responseText);
    })
    .always(function () {
      $searchButton.prop("disabled", false);
      $resultsContainer[0].focus();
      $resultsContainer[0].scrollIntoView();
      load.style.display = "none";
      initializeMaps();
      for (const [name, geometry] of Object.entries(resultGeometries)) {
        addSearchResult(name, geometry);
      }
    });
}

// Search form event handlers
function searchFormSubmit(event) {
  event.preventDefault();
  showSearchPending();

  const $form = $(event.delegateTarget);
  gtag("event", "search", {
    search_term: $form.find("input[name='text']").val()
  });
  handleSearchResults(

    $.ajax({
      type: "GET",
      url: $form.data("api-url"),
      data: $form.find("input[value!='']").serialize(),
      processData: false,
    })
    
  );
}

// Search result UI; show and hide the full result
function showFullResult(event) {
  $(event.delegateTarget)
    .siblings(".result--truncated")
    .removeAttr("aria-expanded")
    .attr("aria-hidden", true)
    .hide();

  $(event.delegateTarget)
    .siblings(".result--full")
    .removeAttr("aria-hidden")
    .attr("aria-expanded", true)
    .show();
  $(event.delegateTarget).siblings(".show_less_button").show();

  $(event.delegateTarget).hide();
}

function hideFullResult(event) {
  $(event.delegateTarget)
    .siblings(".result--full")
    .removeAttr("aria-expanded")
    .attr("aria-hidden", true)
    .hide();
  $(event.delegateTarget)
    .siblings(".result--truncated")
    .removeAttr("aria-hidden")
    .attr("aria-expanded", false)
    .show();

  $(event.delegateTarget).hide();
  $(event.delegateTarget).siblings(".show_more_button").show();
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
  $(".pagination").click(paginate);
});

