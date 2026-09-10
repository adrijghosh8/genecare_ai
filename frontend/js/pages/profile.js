// =========================================
// Profile Page
// =========================================

const profileToken = getToken();

const nameInput =
    document.getElementById("name");

const emailInput =
    document.getElementById("email");

const profileName =
    document.getElementById("profile-name");

const profileEmail =
    document.getElementById("profile-email");

const profileCreated =
    document.getElementById("profile-created");

const profileAvatar =
    document.getElementById("profile-avatar");

const message =
    document.getElementById("profile-message");

const form =
    document.getElementById("profile-form");


// =========================================
// Get Initials
// =========================================

function getInitials(name) {

    const words = name.trim().split(/\s+/);

    if (words.length === 1) {
        return words[0][0].toUpperCase();
    }

    return (
        words[0][0] +
        words[words.length - 1][0]
    ).toUpperCase();
}


// =========================================
// Load Profile
// =========================================

async function loadProfile() {

    try {

        const response = await fetch(
            "https://genecare-ai.onrender.com/me",
            {
                method: "GET",

                headers: {
                    "Authorization": `Bearer ${profileToken}`
                }
            }
        );


        if (!response.ok) {

            throw new Error(
                "Could not load your profile."
            );

        }


        const user = await response.json();


        // =====================================
        // Fill Form
        // =====================================

        nameInput.value = user.name;

        emailInput.value = user.email;


        // =====================================
        // Fill Profile Summary
        // =====================================

        profileName.textContent =
            user.name;

        profileEmail.textContent =
            user.email;


        profileAvatar.textContent =
            getInitials(user.name);


        // =====================================
        // Member Since
        // =====================================

        if (user.created_at) {

            const date = new Date(
                user.created_at.replace(" ", "T") + "Z"
            );


            profileCreated.textContent =
                date.toLocaleDateString(
                    "en-US",
                    {
                        month: "short",
                        day: "numeric",
                        year: "numeric"
                    }
                );

        }

    } catch (error) {

        console.error(
            "Profile loading error:",
            error
        );


        message.textContent =
            error.message;

        message.className =
            "profile-message error";

    }
}


// =========================================
// Update Profile
// =========================================

form.addEventListener(
    "submit",
    async event => {

        event.preventDefault();


        const name =
            nameInput.value.trim();

        const email =
            emailInput.value.trim();


        if (!name || !email) {

            message.textContent =
                "Name and email are required.";

            message.className =
                "profile-message error";

            return;
        }


        const saveButton =
            document.getElementById("save-profile");


        saveButton.disabled = true;

        saveButton.textContent =
            "Saving...";


        message.textContent = "";


        try {

            const response = await fetch(
                "https://genecare-ai.onrender.com/me",
                {
                    method: "PUT",

                    headers: {

                        "Content-Type":
                            "application/json",

                        "Authorization":
                            `Bearer ${profileToken}`
                    },

                    body: JSON.stringify({
                        name: name,
                        email: email
                    })
                }
            );


            const data =
                await response.json();


            if (!response.ok) {

                throw new Error(
                    data.detail ||
                    "Could not update profile."
                );

            }


            // =================================
            // Update Profile UI
            // =================================

            profileName.textContent =
                data.name;

            profileEmail.textContent =
                data.email;

            profileAvatar.textContent =
                getInitials(data.name);


            // =================================
            // Update Form
            // =================================

            nameInput.value =
                data.name;

            emailInput.value =
                data.email;


            // =================================
            // Update Local Storage
            // =================================

            localStorage.setItem(
                "user",
                JSON.stringify({
                    id: data.id,
                    name: data.name,
                    email: data.email
                })
            );


            // =================================
            // Success Message
            // =================================

            message.textContent =
                "Profile updated successfully.";

            message.className =
                "profile-message success";


        } catch (error) {

            console.error(
                "Profile update error:",
                error
            );


            message.textContent =
                error.message;

            message.className =
                "profile-message error";


        } finally {

            saveButton.disabled = false;

            saveButton.textContent =
                "Save Changes";

        }

    }
);


// =========================================
// Start
// =========================================

loadProfile();

const passwordForm =
    document.getElementById("password-form");

const passwordMessage =
    document.getElementById("password-message");

const changePasswordButton =
    document.getElementById(
        "change-password-button"
    );


if (passwordForm) {

    passwordForm.addEventListener(
        "submit",
        async event => {

            event.preventDefault();

            const currentPassword =
                document.getElementById(
                    "current-password"
                ).value;

            const newPassword =
                document.getElementById(
                    "new-password"
                ).value;

            const confirmPassword =
                document.getElementById(
                    "confirm-password"
                ).value;


            // -----------------------------------------
            // VALIDATION
            // -----------------------------------------

            if (newPassword !== confirmPassword) {

                passwordMessage.textContent =
                    "New passwords do not match.";

                passwordMessage.className =
                    "profile-message error";

                return;
            }


            if (newPassword.length < 8) {

                passwordMessage.textContent =
                    "New password must contain at least 8 characters.";

                passwordMessage.className =
                    "profile-message error";

                return;
            }


            changePasswordButton.disabled = true;

            changePasswordButton.textContent =
                "Changing...";

            passwordMessage.textContent = "";


            try {

                const response = await fetch(
                    "https://genecare-ai.onrender.com/change-password",
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json",

                            "Authorization":
                                `Bearer ${profileToken}`
                        },

                        body: JSON.stringify({
                            current_password:
                                currentPassword,

                            new_password:
                                newPassword
                        })
                    }
                );


                const data =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        data.detail ||
                        "Could not change password."
                    );
                }


                passwordMessage.textContent =
                    "Password changed successfully.";

                passwordMessage.className =
                    "profile-message success";


                passwordForm.reset();


            } catch (error) {

                console.error(
                    "Password change error:",
                    error
                );

                passwordMessage.textContent =
                    error.message;

                passwordMessage.className =
                    "profile-message error";

            } finally {

                changePasswordButton.disabled =
                    false;

                changePasswordButton.textContent =
                    "Change Password";
            }

        }
    );

}

document
    .querySelectorAll(".password-toggle")
    .forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const target =
                    document.getElementById(
                        button.dataset.target
                    );

                const isPassword =
                    target.type === "password";

                target.type =
                    isPassword
                        ? "text"
                        : "password";

                button.textContent =
                    isPassword
                        ? "Hide"
                        : "Show";

            }
        );

    });
