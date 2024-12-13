let icon = document.getElementById("theme-icon");
let theme = localStorage.getItem("theme");
    icon.onclick = function(){
        if (theme === "dark") {
            theme = "light";
            icon.src="static/img/moon.png";
            document.querySelector("body").classList.remove("dark-theme");
            document.querySelector("body").classList.add("light-theme");
        } else {
            theme = "dark";
            icon.src="static/img/sun.png";
            document.querySelector("body").classList.remove("light-theme");
            document.querySelector("body").classList.add("dark-theme");
        }
        localStorage.setItem("theme", theme);
    }
      if (theme === "dark") {
        document.querySelector("body").classList.add("dark-theme");
         icon.src="static/img/sun.png";
      }
      if (theme === "light") {
        document.querySelector("body").classList.add("light-theme");
         icon.src="static/img/moon.png";
      }