const registerForm = document.getElementById("registerForm");

registerForm.addEventListener("submit", async function (event) {

    event.preventDefault();

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    const errorMessage = document.getElementById("errorMessage");

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/register",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    name: name,
                    email: email,
                    password: password
                })
            }
        );

        const data = await response.json();

        if (!response.ok || data.error) {
            errorMessage.textContent =
                data.error || "Registration failed";
            return;
        }

        alert("Account created successfully!");

        window.location.href = "login.html";

    } catch (error) {

        console.error(error);

        errorMessage.textContent =
            "Could not connect to the server.";
    }
});