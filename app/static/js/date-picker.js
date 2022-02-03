import $ from "jquery";

/// Based on https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/date
// to make a flexible fallback date picker, in the absence of a native HTML5 one

function populateDays(daySelect, month) {
  // delete the current set of <option> elements out of the
  // day <select>, ready for the next set to be injected
  while (daySelect.firstChild) {
    daySelect.removeChild(daySelect.firstChild);
  }

  // Create variable to hold new number of days to inject
  let dayNum;

  // 31 or 30 days?
  if (
    (month === "January") |
    (month === "March") |
    (month === "May") |
    (month === "July") |
    (month === "August") |
    (month === "October") |
    (month === "December")
  ) {
    dayNum = 31;
  } else if (
    (month === "April") |
    (month === "June") |
    (month === "September") |
    (month === "November")
  ) {
    dayNum = 30;
  } else {
    // If month is February, calculate whether it is a leap year or not
    const year = yearSelect.value;
    const isLeap = new Date(year, 1, 29).getMonth() == 1;
    isLeap ? (dayNum = 29) : (dayNum = 28);
  }

  // inject the right number of new <option> elements into the day <select>
  for (i = 1; i <= dayNum; i++) {
    var option = document.createElement("option");
    option.textContent = i;
    daySelect.appendChild(option);
  }

  // if previous day has already been set, set daySelect's value
  // to that day, to avoid the day jumping back to 1 when you
  // change the year
  if (previousDay) {
    daySelect.value = previousDay;

    // If the previous day was set to a high number, say 31, and then
    // you chose a month with less total days in it (e.g. February),
    // this part of the code ensures that the highest day available
    // is selected, rather than showing a blank daySelect
    if (daySelect.value === "") {
      daySelect.value = previousDay - 1;
    }

    if (daySelect.value === "") {
      daySelect.value = previousDay - 2;
    }

    if (daySelect.value === "") {
      daySelect.value = previousDay - 3;
    }
  }
}

function populateYears(yearSelect) {
  // get this year as a number
  const date = new Date();
  const year = date.getFullYear();

  // Make this year, and the 500 years before it available in the year <select>
  for (i = 0; i <= 500; i++) {
    const option = document.createElement("option");
    option.textContent = year - i;
    yearSelect.appendChild(option);
  }
}

function datePickerSetup() {
  const $nativeDatePicker = $(".date-picker");
  const $fallbackPicker = $(".date-picker__fallback");
  const $fallbackLabel = $(".date-picker__fallback-label");

  // test whether a new date input falls back to a text input or not
  const test = document.createElement("input");

  try {
    test.type = "date";
  } catch (e) {
    console.log(e.description);
  }

  if (test.type === "text") {
    $nativeDatePicker.addClass("hidden");
    $fallbackPicker.removeClass("hidden");
    $fallbackLabel.removeClass("block");

    $fallbackPicker.each(function () {
      const prefix = $(this).data("id-prefix");

      const yearSelect = document.querySelector(`#${prefix}--year`);
      const monthSelect = document.querySelector(`#${prefix}--month`);
      const daySelect = document.querySelector(`#${prefix}--day`);
      // populate the days and years dynamically
      // (the months are always the same, therefore hardcoded)
      populateDays(daySelect, monthSelect.value);
      populateYears(yearSelect);

      // when the month or year <select> values are changed, rerun populateDays()
      // in case the change affected the number of available days
      yearSelect.onchange = function () {
        populateDays(daySelect, monthSelect.value);
      };

      monthSelect.onchange = function () {
        populateDays(daySelect, monthSelect.value);
      };

      //preserve day selection
      let previousDay;

      // update what day has been set to previously
      // see end of populateDays() for usage
      daySelect.onchange = function () {
        previousDay = daySelect.value;
      };
    });
  }
}

$(document).ready(function () {
  datePickerSetup();
});
