const config = window.APP_CONFIG;

async function fetchJson(url) {
  let response;
  try {
    response = await fetch(url, { cache: "no-store" });
  } catch (error) {
    throw new Error("starting up, try again");
  }
  if (response.status === 503) {
    throw new Error("starting up, try again");
  }
  if (!response.ok) {
    throw new Error("request failed");
  }
  return response.json();
}

async function loadHabits() {
  const message = document.getElementById("message");
  const retry = document.getElementById("retry");
  const habitsElement = document.getElementById("habits");
  message.textContent = "Loading...";
  retry.hidden = true;
  habitsElement.replaceChildren();

  try {
    const habits = await fetchJson(config.habitsUrl + "/habits");
    message.textContent = "";
    for (const habit of habits) {
      const card = document.createElement("section");
      card.className = "habit";
      const title = document.createElement("h3");
      title.textContent = habit.name;
      card.appendChild(title);

      const details = document.createElement("p");
      details.textContent = "Loading insights...";
      card.appendChild(details);

      const checkIn = document.createElement("button");
      checkIn.type = "button";
      checkIn.textContent = "Check in";
      checkIn.addEventListener("click", async () => {
        await fetchJsonWithMethod(config.habitsUrl + "/habits/" + habit.id + "/checkins", "POST");
        loadHabits();
      });
      card.appendChild(checkIn);
      habitsElement.appendChild(card);

      try {
        const summary = await fetchJson(
          config.insightsUrl + "/insights/" + habit.id + "/summary"
        );
        details.textContent =
          "Streak: " + summary.streak +
          ", best weekday: " + (summary.best_weekday || "none") +
          ", milestones: " + summary.milestones.length;
      } catch (error) {
        details.textContent = error.message;
      }
    }
  } catch (error) {
    message.textContent = error.message;
    retry.hidden = false;
  }
}

async function fetchJsonWithMethod(url, method) {
  const response = await fetch(url, {
    method: method,
    headers: { "Content-Type": "application/json" },
    body: "{}"
  });
  if (!response.ok) {
    throw new Error("starting up, try again");
  }
  return response.json();
}

document.getElementById("retry").addEventListener("click", loadHabits);

document.getElementById("habit-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = document.getElementById("habit-name").value;
  const cadence = document.getElementById("cadence").value;
  const days = cadence === "daily"
    ? [0, 1, 2, 3, 4, 5, 6]
    : [0];
  await fetchJsonWithPayload(config.habitsUrl + "/habits", "POST", {
    name: name,
    cadence: cadence,
    days_of_week: days,
    time_of_day: "09:00",
    alert_type: "at_time"
  });
  event.target.reset();
  loadHabits();
});

async function fetchJsonWithPayload(url, method, payload) {
  const response = await fetch(url, {
    method: method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  if (!response.ok) {
    throw new Error("starting up, try again");
  }
  return response.json();
}

loadHabits();
