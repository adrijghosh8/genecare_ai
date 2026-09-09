const page = document.body.dataset.page;


// ===============================
// Authentication
// ===============================

const token = localStorage.getItem("access_token");
const userData = localStorage.getItem("user");

let authButton = "";


// ===============================
// Get User Initials
// ===============================

function getInitials(name) {

    if (!name) {
        return "U";
    }

    const words = name.trim().split(/\s+/);

    if (words.length === 1) {
        return words[0].charAt(0).toUpperCase();
    }

    return (
        words[0].charAt(0) +
        words[words.length - 1].charAt(0)
    ).toUpperCase();
}


// ===============================
// Logged In / Logged Out UI
// ===============================

if (token && userData) {

    let user;

    try {
        user = JSON.parse(userData);
    } catch {
        user = null;
    }

    if (user) {

        const initials = getInitials(user.name);

        authButton = `
            <div class="profile-menu">

                <button
                    class="profile-trigger"
                    id="profile-trigger"
                    aria-expanded="false"
                    aria-haspopup="true">

                    <span class="profile-avatar">
                        ${initials}
                    </span>

                    <span class="profile-name">
                        ${user.name}
                    </span>

                    <span class="profile-chevron">
                        ▾
                    </span>

                </button>


                <div
                    class="profile-dropdown"
                    id="profile-dropdown">

                    <div class="profile-dropdown-user">

                        <span class="profile-avatar large">
                            ${initials}
                        </span>

                        <div>

                            <strong>
                                ${user.name}
                            </strong>

                            <span>
                                ${user.email || ""}
                            </span>

                        </div>

                    </div>


                    <div class="profile-divider"></div>


                    <a
                        href="profile.html"
                        class="profile-dropdown-link">

                        <span>Profile</span>

                    </a>


                    <a
                        href="history.html"
                        class="profile-dropdown-link">

                        <span>Prediction History</span>

                    </a>


                    <div class="profile-divider"></div>


                    <button
                        class="profile-dropdown-link logout-link"
                        id="logout-btn">

                        <span>Logout</span>

                    </button>

                </div>

            </div>
        `;

    } else {

        authButton = `
            <a class="button" href="login.html">
                Login
            </a>
        `;
    }

} else {

    authButton = `
        <a class="button" href="login.html">
            Login
        </a>
    `;
}


// ===============================
// Header
// ===============================

document.querySelector("#site-header").innerHTML = `
    <div class="container nav">

        <a
            class="brand"
            href="index.html"
            aria-label="GeneCare AI home">

            <img
                src="assets/icons/genecare-mark.svg"
                alt="">

            <span>GeneCare</span> AI

        </a>


        <button
            class="menu"
            aria-label="Open menu"
            aria-expanded="false">

            ☰

        </button>


        <nav class="nav-links">

            <a
                class="${page === "home" ? "active" : ""}"
                href="index.html">

                Home

            </a>


            <a
                class="${page === "analyze" ? "active" : ""}"
                href="analyze.html">

                Analyze

            </a>


            <a
                class="${page === "diseases" || page === "detail" ? "active" : ""}"
                href="diseases.html">

                Diseases

            </a>


            <a
                class="${page === "about" ? "active" : ""}"
                href="about.html">

                About

            </a>

        </nav>


        ${authButton}

    </div>
`;


// ===============================
// Footer
// ===============================

document.querySelector("#site-footer").innerHTML = `
    <div class="container footer-row">

        <span>
            © 2026 GeneCare AI
        </span>

        <span>
            Educational screening only · Not a medical diagnosis
        </span>

    </div>
`;


// ===============================
// Mobile Menu
// ===============================

const menuButton = document.querySelector(".menu");

if (menuButton) {

    menuButton.addEventListener("click", event => {

        const open =
            document
                .querySelector(".nav-links")
                .classList
                .toggle("open");

        event.currentTarget.setAttribute(
            "aria-expanded",
            String(open)
        );

    });

}


// ===============================
// Profile Dropdown
// ===============================

const profileTrigger =
    document.querySelector("#profile-trigger");

const profileDropdown =
    document.querySelector("#profile-dropdown");


if (profileTrigger && profileDropdown) {

    profileTrigger.addEventListener("click", event => {

        event.stopPropagation();

        const isOpen =
            profileDropdown.classList.toggle("open");

        profileTrigger.setAttribute(
            "aria-expanded",
            String(isOpen)
        );

    });


    // Close when clicking outside

    document.addEventListener("click", event => {

        if (
            !profileDropdown.contains(event.target) &&
            !profileTrigger.contains(event.target)
        ) {

            profileDropdown.classList.remove("open");

            profileTrigger.setAttribute(
                "aria-expanded",
                "false"
            );

        }

    });

}


// ===============================
// Logout
// ===============================

const logoutButton =
    document.querySelector("#logout-btn");

if (logoutButton) {

    logoutButton.addEventListener("click", () => {

        localStorage.removeItem("access_token");

        localStorage.removeItem("user");

        window.location.href = "login.html";

    });

}