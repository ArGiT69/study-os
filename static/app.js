let contributions = [];

let selectedDay = null;


function getToday() {

    return new Date()
        .toISOString()
        .slice(0, 10);
}


function formatDate(day) {

    return new Date(
        day + "T12:00:00"
    ).toLocaleDateString(
        undefined,
        {
            weekday: "long",
            month: "long",
            day: "numeric",
            year: "numeric"
        }
    );
}


function contributionLevel(pages) {

    pages = Number(pages);

    if (pages <= 0)
        return "level-0";

    if (pages <= 2)
        return "level-1";

    if (pages <= 5)
        return "level-2";

    if (pages <= 9)
        return "level-3";

    return "level-4";
}


async function loadWriting() {

    const response =
        await fetch(
            "/api/contributions"
        );


    contributions =
        await response.json();


    renderGraph();


    updateWritingStats();
}


function renderGraph() {

    const graph =
        document.getElementById(
            "contributionGraph"
        );


    if (!graph)
        return;


    graph.innerHTML = "";


    const map = new Map(
        contributions.map(
            item => [
                item.day,
                item
            ]
        )
    );


    const today =
        new Date();


    const start =
        new Date(today);


    start.setDate(
        today.getDate() - 364
    );


    start.setDate(
        start.getDate()
        - start.getDay()
    );


    for (
        let i = 0;
        i < 371;
        i++
    ) {

        const current =
            new Date(start);


        current.setDate(
            start.getDate() + i
        );


        const day =
            current
                .toISOString()
                .slice(0, 10);


        const entry =
            map.get(day);


        const square =
            document.createElement(
                "div"
            );


        square.className =
            "day " +
            contributionLevel(
                entry
                    ? entry.pages
                    : 0
            );


        square.title =
            `${formatDate(day)} — ${
                entry
                    ? entry.pages
                    : 0
            } pages`;


        square.onclick =
            () => {

                selectedDay = day;

                openContribution(
                    day,
                    entry
                );

            };


        graph.appendChild(
            square
        );

    }

}


function updateWritingStats() {

    const total =
        contributions.reduce(
            (sum, item) =>
                sum + Number(item.pages),
            0
        );


    document.getElementById(
        "writingTotal"
    ).textContent =
        total.toFixed(1);


    /*
       Current streak
    */

    const active =
        new Set(
            contributions
                .filter(
                    item =>
                        Number(item.pages) > 0
                )
                .map(
                    item =>
                        item.day
                )
        );


    let streak = 0;

    let day = new Date();


    while (
        active.has(
            day.toISOString().slice(0, 10)
        )
    ) {

        streak++;

        day.setDate(
            day.getDate() - 1
        );

    }


    if (
        streak === 0
    ) {

        day = new Date();

        day.setDate(
            day.getDate() - 1
        );


        while (
            active.has(
                day.toISOString().slice(0, 10)
            )
        ) {

            streak++;

            day.setDate(
                day.getDate() - 1
            );

        }

    }


    document.getElementById(
        "writingStreak"
    ).textContent =
        streak;


    /*
       Best streak
    */

    const days =
        Array.from(active)
            .sort();


    let best = 0;

    let running = 0;

    let previous = null;


    for (
        const value of days
    ) {

        const current =
            new Date(
                value + "T12:00:00"
            );


        if (
            previous &&
            current.getTime()
            ===
            previous.getTime()
            +
            86400000
        ) {

            running++;

        } else {

            running = 1;

        }


        best =
            Math.max(
                best,
                running
            );


        previous =
            current;

    }


    document.getElementById(
        "writingBest"
    ).textContent =
        best;

}


function openContribution(
    day = getToday(),
    entry = null
) {

    selectedDay = day;


    document.getElementById(
        "contributionModal"
    ).classList.remove(
        "hidden"
    );


    document.getElementById(
        "contributionDate"
    ).value =
        day;


    document.getElementById(
        "contributionPages"
    ).value =
        entry
            ? entry.pages
            : "";


    document.getElementById(
        "contributionSubject"
    ).value =
        entry
            ? entry.subject_id || ""
            : "";


    document.getElementById(
        "contributionNotes"
    ).value =
        entry
            ? entry.notes || ""
            : "";

}


function closeContribution() {

    document.getElementById(
        "contributionModal"
    ).classList.add(
        "hidden"
    );

}


async function saveContribution() {

    const day =
        document.getElementById(
            "contributionDate"
        ).value;


    const pages =
        Number(
            document.getElementById(
                "contributionPages"
            ).value || 0
        );


    const subject =
        document.getElementById(
            "contributionSubject"
        ).value;


    const notes =
        document.getElementById(
            "contributionNotes"
        ).value;


    const response =
        await fetch(
            "/api/contributions",
            {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    day: day,

                    pages: pages,

                    subject_id:
                        subject
                            ? Number(subject)
                            : null,

                    notes: notes

                })

            }
        );


    const result =
        await response.json();


    if (!result.ok) {

        alert(
            result.error ||
            "Something went wrong."
        );

        return;

    }


    closeContribution();

    await loadWriting();

}


document.addEventListener(
    "DOMContentLoaded",
    () => {

        document.querySelectorAll(
            ".progress-bar[data-progress]"
        ).forEach(
            progressBar => {

                progressBar.style.width =
                    `${progressBar.dataset.progress}%`;

            }
        );

        if (
            document.getElementById(
                "contributionGraph"
            )
        ) {

            loadWriting();

        }

    }
);