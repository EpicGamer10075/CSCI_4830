//name is logged in username
//usersOnly is whether the current page is meant for logged in users or not ["y", "n", "b"]
//boldTab is the current page to be bolded in tabs
function getTabs(name, usersOnly, boldTab){
	addTab(boldTab, "", "Home")
	if(name == "\"Logged Out\"") //render logged out links
	{
		if(usersOnly == "n" || usersOnly == "b")
		{
			addTab(boldTab, "register", "Register")
			addTab(boldTab, "login",    "Login")
			addTab(boldTab, "pwreset",  "Password Reset")
		}
		else
		{
			location.replace("/");
		}
	}
	else //render logged in links
	{
		if(usersOnly == "y" || usersOnly == "b")
		{
			addTab(boldTab, "focus",    "Focus")
			addTab(boldTab, "stats",    "Goals")
			addTab(boldTab, "stats",    "Stats")
			addTab(boldTab, "logout",   "Logout")
			addTab(boldTab, "pwchange", "Password Change")
		}
		else
		{
			location.replace("/");
		}
	}
	document.querySelector("tr").innerHTML += `<td class=\"l\">${name.substring(1,name.length-1)}</td>`;
}

function addTab(curPage, toPage, pageName){
	let selected = pageName == curPage;
	let tdPart = selected ? " class=\"s\"" : "";
	let classPart = selected ? "-s" : "";
	document.querySelector("tr").innerHTML += `<td${tdPart}><a class=\"header${classPart}\" href='../${toPage}'>${pageName}</a></td>`;
}

function inputChecker(){ //general function to start getAFK loop
	setTimeout(getAFK, 0);
}
async function getAFK(){ //launched asynchronous aka multithreaded
	while(true){ //loops, fetching data from doom.py each second
		fetch('/process-data', { //sends request to doom.py
			method: 'POST',
			headers: {'Content-Type': 'application/json'}
		})
		.then(response => response.text())
		.then(result => { //gets result, and uses that here
			//console.log(result);
			//document.querySelector("p").innerHTML += result;
			if(result=="True"){
				alert("AFK!");
				//createReminderBanner();
				showReminderBanner("AFK!")
			} //if AFK, send alert declaring so
		})
		.catch(error => {
			console.error('Error:', error);
		});
		await sleep(1000);
	}
}
function sleep(time) { //sleeps for a specified amount of millisecons
	return new Promise((resolve) => setTimeout(resolve, time));
}


/**
 * banner.js
 *
 * Displays a reminder banner when a check-in reminder happens.
 * The banner stays on the page until the user dismisses it.
 */

/**
 * Shows the reminder banner.
 *
 * @param {string} message The reminder message to display.
 */
function showReminderBanner(message) {
    document.getElementById("reminderBannerText").textContent = message;

    document
        .getElementById("reminderBanner")
        .classList.remove("hidden");
}

/**
 * Hides the reminder banner.
 */
function hideReminderBanner() {
    const banner = document.getElementById("reminderBanner");

    if (banner) {
        banner.classList.add("hidden");
    }
}
