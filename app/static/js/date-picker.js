import $ from "jquery";

/// Based on https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/date
// to make a flexible fallback date picker, in the absence of a native HTML5 one

function populateDays(daySelect, month, yearSelect, previousDay) {
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
    const year = yearSelect.val();
    const isLeap = new Date(year, 1, 29).getMonth() == 1;
    isLeap ? (dayNum = 29) : (dayNum = 28);
  }

  // inject the right number of new <option> elements into the day <select>
  for (let i = 1; i <= dayNum; i++) {
    var option = document.createElement("option");
    option.textContent = i;
    option.value = i.toString().padStart(2, '0')
    daySelect.append(option);
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
    if (daySelect.val() === "") {
      daySelect.val(reviousDay - 1);
    }

    if (daySelect.val() === "") {
      daySelect.val(previousDay - 2);
    }

    if (daySelect.val() === "") {
      daySelect.val(previousDay - 3);
    }
  }
}

function populateYears(yearSelect) {
  // get this year as a number
  const date = new Date();
  const year = date.getFullYear();

  // Make this year, and the 500 years before it available in the year <select>
  for (let i = 0; i <= 500; i++) {
    const option = document.createElement("option");
    option.textContent = year - i;
    yearSelect.append(option);
  }
}

function populateFormValue(dateFormField, yearSelect, monthSelect, daySelect) {
  dateFormField.val(
    `${yearSelect.val()}-${monthSelect.val()}-${daySelect.val()}`
  );
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

  if (test.type === "date") {
    $nativeDatePicker.addClass("hidden");
    $fallbackPicker.removeClass("hidden");
    $fallbackLabel.removeClass("hidden");

    $fallbackPicker.each(function () {
      const prefix = $(this).data("id-prefix");

      const yearSelect = $(`#${prefix}--year`);
      const monthSelect = $(`#${prefix}--month`);
      const daySelect = $(`#${prefix}--day`);
      const dateFormField = $(`#${prefix}`);

      //preserve day selection
      let previousDay;

      // populate the days and years dynamically
      // (the months are always the same, therefore hardcoded)
      populateDays(daySelect, monthSelect.val(), yearSelect, previousDay);
      populateYears(yearSelect);

      // when the month or year <select> values are changed, rerun populateDays()
      // in case the change affected the number of available days
      yearSelect.change(function () {
        populateDays(daySelect, monthSelect.val(), yearSelect, previousDay);
        populateFormValue(dateFormField, yearSelect, monthSelect, daySelect);
      });

      monthSelect.change(function () {
        populateDays(daySelect, monthSelect.val(), yearSelect, previousDay);
        populateFormValue(dateFormField, yearSelect, monthSelect, daySelect);
      });

      // update what day has been set to previously
      // see end of populateDays() for usage
      daySelect.change(function () {
        previousDay = daySelect.value;
        populateFormValue(dateFormField, yearSelect, monthSelect, daySelect);
      });
    });
  }
}

$(document).ready(function () {
  datePickerSetup();
});
