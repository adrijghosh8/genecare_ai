const loginForm = document.getElementById("loginForm");

loginForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const errorMessage = document.getElementById("errorMessage");

    try {

        const response = await fetch(
            "https://genecare-ai.onrender.com",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    email: email,
                    password: password
                })
            }
        );

        const data = await response.json();

        if (!response.ok || data.error) {
            errorMessage.textContent =
                data.error || "Login failed";
            return;
        }

        // Save JWT
        localStorage.setItem(
            "access_token",
            data.access_token
        );

        // Save basic user information
        localStorage.setItem(
            "user",
            JSON.stringify(data.user)
        );

        // Go to dashboard
        window.location.href = "index.html";

    } catch (error) {

        console.error(error);

        errorMessage.textContent =
            "Could not connect to the server.";
    }
});

function getToken() {
    return localStorage.getItem("access_token");
}


function getUser() {
    const user = localStorage.getItem("user");

    if (!user) {
        return null;
    }

    return JSON.parse(user);
}


function isLoggedIn() {
    return getToken() !== null;
}


function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("user");

    window.location.href = "login.html";
}


function protectPage() {
    if (!isLoggedIn()) {
        window.location.href = "login.html";
    }
}
