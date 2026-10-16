const eyeIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z"></path><circle cx="12" cy="12" r="3"></circle></svg>';
const eyeOffIcon = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 3l18 18"></path><path d="M10.6 5.1A10.8 10.8 0 0 1 12 5c6.4 0 10 7 10 7a15.7 15.7 0 0 1-3 3.8"></path><path d="M6.2 6.2C3.5 8 2 12 2 12s3.6 7 10 7c1.3 0 2.5-.3 3.5-.8"></path><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2"></path></svg>';

document.querySelectorAll('input[type="password"]').forEach((input) => {
  const wrapper = document.createElement("span");
  wrapper.className = "password-input-wrap";
  input.parentNode.insertBefore(wrapper, input);
  wrapper.appendChild(input);

  const toggle = document.createElement("button");
  toggle.type = "button";
  toggle.className = "password-toggle";
  toggle.setAttribute("aria-controls", input.id);
  toggle.setAttribute("aria-pressed", "false");
  toggle.setAttribute("aria-label", "Afficher le mot de passe");
  toggle.title = "Afficher le mot de passe";
  toggle.innerHTML = eyeIcon;
  toggle.addEventListener("click", () => {
    const visible = input.type === "password";
    input.type = visible ? "text" : "password";
    toggle.setAttribute("aria-pressed", String(visible));
    toggle.setAttribute("aria-label", visible ? "Masquer le mot de passe" : "Afficher le mot de passe");
    toggle.title = visible ? "Masquer le mot de passe" : "Afficher le mot de passe";
    toggle.innerHTML = visible ? eyeOffIcon : eyeIcon;
  });
  wrapper.appendChild(toggle);
});