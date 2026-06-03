function test(){
	document.querySelector("tr").innerHTML += "<td><a class=\"header\" href='../'   >TEST</a></td>";
}

//name is logged in username
//usersOnly is whether the current page is meant for logged in users or not ["y", "n", "b"]
//boldTab is the current page to be bolded in tabs
function getTabs(name, usersOnly, boldTab){
	document.querySelector("tr").innerHTML += `<td><a class="header" href='../'>Home</a></td>`;
	if(name == "\"Logged Out\"") //render logged out links
	{
		if(usersOnly == "n" || usersOnly == "b")
		{
			//document.querySelector("tr").innerHTML += "<td><a class=\"header\" href='../register'>Register</a></td>";
			//document.querySelector("tr").innerHTML += "<td><a class=\"header\" href='../login'   >Login</a></td>";
			//document.querySelector("tr").innerHTML += "<td><a class=\"header\" href='../pwreset' >Password Reset</a></td>";
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
			//document.querySelector("tr").innerHTML += "<td><a class=\"header\" href='../focus'   >Focus</a></td>";
			//document.querySelector("tr").innerHTML += "<td><a class=\"header\" href='../logout'  >Logout</a></td>";
			//document.querySelector("tr").innerHTML += "<td><a class=\"header\" href='../pwchange'>Password Change</a></td>";
			addTab(boldTab, "focus",    "Focus")
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


